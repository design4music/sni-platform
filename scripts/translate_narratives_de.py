"""Translate strategic narrative names + claims to German via DeepSeek, then update DB."""

import json
import os
import time

import psycopg2
import requests

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-1ff922c364774577902bf81477e143f0")
API_URL = "https://api.deepseek.com/v1/chat/completions"
DB_URL = "postgresql://postgres:password@localhost:5432/sni_v2"
BATCH_SIZE = 20  # narratives per LLM call

SYSTEM_PROMPT = """You are a professional translator. Translate the following strategic narrative names and claims from English to German.

Rules:
- Keep geopolitical terminology precise and formal
- Use Umlauts as ae/oe/ue (no special characters) for database safety
- Preserve the analytical/academic tone
- Country names in German (e.g., "Russia" -> "Russland", "China" -> "China", "United States" -> "Vereinigte Staaten")
- Return valid JSON array with same structure: [{"id": "...", "name_de": "...", "claim_de": "..."}]
- Do NOT translate proper nouns (NATO, EU, BRICS, etc.)
- If claim is null, return claim_de as null"""


def translate_batch(batch):
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(batch, ensure_ascii=False)},
        ],
        "temperature": 0.2,
        "max_tokens": 8000,
    }
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    resp = requests.post(API_URL, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    text = resp.json()["choices"][0]["message"]["content"]
    # Strip markdown fences if present
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text[:-3]
    return json.loads(text)


def main():
    with open("out/narratives_to_translate.json", encoding="utf-8") as f:
        narratives = json.load(f)

    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    total_updated = 0

    for i in range(0, len(narratives), BATCH_SIZE):
        batch = narratives[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(narratives) + BATCH_SIZE - 1) // BATCH_SIZE
        print(
            f"Batch {batch_num}/{total_batches} ({len(batch)} narratives)...",
            flush=True,
        )

        try:
            results = translate_batch(batch)
        except Exception as e:
            print(f"  ERROR on batch {batch_num}: {e}", flush=True)
            time.sleep(5)
            # Retry once
            try:
                results = translate_batch(batch)
            except Exception as e2:
                print(f"  SKIP batch {batch_num} after retry: {e2}", flush=True)
                continue

        for item in results:
            cur.execute(
                "UPDATE strategic_narratives SET name_de = %s, claim_de = %s WHERE id = %s",
                (item["name_de"], item.get("claim_de"), item["id"]),
            )
            total_updated += 1

        conn.commit()
        print(f"  Updated {len(results)} rows (total: {total_updated})", flush=True)
        time.sleep(1)  # rate limit courtesy

    # Verify
    cur.execute(
        "SELECT count(*) FROM strategic_narratives WHERE is_active = true AND name_de IS NOT NULL"
    )
    count = cur.fetchone()[0]
    print(
        f"\nDone. {count}/260 active narratives now have German translations.",
        flush=True,
    )
    conn.close()


if __name__ == "__main__":
    main()
