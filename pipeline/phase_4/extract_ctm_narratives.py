"""
CTM Narrative Extraction

Single-pass LLM analysis to identify 3-5 narrative frames from a CTM
(Centroid-Track-Month bucket). Samples ~200 titles for frame discovery,
stores results in narratives table with entity_type='ctm'.

Modes:
  - Default: process CTMs that have no narratives yet
  - --refresh: re-process CTMs whose title_count grew significantly

Usage:
    python pipeline/phase_4/extract_ctm_narratives.py --month 2026-02 --dry-run
    python pipeline/phase_4/extract_ctm_narratives.py --month 2026-02 --limit 10
    python pipeline/phase_4/extract_ctm_narratives.py --month 2026-02 --refresh
    python pipeline/phase_4/extract_ctm_narratives.py --ctm <UUID>
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import httpx
import psycopg2
from psycopg2.extras import RealDictCursor

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config  # noqa: E402
from core.llm_utils import extract_json  # noqa: E402

MIN_TITLES = config.v3_p5_min_titles
REFRESH_GROWTH = config.v3_p5_refresh_growth
SAMPLE_SIZE = 200

CTM_NARRATIVE_SYSTEM = (
    "You are a media-framing analyst. You identify distinct narrative frames "
    "used by different news sources to cover a geopolitical topic area."
)

CTM_NARRATIVE_USER = """Region: {centroid_id}
Track: {track}
Month: {month}
CTM summary: {summary}

Below are {sample_count} sampled headlines from this coverage bucket. Each is prefixed with [publisher].

{titles_block}

Identify 3-5 distinct NARRATIVE FRAMES used across these headlines.

RULES:
1. Each frame MUST assign moral roles (hero/villain, victim/aggressor, right/wrong)
2. Frames should capture genuinely different editorial stances, not topic variations
3. Include the headline indices (1-based) that support each frame

REJECT these frame types:
- Neutral/analytical frames everyone agrees on
- Topic descriptions (e.g. "Diplomatic efforts", "Energy crisis")
- Frames where all sides would agree

Return a JSON array:
[
  {{"label": "short frame name", "description": "1-sentence explanation", "moral_frame": "who is hero/villain", "title_indices": [1, 4, 7]}}
]

Return ONLY the JSON array."""


def get_db_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        dbname=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def fetch_ctms(conn, month, limit=50, ctm_id=None, refresh=False):
    """Fetch CTMs eligible for narrative extraction.

    Default mode: CTMs with no narratives yet.
    Refresh mode: CTMs whose title_count grew by >= REFRESH_GROWTH since
    narratives were last created.
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        if ctm_id:
            cur.execute(
                """
                SELECT c.id, c.centroid_id, c.track, c.month, c.title_count,
                       c.summary_text
                FROM ctm c
                WHERE c.id = %s
                """,
                (ctm_id,),
            )
        elif refresh:
            cur.execute(
                """
                SELECT c.id, c.centroid_id, c.track, c.month, c.title_count,
                       c.summary_text
                FROM ctm c
                WHERE c.month = %s
                  AND c.title_count >= %s
                  AND c.is_frozen = false
                  AND EXISTS (
                      SELECT 1 FROM narratives n
                      WHERE n.entity_type = 'ctm' AND n.entity_id = c.id
                  )
                  AND c.title_count >= (
                      SELECT COALESCE(MAX(n.title_count), 0)
                      FROM narratives n
                      WHERE n.entity_type = 'ctm' AND n.entity_id = c.id
                  ) + %s
                ORDER BY c.title_count DESC
                LIMIT %s
                """,
                (month + "-01", MIN_TITLES, REFRESH_GROWTH, limit),
            )
        else:
            cur.execute(
                """
                SELECT c.id, c.centroid_id, c.track, c.month, c.title_count,
                       c.summary_text
                FROM ctm c
                WHERE c.month = %s
                  AND c.title_count >= %s
                  AND c.is_frozen = false
                  AND NOT EXISTS (
                      SELECT 1 FROM narratives n
                      WHERE n.entity_type = 'ctm' AND n.entity_id = c.id
                  )
                ORDER BY c.title_count DESC
                LIMIT %s
                """,
                (month + "-01", MIN_TITLES, limit),
            )
        return cur.fetchall()


def fetch_ctm_titles(conn, ctm_id):
    """Fetch titles for a CTM via events."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT DISTINCT t.title_display, t.publisher_name, t.pubdate_utc,
                   t.detected_language
            FROM events_v3 e
            JOIN event_v3_titles et ON et.event_id = e.id
            JOIN titles_v3 t ON t.id = et.title_id
            WHERE e.ctm_id = %s
            ORDER BY t.pubdate_utc DESC
            """,
            (str(ctm_id),),
        )
        return cur.fetchall()


