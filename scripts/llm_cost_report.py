"""Quick LLM cost / volume report from llm_stats.

Usage:
    python scripts/llm_cost_report.py           # local
    python scripts/llm_cost_report.py --render  # Render DB
    python scripts/llm_cost_report.py --days 7  # last 7 days instead of 1
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from core.config import config

RENDER = "postgresql://maxgenrih55:DGiBGNv89pGtRsaj5Ys2fCN4DFMEmCUb@dpg-d5uem563jp1c739ufrsg-a.frankfurt-postgres.render.com/sni_v2"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--render", action="store_true")
    p.add_argument("--days", type=int, default=1)
    args = p.parse_args()

    if args.render:
        conn = psycopg2.connect(RENDER)
        print("DB: Render")
    else:
        conn = psycopg2.connect(
            host=config.db_host,
            port=config.db_port,
            database=config.db_name,
            user=config.db_user,
            password=config.db_password,
        )
        print(f"DB: {config.db_host}/{config.db_name}")
    print(f"Window: last {args.days} day(s)\n")

    cur = conn.cursor()

    cur.execute(
        """
        SELECT phase,
               COUNT(*)                                AS calls,
               COALESCE(SUM(tokens_in), 0)             AS in_tokens,
               COALESCE(SUM(tokens_out), 0)            AS out_tokens,
               COALESCE(AVG(latency_ms), 0)::int       AS avg_ms,
               COUNT(*) FILTER (WHERE status != 'ok')  AS errors
          FROM llm_stats
         WHERE created_at >= NOW() - (%s || ' days')::interval
         GROUP BY phase
         ORDER BY out_tokens DESC
        """,
        (str(args.days),),
    )
    rows = cur.fetchall()

    if not rows:
        print("No llm_stats rows in the window.")
        return

    fmt = "{:<24} {:>8} {:>12} {:>12} {:>10} {:>7}"
    print(fmt.format("phase", "calls", "tokens_in", "tokens_out", "avg_ms", "errors"))
    print("-" * 78)
    tot_c = tot_in = tot_out = 0
    for phase, calls, t_in, t_out, ms, errs in rows:
        print(fmt.format(phase, calls, f"{t_in:,}", f"{t_out:,}", ms, errs))
        tot_c += calls
        tot_in += t_in
        tot_out += t_out
    print("-" * 78)
    print(fmt.format("TOTAL", tot_c, f"{tot_in:,}", f"{tot_out:,}", "", ""))
    print(f"\nGrand total tokens: {tot_in + tot_out:,}")

    conn.close()


if __name__ == "__main__":
    main()
