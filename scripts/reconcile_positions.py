"""P1 reconcile: db/registry/narrative_positions.yaml -> positions table +
narratives_v2.position_id. Idempotent -- a second run is a no-op.

  python scripts/reconcile_positions.py            # apply
  python scripts/reconcile_positions.py --dry-run  # report only, no write

Refuses to run unless the registry status is `approved` (DG-0 gate).
"""

import argparse
import os
from pathlib import Path

import psycopg2
import psycopg2.extras
import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "db" / "registry" / "narrative_positions.yaml"


def connect():
    load_dotenv(ROOT / ".env")
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )


def load_registry():
    reg = yaml.safe_load(REG.read_text(encoding="utf-8"))
    if reg.get("status") != "approved":
        raise SystemExit(
            f"registry status is '{reg.get('status')}', not 'approved' -- "
            "DG-0 not signed off. Refusing to write."
        )
    return reg["positions"]


def validate(cur, positions):
    """Referential pre-flight -- every id resolves, coverage is exact. Fail loud."""
    cur.execute("SELECT id FROM narratives_v2 WHERE is_active")
    active = {r[0] for r in cur.fetchall()}
    cur.execute("SELECT id FROM meta_narratives")
    metas = {r[0] for r in cur.fetchall()}
    cur.execute("SELECT id FROM centroids_v3")
    centroids = {r[0] for r in cur.fetchall()}

    cards = [c for p in positions for c in (p.get("cards") or [])]
    errs = []
    dupes = {c for c in cards if cards.count(c) > 1}
    if dupes:
        errs.append(f"cards assigned to >1 position: {sorted(dupes)}")
    if set(cards) - active:
        errs.append(f"cards not active in db: {sorted(set(cards) - active)}")
    if active - set(cards):
        errs.append(f"active cards not covered: {sorted(active - set(cards))}")
    for p in positions:
        if p["meta"] not in metas:
            errs.append(f"{p['id']}: bad meta {p['meta']}")
        for s in p.get("meta_secondary") or []:
            if s not in metas:
                errs.append(f"{p['id']}: bad meta_secondary {s}")
        if not p.get("owner_centroids"):
            errs.append(f"{p['id']}: no owner_centroids")
        for o in p.get("owner_centroids") or []:
            if o not in centroids:
                errs.append(f"{p['id']}: owner centroid not in centroids_v3: {o}")
        for field in ("name_en", "name_de", "claim_en", "claim_de"):
            if not (p.get(field) or "").strip():
                errs.append(f"{p['id']}: empty {field}")
    if errs:
        raise SystemExit("VALIDATION FAILED:\n  " + "\n  ".join(errs))
    print(
        f"validation OK: {len(positions)} positions, {len(cards)} cards, "
        f"{len(active)} active cards covered exactly once"
    )


def reconcile(cur, positions, dry_run):
    # 1. upsert positions
    upsert = """
        INSERT INTO positions
          (id, name_en, name_de, claim_en, claim_de, stance_sign,
           meta_narrative_id, meta_secondary_ids, owner_centroids, is_active, updated_at)
        VALUES (%(id)s, %(name_en)s, %(name_de)s, %(claim_en)s, %(claim_de)s,
                %(stance_sign)s, %(meta)s, %(meta_secondary)s, %(owner_centroids)s,
                true, now())
        ON CONFLICT (id) DO UPDATE SET
          name_en = EXCLUDED.name_en, name_de = EXCLUDED.name_de,
          claim_en = EXCLUDED.claim_en, claim_de = EXCLUDED.claim_de,
          stance_sign = EXCLUDED.stance_sign,
          meta_narrative_id = EXCLUDED.meta_narrative_id,
          meta_secondary_ids = EXCLUDED.meta_secondary_ids,
          owner_centroids = EXCLUDED.owner_centroids,
          is_active = true, updated_at = now()
        WHERE (positions.name_en, positions.name_de, positions.claim_en,
               positions.claim_de, positions.stance_sign, positions.meta_narrative_id,
               positions.meta_secondary_ids, positions.owner_centroids, positions.is_active)
          IS DISTINCT FROM
              (EXCLUDED.name_en, EXCLUDED.name_de, EXCLUDED.claim_en,
               EXCLUDED.claim_de, EXCLUDED.stance_sign, EXCLUDED.meta_narrative_id,
               EXCLUDED.meta_secondary_ids, EXCLUDED.owner_centroids, EXCLUDED.is_active);
    """
    rows = [
        {
            "id": p["id"],
            "name_en": p["name_en"],
            "name_de": p["name_de"],
            "claim_en": p["claim_en"],
            "claim_de": p["claim_de"],
            "stance_sign": p["stance_sign"],
            "meta": p["meta"],
            "meta_secondary": p.get("meta_secondary") or [],
            "owner_centroids": p.get("owner_centroids") or [],
        }
        for p in positions
    ]

    # 2. card -> position map
    card_map = [(c, p["id"]) for p in positions for c in (p.get("cards") or [])]

    if dry_run:
        cur.execute("SELECT count(*) FROM positions")
        have = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM narratives_v2 WHERE position_id IS NOT NULL")
        linked = cur.fetchone()[0]
        print(f"[dry-run] would upsert {len(rows)} positions (currently {have})")
        print(f"[dry-run] would link {len(card_map)} cards (currently {linked} linked)")
        return

    cur.executemany(upsert, rows)
    print(f"upserted {len(rows)} positions")

    # deactivate positions no longer in the registry (soft, never delete)
    ids = tuple(p["id"] for p in positions)
    cur.execute(
        "UPDATE positions SET is_active=false, updated_at=now() "
        "WHERE id NOT IN %s AND is_active",
        (ids,),
    )
    if cur.rowcount:
        print(f"deactivated {cur.rowcount} positions absent from registry")

    # set position_id on every card, then clear any stale links
    psycopg2.extras.execute_values(
        cur,
        "UPDATE narratives_v2 AS n SET position_id = v.pid "
        "FROM (VALUES %s) AS v(cid, pid) WHERE n.id = v.cid "
        "AND n.position_id IS DISTINCT FROM v.pid",
        card_map,
    )
    linked = cur.rowcount
    covered = tuple(c for c, _ in card_map)
    cur.execute(
        "UPDATE narratives_v2 SET position_id = NULL "
        "WHERE position_id IS NOT NULL AND id NOT IN %s",
        (covered,),
    )
    print(f"linked/updated {linked} card->position rows; cleared {cur.rowcount} stale")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    positions = load_registry()
    conn = connect()
    cur = conn.cursor()
    validate(cur, positions)
    reconcile(cur, positions, args.dry_run)
    if args.dry_run:
        conn.rollback()
        print("dry-run: rolled back")
    else:
        conn.commit()
        # post-check
        cur.execute("SELECT count(*) FROM positions WHERE is_active")
        npos = cur.fetchone()[0]
        cur.execute(
            "SELECT count(*) FROM narratives_v2 WHERE is_active AND position_id IS NULL"
        )
        orphan = cur.fetchone()[0]
        print(
            f"committed. active positions: {npos}; active cards without a position: {orphan}"
        )
    conn.close()


if __name__ == "__main__":
    main()