def sample_titles(titles, n=SAMPLE_SIZE):
    """Language-stratified sampling for narrative diversity.

    Each language with >= 3 titles gets a guaranteed floor (MIN_LANG_SHARE
    of the sample), so minority-language ecosystems are properly represented.
    Within each language stratum, titles are round-robin'd across publishers.
    """
    if len(titles) <= n:
        return titles

    MIN_LANG_FLOOR = 5  # each qualifying language gets at least 5 titles
    MIN_LANG_TITLES = 3  # need >= 3 titles to qualify

    # Group by language
    by_lang = defaultdict(list)
    for t in titles:
        by_lang[t.get("detected_language") or "unknown"].append(t)

    # Compute allocation: proportional with a floor for minority languages
    total = len(titles)
    lang_allocs = {}
    for lang, ltitles in by_lang.items():
        if len(ltitles) < MIN_LANG_TITLES:
            continue
        proportional_slots = round(n * len(ltitles) / total)
        slots = max(MIN_LANG_FLOOR, proportional_slots)
        # Don't allocate more than available
        slots = min(slots, len(ltitles))
        lang_allocs[lang] = {
            "slots": slots,
            "titles": ltitles,
        }

    # If total slots exceed n, scale down proportionally but keep floors
    total_slots = sum(a["slots"] for a in lang_allocs.values())
    if total_slots > n:
        scale = n / total_slots
        for lang in lang_allocs:
            lang_allocs[lang]["slots"] = max(
                MIN_LANG_FLOOR,
                round(lang_allocs[lang]["slots"] * scale),
            )

    # Round-robin by publisher within each language stratum
    sampled = []
    for lang, alloc in lang_allocs.items():
        slots = alloc["slots"]
        ltitles = alloc["titles"]

        by_pub = defaultdict(list)
        for t in ltitles:
            by_pub[t["publisher_name"] or "unknown"].append(t)

        pubs = list(by_pub.values())
        picked = 0
        idx = 0
        while picked < slots and picked < len(ltitles):
            bucket = pubs[idx % len(pubs)]
            if bucket:
                sampled.append(bucket.pop(0))
                picked += 1
            idx += 1
            if idx > slots + len(pubs):
                break

    # Trim to n if over-allocated due to rounding
    return sampled[:n]


def build_titles_block(titles):
    """Format titles for LLM prompt."""
    lines = []
    for i, t in enumerate(titles, 1):
        pub = t.get("publisher_name") or "unknown"
        lines.append("%d. [%s] %s" % (i, pub, t["title_display"]))
    return "\n".join(lines)


def extract_narratives_llm(ctm, sampled):
    """Call LLM to extract narrative frames."""
    titles_block = build_titles_block(sampled)

    user_prompt = CTM_NARRATIVE_USER.format(
        centroid_id=ctm["centroid_id"],
        track=ctm["track"],
        month=str(ctm["month"])[:7],
        summary=ctm.get("summary_text") or "N/A",
        sample_count=len(sampled),
        titles_block=titles_block,
    )

    headers = {
        "Authorization": "Bearer %s" % config.deepseek_api_key,
        "Content-Type": "application/json",
    }

    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": CTM_NARRATIVE_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 1200,
    }

    resp = httpx.post(
        "%s/chat/completions" % config.deepseek_api_url,
        headers=headers,
        json=payload,
        timeout=120,
    )

    if resp.status_code != 200:
        raise Exception("LLM error: %d - %s" % (resp.status_code, resp.text[:200]))

    data = resp.json()
    content = data["choices"][0]["message"]["content"].strip()
    usage = data.get("usage", {})
    tok_in = usage.get("prompt_tokens", 0)
    tok_out = usage.get("completion_tokens", 0)

    frames = extract_json(content)
    return frames, tok_in, tok_out


def compute_top_sources(titles, indices):
    """Top sources from title indices."""
    sources = Counter()
    for idx in indices:
        if 0 < idx <= len(titles):
            pub = titles[idx - 1].get("publisher_name") or "unknown"
            sources[pub] += 1
    return [s for s, _ in sources.most_common(10)]


def delete_ctm_narratives(conn, ctm_id):
    """Delete existing narratives for a CTM (used before refresh)."""
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM narratives WHERE entity_type = 'ctm' AND entity_id = %s",
            (str(ctm_id),),
        )
        deleted = cur.rowcount
    conn.commit()
    return deleted


def save_narratives(conn, ctm_id, frames, titles):
    """Save extracted frames to narratives table."""
    saved = 0
    with conn.cursor() as cur:
        for frame in frames:
            label = frame.get("label", "").strip()
            if not label:
                continue

            indices = frame.get("title_indices", [])
            title_count = len(indices)
            top_sources = compute_top_sources(titles, indices)

            sample_titles = []
            for idx in indices[:15]:
                if 0 < idx <= len(titles):
                    t = titles[idx - 1]
                    sample_titles.append(
                        {
                            "title": t["title_display"],
                            "publisher": t.get("publisher_name") or "",
                        }
                    )

            cur.execute(
                """
                INSERT INTO narratives
                    (entity_type, entity_id, label, description, moral_frame,
                     title_count, top_sources, sample_titles)
                VALUES ('ctm', %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (entity_id, label) DO UPDATE SET
                    description = EXCLUDED.description,
                    moral_frame = EXCLUDED.moral_frame,
                    title_count = EXCLUDED.title_count,
                    top_sources = EXCLUDED.top_sources,
                    sample_titles = EXCLUDED.sample_titles
                """,
                (
                    str(ctm_id),
                    label,
                    frame.get("description"),
                    frame.get("moral_frame"),
                    title_count,
                    top_sources,
                    json.dumps(sample_titles),
                ),
            )
            saved += 1

    conn.commit()
    return saved


