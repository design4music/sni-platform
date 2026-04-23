"""Phase 5.5 — Centroid period summaries (bilingual EN+DE).

Produces a state-of-play brief per centroid covering a rolling 30-day window
(daemon refresh) or a monthly window (month-freeze snapshot). Three tiers:

  tier=1  FULL    Tier 0 headline + 4 track paragraphs, bilingual
  tier=2  LIGHT   Tier 0 headline only; track paragraphs omitted
  tier=3  CANNED  Pure static message, no LLM call

See db/migrations/20260420_add_centroid_summaries.sql for schema.
"""

import asyncio
import hashlib
import json
import time
from datetime import date, timedelta

import httpx
import psycopg2

from core.config import config
from core.llm_logger import log_llm_call
from core.llm_utils import async_check_rate_limit, extract_json, fix_role_hallucinations

# Tier thresholds
TIER1_MIN_TOTAL_EVENTS = 20
TIER1_MIN_STRONG_TRACKS = 3  # tracks with >= 5 events
TIER2_MIN_TOTAL_EVENTS = 5
TRACK_STRONG_THRESHOLD = 5

# Canned text for tier 3 (bilingual)
TIER3_OVERALL_EN = "Coverage limited for this period — see individual events below."
TIER3_OVERALL_DE = (
    "Begrenzte Berichterstattung in diesem Zeitraum — siehe einzelne Ereignisse unten."
)

TRACKS = ["geo_economy", "geo_politics", "geo_security", "geo_society"]
TRACK_JSON_KEY = {
    "geo_economy": "economy",
    "geo_politics": "politics",
    "geo_security": "security",
    "geo_society": "society",
}


def get_conn():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


# ---------------------------------------------------------------------------
# Data fetch
# ---------------------------------------------------------------------------


def fetch_top_events(
    cur, centroid_id: str, end_date: date, days_back: int = 30
) -> dict:
    """Top 10 events per track for the rolling window ending on end_date."""
    start_date = end_date - timedelta(days=days_back - 1)
    cur.execute(
        """WITH ranked AS (
             SELECT c.track, e.id::text AS id, e.title, e.source_batch_count,
                    e.date::text AS date,
                    ROW_NUMBER() OVER (
                      PARTITION BY c.track
                      ORDER BY e.source_batch_count DESC, e.date DESC
                    ) AS rnk
               FROM events_v3 e JOIN ctm c ON c.id = e.ctm_id
              WHERE c.centroid_id = %s AND e.is_promoted = true
                AND e.merged_into IS NULL
                AND e.date BETWEEN %s AND %s
           )
           SELECT track, id, title, source_batch_count, date
             FROM ranked WHERE rnk <= 10
            ORDER BY track, rnk""",
        (centroid_id, start_date, end_date),
    )
    by_track = {t: [] for t in TRACKS}
    for row in cur.fetchall():
        if row[0] in by_track:
            by_track[row[0]].append(
                {"id": row[1], "title": row[2], "source_count": row[3], "date": row[4]}
            )
    return by_track


