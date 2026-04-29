"""
Stance-Clustered Narrative Extraction

Groups publishers by their stance scores toward a centroid, samples headlines
per cluster, and asks the LLM to identify the dominant narrative frame for
each cluster. Produces 1-3 narratives grounded in real editorial groupings.

Supports both events and CTMs.

Usage:
    python pipeline/phase_4/extract_stance_narratives.py --entity-type event --entity-id <UUID>
    python pipeline/phase_4/extract_stance_narratives.py --entity-type ctm --entity-id <UUID>
    python pipeline/phase_4/extract_stance_narratives.py --entity-type event --entity-id <UUID> --dry-run
"""

import argparse
import json
import sys
from collections import Counter
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
from core.prompts import STANCE_NARRATIVE_SYSTEM, STANCE_NARRATIVE_USER  # noqa: E402
from pipeline.phase_4.extract_ctm_narratives import sample_titles  # noqa: E402

MIN_TITLES_PER_CLUSTER = 10
SAMPLE_PER_CLUSTER = 60

# Stance score boundaries
CRITICAL_UPPER = -0.5
SUPPORTIVE_LOWER = 0.5

CLUSTER_LABELS = {
    "critical": "Critical / Skeptical",
    "reportorial": "Reportorial / Neutral",
    "supportive": "Constructive / Supportive",
}


def get_db_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        dbname=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


# ---------------------------------------------------------------------------
# Entity loading
# ---------------------------------------------------------------------------


def load_event(conn, event_id):
    """Load event + parent CTM context."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT e.id, e.title, e.summary, e.source_batch_count,
                   e.ctm_id, c.centroid_id, c.track, c.month
            FROM events_v3 e
            JOIN ctm c ON c.id = e.ctm_id
            WHERE e.id = %s
            """,
            (str(event_id),),
        )
        return cur.fetchone()


def load_ctm(conn, ctm_id):
    """Load CTM."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT c.id, c.centroid_id, c.track, c.month, c.title_count,
                   c.summary_text
            FROM ctm c WHERE c.id = %s
            """,
            (str(ctm_id),),
        )
        return cur.fetchone()


# ---------------------------------------------------------------------------
# Stance clustering
# ---------------------------------------------------------------------------


def fetch_stance_scores(conn, centroid_id, month):
    """Get publisher stance scores for this centroid.

    Uses the exact month if available, otherwise falls back to the most
    recent month with scores (editorial stance is structurally stable).
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT feed_name, score, confidence, month
            FROM publisher_stance
            WHERE centroid_id = %s
              AND month = (
                  SELECT MAX(month) FROM publisher_stance
                  WHERE centroid_id = %s AND month <= %s
              )
            ORDER BY score
            """,
            (centroid_id, centroid_id, month),
        )
        rows = cur.fetchall()
        if rows and rows[0]["month"] != month:
            used = str(rows[0]["month"])[:7]
            print(
                "  Stance fallback: using %s scores (no data for %s)"
                % (used, str(month)[:7])
            )
        return rows


def build_clusters(stance_rows):
    """Bucket publishers into critical/reportorial/supportive clusters.

    Returns dict of cluster_label -> {publishers: [...], avg_score: float}.
    Clusters with zero publishers are omitted.
    """
    clusters = {
        "critical": [],
        "reportorial": [],
        "supportive": [],
    }

    for row in stance_rows:
        score = row["score"]
        if score < CRITICAL_UPPER:
            clusters["critical"].append(row)
        elif score > SUPPORTIVE_LOWER:
            clusters["supportive"].append(row)
        else:
            clusters["reportorial"].append(row)

    result = {}
    for label, rows in clusters.items():
        if not rows:
            continue
        publishers = [r["feed_name"] for r in rows]
        avg_score = sum(r["score"] for r in rows) / len(rows)
        result[label] = {
            "publishers": publishers,
            "avg_score": round(avg_score, 2),
            "scores": {r["feed_name"]: r["score"] for r in rows},
        }

    return result


# ---------------------------------------------------------------------------
# Title fetching (per cluster)
# ---------------------------------------------------------------------------


def fetch_event_titles_by_publishers(conn, event_id, publishers):
    """Fetch headlines for an event, filtered to specific publishers."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT DISTINCT t.title_display, t.publisher_name, t.pubdate_utc,
                   t.detected_language
            FROM event_v3_titles evt
            JOIN titles_v3 t ON t.id = evt.title_id
            WHERE evt.event_id = %s
              AND t.publisher_name = ANY(%s)
            ORDER BY t.pubdate_utc DESC
            """,
            (str(event_id), publishers),
        )
        return cur.fetchall()


