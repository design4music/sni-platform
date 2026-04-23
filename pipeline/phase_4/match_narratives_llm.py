"""
Phase 4.2g: LLM-based narrative matching for ideological narratives.

Narrative-centric: for each ideological narrative, gather candidate events
from its centroid, pre-filter by keyword overlap with matching_guidance,
then ask the LLM to pick the matches.

One LLM call per narrative (not per event). ~142 calls for full archive.
"""

import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import httpx
import psycopg2
from psycopg2.extras import Json, RealDictCursor, execute_values

from core.config import config
from core.llm_logger import log_llm_call
from core.llm_utils import check_rate_limit

# Minimum keyword overlap words to qualify an event as candidate
MIN_KEYWORD_OVERLAP = 2

SYSTEM_PROMPT = """You match news events to a strategic narrative.

A strategic narrative is a persistent claim by a political actor about how the world should work.
An event MATCHES when it directly advances, defends, or challenges the narrative's claim.

You will receive ONE narrative (with its claim, matching guidance, and example events)
and a numbered list of CANDIDATE events.

For each candidate, decide:
- YES if the event is genuinely relevant to this specific narrative's claim
- NO if the event merely involves the same country/region but is about something else

Be selective. Quality over quantity. When in doubt, say NO.

Return a JSON array of matches:
  [{"n": 3, "confidence": 0.8, "reason": "one sentence"}, ...]

where "n" is the event number from the list. Return [] if nothing matches.
Return ONLY valid JSON, no other text."""


def call_llm(system_prompt, user_prompt, max_tokens=2000):
    """Call LLM and return parsed JSON."""
    headers = {
        "Authorization": "Bearer %s" % config.deepseek_api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": max_tokens,
    }

    for attempt in range(config.llm_retry_attempts):
        try:
            t0 = time.time()
            with httpx.Client(timeout=config.llm_timeout_seconds) as client:
                response = client.post(
                    "%s/chat/completions" % config.deepseek_api_url,
                    headers=headers,
                    json=payload,
                )
                if check_rate_limit(response, attempt):
                    continue
                if response.status_code != 200:
                    raise RuntimeError(
                        "LLM error: %d %s" % (response.status_code, response.text[:200])
                    )

                data = response.json()
                log_llm_call(
                    "narrative_discovery",
                    data.get("usage"),
                    int((time.time() - t0) * 1000),
                )
                text = data["choices"][0]["message"]["content"].strip()
                if text.startswith("```"):
                    text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                return json.loads(text)
        except json.JSONDecodeError as e:
            print("  JSON parse error (attempt %d): %s" % (attempt + 1, e))
            if attempt == config.llm_retry_attempts - 1:
                return []
        except Exception as e:
            print("  LLM error (attempt %d): %s" % (attempt + 1, e))
            if attempt < config.llm_retry_attempts - 1:
                time.sleep(config.llm_retry_backoff**attempt)
            else:
                return []
    return []


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def parse_uuid_array(val):
    if not val or val == "{}":
        return []
    return val.strip("{}").split(",")


def load_narratives(cur):
    """Load ideological narratives with guidance and examples."""
    cur.execute(
        """
        SELECT sn.id, sn.name, sn.claim, sn.matching_guidance,
               sn.actor_centroid, sn.example_event_ids
        FROM strategic_narratives sn
        WHERE sn.is_active = true AND sn.tier = 'ideological'
          AND sn.matching_guidance IS NOT NULL
        ORDER BY sn.actor_centroid, sn.id
    """
    )
    narratives = cur.fetchall()

    # Pre-fetch example titles
    all_ids = []
    for n in narratives:
        n["_example_ids"] = parse_uuid_array(n["example_event_ids"] or "")
        all_ids.extend(n["_example_ids"])

    example_titles = {}
    if all_ids:
        cur.execute(
            "SELECT id, title FROM events_v3 WHERE id = ANY(%s::uuid[])", [all_ids]
        )
        for r in cur.fetchall():
            example_titles[str(r["id"])] = r["title"]

    for n in narratives:
        n["example_titles"] = [
            example_titles.get(eid, "")
            for eid in n["_example_ids"]
            if eid in example_titles
        ][:3]

    return narratives


def extract_guidance_words(guidance):
    """Extract meaningful words from matching_guidance for pre-filtering."""
    words = set()
    for w in re.findall(r"[a-zA-Z]{4,}", guidance.lower()):
        # Skip very common words
        if w not in {
            "that",
            "this",
            "with",
            "from",
            "have",
            "been",
            "their",
            "about",
            "which",
            "would",
            "other",
            "than",
            "into",
            "also",
            "more",
            "some",
            "when",
            "what",
            "such",
            "each",
            "between",
            "against",
            "through",
            "over",
            "under",
        }:
            words.add(w)
    return words


def fetch_centroid_events(cur, centroid_id, only_new=True):
    """Fetch all events from a centroid (optionally only LLM-unscored)."""
    where_new = ""
    if only_new:
        where_new = """
            AND NOT EXISTS (
                SELECT 1 FROM event_strategic_narratives esn
                WHERE esn.event_id = e.id
                AND esn.matched_signals->>'method' = 'llm'
            )"""
    cur.execute(
        """
        SELECT e.id AS event_id, e.title, e.summary, e.date::text as date
        FROM events_v3 e
        JOIN ctm c ON c.id = e.ctm_id
        WHERE c.centroid_id = %%s
          AND e.is_catchall = false
          AND e.merged_into IS NULL
          AND e.title IS NOT NULL
          %s
        ORDER BY e.date DESC
    """
        % where_new,
        (centroid_id,),
    )
    return cur.fetchall()


