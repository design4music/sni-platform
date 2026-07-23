"""P0(c) -- thin-narrative triage.

NARRATIVE_CONSOLIDATION_SPEC.md P0(c): classify narratives with too few
attributed titles as bad publisher bloc / dead vocabulary / genuinely silent,
so DG-0 #3 (the publication-gate threshold) is decided against real numbers.

METHOD. `link_titles` is a conjunction, so the diagnosis is a funnel -- relax
one condition at a time and see which step drops the count to zero:

  S0  in window, centroid overlap, primary_target      -- the FN's terrain
  S1  S0 + an fn_anchor alias hit                      -- the FN's title pool
  S2  S1 + publisher in this narrative's bloc
  S3  S2 + a framing keyword (only if framing_required) == attributed count

  S1 == 0                     -> FN_GATE_DEAD    (FN-level: no bundle, wrong
                                                  centroids, or primary_target
                                                  excludes everything)
  S1 > 0, S2 == 0             -> BAD_PUBLISHER_BLOC
  S2 > 0, S3 == 0             -> DEAD_VOCABULARY (framing_required, no keyword hits)
  S3 > 0 but under the gate   -> GENUINELY_THIN  (gate works, position barely voiced)

The funnel only runs for narratives with ZERO attributed titles -- spec C4 asks
to triage exactly those, and for a narrative that has any titles at all the gate
is demonstrably working end to end, so it is GENUINELY_THIN by construction with
nothing to diagnose. This is not an approximation, and it matters: each funnel
step is a scan of ~325k titles with alias regex, ~90s apiece.

Per FN, the pool is materialized into a temp table once and the per-narrative
publisher/framing steps run against that (a few thousand rows) instead of
re-scanning titles_v3.

Theater narratives attribute no titles of their own (no bundle by design); their
count is the THEATER_ROLLUP_SQL union over member atomics. They get their own
funnel: member atomics with a same-sign narrative, then publisher overlap.

Read-only. Writes a markdown report, touches no table.

Usage:
  python scripts/thin_narrative_triage.py
  python scripts/thin_narrative_triage.py --gate 25 --window-days 180
"""

from __future__ import annotations

import argparse
import collections
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config  # noqa: E402
from scripts.bootstrap_friction_node import (  # noqa: E402
    ALIAS_MATCH_EN_SQL,
    ALIAS_MATCH_OTHER_SQL,
    flatten_aliases,
)
from scripts.narrative_counts import effective_counts  # noqa: E402

OUT = (
    Path(__file__).parent.parent
    / "out"
    / "narrative_consolidation"
    / "P0c_thin_narratives.md"
)
DEFAULT_GATE = 25
WINDOW_DAYS = 180

# One scan per FN. Materializes the FN's alias-matching title pool (S1) into a
# temp table; S0 comes back alongside it so the scan is not repeated.
TERRAIN_SQL = """
    SELECT COUNT(*)::int AS c
      FROM titles_v3 t
     WHERE t.pubdate_utc > NOW() - (%(window)s || ' days')::interval
       AND t.centroid_ids && %(centroids)s::text[]
       AND (%(primary_target)s::text IS NULL OR %(primary_target)s = ANY(t.centroid_ids))
"""

BUILD_POOL_SQL = (
    """
    CREATE TEMP TABLE fn_pool AS
    SELECT t.id, t.publisher_name, t.title_display
      FROM titles_v3 t
     WHERE t.pubdate_utc > NOW() - (%(window)s || ' days')::interval
       AND t.centroid_ids && %(centroids)s::text[]
       AND (%(primary_target)s::text IS NULL OR %(primary_target)s = ANY(t.centroid_ids))
       AND (
         EXISTS (SELECT 1 FROM unnest(%(en_aliases)s::text[]) kw WHERE """
    + ALIAS_MATCH_EN_SQL
    + """)
         OR EXISTS (SELECT 1 FROM unnest(%(other_aliases)s::text[]) kw WHERE """
    + ALIAS_MATCH_OTHER_SQL
    + """)
       )
"""
)

PUB_SQL = """
    SELECT COUNT(*)::int AS c FROM fn_pool t
     WHERE t.publisher_name = ANY(%(publishers)s)
"""

FRAMED_SQL = (
    PUB_SQL
    + """       AND EXISTS (SELECT 1 FROM unnest(%(framing_keywords)s::text[]) fk
                    WHERE t.title_display ILIKE '%%' || fk || '%%')
"""
)

