"""
Whale extraction prototype: event detection via (beat, date, ubiquity-filtered entity).

For a given CTM:
  - Pull all titles with labels (actor, action_class, target, places, persons, orgs)
  - Group into beats = (actor, action_class, target)
  - For each beat, compute daily title counts and identify spike days
    (spike = count >= max(ABS_FLOOR, SPIKE_MULT * beat_median))
  - Compute per-CTM ubiquity stats for entities; drop any entity
    appearing in >UBIQUITY_PCT of CTM titles
  - For each (beat, spike-day), name the event:
      * top non-ubiquitous place/person/org (prefer based on beat's action_class)
      * representative headline = title linked to the biggest events_v3 row
        among those carrying this beat on this day (fallback: any title)
  - Emit CSV: lane, lane_size, lane_days, date, day_count, spike_ratio,
              top_entity, headline, headline_sources

Baseline limitation: within-CTM median only. A rolling 14-day window
would be better; see Q3 discussion in conversation. Works well when
beats are bursty, under-fires on mega-conflict CTMs where every day
is above baseline. Prototype uses a hard absolute floor as a safety net.

Usage:
  python scripts/prototype_whale_extraction.py AMERICAS-USA geo_security 2026-03
"""

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median, quantiles

from sqlalchemy import create_engine, text

from core.config import get_config

# Tunable parameters
ABS_FLOOR_BIG = 8  # absolute minimum titles/day to count as event in big CTMs
ABS_FLOOR_SMALL = 2  # small CTMs (<500 titles): lower floor
P75_MULT = 1.0  # day count must be >= MULT * P75(lane's daily counts)
MIN_SPIKE_RATIO = (
    1.5  # day count must also be >= MIN_SPIKE_RATIO * median (drops flat lanes)
)
UBIQUITY_PCT = 0.12  # entities in >12% of CTM titles are ubiquitous, drop from naming
SECONDARY_ENTITY_RATIO = (
    0.35  # secondary entity must be at least this ratio of top's count
)
BIG_CTM_THRESHOLD = 500  # titles above this = "big CTM" -> larger floors
MAX_EVENTS_PER_LANE = 15  # retain at most this many events per lane
THEATER_MIN_EVENTS = 15  # below this, skip theater grouping and emit a flat list


def lane_min_titles(n_titles: int) -> int:
    """Scale the minimum lane size with CTM mass."""
    if n_titles >= 2000:
        return 15
    if n_titles >= 500:
        return 10
    if n_titles >= 150:
        return 5
    return 3


# Generic entities that should never name an event (too broad).
# Capital cities are deliberately NOT here - they're legitimate strike/event targets.
GENERIC_PLACES = {
    "Middle East",
    "Mideast",
    "Asia",
    "Asia Pacific",
    "Asia-Pacific",
    "Europe",
    "Africa",
    "Americas",
    "Persian",
    "Persian Gulf",
    "Gulf",
    "Red Sea",
    "Mediterranean",
    "Pacific",
    "Atlantic",
    "World",
    "Global",
    "North",
    "South",
    "East",
    "West",
    "White House",
}
# News publishers / broadcast networks that leak into orgs (Phase 2 bug workaround).
GENERIC_ORGS = {
    "CNN",
    "BBC",
    "REUTERS",
    "AP",
    "AFP",
    "NYT",
    "NY TIMES",
    "FOX",
    "FOX NEWS",
    "MSNBC",
    "ABC",
    "NBC",
    "CBS",
    "PBS",
    "BLOOMBERG",
    "WSJ",
    "WALL_STREET_JOURNAL",
    "WALL STREET JOURNAL",
    "GUARDIAN",
    "TELEGRAPH",
    "ECONOMIST",
    "FT",
    "FINANCIAL TIMES",
    "GLOBAL_TIMES",
    "GLOBAL TIMES",
    "CGTN",
    "XINHUA",
    "CHINA_DAILY",
    "CHINA DAILY",
    "PEOPLES_DAILY",
    "TASS",
    "RT",
    "AL JAZEERA",
    "DAWN",
    "DAWN NEWS",
    "PRESS TV",
    "NBS",
    # generic institutions, rarely event-specific
    "UN",
    "EU",
    "NATO",
    # US actor defaults - these name the actor, not the event
    "PENTAGON",
    "CIA",
    "DOD",
    "DHS",
    "DOJ",
}

