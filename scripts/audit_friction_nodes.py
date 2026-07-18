"""Friction-node data-quality audit. Read-only.

Emits a per-region markdown review sheet covering:
  1. Inventory      -- theaters + members: anchor presence, event/title counts,
                       narrative counts, missing DE/editorial fields
  2. Structure      -- duplicate members across theaters, dangling member ids,
                       orphan atomics, inactive members, region fragility
  3. Duplicates     -- FN pairs with high name-token or centroid overlap
  4. Centroid audit -- declared centroid_ids vs observed centroid distribution
                       of attributed events' titles (only FNs with events)
  5. Assets         -- theater asset links + region assets linked to no FN
  6. Anchor lint    -- fn_anchor aliases that over-match: substring hits on a
                       random recent-title sample (ILIKE '%alias%' semantics)

Usage:
  python scripts/audit_friction_nodes.py --region EUROPE
  python scripts/audit_friction_nodes.py --all

Output: out/fn_audit_<REGION>.md
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config

REGIONS = ["EUROPE", "MIDEAST", "AFRICA", "ASIA", "AMERICAS", "OCEANIA", "NON-STATE"]

# Centroid-evidence thresholds: flag declared centroids carrying <1% of
# attributed titles, and undeclared centroids carrying >=10%.
DECLARED_DEAD_PCT = 1.0
UNDECLARED_HOT_PCT = 10.0

# Anchor lint: sample size of random recent titles, and the hit-rate above
# which an alias is considered too generic (a topic alias should be rare).
LINT_SAMPLE = 10000
LINT_WINDOW_DAYS = 30
LINT_HIT_PCT = 0.5
LINT_MIN_ALIAS_LEN = 4

NAME_STOPWORDS = {
    "and",
    "the",
    "of",
    "in",
    "on",
    "for",
    "to",
    "a",
    "an",
    "vs",
    "strategic",
    "competition",
    "conflict",
    "confrontation",
    "tensions",
    "crisis",
    "dispute",
    "disputes",
    "war",
    "theater",
    "zone",
    "regional",
}


def extract_region(centroid_ids: list[str] | None) -> str:
    # Mirrors apps/frontend/lib/friction-nodes.ts extractRegion(): prefix of
    # the FIRST centroid decides the region.
    if not centroid_ids:
        return "OTHER"
    prefix = centroid_ids[0].split("-")[0]
    return prefix if prefix in REGIONS else "NON-STATE"


def name_tokens(name: str) -> set[str]:
    return {
        t for t in name.lower().replace("-", " ").split() if t not in NAME_STOPWORDS
    }


def load(conn) -> dict:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, name_en, fn_type, is_active, centroid_ids,
               member_fn_ids, affected_asset_ids,
               (name_de IS NULL OR description_de IS NULL) AS missing_de,
               (editorial_summary_en IS NULL) AS missing_editorial
        FROM friction_nodes
    """
    )
    fns = {r["id"]: r for r in cur.fetchall()}

    cur.execute(
        """
        SELECT linked_id FROM taxonomy_v3
        WHERE taxonomy_function='fn_anchor' AND is_active
    """
    )
    anchored = {r["linked_id"] for r in cur.fetchall()}

    cur.execute(
        "SELECT fn_id, COUNT(*) n, MAX(e.last_active) last FROM event_friction_nodes efn JOIN events_v3 e ON e.id=efn.event_id GROUP BY fn_id"
    )
    events = {r["fn_id"]: (int(r["n"]), r["last"]) for r in cur.fetchall()}

    cur.execute(
        """
        SELECT n.fn_id, COUNT(DISTINCT n.id) n_narr, COUNT(tn.title_id) n_titles
        FROM narratives_v2 n
        LEFT JOIN title_narratives tn ON tn.narrative_id = n.id
        WHERE n.is_active
        GROUP BY n.fn_id
    """
    )
    narrs = {r["fn_id"]: (int(r["n_narr"]), int(r["n_titles"])) for r in cur.fetchall()}

    cur.execute(
        "SELECT id, name_en, asset_type, centroid_ids, criticality FROM strategic_assets WHERE is_active IS DISTINCT FROM false"
    )
    assets = cur.fetchall()

    return {
        "fns": fns,
        "anchored": anchored,
        "events": events,
        "narrs": narrs,
        "assets": assets,
    }


