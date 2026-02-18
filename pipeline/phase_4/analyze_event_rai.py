"""
RAI Signal Analysis for Narratives

Processes both event and CTM narratives through the two-tier signal architecture:
  - Tier 1: compute hard stats locally (no LLM)
  - Tier 2: send stats to RAI for compact JSON interpretation

Modes:
  - Signals (default): compact, data-driven signals via /worldbrief/signals
  - Full (--full):      full HTML analysis via /worldbrief/analyze (legacy, events only)

Usage:
    python pipeline/phase_4/analyze_event_rai.py --limit 10
    python pipeline/phase_4/analyze_event_rai.py --entity-type ctm --limit 5
    python pipeline/phase_4/analyze_event_rai.py --event <UUID>
    python pipeline/phase_4/analyze_event_rai.py --full --limit 5
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
from core.signal_stats import compute_ctm_stats, compute_event_stats  # noqa: E402

config = get_config()

RAI_FULL_URL = config.rai_worldbrief_url
RAI_SIGNALS_URL = config.rai_signals_url
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


def fetch_narratives(conn, entity_type, limit=50, entity_id=None, mode="signals"):
    """Fetch narratives that need RAI analysis."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        if mode == "signals":
            where = "n.entity_type = %s AND n.rai_signals_at IS NULL"
        else:
            where = "n.entity_type = %s AND n.rai_analyzed_at IS NULL"
        params = [entity_type]

        if entity_id:
            where += " AND n.entity_id = %s"
            params.append(entity_id)

        params.append(limit)

        if entity_type == "event":
            cur.execute(
                """
                SELECT n.id, n.entity_type, n.entity_id, n.label, n.description,
                       n.moral_frame, n.title_count, n.top_sources, n.sample_titles,
                       e.title as context_title, e.summary as context_summary,
                       e.source_batch_count,
                       c.centroid_id, c.track
                FROM narratives n
                JOIN events_v3 e ON n.entity_id = e.id
                JOIN ctm c ON c.id = e.ctm_id
                WHERE """
                + where
                + """
                ORDER BY n.title_count DESC
                LIMIT %s
                """,
                params,
            )
        else:
            # CTM narratives
            cur.execute(
                """
                SELECT n.id, n.entity_type, n.entity_id, n.label, n.description,
                       n.moral_frame, n.title_count, n.top_sources, n.sample_titles,
                       c.summary_text as context_title,
                       c.summary_text as context_summary,
                       c.title_count as source_batch_count,
                       c.centroid_id, c.track
                FROM narratives n
                JOIN ctm c ON n.entity_id = c.id
                WHERE """
                + where
                + """
                ORDER BY n.title_count DESC
                LIMIT %s
                """,
                params,
            )
        return cur.fetchall()


# =========================================================================
# Signals path (default)
# =========================================================================


def build_signals_payload(narrative, stats):
    """Build payload for /worldbrief/signals endpoint."""
    sample_titles = narrative["sample_titles"]
    if isinstance(sample_titles, str):
        sample_titles = json.loads(sample_titles)

    context_title = narrative.get("context_title") or ""
    if len(context_title) > 200:
        context_title = context_title[:200] + "..."

    return {
        "content_type": "%s_narrative" % narrative["entity_type"],
        "narrative": {
            "label": narrative["label"],
            "moral_frame": narrative.get("moral_frame"),
            "description": narrative.get("description"),
            "sample_titles": sample_titles or [],
        },
        "context": {
            "centroid_id": narrative.get("centroid_id", ""),
            "track": narrative.get("track", ""),
            "event_title": context_title,
        },
        "stats": stats,
    }


def call_signals_api(payload):
    """Call /worldbrief/signals and return response."""
    try:
        with httpx.Client(timeout=RAI_TIMEOUT) as client:
            response = client.post(
                RAI_SIGNALS_URL,
                json=payload,
                headers={
                    "Authorization": "Bearer %s" % RAI_API_KEY,
                    "Content_Type": "application/json",
                },
            )
            if response.status_code != 200:
                print(
                    "  Signals API error: %d - %s"
                    % (response.status_code, response.text[:200])
                )
                return None
            return response.json()
    except httpx.TimeoutException:
        print("  Signals API timeout (>%ds)" % RAI_TIMEOUT)
        return None
    except Exception as e:
        print("  Signals API error: %s" % e)
        return None


