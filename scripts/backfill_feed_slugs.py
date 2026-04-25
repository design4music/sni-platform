"""Backfill the feeds.slug column with deterministic slugs + collision rule.

Order of insertion is deterministic: feeds sorted by (created_at, name). The
first outlet that produces a given slug claims it; later collisions append
"-<lang>", then a numeric suffix as a final tiebreaker.

Idempotent: only writes to rows where slug IS NULL or where the recomputed
slug differs from the stored one. Safe to re-run.

Usage:
    python scripts/backfill_feed_slugs.py            # local
    python scripts/backfill_feed_slugs.py --dry-run  # print only
"""

import argparse
import re
import sys
import unicodedata
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config

# Manual transliterations applied before the generic NFKD diacritic strip.
# German umlauts get the canonical -e form rather than naive a/o/u.
_UMLAUTS = {
    "ä": "ae",
    "ö": "oe",
    "ü": "ue",
    "Ä": "ae",
    "Ö": "oe",
    "Ü": "ue",
    "ß": "ss",
}


def slugify(name: str) -> str:
    if not name:
        return ""
    s = name
    for k, v in _UMLAUTS.items():
        s = s.replace(k, v)
    # Strip remaining diacritics
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    # Replace non-alphanumeric runs with "-"
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s


def get_conn():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        dbname=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """
        SELECT id, name, language_code, slug
        FROM feeds
        ORDER BY created_at NULLS FIRST, name
        """
    )
    rows = cur.fetchall()
    print("Feeds: %d" % len(rows), flush=True)

    used: set[str] = set()
    plan: list[tuple[str, str, str]] = []  # (id, name, slug)
    collisions: list[tuple[str, str, str]] = []  # name, base, final

    for r in rows:
        base = slugify(r["name"]) or "feed"
        candidate = base
        if candidate in used:
            lang = (r["language_code"] or "x").lower()
            candidate = "%s-%s" % (base, lang)
            collisions.append((r["name"], base, candidate))
            i = 2
            while candidate in used:
                candidate = "%s-%s-%d" % (base, lang, i)
                i += 1
        used.add(candidate)
        plan.append((r["id"], r["name"], candidate))

    if collisions:
        print("Collisions resolved (%d):" % len(collisions))
        for n, b, f in collisions:
            print("  %s: %s -> %s" % (n, b, f))

    print("Sample (10 of %d):" % len(plan))
    for _id, name, slug in plan[:10]:
        print("  %-40s -> %s" % (name[:40], slug))

    if args.dry_run:
        print("Dry-run; nothing written.")
        return

    cur2 = conn.cursor()
    written = 0
    for fid, _name, slug in plan:
        cur2.execute(
            "UPDATE feeds SET slug = %s WHERE id = %s AND (slug IS DISTINCT FROM %s)",
            (slug, fid, slug),
        )
        written += cur2.rowcount
    conn.commit()
    print("Updated %d / %d rows" % (written, len(plan)))
    cur2.close()
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