def centroid_evidence(conn, fn_ids: list[str]) -> dict[str, list[tuple[str, int]]]:
    """Observed centroid frequency across attributed events' member titles."""
    if not fn_ids:
        return {}
    cur = conn.cursor()
    cur.execute(
        """
        SELECT efn.fn_id, c AS centroid, COUNT(*) n
        FROM event_friction_nodes efn
        JOIN event_v3_titles evt ON evt.event_id = efn.event_id
        JOIN titles_v3 t ON t.id = evt.title_id
        CROSS JOIN LATERAL unnest(t.centroid_ids) c
        WHERE efn.fn_id = ANY(%s)
        GROUP BY 1, 2
    """,
        (fn_ids,),
    )
    out: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for r in cur.fetchall():
        out[r["fn_id"]].append((r["centroid"], int(r["n"])))
    return out


def anchor_lint(conn, fn_ids: list[str]) -> tuple[list[tuple], list[tuple]]:
    """Aliases that over-match under ILIKE '%alias%': hit rate on a random
    sample of recent titles, plus statically suspect short aliases."""
    if not fn_ids:
        return [], []
    cur = conn.cursor()
    cur.execute(
        """
        WITH sample AS (
            SELECT title_display FROM titles_v3
            WHERE pubdate_utc > NOW() - make_interval(days => %s)
            ORDER BY random() LIMIT %s
        ),
        al AS (
            SELECT t.linked_id AS fn_id, a.alias
            FROM taxonomy_v3 t,
            LATERAL (SELECT DISTINCT jsonb_array_elements_text(l.value) AS alias
                     FROM jsonb_each(t.aliases) l) a
            WHERE t.taxonomy_function='fn_anchor' AND t.is_active
              AND t.linked_id = ANY(%s)
        )
        SELECT al.fn_id, al.alias, length(al.alias) AS len,
               (SELECT COUNT(*) FROM sample s
                WHERE s.title_display ILIKE '%%' || al.alias || '%%') AS hits
        FROM al
    """,
        (LINT_WINDOW_DAYS, LINT_SAMPLE, fn_ids),
    )
    rows = cur.fetchall()
    hot = [
        (r["fn_id"], r["alias"], int(r["hits"]))
        for r in rows
        if int(r["hits"]) > LINT_SAMPLE * LINT_HIT_PCT / 100.0
    ]
    short = [
        (r["fn_id"], r["alias"], int(r["hits"]))
        for r in rows
        if r["len"] < LINT_MIN_ALIAS_LEN
    ]
    hot.sort(key=lambda x: -x[2])
    short.sort(key=lambda x: -x[2])
    return hot, short


def region_fn_ids(data: dict, region: str) -> tuple[list[dict], list[str]]:
    """Theaters whose UI region matches, plus all their members, plus
    orphan atomics whose own first centroid matches."""
    fns = data["fns"]
    theaters = [
        f
        for f in fns.values()
        if f["fn_type"] == "theater"
        and f["is_active"]
        and extract_region(f["centroid_ids"]) == region
    ]
    member_ids = {m for t in theaters for m in (t["member_fn_ids"] or [])}
    all_members = {
        m
        for f in fns.values()
        if f["fn_type"] == "theater" and f["is_active"]
        for m in (f["member_fn_ids"] or [])
    }
    orphans = [
        f["id"]
        for f in fns.values()
        if f["fn_type"] == "atomic"
        and f["is_active"]
        and f["id"] not in all_members
        and extract_region(f["centroid_ids"]) == region
    ]
    ids = [t["id"] for t in theaters] + sorted(member_ids) + orphans
    return sorted(theaters, key=lambda t: t["name_en"]), ids


def fmt_fn_row(f: dict, data: dict) -> str:
    ev = data["events"].get(f["id"], (0, None))
    nn = data["narrs"].get(f["id"], (0, 0))
    flags = []
    if f["id"] not in data["anchored"]:
        flags.append("NO ANCHOR")
    if f["missing_de"]:
        flags.append("no DE")
    if f["missing_editorial"]:
        flags.append("no editorial")
    if not f["is_active"]:
        flags.append("INACTIVE")
    last = str(ev[1]) if ev[1] else "-"
    return (
        f"| `{f['id']}` | {f['name_en']} | {ev[0]} | {last} | {nn[0]} | {nn[1]} "
        f"| {len(f['affected_asset_ids'] or [])} | {', '.join(flags) or 'ok'} |"
    )


