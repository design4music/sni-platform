"""Translate epic centroid_summaries to German via DeepSeek API."""

import json
import os
import sys
import time

import psycopg2
import requests

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "sni_v2")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"


def translate_json_obj(obj: dict) -> dict:
    """Translate all values in a {key: text} dict to German."""
    prompt = (
        "Translate the values of this JSON object to German. "
        "Keep the keys exactly as-is. Return ONLY valid JSON, nothing else.\n\n"
        + json.dumps(obj, ensure_ascii=False)
    )
    resp = requests.post(
        DEEPSEEK_URL,
        headers={
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 4000,
        },
        timeout=120,
    )
    resp.raise_for_status()
    raw = resp.json()["choices"][0]["message"]["content"].strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3].strip()
    return json.loads(raw)


def main():
    if not DEEPSEEK_API_KEY:
        print("ERROR: DEEPSEEK_API_KEY not set")
        sys.exit(1)

    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )
    cur = conn.cursor()
    cur.execute(
        "SELECT id, slug, centroid_summaries "
        "FROM epics WHERE centroid_summaries IS NOT NULL "
        "AND centroid_summaries_de IS NULL ORDER BY slug"
    )
    rows = cur.fetchall()
    print(f"Found {len(rows)} epics to translate")

    for epic_id, slug, summaries in rows:
        obj = summaries if isinstance(summaries, dict) else json.loads(summaries)
        print(f"  {slug}: {len(obj)} summaries ... ", end="", flush=True)
        try:
            translated = translate_json_obj(obj)
            cur.execute(
                "UPDATE epics SET centroid_summaries_de = %s WHERE id = %s",
                [json.dumps(translated, ensure_ascii=False), epic_id],
            )
            conn.commit()
            print("OK")
        except Exception as e:
            conn.rollback()
            print(f"FAIL: {e}")
        time.sleep(0.5)  # rate limit courtesy

    cur.close()
    conn.close()
    print("Done")


if __name__ == "__main__":
    main()
