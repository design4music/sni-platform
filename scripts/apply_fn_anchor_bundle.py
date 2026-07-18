"""Apply a curated fn_anchor bundle JSON into taxonomy_v3.

Reads the JSON shape produced by scripts/extract_fn_anchor_via_deepseek.py
(or hand-curated equivalents) and UPSERTs one row in taxonomy_v3 with
taxonomy_function='fn_anchor' and linked_id=<fn_id>.

Idempotent: re-running replaces the bundle's aliases for that FN. Use this
to roll forward changes after curation passes.

Usage:
    python scripts/apply_fn_anchor_bundle.py \\
        --json out/extraction/iran_nuclear_program__curated.json \\
        --mode dry-run        # default; prints summary only
    python scripts/apply_fn_anchor_bundle.py --json <path> --mode apply

The aliases JSONB in taxonomy_v3 is the UNION of every term's per-language
aliases across the bundle, in the same 10-lang shape (ar, de, en, es, fr,
hi, it, ja, ru, zh — empty arrays where no alias). item_raw is the FN id
plus a "fn_anchor" suffix for display.
"""

import argparse
import json
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import Json

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.config import config  # noqa: E402

LANG_KEYS = ["ar", "de", "en", "es", "fr", "hi", "it", "ja", "ru", "zh"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json", required=True, help="Path to curated bundle JSON.")
    p.add_argument(
        "--mode",
        choices=["dry-run", "apply"],
        default="dry-run",
        help="dry-run prints what would change; apply commits.",
    )
    return p.parse_args()


def merge_bundle_to_aliases(bundle: list[dict]) -> dict:
    """Union per-term aliases into one JSONB-shaped dict."""
    merged: dict[str, list[str]] = {k: [] for k in LANG_KEYS}
    seen: dict[str, set[str]] = {k: set() for k in LANG_KEYS}
    for item in bundle:
        for lang in LANG_KEYS:
            for alias in item.get("aliases", {}).get(lang, []) or []:
                if alias and alias not in seen[lang]:
                    merged[lang].append(alias)
                    seen[lang].add(alias)
    return merged


def main() -> None:
    args = parse_args()
    path = Path(args.json)
    if not path.exists():
        raise SystemExit(f"JSON not found: {path}")
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    fn_id = data.get("metadata", {}).get("fn_id")
    if not fn_id:
        raise SystemExit("metadata.fn_id missing in JSON")
    bundle = data.get("bundle", [])
    if not bundle:
        raise SystemExit("bundle empty in JSON")

    aliases = merge_bundle_to_aliases(bundle)
    total_aliases = sum(len(v) for v in aliases.values())

    print(f"FN: {fn_id}")
    print(
        f"Bundle: {len(bundle)} terms, {total_aliases} aliases across {sum(1 for v in aliases.values() if v)} languages"
    )
    for lang, vals in aliases.items():
        if vals:
            print(f"  {lang}: {len(vals):3d} aliases")

    if args.mode == "dry-run":
        print("\nDRY-RUN: no changes committed. Re-run with --mode apply to write.")
        return

    item_raw = f"{fn_id} fn_anchor"
    conn = psycopg2.connect(**config.db_connect_kwargs())
    try:
        with conn.cursor() as cur:
            # Look for existing fn_anchor row for this FN (UNIQUE partial index
            # ensures at most one).
            cur.execute(
                "SELECT id FROM taxonomy_v3 WHERE taxonomy_function='fn_anchor' AND linked_id=%s AND is_active=true",
                (fn_id,),
            )
            existing = cur.fetchone()
            if existing:
                cur.execute(
                    """
                    UPDATE taxonomy_v3
                    SET item_raw = %s,
                        aliases = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (item_raw, Json(aliases), existing[0]),
                )
                print(
                    f"\nUPDATED existing fn_anchor row for {fn_id} (id={existing[0]})"
                )
            else:
                cur.execute(
                    """
                    INSERT INTO taxonomy_v3
                      (item_raw, aliases, taxonomy_function, linked_id, is_active, is_stop_word)
                    VALUES (%s, %s, 'fn_anchor', %s, true, false)
                    RETURNING id
                    """,
                    (item_raw, Json(aliases), fn_id),
                )
                new_id = cur.fetchone()[0]
                print(f"\nINSERTED new fn_anchor row for {fn_id} (id={new_id})")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
