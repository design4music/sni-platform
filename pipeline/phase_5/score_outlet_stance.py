"""D-071 Phase B: outlet × entity × month stance scoring.

For each outlet above a title-volume threshold in a given month, find the
top-N most-mentioned entities (countries via entity_countries + persons via
persons[]), sample up to SAMPLE_PER_BUNDLE headlines per qualifying entity
(>= MIN_PER_BUNDLE), and run one LLM call per bundle. Results upserted into
outlet_entity_stance.

Usage:
    python -m pipeline.phase_5.score_outlet_stance --outlet "Lenta.ru" --month 2026-03 --report
    python -m pipeline.phase_5.score_outlet_stance --month 2026-03 --concurrency 10
    python -m pipeline.phase_5.score_outlet_stance --outlet "Handelsblatt" --month 2026-03 --dry-run
"""

import argparse
import asyncio
import json
import re
import sys
import time
from pathlib import Path

import httpx
import psycopg2
import psycopg2.extras
from psycopg2.extras import RealDictCursor

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config  # noqa: E402

# Ensure psycopg2 returns uuid[] as list of uuid objects, not PG array literal.
psycopg2.extras.register_uuid()

SAMPLE_PER_BUNDLE = 25
MIN_PER_BUNDLE = 15
TOP_N_ENTITIES = 15
CONCURRENCY = 5
REPORT_DIR = Path("out/outlet_stance")

SYSTEM_PROMPT = """You analyse how an outlet TREATS a specific entity in its editorial coverage, based on a bundle of headlines the outlet published mentioning that entity.

Return JSON only, no prose:
{
  "stance": -2|-1|0|1|2,
  "confidence": "low"|"medium"|"high",
  "tone": "short phrase",
  "patterns": ["...", "..."],
  "evidence_idx": [N, N, N],
  "caveats": "..."
}

CRITICAL — what "stance" measures:
The score is the outlet's stance TOWARD THE NAMED ENTITY, NOT the stance the entity expresses toward third parties, and NOT the overall mood of the news.

When the entity is a spokesperson, official, or activist whose statements are being reported, ask: does the outlet treat THEM as authoritative / credible / sympathetic (positive), or as a problem / liability / antagonist (negative)? The fact that the entity is quoted attacking, criticising, or threatening someone else does NOT make the OUTLET's stance toward THEM negative — it may well be the opposite.

Worked examples:
- TASS publishing "Lavrov slams US-Israeli aggression on Iran": Lavrov is quoted authoritatively, his words are amplified as Russian foreign-policy voice → POSITIVE toward Lavrov (+1), even though the QUOTE is hostile to US/Israel. The outlet treats him as a credible spokesperson.
- A Western outlet's bundle "Putin claims West is decadent / Putin denies invasion plans / Kremlin sources tell us X": the entity (Putin) is quoted but the outlet uses distancing verbs ("claims", "denies", attribution to "Kremlin sources") → SKEPTICAL of Putin (-1).
- "Brutal Russian crackdown intensifies / regime detains journalists": outlet's own evaluative vocabulary ("brutal", "regime") frames the actor → HOSTILE to actor (-2).
- "Trump signs executive order / Trump meets Xi": neutral reporting of actions, no evaluative voice → NEUTRAL (0).

Scale (always toward the entity):
  -2 = consistently hostile / delegitimising language about the entity
  -1 = skeptical / critical of the entity (distancing verbs, scare quotes, exposing failures)
   0 = neutral reporting / mixed / no clear stance toward the entity
  +1 = treats the entity as credible / sympathetic / favoured
  +2 = consistently celebratory / promotional / lionising

Read ALL headlines in the bundle. Look for:
  - Whether the outlet's own vocabulary frames the ENTITY positively or negatively
  - Whether the entity is quoted authoritatively (positive) or with distance ("claims", "alleges")
  - Selection: does the outlet foreground the entity's wins or failures?
  - Consistency or variation
  - Irony, pragmatic alignment, fake distancing

Be honest about nuance. Mark stance=0 with explicit caveat when coverage is genuinely mixed or factual.
"confidence":"low" is correct when the bundle is small, mixed, or primarily factual.
patterns: 2-4 short observable rhetorical patterns (vocabulary, framing, selection).
evidence_idx: 2-3 headline indices (1-based) that best exemplify the stance.
caveats: any complicating signal — especially flag if the entity's quoted *content* is critical of others while the outlet *itself* is favourable to the entity."""