def pre_filter_events(events, guidance_words):
    """Filter events that have keyword overlap with narrative guidance."""
    candidates = []
    for ev in events:
        text = ((ev["title"] or "") + " " + (ev["summary"] or "")).lower()
        event_words = set(re.findall(r"[a-zA-Z]{4,}", text))
        overlap = guidance_words & event_words
        if len(overlap) >= MIN_KEYWORD_OVERLAP:
            candidates.append(ev)
    return candidates


def build_prompt(narrative, candidates):
    """Build prompt: one narrative, many candidate events."""
    lines = []
    lines.append("NARRATIVE: %s" % narrative["name"])
    lines.append("Claim: %s" % (narrative["claim"] or narrative["name"]))
    lines.append("Look for events about: %s" % narrative["matching_guidance"])
    if narrative["example_titles"]:
        lines.append("Examples of matching events:")
        for t in narrative["example_titles"]:
            lines.append("  - %s" % t)
    lines.append("")
    lines.append("CANDIDATE EVENTS (pick only genuinely relevant ones):")

    for i, ev in enumerate(candidates, 1):
        summary_snippet = ""
        if ev["summary"]:
            summary_snippet = " -- %s" % ev["summary"][:150]
        lines.append("%d. [%s] %s%s" % (i, ev["date"], ev["title"], summary_snippet))

    return "\n".join(lines)


def match_narratives_llm(only_new=True, dry_run=False, narrative_id=None):
    """Run LLM matching: one call per narrative with pre-filtered events."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            narratives = load_narratives(cur)
            if narrative_id:
                narratives = [n for n in narratives if n["id"] == narrative_id]
            if not narratives:
                print("No narratives to process")
                return 0

            print("Processing %d ideological narratives..." % len(narratives))

            total_links = 0
            total_calls = 0
            skipped = 0

            for nar in narratives:
                centroid = nar["actor_centroid"]
                guidance_words = extract_guidance_words(nar["matching_guidance"])

                # Fetch events from this centroid
                events = fetch_centroid_events(cur, centroid, only_new=only_new)
                if not events:
                    skipped += 1
                    continue

                # Pre-filter by keyword overlap
                candidates = pre_filter_events(events, guidance_words)
                if not candidates:
                    skipped += 1
                    continue

                # Cap at 80 candidates per call to stay within context limits
                candidates = candidates[:80]

                if dry_run:
                    print(
                        "  [DRY] %s: %d events -> %d candidates"
                        % (nar["id"], len(events), len(candidates))
                    )
                    total_calls += 1
                    continue

                prompt = build_prompt(nar, candidates)
                # Scale max_tokens with candidate count
                max_tok = min(4000, 200 + len(candidates) * 30)
                matches = call_llm(SYSTEM_PROMPT, prompt, max_tokens=max_tok)
                total_calls += 1

                if not matches:
                    if total_calls % 20 == 0:
                        print(
                            "  ...%d narratives processed, %d links"
                            % (total_calls, total_links)
                        )
                    continue

                # Map response numbers back to event IDs
                links = []
                for m in matches:
                    idx = m.get("n", 0) - 1  # 1-based to 0-based
                    conf = m.get("confidence", 0.7)
                    reason = m.get("reason", "")
                    if 0 <= idx < len(candidates) and conf >= 0.5:
                        ev = candidates[idx]
                        links.append(
                            (
                                ev["event_id"],
                                nar["id"],
                                round(conf, 2),
                                Json({"method": "llm", "reason": reason}),
                                ev["date"],
                            )
                        )

                if links:
                    execute_values(
                        cur,
                        """
                        INSERT INTO event_strategic_narratives
                            (event_id, narrative_id, confidence, matched_signals)
                        VALUES %s
                        ON CONFLICT (event_id, narrative_id)
                        DO UPDATE SET confidence = GREATEST(
                            event_strategic_narratives.confidence, EXCLUDED.confidence
                        ),
                        matched_signals = CASE
                            WHEN EXCLUDED.confidence > event_strategic_narratives.confidence
                            THEN EXCLUDED.matched_signals
                            ELSE event_strategic_narratives.matched_signals
                        END
                        """,
                        [(eid, nid, conf, sigs) for eid, nid, conf, sigs, _ in links],
                    )
                    # Update weekly activity
                    for eid, nid, conf, sigs, date in links:
                        cur.execute(
                            """
                            INSERT INTO narrative_weekly_activity (narrative_id, week, event_count)
                            VALUES (%s, date_trunc('week', %s::date)::date::text, 1)
                            ON CONFLICT (narrative_id, week)
                            DO UPDATE SET event_count = narrative_weekly_activity.event_count + 1
                        """,
                            (nid, date),
                        )

                    total_links += len(links)

                conn.commit()

                if total_calls % 20 == 0:
                    print(
                        "  ...%d narratives processed, %d links"
                        % (total_calls, total_links)
                    )

            print(
                "Done: %d LLM calls, %d skipped, %d new links"
                % (total_calls, skipped, total_links)
            )
            return total_links
    finally:
        conn.close()


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    full = "--full" in sys.argv  # process all events, not just new
    nid = None
    for arg in sys.argv:
        if arg.startswith("--narrative="):
            nid = arg.split("=", 1)[1]
    match_narratives_llm(only_new=not full, dry_run=dry, narrative_id=nid)