# Theater funnel: member atomics carrying a same-sign narrative, then the
# theater narrative's publisher bloc over those atomics' attributed titles.
THEATER_SAMESIGN_SQL = """
    SELECT COUNT(DISTINCT t.id)::int AS c
      FROM title_narratives tn
      JOIN narratives_v2 an ON an.id = tn.narrative_id
      JOIN friction_nodes afn ON afn.id = an.fn_id
      JOIN titles_v3 t ON t.id = tn.title_id
     WHERE afn.id = ANY(%(members)s) AND afn.fn_type = 'atomic'
       AND an.stance IS NOT NULL AND sign(an.stance)::int = sign(%(stance)s::int)
"""

CLASSES = (
    "FN_GATE_DEAD",
    "BAD_PUBLISHER_BLOC",
    "DEAD_VOCABULARY",
    "GENUINELY_THIN",
    "THEATER_NO_SAMESIGN_MEMBER",
    "THEATER_BLOC_MISS",
    "NO_PUBLISHERS_CONFIGURED",
)

REMEDY = {
    "FN_GATE_DEAD": "FN-level, not narrative-level: missing/blind fn_anchor bundle, "
    "wrong centroid_ids, or a primary_target that excludes the corpus. Fix on the "
    "FN under FN_THEATER_BUILD_SPEC.md; every narrative on the FN is affected.",
    "BAD_PUBLISHER_BLOC": "The FN has titles, but no outlet in this narrative's "
    "publisher bloc covers this terrain. Re-measure the bloc against the corpus "
    "before shipping the narrative.",
    "DEAD_VOCABULARY": "Publishers match, framing keywords match nothing. "
    "framing_required is filtering everything out -- corpus-verify the keywords "
    "or drop the requirement.",
    "GENUINELY_THIN": "The gate works and the position is honestly barely voiced. "
    "Keep as an FN card; this is the population the publication gate exists for.",
    "THEATER_NO_SAMESIGN_MEMBER": "No member atomic carries a narrative of the same "
    "stance sign, so the roll-up can never find titles. Either the theater card's "
    "stance is wrong or the member atomics are missing that side.",
    "THEATER_BLOC_MISS": "Member atomics have same-sign titles, but none from this "
    "theater card's publisher bloc. Same-sign theater cards must be "
    "publisher-DISJOINT, so widening the bloc risks double-counting -- check both.",
    "NO_PUBLISHERS_CONFIGURED": "publishers[] is empty; link_titles short-circuits "
    "to zero. Authoring gap.",
}


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--gate", type=int, default=DEFAULT_GATE)
    p.add_argument("--window-days", type=int, default=WINDOW_DAYS)
    return p.parse_args()


def scalar(cur, sql, params) -> int:
    cur.execute(sql, params)
    return cur.fetchone()["c"]


def diagnose_atomic(cur, r, bundle, window, fn_cache) -> tuple[str, dict]:
    en_aliases, other_aliases = bundle
    base = {
        "window": str(window),
        "centroids": list(r["centroid_ids"] or []),
        "primary_target": r["primary_target"],
        "en_aliases": en_aliases,
        "other_aliases": other_aliases,
        "publishers": r["publishers"] or [],
        "framing_keywords": r["framing_keywords"] or [],
    }
    if not base["publishers"]:
        return "NO_PUBLISHERS_CONFIGURED", {}
    if not base["centroids"] or (not en_aliases and not other_aliases):
        return "FN_GATE_DEAD", {"s0": 0, "s1": 0, "s2": 0, "s3": 0}

    # S0 and S1 depend only on the FN, not on the narrative -- and this is the
    # expensive scan, so build the pool once per FN and reuse it.
    if fn_cache.get("__fn__") != r["fn_id"]:
        cur.execute("DROP TABLE IF EXISTS fn_pool")
        cur.execute(BUILD_POOL_SQL, base)
        fn_cache["__fn__"] = r["fn_id"]
        fn_cache["__s0__"] = scalar(cur, TERRAIN_SQL, base)
        fn_cache["__s1__"] = scalar(cur, "SELECT COUNT(*)::int AS c FROM fn_pool", {})
    s0, s1 = fn_cache["__s0__"], fn_cache["__s1__"]
    if s1 == 0:
        return "FN_GATE_DEAD", {"s0": s0, "s1": 0, "s2": 0, "s3": 0}
    s2 = scalar(cur, PUB_SQL, base)
    if s2 == 0:
        return "BAD_PUBLISHER_BLOC", {"s0": s0, "s1": s1, "s2": 0, "s3": 0}
    s3 = s2
    if r["framing_required"]:
        s3 = scalar(cur, FRAMED_SQL, base) if base["framing_keywords"] else 0
        if s3 == 0:
            return "DEAD_VOCABULARY", {"s0": s0, "s1": s1, "s2": s2, "s3": 0}
    return "GENUINELY_THIN", {"s0": s0, "s1": s1, "s2": s2, "s3": s3}


