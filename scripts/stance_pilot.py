"""Stance detection pilot — 1000 stratified titles, LLM-only.

Sample: 500 EN + 125 DE + 125 RU + 125 AR + 125 JA. March 2026.
Per-title LLM call with tight stance prompt.
Writes results.csv + raw.jsonl + report.md under out/stance_pilot/.

Usage:
    python scripts/stance_pilot.py [--limit-per-lang N] [--concurrency 5]
"""

import argparse
import asyncio
import csv
import json
import random
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import httpx
import psycopg2
from psycopg2.extras import RealDictCursor

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config

SAMPLE = {"en": 500, "de": 125, "ru": 125, "ar": 125, "ja": 125}
SAMPLE_SMOKE = {"en": 3, "de": 2, "ru": 2, "ar": 2, "ja": 1}
MONTH_START = "2026-03-01"
MONTH_END = "2026-04-01"
OUT_DIR = Path("out/stance_pilot")

VERSION = "v5"
BATCH_SIZE = 25

STANCE_SYSTEM = """Editorial stance = the publisher's OWN vocabulary passing moral/political judgment on an entity.

CRITICAL RULE: only flag vocabulary that is POLARITY-STABLE across publishers — words any reader, regardless of political alignment, would read as positive or negative for the target. Action verbs (strikes, attacks, hits, mocks, defies, slams, cracks down, targets) are NOT polarity-stable: "Trump struck at Zelensky's strategy" reads as praise in a pro-Russian outlet and as criticism in a pro-Ukrainian one. The headline alone cannot resolve this.

Return a JSON array, one object per headline: {"s":"r"|"f","t":[]}

For s=f, t is a list of: {"k":"c"|"p","i":ISO2,"n":name (only k=p),"v":-2|-1|1|2,"w":[2-3 verbatim phrases]}
k=c: country/state itself framed. k=p: named public figure framed individually.

Mark s=f ONLY when the headline's own words contain:
  (a) Polarity-stable evaluative vocabulary — condemns any actor (regime, junta, thugs, brutal, ruthless, atrocity, massacre, unprovoked, illegal, reckless, so-called, scare-quotes) OR lionises any actor (hero, martyr, brave, liberator, liberation, heroic) OR possessive blaming ("Putin's war", "Netanyahu's war").
  (b) Attached to a specific entity.
  (c) In the publisher's own voice — NOT inside quotation marks and NOT attributed to a speaker ("X says Y", "X: 'Y'", "'Y', X claims").

s=r for EVERYTHING ELSE, including:
  - Action verbs, even dramatic ones (strikes, attacks, kills, blows up, hits, slams, mocks, defies, cracks down, detains, targets, warns) — ideologically ambiguous.
  - Casualties / scale (100 killed, massive, wave of)
  - Reported criticism (X criticizes Y)
  - Official actions (signs, announces, issues, rejects)
  - Evaluative words inside quotes or attributed to a speaker.

Examples:
  "Putin's unprovoked aggression enters year 4" → s=f, RU -2 (possessive blame + "unprovoked aggression" in publisher's voice)
  "Russia strikes Ukraine power grid" → s=r (action verb, ideologically ambiguous)
  "Трамп нанес удар по стратегии Зеленского" → s=r (action verb; valence depends on publisher)
  "'Unprovoked aggression,' Russia claims Israel attacked" → s=r ("unprovoked aggression" is Russia's quote, not publisher's voice)
  "Brutal Israeli strikes kill 47 in Rafah hospital" → s=f, IL -2 ("brutal" is publisher's word)
  "China's crackdown on Uyghurs continues" → s=f, CN -2 ("crackdown" is condemnatory noun)
  "Netanyahu Says Iran's 'Blackmail' Won't Work" → s=r ("blackmail" is Netanyahu's quote)
  "Trump mocks Newsom's dyslexia" → s=r (action verb "mocks" describes Trump's action neutrally)

v=-2/+2 for strongest editorialising (regime, atrocity, hero, liberator, unprovoked aggression).
v=-1/+1 for milder (so-called, possessive blame, crackdown).
For k=p, use internationally-known Latin-script name if available (Trump, Putin, Xi, Netanyahu).
Markers (w) verbatim from headline, original script.
When in doubt, s=r. Most headlines are factual reporting."""


