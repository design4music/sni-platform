"""Generate major trade corridors as strategic_assets rows via searoute.

Routes are computed on the Eurostat marnet shipping-lane network (Oak Ridge
GSLN + AIS) so they follow real lanes and never cross land. Each corridor
records the maritime passages it traverses, mapped to our chokepoint asset
ids (meta.via_asset_ids) -- the seed of route-level risk propagation.

Writes db/migrations/20260703_seed_trade_corridors.sql. Idempotent output
(ON CONFLICT DO NOTHING). Run: python scripts/generate_trade_corridors.py
"""

import json
import os

import psycopg2
import searoute as sr
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "db", "migrations", "20260703_seed_trade_corridors.sql")

SIMPLIFY_TOLERANCE_DEG = 0.25
MAX_POINTS = 80

# searoute passage name -> our chokepoint asset id
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

# (id, origin_asset, dest_asset, name_en, name_de, commodities, desc_en, desc_de)
LANES = [
    (
        "lane_asia_europe",
        "port_of_shanghai",
        "port_of_rotterdam",
        "Asia-Europe container lane",
        "Containerroute Asien-Europa",
        ["containers"],
        "The world's busiest long-haul container corridor, linking Chinese export hubs to Northern Europe.",
        "Der verkehrsreichste Langstrecken-Containerkorridor der Welt zwischen chinesischen Exporthaefen und Nordeuropa.",
    ),
    (
        "lane_transpacific",
        "port_of_shanghai",
        "port_of_la_long_beach",
        "Transpacific container lane",
        "Transpazifische Containerroute",
        ["containers"],
        "Primary corridor for Asian exports to the US West Coast.",
        "Hauptkorridor fuer asiatische Exporte an die US-Westkueste.",
    ),
    (
        "lane_asia_gulf",
        "port_of_singapore",
        "jebel_ali_port",
        "Asia-Gulf lane",
        "Route Asien-Golf",
        ["containers"],
        "Container and transshipment corridor between Southeast Asia and the Gulf.",
        "Container- und Umschlagkorridor zwischen Suedostasien und dem Golf.",
    ),
    (
        "lane_gulf_asia_oil",
        "ras_tanura",
        "port_of_shanghai",
        "Gulf-Asia crude lane",
        "Rohoelroute Golf-Asien",
        ["oil"],
        "The main artery of seaborne crude: Gulf exports to East Asian refineries.",
        "Die Hauptader des seewaertigen Rohoelhandels: Golfexporte zu ostasiatischen Raffinerien.",
    ),
    (
        "lane_gulf_japan_lng",
        "ras_laffan_lng",
        "yokohama_tokyo_bay_port",
        "Gulf-Japan LNG lane",
        "LNG-Route Golf-Japan",
        ["lng"],
        "Qatari LNG lifeline to Japan and Northeast Asia.",
        "Katarische LNG-Lebensader nach Japan und Nordostasien.",
    ),
    (
        "lane_pilbara_china_iron",
        "port_hedland",
        "qingdao_port",
        "Pilbara-China iron ore lane",
        "Eisenerzroute Pilbara-China",
        ["iron_ore"],
        "Australian iron ore to Chinese steel mills; the highest-volume dry bulk trade on earth.",
        "Australisches Eisenerz zu chinesischen Stahlwerken; der volumenstaerkste Massengutverkehr der Welt.",
    ),
    (
        "lane_australia_korea_coal",
        "newcastle_au_port",
        "busan_port",
        "Australia-Northeast Asia coal lane",
        "Kohleroute Australien-Nordostasien",
        ["coal"],
        "Australian coal exports to Northeast Asian power and steel producers.",
        "Australische Kohleexporte an Strom- und Stahlerzeuger in Nordostasien.",
    ),
    (
        "lane_brazil_china_iron",
        "tubarao_vitoria_port",
        "qingdao_port",
        "Brazil-China iron ore lane",
        "Eisenerzroute Brasilien-China",
        ["iron_ore"],
        "Brazilian iron ore to China around the Cape of Good Hope.",
        "Brasilianisches Eisenerz nach China um das Kap der Guten Hoffnung.",
    ),
    (
        "lane_southamerica_europe",
        "santos_port",
        "port_of_rotterdam",
        "South America-Europe lane",
        "Route Suedamerika-Europa",
        ["containers", "soy"],
        "Containers and agricultural bulk from Brazil to Northern Europe.",
        "Container und Agrargueter aus Brasilien nach Nordeuropa.",
    ),
    (
        "lane_laplata_grain",
        "rosario_grain_hub",
        "port_said_east",
        "La Plata grain lane",
        "Getreideroute La Plata",
        ["grain", "soy"],
        "Argentine grain and soy to Mediterranean and MENA buyers.",
        "Argentinisches Getreide und Soja an Abnehmer im Mittelmeerraum und MENA.",
    ),
    (
        "lane_blacksea_grain",
        "odesa_port",
        "port_said_east",
        "Black Sea grain lane",
        "Schwarzmeer-Getreideroute",
        ["grain"],
        "Ukrainian grain export route through the Bosphorus to MENA markets.",
        "Ukrainische Getreideexportroute durch den Bosporus zu MENA-Maerkten.",
    ),
    (
        "lane_us_europe_energy",
        "houston_port",
        "port_of_rotterdam",
        "US Gulf-Europe energy lane",
        "Energieroute US-Golf-Europa",
        ["oil", "refined_products"],
        "US Gulf crude and products to European refining centers.",
        "Rohoel und Produkte vom US-Golf zu europaeischen Raffineriezentren.",
    ),
    (
        "lane_us_europe_lng",
        "sabine_pass_lng",
        "port_of_rotterdam",
        "US-Europe LNG lane",
        "LNG-Route USA-Europa",
        ["lng"],
        "US LNG to Europe; the corridor that replaced Russian pipeline gas after 2022.",
        "US-LNG nach Europa; der Korridor, der russisches Pipelinegas nach 2022 ersetzte.",
    ),
    (
        "lane_transatlantic",
        "new_york_nj_port",
        "port_of_rotterdam",
        "Transatlantic container lane",
        "Transatlantische Containerroute",
        ["containers"],
        "Container corridor between the US East Coast and Northern Europe.",
        "Containerkorridor zwischen der US-Ostkueste und Nordeuropa.",
    ),
]