# ----------------------------------------------------------------------
# DB helpers
# ----------------------------------------------------------------------


def get_conn():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        dbname=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def month_bounds(month: str) -> tuple[str, str]:
    """'2026-03' -> ('2026-03-01', '2026-04-01')."""
    y, m = month.split("-")
    y, m = int(y), int(m)
    if m == 12:
        ny, nm = y + 1, 1
    else:
        ny, nm = y, m + 1
    return ("%04d-%02d-01" % (y, m), "%04d-%02d-01" % (ny, nm))


def fetch_qualifying_outlets(cur, month: str, min_per_bundle: int) -> list[str]:
    """Outlets that have at least one (kind, code) entity with >= min_per_bundle
    mentions in the given month. No outlet-volume gate — the entity bundle gate
    is the real filter, and small outlets with focused coverage are valuable.
    """
    start, end = month_bounds(month)
    cur.execute(
        """
        WITH mentions AS (
            SELECT t.publisher_name, 'country' AS kind, je.value AS code
            FROM titles_v3 t
            JOIN title_labels tl ON tl.title_id = t.id,
                 jsonb_each_text(tl.entity_countries) je
            WHERE t.pubdate_utc >= %s::date AND t.pubdate_utc < %s::date
              AND t.publisher_name IS NOT NULL
              AND tl.entity_countries IS NOT NULL
              AND je.value IS NOT NULL AND je.value <> ''
            UNION ALL
            SELECT t.publisher_name, 'person' AS kind, p AS code
            FROM titles_v3 t
            JOIN title_labels tl ON tl.title_id = t.id,
                 unnest(tl.persons) p
            WHERE t.pubdate_utc >= %s::date AND t.pubdate_utc < %s::date
              AND t.publisher_name IS NOT NULL
              AND tl.persons IS NOT NULL
              AND p IS NOT NULL AND p <> ''
        )
        SELECT DISTINCT publisher_name FROM (
            SELECT publisher_name, kind, code, COUNT(*) AS n
            FROM mentions
            GROUP BY publisher_name, kind, code
            HAVING COUNT(*) >= %s
        ) q
        ORDER BY publisher_name
        """,
        (start, end, start, end, min_per_bundle),
    )
    return [r[0] for r in cur.fetchall()]


def fetch_top_entities(
    cur, outlet: str, month: str, top_n: int, min_per_bundle: int
) -> list[dict]:
    """Return [{kind, code, n}] ordered by mention count, filtered to those
    with at least min_per_bundle mentions (so we know a bundle can be built).
    """
    start, end = month_bounds(month)
    cur.execute(
        """
        WITH outlet_titles AS (
            SELECT tl.entity_countries, tl.persons
            FROM titles_v3 t
            JOIN title_labels tl ON tl.title_id = t.id
            WHERE t.publisher_name = %s
              AND t.pubdate_utc >= %s::date
              AND t.pubdate_utc <  %s::date
        ),
        country_mentions AS (
            SELECT 'country' AS kind, je.value AS code
            FROM outlet_titles, jsonb_each_text(entity_countries) je
            WHERE entity_countries IS NOT NULL
        ),
        person_mentions AS (
            SELECT 'person' AS kind, p AS code
            FROM outlet_titles, unnest(persons) p
            WHERE persons IS NOT NULL
        ),
        all_mentions AS (
            SELECT * FROM country_mentions
            UNION ALL
            SELECT * FROM person_mentions
        )
        SELECT kind, code, COUNT(*)::int AS n
        FROM all_mentions
        WHERE code IS NOT NULL AND code <> ''
        GROUP BY kind, code
        HAVING COUNT(*) >= %s
        ORDER BY n DESC
        LIMIT %s
        """,
        (outlet, start, end, min_per_bundle, top_n),
    )
    return [dict(r) for r in cur.fetchall()]


