"""
Phase 4.5a-fam: Family Title + Summary Generation

Generates LLM titles and summaries for event families.
Input: cluster titles within each family.
Output: family title, summary (EN + DE).

Families with 1 cluster copy the cluster title directly.
Families with 2+ clusters get an LLM-generated title + summary.

Usage:
    python pipeline/phase_4/generate_family_summaries.py --ctm-id <uuid>
    python pipeline/phase_4/generate_family_summaries.py --centroid AMERICAS-USA --track geo_security
    python pipeline/phase_4/generate_family_summaries.py --centroid AMERICAS-USA --track geo_security --force
"""

import argparse
import asyncio
import sys
from pathlib import Path

import httpx
import psycopg2

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config
from core.llm_utils import extract_json

FAMILY_SUMMARY_SYSTEM = """Generate a title and summary for a news story family.

You receive a list of topic cluster titles that belong to the same developing story.

Return JSON: {"title": "...", "summary": "..."}

TITLE: 5-10 words. What a reader would remember this story as. Plain language, no jargon.
SUMMARY: 2-4 sentences. What happened, key actors, current status. Factual, no opinion.

ASCII only. No emoji. No markdown."""

FAMILY_SUMMARY_USER = """Story family ({cluster_count} topics, {source_count} sources):

{cluster_list}

Generate JSON:"""

TRANSLATE_SYSTEM = (
    "Translate the title and summary to German. "
    'Return JSON: {"title_de": "...", "summary_de": "..."}\n'
    "Return ONLY the JSON."
)