def get_conn():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        dbname=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def sample_titles_by_ids(title_ids: list[str]) -> list[dict]:
    """Re-fetch same titles for apples-to-apples comparison. Includes persons[]."""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """
        SELECT t.id::text AS title_id,
               t.detected_language AS language,
               t.pubdate_utc,
               t.title_display,
               t.publisher_name,
               tl.sector,
               tl.subject,
               tl.actor,
               tl.action_class,
               tl.target,
               tl.entity_countries,
               tl.persons
        FROM titles_v3 t
        JOIN title_labels tl ON tl.title_id = t.id
        WHERE t.id = ANY(%s::uuid[])
        """,
        (title_ids,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]


def sample_titles(limit_per_lang: dict) -> list[dict]:
    """Stratified random sample per language, March 2026, strategic, non-empty entity_countries."""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    rows = []
    for lang, n in limit_per_lang.items():
        cur.execute(
            """
            SELECT t.id::text AS title_id,
                   t.detected_language AS language,
                   t.pubdate_utc,
                   t.title_display,
                   t.publisher_name,
                   tl.sector,
                   tl.subject,
                   tl.actor,
                   tl.action_class,
                   tl.target,
                   tl.entity_countries,
                   tl.persons
            FROM titles_v3 t
            JOIN title_labels tl ON tl.title_id = t.id
            WHERE t.pubdate_utc >= %s::date
              AND t.pubdate_utc <  %s::date
              AND t.detected_language = %s
              AND tl.entity_countries IS NOT NULL
              AND tl.entity_countries <> '{}'::jsonb
              AND tl.sector <> 'NON_STRATEGIC'
            ORDER BY random()
            LIMIT %s
            """,
            (MONTH_START, MONTH_END, lang, n),
        )
        got = cur.fetchall()
        rows.extend(got)
        print("sampled %d for lang=%s" % (len(got), lang), flush=True)
    cur.close()
    conn.close()
    return [dict(r) for r in rows]


def build_batched_user(batch: list[dict]) -> str:
    """One user prompt for a batch of up to BATCH_SIZE titles."""
    lines = [
        "Rate each headline below. Return JSON array of %d objects." % len(batch),
        "",
    ]
    for i, row in enumerate(batch, 1):
        ec = row.get("entity_countries") or {}
        if isinstance(ec, str):
            ec = json.loads(ec)
        iso_codes = sorted(set(v for v in ec.values() if v))
        ec_str = ",".join(iso_codes) if iso_codes else "-"
        lines.append("%d. %s | ec:%s" % (i, row["title_display"], ec_str))
    return "\n".join(lines)


async def call_llm_batch_async(
    client: httpx.AsyncClient, system: str, user: str, sem: asyncio.Semaphore
) -> tuple[str, dict, float]:
    headers = {
        "Authorization": "Bearer %s" % config.deepseek_api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.0,
        "max_tokens": 4000,
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


def _extract_json_array(text: str):
    """Tolerant JSON array parser. Returns list or None."""
    if not text:
        return None
    t = text.strip()
    # Strip markdown fences
    m = re.search(r"```(?:json)?\s*(.*?)\s*```", t, re.DOTALL)
    if m:
        t = m.group(1).strip()
    try:
        obj = json.loads(t)
    except json.JSONDecodeError:
        m = re.search(r"\[.*\]", t, re.DOTALL)
        if not m:
            return None
        try:
            obj = json.loads(m.group())
        except json.JSONDecodeError:
            return None
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict) and "results" in obj:
        return obj["results"]
    return None


def _normalise_target(tt: dict) -> dict | None:
    """Compact LLM keys (k/i/n/v/w) -> canonical (t/c/name/p/m). Validates."""
    kind = tt.get("k") or tt.get("t")
    if kind == "c":
        kind = "country"
    elif kind == "p":
        kind = "person"
    if kind not in ("country", "person"):
        return None
    c = tt.get("i") or tt.get("c") or ""
    if not isinstance(c, str) or len(c) < 2 or len(c) > 3:
        return None
    v = tt.get("v")
    if v is None:
        v = tt.get("p")
    try:
        v = int(v)
    except (TypeError, ValueError):
        return None
    if v not in (-2, -1, 1, 2):
        return None
    w = tt.get("w") or tt.get("m") or []
    if not isinstance(w, list):
        w = []
    name = tt.get("n") or tt.get("name") or ""
    if kind == "person" and not name:
        return None
    entry = {"t": kind, "c": c.upper(), "p": v, "m": [str(x)[:80] for x in w][:3]}
    if kind == "person":
        entry["name"] = str(name)[:60]
    return entry


