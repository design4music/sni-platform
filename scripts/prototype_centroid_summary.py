"""Prototype centroid period summaries — rolling 30-day, chained across months.

Generates 4 summaries for Germany: end of Jan, Feb, Mar, and most-recent
(Apr 15), each informed by the previous period's summary. Prints and
saves to out/centroid_summary_prototype/.

Purpose: see what the LLM produces before committing to a schema + prompt.
"""

import asyncio
import json
import sys
import time
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse

import httpx
import psycopg2

from core.config import config
from core.llm_utils import extract_json, fix_role_hallucinations

PERIOD_ENDS = ["2026-01-31", "2026-02-28", "2026-03-31", "2026-04-15"]
OUTPUT_DIR = Path("out/centroid_summary_prototype")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_conn():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def fetch_ambient_context(
    cur, centroid_id: str, end_date: date, days_back: int = 30
) -> dict:
    """Aggregate top-N entities across all titles assigned to this centroid,
    filtering out entities so ubiquitous they add noise (>=80% of titles).

    Returns {persons, orgs, countries, places} each a list of {name, count}.
    """
    start_date = end_date - timedelta(days=days_back - 1)

    # First get total title count for the ubiquity threshold
    cur.execute(
        """SELECT COUNT(DISTINCT ta.title_id)
             FROM title_assignments ta
             JOIN ctm c ON c.id = ta.ctm_id
             JOIN titles_v3 t ON t.id = ta.title_id
            WHERE c.centroid_id = %s AND t.pubdate_utc BETWEEN %s AND %s""",
        (centroid_id, start_date, end_date),
    )
    total_titles = cur.fetchone()[0] or 0
    ubiquity_threshold = max(1, int(total_titles * 0.8))

    def top_entities(column_expr: str, lateral_clause: str, limit: int = 10) -> list:
        cur.execute(
            f"""SELECT e AS name, COUNT(DISTINCT tl.title_id) AS n
                  FROM title_labels tl
                  JOIN title_assignments ta ON ta.title_id = tl.title_id
                  JOIN ctm c ON c.id = ta.ctm_id
                  JOIN titles_v3 t ON t.id = tl.title_id
                  {lateral_clause}
                 WHERE c.centroid_id = %s
                   AND t.pubdate_utc BETWEEN %s AND %s
                   AND tl.label_version = 'ELO_v3.0.1'
                 GROUP BY e
                 HAVING COUNT(DISTINCT tl.title_id) < %s
                 ORDER BY n DESC LIMIT %s""",
            (centroid_id, start_date, end_date, ubiquity_threshold, limit),
        )
        return [{"name": r[0], "count": r[1]} for r in cur.fetchall()]

    return {
        "total_titles": total_titles,
        "persons": top_entities(
            "persons", "CROSS JOIN LATERAL unnest(tl.persons) AS e"
        ),
        "orgs": top_entities("orgs", "CROSS JOIN LATERAL unnest(tl.orgs) AS e"),
        "countries": top_entities(
            "entity_countries",
            "CROSS JOIN LATERAL jsonb_each_text(tl.entity_countries) AS ec(_name, e)",
        ),
        "places": top_entities("places", "CROSS JOIN LATERAL unnest(tl.places) AS e"),
    }


def format_ambient_for_prompt(ambient: dict) -> str:
    def fmt(label: str, items: list) -> str:
        if not items:
            return f"  {label}: (none)"
        parts = [f"{i['name']}({i['count']})" for i in items]
        return f"  {label}: " + ", ".join(parts)

    return (
        f"AMBIENT CONTEXT (persistent presence across all coverage, "
        f"{ambient['total_titles']} total titles this period):\n"
        + fmt("Top persons", ambient["persons"])
        + "\n"
        + fmt("Top orgs", ambient["orgs"])
        + "\n"
        + fmt("Top countries", ambient["countries"])
        + "\n"
        + fmt("Top places", ambient["places"])
    )