def fetch_ambient_context(
    cur, centroid_id: str, end_date: date, days_back: int = 30
) -> dict:
    start_date = end_date - timedelta(days=days_back - 1)
    cur.execute(
        """SELECT COUNT(DISTINCT ta.title_id)
             FROM title_assignments ta
             JOIN ctm c ON c.id = ta.ctm_id
             JOIN titles_v3 t ON t.id = ta.title_id
            WHERE c.centroid_id = %s AND t.pubdate_utc BETWEEN %s AND %s""",
        (centroid_id, start_date, end_date),
    )
    total = cur.fetchone()[0] or 0
    ubiquity = max(1, int(total * 0.8))

    def top(lateral: str, limit: int = 10) -> list:
        cur.execute(
            f"""SELECT e AS name, COUNT(DISTINCT tl.title_id) AS n
                  FROM title_labels tl
                  JOIN title_assignments ta ON ta.title_id = tl.title_id
                  JOIN ctm c ON c.id = ta.ctm_id
                  JOIN titles_v3 t ON t.id = tl.title_id
                  {lateral}
                 WHERE c.centroid_id = %s
                   AND t.pubdate_utc BETWEEN %s AND %s
                   AND tl.label_version = 'ELO_v3.0.1'
                 GROUP BY e
                 HAVING COUNT(DISTINCT tl.title_id) < %s
                 ORDER BY n DESC LIMIT %s""",
            (centroid_id, start_date, end_date, ubiquity, limit),
        )
        return [{"name": r[0], "count": r[1]} for r in cur.fetchall()]

    return {
        "total_titles": total,
        "persons": top("CROSS JOIN LATERAL unnest(tl.persons) AS e"),
        "orgs": top("CROSS JOIN LATERAL unnest(tl.orgs) AS e"),
        "countries": top(
            "CROSS JOIN LATERAL jsonb_each_text(tl.entity_countries) AS ec(_n, e)"
        ),
        "places": top("CROSS JOIN LATERAL unnest(tl.places) AS e"),
    }


# ---------------------------------------------------------------------------
# Tier classification
# ---------------------------------------------------------------------------


def classify_tier(events_by_track: dict) -> int:
    """Return 1 (full), 2 (light), or 3 (canned)."""
    total = sum(len(v) for v in events_by_track.values())
    strong_tracks = sum(
        1 for v in events_by_track.values() if len(v) >= TRACK_STRONG_THRESHOLD
    )

    if total >= TIER1_MIN_TOTAL_EVENTS and strong_tracks >= TIER1_MIN_STRONG_TRACKS:
        return 1
    if total >= TIER2_MIN_TOTAL_EVENTS:
        return 2
    return 3


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------


SYSTEM_PROMPT_TIER1 = """You are a strategic intelligence analyst writing a concise "state of play" brief for a specific country or entity, covering a rolling 30-day period. You produce bilingual output (English + German) in one call.

Produce JSON with this exact structure:
{
  "overall_en": "1-2 sentence headline capturing the dominant tension or trajectory across all domains. Name actors and substance.",
  "overall_de": "Same content in German.",
  "economy":  { "state_en": "...", "state_de": "...", "supporting_events": ["id1","id2"] },
  "politics": { "state_en": "...", "state_de": "...", "supporting_events": [...] },
  "security": { "state_en": "...", "state_de": "...", "supporting_events": [...] },
  "society":  { "state_en": "...", "state_de": "...", "supporting_events": [...] }
}

Each track's state is 2-3 sentences that:
- LEAD with the current state as a concrete observation. Good: "Economy is in stagnation." Bad: "Economic situation is complex."
- SUPPORT the lead with specific developments from the provided events.

CONSTRAINTS:
- Cite 1-3 specific events per track via their 8-char ID prefixes in supporting_events. DO NOT INVENT events, numbers, or dates not in the provided list.
- Tier 0 overall synthesizes ALL FOUR tracks; it names 2+ concrete actors or forces.
- When AMBIENT CONTEXT shows multiple prominent actors, NAME at least 2-3 beyond the head of government where relevant.
- Write in direct, reportorial English/German. Subject-verb-object. No hedging.
- For a track with fewer than 3 events provided, keep the paragraph brief (1 sentence) and note ambient signals only if they are clear.

ROLE / TITLE RULES (CRITICAL):
- You may restate a role or title ONLY if it appears verbatim in a provided event title.
- You may NOT assign roles from your own knowledge. If an entity appears only as a bare name in the data, use only the bare name.
- NEVER call anyone "former X" unless the event explicitly says so.
- When in doubt, drop the title.

BACKGROUND CONTEXT:
- If AMBIENT CONTEXT shows a foreign country or recurring topic persistently present but no discrete events lead the period, you MAY acknowledge it as background in one clause, without inventing specifics. Example: "Russia-Ukraine war persists as coverage backdrop without major developments this period."

SOCIETY PARAGRAPH:
- Name ONE dominant tension and describe its current phase. Don't list unrelated items as equal.

FORBIDDEN PHRASES (never use):
- "turbulent times", "challenging period", "complex situation", "uncertainty persists"
- "ongoing tensions", "dynamic landscape", "evolving circumstances"
- "faces [X]", "navigates [Y]", "grapples with [Y]"
- "balance between", "dual-track", generic "pivot"

Do NOT project from pre-2026 background knowledge. Stick to the provided material.

Output ONLY the JSON object. No preamble."""


