"""Generate strategic_assets from the registry (db/registry/*.yaml).

The registry is the single source of truth; this reconciles it into the DB.

Two phases, both idempotent:
  upsert  (default): insert new assets, update metadata on existing ones.
                     Geometry on existing rows is PRESERVED unless the
                     registry row supplies new geometry (lon/lat, hull, line).
  retire  (--retire): deactivate DB assets absent from the registry. Assets
                     referenced by asset_flows are never retired. Prints a
                     dry-run report and requires --yes to apply. Run only
                     once the full registry exists.

Run: python scripts/generate_asset_registry.py [--retire] [--yes]
"""

import argparse
import glob
import json
import os
import re

import psycopg2
import yaml
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG_DIR = os.path.join(ROOT, "db", "registry")

REQUIRED = (
    "id",
    "name_en",
    "name_de",
    "category",
    "subcategory",
    "asset_type",
    "commodities",
    "centroid_ids",
    "criticality",
    "ranking_source",
    "rank_note",
    "description_en",
    "description_de",
)


def load_registry():
    rows = {}
    for path in sorted(glob.glob(os.path.join(REG_DIR, "*.yaml"))):
        entries = yaml.safe_load(open(path, encoding="ascii")) or []
        # db/registry/ also hosts non-asset registries (e.g. regulatory
        # source feeds for official_sources) that share the directory but
        # not this schema -- skip files whose rows declare a different
        # source_class instead of failing the whole asset load.
        if entries and "source_class" in entries[0]:
            continue
        for a in entries:
            missing = [k for k in REQUIRED if k not in a or a[k] in (None, "")]
            if missing:
                raise SystemExit(f"FAIL {path} {a.get('id')}: missing {missing}")
            if a["id"] in rows:
                raise SystemExit(f"FAIL duplicate id {a['id']}")
            rows[a["id"]] = a
    return rows


# Aliases for headline matching (fn_asset_evidence layer). Derived from
# name_en unless the registry row supplies an explicit `aliases:` list
# (an empty list disables matching for that asset). Same substring-match
# semantics as fn_anchor bundles: ILIKE '%alias%'.
ALIAS_LEAD = ("port of ", "strait of ")
ALIAS_TAIL = {
    "terminal",
    "terminals",
    "port",
    "complex",
    "cluster",
    "belt",
    "basin",
    "field",
    "fields",
    "refinery",
    "refining",
    "hub",
    "mine",
    "npp",
    "dam",
    "canal",
    "corridor",
    "industrial",
    "zone",
    "grounds",
    "triangle",
    "facility",
    "station",
    "plant",
    "park",
    "lng",
    "fsru",
    "lane",
    "route",
    "system",
    "area",
    "region",
    "platform",
    "project",
    "projects",
    "works",
}


def derive_aliases(name_en, override=None):
    if override is not None:
        return sorted({a for a in override if a})
    base = re.sub(r"\s*\(.*?\)", "", name_en).strip()
    out = {base}
    short = base
    for lead in ALIAS_LEAD:
        if short.lower().startswith(lead):
            short = short[len(lead) :]
            break
    words = short.split()
    while len(words) > 1 and words[-1].lower() in ALIAS_TAIL:
        words.pop()
    short = " ".join(words)
    if len(short) >= 5 and short.lower() != base.lower():
        out.add(short)
    return sorted(out)


def geometry_for(a):
    """Return GeoJSON dict if the row supplies geometry, else None (preserve)."""
    if "lon" in a and "lat" in a:
        return {"type": "Point", "coordinates": [a["lon"], a["lat"]]}
    if a.get("hull"):
        ring = [list(p) for p in a["hull"]]
        if ring[0] != ring[-1]:
            ring.append(ring[0])
        return {"type": "Polygon", "coordinates": [ring]}
    if a.get("line"):
        return {"type": "LineString", "coordinates": [list(p) for p in a["line"]]}
    return None


def connect():
    load_dotenv(os.path.join(ROOT, ".env"))
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )


def upsert(cur, reg):
    existing = {r[0] for r in _fetch(cur, "SELECT id FROM strategic_assets")}
    ins = upd = 0
    for aid, a in reg.items():
        geom = geometry_for(a)
        meta = {"ranking_source": a["ranking_source"], "rank_note": a["rank_note"]}
        meta["aliases"] = derive_aliases(a["name_en"], a.get("aliases"))
        if a.get("as_of"):
            meta["as_of"] = str(a["as_of"])
        if aid in existing:
            # Update metadata; geometry only if the registry supplies new.
            # meta MERGES over the existing jsonb (registry keys win) so
            # non-registry keys like corridors' via_asset_ids survive --
            # a full replace here silently broke route-pressure propagation
            # once (caught 2026-07-07).
            fields = {
                "name_en": a["name_en"],
                "name_de": a["name_de"],
                "asset_type": a["asset_type"],
                "subcategory": a["subcategory"],
                "commodities": a["commodities"],
                "centroid_ids": a["centroid_ids"],
                "criticality": a["criticality"],
                "description_en": a["description_en"],
                "description_de": a["description_de"],
                "is_active": True,
            }
            if geom is not None:
                fields["geometry"] = geom
            sets = [f"{k}=%s::jsonb" if k == "geometry" else f"{k}=%s" for k in fields]
            vals = [json.dumps(v) if k == "geometry" else v for k, v in fields.items()]
            sets.append("meta = COALESCE(meta, '{}'::jsonb) || %s::jsonb")
            vals.append(json.dumps(meta))
            cur.execute(
                f"UPDATE strategic_assets SET {', '.join(sets)}, updated_at=now() WHERE id=%s",
                vals + [aid],
            )
            upd += 1
        else:
            if geom is None:
                raise SystemExit(f"FAIL new asset {aid} has no geometry")
            cur.execute(
                "INSERT INTO strategic_assets (id, name_en, name_de, asset_type, "
                "subcategory, geometry, commodities, centroid_ids, criticality, "
                "meta, description_en, description_de, is_active) VALUES "
                "(%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s::jsonb,%s,%s,true)",
                [
                    aid,
                    a["name_en"],
                    a["name_de"],
                    a["asset_type"],
                    a["subcategory"],
                    json.dumps(geom),
                    a["commodities"],
                    a["centroid_ids"],
                    a["criticality"],
                    json.dumps(meta),
                    a["description_en"],
                    a["description_de"],
                ],
            )
            ins += 1
    print(f"OK upsert: {ins} inserted, {upd} updated")


def retire(cur, reg, apply):
    flow_refs = set()
    for r in _fetch(cur, "SELECT from_asset, to_asset, via_asset_ids FROM asset_flows"):
        flow_refs.add(r[0])
        flow_refs.add(r[1])
        flow_refs.update(r[2] or [])
    db_active = {
        r[0] for r in _fetch(cur, "SELECT id FROM strategic_assets WHERE is_active")
    }
    stale = sorted(db_active - set(reg) - flow_refs)
    protected = sorted((db_active - set(reg)) & flow_refs)
    print(
        f"-- retire report: {len(stale)} to deactivate, "
        f"{len(protected)} kept (flow-referenced)"
    )
    for s in stale:
        print(f"   RETIRE {s}")
    for p in protected:
        print(f"   KEEP   {p} (referenced by asset_flows)")
    if apply and stale:
        cur.execute(
            "UPDATE strategic_assets SET is_active=false, updated_at=now() "
            "WHERE id = ANY(%s)",
            (stale,),
        )
        print(f"OK retired {len(stale)}")
    elif stale:
        print("dry run -- pass --yes to apply")


def _fetch(cur, q):
    cur.execute(q)
    return cur.fetchall()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--retire", action="store_true")
    ap.add_argument("--yes", action="store_true")
    args = ap.parse_args()

    reg = load_registry()
    print(
        f"OK registry: {len(reg)} assets across "
        f"{len(glob.glob(os.path.join(REG_DIR, '*.yaml')))} files"
    )

    conn = connect()
    cur = conn.cursor()
    upsert(cur, reg)
    if args.retire:
        retire(cur, reg, args.yes)
    conn.commit()
    conn.close()
    print("OK done")


if __name__ == "__main__":
    main()
