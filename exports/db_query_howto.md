How to run the article_clusters count query locally

Goal
- Execute: SELECT COUNT(*)::int AS count FROM article_clusters;
- Save JSON output to exports/db_count.json

Option A) Using Python (recommended, cross-platform)
Prereqs
- Python 3.9+
- pip install one of:
  - psycopg[binary]  (psycopg 3)   OR
  - psycopg2-binary  (psycopg 2)
- Optional: python-dotenv if you want automatic .env loading

Script (save as scripts/run_count.py or run directly)

#!/usr/bin/env python3
import os, json, sys
from datetime import datetime

SQL = "SELECT COUNT(*)::int AS count FROM article_clusters;"

# Try loading .env if python-dotenv is available
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

db_url = os.getenv("DATABASE_URL")
if not db_url:
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD", "")
    if not name or not user:
        print(json.dumps({
            "ok": False,
            "count": None,
            "sql": SQL,
            "error": "Missing DATABASE_URL or DB_NAME/DB_USER in environment",
        }, indent=2))
        sys.exit(1)
    db_url = f"postgresql://{user}:{password}@{host}:{port}/{name}"

conn = None
err = None
try:
    import psycopg  # psycopg 3
    conn = psycopg.connect(db_url)
    cursor_ctx = conn.cursor
except Exception as e1:
    try:
        import psycopg2  # fallback to psycopg2
        conn = psycopg2.connect(db_url)
        cursor_ctx = conn.cursor
    except Exception as e2:
        err = f"Failed to connect with psycopg/psycopg2: {e1} | {e2}"

if conn is None:
    print(json.dumps({
        "ok": False,
        "count": None,
        "sql": SQL,
        "error": err,
    }, indent=2))
    sys.exit(1)

try:
    with conn:
        with cursor_ctx() as cur:
            cur.execute(SQL)
            row = cur.fetchone()
            count = row[0] if row else None
    print(json.dumps({
        "ok": count is not None,
        "count": count,
        "sql": SQL,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }, indent=2))
except Exception as e:
    print(json.dumps({
        "ok": False,
        "count": None,
        "sql": SQL,
        "error": str(e),
    }, indent=2))
finally:
    try:
        conn.close()
    except Exception:
        pass

Run and persist output
- Create directory if needed: mkdir -p exports
- Run: python scripts/run_count.py > exports/db_count.json
- Verify: type exports/db_count.json  (Windows) or cat exports/db_count.json (macOS/Linux)

Option B) Using psql (if installed)
- Ensure DATABASE_URL is set, then:
  psql "$DATABASE_URL" -Atc "SELECT json_build_object('ok', true, 'count', (SELECT COUNT(*)::int FROM article_clusters), 'sql', 'SELECT COUNT(*)::int AS count FROM article_clusters;')" > exports/db_count.json

Notes
- .env currently contains discrete DB_* variables; either set DATABASE_URL or ensure DB_NAME and DB_USER (and others) are correct.
- If your DB requires SSL or special params, include them in DATABASE_URL.
