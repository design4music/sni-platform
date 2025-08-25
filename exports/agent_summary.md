Task: Run SQL count on article_clusters, write to exports/db_count.json, and read it back.

What happened:
- Attempted to execute: SELECT COUNT(*)::int AS count FROM article_clusters;
- The db_query command is not available in this environment, and psql is also not installed.
- Wrote fallback result to exports/db_count.json capturing the failure and actionable hints.
- Successfully read exports/db_count.json back to confirm the write.
- Added exports/db_query_howto.md with step-by-step instructions to actually run the query using either psql or a small Python script.

Current artifacts:
- exports/db_count.json
  - ok: false
  - count: null
  - sql: SELECT COUNT(*)::int AS count FROM article_clusters;
  - error: 'db_query' command is not available in this environment; unable to execute the SQL query.
  - hints: suggestions to provide db_query, use psql with $DATABASE_URL, or add a Python script.
  - timestamp: present
- exports/db_query_howto.md
  - Contains: how to set DATABASE_URL (from .env DB_*), exact psql command, and a minimal Python (psycopg) approach to write the real result to exports/db_count.json.

Environment notes:
- .env present with DB connection parts (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD).
- .env.example shows DATABASE_URL pattern; not currently set in .env.

Next steps to get a real count:
1) Provide a db_query tool or install psql and set DATABASE_URL, then run:
   psql "$DATABASE_URL" -Atc "SELECT COUNT(*)::int AS count FROM article_clusters;"
   and update exports/db_count.json with the actual result.
2) Or run the minimal Python script (psycopg) described in exports/db_query_howto.md to execute the query using .env DB_* values and write the JSON result to exports/db_count.json.