def fetch_bundle(
    cur, outlet: str, month: str, kind: str, code: str, sample: int
) -> list[dict]:
    start, end = month_bounds(month)
    if kind == "country":
        cur.execute(
            """
            SELECT t.id::text AS title_id, t.detected_language,
                   t.title_display, t.pubdate_utc
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
            (outlet, start, end, code, sample),
        )
    else:  # person
        cur.execute(
            """
            SELECT t.id::text AS title_id, t.detected_language,
                   t.title_display, t.pubdate_utc,
                   tl.entity_countries
            FROM titles_v3 t
            JOIN title_labels tl ON tl.title_id = t.id
            WHERE t.publisher_name = %s
              AND t.pubdate_utc >= %s::date AND t.pubdate_utc < %s::date
              AND %s = ANY(tl.persons)
            ORDER BY random()
            LIMIT %s
            """,
            (outlet, start, end, code, sample),
        )
    return [dict(r) for r in cur.fetchall()]


def infer_person_country(bundle: list[dict]) -> str | None:
    """Person rows carry entity_countries. Pick the most frequent country
    seen alongside the person across the bundle. None if ambiguous."""
    counts: dict[str, int] = {}
    for row in bundle:
        ec = row.get("entity_countries")
        if not ec:
            continue
        if isinstance(ec, str):
            ec = json.loads(ec)
        for v in ec.values():
            if v:
                counts[v] = counts.get(v, 0) + 1
    if not counts:
        return None
    # Pick most frequent; tiebreaker alphabetical
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


# ----------------------------------------------------------------------
# LLM
# ----------------------------------------------------------------------


def build_user_prompt(
    outlet: str, kind: str, code: str, month: str, headlines: list[dict]
) -> str:
    lines = [
        "Outlet: %s" % outlet,
        "Entity: %s (%s)" % (code, kind),
        "Month: %s" % month,
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


# ----------------------------------------------------------------------
# Upsert
# ----------------------------------------------------------------------


def upsert_stance(
    cur,
    outlet: str,
    kind: str,
    code: str,
    entity_country: str | None,
    month: str,
    n_headlines: int,
    obj: dict,
    evidence_ids: list[str],
    tokens_in: int,
    tokens_out: int,
) -> None:
    start, _ = month_bounds(month)
    stance = obj.get("stance") if isinstance(obj, dict) else None
    if stance is not None:
        try:
            stance = int(stance)
            if stance < -2 or stance > 2:
                stance = None
        except (TypeError, ValueError):
            stance = None
    confidence = obj.get("confidence") if isinstance(obj, dict) else None
    if confidence not in ("low", "medium", "high"):
        confidence = None
    tone = obj.get("tone") if isinstance(obj, dict) else None
    patterns = obj.get("patterns") if isinstance(obj, dict) else None
    if patterns is not None and not isinstance(patterns, list):
        patterns = None
    caveats = obj.get("caveats") if isinstance(obj, dict) else None

    cur.execute(
        """
        INSERT INTO outlet_entity_stance
            (outlet_name, entity_kind, entity_code, entity_country, month,
             stance, confidence, tone, patterns, evidence_title_ids, caveats,
             n_headlines, tokens_in, tokens_out)
        VALUES
            (%s, %s, %s, %s, %s::date,
             %s, %s, %s, %s::jsonb, %s::uuid[], %s,
             %s, %s, %s)
        ON CONFLICT (outlet_name, entity_kind, entity_code, month) DO UPDATE SET
            entity_country     = EXCLUDED.entity_country,
            stance             = EXCLUDED.stance,
            confidence         = EXCLUDED.confidence,
            tone               = EXCLUDED.tone,
            patterns           = EXCLUDED.patterns,
            evidence_title_ids = EXCLUDED.evidence_title_ids,
            caveats            = EXCLUDED.caveats,
            n_headlines        = EXCLUDED.n_headlines,
            tokens_in          = EXCLUDED.tokens_in,
            tokens_out         = EXCLUDED.tokens_out,
            computed_at        = NOW()
        """,
        (
            outlet,
            kind,
            code,
            entity_country,
            start,
            stance,
            confidence,
            tone,
            json.dumps(patterns, ensure_ascii=False) if patterns is not None else None,
            evidence_ids,
            caveats,
            n_headlines,
            tokens_in,
            tokens_out,
        ),
    )


# ----------------------------------------------------------------------
# Report
# ----------------------------------------------------------------------


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


def write_report(outlet: str, month: str, conn) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    start, _ = month_bounds(month)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """
        SELECT entity_kind, entity_code, entity_country, n_headlines,
               stance, confidence, tone, patterns, caveats,
               evidence_title_ids::text[] AS evidence_title_ids,
               tokens_in, tokens_out
        FROM outlet_entity_stance
        WHERE outlet_name = %s AND month = %s::date
        ORDER BY n_headlines DESC
        """,
        (outlet, start),
    )
    rows = list(cur.fetchall())

    # Fetch evidence titles
    all_ids: list[str] = []
    for r in rows:
        ids = r["evidence_title_ids"] or []
        all_ids.extend(str(x) for x in ids if x)
    titles_by_id: dict[str, tuple[str, str]] = {}
    if all_ids:
        cur.execute(
            """
            SELECT id::text AS id, detected_language, title_display
            FROM titles_v3 WHERE id = ANY(%s::uuid[])
            """,
            (all_ids,),
        )
        for r in cur.fetchall():
            titles_by_id[r["id"]] = (r["detected_language"], r["title_display"])
    cur.close()

    safe_outlet = re.sub(r"[^A-Za-z0-9._-]+", "_", outlet)
    path = REPORT_DIR / ("%s_%s.md" % (safe_outlet, month))

    lines = ["# Outlet Stance — %s, %s\n" % (outlet, month)]
    if not rows:
        lines.append("_No rows in outlet_entity_stance for this (outlet, month)._\n")
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    tok_in = sum((r["tokens_in"] or 0) for r in rows)
    tok_out = sum((r["tokens_out"] or 0) for r in rows)
    cost = tok_in * (0.14 / 1_000_000) + tok_out * (0.28 / 1_000_000)

    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append("| entities scored | %d |" % len(rows))
    lines.append(
        "| by kind | %d country · %d person |"
        % (
            sum(1 for r in rows if r["entity_kind"] == "country"),
            sum(1 for r in rows if r["entity_kind"] == "person"),
        )
    )
    lines.append("| tokens in / out | %d / %d |" % (tok_in, tok_out))
    lines.append("| cost (est.) | $%.4f |" % cost)
    lines.append("")

    # Matrix-style overview
    lines.append("## Stance overview\n")
    lines.append("| kind | entity | country | n | stance | conf | tone |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in rows:
        country = r["entity_country"] or ""
        entity_label = r["entity_code"]
        lines.append(
            "| %s | %s | %s | %d | %s | %s | %s |"
            % (
                r["entity_kind"],
                entity_label,
                country,
                r["n_headlines"],
                _stance_str(r["stance"]),
                r["confidence"] or "—",
                (r["tone"] or "—")[:60],
            )
        )
    lines.append("")

    # Per-entity detail
    lines.append("## Per-entity detail\n")
    for r in rows:
        heading = "%s · %s" % (r["entity_kind"], r["entity_code"])
        if r["entity_country"]:
            heading += " (%s)" % r["entity_country"]
        lines.append("### %s" % heading)
        lines.append("")
        lines.append(
            "**Stance**: %s · **Confidence**: %s · **Tone**: %s · **n=%d**"
            % (
                _stance_str(r["stance"]),
                r["confidence"] or "—",
                r["tone"] or "—",
                r["n_headlines"],
            )
        )
        lines.append("")
        if r["patterns"]:
            lines.append("Patterns:")
            for p in r["patterns"]:
                lines.append("- %s" % p)
            lines.append("")
        if r["caveats"]:
            lines.append("Caveats: %s" % r["caveats"])
            lines.append("")
        ev_ids = r["evidence_title_ids"] or []
        if ev_ids:
            lines.append("Evidence headlines:")
            for tid in ev_ids:
                tup = titles_by_id.get(str(tid))
                if tup:
                    lang, txt = tup
                    lines.append("- [%s] %s" % (lang, txt))
            lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# ----------------------------------------------------------------------
# Runner
# ----------------------------------------------------------------------


async def process_outlet(
    outlet: str,
    month: str,
    top_n: int,
    min_per_bundle: int,
    sample: int,
    dry_run: bool,
    concurrency: int,
) -> int:
    """Returns number of rows upserted."""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    entities = fetch_top_entities(cur, outlet, month, top_n, min_per_bundle)
    print(
        "  %s: %d entities above %d-headline floor"
        % (outlet, len(entities), min_per_bundle),
        flush=True,
    )
    # Fetch bundles
    bundles = []
    for ent in entities:
        rows = fetch_bundle(cur, outlet, month, ent["kind"], ent["code"], sample)
        if len(rows) < min_per_bundle:
            continue
        country = None
        if ent["kind"] == "person":
            country = infer_person_country(rows)
        bundles.append(
            {
                "kind": ent["kind"],
                "code": ent["code"],
                "country": country,
                "headlines": rows,
            }
        )
    cur.close()

    if dry_run:
        print("  [dry-run] would score %d bundles:" % len(bundles), flush=True)
        for b in bundles:
            print(
                "    %s %s%s n=%d"
                % (
                    b["kind"],
                    b["code"],
                    (" (" + b["country"] + ")") if b["country"] else "",
                    len(b["headlines"]),
                ),
                flush=True,
            )
        conn.close()
        return 0

    # LLM calls
    sem = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient() as client:
        tasks = [
            call_llm(
                client,
                build_user_prompt(outlet, b["kind"], b["code"], month, b["headlines"]),
                sem,
            )
            for b in bundles
        ]
        results = await asyncio.gather(*tasks)

    # Upsert
    cur = conn.cursor()
    written = 0
    for b, (raw, usage, _latency) in zip(bundles, results):
        obj = parse_json(raw) or {}
        # Evidence title ids from the LLM's chosen indices
        ev_idx = obj.get("evidence_idx", []) if isinstance(obj, dict) else []
        ev_title_ids = []
        if isinstance(ev_idx, list):
            for idx in ev_idx:
                try:
                    i = int(idx)
                    if 1 <= i <= len(b["headlines"]):
                        ev_title_ids.append(b["headlines"][i - 1]["title_id"])
                except (TypeError, ValueError):
                    continue
        upsert_stance(
            cur,
            outlet,
            b["kind"],
            b["code"],
            b["country"],
            month,
            len(b["headlines"]),
            obj,
            ev_title_ids,
            usage.get("prompt_tokens", 0),
            usage.get("completion_tokens", 0),
        )
        written += 1
    conn.commit()
    cur.close()
    conn.close()
    return written


async def run(
    outlet: str | None,
    month: str,
    top_n: int,
    min_per_bundle: int,
    sample: int,
    dry_run: bool,
    report: bool,
    concurrency: int,
):
    conn = get_conn()
    cur = conn.cursor()
    if outlet:
        outlets = [outlet]
    else:
        outlets = fetch_qualifying_outlets(cur, month, min_per_bundle)
    cur.close()
    conn.close()
    print(
        "Month %s · outlets to process: %d (min %d titles per entity)"
        % (month, len(outlets), min_per_bundle),
        flush=True,
    )

    t0 = time.time()
    total = 0
    for o in outlets:
        total += await process_outlet(
            o, month, top_n, min_per_bundle, sample, dry_run, concurrency
        )
    wall = time.time() - t0
    print(
        "Done: %d rows written · %.1fs wall" % (total, wall),
        flush=True,
    )

    if report and not dry_run:
        conn = get_conn()
        for o in outlets:
            path = write_report(o, month, conn)
            print("Report: %s" % path, flush=True)
        conn.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outlet", help="Single outlet name; else all above --min-volume")
    ap.add_argument("--month", required=True, help="YYYY-MM")
    ap.add_argument("--top-n", type=int, default=TOP_N_ENTITIES)
    ap.add_argument("--min-per-bundle", type=int, default=MIN_PER_BUNDLE)
    ap.add_argument("--sample", type=int, default=SAMPLE_PER_BUNDLE)
    ap.add_argument("--concurrency", type=int, default=CONCURRENCY)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()

    asyncio.run(
        run(
            args.outlet,
            args.month,
            args.top_n,
            args.min_per_bundle,
            args.sample,
            args.dry_run,
            args.report,
            args.concurrency,
        )
    )


if __name__ == "__main__":
    main()
