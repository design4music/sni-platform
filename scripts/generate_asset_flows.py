"""Generate the oil-flows pilot: structural supply relationships between
strategic assets, with geometry precomputed offline.

Sea legs: searoute (follows real shipping lanes, records passages ->
via_asset_ids). Land legs: schematic quadratic arc (a flow is a
relationship, not infrastructure -- arcs are honest here). One flow
reuses the Druzhba pipeline geometry (suspended flow demo).

Writes db/migrations/20260704_seed_oil_flows.sql. Idempotent.
Run: python scripts/generate_asset_flows.py
"""

import json
import os

import psycopg2
import searoute as sr
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "db", "migrations", "20260704_seed_oil_flows.sql")

AS_OF = "2026-07-03"
SRC_EIA = "EIA country analyses; JODI"
SRC_TANKER = "press-reported tanker tracking (Kpler/Vortexa)"

PASSAGE_TO_ASSET = {
    "suez": "suez_canal",
    "malacca": "strait_of_malacca",
    "babalmandab": "bab_el_mandeb",
    "gibraltar": "strait_of_gibraltar",
    "ormuz": "strait_of_hormuz",
    "panama": "panama_canal",
    "bosporus": "turkish_straits",
    "taiwan": "taiwan_strait",
}

# (id, from, to, commodity, mode, magnitude, status, source, confidence, notes)
FLOWS = [
    (
        "flow_saudi_china_crude",
        "ras_tanura",
        "zhenhai_zhoushan_refining",
        "oil",
        "sea",
        "major",
        "active",
        SRC_EIA,
        "high",
        None,
    ),
    (
        "flow_saudi_india_crude",
        "ras_tanura",
        "jamnagar_refinery",
        "oil",
        "sea",
        "major",
        "active",
        SRC_EIA,
        "high",
        None,
    ),
    (
        "flow_saudi_korea_crude",
        "ras_tanura",
        "ulsan_industrial",
        "oil",
        "sea",
        "major",
        "active",
        SRC_EIA,
        "high",
        None,
    ),
    (
        "flow_saudi_japan_crude",
        "ras_tanura",
        "yokohama_tokyo_bay_port",
        "oil",
        "sea",
        "major",
        "active",
        SRC_EIA,
        "high",
        None,
    ),
    (
        "flow_iraq_india_crude",
        "basra_oil_terminal",
        "jamnagar_refinery",
        "oil",
        "sea",
        "major",
        "active",
        SRC_EIA,
        "high",
        None,
    ),
    (
        "flow_iraq_china_crude",
        "basra_oil_terminal",
        "zhenhai_zhoushan_refining",
        "oil",
        "sea",
        "major",
        "active",
        SRC_EIA,
        "high",
        None,
    ),
    (
        "flow_iran_china_crude",
        "kharg_island_terminal",
        "zhenhai_zhoushan_refining",
        "oil",
        "sea",
        "major",
        "active",
        SRC_TANKER,
        "medium",
        "Sanctioned trade; volumes and routing reported via tanker tracking, not official statistics.",
    ),
    (
        "flow_russia_india_crude",
        "primorsk_ust_luga_terminals",
        "jamnagar_refinery",
        "oil",
        "sea",
        "major",
        "active",
        SRC_TANKER,
        "high",
        "Post-2022 price-cap trade, substantially on shadow-fleet tonnage. Volatile: subject to sanctions policy swings.",
    ),
    (
        "flow_russia_china_baltic_crude",
        "primorsk_ust_luga_terminals",
        "zhenhai_zhoushan_refining",
        "oil",
        "sea",
        "secondary",
        "active",
        SRC_TANKER,
        "high",
        None,
    ),
    (
        "flow_russia_china_espo_crude",
        "kozmino_terminal",
        "zhenhai_zhoushan_refining",
        "oil",
        "sea",
        "major",
        "active",
        SRC_EIA,
        "high",
        None,
    ),
    (
        "flow_urals_bosporus_india",
        "novorossiysk_port",
        "jamnagar_refinery",
        "oil",
        "sea",
        "secondary",
        "active",
        SRC_TANKER,
        "high",
        "Black Sea Urals and CPC blend exiting through the Turkish Straits.",
    ),
    (
        "flow_us_europe_crude",
        "corpus_christi_export_hub",
        "port_of_rotterdam",
        "oil",
        "sea",
        "major",
        "active",
        SRC_EIA,
        "high",
        None,
    ),
    (
        "flow_us_india_crude",
        "corpus_christi_export_hub",
        "jamnagar_refinery",
        "oil",
        "sea",
        "secondary",
        "active",
        SRC_EIA,
        "high",
        None,
    ),
    (
        "flow_ceyhan_med_crude",
        "ceyhan_terminal",
        "trieste_port",
        "oil",
        "sea",
        "secondary",
        "active",
        SRC_EIA,
        "high",
        "BTC and Iraqi crude into Mediterranean refining; Trieste feeds the TAL pipeline into Central Europe.",
    ),
    (
        "flow_fujairah_singapore_products",
        "fujairah_hub",
        "port_of_singapore",
        "refined_products",
        "sea",
        "secondary",
        "active",
        SRC_EIA,
        "high",
        None,
    ),
    (
        "flow_india_europe_products",
        "jamnagar_refinery",
        "port_of_rotterdam",
        "refined_products",
        "sea",
        "major",
        "active",
        SRC_TANKER,
        "high",
        "Indian diesel exports to Europe grew sharply after the EU embargo on Russian products.",
    ),
    (
        "flow_singapore_indonesia_products",
        "jurong_island_refining",
        "tanjung_priok_port",
        "refined_products",
        "sea",
        "secondary",
        "active",
        SRC_EIA,
        "high",
        None,
    ),
    (
        "flow_usgulf_brazil_products",
        "us_gulf_coast_refining_corridor",
        "santos_port",
        "refined_products",
        "sea",
        "secondary",
        "active",
        SRC_EIA,
        "high",
        None,
    ),
    (
        "flow_brazil_china_crude",
        "santos_presalt_basin",
        "zhenhai_zhoushan_refining",
        "oil",
        "sea",
        "major",
        "active",
        SRC_EIA,
        "high",
        None,
    ),
    (
        "flow_guyana_europe_crude",
        "stabroek_block",
        "port_of_rotterdam",
        "oil",
        "sea",
        "secondary",
        "active",
        SRC_EIA,
        "high",
        None,
    ),
    (
        "flow_canada_usgulf_crude",
        "athabasca_oil_sands",
        "us_gulf_coast_refining_corridor",
        "oil",
        "land",
        "major",
        "active",
        SRC_EIA,
        "high",
        "Overland pipeline systems (Keystone, Enbridge Mainline); schematic path.",
    ),
    (
        "flow_kazakh_novorossiysk_crude",
        "tengiz_kashagan_fields",
        "novorossiysk_port",
        "oil",
        "land",
        "major",
        "active",
        SRC_EIA,
        "high",
        "CPC pipeline to the Black Sea; schematic path.",
    ),
    (
        "flow_druzhba_europe_crude",
        "west_siberian_basin",
        "rhine_ruhr_industrial",
        "oil",
        "druzhba",
        "major",
        "suspended",
        SRC_EIA,
        "high",
        "Northern Druzhba deliveries to Germany/Poland halted after 2022; southern branch to Hungary/Slovakia continues.",
    ),
]


