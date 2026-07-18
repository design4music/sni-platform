"""Extract an fn_anchor vocabulary bundle from headlines using Deepseek.

Slices the corpus by centroid + optional seed-keyword pre-filter, samples
N headlines balanced across publisher coalitions, sends them to Deepseek
with the fn_anchor extraction rules, and writes the proposed bundle as JSON
in taxonomy_v3 aliases format (10 language keys: ar, de, en, es, fr, hi,
it, ja, ru, zh — empty arrays where Deepseek has no alias).

Usage:
  python scripts/extract_fn_anchor_via_deepseek.py \
      --fn-id iran_nuclear_program \
      --centroid MIDEAST-IRAN \
      --sample-size 200 \
      --window-days 365 \
      --seeds nuclear,enrich,centrifuge,JCPOA,Natanz,Fordow,uranium,IAEA,fissile,atomic,plutonium,snapback,Bushehr,Arak,Fakhrizadeh,AEOI,Parchin

Outputs:
  out/extraction/<fn_id>__<timestamp>.json   - structured proposal
  out/extraction/<fn_id>__<timestamp>.corpus.md  - sample headlines used

Convention: this is curation infrastructure, not a pipeline component.
Run interactively when building or refreshing an FN's anchor bundle.
"""

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx
import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.config import config  # noqa: E402
from core.llm_utils import async_check_rate_limit, extract_json  # noqa: E402

LANG_KEYS = ["ar", "de", "en", "es", "fr", "hi", "it", "ja", "ru", "zh"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--fn-id", required=True, help="friction_nodes.id (linked_id for the bundle)"
    )
    p.add_argument(
        "--centroid", required=True, help="primary centroid_id, e.g. MIDEAST-IRAN"
    )
    p.add_argument("--sample-size", type=int, default=200)
    p.add_argument("--window-days", type=int, default=365)
    p.add_argument(
        "--seeds",
        default="",
        help="Comma-separated topic seed keywords for pre-filtering headlines (substring match).",
    )
    p.add_argument(
        "--out-dir",
        default="out/extraction",
        help="Output directory for JSON + corpus.md.",
    )
    return p.parse_args()


PUBLISHER_COALITIONS = {
    "WESTERN_MAIN": [
        "Reuters",
        "Bloomberg",
        "Associated Press",
        "BBC World",
        "The Guardian",
        "Financial Times",
        "Wall Street Journal",
        "New York Times",
        "The New York Times",
        "Washington Post",
        "The Washington Post",
        "Fox News",
        "CNN",
        "NPR",
        "ABC News",
        "MSNBC",
    ],
    "IRANIAN": [
        "Press TV",
        "IRNA",
        "Fars News",
        "Tasnim News",
        "Mehr News",
        "Al Manar",
        "Al Mayadeen",
    ],
    "RUSSIAN": ["TASS", "TASS (EN)", "RT", "Sputnik"],
    "CHINESE": ["CGTN", "Global Times", "China Daily", "Xinhua"],
    "ISRAELI": [
        "Jerusalem Post",
        "The Jerusalem Post",
        "Times of Israel",
        "Haaretz",
        "Israel Hayom",
        "JNS",
        "Ynet",
        "i24NEWS",
    ],
    "ARAB_TURK": [
        "Al Jazeera",
        "Al Arabiya",
        "Al Arabiya English",
        "Arab News",
        "Al-Ahram",
        "Asharq Al-Awsat",
        "Saudi Gazette",
        "Anadolu Agency",
        "Daily Sabah",
        "The National",
        "Khaleej Times",
        "Gulf News",
    ],
    "EUROPEAN": [
        "Le Monde",
        "Le Figaro",
        "France 24",
        "France 24 (EN)",
        "Euronews",
        "EurActiv",
        "Frankfurter Allgemeine",
        "Handelsblatt",
        "Deutsche Welle",
        "Die Zeit",
        "Die Presse",
        "Corriere della Sera",
        "El Mundo",
        "El País",
    ],
}

COALITION_QUOTAS = {
    "WESTERN_MAIN": 0.25,
    "EUROPEAN": 0.22,
    "ARAB_TURK": 0.15,
    "ISRAELI": 0.12,
    "IRANIAN": 0.10,
    "RUSSIAN": 0.10,
    "CHINESE": 0.06,
}