SYSTEM_PROMPT_TIER2 = """You are a strategic intelligence analyst writing a brief "state of play" headline for a country/entity covering a rolling 30-day period with LIMITED coverage. Produce bilingual output (English + German).

Produce JSON:
{
  "overall_en": "1-2 sentence headline. Name the most salient actor or event in the period. If the period is too thin for a confident synthesis, say so briefly.",
  "overall_de": "Same in German."
}

CONSTRAINTS:
- Ground in the provided events. Do NOT invent.
- Roles only if in event titles verbatim.
- No forbidden phrases ("faces / navigates / grapples / turbulent / complex / uncertainty persists / dual-track / pivot as generic").

Output ONLY the JSON object."""


def _fmt_events_block(events_by_track: dict) -> str:
    sections = []
    for track in TRACKS:
        evs = events_by_track.get(track, [])
        label = track.replace("geo_", "").upper()
        if not evs:
            sections.append(f"{label}: (no events this period)")
            continue
        lines = [f"{label} ({len(evs)} events):"]
        for e in evs:
            lines.append(
                f'  {e["source_count"]} src | {e["date"]} | {e["title"]} | id={e["id"][:8]}'
            )
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


def _fmt_ambient_block(ambient: dict) -> str:
    def f(label: str, items: list) -> str:
        if not items:
            return f"  {label}: (none)"
        return f"  {label}: " + ", ".join(f"{i['name']}({i['count']})" for i in items)

    return (
        f"AMBIENT CONTEXT ({ambient['total_titles']} total titles this period):\n"
        + f(" Persons", ambient["persons"])
        + "\n"
        + f(" Orgs", ambient["orgs"])
        + "\n"
        + f(" Countries", ambient["countries"])
        + "\n"
        + f(" Places", ambient["places"])
    )


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------