# Entity-field preference by action_class
#   military/kinetic → place is most discriminating
#   policy/economic → orgs first (brand, company), then persons
#   political/diplomatic → orgs first (institution), then persons
ACTION_CLASS_FIELD_PREF = {
    # v2.0 classes (still in legacy DB data until re-extraction)
    "MILITARY_OPERATION": ["places", "persons", "orgs"],
    "SECURITY_INCIDENT": ["places", "persons", "orgs"],
    "CAPABILITY_TRANSFER": ["orgs", "places", "persons"],
    "POLITICAL_PRESSURE": ["orgs", "places", "persons"],
    "DIPLOMATIC_PRESSURE": ["orgs", "places", "persons"],
    "POLICY_CHANGE": ["orgs", "policies", "places"],
    "ECONOMIC_DISRUPTION": ["orgs", "places", "persons"],
    "ECONOMIC_PRESSURE": ["orgs", "places", "persons"],
    "RESOURCE_ALLOCATION": ["orgs", "places", "persons"],
    "INFRASTRUCTURE_DEVELOPMENT": ["orgs", "places", "persons"],
    "INFORMATION_INFLUENCE": ["orgs", "persons", "places"],
    "LAW_ENFORCEMENT_OPERATION": ["orgs", "places", "persons"],
    "COLLECTIVE_PROTEST": ["places", "orgs", "persons"],
    "SOCIAL_INCIDENT": ["places", "persons", "orgs"],
    # v3.0 classes (new/renamed/merged)
    "PRESSURE": ["orgs", "places", "persons"],
    "STATEMENT": ["persons", "orgs", "places"],
    "ELECTORAL_EVENT": ["places", "persons", "orgs"],
    "COMMERCIAL_TRANSACTION": ["orgs", "places", "persons"],
    "CIVIL_ACTION": ["places", "orgs", "persons"],
    "NATURAL_EVENT": ["places", "persons", "orgs"],
    "MARKET_SHOCK": ["orgs", "places", "persons"],
}
DEFAULT_FIELD_PREF = ["places", "orgs", "persons"]


# --- Theater classification -------------------------------------------------
# For big CTMs, group lanes into a small number of named theaters so the
# frontend can render 3-6 simple timelines instead of 30 raw beats.
# Rules are matched in order; first match wins. Target matching uses
# substring checks so "IL,US" or "IR,IL" both route to the Iran theater.


def _has(target, codes):
    if not target:
        return False
    parts = {p.strip() for p in target.split(",")}
    return any(c in parts for c in codes)


THEATER_RULES = {
    "AMERICAS-USA": [
        (
            "Iran War",
            lambda a, ac, t: _has(t, {"IR", "IL"})
            or a
            in {"IR_ARMED_FORCES", "IR_EXECUTIVE", "IL_ARMED_FORCES", "IL_EXECUTIVE"},
        ),
        (
            "Russia/Ukraine",
            lambda a, ac, t: _has(t, {"RU", "UA"})
            or a
            in {"RU_ARMED_FORCES", "RU_EXECUTIVE", "UA_ARMED_FORCES", "UA_EXECUTIVE"},
        ),
        ("China/Taiwan", lambda a, ac, t: _has(t, {"CN", "TW"}) or a.startswith("CN_")),
        (
            "Korean Peninsula",
            lambda a, ac, t: _has(t, {"KP", "KR"})
            or a.startswith("KP_")
            or a.startswith("KR_"),
        ),
        (
            "Latin America",
            lambda a, ac, t: _has(
                t, {"VE", "CO", "MX", "CU", "NI", "CL", "BR", "PE", "HN", "AR"}
            ),
        ),
        (
            "Greenland/Arctic",
            lambda a, ac, t: _has(t, {"GL", "IS", "NO", "DK", "FI", "SE"}),
        ),
        (
            "Domestic",
            lambda a, ac, t: (not t or t == "NONE")
            and (
                "LAW_ENFORCEMENT" in a
                or "IMMIGRATION" in a
                or a == "US_DOMESTIC"
                or ac == "LAW_ENFORCEMENT_OPERATION"
            ),
        ),
        ("Other", lambda a, ac, t: True),
    ],
    "ASIA-CHINA": [
        ("US-China relations", lambda a, ac, t: _has(t, {"US"}) or a.startswith("US_")),
        ("Taiwan Strait", lambda a, ac, t: _has(t, {"TW"}) or "TAIWAN" in a),
        ("Hong Kong", lambda a, ac, t: _has(t, {"HK"}) or "HK" in a),
        (
            "EU/Europe",
            lambda a, ac, t: _has(t, {"DE", "FR", "EU", "GB", "IT", "NL"})
            or a.startswith("EU_"),
        ),
        ("Corporate/Market", lambda a, ac, t: a == "CORPORATION"),
        ("Domestic", lambda a, ac, t: True),
    ],
    "EUROPE-BALTIC": [
        (
            "Russia pressure",
            lambda a, ac, t: _has(t, {"RU", "EE", "LV", "LT"}) or a.startswith("RU_"),
        ),
        (
            "NATO defense",
            lambda a, ac, t: _has(t, {"US", "DE", "PL", "FI", "SE"}) or "NATO" in a,
        ),
        ("Other", lambda a, ac, t: True),
    ],
}