def fetch_corpus(
    centroid: str, window_days: int, sample_size: int, seeds: list[str]
) -> list[dict]:
    """Sample headlines balanced across publisher coalitions."""
    if not seeds:
        raise SystemExit(
            "--seeds is required: provide at least 3-5 high-confidence topic terms."
        )

    conn = psycopg2.connect(**config.db_connect_kwargs(), cursor_factory=RealDictCursor)
    headlines = []
    try:
        with conn.cursor() as cur:
            for coalition, pubs in PUBLISHER_COALITIONS.items():
                quota = int(sample_size * COALITION_QUOTAS.get(coalition, 0))
                if quota == 0:
                    continue
                cur.execute(
                    """
                    SELECT publisher_name, pubdate_utc::date AS d, title_display
                    FROM titles_v3 t
                    WHERE %s = ANY(centroid_ids)
                      AND pubdate_utc > NOW() - (%s || ' days')::interval
                      AND publisher_name = ANY(%s)
                      AND EXISTS (
                          SELECT 1 FROM unnest(%s::text[]) kw
                          WHERE t.title_display ILIKE '%%' || kw || '%%'
                      )
                    ORDER BY pubdate_utc DESC
                    LIMIT %s
                    """,
                    (centroid, str(window_days), pubs, seeds, quota),
                )
                rows = cur.fetchall()
                for r in rows:
                    headlines.append({**r, "coalition": coalition})
    finally:
        conn.close()
    return headlines


def build_prompt(fn_id: str, headlines: list[dict]) -> tuple[str, str]:
    system = (
        "You are building a topic-vocabulary bundle for a friction node in a news intelligence system. "
        "The bundle's purpose is to match headlines that concern this friction node's phenomenon. "
        "It works in conjunction with an actor centroid filter applied at query time, so the bundle "
        "must be country-neutral: never include country anchors like the actor's name, capital, or general political leadership."
    )
    rules = f"""
You are extracting the fn_anchor vocabulary bundle for friction node `{fn_id}`.

OUTPUT FORMAT (strict — must match the existing taxonomy_v3 aliases shape):
{{
  "bundle": [
    {{
      "term": "<canonical surface form>",
      "type": "entity" | "concept",
      "aliases": {{
         "ar": [...], "de": [...], "en": [...], "es": [...], "fr": [...],
         "hi": [...], "it": [...], "ja": [...], "ru": [...], "zh": [...]
      }},
      "evidence": "<publisher / YYYY-MM-DD>"
    }},
    ...
  ]
}}

RULES:
1) All 10 language keys MUST be present. Use empty arrays [] for languages you don't know the equivalent in. Never invent.
2) Latin-script collapse: if a term spells identically across en/de/fr/es/it, put it in `en` only and leave the other Latin keys empty. Only add to other Latin keys when the spelling differs (e.g., Bushehr=en/es/it, Buschehr=de, Bouchehr=fr).
3) Two flavors of term, both go in the same flat list:
   - FN-specific anchor: named place / program / treaty / organisation / specific person tied to this FN's phenomenon (Natanz, Fordow, JCPOA, IAEA, AEOI, Fakhrizadeh)
   - cross-cutting concept: domain word that, paired with the actor centroid filter, identifies the topic (nuclear, enrichment, centrifuge, uranium, plutonium)
4) EXCLUDE:
   - Actor anchors (country name, capital, supreme political leader, common adjective). The centroid filter handles these.
   - Generic news vocabulary (war, attack, regime, talks, sanctions, threat, deal).
   - Rhetorical phrases that carry stance ("existential threat", "weaponisation", "imperial overreach", "rogue program"). Those belong elsewhere.
   - Substring-redundant compounds: if `nuclear` is in the bundle, do NOT also include `nuclear weapon`, `nuclear facility`, `nuclear program` — the matcher does substring matching, so the base term subsumes compounds. Apply this rule across the whole bundle: keep the shortest distinctive form only.
5) Target ~20-30 terms total. Quality beats quantity. If unsure about specificity, exclude.
6) For each term, cite ONE sample headline from the corpus as evidence.
"""

    corpus_lines = []
    for h in headlines:
        corpus_lines.append(
            f"- [{h['publisher_name']} / {h['coalition']} / {h['d']}] {h['title_display']}"
        )
    user = (
        rules
        + "\n\nCORPUS ("
        + str(len(headlines))
        + " headlines):\n\n"
        + "\n".join(corpus_lines)
    )
    user += "\n\nReturn ONLY the JSON object. No prose before or after."
    return system, user