async def _call_llm(system_prompt: str, user_prompt: str, max_tokens: int) -> dict:
    headers = {
        "Authorization": f"Bearer {config.deepseek_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": max_tokens,
    }
    async with httpx.AsyncClient(timeout=120) as client:
        for attempt in range(3):
            t0 = time.time()
            resp = await client.post(
                f"{config.deepseek_api_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            if await async_check_rate_limit(resp, attempt):
                continue
            if resp.status_code != 200:
                raise RuntimeError(f"LLM {resp.status_code}: {resp.text[:300]}")
            data = resp.json()
            log_llm_call(
                "centroid_summary", data.get("usage"), int((time.time() - t0) * 1000)
            )
            return extract_json(data["choices"][0]["message"]["content"])
        raise RuntimeError("LLM retries exhausted")


# ---------------------------------------------------------------------------
# Post-processing
# ---------------------------------------------------------------------------


def _sanitize_and_validate(parsed: dict, events_by_track: dict) -> dict:
    """Apply fix_role_hallucinations on all state strings + validate event IDs."""
    all_ids = set()
    for evs in events_by_track.values():
        for e in evs:
            all_ids.add(e["id"][:8])

    # Sanitize
    for key in ("overall_en", "overall_de"):
        if isinstance(parsed.get(key), str):
            parsed[key] = fix_role_hallucinations(parsed[key])

    for track_key in ("economy", "politics", "security", "society"):
        td = parsed.get(track_key)
        if isinstance(td, dict):
            if "state_en" in td:
                td["state_en"] = fix_role_hallucinations(td["state_en"])
            if "state_de" in td:
                td["state_de"] = fix_role_hallucinations(td["state_de"])
            # Filter out invented IDs
            sup = td.get("supporting_events") or []
            td["supporting_events"] = [
                sid for sid in sup if isinstance(sid, str) and sid[:8] in all_ids
            ]

    return parsed


# ---------------------------------------------------------------------------
# DB write
# ---------------------------------------------------------------------------


def compute_source_fingerprint(events_by_track: dict) -> str:
    """Stable hash of the (track, event_id, source_count) tuples feeding the LLM.

    Two centroids with identical top-N events (same ranking, same source counts)
    produce the same fingerprint. One new event entering the top-N, or any
    source_count change on a ranked event, flips the hash.
    """
    parts = []
    for track in sorted(events_by_track.keys()):
        for e in events_by_track[track]:
            parts.append(f"{track}|{e['id']}|{e['source_count']}")
    return hashlib.md5("\n".join(parts).encode("utf-8")).hexdigest()


def get_stored_fingerprint(
    conn, centroid_id: str, period_kind: str, period_end: date
) -> str | None:
    """Return the stored fingerprint or None."""
    cur = conn.cursor()
    cur.execute(
        """SELECT source_fingerprint FROM centroid_summaries
             WHERE centroid_id=%s AND period_kind=%s AND period_end=%s""",
        (centroid_id, period_kind, period_end),
    )
    row = cur.fetchone()
    return row[0] if row else None


# Hard-max age: regenerate after this many days even if fingerprint matches.
# Safety net against stale content the fingerprint can't detect (e.g., ambient
# context drift that doesn't show up in top-10-per-track event_ids).
ROLLING_HARD_MAX_DAYS = 7


def should_skip_regeneration(
    conn, centroid_id: str, period_kind: str, period_end: date, fingerprint: str
) -> bool:
    """Return True if fingerprint matches stored AND stored is recent enough."""
    if period_kind != "rolling_30d":
        return False  # monthly snapshots always regenerate
    cur = conn.cursor()
    cur.execute(
        """SELECT source_fingerprint,
                  (NOW() - generated_at) < (%s || ' days')::interval AS recent
             FROM centroid_summaries
            WHERE centroid_id=%s AND period_kind='rolling_30d'""",
        (str(ROLLING_HARD_MAX_DAYS), centroid_id),
    )
    row = cur.fetchone()
    if not row:
        return False
    stored_fp, recent = row
    return stored_fp == fingerprint and bool(recent)


def _upsert_summary(
    conn,
    centroid_id: str,
    period_kind: str,
    period_end: date,
    tier: int,
    parsed: dict,
    source_event_count: int,
    source_fingerprint: str | None = None,
) -> None:
    cur = conn.cursor()
    if period_kind == "rolling_30d":
        # Replace the active rolling row
        cur.execute(
            "DELETE FROM centroid_summaries WHERE centroid_id=%s AND period_kind='rolling_30d'",
            (centroid_id,),
        )

    cur.execute(
        """INSERT INTO centroid_summaries (
             centroid_id, period_kind, period_end, tier,
             overall_en, overall_de, economy, politics, security, society,
             source_event_count, source_fingerprint)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
           ON CONFLICT (centroid_id, period_kind, period_end) DO UPDATE SET
             tier = EXCLUDED.tier,
             overall_en = EXCLUDED.overall_en,
             overall_de = EXCLUDED.overall_de,
             economy = EXCLUDED.economy,
             politics = EXCLUDED.politics,
             security = EXCLUDED.security,
             society = EXCLUDED.society,
             source_event_count = EXCLUDED.source_event_count,
             source_fingerprint = EXCLUDED.source_fingerprint,
             generated_at = NOW()""",
        (
            centroid_id,
            period_kind,
            period_end,
            tier,
            parsed.get("overall_en"),
            parsed.get("overall_de"),
            (
                psycopg2.extras.Json(parsed.get("economy"))
                if parsed.get("economy")
                else None
            ),
            (
                psycopg2.extras.Json(parsed.get("politics"))
                if parsed.get("politics")
                else None
            ),
            (
                psycopg2.extras.Json(parsed.get("security"))
                if parsed.get("security")
                else None
            ),
            (
                psycopg2.extras.Json(parsed.get("society"))
                if parsed.get("society")
                else None
            ),
            source_event_count,
            source_fingerprint,
        ),
    )
    conn.commit()


import psycopg2.extras  # noqa: E402

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def generate_centroid_summary(
    centroid_id: str,
    period_end: date,
    period_kind: str = "rolling_30d",
    country_label: str | None = None,
) -> dict:
    """Generate and persist a summary for one centroid and period.

    Returns the parsed summary (including tier + source_event_count).
    """
    assert period_kind in ("rolling_30d", "monthly"), f"bad period_kind {period_kind!r}"

    conn = get_conn()
    cur = conn.cursor()

    # Resolve label from centroid row if not passed
    if not country_label:
        cur.execute(
            "SELECT COALESCE(label, id) FROM centroids_v3 WHERE id=%s", (centroid_id,)
        )
        row = cur.fetchone()
        country_label = row[0] if row else centroid_id

    events_by_track = fetch_top_events(cur, centroid_id, period_end)
    total_events = sum(len(v) for v in events_by_track.values())
    tier = classify_tier(events_by_track)

    # Content-based skip: if the top-N events feeding the LLM haven't changed
    # since last generation AND the stored row is still recent, don't spend
    # the LLM call. Applies only to rolling_30d (monthly always regenerates).
    fingerprint = compute_source_fingerprint(events_by_track)
    if should_skip_regeneration(
        conn, centroid_id, period_kind, period_end, fingerprint
    ):
        conn.close()
        return {
            "tier": 0,
            "source_event_count": total_events,
            "parsed": None,
            "status": "unchanged",
        }

    if tier == 3:
        # Canned, no LLM
        parsed = {
            "overall_en": TIER3_OVERALL_EN,
            "overall_de": TIER3_OVERALL_DE,
            "economy": None,
            "politics": None,
            "security": None,
            "society": None,
        }
        _upsert_summary(
            conn,
            centroid_id,
            period_kind,
            period_end,
            tier,
            parsed,
            total_events,
            source_fingerprint=fingerprint,
        )
        conn.close()
        return {"tier": 3, "source_event_count": total_events, "parsed": parsed}

    ambient = fetch_ambient_context(cur, centroid_id, period_end)
    events_block = _fmt_events_block(events_by_track)
    ambient_block = _fmt_ambient_block(ambient)

    user_prompt = (
        f"Country: {country_label}\n"
        f"Period: rolling 30 days ending {period_end.isoformat()}\n\n"
        f"{events_block}\n\n"
        f"{ambient_block}\n\n"
        f"Produce the JSON now."
    )

    system_prompt = SYSTEM_PROMPT_TIER1 if tier == 1 else SYSTEM_PROMPT_TIER2
    # Tier-1: 1500 caps the real ~1000-1300 token bilingual output; 3000 just
    # let the model ramble (2026-04-23 cost-control pass).
    max_tokens = 1500 if tier == 1 else 800

    parsed = await _call_llm(system_prompt, user_prompt, max_tokens)
    parsed = _sanitize_and_validate(parsed, events_by_track)

    _upsert_summary(
        conn,
        centroid_id,
        period_kind,
        period_end,
        tier,
        parsed,
        total_events,
        source_fingerprint=fingerprint,
    )
    conn.close()
    return {"tier": tier, "source_event_count": total_events, "parsed": parsed}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--centroid", required=True)
    parser.add_argument("--period-end", required=True, help="YYYY-MM-DD")
    parser.add_argument(
        "--period-kind", default="rolling_30d", choices=["rolling_30d", "monthly"]
    )
    args = parser.parse_args()

    result = asyncio.run(
        generate_centroid_summary(
            args.centroid, date.fromisoformat(args.period_end), args.period_kind
        )
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