def fetch_ctm_titles_by_publishers(conn, ctm_id, publishers):
    """Fetch headlines for a CTM, filtered to specific publishers."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT DISTINCT t.title_display, t.publisher_name, t.pubdate_utc,
                   t.detected_language
            FROM events_v3 e
            JOIN event_v3_titles et ON et.event_id = e.id
            JOIN titles_v3 t ON t.id = et.title_id
            WHERE e.ctm_id = %s
              AND e.merged_into IS NULL
              AND t.publisher_name = ANY(%s)
            ORDER BY t.pubdate_utc DESC
            """,
            (str(ctm_id), publishers),
        )
        return cur.fetchall()


# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------


def build_entity_context(entity, entity_type):
    """Build the entity context block for the prompt."""
    if entity_type == "event":
        parts = []
        parts.append("Event: %s" % (entity.get("title") or "untitled"))
        if entity.get("summary"):
            parts.append("Summary: %s" % entity["summary"][:500])
        parts.append("Region: %s" % entity["centroid_id"])
        parts.append("Track: %s" % entity["track"])
        return "\n".join(parts)
    else:
        parts = []
        parts.append("Region: %s" % entity["centroid_id"])
        parts.append("Track: %s" % entity["track"])
        parts.append("Month: %s" % str(entity["month"])[:7])
        if entity.get("summary_text"):
            parts.append("CTM summary: %s" % entity["summary_text"][:500])
        return "\n".join(parts)


def build_clusters_block(cluster_samples):
    """Build the prompt block for all clusters.

    cluster_samples: list of (cluster_label, publishers, avg_score, sampled_titles)
    """
    parts = []
    for cluster_label, publishers, avg_score, titles in cluster_samples:
        parts.append(
            "--- CLUSTER: %s (avg stance score: %.1f) ---" % (cluster_label, avg_score)
        )
        parts.append("Publishers: %s" % ", ".join(publishers))
        parts.append("")
        for i, t in enumerate(titles, 1):
            pub = t.get("publisher_name") or "unknown"
            dt = t.get("pubdate_utc")
            day = str(dt)[:10] if dt else ""
            parts.append("%d. [%s][%s] %s" % (i, day, pub, t["title_display"]))
        parts.append("")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------


def call_extraction_llm(entity_context, clusters_block):
    """Call LLM to extract one narrative frame per cluster."""
    user_prompt = STANCE_NARRATIVE_USER.format(
        entity_context=entity_context,
        clusters_block=clusters_block,
    )

    headers = {
        "Authorization": "Bearer %s" % config.deepseek_api_key,
        "Content-Type": "application/json",
    }

    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": STANCE_NARRATIVE_SYSTEM},
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


# ---------------------------------------------------------------------------
# Save results
# ---------------------------------------------------------------------------


def save_stance_narratives(
    conn, entity_type, entity_id, frames, cluster_meta, source_batch_count=None
):
    """Save extracted stance-clustered narratives.

    cluster_meta: dict of cluster_label -> {publishers, avg_score, titles, sample_titles}
    """
    saved = 0
    with conn.cursor() as cur:
        for frame in frames:
            raw_cluster = frame.get("cluster", "").strip()
            label = frame.get("label", "").strip()
            if not label or not raw_cluster:
                continue

            # Match cluster key: exact first, then fuzzy (LLM may echo
            # human-readable label instead of key)
            cluster = raw_cluster
            meta = cluster_meta.get(cluster)
            if not meta:
                raw_lower = raw_cluster.lower()
                for key in cluster_meta:
                    if key in raw_lower:
                        cluster = key
                        meta = cluster_meta[key]
                        break
            if not meta:
                print(
                    "  WARNING: frame cluster '%s' not in meta, skipping" % raw_cluster
                )
                continue

            exemplars = frame.get("exemplar_indices", [])
            sample_titles_json = []
            for idx in exemplars[:15]:
                if 0 < idx <= len(meta["sampled"]):
                    t = meta["sampled"][idx - 1]
                    sample_titles_json.append(
                        {
                            "title": t["title_display"],
                            "publisher": t.get("publisher_name") or "",
                        }
                    )

            # Also include first N non-exemplar titles for sample breadth
            if len(sample_titles_json) < 10:
                for t in meta["sampled"][:15]:
                    entry = {
                        "title": t["title_display"],
                        "publisher": t.get("publisher_name") or "",
                    }
                    if entry not in sample_titles_json:
                        sample_titles_json.append(entry)
                        if len(sample_titles_json) >= 15:
                            break

            top_sources = [
                s
                for s, _ in Counter(
                    t.get("publisher_name") or "unknown" for t in meta["sampled"]
                ).most_common(10)
            ]

            # Frame-level stats
            signal_stats = {
                "source_count_at_extraction": source_batch_count
                or len(meta["sampled"]),
                "cluster_publishers": meta["publishers"],
                "cluster_avg_score": meta["avg_score"],
                "frame_title_count": len(meta["sampled"]),
            }

            cur.execute(
                """
                INSERT INTO narratives
                    (entity_type, entity_id, label, description, moral_frame,
                     title_count, top_sources, sample_titles, signal_stats,
                     extraction_method, cluster_label, cluster_publishers,
                     cluster_score_avg)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,
                        'stance_clustered', %s, %s, %s)
                ON CONFLICT (entity_id, label) DO UPDATE SET
                    description = EXCLUDED.description,
                    moral_frame = EXCLUDED.moral_frame,
                    title_count = EXCLUDED.title_count,
                    top_sources = EXCLUDED.top_sources,
                    sample_titles = EXCLUDED.sample_titles,
                    signal_stats = EXCLUDED.signal_stats,
                    extraction_method = EXCLUDED.extraction_method,
                    cluster_label = EXCLUDED.cluster_label,
                    cluster_publishers = EXCLUDED.cluster_publishers,
                    cluster_score_avg = EXCLUDED.cluster_score_avg
                """,
                (
                    entity_type,
                    str(entity_id),
                    label,
                    frame.get("description"),
                    frame.get("moral_frame"),
                    len(meta["sampled"]),
                    top_sources,
                    json.dumps(sample_titles_json),
                    json.dumps(signal_stats),
                    cluster,
                    meta["publishers"],
                    meta["avg_score"],
                ),
            )
            saved += 1

    conn.commit()
    return saved