def save_signals(conn, narrative_id, stats, signals_result):
    """Save Tier 1 stats and Tier 2 signals to narratives."""
    signals = signals_result.get("signals", {})
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE narratives
            SET signal_stats = %s,
                rai_signals = %s,
                rai_signals_at = NOW()
            WHERE id = %s
            """,
            (json.dumps(stats), json.dumps(signals), narrative_id),
        )
    conn.commit()


def run_signals(conn, narratives, delay):
    """Process narratives through the signals path."""
    counts = {"success": 0, "failed": 0}

    for i, narrative in enumerate(narratives, 1):
        etype = narrative["entity_type"]
        print("\n[%d/%d] [%s] %s" % (i, len(narratives), etype, narrative["label"]))
        ctx = narrative.get("context_title") or ""
        if ctx:
            print("  Context: %s" % ctx[:80])
        print("  Titles: %d" % narrative["title_count"])

        # Tier 1: compute stats locally
        print("  Computing stats...")
        if etype == "event":
            stats = compute_event_stats(conn, narrative["entity_id"])
        else:
            stats = compute_ctm_stats(conn, narrative["entity_id"])

        if not stats:
            print("  No titles found, skipping")
            counts["failed"] += 1
            continue
        print(
            "  Stats: %d titles, %d publishers (HHI %.3f), %d languages"
            % (
                stats["title_count"],
                stats["publisher_count"],
                stats["publisher_hhi"],
                stats["language_count"],
            )
        )

        # Save Tier 1 stats immediately
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE narratives SET signal_stats = %s WHERE id = %s",
                (json.dumps(stats), narrative["id"]),
            )
        conn.commit()

        # Tier 2: call RAI signals endpoint
        payload = build_signals_payload(narrative, stats)
        print("  Calling RAI signals API...")
        result = call_signals_api(payload)

        if not result:
            counts["failed"] += 1
            continue

        save_signals(conn, narrative["id"], stats, result)

        signals = result.get("signals", {})
        print("  Adequacy: %s" % signals.get("adequacy", "N/A"))
        print("  Source concentration: %s" % signals.get("source_concentration", "N/A"))
        findings = signals.get("findings", [])
        if findings:
            print("  Findings: %s" % findings[0][:80])

        counts["success"] += 1

        if i < len(narratives):
            time.sleep(delay)

    return counts


# =========================================================================
# Full analysis path (--full, legacy)
# =========================================================================


def build_full_payload(narrative):
    """Build WorldBrief RAI API request payload (legacy full analysis)."""
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
            "event_title": narrative.get("context_title", ""),
        },
    }


def call_full_api(payload):
    """Call /worldbrief/analyze and return response."""
    try:
        with httpx.Client(timeout=RAI_TIMEOUT) as client:
            response = client.post(
                RAI_FULL_URL,
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


def save_full_analysis(conn, narrative_id, rai_result):
    """Save full RAI analysis to narratives table."""
    scores = rai_result.get("scores", {})
    rai_data = {
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
    return rai_data


def run_full(conn, narratives, delay):
    """Process narratives through the full analysis path."""
    counts = {"success": 0, "failed": 0}

    for i, narrative in enumerate(narratives, 1):
        print("\n[%d/%d] %s" % (i, len(narratives), narrative["label"]))
        print("  Event: %s" % narrative.get("context_title", ""))
        print("  Titles: %d" % narrative["title_count"])

        payload = build_full_payload(narrative)
        print("  Calling RAI full analysis API...")
        rai_result = call_full_api(payload)

        if not rai_result:
            counts["failed"] += 1
            continue

        rai_data = save_full_analysis(conn, narrative["id"], rai_result)

        print("  Adequacy: %s" % rai_data["adequacy"])
        print("  Blind spots: %d" % len(rai_data["blind_spots"]))
        if rai_data["synthesis"]:
            print("  Synthesis: %s..." % rai_data["synthesis"][:100])

        counts["success"] += 1

        if i < len(narratives):
            time.sleep(delay)

    return counts


# =========================================================================
# Daemon callable
# =========================================================================


def process_rai_signals(limit=20, delay=2.0):
    """Daemon-callable entry point. Runs signals for both event + CTM narratives."""
    conn = get_db_connection()
    total = {"success": 0, "failed": 0}

    for etype in ("event", "ctm"):
        narratives = fetch_narratives(conn, etype, limit=limit)
        if narratives:
            print("%s narratives: %d pending RAI signals" % (etype, len(narratives)))
            r = run_signals(conn, narratives, delay)
            total["success"] += r["success"]
            total["failed"] += r["failed"]

    if total["success"] == 0 and total["failed"] == 0:
        print("No narratives need RAI signal analysis")

    conn.close()
    return total


# =========================================================================
# Main
# =========================================================================


def main():
    parser = argparse.ArgumentParser(description="RAI analysis for narratives")
    parser.add_argument("--event", type=str, help="Process specific event by ID")
    parser.add_argument(
        "--entity-type",
        type=str,
        default="event",
        choices=["event", "ctm"],
        help="Entity type to process",
    )
    parser.add_argument(
        "--limit", type=int, default=10, help="Max narratives to process"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be processed"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Use full analysis (legacy) instead of signals",
    )
    parser.add_argument(
        "--delay", type=float, default=2.0, help="Delay between API calls (seconds)"
    )
    args = parser.parse_args()

    mode = "full" if args.full else "signals"
    etype = args.entity_type
    print("RAI Narrative Analysis [%s mode, %s]" % (mode, etype))
    print("=" * 50)

    conn = get_db_connection()

    narratives = fetch_narratives(conn, etype, args.limit, args.event, mode)
    print("Found %d %s narratives pending RAI analysis" % (len(narratives), etype))

    if not narratives:
        print("Nothing to process")
        conn.close()
        return

    if args.dry_run:
        print("\nDry run - would process:")
        for n in narratives:
            ctx = n.get("context_title") or ""
            print("  - %s (%d titles) %s" % (n["label"], n["title_count"], ctx[:60]))
        conn.close()
        return

    if mode == "signals":
        counts = run_signals(conn, narratives, args.delay)
    else:
        counts = run_full(conn, narratives, args.delay)

    print("\n" + "=" * 50)
    print("Complete: %d success, %d failed" % (counts["success"], counts["failed"]))

    conn.close()


if __name__ == "__main__":
    main()