def classify_theater(centroid_id: str, actor: str, action: str, target: str) -> str:
    rules = THEATER_RULES.get(centroid_id)
    if not rules:
        return "All"
    for name, pred in rules:
        try:
            if pred(actor, action, target or ""):
                return name
        except Exception:
            continue
    return "Other"


def fetch_ctm_data(engine, centroid_id: str, track: str, month: str):
    """Return list of rows: (title_id, pubdate, title_text, actor, action_class, target,
    places, persons, orgs, event_id, event_source_count)"""
    with engine.connect() as conn:
        ctm_row = conn.execute(
            text("SELECT id FROM ctm WHERE centroid_id=:c AND track=:t AND month=:m"),
            {"c": centroid_id, "t": track, "m": f"{month}-01"},
        ).fetchone()
        if not ctm_row:
            raise SystemExit(f"No CTM found for {centroid_id}/{track}/{month}")
        ctm_id = ctm_row[0]

        rows = conn.execute(
            text(
                """
            SELECT ta.title_id,
                   t.pubdate_utc::date AS d,
                   t.title_display,
                   t.detected_language,
                   tl.actor, tl.action_class, tl.target,
                   tl.places, tl.persons, tl.orgs,
                   ev.id AS event_id,
                   ev.source_batch_count AS event_sources
            FROM title_assignments ta
            JOIN title_labels tl ON tl.title_id = ta.title_id
            JOIN titles_v3 t ON t.id = ta.title_id
            LEFT JOIN event_v3_titles evt ON evt.title_id = ta.title_id
            LEFT JOIN events_v3 ev ON ev.id = evt.event_id AND ev.ctm_id = ta.ctm_id
            WHERE ta.ctm_id = :ctm_id
        """
            ),
            {"ctm_id": ctm_id},
        ).fetchall()
        return ctm_id, [dict(r._mapping) for r in rows]


def compute_ubiquity(rows):
    """Return set of (field, value) tuples that appear in >UBIQUITY_PCT of titles."""
    n_titles = len({r["title_id"] for r in rows})
    if n_titles == 0:
        return set()
    counts = defaultdict(set)
    for r in rows:
        tid = r["title_id"]
        for field in ("places", "persons", "orgs"):
            for v in r.get(field) or []:
                counts[(field, v)].add(tid)
    threshold = n_titles * UBIQUITY_PCT
    return {k for k, tids in counts.items() if len(tids) > threshold}


def build_beat_index(rows):
    """Return {beat: {date: [row, ...]}}, where beat = (actor, action_class, target)."""
    idx = defaultdict(lambda: defaultdict(list))
    for r in rows:
        beat = (r["actor"], r["action_class"], r["target"])
        idx[beat][r["d"]].append(r)
    return idx


def pick_field_pref(action_class: str):
    return ACTION_CLASS_FIELD_PREF.get(action_class, DEFAULT_FIELD_PREF)


_GENERIC_ORGS_NORM = {o.upper().replace("_", " ") for o in GENERIC_ORGS}


def is_blocked(field, value):
    if not value:
        return True
    if field == "places" and value in GENERIC_PLACES:
        return True
    if field == "orgs" and value.upper().replace("_", " ") in _GENERIC_ORGS_NORM:
        return True
    return False