def fetch_top_events(
    cur, centroid_id: str, end_date: date, days_back: int = 30
) -> dict:
    """Top 10 events per track for the rolling window ending on end_date."""
    start_date = end_date - timedelta(days=days_back - 1)
    cur.execute(
        """WITH ranked AS (
             SELECT c.track, e.id::text AS id, e.title, e.source_batch_count, e.date::text AS date,
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
    by_track = {
        "geo_economy": [],
        "geo_politics": [],
        "geo_security": [],
        "geo_society": [],
    }
    for row in cur.fetchall():
        track = row[0]
        if track in by_track:
            by_track[track].append(
                {"id": row[1], "title": row[2], "source_count": row[3], "date": row[4]}
            )
    return by_track


def format_events_for_prompt(by_track: dict) -> str:
    sections = []
    for track, label in [
        ("geo_economy", "ECONOMY"),
        ("geo_politics", "POLITICS"),
        ("geo_security", "SECURITY"),
        ("geo_society", "SOCIETY"),
    ]:
        evs = by_track.get(track, [])
        if not evs:
            sections.append(f"{label}: (no events this period)")
            continue
        lines = [f"{label} ({len(evs)} events):"]
        for e in evs:
            lines.append(
                f'  [{e["id"][:8]}] {e["source_count"]} src | {e["date"]} | {e["title"]}'
            )
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


SYSTEM_PROMPT = """You are a strategic intelligence analyst writing a concise "state of play" brief for a specific country, covering a rolling 30-day period.

Produce a JSON object with this exact structure:
{
  "overall": "1-2 sentence headline capturing the country's dominant tension or trajectory across all domains. Name actors and substance; do not rely on mood words.",
  "economy":  { "state": "...", "supporting_events": ["id1", "id2"] },
  "politics": { "state": "...", "supporting_events": [...] },
  "security": { "state": "...", "supporting_events": [...] },
  "society":  { "state": "...", "supporting_events": [...] }
}

Each track's "state" is 2-3 sentences that:
- LEAD with the current state as a concrete observation. Good: "Economy is in stagnation." Bad: "Economic situation is complex."
- SUPPORT the lead with specific developments from the provided events.
- If a prior period summary is provided AND the state has NOT materially changed, say so briefly and point to deepening specifics. Do NOT re-narrate the same frame.

CONSTRAINTS:
- Cite 1-3 specific events per track via their 8-char ID prefixes in supporting_events. DO NOT INVENT events, numbers, or dates not in the provided list.
- Cross-track references are welcome where relevant.
- Tier 0 "overall" must synthesize ALL FOUR tracks, not just repeat one. Should name 2+ concrete actors or forces.
- Write in direct, reportorial English. Subject-verb-object. No hedging.
- When AMBIENT CONTEXT shows multiple prominent actors for a track, NAME AT LEAST 2-3 beyond the head of government where relevant. Don't let any single figure dominate every sentence.

ROLE / TITLE RULES (CRITICAL — hallucination hazard):
- You may restate a role or title ONLY if it appears verbatim in a provided event title (e.g., "Chancellor Merz" if the event title reads "Chancellor Merz announces...").
- You may NOT assign roles from your own knowledge. If an entity appears only as a bare name in the data, use only the bare name.
- NEVER call anyone a "former X" unless the event explicitly says so.
- When in doubt, drop the title. "Merz said X" is safer than "Chancellor Merz said X" if no event title carries the role.

BACKGROUND CONTEXT (persistent issues not captured as discrete events):
- If AMBIENT CONTEXT shows a foreign country or recurring topic persistently present (e.g. multiple mentions across coverage) but no discrete events lead the period, you MAY acknowledge it as background in one clause. Example: "Russia-Ukraine war persists as coverage backdrop without major German-driven developments this period."
- You may NOT invent specifics (numbers, named events, new developments) about such background topics. Pure acknowledgment only.

SOCIETY PARAGRAPH SPECIFIC:
- Name ONE dominant tension and describe its current phase. Don't list unrelated items with equal weight ("labor strikes AND digital violence AND peace marches..." reads as a grab bag).

FORBIDDEN PHRASES (never use anywhere):
- "turbulent times", "challenging period", "complex situation", "uncertainty persists"
- "ongoing tensions", "dynamic landscape", "evolving circumstances"
- "Germany faces [X]", "[Country] navigates [Y]", "[Country] grapples with [Y]"
- "It appears", "seems to be", "one could argue", "some believe"
- "balance between", "dual-track", "pivot" (overused; find concrete alternatives)

DO NOT project from pre-2026 background knowledge. Stick to the provided material.

FEW-SHOT EXAMPLES (good style):

GOOD economy:
{"state": "Economy is in measured decline. Automakers continue to contract — VW layoffs at Wolfsburg, Mercedes cuts at Tuscaloosa — amid weak EV demand and China market losses. SAP's 20% share drop on cloud-revenue disappointment adds to the industrial signal.", "supporting_events": ["vw_abc123", "mrc_def456", "sap_ghi789"]}

GOOD politics, naming multiple actors:
{"state": "Politics is polarized around the AfD question. Merz's CDU passed migration legislation with AfD votes, breaking the postwar cordon sanitaire. Greens threaten coalition exit; Weidel (AfD) gains procedural ground; Klingbeil (SPD) under internal pressure.", "supporting_events": ["mig_xyz111", "prt_xyz222"]}

GOOD continuity (Month N+1, with prior):
{"state": "Stagnation deepens from last period. VW now in talks to pivot production to missile defense parts; Mercedes and Porsche report sharp sales drops in China and America. State intervenes on fuel prices to cushion consumers.", "supporting_events": ["vw_pivot_id", "mb_sales_id"]}

BAD (do not emulate):
- "Germany faces a complex political landscape with many challenges." (vague, no content)
- "Rising economic uncertainty continues." (hedging, no events)
- "Consumer confidence at multi-year lows." (hallucinated data)
- "Germany is navigating turbulent times." (banned phrase)
- "Former Chancellor Scholz commented..." (wrong role — Scholz wasn't in the data)

Output ONLY the JSON object. No preamble, no commentary."""


USER_PROMPT_TEMPLATE = """Country: {country}
Period: rolling 30 days ending {end_date}

{events_block}

{ambient_block}

{prior_block}

Produce the JSON now."""


async def generate_summary(
    country: str,
    end_date: str,
    events_by_track: dict,
    ambient: dict,
    prior_summary: dict | None,
) -> dict:
    events_block = format_events_for_prompt(events_by_track)
    ambient_block = format_ambient_for_prompt(ambient)

    if prior_summary:
        prior_text = (
            f"PRIOR PERIOD summary (ending {prior_summary['end_date']}):\n"
            f"  overall: {prior_summary['summary'].get('overall', '')}\n"
        )
        for tk in ["economy", "politics", "security", "society"]:
            p = prior_summary["summary"].get(tk, {})
            prior_text += f"  {tk}: {p.get('state', '')}\n"
        prior_text += (
            "\nUse the prior summary to judge continuity or change. If the state persists, "
            "acknowledge briefly. If it shifted, lead with the change."
        )
    else:
        prior_text = "PRIOR PERIOD: (none — this is the first period)"

    user_prompt = USER_PROMPT_TEMPLATE.format(
        country=country,
        end_date=end_date,
        events_block=events_block,
        ambient_block=ambient_block,
        prior_block=prior_text,
    )

    headers = {
        "Authorization": f"Bearer {config.deepseek_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 2000,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{config.deepseek_api_url}/chat/completions", headers=headers, json=payload
        )
        if resp.status_code != 200:
            raise RuntimeError(f"LLM {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        raw = data["choices"][0]["message"]["content"]
    parsed = extract_json(raw)
    return {"raw": raw, "parsed": parsed, "user_prompt": user_prompt}


def validate_supporting_events(parsed: dict, events_by_track: dict) -> list[str]:
    """Check that supporting_events IDs (8-char prefixes) actually exist in input."""
    all_ids = set()
    for evs in events_by_track.values():
        for e in evs:
            all_ids.add(e["id"][:8])
    issues = []
    for tk in ["economy", "politics", "security", "society"]:
        sup = parsed.get(tk, {}).get("supporting_events", []) or []
        for sid in sup:
            prefix = sid.replace("_", "")[:8] if "_" in sid else sid[:8]
            if prefix not in all_ids:
                issues.append(f"{tk}: cited {sid!r} not in provided events")
    return issues


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--centroid", required=True, help="Centroid ID, e.g. EUROPE-GERMANY"
    )
    parser.add_argument("--label", required=True, help="Display label, e.g. Germany")
    parser.add_argument(
        "--no-chain",
        action="store_true",
        help="Do NOT feed prior-period summary as context (one-shot per period)",
    )
    args = parser.parse_args()

    CENTROID_ID = args.centroid
    CENTROID_LABEL = args.label
    tag = "_oneshot" if args.no_chain else ""

    conn = get_conn()
    cur = conn.cursor()

    prior_summary = None
    for end_date_str in PERIOD_ENDS:
        end_date = date.fromisoformat(end_date_str)
        print(
            f"\n{'='*70}\n{CENTROID_LABEL} — rolling 30d ending {end_date_str}\n{'='*70}"
        )
        events_by_track = fetch_top_events(cur, CENTROID_ID, end_date)
        ambient = fetch_ambient_context(cur, CENTROID_ID, end_date)
        total_events = sum(len(v) for v in events_by_track.values())
        print(
            f"Fetched {total_events} events + ambient ({ambient['total_titles']} titles)\n"
        )

        t0 = time.time()
        result = await generate_summary(
            CENTROID_LABEL, end_date_str, events_by_track, ambient, prior_summary
        )
        elapsed = time.time() - t0
        parsed = result["parsed"]

        # Post-process: sanitize role hallucinations in all state strings
        for tk in ("overall", "economy", "politics", "security", "society"):
            if isinstance(parsed.get(tk), str):
                parsed[tk] = fix_role_hallucinations(parsed[tk])
            elif isinstance(parsed.get(tk), dict) and "state" in parsed[tk]:
                parsed[tk]["state"] = fix_role_hallucinations(parsed[tk]["state"])

        issues = validate_supporting_events(parsed, events_by_track)

        print(f"--- RAW OUTPUT ({elapsed:.1f}s) ---")
        print(json.dumps(parsed, indent=2, ensure_ascii=False))
        print()
        if issues:
            print("--- VALIDATION ISSUES ---")
            for i in issues:
                print(f"  ! {i}")
            print()

        # Save full artifact
        artifact = {
            "end_date": end_date_str,
            "centroid_id": CENTROID_ID,
            "events_provided": events_by_track,
            "prior_summary": prior_summary,
            "user_prompt": result["user_prompt"],
            "raw_output": result["raw"],
            "parsed": parsed,
            "validation_issues": issues,
            "elapsed_s": elapsed,
        }
        out_path = (
            OUTPUT_DIR
            / f"{CENTROID_ID.lower().replace('-', '_')}_{end_date_str}{tag}.json"
        )
        out_path.write_text(
            json.dumps(artifact, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"Saved: {out_path}\n")

        prior_summary = (
            None if args.no_chain else {"end_date": end_date_str, "summary": parsed}
        )

    conn.close()


if __name__ == "__main__":
    asyncio.run(main())
