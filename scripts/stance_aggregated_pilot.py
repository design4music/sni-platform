"""Aggregated stance pilot.

Rather than rate each headline, sample N headlines per (outlet, entity, month)
and ask the LLM to characterize the outlet's editorial stance toward the entity
based on the full bundle. Aggregate pattern detection, not per-title classification.

Writes:
    out/stance_aggregated/results.csv   — one row per (outlet, entity) pair
    out/stance_aggregated/bundles.jsonl — raw headlines per bundle for audit
    out/stance_aggregated/report.md     — human-readable matrix
"""

import asyncio
import csv
import json
import re
import sys
import time
from pathlib import Path

import httpx
import psycopg2
from psycopg2.extras import RealDictCursor

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config

MONTH_START = "2026-03-01"
MONTH_END = "2026-04-01"
MONTH_LABEL = "March 2026"
SAMPLE_PER_BUNDLE = 25
MIN_PER_BUNDLE = 15
CONCURRENCY = 5
OUT_DIR = Path("out/stance_aggregated")

OUTLETS = [
    "New York Times",
    "Handelsblatt",
    "Lenta.ru",
    "Al Jazeera",
    "Jerusalem Post",
    "CGTN",
]

# (code, kind, country_for_person)
ENTITIES = [
    ("US", "country", None),
    ("RU", "country", None),
    ("IR", "country", None),
    ("IL", "country", None),
    ("TRUMP", "person", "US"),
    ("PUTIN", "person", "RU"),
]

SYSTEM_PROMPT = """You analyse the editorial stance of a news outlet toward a specific entity, based on a bundle of headlines the outlet published about it.

Return JSON only, no prose:
{
  "stance": -2|-1|0|1|2,
  "confidence": "low"|"medium"|"high",
  "tone": "short phrase",
  "patterns": ["...", "..."],
  "evidence_idx": [N, N, N],
  "caveats": "..."
}

Scale:
  -2 = consistently hostile / delegitimising
  -1 = skeptical / critical
   0 = neutral reporting / mixed / no clear stance
  +1 = sympathetic / supportive
  +2 = consistently celebratory / promotional

Read ALL headlines in the bundle. Look for:
  - Vocabulary choices (evaluative words, possessive blaming, scare quotes)
  - Selection patterns (what is covered, what is foregrounded)
  - Consistency or variation of editorial voice
  - Irony, pragmatic alignment, or fake distancing (citing sources that carry the framing the outlet itself endorses)

Be honest about nuance. Mark stance=0 with explicit caveat when the coverage is genuinely mixed or factual.
Russian-outlet coverage of the US/Trump, or Arab-outlet coverage of Israel, may be complex — ironic, pragmatic, or conditional rather than flatly hostile.
"confidence":"low" is correct when the bundle is small, mixed, or primarily factual.
patterns: 2-4 short observable rhetorical patterns (vocabulary, framing, selection).
evidence_idx: 2-3 headline indices that best exemplify the stance.
caveats: any complicating signal.
"""


def get_conn():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        dbname=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def fetch_bundle(cur, outlet: str, code: str, kind: str) -> list[dict]:
    if kind == "country":
        cur.execute(
            """
            SELECT t.id::text AS title_id, t.detected_language, t.title_display, t.pubdate_utc
            FROM titles_v3 t
            JOIN title_labels tl ON tl.title_id = t.id
            WHERE t.publisher_name = %s
              AND t.pubdate_utc >= %s::date AND t.pubdate_utc < %s::date
              AND EXISTS (
                SELECT 1 FROM jsonb_each_text(tl.entity_countries) je
                WHERE je.value = %s
              )
            ORDER BY random()
            LIMIT %s
            """,
            (outlet, MONTH_START, MONTH_END, code, SAMPLE_PER_BUNDLE),
        )
    else:  # person
        cur.execute(
            """
            SELECT t.id::text AS title_id, t.detected_language, t.title_display, t.pubdate_utc
            FROM titles_v3 t
            JOIN title_labels tl ON tl.title_id = t.id
            WHERE t.publisher_name = %s
              AND t.pubdate_utc >= %s::date AND t.pubdate_utc < %s::date
              AND %s = ANY(tl.persons)
            ORDER BY random()
            LIMIT %s
            """,
            (outlet, MONTH_START, MONTH_END, code, SAMPLE_PER_BUNDLE),
        )
    return [dict(r) for r in cur.fetchall()]