# ---------------------------------------------------------------------------
# Main extraction flow
# ---------------------------------------------------------------------------


def extract_stance_narratives(conn, entity_type, entity_id, dry_run=False):
    """Full extraction pipeline for one entity.

    Returns dict with cluster_count, narrative_count, or None on skip.
    """
    # 1. Load entity
    if entity_type == "event":
        entity = load_event(conn, entity_id)
    else:
        entity = load_ctm(conn, entity_id)

    if not entity:
        print("Entity not found: %s %s" % (entity_type, entity_id))
        return None

    centroid_id = entity["centroid_id"]
    month = entity["month"]

    print("Entity: %s %s" % (entity_type, entity_id))
    print("Centroid: %s, Month: %s" % (centroid_id, str(month)[:7]))
    if entity_type == "event":
        print("Event: %s" % (entity.get("title") or "untitled")[:80])

    # 2. Fetch stance scores
    stance_rows = fetch_stance_scores(conn, centroid_id, month)
    if not stance_rows:
        print(
            "No stance scores for %s / %s -- cannot cluster"
            % (centroid_id, str(month)[:7])
        )
        return None

    print("Stance scores: %d publishers" % len(stance_rows))

    # 3. Build clusters
    clusters = build_clusters(stance_rows)
    print(
        "Clusters formed: %s"
        % ", ".join(
            "%s (%d pubs, avg %.1f)" % (k, len(v["publishers"]), v["avg_score"])
            for k, v in clusters.items()
        )
    )

    # 4. Fetch and sample titles per cluster
    cluster_samples = []  # (label, publishers, avg_score, sampled_titles)
    cluster_meta = {}

    for cluster_label, cdata in clusters.items():
        publishers = cdata["publishers"]

        if entity_type == "event":
            titles = fetch_event_titles_by_publishers(conn, entity_id, publishers)
        else:
            titles = fetch_ctm_titles_by_publishers(conn, entity_id, publishers)

        if len(titles) < MIN_TITLES_PER_CLUSTER:
            print(
                "  %s: %d titles (below minimum %d) -- skipping cluster"
                % (cluster_label, len(titles), MIN_TITLES_PER_CLUSTER)
            )
            continue

        sampled = sample_titles(
            titles, n=SAMPLE_PER_CLUSTER, time_stratify=(entity_type == "event")
        )

        lang_counts = Counter(t.get("detected_language") or "?" for t in sampled)
        top_langs = ", ".join("%s:%d" % (lg, c) for lg, c in lang_counts.most_common(3))
        print(
            "  %s: %d titles, sampled %d (%s)"
            % (cluster_label, len(titles), len(sampled), top_langs)
        )

        cluster_samples.append((cluster_label, publishers, cdata["avg_score"], sampled))
        cluster_meta[cluster_label] = {
            "publishers": publishers,
            "avg_score": cdata["avg_score"],
            "sampled": sampled,
        }

    if not cluster_samples:
        print("No clusters have enough titles -- cannot extract")
        return None

    if len(cluster_samples) == 1:
        print("NOTE: Only 1 cluster has enough data -- single-perspective extraction")

    if dry_run:
        print("\nDry run -- would extract %d cluster narratives" % len(cluster_samples))
        for cl, pubs, avg, titles in cluster_samples:
            print(
                "  %s: %d publishers, %d sampled titles, avg score %.1f"
                % (cl, len(pubs), len(titles), avg)
            )
            for p in pubs:
                score = clusters[cl]["scores"].get(p, 0)
                print("    - %s (%.1f)" % (p, score))
        return {"cluster_count": len(cluster_samples), "narrative_count": 0}

    # 5. Build prompt and call LLM
    entity_context = build_entity_context(entity, entity_type)
    clusters_block = build_clusters_block(cluster_samples)

    print("\nCalling LLM...")
    frames, tok_in, tok_out = call_extraction_llm(entity_context, clusters_block)
    print("Tokens: %d in, %d out" % (tok_in, tok_out))

    if not frames or not isinstance(frames, list):
        print("ERROR: No frames extracted from LLM response")
        return {"cluster_count": len(cluster_samples), "narrative_count": 0}

    # 6. Save
    saved = save_stance_narratives(
        conn,
        entity_type,
        entity_id,
        frames,
        cluster_meta,
        source_batch_count=entity.get("source_batch_count"),
    )

    print("\nSaved %d stance-clustered narratives:" % saved)
    for f in frames:
        print("  [%s] %s" % (f.get("cluster", "?"), f.get("label", "?")))
        print("    %s" % f.get("description", "")[:100])

    return {"cluster_count": len(cluster_samples), "narrative_count": saved}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def batch_extract_events(conn, min_sources=30, dry_run=False, limit=None):
    """Extract stance narratives for all eligible events in Jan/Feb."""
    from psycopg2.extras import RealDictCursor

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT e.id
            FROM events_v3 e
            WHERE e.date >= '2026-01-01' AND e.date < '2026-03-01'
              AND e.merged_into IS NULL
              AND e.source_batch_count >= %s
              AND NOT EXISTS (
                SELECT 1 FROM narratives n
                WHERE n.entity_type = 'event' AND n.entity_id = e.id
                  AND n.extraction_method = 'stance_clustered'
              )
            ORDER BY e.source_batch_count DESC
            """,
            (min_sources,),
        )
        rows = cur.fetchall()

    total = len(rows)
    if limit:
        rows = rows[:limit]

    print("Found %d eligible events (%d after limit)" % (total, len(rows)))
    extracted = 0
    skipped = 0
    errors = 0

    for i, row in enumerate(rows):
        eid = str(row["id"])
        print("\n[%d/%d] Event %s" % (i + 1, len(rows), eid))
        try:
            result = extract_stance_narratives(conn, "event", eid, dry_run=dry_run)
            if result:
                extracted += 1
                print(
                    "  -> %d clusters, %d narratives"
                    % (result["cluster_count"], result["narrative_count"])
                )
            else:
                skipped += 1
                print("  -> skipped")
        except Exception as e:
            errors += 1
            print("  -> ERROR: %s" % str(e)[:100])

    print("\n" + "=" * 50)
    print(
        "BATCH COMPLETE: %d extracted, %d skipped, %d errors (of %d)"
        % (extracted, skipped, errors, len(rows))
    )
    return extracted, skipped, errors


def main():
    parser = argparse.ArgumentParser(
        description="Extract stance-clustered narrative frames"
    )
    parser.add_argument(
        "--entity-type",
        choices=["event", "ctm"],
        help="Entity type (for single entity mode)",
    )
    parser.add_argument("--entity-id", help="Entity UUID (for single entity mode)")
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Batch mode: extract for all eligible events",
    )
    parser.add_argument(
        "--min-sources",
        type=int,
        default=30,
        help="Minimum source count for batch eligibility (default: 30)",
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Max events to process in batch mode"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show clusters and samples without calling LLM",
    )
    args = parser.parse_args()

    print("Stance-Clustered Narrative Extraction")
    print("=" * 50)

    conn = get_db_connection()

    if args.batch:
        batch_extract_events(
            conn, min_sources=args.min_sources, dry_run=args.dry_run, limit=args.limit
        )
    elif args.entity_type and args.entity_id:
        result = extract_stance_narratives(
            conn, args.entity_type, args.entity_id, dry_run=args.dry_run
        )
        if result:
            print(
                "\nResult: %d clusters, %d narratives"
                % (result["cluster_count"], result["narrative_count"])
            )
        else:
            print("\nNo extraction performed")
    else:
        parser.error("Either --batch or --entity-type + --entity-id required")

    conn.close()


if __name__ == "__main__":
    main()