def parse_batch_response(raw: str, batch_size: int) -> list[tuple[str, list]]:
    """Returns list of (mode, targets) aligned with input order.

    If the response is invalid/short, missing slots get ('error', [])."""
    arr = _extract_json_array(raw)
    out = []
    if arr is None:
        return [("error", []) for _ in range(batch_size)]
    for item in arr[:batch_size]:
        if not isinstance(item, dict):
            out.append(("error", []))
            continue
        s = item.get("s") or item.get("mode")
        if s == "r":
            s = "report"
        elif s == "f":
            s = "framed"
        if s not in ("report", "framed"):
            out.append(("error", []))
            continue
        targets_raw = item.get("t") or item.get("targets") or []
        clean = []
        for tt in targets_raw:
            if not isinstance(tt, dict):
                continue
            norm = _normalise_target(tt)
            if norm:
                clean.append(norm)
        out.append((s, clean))
    # Pad if LLM returned fewer items than expected
    while len(out) < batch_size:
        out.append(("error", []))
    return out


def _normalise_script(s: str) -> str:
    """Lowercase + strip diacritics for matching."""
    import unicodedata

    nkfd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nkfd if not unicodedata.combining(c)).lower().strip()


def canonicalise_name(raw_name: str, persons_list: list, actor: str) -> tuple[str, str]:
    """Return (canonical_name, source) using title_labels.persons[] + actor.

    source in {'persons', 'actor', 'none'}.
    Simple substring match on script-normalised forms.
    """
    if not raw_name:
        return ("", "none")
    raw_n = _normalise_script(raw_name)
    persons_list = persons_list or []
    for p in persons_list:
        if not isinstance(p, str):
            continue
        pn = _normalise_script(p)
        if not pn:
            continue
        if raw_n in pn or pn in raw_n:
            return (p, "persons")
    # Fallback: actor field (less likely to contain a person name)
    if actor and isinstance(actor, str):
        an = _normalise_script(actor)
        if an and (raw_n in an or an in raw_n):
            return (actor, "actor")
    return ("", "none")


async def run_pilot(
    rows: list[dict], concurrency: int, raw_fp, csv_writer
) -> list[dict]:
    sem = asyncio.Semaphore(concurrency)
    results = []
    # Chunk into batches of BATCH_SIZE
    batches = [rows[i : i + BATCH_SIZE] for i in range(0, len(rows), BATCH_SIZE)]
    print("Batched: %d batches of up to %d" % (len(batches), BATCH_SIZE), flush=True)
    async with httpx.AsyncClient() as client:
        tasks = [
            call_llm_batch_async(client, STANCE_SYSTEM, build_batched_user(b), sem)
            for b in batches
        ]
        # Process batches as they complete for live progress
        completed = 0
        raw_results = [None] * len(batches)

        async def _runner(i, coro):
            nonlocal completed
            raw_results[i] = await coro
            completed += 1
            if completed % 5 == 0 or completed == len(batches):
                print("  batches done: %d/%d" % (completed, len(batches)), flush=True)

        await asyncio.gather(*[_runner(i, t) for i, t in enumerate(tasks)])

    # Assemble per-title results, distribute batch-level usage proportionally
    for batch, (raw, usage, latency) in zip(batches, raw_results):
        parsed = parse_batch_response(raw, len(batch))
        # Token accounting: divide batch usage across titles (simplest fair split)
        bt_in = usage.get("prompt_tokens", 0)
        bt_out = usage.get("completion_tokens", 0)
        per_in = bt_in / len(batch) if batch else 0
        per_out = bt_out / len(batch) if batch else 0

        raw_fp.write(
            json.dumps(
                {
                    "batch_title_ids": [r["title_id"] for r in batch],
                    "raw": raw,
                },
                ensure_ascii=False,
            )
            + "\n"
        )

        for row, (mode, targets) in zip(batch, parsed):
            # persons[] post-processing for person targets
            persons = row.get("persons") or []
            for tgt in targets:
                if tgt["t"] != "person":
                    continue
                canonical, source = canonicalise_name(
                    tgt.get("name", ""), persons, row.get("actor") or ""
                )
                tgt["name_canonical"] = canonical
                tgt["name_match_source"] = source

            rec = {
                "title_id": row["title_id"],
                "language": row["language"],
                "sector": row["sector"] or "",
                "subject": row["subject"] or "",
                "actor": row["actor"] or "",
                "action_class": row["action_class"] or "",
                "target": row["target"] or "",
                "publisher": row["publisher_name"] or "",
                "pubdate": row["pubdate_utc"].isoformat() if row["pubdate_utc"] else "",
                "title_display": row["title_display"],
                "entity_countries": json.dumps(
                    row["entity_countries"], ensure_ascii=False
                ),
                "persons_labels": json.dumps(
                    row.get("persons") or [], ensure_ascii=False
                ),
                "llm_mode": mode,
                "llm_targets_json": json.dumps(targets, ensure_ascii=False),
                "tokens_in": round(per_in, 1),
                "tokens_out": round(per_out, 1),
                "latency_s": round(latency, 3),
            }
            results.append(rec)
            csv_writer.writerow(rec)
    return results


