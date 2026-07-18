"""Surgical, reversible prune of the 5 Ukraine atomic fn_anchor bundles.

Removes leak-class aliases (delivery systems, corporate/market terms,
cross-theater institutions, generic civil-domain nouns, dangerous short
substrings, bare weapon systems) identified by the per-alias audit in
scripts/audit_fn_anchor_aliases.py. Keeps high-precision phenomenon nouns:
toponyms, own-side org acronyms, fixed target nouns, named in-theater sites.

Data-only change (taxonomy_v3.aliases). Fully reversible:
  --mode dry-run   default; prints per-language before/after + drops-not-found
  --mode apply     writes new aliases, after backing up originals
  --mode restore   restores every bundle from its backup JSON

Backups: out/fn_tuning/backup_<fn_id>.json (written on first apply, kept).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import Json, RealDictCursor

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config

BACKUP_DIR = Path(__file__).parent.parent / "out" / "fn_tuning"

# Exact alias strings to DROP per FN, across every language. Anything not
# listed is kept. Derived from out/fn_tuning/audit_*.md.
DROPS: dict[str, set[str]] = {
    # -------------------------------------------------------------------
    "ukraine_battlefield": {
        # weapon systems (equipment, not operations; overlap with aid/theater)
        "HIMARS",
        "ATACMS",
        "Storm Shadow",
        "SCALP",
        "Taurus",
        "Patriot",
        "F-16",
        "Bayraktar",
        "IRIS-T",
        "NASAMS",
        "Caesar",
        "Leopard",
        "Abrams",
        "Bradley",
        "Iskander",
        "Lancet",
        "FAB",
        "KAB",
        "FPV",
        "EW",
        # cross-theater proper nouns / collisions
        "Wagner",
        "Black Sea Fleet",
        "North Korean troops",
        "breakthrough",
        # ru
        "Хаймарс",
        "АТАКМС",
        "Шторм Шэдоу",
        "Таурус",
        "Пэтриот",
        "Байрактар",
        "Искандер",
        "Ланцет",
        "ФАБ",
        "КАБ",
        "Вагнер",
        "Черноморский флот",
        "войска КНДР",
        "прорыв",
        # de
        "Kampfdrohne",
        "nordkoreanische Truppen",
        "Durchbruch",
        # ar
        "هايمارس",
        "اتاكمز",
        "ستورم شادو",
        "توروس",
        "باتريوت",
        "بيرقدار",
        "اسكندر",
        "اختراق",
        # ja
        "ハイマース",
        "ストームシャドウ",
        "タウルス",
        "パトリオット",
        "バイラクタル",
        "イスカンデル",
        "黒海艦隊",
        # zh
        "海玛斯",
        "陆军战术导弹",
        "风暴之影",
        "金牛座",
        "爱国者",
        "拜拉克塔尔",
        "伊斯坎德尔",
        "柳叶刀",
        "黑海舰队",
        "朝鲜军队",
        # es (Crimea bridge belongs to infrastructure)
        "puente de Crimea",
    },
    # -------------------------------------------------------------------
    "ukraine_infrastructure_war": {
        # delivery systems / munitions
        "Shahed",
        "Geran",
        "Kalibr",
        "Kinzhal",
        "Engels",
        "Flamingo",
        "suicide drone",
        "loitering munition",
        "interceptor drone",
        # air-defense / drone battlefield vocab
        "UAV",
        "air defen",
        "airbase",
        "air base",
        "sabotage",
        # generic civil nuclear (keep only named Ukraine sites)
        "reactor",
        "power unit",
        "spent fuel",
        "nuclear safety",
        "IAEA",
        "Grossi",
        # Russian energy corporates
        "Rosatom",
        "Rosneft",
        "Transneft",
        "Gazprom",
        "Lukoil",
        # energy market / prices
        "gasoline",
        "petrol",
        "fuel shortage",
        "fuel crisis",
        "fuel export",
        "diesel",
        "energy crisis",
        "gas station",
        "fuel rationing",
        # pipeline politics (named)
        "Caspian Pipeline",
        "Druzhba",
        # ru
        "МАГАТЭ",
        "Гросси",
        "АЭС",
        "энергоблок",
        "Транснефть",
        "Росатом",
        "Лукойл",
        "Газпром",
        "Роснефть",
        "бензин",
        "дефицит топлива",
        "топливный кризис",
        "дизель",
        "энергетический кризис",
        "АЗС",
        "нормирование топлива",
        "Шахед",
        "Герань",
        "Калибр",
        "Кинжал",
        "Энгельс",
        "Фламинго",
        "авиабаза",
        "аэродром",
        "БПЛА",
        "ПВО",
        "диверси",
        # de
        "Atomkraftwerk",
        "Kernkraftwerk",
        "AKW",
        "Benzin",
        "Kraftstoffmangel",
        "Kraftstoffkrise",
        "Diesel",
        "Energiekrise",
        "Tankstelle",
        "Kraftstoffrationierung",
        "Kamikaze-Drohne",
        "Militärflugplatz",
        # es
        "central nuclear",
        "planta nuclear",
        "gasolina",
        "escasez de combustible",
        "crisis de combustible",
        "diésel",
        "crisis energética",
        "gasolinera",
        "racionamiento de combustible",
        # fr
        "centrale nucléaire",
        "sûreté nucléaire",
        "essence",
        "pénurie de carburant",
        "crise du carburant",
        "gazole",
        "crise énergétique",
        "station-service",
        "rationnement de carburant",
        # it
        "centrale nucleare",
        "benzina",
        "carenza di carburante",
        "crisi del carburante",
        "gasolio",
        "crisi energetica",
        "stazione di servizio",
        "razionamento del carburante",
        # ja
        "原発",
        "グロッシ",
        "ガソリン",
        "燃料不足",
        "エネルギー危機",
        "ディーゼル",
        "ガソリンスタンド",
        "シャヘド",
        "カリブル",
        "キンジャール",
        "空軍基地",
        "無人機",
        # zh
        "国际原子能机构",
        "核电站",
        "汽油",
        "燃料短缺",
        "燃料危机",
        "柴油",
        "能源危机",
        "加油站",
        "燃料配给",
        "沙赫德",
        "口径",
        "匕首",
        "空军基地",
        "无人机",
        # ar
        "الوكالة الدولية للطاقة الذرية",
        "محطة نووية",
        "غروسي",
        "بنزين",
        "نقص الوقود",
        "أزمة الطاقة",
        "ديزل",
        "محطة وقود",
        "كاليبر",
        "كينجال",
        "قاعدة جوية",
        # hi
        "परमाणु संयंत्र",
        "पेट्रोल",
        "ईंधन की कमी",
        "ऊर्जा संकट",
        "डीजल",
    },
    # -------------------------------------------------------------------
    "ukraine_peace_negotiations": {
        # catastrophic 3-char substring (matches Vergeltung, geprügelt, ...)
        "gel",
        # generic English collisions (Fed framework, legal settlement,
        # visa/asset freeze, Epstein accountability, Israeli settlements)
        "framework",
        "settlement",
        "freeze",
        "accountability",
        "autonomy",
        "territorial integrity",
        # promiscuous Gulf/Iran diplomacy venues
        "Doha",
        "Riyadh",
        "Vienna",
    },
    # -------------------------------------------------------------------
    "ukraine_official_corruption": {
        # generic governance vocab (fires on unrelated political reporting)
        "reform progress",
        "reform track",
        "transparency",
        "EU conditionality",
        "IMF conditionality",
        # acronym collisions (State Bank of India, etc.)
        "SBI",
        "DBR",
        # de
        "Transparenz",
        "Reformfortschritt",
        "EU-Konditionalität",
        "IWF-Konditionalität",
        # es / fr / it
        "transparencia",
        "transparence",
        "trasparenza",
        "condicionalidad de la UE",
        "condicionalidad del FMI",
        "conditionnalité de l'UE",
        "conditionnalité du FMI",
        "condizionalità UE",
        "condizionalità FMI",
        "progreso de reforma",
        "progrès de réforme",
        "progresso di riforma",
    },
    # -------------------------------------------------------------------
    "western_aid_to_ukraine": {
        # bare weapon systems (double with battlefield destruction context)
        "fighter jets",
        "F-16",
        "Patriot",
        "long-range missiles",
        "air defense system",
        "air defence system",
        # generic finance collisions (Epstein/UFO tranche, corporate JV)
        "frozen assets",
        "immobilised assets",
        "joint venture",
        "arms deal",
        "tranche",
        "windfall profits",
        "pledge",
        "military aid",
        # defense-contractor corporate names (general corporate news)
        "Lockheed",
        "Raytheon",
        "BAE",
        "Saab",
        "Bundeswehr",
        # over-broad container terms whose samples are Gaza/Iran
        "emergency aid",
        "EU Council",
        # non-en variants
        "Joint Venture",
        "Kampfjets",
        "истребители",
        "cazas",
        "caccia",
        "avions de chasse",
        "باتريوت",
        "Sondervermögen",
        "транш",
        "Militärhilfe",
        "Бундесвер",
    },
}

# Optional ADD-backs: high-precision anchors the corpus missed.
ADDS: dict[str, dict[str, list[str]]] = {
    "ukraine_infrastructure_war": {
        "en": ["Chernobyl"],
        "ru": ["Чернобыль"],
    },
}


def fetch_bundle(cur, fn_id: str) -> dict | None:
    cur.execute(
        """SELECT id, aliases FROM taxonomy_v3
           WHERE taxonomy_function='fn_anchor' AND linked_id=%s AND is_active=true""",
        (fn_id,),
    )
    return cur.fetchone()


def prune_aliases(aliases: dict, drop: set[str], add: dict[str, list[str]]):
    """Return (new_aliases, removed_list, not_found). Removes exact matches
    from every language list; appends ADDs (deduped)."""
    new: dict[str, list[str]] = {}
    removed: list[str] = []
    remaining_drop = set(drop)
    for lang, arr in (aliases or {}).items():
        kept = []
        for a in arr or []:
            if a in drop:
                removed.append(a)
                remaining_drop.discard(a)
            else:
                kept.append(a)
        for extra in (add or {}).get(lang, []):
            if extra not in kept:
                kept.append(extra)
        new[lang] = kept
    return new, removed, sorted(remaining_drop)


def do_restore(cur, conn):
    for fn_id in DROPS:
        bpath = BACKUP_DIR / f"backup_{fn_id}.json"
        if not bpath.exists():
            print(f"  [skip] no backup for {fn_id}")
            continue
        aliases = json.loads(bpath.read_text(encoding="utf-8"))
        cur.execute(
            "UPDATE taxonomy_v3 SET aliases=%s, updated_at=NOW() "
            "WHERE taxonomy_function='fn_anchor' AND linked_id=%s AND is_active=true",
            (Json(aliases), fn_id),
        )
        print(f"  [restored] {fn_id} <- {bpath.name}")
    conn.commit()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--mode", choices=["dry-run", "apply", "restore"], default="dry-run"
    )
    args = ap.parse_args()

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    conn = psycopg2.connect(**config.db_connect_kwargs(), cursor_factory=RealDictCursor)
    try:
        with conn.cursor() as cur:
            if args.mode == "restore":
                do_restore(cur, conn)
                return

            for fn_id, drop in DROPS.items():
                row = fetch_bundle(cur, fn_id)
                if not row:
                    print(f"!! {fn_id}: no fn_anchor bundle found")
                    continue
                aliases = row["aliases"]
                new, removed, not_found = prune_aliases(
                    aliases, drop, ADDS.get(fn_id, {})
                )
                before = sum(len(v or []) for v in aliases.values())
                after = sum(len(v) for v in new.values())
                print(
                    f"\n=== {fn_id}: {before} -> {after} aliases "
                    f"({len(removed)} dropped)"
                )
                for lang in sorted(aliases):
                    b = len(aliases.get(lang) or [])
                    a = len(new.get(lang) or [])
                    if b != a:
                        print(f"    {lang}: {b} -> {a}")
                if not_found:
                    print(f"    [drop strings NOT found - check spelling]: {not_found}")

                if args.mode == "apply":
                    bpath = BACKUP_DIR / f"backup_{fn_id}.json"
                    if not bpath.exists():
                        bpath.write_text(
                            json.dumps(aliases, ensure_ascii=False, indent=2),
                            encoding="utf-8",
                        )
                        print(f"    [backup] {bpath.name}")
                    cur.execute(
                        "UPDATE taxonomy_v3 SET aliases=%s, updated_at=NOW() "
                        "WHERE id=%s",
                        (Json(new), row["id"]),
                    )
                    print("    [applied]")
            if args.mode == "apply":
                conn.commit()
                print("\nCommitted.")
            else:
                print("\nDRY-RUN: nothing written. Re-run with --mode apply.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