def process_ctm_list(conn, ctms, refresh=False):
    """Process a list of CTMs through narrative extraction.

    Returns dict with ctms, narratives, failed counts.
    """
    results = {"ctms": 0, "narratives": 0, "failed": 0}
    total_tok_in = 0
    total_tok_out = 0

    for i, ctm in enumerate(ctms, 1):
        print(
            "\n[%d/%d] %s / %s (%d titles)"
            % (i, len(ctms), ctm["centroid_id"], ctm["track"], ctm["title_count"])
        )

        titles = fetch_ctm_titles(conn, ctm["id"])
        if len(titles) < MIN_TITLES:
            print("  Skipping: only %d titles (min %d)" % (len(titles), MIN_TITLES))
            results["failed"] += 1
            continue

        sampled = sample_titles(titles)
        lang_counts = Counter(t.get("detected_language") or "?" for t in sampled)
        top_langs = ", ".join("%s:%d" % (lg, c) for lg, c in lang_counts.most_common(5))
        print("  %d titles, sampled %d (%s)" % (len(titles), len(sampled), top_langs))

        try:
            frames, tok_in, tok_out = extract_narratives_llm(ctm, sampled)
            total_tok_in += tok_in
            total_tok_out += tok_out
        except Exception as e:
            print("  ERROR: %s" % e)
            results["failed"] += 1
            continue

        if not frames or not isinstance(frames, list):
            print("  No frames extracted")
            results["failed"] += 1
            continue

        if refresh:
            deleted = delete_ctm_narratives(conn, ctm["id"])
            print("  Deleted %d old narratives" % deleted)

        saved = save_narratives(conn, ctm["id"], frames, sampled)
        results["ctms"] += 1
        results["narratives"] += saved

        print("  -> %d narrative frames saved" % saved)
        for f in frames:
            print(
                "     [%s] %s (%d titles)"
                % (
                    f["label"],
                    f.get("description", "")[:60],
                    len(f.get("title_indices", [])),
                )
            )

    print(
        "\nComplete: %d CTMs, %d narratives, %d failed"
        % (results["ctms"], results["narratives"], results["failed"])
    )
    print("Tokens: %d in, %d out" % (total_tok_in, total_tok_out))
    return results


def process_ctm_narratives(month=None, limit=20):
    """Daemon-callable entry point. Runs both new + refresh passes."""
    from datetime import date

    if not month:
        month = date.today().strftime("%Y-%m")

    conn = get_db_connection()
    total = {"ctms": 0, "narratives": 0, "failed": 0}

    # Pass 1: new CTMs without narratives
    new_ctms = fetch_ctms(conn, month, limit=limit)
    if new_ctms:
        print("New CTMs: %d eligible" % len(new_ctms))
        r = process_ctm_list(conn, new_ctms, refresh=False)
        for k in total:
            total[k] += r[k]

    # Pass 2: refresh CTMs with significant growth
    refresh_ctms = fetch_ctms(conn, month, limit=limit, refresh=True)
    if refresh_ctms:
        print("\nRefresh CTMs: %d eligible" % len(refresh_ctms))
        r = process_ctm_list(conn, refresh_ctms, refresh=True)
        for k in total:
            total[k] += r[k]

    if not new_ctms and not refresh_ctms:
        print("No CTMs need narrative extraction")

    conn.close()
    return total


def main():
    parser = argparse.ArgumentParser(
        description="Extract narrative frames from CTM buckets"
    )
    parser.add_argument("--month", type=str, help="YYYY-MM format")
    parser.add_argument("--ctm", type=str, help="Process specific CTM by UUID")
    parser.add_argument("--limit", type=int, default=20, help="Max CTMs to process")
    parser.add_argument(
        "--refresh", action="store_true", help="Re-extract CTMs with title growth"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be processed"
    )
    args = parser.parse_args()

    if not args.month and not args.ctm:
        print("ERROR: specify --month or --ctm")
        sys.exit(1)

    mode = "refresh" if args.refresh else "new"
    print("CTM Narrative Extraction [%s mode]" % mode)
    print("=" * 50)

    conn = get_db_connection()

    ctms = fetch_ctms(
        conn, args.month or "", args.limit, args.ctm, refresh=args.refresh
    )
    print("Found %d CTMs eligible for narrative extraction" % len(ctms))

    if not ctms:
        print("Nothing to process")
        conn.close()
        return

    if args.dry_run:
        print("\nDry run - would process:")
        for c in ctms:
            print(
                "  - %s / %s (%d titles)"
                % (c["centroid_id"], c["track"], c["title_count"])
            )
        conn.close()
        return

    process_ctm_list(conn, ctms, refresh=args.refresh)
    conn.close()


if __name__ == "__main__":
    main()