def build_user_prompt(
    outlet: str, entity: str, kind: str, headlines: list[dict]
) -> str:
    lines = [
        "Outlet: %s" % outlet,
        "Entity: %s (%s)" % (entity, kind),
        "Month: %s" % MONTH_LABEL,
        "Headlines (%d):" % len(headlines),
        "",
    ]
    for i, h in enumerate(headlines, 1):
        lines.append("%d. [%s] %s" % (i, h["detected_language"], h["title_display"]))
    return "\n".join(lines)


def parse_json(text: str):
    if not text:
        return None
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    m = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return None


async def call_llm(
    client: httpx.AsyncClient, user: str, sem: asyncio.Semaphore
) -> tuple[str, dict, float]:
    headers = {
        "Authorization": "Bearer %s" % config.deepseek_api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
        "temperature": 0.0,
        "max_tokens": 800,
    }
    async with sem:
        for attempt in range(3):
            try:
                t0 = time.time()
                resp = await client.post(
                    "%s/chat/completions" % config.deepseek_api_url,
                    headers=headers,
                    json=payload,
                    timeout=120.0,
                )
                if resp.status_code in (429, 502, 503, 504):
                    await asyncio.sleep(5 * (3**attempt))
                    continue
                if resp.status_code != 200:
                    return ("", {}, time.time() - t0)
                data = resp.json()
                return (
                    data["choices"][0]["message"]["content"],
                    data.get("usage", {}),
                    time.time() - t0,
                )
            except (httpx.RequestError, httpx.TimeoutException):
                await asyncio.sleep(2 * (attempt + 1))
                continue
        return ("", {}, 0.0)