def entities_for_day(day_rows, ubiquitous, action_class, abs_floor):
    """Return up to 3 ranked (field, value, count) tuples for this day.
    The top entity must meet abs_floor. Secondary entities additionally
    need at least SECONDARY_ENTITY_RATIO of the top count AND abs_floor
    absolute titles to count as a distinct event."""
    for field in pick_field_pref(action_class):
        if field not in ("places", "persons", "orgs"):
            continue
        c = Counter()
        for r in day_rows:
            for v in r.get(field) or []:
                if (field, v) in ubiquitous:
                    continue
                if is_blocked(field, v):
                    continue
                c[v] += 1
        if not c:
            continue
        ranked = c.most_common(5)
        top_val, top_n = ranked[0]
        if top_n < abs_floor:
            continue  # entity too weak in this field; try next field
        out = [(field, top_val, top_n)]
        for val, n in ranked[1:]:
            if val.lower() == top_val.lower():
                continue
            if n < abs_floor:
                break
            if n >= SECONDARY_ENTITY_RATIO * top_n:
                out.append((field, val, n))
            if len(out) >= 3:
                break
        return out
    return []  # no namable entity at this strictness


def rows_matching_entity(day_rows, field, value):
    """Filter day_rows to those that mention (field, value) — either in the
    labeled field or as a substring in the title text. Fallback to all rows
    if nothing matches (keeps behavior safe)."""
    if not field or not value:
        return day_rows
    val_lower = value.lower()
    matched = []
    for r in day_rows:
        if value in (r.get(field) or []):
            matched.append(r)
            continue
        title = (r.get("title_display") or "").lower()
        if val_lower in title:
            matched.append(r)
    return matched or day_rows


def pick_headline(rows):
    """English title linked to the biggest events_v3 row, preferring event_sources > 0."""

    def sort_key(r):
        lang_rank = (
            0 if (r.get("detected_language") or "").lower().startswith("en") else 1
        )
        has_event = 0 if (r.get("event_sources") or 0) > 0 else 1
        neg_event_src = -(r.get("event_sources") or 0)
        return (has_event, lang_rank, neg_event_src)

    if not rows:
        return "", 0
    best = sorted(rows, key=sort_key)[0]
    return best["title_display"] or "", (best.get("event_sources") or 0)