def summarise(results: list[dict]) -> str:
    total = len(results)
    by_lang = defaultdict(list)
    for r in results:
        by_lang[r["language"]].append(r)

    def pct(n, d):
        return "%5.1f%%" % (100.0 * n / d) if d else "  n/a"

    def pdist(rs):
        c = Counter()
        for r in rs:
            if r["llm_mode"] != "framed":
                continue
            for t in json.loads(r["llm_targets_json"]):
                c[t["p"]] += 1
        return c

    lines = []
    lines.append("# Stance Pilot Report — %s\n" % VERSION)
    lines.append(
        "Sample: %d titles, March 2026, strategic + non-empty entity_countries. Batch=%d."
        % (total, BATCH_SIZE)
    )
    lines.append("")

    # Global
    framed = sum(1 for r in results if r["llm_mode"] == "framed")
    report = sum(1 for r in results if r["llm_mode"] == "report")
    errors = sum(1 for r in results if r["llm_mode"] == "error")
    tok_in = sum(r["tokens_in"] for r in results)
    tok_out = sum(r["tokens_out"] for r in results)
    avg_lat = sum(r["latency_s"] for r in results) / max(total, 1)
    targets_tot = sum(len(json.loads(r["llm_targets_json"])) for r in results)

    lines.append("## Global")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append("| Total titles   | %d |" % total)
    lines.append("| `framed`       | %d (%s) |" % (framed, pct(framed, total)))
    lines.append("| `report`       | %d (%s) |" % (report, pct(report, total)))
    lines.append("| parse error    | %d (%s) |" % (errors, pct(errors, total)))
    lines.append("| targets/framed | %.2f |" % (targets_tot / framed if framed else 0))
    lines.append("| tokens in (sum)  | %d |" % tok_in)
    lines.append("| tokens out (sum) | %d |" % tok_out)
    lines.append("| tokens in/title (avg)  | %.1f |" % (tok_in / total if total else 0))
    lines.append(
        "| tokens out/title (avg) | %.1f |" % (tok_out / total if total else 0)
    )
    lines.append("| latency/title (avg) | %.2fs |" % avg_lat)
    lines.append("")
    lines.append("### Global polarity distribution (across all framed targets)")
    lines.append("")
    gd = pdist(results)
    lines.append("| p | count |")
    lines.append("|---|---|")
    for p in (-2, -1, 1, 2):
        lines.append("| %+d | %d |" % (p, gd.get(p, 0)))
    lines.append("")

    # Per-language
    lines.append("## Per language")
    lines.append("")
    lines.append(
        "| lang | n | framed | report | err | tgt/fr | p:-2 | p:-1 | p:+1 | p:+2 | tok in/out avg |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for lang in ("en", "de", "ru", "ar", "ja"):
        rs = by_lang.get(lang, [])
        n = len(rs)
        if n == 0:
            continue
        fr = sum(1 for r in rs if r["llm_mode"] == "framed")
        rp = sum(1 for r in rs if r["llm_mode"] == "report")
        er = sum(1 for r in rs if r["llm_mode"] == "error")
        tpf = sum(len(json.loads(r["llm_targets_json"])) for r in rs) / fr if fr else 0
        d = pdist(rs)
        ti = sum(r["tokens_in"] for r in rs) / n
        to = sum(r["tokens_out"] for r in rs) / n
        lines.append(
            "| %s | %d | %d (%s) | %d (%s) | %d | %.2f | %d | %d | %d | %d | %.0f / %.0f |"
            % (
                lang,
                n,
                fr,
                pct(fr, n),
                rp,
                pct(rp, n),
                er,
                tpf,
                d.get(-2, 0),
                d.get(-1, 0),
                d.get(1, 0),
                d.get(2, 0),
                ti,
                to,
            )
        )
    lines.append("")

    # Per-sector (EN only — largest sample)
    en_rows = by_lang.get("en", [])
    lines.append("## Per sector (English only, n=%d)" % len(en_rows))
    lines.append("")
    bysec = defaultdict(list)
    for r in en_rows:
        bysec[r["sector"] or "UNKNOWN"].append(r)
    lines.append("| sector | n | framed | report | err |")
    lines.append("|---|---|---|---|---|")
    for sec, rs in sorted(bysec.items(), key=lambda kv: -len(kv[1])):
        n = len(rs)
        fr = sum(1 for r in rs if r["llm_mode"] == "framed")
        rp = sum(1 for r in rs if r["llm_mode"] == "report")
        er = sum(1 for r in rs if r["llm_mode"] == "error")
        lines.append(
            "| %s | %d | %d (%s) | %d (%s) | %d |"
            % (sec, n, fr, pct(fr, n), rp, pct(rp, n), er)
        )
    lines.append("")

    # Cost projection
    lines.append("## Cost projection")
    lines.append("")
    per_title_in = tok_in / total if total else 0
    per_title_out = tok_out / total if total else 0
    # DeepSeek chat cached-hit pricing — indicative only
    rate_in = 0.14 / 1_000_000
    rate_out = 0.28 / 1_000_000
    eur_per_title = per_title_in * rate_in + per_title_out * rate_out
    for label, n in (("March 2026", 63_193), ("Jan-Apr 2026", 126_000)):
        lines.append("- %s (%d titles): est ~$%.2f" % (label, n, eur_per_title * n))
    lines.append("")

    # Target type split
    def all_targets(rs):
        out = []
        for r in rs:
            if r["llm_mode"] != "framed":
                continue
            for t in json.loads(r["llm_targets_json"]):
                out.append(t)
        return out

    gtgts = all_targets(results)
    country_tgts = [t for t in gtgts if t.get("t", "country") == "country"]
    person_tgts = [t for t in gtgts if t.get("t") == "person"]

    lines.append("## Target types (all languages)")
    lines.append("")
    lines.append("| type | count | share |")
    lines.append("|---|---|---|")
    lines.append(
        "| country | %d | %s |"
        % (len(country_tgts), pct(len(country_tgts), len(gtgts)))
    )
    lines.append(
        "| person  | %d | %s |" % (len(person_tgts), pct(len(person_tgts), len(gtgts)))
    )
    lines.append("")

    # Top framed persons
    person_counts = Counter()
    person_polarity = defaultdict(list)
    for t in person_tgts:
        key = (t["name"], t["c"])
        person_counts[key] += 1
        person_polarity[key].append(t["p"])

    lines.append("## Top framed persons")
    lines.append("")
    lines.append("| name | country | n | avg p | polarity mix |")
    lines.append("|---|---|---|---|---|")
    for (name, c), n in person_counts.most_common(20):
        pols = person_polarity[(name, c)]
        avg = sum(pols) / len(pols)
        mix = ", ".join("%+d×%d" % (p, pols.count(p)) for p in sorted(set(pols)))
        lines.append("| %s | %s | %d | %+.2f | %s |" % (name, c, n, avg, mix))
    lines.append("")

    # Top framed countries
    country_counts = Counter()
    country_polarity = defaultdict(list)
    for t in country_tgts:
        country_counts[t["c"]] += 1
        country_polarity[t["c"]].append(t["p"])

    lines.append("## Top framed countries (direct framing only)")
    lines.append("")
    lines.append("| country | n | avg p | polarity mix |")
    lines.append("|---|---|---|---|")
    for c, n in country_counts.most_common(15):
        pols = country_polarity[c]
        avg = sum(pols) / len(pols)
        mix = ", ".join("%+d×%d" % (p, pols.count(p)) for p in sorted(set(pols)))
        lines.append("| %s | %d | %+.2f | %s |" % (c, n, avg, mix))
    lines.append("")

    # Name canonicalisation metrics (v3+)
    lines.append("## Name canonicalisation (person targets only)")
    lines.append("")
    match_by_lang = defaultdict(lambda: Counter())
    by_lang_person_tgts = defaultdict(list)
    for r in results:
        if r["llm_mode"] != "framed":
            continue
        for t in json.loads(r["llm_targets_json"]):
            if t.get("t") != "person":
                continue
            by_lang_person_tgts[r["language"]].append(t)
            src = t.get("name_match_source") or "none"
            match_by_lang[r["language"]][src] += 1
    lines.append(
        "| lang | person targets | persons[] match | actor match | no match | match rate |"
    )
    lines.append("|---|---|---|---|---|---|")
    for lang in ("en", "de", "ru", "ar", "ja"):
        total_l = len(by_lang_person_tgts.get(lang, []))
        if total_l == 0:
            continue
        c = match_by_lang[lang]
        matched = c["persons"] + c["actor"]
        lines.append(
            "| %s | %d | %d | %d | %d | %s |"
            % (
                lang,
                total_l,
                c["persons"],
                c["actor"],
                c["none"],
                pct(matched, total_l),
            )
        )
    lines.append("")

    # Diff across v1/v2/v3
    version_paths = [
        ("v1", Path("out/stance_pilot_v1/results.csv")),
        ("v2", Path("out/stance_pilot_v2/results.csv")),
    ]
    loaded = []
    for label, p in version_paths:
        if p.exists():
            rows_by_id = {}
            for rr in csv.DictReader(open(p, encoding="utf-8")):
                rows_by_id[rr["title_id"]] = rr
            loaded.append((label, rows_by_id))
    # Current (v3) as a dict too
    current_by_id = {r["title_id"]: r for r in results}
    loaded.append((VERSION, current_by_id))

    if len(loaded) >= 2:
        lines.append("## Diff across versions")
        lines.append("")

        def framed_count(rows_by_id):
            return sum(1 for r in rows_by_id.values() if r["llm_mode"] == "framed")

        def strong_titles(rows_by_id):
            c = 0
            for r in rows_by_id.values():
                if r["llm_mode"] != "framed":
                    continue
                tgts = json.loads(r["llm_targets_json"])
                if any(t["p"] in (-2, 2) for t in tgts):
                    c += 1
            return c

        def avg_tokens(rows_by_id):
            vals_in = [float(r.get("tokens_in", 0) or 0) for r in rows_by_id.values()]
            vals_out = [float(r.get("tokens_out", 0) or 0) for r in rows_by_id.values()]
            n = len(vals_in) or 1
            return sum(vals_in) / n, sum(vals_out) / n

        lines.append("| metric | " + " | ".join(lbl for lbl, _ in loaded) + " |")
        lines.append("|---|" + "|".join(["---"] * len(loaded)) + "|")
        row_n = (
            "| titles paired | " + " | ".join("%d" % len(d) for _, d in loaded) + " |"
        )
        lines.append(row_n)
        row_fr = (
            "| framed rate | "
            + " | ".join(pct(framed_count(d), len(d)) for _, d in loaded)
            + " |"
        )
        lines.append(row_fr)
        row_st = (
            "| strong-pole titles | "
            + " | ".join(pct(strong_titles(d), len(d)) for _, d in loaded)
            + " |"
        )
        lines.append(row_st)
        avg_cells = []
        for _, d in loaded:
            ai, ao = avg_tokens(d)
            avg_cells.append("%.0f / %.0f" % (ai, ao))
        lines.append("| avg tokens in/out | " + " | ".join(avg_cells) + " |")
        lines.append("")

        # Pair-wise mode flips between last two versions
        if len(loaded) >= 2:
            prev_label, prev = loaded[-2]
            curr_label, curr = loaded[-1]
            common = [tid for tid in curr if tid in prev]
            n = len(common)
            if n:
                f2r = sum(
                    1
                    for tid in common
                    if prev[tid]["llm_mode"] == "framed"
                    and curr[tid]["llm_mode"] == "report"
                )
                r2f = sum(
                    1
                    for tid in common
                    if prev[tid]["llm_mode"] == "report"
                    and curr[tid]["llm_mode"] == "framed"
                )
                lines.append(
                    "Flips from **%s → %s** on %d paired titles: framed→report %d (%s), report→framed %d (%s)"
                    % (prev_label, curr_label, n, f2r, pct(f2r, n), r2f, pct(r2f, n))
                )
                lines.append("")

    lines.append("## Sample rows (20 random framed)")
    lines.append("")
    framed_rows = [r for r in results if r["llm_mode"] == "framed"]
    sample = random.sample(framed_rows, min(20, len(framed_rows)))
    lines.append("| lang | sector | targets | title |")
    lines.append("|---|---|---|---|")
    for r in sample:
        tgts = json.loads(r["llm_targets_json"])

        def fmt_t(t):
            lbl = (
                t["c"]
                if t.get("t", "country") == "country"
                else "%s(%s)"
                % (
                    t.get("name", "?"),
                    t["c"],
                )
            )
            return "%s%+d [%s]" % (lbl, t["p"], " / ".join(t["m"]))

        tgts_str = "; ".join(fmt_t(t) for t in tgts)
        title = r["title_display"].replace("|", "¦")[:120]
        lines.append(
            "| %s | %s | %s | %s |" % (r["language"], r["sector"], tgts_str, title)
        )
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--concurrency", type=int, default=5)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--smoke", action="store_true", help="Run 10-title smoke test")
    ap.add_argument(
        "--reuse-sample",
        type=str,
        default=None,
        help="Path to existing results.csv — reuse same title_ids for deterministic diff",
    )
    args = ap.parse_args()
    random.seed(args.seed)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.reuse_sample:
        print("Reusing sample from: %s" % args.reuse_sample, flush=True)
        with open(args.reuse_sample, encoding="utf-8") as f:
            rdr = csv.DictReader(f)
            ids = [r["title_id"] for r in rdr]
        rows = sample_titles_by_ids(ids)
        # Preserve order from the source CSV for reproducibility
        by_id = {r["title_id"]: r for r in rows}
        rows = [by_id[i] for i in ids if i in by_id]
    else:
        print("Sampling titles...", flush=True)
        rows = sample_titles(SAMPLE_SMOKE if args.smoke else SAMPLE)
    print("Total sampled: %d" % len(rows), flush=True)

    csv_path = OUT_DIR / "results.csv"
    raw_path = OUT_DIR / "raw.jsonl"
    report_path = OUT_DIR / "report.md"

    fieldnames = [
        "title_id",
        "language",
        "sector",
        "subject",
        "actor",
        "action_class",
        "target",
        "publisher",
        "pubdate",
        "title_display",
        "entity_countries",
        "persons_labels",
        "llm_mode",
        "llm_targets_json",
        "tokens_in",
        "tokens_out",
        "latency_s",
    ]

    t0 = time.time()
    with open(csv_path, "w", newline="", encoding="utf-8") as f_csv, open(
        raw_path, "w", encoding="utf-8"
    ) as f_raw:
        writer = csv.DictWriter(f_csv, fieldnames=fieldnames)
        writer.writeheader()
        results = asyncio.run(
            run_pilot(
                rows, concurrency=args.concurrency, raw_fp=f_raw, csv_writer=writer
            )
        )
    wall = time.time() - t0
    print("Pilot done in %.1fs (wall clock)" % wall, flush=True)

    report = summarise(results)
    report_path.write_text(report, encoding="utf-8")
    print("Wrote: %s" % csv_path, flush=True)
    print("Wrote: %s" % raw_path, flush=True)
    print("Wrote: %s" % report_path, flush=True)


if __name__ == "__main__":
    main()