def diagnose_theater(cur, r) -> tuple[str, dict]:
    members = r["member_fn_ids"] or []
    publishers = r["publishers"] or []
    if not publishers:
        return "NO_PUBLISHERS_CONFIGURED", {}
    if not members or r["stance"] is None:
        return "THEATER_NO_SAMESIGN_MEMBER", {"samesign": 0}
    samesign = scalar(
        cur, THEATER_SAMESIGN_SQL, {"members": members, "stance": r["stance"]}
    )
    if samesign == 0:
        return "THEATER_NO_SAMESIGN_MEMBER", {"samesign": 0}
    return "THEATER_BLOC_MISS", {"samesign": samesign}


def main():
    args = parse_args()
    conn = psycopg2.connect(**config.db_connect_kwargs(), cursor_factory=RealDictCursor)
    conn.autocommit = True  # read-only; keeps the temp pool table alive per FN
    cur = conn.cursor()

    cur.execute(
        """SELECT n.id, n.fn_id, n.stance, n.name_en, n.publishers,
                  n.framing_keywords, n.framing_required,
                  f.fn_type, f.member_fn_ids, f.centroid_ids, f.primary_target
             FROM narratives_v2 n
             JOIN friction_nodes f ON f.id = n.fn_id
            WHERE n.is_active AND f.is_active
            ORDER BY n.fn_id, n.display_order"""
    )
    rows = [dict(r) for r in cur.fetchall()]
    counts = effective_counts(cur, rows)

    cur.execute(
        """SELECT linked_id, aliases FROM taxonomy_v3
            WHERE taxonomy_function = 'fn_anchor' AND is_active = true"""
    )
    bundles = {r["linked_id"]: flatten_aliases(r["aliases"]) for r in cur.fetchall()}

    thin = [r for r in rows if counts.get(r["id"], 0) < args.gate]
    # Only zero-title narratives need the funnel; anything with titles has a
    # working gate by construction. Grouped by fn_id so the pool builds once.
    dead = sorted(
        [r for r in thin if counts.get(r["id"], 0) == 0], key=lambda x: x["fn_id"]
    )
    verdicts = {}
    fn_cache: dict[str, object] = {}
    for i, r in enumerate(dead, 1):
        if r["fn_type"] == "theater":
            verdicts[r["id"]] = diagnose_theater(cur, r)
        else:
            verdicts[r["id"]] = diagnose_atomic(
                cur,
                r,
                bundles.get(r["fn_id"], ([], [])),
                args.window_days,
                fn_cache,
            )
        print(
            "  [%2d/%d] %-46s %s" % (i, len(dead), r["id"], verdicts[r["id"]][0]),
            flush=True,
        )
    for r in thin:
        if r["id"] not in verdicts:
            verdicts[r["id"]] = ("GENUINELY_THIN", {})
    conn.close()

    dist = collections.Counter(v[0] for v in verdicts.values())
    buckets = collections.Counter()
    for r in rows:
        n = counts.get(r["id"], 0)
        buckets[
            (
                "zero"
                if n == 0
                else (
                    "1-9"
                    if n < 10
                    else "10-24" if n < 25 else "25-99" if n < 100 else "100+"
                )
            )
        ] += 1

    L = []
    L.append("# P0(c) -- Thin-narrative triage")
    L.append("")
    L.append(
        "Artifact for `NARRATIVE_CONSOLIDATION_SPEC.md` P0(c), feeding **DG-0 #3** "
        "(publication-gate threshold). Read-only; nothing was written."
    )
    L.append("")
    L.append("## Correction to spec 5.4")
    L.append("")
    L.append(
        "Spec 5.4 reports **71 of 309 (23%) with zero attributed titles**. That "
        "figure counts `title_narratives` rows only. Theater narratives carry no "
        "`fn_anchor` bundle *by design* and never attribute a title directly -- "
        "their count is the `THEATER_ROLLUP_SQL` union over member atomics, which "
        "is what the FN page actually renders. Counting them off `title_narratives` "
        "reports every theater narrative as dead."
    )
    L.append("")
    L.append(
        "Measured roll-up-aware over %d active narratives (attribution rebuilt "
        "in full on 2026-07-21, %d-day window):" % (len(rows), args.window_days)
    )
    L.append("")
    L.append("| attributed titles | narratives | share |")
    L.append("|---|---:|---:|")
    for k in ("zero", "1-9", "10-24", "25-99", "100+"):
        L.append(
            "| %s | %d | %.0f%% |" % (k, buckets[k], 100.0 * buckets[k] / len(rows))
        )
    L.append("")
    L.append(
        "**%d truly have zero, not 71.** But **%d of %d (%.0f%%) fall under the "
        "proposed gate of %d** -- so the gate, not the zero count, is the live "
        "question at DG-0 #3."
        % (
            buckets["zero"],
            len(thin),
            len(rows),
            100.0 * len(thin) / len(rows),
            args.gate,
        )
    )
    L.append("")
    L.append("### Where the gate would land")
    L.append("")
    L.append("| gate | published | suppressed |")
    L.append("|---:|---:|---:|")
    for g in (10, 25, 50, 100):
        pub = sum(1 for r in rows if counts.get(r["id"], 0) >= g)
        L.append("| >= %d | %d | %d |" % (g, pub, len(rows) - pub))
    L.append("")
    L.append("---")
    L.append("")
    L.append("## Triage of the %d under-gate narratives" % len(thin))
    L.append("")
    L.append(
        "The **%d zero-title** narratives are classified by replaying the "
        "`link_titles` conjunction as a funnel and finding which condition zeroes "
        "it: `S0` terrain (centroids + primary_target), `S1` + fn_anchor alias hit, "
        "`S2` + publisher bloc, `S3` + framing keyword when `framing_required`."
        % buckets["zero"]
    )
    L.append("")
    L.append(
        "The other %d are `GENUINELY_THIN` **by construction** -- a narrative that "
        "attributed any titles at all has a gate that demonstrably works at every "
        "step, so there is nothing to diagnose. (This is also why the funnel is not "
        "run on them: each step is a ~325k-title scan with alias regex.)"
        % (len(thin) - buckets["zero"])
    )
    L.append("")
    L.append("| class | narratives | meaning |")
    L.append("|---|---:|---|")
    for c in CLASSES:
        if dist[c]:
            L.append("| `%s` | %d | %s |" % (c, dist[c], REMEDY[c].split(".")[0] + "."))
    L.append("")
    L.append(
        "Note `GENUINELY_THIN` is the only class the publication gate is *for*. "
        "The others are calibration defects that a gate would hide rather than fix "
        "-- they belong to FN work under `FN_THEATER_BUILD_SPEC.md`, and spec 5.4 "
        "already says that runs in parallel and blocks a clean launch."
    )
    L.append("")

    by_id = {r["id"]: r for r in rows}
    for c in CLASSES:
        members = [k for k, v in verdicts.items() if v[0] == c]
        if not members:
            continue
        L.append("---")
        L.append("")
        L.append("### `%s` -- %d narratives" % (c, len(members)))
        L.append("")
        L.append("**Remedy.** %s" % REMEDY[c])
        L.append("")
        L.append("| narrative | friction node | type | stance | titles | funnel |")
        L.append("|---|---|---|---:|---:|---|")
        for m in sorted(members, key=lambda x: (by_id[x]["fn_id"], x)):
            r = by_id[m]
            f = verdicts[m][1]
            if c.startswith("THEATER"):
                funnel = "same-sign member titles: %d" % f.get("samesign", 0)
            elif f:
                funnel = "S0 %d -> S1 %d -> S2 %d -> S3 %d" % (
                    f.get("s0", 0),
                    f.get("s1", 0),
                    f.get("s2", 0),
                    f.get("s3", 0),
                )
            else:
                funnel = "-"
            L.append(
                "| `%s` | `%s` | %s | %+d | %d | %s |"
                % (
                    m,
                    r["fn_id"],
                    r["fn_type"],
                    r["stance"] or 0,
                    counts.get(m, 0),
                    funnel,
                )
            )
        L.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(L), encoding="utf-8")

    print("active narratives : %d" % len(rows))
    print("zero titles       : %d  (spec 5.4 said 71 -- see report)" % buckets["zero"])
    print("under gate %-3d    : %d" % (args.gate, len(thin)))
    for c in CLASSES:
        if dist[c]:
            print("  %-28s %d" % (c, dist[c]))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