def detect_events(rows, centroid_id):
    n_titles = len({r["title_id"] for r in rows})
    abs_floor = ABS_FLOOR_BIG if n_titles >= BIG_CTM_THRESHOLD else ABS_FLOOR_SMALL
    min_lane = lane_min_titles(n_titles)
    ubiquitous = compute_ubiquity(rows)
    beats = build_beat_index(rows)

    # Pass 1: detect atomic (lane, single-date, entity) events.
    atomic = []
    lane_meta = []

    for beat, day_map in beats.items():
        actor, action, target = beat
        if actor == "NONE" and action == "SECURITY_INCIDENT":
            continue

        daily_counts = {d: len(rs) for d, rs in day_map.items()}
        lane_total = sum(daily_counts.values())
        if lane_total < min_lane:
            continue

        counts_sorted = sorted(daily_counts.values())
        med = median(counts_sorted)
        p75 = (
            quantiles(counts_sorted, n=4)[2]
            if len(counts_sorted) >= 4
            else counts_sorted[-1]
        )
        threshold = max(abs_floor, P75_MULT * p75)

        lane_meta.append(
            {
                "beat": beat,
                "lane_total": lane_total,
                "lane_days": len(daily_counts),
                "baseline_median": med,
                "baseline_p75": p75,
                "threshold": threshold,
            }
        )

        for d, day_rows in sorted(day_map.items()):
            cnt = len(day_rows)
            if cnt < threshold:
                continue
            spike_ratio = cnt / max(med, 1)
            if spike_ratio < MIN_SPIKE_RATIO:
                continue

            entities = entities_for_day(day_rows, ubiquitous, action, abs_floor)
            if not entities:
                headline, headline_src = pick_headline(day_rows)
                atomic.append(
                    {
                        "beat": beat,
                        "actor": actor,
                        "action": action,
                        "target": target,
                        "date": d,
                        "lane_size": lane_total,
                        "lane_days": len(daily_counts),
                        "baseline": round(med, 1),
                        "p75": round(p75, 1),
                        "day_count": cnt,
                        "spike_ratio": round(spike_ratio, 1),
                        "entity_field": None,
                        "entity_value": None,
                        "entity_count": cnt,
                        "headline": headline,
                        "headline_src": headline_src,
                    }
                )
                continue

            for field, value, ecount in entities:
                sub_rows = rows_matching_entity(day_rows, field, value)
                headline, headline_src = pick_headline(sub_rows)
                atomic.append(
                    {
                        "beat": beat,
                        "actor": actor,
                        "action": action,
                        "target": target,
                        "date": d,
                        "lane_size": lane_total,
                        "lane_days": len(daily_counts),
                        "baseline": round(med, 1),
                        "p75": round(p75, 1),
                        "day_count": cnt,
                        "spike_ratio": round(spike_ratio, 1),
                        "entity_field": field,
                        "entity_value": value,
                        "entity_count": ecount,
                        "headline": headline,
                        "headline_src": headline_src,
                    }
                )

    # Pass 2: cross-beat dedupe — same (actor, action, date, entity) in different targets.
    by_key = defaultdict(list)
    for ev in atomic:
        key = (
            ev["actor"],
            ev["action"],
            ev["date"],
            (ev["entity_value"] or "").lower(),
        )
        by_key[key].append(ev)

    deduped = []
    for key, group in by_key.items():
        if len(group) == 1:
            ev = group[0]
            ev["merged_targets"] = ""
            deduped.append(ev)
            continue
        group.sort(key=lambda e: -e["lane_size"])
        keep = dict(group[0])
        others = sorted(
            {g["target"] for g in group[1:] if g["target"] != keep["target"]}
        )
        keep["merged_targets"] = ",".join(others)
        keep["day_count"] = max(g["day_count"] for g in group)
        keep["entity_count"] = max(g["entity_count"] for g in group)
        deduped.append(keep)

    # Pass 3: merge consecutive days in the same (lane, entity) into event spans.
    by_lane_entity = defaultdict(list)
    for ev in deduped:
        k = (ev["beat"], ev["entity_field"], (ev["entity_value"] or "").lower())
        by_lane_entity[k].append(ev)

    spans = []
    for k, group in by_lane_entity.items():
        group.sort(key=lambda e: e["date"])
        i = 0
        while i < len(group):
            j = i + 1
            while (
                j < len(group) and (group[j]["date"] - group[j - 1]["date"]).days <= 2
            ):
                j += 1
            slice_ = group[i:j]
            start = slice_[0]["date"]
            end = slice_[-1]["date"]
            start_ev = slice_[0]
            theater = classify_theater(
                centroid_id, start_ev["actor"], start_ev["action"], start_ev["target"]
            )
            merged_targets = ",".join(
                sorted(
                    {
                        t
                        for x in slice_
                        for t in (x.get("merged_targets") or "").split(",")
                        if t
                    }
                )
            )
            best = max(slice_, key=lambda x: x.get("headline_src") or 0)
            spans.append(
                {
                    "theater": theater,
                    "lane": f"{start_ev['actor']}>{start_ev['action']}>{start_ev['target']}",
                    "lane_size": start_ev["lane_size"],
                    "lane_days": start_ev["lane_days"],
                    "baseline": start_ev["baseline"],
                    "p75": start_ev["p75"],
                    "date": (
                        start.isoformat()
                        if start == end
                        else f"{start.isoformat()}..{end.isoformat()}"
                    ),
                    "date_sort": start.isoformat(),
                    "day_count": max(x["day_count"] for x in slice_),
                    "entity_count": sum(x["entity_count"] for x in slice_),
                    "spike_ratio": start_ev["spike_ratio"],
                    "top_entity": (
                        f"{start_ev['entity_field']}:{start_ev['entity_value']}"
                        if start_ev["entity_value"]
                        else ""
                    ),
                    "merged_targets": merged_targets,
                    "headline": best["headline"],
                    "headline_src": best["headline_src"],
                }
            )
            i = j

    # Per-lane cap to prevent mega-lanes from dominating
    spans.sort(key=lambda e: (-e["lane_size"], -e["entity_count"]))
    by_lane_cap = defaultdict(int)
    capped = []
    for s in spans:
        if by_lane_cap[s["lane"]] >= MAX_EVENTS_PER_LANE:
            continue
        by_lane_cap[s["lane"]] += 1
        capped.append(s)

    # Final display sort: theater, then lane size, then date
    capped.sort(
        key=lambda e: (e["theater"], -e["lane_size"], e["lane"], e["date_sort"])
    )
    lane_meta.sort(key=lambda m: -m["lane_total"])
    return capped, lane_meta, n_titles, len(ubiquitous)