def esc(s):
    return s.replace("'", "''") if s else s


def rep_point(geom):
    g = geom
    if g["type"] == "Point":
        return g["coordinates"]
    if g["type"] == "Polygon":
        ring = g["coordinates"][0][:-1]
        return [
            sum(p[0] for p in ring) / len(ring),
            sum(p[1] for p in ring) / len(ring),
        ]
    if g["type"] == "LineString":
        c = g["coordinates"]
        return c[len(c) // 2]
    raise ValueError(g["type"])


def land_arc(a, b, steps=32):
    """Schematic quadratic arc for overland flows ([lon,lat] in/out)."""
    dist = ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
    ctrl = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + dist * 0.15]
    pts = []
    for i in range(steps + 1):
        t = i / steps
        s = 1 - t
        pts.append(
            [
                round(s * s * a[0] + 2 * s * t * ctrl[0] + t * t * b[0], 3),
                round(s * s * a[1] + 2 * s * t * ctrl[1] + t * t * b[1], 3),
            ]
        )
    return pts


def main():
    load_dotenv(os.path.join(ROOT, ".env"))
    conn = psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )
    cur = conn.cursor()
    ids = {f[1] for f in FLOWS} | {f[2] for f in FLOWS} | {"druzhba_pipeline_west"}
    cur.execute(
        "SELECT id, geometry FROM strategic_assets WHERE id = ANY(%s)", (list(ids),)
    )
    geo = {r[0]: r[1] for r in cur.fetchall()}
    conn.close()

    missing = ids - set(geo)
    if missing:
        raise SystemExit(f"FAIL missing assets: {sorted(missing)}")

    stmts = []
    for fid, from_a, to_a, commodity, mode, mag, status, source, conf, notes in FLOWS:
        via = []
        if mode == "sea":
            o, d = rep_point(geo[from_a]), rep_point(geo[to_a])
            route = sr.searoute(o, d, return_passages=True)
            coords = [
                [round(c[0], 3), round(c[1], 3)]
                for c in route["geometry"]["coordinates"]
            ]
            passages = route["properties"].get("traversed_passages") or []
            via = sorted(
                {PASSAGE_TO_ASSET[p] for p in passages if p in PASSAGE_TO_ASSET}
            )
        elif mode == "land":
            coords = land_arc(rep_point(geo[from_a]), rep_point(geo[to_a]))
        elif mode == "druzhba":
            coords = geo["druzhba_pipeline_west"]["coordinates"]
            via = ["druzhba_pipeline_west"]
        else:
            raise ValueError(mode)

        geometry = json.dumps({"type": "LineString", "coordinates": coords})
        via_sql = (
            "ARRAY[" + ",".join(f"'{v}'" for v in via) + "]"
            if via
            else "ARRAY[]::text[]"
        )
        notes_sql = f"'{esc(notes)}'" if notes else "NULL"
        stmts.append(
            "INSERT INTO asset_flows (id, commodity, from_asset, to_asset, via_asset_ids, geometry, magnitude_class, status, as_of, source, confidence, notes)\n"
            f"VALUES ('{fid}', '{commodity}', '{from_a}', '{to_a}', {via_sql}, '{geometry}'::jsonb, "
            f"'{mag}', '{status}', '{AS_OF}', '{esc(source)}', '{conf}', {notes_sql})\n"
            "ON CONFLICT (id) DO UPDATE SET geometry = EXCLUDED.geometry, via_asset_ids = EXCLUDED.via_asset_ids;"
        )
        print(f"OK {fid} [{mode}] {len(coords)}pts via {via or '-'}")

    header = (
        "-- Oil flows pilot: structural supply relationships, generated by\n"
        "-- scripts/generate_asset_flows.py. Sea geometry via searoute; land\n"
        "-- flows are schematic arcs. Every row carries as_of/source/confidence.\n\n"
    )
    with open(OUT, "w", encoding="ascii") as fh:
        fh.write(header + "\n\n".join(stmts) + "\n")
    print(f"OK wrote {OUT} ({len(stmts)} flows)")


if __name__ == "__main__":
    main()