async def run():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sem = asyncio.Semaphore(CONCURRENCY)

    # Build all bundles synchronously
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    bundles = []
    for outlet in OUTLETS:
        for code, kind, person_country in ENTITIES:
            headlines = fetch_bundle(cur, outlet, code, kind)
            print(
                "  %-22s × %-10s : %d titles"
                % (outlet, "%s(%s)" % (code, kind), len(headlines)),
                flush=True,
            )
            if len(headlines) < MIN_PER_BUNDLE:
                continue
            bundles.append(
                {
                    "outlet": outlet,
                    "entity_code": code,
                    "entity_kind": kind,
                    "entity_country": person_country,
                    "headlines": headlines,
                }
            )
    cur.close()
    conn.close()
    print("Qualifying bundles: %d" % len(bundles), flush=True)

    # Fire LLM calls in parallel
    async with httpx.AsyncClient() as client:
        tasks = []
        for b in bundles:
            user = build_user_prompt(
                b["outlet"], b["entity_code"], b["entity_kind"], b["headlines"]
            )
            tasks.append(call_llm(client, user, sem))
        raw_results = await asyncio.gather(*tasks)

    # Assemble records
    rows = []
    with open(OUT_DIR / "bundles.jsonl", "w", encoding="utf-8") as f_bundle:
        for b, (raw, usage, latency) in zip(bundles, raw_results):
            obj = parse_json(raw) or {}
            rec = {
                "outlet": b["outlet"],
                "entity_code": b["entity_code"],
                "entity_kind": b["entity_kind"],
                "entity_country": b["entity_country"] or "",
                "n_headlines": len(b["headlines"]),
                "stance": obj.get("stance"),
                "confidence": obj.get("confidence", ""),
                "tone": obj.get("tone", ""),
                "patterns": json.dumps(obj.get("patterns", []), ensure_ascii=False),
                "evidence_idx": json.dumps(
                    obj.get("evidence_idx", []), ensure_ascii=False
                ),
                "caveats": obj.get("caveats", ""),
                "tokens_in": usage.get("prompt_tokens", 0),
                "tokens_out": usage.get("completion_tokens", 0),
                "latency_s": round(latency, 2),
            }
            rows.append((rec, b["headlines"], obj))
            f_bundle.write(
                json.dumps(
                    {
                        "outlet": b["outlet"],
                        "entity": b["entity_code"],
                        "headlines": [h["title_display"] for h in b["headlines"]],
                        "raw_llm": raw,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    # Write CSV
    with open(OUT_DIR / "results.csv", "w", newline="", encoding="utf-8") as f_csv:
        w = csv.DictWriter(
            f_csv,
            fieldnames=[
                "outlet",
                "entity_code",
                "entity_kind",
                "entity_country",
                "n_headlines",
                "stance",
                "confidence",
                "tone",
                "patterns",
                "evidence_idx",
                "caveats",
                "tokens_in",
                "tokens_out",
                "latency_s",
            ],
        )
        w.writeheader()
        for rec, _, _ in rows:
            w.writerow(rec)

    # Write report
    lines = ["# Aggregated Stance Pilot — %s\n" % MONTH_LABEL]
    lines.append(
        "One LLM call per (outlet, entity) bundle of ~%d headlines.\n"
        % SAMPLE_PER_BUNDLE
    )

    # Matrix table
    lines.append("## Stance matrix\n")
    lines.append("| outlet \\ entity | " + " | ".join(e[0] for e in ENTITIES) + " |")
    lines.append("|---|" + "|".join(["---"] * len(ENTITIES)) + "|")
    cell = {(r[0]["outlet"], r[0]["entity_code"]): r[0] for r in rows}
    for outlet in OUTLETS:
        parts = ["| %s" % outlet]
        for code, _, _ in ENTITIES:
            r = cell.get((outlet, code))
            if r is None:
                parts.append("—")
                continue
            stance = r["stance"] if r["stance"] is not None else "?"
            conf = r["confidence"][:3] if r["confidence"] else ""
            parts.append(
                "%s (%s, n=%d)" % (_stance_str(stance), conf, r["n_headlines"])
            )
        lines.append(" | ".join(parts) + " |")
    lines.append("")

    # Per-bundle detail
    lines.append("## Per-bundle detail\n")
    for rec, headlines, obj in rows:
        title = "%s × %s%s" % (
            rec["outlet"],
            rec["entity_code"],
            " (person)" if rec["entity_kind"] == "person" else "",
        )
        lines.append("### %s" % title)
        lines.append("")
        stance = rec["stance"] if rec["stance"] is not None else "?"
        lines.append(
            "**Stance**: %s · **Confidence**: %s · **Tone**: %s · **n=%d**"
            % (
                _stance_str(stance),
                rec["confidence"] or "—",
                rec["tone"] or "—",
                rec["n_headlines"],
            )
        )
        lines.append("")
        if obj.get("patterns"):
            lines.append("Patterns:")
            for p in obj["patterns"]:
                lines.append("- %s" % p)
            lines.append("")
        if rec["caveats"]:
            lines.append("Caveats: %s" % rec["caveats"])
            lines.append("")
        # Evidence
        ev_idx = obj.get("evidence_idx", []) or []
        if ev_idx:
            lines.append("Evidence headlines:")
            for idx in ev_idx:
                try:
                    idx = int(idx)
                    if 1 <= idx <= len(headlines):
                        h = headlines[idx - 1]
                        lines.append(
                            "- [%d] [%s] %s"
                            % (idx, h["detected_language"], h["title_display"])
                        )
                except (TypeError, ValueError):
                    continue
            lines.append("")

    # Totals
    tok_in = sum(r[0]["tokens_in"] for r in rows)
    tok_out = sum(r[0]["tokens_out"] for r in rows)
    lines.append("## Cost")
    lines.append("")
    rate_in = 0.14 / 1_000_000
    rate_out = 0.28 / 1_000_000
    cost = tok_in * rate_in + tok_out * rate_out
    lines.append(
        "- %d bundles · tokens in %d / out %d · est $%.4f"
        % (len(rows), tok_in, tok_out, cost)
    )
    (OUT_DIR / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("Wrote: %s" % (OUT_DIR / "results.csv"), flush=True)
    print("Wrote: %s" % (OUT_DIR / "report.md"), flush=True)


def _stance_str(s):
    if s == 2:
        return "**+2**"
    if s == 1:
        return "+1"
    if s == 0:
        return "0"
    if s == -1:
        return "-1"
    if s == -2:
        return "**-2**"
    return "?"


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