def safe(s: str) -> str:
    """Strip characters the Windows console can't print."""
    if s is None:
        return ""
    return s.encode("ascii", "replace").decode("ascii")


def main():
    # Best-effort UTF-8 stdout on Windows
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if len(sys.argv) != 4:
        print(
            "Usage: python scripts/prototype_whale_extraction.py <centroid_id> <track> <YYYY-MM>"
        )
        sys.exit(1)
    centroid_id, track, month = sys.argv[1], sys.argv[2], sys.argv[3]

    engine = create_engine(get_config().database_url)
    ctm_id, rows = fetch_ctm_data(engine, centroid_id, track, month)

    events, lanes, n_titles, n_ubiq = detect_events(rows, centroid_id)

    out_dir = Path("out/whale")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"whale_{centroid_id}_{track}_{month}.csv"

    with out_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "theater",
                "lane",
                "lane_size",
                "lane_days",
                "baseline",
                "p75",
                "date",
                "date_sort",
                "day_count",
                "entity_count",
                "spike_ratio",
                "top_entity",
                "merged_targets",
                "headline",
                "headline_src",
            ],
        )
        writer.writeheader()
        writer.writerows(events)

    print(f"=== BEATS EXTRACTION: {centroid_id} / {track} / {month} ===")
    print(f"Titles in CTM: {n_titles}")
    print(f"Ubiquitous entities dropped: {n_ubiq}")
    print(f"Lanes: {len(lanes)}")
    print(f"Events detected: {len(events)}")
    print(f"Output: {out_file}")
    print()
    print("=== TOP LANES ===")
    for lane in lanes[:12]:
        a, ac, tg = lane["beat"]
        print(
            f"  {a:24s} > {ac:28s} > {tg:10s}  "
            f"size={lane['lane_total']:4d}  days={lane['lane_days']:3d}  "
            f"med={lane['baseline_median']:.1f}  p75={lane['baseline_p75']:.1f}  thr={lane['threshold']:.1f}"
        )
    print()

    # Mode A vs Mode B
    if len(events) >= THEATER_MIN_EVENTS:
        print(f"=== EVENTS BY THEATER ({len(events)} events) ===")
        by_theater = defaultdict(list)
        for e in events:
            by_theater[e["theater"]].append(e)
        # Order theaters by total entity mass
        theater_order = sorted(
            by_theater, key=lambda t: -sum(e["entity_count"] for e in by_theater[t])
        )
        for theater in theater_order:
            items = sorted(by_theater[theater], key=lambda e: e["date_sort"])
            total_mass = sum(e["entity_count"] for e in items)
            print(
                f"\n##### {theater.upper()}   ({len(items)} events, {total_mass} title-mass)"
            )
            cur_lane = None
            for e in items:
                if e["lane"] != cur_lane:
                    cur_lane = e["lane"]
                    mt = f" +[{e['merged_targets']}]" if e["merged_targets"] else ""
                    print(f"  --- {cur_lane}{mt}  (lane_size={e['lane_size']})")
                print(
                    f"      {e['date']:<22s} n={e['entity_count']:3d}  x{e['spike_ratio']:<4}  "
                    f"{safe(e['top_entity'])[:26]:26s}  [{e['headline_src']:>4d} src]  {safe(e['headline'])[:90]}"
                )
    else:
        print(f"=== FLAT LIST ({len(events)} events) ===")
        for e in sorted(events, key=lambda e: e["date_sort"]):
            mt = f" +[{e['merged_targets']}]" if e["merged_targets"] else ""
            print(
                f"  {e['date']:<22s} n={e['entity_count']:3d}  x{e['spike_ratio']:<4}  "
                f"{safe(e['lane'])[:44]:44s}{mt}"
            )
            print(
                f"      {safe(e['top_entity'])[:26]:26s}  [{e['headline_src']:>4d} src]  {safe(e['headline'])[:90]}"
            )


if __name__ == "__main__":
    main()
