"""
RAI Analysis for Event Narratives

Sends event narrative frames to the WorldBrief RAI endpoint for philosophical
analysis of adequacy, conflicts, blind spots, and synthesis.
Uses structured JSON scores (no HTML regex parsing).
"""

import argparse
import json
import sys
import time

import httpx
import psycopg2
from psycopg2.extras import RealDictCursor

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(__file__).replace("\\", "/").rsplit("/", 3)[0])
from core.config import get_config  # noqa: E402

config = get_config()

RAI_URL = config.rai_worldbrief_url
RAI_API_KEY = config.rai_api_key
RAI_TIMEOUT = getattr(config, "rai_timeout_seconds", 300)


def get_db_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        dbname=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def fetch_narratives_for_rai(conn, limit=50, event_id=None):
    """Fetch event narratives that need RAI analysis."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        where = "en.entity_type = 'event' AND en.rai_analyzed_at IS NULL"
        params = []

        if event_id:
            where += " AND en.entity_id = %s"
            params.append(event_id)

        params.append(limit)
        cur.execute(
            """
            SELECT en.id, en.entity_id as event_id, en.label, en.description, en.moral_frame,
                   en.title_count, en.top_sources, en.sample_titles,
                   e.title as event_title, e.summary as event_summary,
                   e.source_batch_count,
                   c.centroid_id, c.track
            FROM narratives en
            JOIN events_v3 e ON en.entity_id = e.id
            JOIN ctm c ON c.id = e.ctm_id
            WHERE """
            + where
            + """
            ORDER BY en.title_count DESC
            LIMIT %s
        """,
            params,
        )
        return cur.fetchall()


def build_rai_payload(narrative):
    """Build WorldBrief RAI API request payload."""
    sample_titles = narrative["sample_titles"]
    if isinstance(sample_titles, str):
        sample_titles = json.loads(sample_titles)

    return {
        "content_type": "event_narrative",
        "narrative": {
            "label": narrative["label"],
            "moral_frame": narrative.get("moral_frame"),
            "description": narrative.get("description"),
            "sample_titles": sample_titles or [],
            "source_count": narrative.get("source_batch_count", 0),
            "top_sources": narrative.get("top_sources") or [],
        },
        "context": {
            "centroid_id": narrative.get("centroid_id", ""),
            "track": narrative.get("track", ""),
            "event_title": narrative.get("event_title", ""),
        },
    }


def call_rai_api(payload):
    """Call WorldBrief RAI API and return response."""
    try:
        with httpx.Client(timeout=RAI_TIMEOUT) as client:
            response = client.post(
                RAI_URL,
                json=payload,
                headers={
                    "Authorization": "Bearer %s" % RAI_API_KEY,
                    "Content-Type": "application/json",
                },
            )

            if response.status_code != 200:
                print(
                    "  RAI API error: %d - %s"
                    % (response.status_code, response.text[:200])
                )
                return None

            return response.json()

    except httpx.TimeoutException:
        print("  RAI API timeout (>%ds)" % RAI_TIMEOUT)
        return None
    except Exception as e:
        print("  RAI API error: %s" % e)
        return None


def process_rai_response(rai_result):
    """Process structured RAI response into database fields."""
    if not rai_result:
        return None

    scores = rai_result.get("scores", {})

    return {
        "adequacy": scores.get("adequacy"),
        "synthesis": scores.get("synthesis"),
        "conflicts": scores.get("conflicts") or [],
        "blind_spots": scores.get("blind_spots") or [],
        "shifts": {
            "adequacy": scores.get("adequacy"),
            "bias_detected": scores.get("bias_detected"),
            "coherence": scores.get("coherence"),
            "evidence_quality": scores.get("evidence_quality"),
        },
        "full_analysis": rai_result.get("full_analysis", ""),
    }


def save_rai_analysis(conn, narrative_id, rai_data):
    """Save RAI analysis to narratives table."""
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE narratives
            SET rai_adequacy = %s,
                rai_synthesis = %s,
                rai_conflicts = %s,
                rai_blind_spots = %s,
                rai_shifts = %s,
                rai_full_analysis = %s,
                rai_analyzed_at = NOW()
            WHERE id = %s
        """,
            (
                rai_data["adequacy"],
                rai_data["synthesis"],
                rai_data["conflicts"] if rai_data["conflicts"] else None,
                rai_data["blind_spots"] if rai_data["blind_spots"] else None,
                json.dumps(rai_data["shifts"]),
                rai_data.get("full_analysis"),
                narrative_id,
            ),
        )
    conn.commit()


def main():
    parser = argparse.ArgumentParser(description="RAI analysis for event narratives")
    parser.add_argument("--event", type=str, help="Process specific event by ID")
    parser.add_argument(
        "--limit", type=int, default=10, help="Max narratives to process"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be processed"
    )
    parser.add_argument(
        "--delay", type=float, default=2.0, help="Delay between API calls (seconds)"
    )
    args = parser.parse_args()

    print("RAI Event Narrative Analysis")
    print("=" * 50)

    conn = get_db_connection()

    narratives = fetch_narratives_for_rai(conn, args.limit, args.event)
    print("Found %d event narratives pending RAI analysis" % len(narratives))

    if not narratives:
        print("Nothing to process")
        conn.close()
        return

    if args.dry_run:
        print("\nDry run - would process:")
        for n in narratives:
            print(
                "  - %s (%d titles) from event: %s"
                % (n["label"], n["title_count"], n["event_title"])
            )
        conn.close()
        return

    stats = {"success": 0, "failed": 0}

    for i, narrative in enumerate(narratives, 1):
        print("\n[%d/%d] %s" % (i, len(narratives), narrative["label"]))
        print("  Event: %s" % narrative["event_title"])
        print("  Titles: %d" % narrative["title_count"])

        payload = build_rai_payload(narrative)

        print("  Calling RAI API...")
        rai_result = call_rai_api(payload)

        if not rai_result:
            stats["failed"] += 1
            continue

        rai_data = process_rai_response(rai_result)

        if not rai_data:
            stats["failed"] += 1
            continue

        save_rai_analysis(conn, narrative["id"], rai_data)

        print("  Adequacy: %s" % rai_data["adequacy"])
        print("  Blind spots: %d" % len(rai_data["blind_spots"]))
        print("  Conflicts: %d" % len(rai_data["conflicts"]))
        if rai_data["synthesis"]:
            print("  Synthesis: %s..." % rai_data["synthesis"][:100])

        stats["success"] += 1

        if i < len(narratives):
            time.sleep(args.delay)

    print("\n" + "=" * 50)
    print("Complete: %d success, %d failed" % (stats["success"], stats["failed"]))

    conn.close()


if __name__ == "__main__":
    main()
