"""
Generate EN + DE editorial descriptions for every outlet in feeds.

Reads stance data from outlet_entity_stance and general outlet metadata
(name, country, language) to build a two-sentence description per outlet:
  - Sentence 1: what the outlet is (draws on LLM training knowledge)
  - Sentence 2: one specific observation from WorldBrief's coverage data

Stores results in feeds.description + feeds.description_de.

Usage:
  python scripts/generate_outlet_descriptions.py            # skip already-done
  python scripts/generate_outlet_descriptions.py --force    # regenerate all
  python scripts/generate_outlet_descriptions.py --slug reuters  # single outlet
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

import httpx
import psycopg2
import psycopg2.extras

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config

CONCURRENCY = 6
MAX_DESC_CHARS = 360  # target; truncation to 155 chars happens at render time


SYSTEM_PROMPT = """\
You write concise editorial-profile descriptions for a global news intelligence platform called WorldBrief.
Each description appears on the outlet's profile page and as the meta description in Google search results.

Rules:
- Exactly 2 sentences. Total length 250-360 characters including spaces.
- Sentence 1: what the outlet is, where it is based, and what it is known for (use your training knowledge — founding year, parent company, reach, or editorial reputation if notable).
- Sentence 2: If coverage statistics are provided, use the most interesting or surprising insight from the numbers (unusual stance, narrow geographic focus, unexpected coverage of a distant country, stark contrast between two entities). If NO statistics are provided, use a specific editorial angle the outlet is known for — its beat, its ideological tilt, its audience, or a notable fact about its history.
- Never write "no coverage data is available" or any variant — always make sentence 2 substantive.
- Write in third person. No em dashes. No mention of "WorldBrief" in the text.
- German version must be natural, idiomatic German — not a word-for-word translation.
- Return ONLY a JSON object: {"en": "...", "de": "..."}
"""


def build_user_prompt(
    name: str,
    country_code: str | None,
    language_code: str | None,
    source_domain: str | None,
    stance_rows: list[dict],
    total_headlines: int,
) -> str:
    country_label = country_code or "unknown"
    lang_label = language_code or "unknown"

    parts = [
        f"Outlet: {name}",
        f"Country of origin: {country_label}",
        f"Primary language: {lang_label}",
    ]
    if source_domain:
        parts.append(f"Domain: {source_domain}")
    parts.append(f"Total headlines analyzed by WorldBrief: {total_headlines}")

    if stance_rows:
        parts.append("\nTop entities covered (by headline volume):")
        for r in stance_rows[:8]:
            stance_val = r["stance"]
            if stance_val is None:
                stance_str = "unscored"
            elif stance_val >= 1:
                stance_str = "sympathetic"
            elif stance_val <= -1:
                stance_str = "critical"
            else:
                stance_str = "neutral"
            tone_note = f' — "{r["tone"]}"' if r["tone"] else ""
            parts.append(
                f"  {r['entity_code']} ({r['entity_kind']}): "
                f"{r['n_headlines']} headlines, stance={stance_str}{tone_note}"
            )
    else:
        parts.append("\nNo detailed stance data available for this outlet.")

    return "\n".join(parts)


async def call_deepseek(prompt: str) -> dict:
    headers = {
        "Authorization": "Bearer %s" % config.deepseek_api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.llm_model,
        "temperature": 0.5,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    }
    async with httpx.AsyncClient(timeout=60) as client:
        for attempt in range(3):
            resp = await client.post(
                "%s/chat/completions" % config.deepseek_api_url,
                headers=headers,
                json=payload,
            )
            if resp.status_code == 429:
                wait = 5 * (attempt + 1)
                print("  rate-limited, waiting %ds" % wait)
                await asyncio.sleep(wait)
                continue
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return json.loads(content)
    raise RuntimeError("DeepSeek failed after 3 attempts")


def load_outlets(conn, slug_filter: str | None) -> list[dict]:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        if slug_filter:
            cur.execute(
                """
                SELECT id, name, slug, country_code, language_code, source_domain,
                       description, description_de
                  FROM feeds
                 WHERE is_active = true AND slug IS NOT NULL
                   AND slug = %s
                """,
                (slug_filter,),
            )
        else:
            cur.execute(
                """
                SELECT id, name, slug, country_code, language_code, source_domain,
                       description, description_de
                  FROM feeds
                 WHERE is_active = true AND slug IS NOT NULL
                 ORDER BY name
                """
            )
        return [dict(r) for r in cur.fetchall()]


def load_stance_data(conn, feed_name: str) -> tuple[list[dict], int]:
    """Return (stance_rows ordered by headline volume, total_headline_count)."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT entity_code, entity_kind,
                   SUM(n_headlines)  AS n_headlines,
                   AVG(stance)::float AS stance,
                   MAX(tone)          AS tone
              FROM outlet_entity_stance
             WHERE outlet_name = %s
             GROUP BY entity_code, entity_kind
             ORDER BY n_headlines DESC
            """,
            (feed_name,),
        )
        rows = [dict(r) for r in cur.fetchall()]
        total = sum(int(r["n_headlines"]) for r in rows)
    return rows, total


def save_description(conn, feed_id: str, en: str, de: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE feeds SET description = %s, description_de = %s WHERE id = %s",
            (en, de, feed_id),
        )
    conn.commit()


async def process_outlet(
    sem: asyncio.Semaphore,
    conn,
    outlet: dict,
    force: bool,
) -> None:
    name = outlet["name"]
    slug = outlet["slug"]

    if not force and outlet["description"]:
        print("SKIP %s (already done)" % slug)
        return

    async with sem:
        print("GEN  %s ..." % slug)
        stance_rows, total_headlines = load_stance_data(conn, name)
        prompt = build_user_prompt(
            name=name,
            country_code=outlet["country_code"],
            language_code=outlet["language_code"],
            source_domain=outlet["source_domain"],
            stance_rows=stance_rows,
            total_headlines=total_headlines,
        )
        try:
            result = await call_deepseek(prompt)
            en = (result.get("en") or "").strip()
            de = (result.get("de") or "").strip()
            if not en or not de:
                print("  WARN: empty response for %s" % slug)
                return
            # Soft-warn if over target length; truncateDescription on the
            # frontend caps the meta description to 155 chars automatically.
            if len(en) > MAX_DESC_CHARS:
                print(
                    "  WARN: EN desc %d chars (target <=%d)" % (len(en), MAX_DESC_CHARS)
                )
            save_description(conn, outlet["id"], en, de)
            print("  OK   %s (%d/%d chars)" % (slug, len(en), len(de)))
        except Exception as exc:
            print("  ERR  %s: %s" % (slug, exc))


async def main(force: bool, slug_filter: str | None) -> None:
    conn = psycopg2.connect(**config.db_connect_kwargs())
    outlets = load_outlets(conn, slug_filter)
    pending = [o for o in outlets if force or not o["description"]]
    done = len(outlets) - len(pending)

    print(
        "Outlets: %d total, %d already done, %d to generate"
        % (len(outlets), done, len(pending))
    )
    if not pending:
        print("Nothing to do.")
        return

    sem = asyncio.Semaphore(CONCURRENCY)
    tasks = [process_outlet(sem, conn, outlet, force) for outlet in pending]
    await asyncio.gather(*tasks)
    conn.close()
    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--force", action="store_true", help="Regenerate even if already done"
    )
    parser.add_argument(
        "--slug", type=str, default=None, help="Process a single outlet by slug"
    )
    args = parser.parse_args()
    asyncio.run(main(force=args.force, slug_filter=args.slug))