def build_report(conn, data: dict, region: str) -> str:
    fns = data["fns"]
    theaters, ids = region_fn_ids(data, region)
    lines = [f"# FN Audit -- {region}", ""]
    lines.append(
        f"{len(theaters)} theaters, {len(ids) - len(theaters)} atomic FNs (members + orphans)."
    )
    lines.append("")

    # --- 1. Inventory ---
    lines.append("## 1. Inventory")
    header = (
        "| id | name | events | last_active | narratives | attributed_titles | assets | flags |\n"
        "|---|---|---|---|---|---|---|---|"
    )
    for t in theaters:
        lines.append("")
        lines.append(f"### {t['name_en']} (`{t['id']}`)")
        lines.append(f"Centroids: `{', '.join(t['centroid_ids'] or [])}`")
        lines.append("")
        lines.append(header)
        lines.append(fmt_fn_row(t, data))
        for mid in t["member_fn_ids"] or []:
            m = fns.get(mid)
            if m:
                lines.append(fmt_fn_row(m, data))
            else:
                lines.append(
                    f"| `{mid}` | ** MISSING FROM friction_nodes ** | | | | | | DANGLING |"
                )
    _, all_ids = region_fn_ids(data, region)
    orphan_ids = [
        i
        for i in all_ids
        if fns.get(i, {}).get("fn_type") == "atomic"
        and not any(
            i in (t["member_fn_ids"] or [])
            for t in fns.values()
            if t["fn_type"] == "theater" and t["is_active"]
        )
    ]
    if orphan_ids:
        lines.append("")
        lines.append("### Orphan atomics (no theater)")
        lines.append(header)
        for i in orphan_ids:
            lines.append(fmt_fn_row(fns[i], data))

    # --- 2. Structure ---
    lines.append("")
    lines.append("## 2. Structural issues (global, not region-filtered)")
    member_of = defaultdict(list)
    for f in fns.values():
        if f["fn_type"] == "theater" and f["is_active"]:
            for m in f["member_fn_ids"] or []:
                member_of[m].append(f["id"])
    issues = []
    for m, ts in sorted(member_of.items()):
        if len(ts) > 1:
            issues.append(f"- `{m}` belongs to multiple theaters: {', '.join(ts)}")
        if m not in fns:
            issues.append(
                f"- `{m}` referenced by {', '.join(ts)} but missing from friction_nodes"
            )
        elif not fns[m]["is_active"]:
            issues.append(f"- `{m}` is inactive but still a member of {', '.join(ts)}")
    for f in fns.values():
        if f["fn_type"] == "atomic" and f["is_active"] and f["id"] not in member_of:
            issues.append(f"- `{f['id']}` is an orphan atomic (no theater)")
    for f in fns.values():
        if f["fn_type"] == "theater" and f["is_active"] and f["centroid_ids"]:
            prefixes = {c.split("-")[0] for c in f["centroid_ids"]}
            first = f["centroid_ids"][0].split("-")[0]
            majority = max(
                prefixes,
                key=lambda p: sum(1 for c in f["centroid_ids"] if c.startswith(p)),
            )
            if first != majority and len(prefixes) > 1:
                issues.append(
                    f"- `{f['id']}` region is `{first}` (first centroid) but majority prefix is `{majority}` -- region grouping depends on array order"
                )
    lines.extend(issues or ["- none found"])

    # --- 3. Duplicate candidates ---
    lines.append("")
    lines.append(f"## 3. Duplicate candidates within {region}")
    rfns = [fns[i] for i in ids if i in fns]
    dups = []
    for i, a in enumerate(rfns):
        for b in rfns[i + 1 :]:
            ta, tb = name_tokens(a["name_en"]), name_tokens(b["name_en"])
            shared = ta & tb
            jacc = len(shared) / len(ta | tb) if ta | tb else 0
            ca, cb = set(a["centroid_ids"] or []), set(b["centroid_ids"] or [])
            cent_same = ca and ca == cb
            if (
                len(shared) >= 2
                or jacc >= 0.5
                or (cent_same and a["fn_type"] == b["fn_type"])
            ):
                why = []
                if shared:
                    why.append(f"name tokens: {', '.join(sorted(shared))}")
                if cent_same:
                    why.append("identical centroid set")
                dups.append(f"- `{a['id']}` vs `{b['id']}` ({why and '; '.join(why)})")
    lines.extend(dups or ["- none found"])

    # --- 4. Centroid evidence ---
    lines.append("")
    lines.append("## 4. Centroid audit (FNs with attributed events)")
    lines.append(
        f"Flags: DEAD = declared but <{DECLARED_DEAD_PCT}% of titles; "
        f"HOT = undeclared but >={UNDECLARED_HOT_PCT}% of titles."
    )
    ev_ids = [i for i in ids if i in data["events"]]
    evidence = centroid_evidence(conn, ev_ids)
    for fid in ev_ids:
        obs = sorted(evidence.get(fid, []), key=lambda x: -x[1])
        total = sum(n for _, n in obs) or 1
        declared = set(fns[fid]["centroid_ids"] or [])
        lines.append("")
        lines.append(f"### `{fid}` ({total} title-centroid hits)")
        rows, flagged = [], []
        for c, n in obs[:15]:
            pct = 100.0 * n / total
            mark = "declared" if c in declared else ""
            if c not in declared and pct >= UNDECLARED_HOT_PCT:
                mark = "**HOT -- add?**"
                flagged.append(c)
            rows.append(f"| {c} | {n} | {pct:.1f}% | {mark} |")
        seen = {c for c, _ in obs}
        for c in sorted(declared):
            pct = 100.0 * dict(obs).get(c, 0) / total
            if c not in seen or pct < DECLARED_DEAD_PCT:
                rows.append(
                    f"| {c} | {dict(obs).get(c, 0)} | {pct:.1f}% | **DEAD -- remove?** |"
                )
        lines.append("| centroid | titles | share | flag |")
        lines.append("|---|---|---|---|")
        lines.extend(rows)

    # --- 5. Assets ---
    lines.append("")
    lines.append("## 5. Assets")
    linked = {
        a
        for f in fns.values()
        if f["is_active"]
        for a in (f["affected_asset_ids"] or [])
    }
    region_prefixes = {region} if region != "NON-STATE" else set()
    region_assets = [
        a
        for a in data["assets"]
        if any(c.split("-")[0] in region_prefixes for c in (a["centroid_ids"] or []))
    ]
    unlinked = [a for a in region_assets if a["id"] not in linked]
    lines.append(
        f"{len(region_assets)} registry assets have a {region} centroid; "
        f"{len(unlinked)} are linked to NO friction node:"
    )
    lines.append("")
    lines.append("| id | name | type | criticality | centroids |")
    lines.append("|---|---|---|---|---|")
    for a in sorted(unlinked, key=lambda x: -(x["criticality"] or 0)):
        lines.append(
            f"| `{a['id']}` | {a['name_en']} | {a['asset_type']} | {a['criticality']} "
            f"| {', '.join(a['centroid_ids'] or [])} |"
        )
    lines.append("")
    lines.append("Per-theater linked assets:")
    for t in theaters:
        aids = t["affected_asset_ids"] or []
        lines.append(f"- `{t['id']}`: {', '.join(aids) if aids else '(none)'}")

    # --- 6. Anchor lint ---
    lines.append("")
    lines.append("## 6. Anchor lint (over-matching aliases)")
    lines.append(
        f"Hit rate of each alias (substring ILIKE) on {LINT_SAMPLE} random titles "
        f"from the last {LINT_WINDOW_DAYS} days. An on-topic alias should be rare; "
        f"anything above {LINT_HIT_PCT}% pollutes attribution."
    )
    hot, short = anchor_lint(conn, [i for i in ids if i in data["anchored"]])
    lines.append("")
    lines.append(f"### Aliases hitting >{LINT_HIT_PCT}% of random titles")
    if hot:
        lines.append("| fn_id | alias | hits | sample share |")
        lines.append("|---|---|---|---|")
        for fid, alias, hits in hot:
            lines.append(
                f"| `{fid}` | `{alias}` | {hits} | {100.0 * hits / LINT_SAMPLE:.1f}% |"
            )
    else:
        lines.append("- none")
    lines.append("")
    lines.append(
        f"### Aliases shorter than {LINT_MIN_ALIAS_LEN} chars (substring-collision risk)"
    )
    if short:
        lines.append("| fn_id | alias | hits in sample |")
        lines.append("|---|---|---|")
        for fid, alias, hits in short:
            lines.append(f"| `{fid}` | `{alias}` | {hits} |")
    else:
        lines.append("- none")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--region", choices=REGIONS)
    g.add_argument("--all", action="store_true")
    args = p.parse_args()

    conn = psycopg2.connect(**config.db_connect_kwargs(), cursor_factory=RealDictCursor)
    data = load(conn)
    out_dir = Path(__file__).parent.parent / "out"
    out_dir.mkdir(exist_ok=True)
    for region in REGIONS if args.all else [args.region]:
        report = build_report(conn, data, region)
        path = out_dir / f"fn_audit_{region}.md"
        path.write_text(report, encoding="utf-8")
        print(f"OK wrote {path}")
    conn.close()


if __name__ == "__main__":
    main()