def esc(s: str) -> str:
    """SQL string-literal escaping for generated migration text."""
    return s.replace("'", "''")


def simplify(coords, tolerance):
    try:
        from shapely.geometry import LineString

        line = LineString(coords).simplify(tolerance, preserve_topology=False)
        return [list(c) for c in line.coords]
    except ImportError:
        step = max(1, len(coords) // MAX_POINTS)
        out = coords[::step]
        if out[-1] != coords[-1]:
            out.append(coords[-1])
        return out


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
    all_ids = {lane[1] for lane in LANES} | {lane[2] for lane in LANES}
    cur.execute(
        "SELECT id, geometry->'coordinates' FROM strategic_assets WHERE id = ANY(%s) AND geometry->>'type' = 'Point'",
        (list(all_ids),),
    )
    port_pos = {r[0]: r[1] for r in cur.fetchall()}
    conn.close()

    missing = all_ids - set(port_pos)
    if missing:
        raise SystemExit(f"FAIL missing Point assets: {sorted(missing)}")

    stmts = []
    for lane_id, o_id, d_id, name_en, name_de, commodities, desc_en, desc_de in LANES:
        route = sr.searoute(port_pos[o_id], port_pos[d_id], return_passages=True)
        coords = [
            [round(c[0], 3), round(c[1], 3)] for c in route["geometry"]["coordinates"]
        ]
        coords = simplify(coords, SIMPLIFY_TOLERANCE_DEG)
        if len(coords) > MAX_POINTS:
            coords = simplify(coords, SIMPLIFY_TOLERANCE_DEG * 2)
        passages = route["properties"].get("traversed_passages") or []
        via = sorted({PASSAGE_TO_ASSET[p] for p in passages if p in PASSAGE_TO_ASSET})
        geometry = json.dumps({"type": "LineString", "coordinates": coords})
        meta = json.dumps(
            {
                "generator": "searoute (Eurostat marnet)",
                "endpoints": [o_id, d_id],
                "passages_raw": passages,
                "via_asset_ids": via,
                "length_km": round(route["properties"]["length"]),
            }
        )
        commodities_sql = "ARRAY[" + ",".join(f"'{c}'" for c in commodities) + "]"
        stmts.append(
            "INSERT INTO strategic_assets (id, name_en, name_de, asset_type, geometry, commodities, centroid_ids, criticality, meta, description_en, description_de)\n"
            f"VALUES ('{lane_id}', '{esc(name_en)}', '{esc(name_de)}', 'corridor', '{geometry}'::jsonb, {commodities_sql}, "
            f"ARRAY[]::text[], 3, '{meta}'::jsonb, '{esc(desc_en)}', '{esc(desc_de)}')\n"
            "ON CONFLICT (id) DO UPDATE SET geometry = EXCLUDED.geometry, meta = EXCLUDED.meta, is_active = true;"
        )
        print(f"OK {lane_id}: {len(coords)} pts, via {via or 'open water'}")

    header = (
        "-- Major seaborne trade corridors, generated by scripts/generate_trade_corridors.py\n"
        "-- via searoute (Eurostat marnet network: Oak Ridge GSLN + AIS). Routes follow\n"
        "-- real shipping lanes and never cross land. meta.via_asset_ids records the\n"
        "-- chokepoints each lane transits (route-level risk propagation).\n\n"
    )
    with open(OUT, "w", encoding="ascii") as fh:
        fh.write(header + "\n\n".join(stmts) + "\n")
    print(f"OK wrote {OUT} ({len(stmts)} corridors)")


if __name__ == "__main__":
    main()