async def call_llm(system, user, temperature=0.3, max_tokens=500):
    """Single LLM call. Returns parsed content string."""
    from core.llm_utils import async_check_rate_limit

    headers = {
        "Authorization": "Bearer %s" % config.deepseek_api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        for attempt in range(3):
            resp = await client.post(
                "%s/chat/completions" % config.deepseek_api_url,
                headers=headers,
                json=payload,
            )
            if await async_check_rate_limit(resp, attempt):
                continue
            if resp.status_code != 200:
                return None
            break
        else:
            return None

        return resp.json()["choices"][0]["message"]["content"].strip()


async def generate_family_title_summary(clusters):
    """Generate title + summary for a family from its cluster titles."""
    lines = []
    for i, (title, src) in enumerate(clusters, 1):
        lines.append("%d. [%d src] %s" % (i, src, title or "untitled"))
    cluster_list = "\n".join(lines)

    user = FAMILY_SUMMARY_USER.format(
        cluster_count=len(clusters),
        source_count=sum(s for _, s in clusters),
        cluster_list=cluster_list,
    )

    content = await call_llm(FAMILY_SUMMARY_SYSTEM, user)
    if not content:
        return None, None

    result = extract_json(content)
    if not result:
        return None, None

    return result.get("title", ""), result.get("summary", "")


async def translate_de(title, summary):
    """Translate title + summary to German."""
    user = "Title: %s\nSummary: %s" % (title, summary)
    content = await call_llm(TRANSLATE_SYSTEM, user, temperature=0.2, max_tokens=400)
    if not content:
        return None, None

    result = extract_json(content)
    if not result:
        return None, None

    return result.get("title_de", ""), result.get("summary_de", "")


# --- DB ---


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def get_ctm_info(conn, ctm_id=None, centroid=None, track=None):
    cur = conn.cursor()
    if ctm_id:
        cur.execute(
            "SELECT id, centroid_id, track, month FROM ctm WHERE id = %s",
            (ctm_id,),
        )
    else:
        cur.execute(
            "SELECT id, centroid_id, track, month FROM ctm "
            "WHERE centroid_id = %s AND track = %s ORDER BY month DESC LIMIT 1",
            (centroid, track),
        )
    row = cur.fetchone()
    cur.close()
    if not row:
        return None
    return {"id": row[0], "centroid_id": row[1], "track": row[2], "month": row[3]}


def load_families_needing_summaries(conn, ctm_id, force=False):
    """Load families that need LLM title/summary generation."""
    cur = conn.cursor()
    if force:
        cur.execute(
            """SELECT ef.id, ef.spine_value, ef.cluster_count, ef.source_count
               FROM event_families ef
               WHERE ef.ctm_id = %s
               ORDER BY ef.source_count DESC""",
            (ctm_id,),
        )
    else:
        # Only families without summary (spine_value as title = not yet LLM-processed)
        cur.execute(
            """SELECT ef.id, ef.spine_value, ef.cluster_count, ef.source_count
               FROM event_families ef
               WHERE ef.ctm_id = %s AND ef.summary IS NULL
               ORDER BY ef.source_count DESC""",
            (ctm_id,),
        )
    families = cur.fetchall()
    cur.close()
    return families


def load_family_clusters(conn, family_id):
    """Load cluster titles for a family."""
    cur = conn.cursor()
    cur.execute(
        """SELECT e.title, e.source_batch_count
           FROM events_v3 e
           WHERE e.family_id = %s AND NOT e.is_catchall AND e.merged_into IS NULL
           ORDER BY e.source_batch_count DESC""",
        (str(family_id),),
    )
    rows = cur.fetchall()
    cur.close()
    return [(r[0], r[1]) for r in rows]


# --- Main ---


async def process_ctm_async(ctm_id=None, centroid=None, track=None, force=False):
    """Generate LLM titles/summaries for families in a CTM."""
    conn = get_connection()
    try:
        ctm = get_ctm_info(conn, ctm_id, centroid, track)
        if not ctm:
            print("CTM not found")
            return 0

        ctm_id_str = str(ctm["id"])
        print("=== Family Summary Generation ===")
        print("  %s / %s / %s" % (ctm["centroid_id"], ctm["track"], ctm["month"]))

        families = load_families_needing_summaries(conn, ctm_id_str, force)
        if not families:
            print("  No families need summaries")
            return 0

        print("  %d families to process" % len(families))

        cur = conn.cursor()
        generated = 0
        translated = 0

        for fam_id, spine_value, cluster_count, source_count in families:
            clusters = load_family_clusters(conn, fam_id)
            if not clusters:
                continue

            if len(clusters) == 1:
                # Single-cluster family: copy cluster title, no LLM
                title = clusters[0][0] or spine_value
                summary = None
            else:
                # Multi-cluster family: LLM generates title + summary
                title, summary = await generate_family_title_summary(clusters)
                if not title:
                    print(
                        "    WARN: LLM failed for family %s (%s)"
                        % (
                            str(fam_id)[:8],
                            spine_value,
                        )
                    )
                    title = spine_value
                    summary = None

            # Translate to German
            title_de, summary_de = None, None
            if title and (summary or len(clusters) == 1):
                if summary:
                    title_de, summary_de = await translate_de(title, summary)
                else:
                    # Title-only: quick translate
                    title_de, _ = await translate_de(title, title)
                if title_de:
                    translated += 1

            cur.execute(
                """UPDATE event_families
                   SET title = %s, summary = %s,
                       title_de = %s, summary_de = %s,
                       updated_at = NOW()
                   WHERE id = %s""",
                (title, summary, title_de, summary_de, str(fam_id)),
            )
            generated += 1

            if generated % 10 == 0:
                conn.commit()
                print("    %d/%d families processed..." % (generated, len(families)))

        conn.commit()
        cur.close()
        print(
            "  Generated %d family summaries (%d DE translations)"
            % (
                generated,
                translated,
            )
        )
        return generated
    finally:
        conn.close()


def process_ctm(ctm_id=None, centroid=None, track=None, force=False):
    """Sync wrapper for daemon compatibility."""
    return asyncio.run(
        process_ctm_async(
            ctm_id=ctm_id,
            centroid=centroid,
            track=track,
            force=force,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Phase 4.5a-fam: Family Title + Summary Generation"
    )
    parser.add_argument("--ctm-id", type=str)
    parser.add_argument("--centroid", type=str)
    parser.add_argument("--track", type=str)
    parser.add_argument("--force", action="store_true", help="Regenerate all")
    args = parser.parse_args()

    if not args.ctm_id and not (args.centroid and args.track):
        print("ERROR: provide --ctm-id or --centroid + --track")
        sys.exit(1)

    result = process_ctm(
        ctm_id=args.ctm_id,
        centroid=args.centroid,
        track=args.track,
        force=args.force,
    )
    print("\nDone. %d families processed." % result)
