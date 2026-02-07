"""
RAI Analysis for Epic Narratives (Phase 6)
Sends narrative frames to RAI service for adequacy, conflicts, and blind spot analysis.
"""

import argparse
import json
import re
import sys
import time

import httpx
import psycopg2
from psycopg2.extras import RealDictCursor

# Windows console encoding fix
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Load config
sys.path.insert(0, str(__file__).replace("\\", "/").rsplit("/", 3)[0])
from core.config import get_config  # noqa: E402

config = get_config()

RAI_API_URL = config.rai_api_url
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


def fetch_narratives_for_rai(conn, epic_slug=None, limit=50):
    """Fetch narratives that need RAI analysis."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        if epic_slug:
            cur.execute(
                """
                SELECT n.id, n.epic_id, n.label, n.description, n.moral_frame,
                       n.title_count, n.top_sources, n.sample_titles,
                       e.title as epic_title, e.summary as epic_summary
                FROM epic_narratives n
                JOIN epics e ON n.epic_id = e.id
                WHERE e.slug = %s
                  AND n.rai_analyzed_at IS NULL
                ORDER BY n.title_count DESC
                LIMIT %s
            """,
                (epic_slug, limit),
            )
        else:
            cur.execute(
                """
                SELECT n.id, n.epic_id, n.label, n.description, n.moral_frame,
                       n.title_count, n.top_sources, n.sample_titles,
                       e.title as epic_title, e.summary as epic_summary
                FROM epic_narratives n
                JOIN epics e ON n.epic_id = e.id
                WHERE n.rai_analyzed_at IS NULL
                ORDER BY n.title_count DESC
                LIMIT %s
            """,
                (limit,),
            )
        return cur.fetchall()


def build_rai_payload(narrative):
    """Build RAI API request payload from narrative data."""
    # Title is just the narrative frame - don't dilute with factual epic title
    title = narrative["label"]

    # Summary provides the moral frame and context
    summary_parts = []
    if narrative["moral_frame"]:
        summary_parts.append(narrative["moral_frame"])
    if narrative["description"]:
        summary_parts.append(narrative["description"])
    # Epic context as background, not primary focus
    if narrative["epic_summary"]:
        summary_parts.append(f"Context: {narrative['epic_summary']}")
    if narrative["top_sources"]:
        summary_parts.append(f"Top Sources: {', '.join(narrative['top_sources'][:5])}")

    summary = "\n\n".join(summary_parts)

    # Excerpts from sample titles
    excerpts = []
    if narrative["sample_titles"]:
        samples = narrative["sample_titles"]
        if isinstance(samples, str):
            samples = json.loads(samples)
        for s in samples[:10]:
            if isinstance(s, dict):
                excerpts.append(s.get("title", ""))
            else:
                excerpts.append(str(s))

    return {
        "content": {
            "title": title,
            "summary": summary,
            "excerpts": excerpts,
        },
        "analysis_type": "guided",
    }


def extract_blind_spots(full_analysis):
    """Extract blind spots from RAI analysis HTML."""
    blind_spots = []

    # Look for blind spots section
    if "Blind Spot" in full_analysis or "blind spot" in full_analysis:
        # Extract numbered list items after blind spots mention
        patterns = [
            r"Blind Spots[^<]*</strong>:?\s*[^<]*<ol[^>]*>(.*?)</ol>",
            r"blind spots[^<]*:([^<]+(?:<li[^>]*>[^<]+</li>)+)",
            r"cannot process[^<]*:?\s*<[ou]l[^>]*>(.*?)</[ou]l>",
        ]

        for pattern in patterns:
            match = re.search(pattern, full_analysis, re.IGNORECASE | re.DOTALL)
            if match:
                items = re.findall(r"<li[^>]*>([^<]+)</li>", match.group(1))
                for item in items:
                    # Clean up the text
                    clean = re.sub(r"<[^>]+>", "", item).strip()
                    clean = re.sub(r"\s+", " ", clean)
                    if clean and len(clean) > 10:
                        blind_spots.append(clean[:500])
                break

    return blind_spots[:5]  # Max 5 blind spots


def extract_conflicts(full_analysis):
    """Extract conflicts/tensions from RAI analysis."""
    conflicts = []

    # Look for conflict-related sections
    keywords = ["conflict", "tension", "contradiction", "competing", "alternative"]

    for keyword in keywords:
        if keyword in full_analysis.lower():
            # Find sentences containing the keyword
            sentences = re.split(r"[.!?]", full_analysis)
            for sent in sentences:
                if keyword in sent.lower() and len(sent) > 50:
                    clean = re.sub(r"<[^>]+>", "", sent).strip()
                    clean = re.sub(r"\s+", " ", clean)
                    if clean and len(clean) > 30:
                        conflicts.append(clean[:300])
                        if len(conflicts) >= 3:
                            break
            if conflicts:
                break

    return conflicts[:3]


def extract_synthesis(full_analysis):
    """Extract synthesis/conclusion from RAI analysis."""
    # Look for synthesis or conclusion section
    patterns = [
        r"Synthesis[^<]*</h1>\s*<p[^>]*>([^<]+)</p>",
        r"Conclusion[^<]*</h1>\s*<p[^>]*>([^<]+)</p>",
        r"Final Judgment[^<]*:</strong>\s*([^<]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, full_analysis, re.IGNORECASE)
        if match:
            text = match.group(1).strip()
            text = re.sub(r"<[^>]+>", "", text)
            text = re.sub(r"\s+", " ", text)
            return text[:1000]

    return None


def call_rai_api(payload):
    """Call RAI API and return response."""
    try:
        with httpx.Client(timeout=RAI_TIMEOUT) as client:
            response = client.post(
                RAI_API_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {RAI_API_KEY}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code != 200:
                print(
                    f"  RAI API error: {response.status_code} - {response.text[:200]}"
                )
                return None

            return response.json()

    except httpx.TimeoutException:
        print(f"  RAI API timeout (>{RAI_TIMEOUT}s)")
        return None
    except Exception as e:
        print(f"  RAI API error: {e}")
        return None


def process_rai_response(rai_result):
    """Process RAI response into database fields."""
    if not rai_result:
        return None

    # Extract adequacy score
    adequacy = rai_result.get("overall_score") or rai_result.get("credibility", {}).get(
        "score"
    )

    # Extract full analysis (complete HTML report)
    full_analysis = rai_result.get("full_analysis", "")

    # Extract synthesis
    synthesis = extract_synthesis(full_analysis)

    # Extract blind spots
    blind_spots = extract_blind_spots(full_analysis)

    # Extract conflicts
    conflicts = extract_conflicts(full_analysis)

    # Build shifts object with all scores
    shifts = {
        "overall_score": rai_result.get("overall_score"),
        "bias_score": rai_result.get("bias", {}).get("score"),
        "coherence_score": rai_result.get("coherence", {}).get("score"),
        "credibility_score": rai_result.get("credibility", {}).get("score"),
        "evidence_quality": rai_result.get("evidence", {}).get("quality"),
        "relevance_score": rai_result.get("relevance", {}).get("score"),
        "safety_score": rai_result.get("safety", {}).get("score"),
        "recommendations": rai_result.get("recommendations", []),
        "violations": rai_result.get("violations", []),
    }

    return {
        "adequacy": adequacy,
        "synthesis": synthesis,
        "conflicts": conflicts,
        "blind_spots": blind_spots,
        "shifts": shifts,
        "full_analysis": full_analysis,
    }


def save_rai_analysis(conn, narrative_id, rai_data):
    """Save RAI analysis to database."""
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE epic_narratives
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
    parser = argparse.ArgumentParser(description="RAI analysis for epic narratives")
    parser.add_argument("--epic", type=str, help="Process specific epic by slug")
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

    print("RAI Narrative Analysis (Phase 6)")
    print("=" * 50)

    conn = get_db_connection()

    # Fetch narratives
    narratives = fetch_narratives_for_rai(conn, args.epic, args.limit)
    print(f"Found {len(narratives)} narratives pending RAI analysis")

    if not narratives:
        print("Nothing to process")
        return

    if args.dry_run:
        print("\nDry run - would process:")
        for n in narratives:
            print(
                f"  - {n['label']} ({n['title_count']} titles) from {n['epic_title']}"
            )
        return

    # Process each narrative
    stats = {"success": 0, "failed": 0}

    for i, narrative in enumerate(narratives, 1):
        print(f"\n[{i}/{len(narratives)}] {narrative['label']}")
        print(f"  Epic: {narrative['epic_title']}")
        print(f"  Titles: {narrative['title_count']}")

        # Build payload
        payload = build_rai_payload(narrative)

        # Call RAI API
        print("  Calling RAI API...")
        rai_result = call_rai_api(payload)

        if not rai_result:
            stats["failed"] += 1
            continue

        # Process response
        rai_data = process_rai_response(rai_result)

        if not rai_data:
            stats["failed"] += 1
            continue

        # Save to database
        save_rai_analysis(conn, narrative["id"], rai_data)

        print(f"  Adequacy: {rai_data['adequacy']}")
        print(f"  Blind spots: {len(rai_data['blind_spots'])}")
        print(f"  Conflicts: {len(rai_data['conflicts'])}")
        if rai_data["synthesis"]:
            print(f"  Synthesis: {rai_data['synthesis'][:100]}...")

        stats["success"] += 1

        # Delay between calls
        if i < len(narratives):
            time.sleep(args.delay)

    print("\n" + "=" * 50)
    print(f"Complete: {stats['success']} success, {stats['failed']} failed")

    conn.close()


if __name__ == "__main__":
    main()
