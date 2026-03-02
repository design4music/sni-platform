"""Translate centroid strategic briefs (profile_json) to German.

Adds a 'profile_json_de' JSONB column to centroids_v3 if not present,
then translates each centroid's brief section-by-section.
"""

import asyncio
import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from core.config import config

CONCURRENCY = 3


async def translate_text(client: httpx.AsyncClient, text: str) -> str | None:
    """Translate text to German via DeepSeek."""
    headers = {
        "Authorization": "Bearer %s" % config.deepseek_api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.llm_model,
        "messages": [
            {
                "role": "system",
                "content": "Translate the following text to German. "
                "Return only the translation. Preserve JSON structure if present.",
            },
            {"role": "user", "content": text},
        ],
        "temperature": 0.2,
        "max_tokens": min(len(text) * 2, 4000),
    }
    try:
        response = await client.post(
            "%s/chat/completions" % config.deepseek_api_url,
            headers=headers,
            json=payload,
        )
        if response.status_code != 200:
            return None
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


async def translate_profile(client: httpx.AsyncClient, profile: dict) -> dict:
    """Translate a GeoBriefProfile dict, section by section."""
    result = dict(profile)

    # Translate sections
    if "sections" in profile and profile["sections"]:
        translated_sections = []
        for section in profile["sections"]:
            new_section = dict(section)
            # Translate title
            if section.get("title"):
                t = await translate_text(client, section["title"])
                if t:
                    new_section["title"] = t
            # Translate intro
            if section.get("intro"):
                t = await translate_text(client, section["intro"])
                if t:
                    new_section["intro"] = t
            # Translate bullets
            if section.get("bullets"):
                bullets_text = "\n".join(section["bullets"])
                t = await translate_text(client, bullets_text)
                if t:
                    new_section["bullets"] = t.split("\n")
            # Translate groups
            if section.get("groups"):
                new_groups = []
                for group in section["groups"]:
                    new_group = dict(group)
                    if group.get("title"):
                        t = await translate_text(client, group["title"])
                        if t:
                            new_group["title"] = t
                    if group.get("bullets"):
                        bullets_text = "\n".join(group["bullets"])
                        t = await translate_text(client, bullets_text)
                        if t:
                            new_group["bullets"] = t.split("\n")
                    new_groups.append(new_group)
                new_section["groups"] = new_groups
            translated_sections.append(new_section)
        result["sections"] = translated_sections

    # Translate footer_note
    if profile.get("footer_note"):
        t = await translate_text(client, profile["footer_note"])
        if t:
            result["footer_note"] = t

    return result


async def main():
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    # Ensure columns exist
    with conn.cursor() as cur:
        cur.execute(
            "ALTER TABLE centroids_v3 ADD COLUMN IF NOT EXISTS profile_json_de JSONB"
        )
        cur.execute(
            "ALTER TABLE centroids_v3 ADD COLUMN IF NOT EXISTS description_de TEXT"
        )
    conn.commit()

    # --- Part 1: Translate descriptions ---
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, label, description FROM centroids_v3 "
            "WHERE description IS NOT NULL AND description_de IS NULL "
            "AND is_active = true ORDER BY label"
        )
        desc_rows = cur.fetchall()

    print("Found %d centroids needing description_de" % len(desc_rows))

    async with httpx.AsyncClient(timeout=60) as client:
        for i, (cid, label, desc) in enumerate(desc_rows):
            print("[%d/%d] description_de: %s..." % (i + 1, len(desc_rows), label))
            translated = await translate_text(client, desc)
            if translated:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE centroids_v3 SET description_de = %s WHERE id = %s",
                        (translated, cid),
                    )
                conn.commit()
                print("  OK: %s" % translated[:60])
            else:
                print("  SKIP (translation failed)")

    # --- Part 2: Translate profile_json ---
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, label, profile_json FROM centroids_v3 "
            "WHERE profile_json IS NOT NULL AND profile_json_de IS NULL "
            "AND is_active = true ORDER BY label"
        )
        rows = cur.fetchall()

    print("Found %d centroids needing profile_json_de" % len(rows))

    async with httpx.AsyncClient(timeout=60) as client:
        for i, (cid, label, profile_json) in enumerate(rows):
            print("[%d/%d] profile_json_de: %s..." % (i + 1, len(rows), label))
            profile = (
                profile_json
                if isinstance(profile_json, dict)
                else json.loads(profile_json)
            )
            if not profile or (isinstance(profile, list) and len(profile) == 0):
                print("  SKIP (empty profile)")
                continue
            if isinstance(profile, dict) and not profile.get("sections"):
                print("  SKIP (no sections)")
                continue
            translated = await translate_profile(client, profile)
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE centroids_v3 SET profile_json_de = %s WHERE id = %s",
                    (json.dumps(translated, ensure_ascii=False), cid),
                )
            conn.commit()
            print("  Done: %s" % label)

    conn.close()
    print("All done.")


if __name__ == "__main__":
    asyncio.run(main())