async def call_deepseek(system: str, user: str) -> dict:
    headers = {
        "Authorization": f"Bearer {config.deepseek_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
        "max_tokens": 8000,
    }
    async with httpx.AsyncClient(timeout=300) as client:
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
                raise RuntimeError(f"LLM HTTP {resp.status_code}: {resp.text[:400]}")
            data = resp.json()
            ms = int((time.time() - t0) * 1000)
            usage = data.get("usage", {})
            print(
                f"  LLM call: {ms}ms  prompt_tokens={usage.get('prompt_tokens')} "
                f"completion_tokens={usage.get('completion_tokens')}"
            )
            return extract_json(data["choices"][0]["message"]["content"])
        raise RuntimeError("LLM retries exhausted")


def normalize_aliases(bundle_item: dict) -> dict:
    """Ensure every term has all 10 language keys (fill missing with [])."""
    aliases = bundle_item.get("aliases", {})
    for k in LANG_KEYS:
        aliases.setdefault(k, [])
    bundle_item["aliases"] = {k: aliases[k] for k in LANG_KEYS}
    return bundle_item


LATIN_SECONDARY = ("de", "fr", "es", "it")


def collapse_latin_duplicates(bundle_item: dict) -> dict:
    """If a Latin-secondary lang has only forms already present in `en`, empty it.

    Matcher does substring matching across all aliases.values() — listing the
    same Latin form in multiple language keys is wasted JSONB. Diverging
    spellings (e.g. Bushehr vs Buschehr) stay in their respective keys.
    """
    a = bundle_item["aliases"]
    en_set = set(a.get("en", []))
    for lang in LATIN_SECONDARY:
        lang_set = set(a.get(lang, []))
        if lang_set and lang_set.issubset(en_set):
            a[lang] = []
    return bundle_item


def main() -> None:
    args = parse_args()
    seeds = [s.strip() for s in args.seeds.split(",") if s.strip()]
    if not seeds:
        raise SystemExit("--seeds is required.")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    stem = f"{args.fn_id}__{timestamp}"

    print(
        f"Fetching corpus: centroid={args.centroid}, window={args.window_days}d, sample={args.sample_size}"
    )
    headlines = fetch_corpus(args.centroid, args.window_days, args.sample_size, seeds)
    print(f"Got {len(headlines)} headlines.")
    from collections import Counter

    coalitions = Counter(h["coalition"] for h in headlines)
    for c, n in coalitions.most_common():
        print(f"  {c}: {n}")

    corpus_path = out_dir / f"{stem}.corpus.md"
    with corpus_path.open("w", encoding="utf-8") as f:
        for h in headlines:
            f.write(
                f"- [{h['publisher_name']} / {h['coalition']} / {h['d']}] {h['title_display']}\n"
            )
    print(f"Wrote corpus: {corpus_path}")

    print("Calling Deepseek...")
    system, user = build_prompt(args.fn_id, headlines)
    result = asyncio.run(call_deepseek(system, user))

    bundle = result.get("bundle", [])
    bundle = [collapse_latin_duplicates(normalize_aliases(item)) for item in bundle]
    out = {
        "metadata": {
            "fn_id": args.fn_id,
            "centroid": args.centroid,
            "window_days": args.window_days,
            "sample_size_requested": args.sample_size,
            "sample_size_actual": len(headlines),
            "seeds": seeds,
            "timestamp": datetime.utcnow().isoformat(),
        },
        "bundle": bundle,
    }
    json_path = out_dir / f"{stem}.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"Wrote bundle: {json_path}")
    print(f"Term count: {len(bundle)}")


if __name__ == "__main__":
    main()
