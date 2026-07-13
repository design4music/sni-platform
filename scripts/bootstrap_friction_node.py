"""Friction-node attribution bootstrap.

Populates event_friction_nodes + title_narratives for a single friction
node, reading all per-FN configuration from the database.

Two entry points:
  - CLI (main): one FN, interactive. Run when a new FN is added, its
    narratives/publishers change, or keyword tuning lands.
  - refresh_all_active(conn): every active FN, for the daemon's fn_refresh
    slot -- this is what keeps theater attribution current as news flows.
    Atomics are re-attributed before theaters (theater title attribution
    excludes titles already claimed by an atomic FN).

Usage:
  python scripts/bootstrap_friction_node.py --fn-id iran_nuclear_program
  python scripts/bootstrap_friction_node.py --fn-id iran_nuclear_program --window-days 90

Inputs read from DB:
  friction_nodes.centroid_ids
    Default actor-scope for event + title attribution.

  taxonomy_v3 (taxonomy_function='fn_anchor', linked_id=fn.id)
    Multi-lingual alias bundle used as the topic gate.

  narratives_v2  (1-to-1 with friction_nodes via fn_id)
    Per-narrative attribution rule: publisher cohort + framing-keyword
    fingerprint. Attribution scope inherits the parent FN's centroid_ids.

Side effects:
  - DELETEs all existing event_friction_nodes rows for the FN
  - DELETEs all existing title_narratives rows for the FN's narratives
  - INSERTs the new attribution sets
  - Idempotent: re-runs produce the same result
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


class FNConfigError(Exception):
    """A friction node is missing config needed to attribute (no centroids
    or no fn_anchor bundle). Fatal for the CLI, skippable in batch."""


# Alias match semantics (see out/fn_audit_EUROPE.md section 6 for why the
# old substring ILIKE over-matched: EW hit 9.2% of random titles via "news").
# Two independent paths -- aliases are pre-split by source language (see
# flatten_aliases) because English needs boundary protection that other
# languages don't have and can't safely use. German compounds words with no
# separator ("Fluechtlinge" embedded in "Kriegsfluechtlinge" has no \m
# transition to anchor on) -- a boundary regex silently stops matching real
# German compounds even with correct spelling. Non-English aliases in this
# system are either script-distinct (ru/zh/ar/ja/hi -- no word-boundary
# concept to exploit) or long, specific Latin words, not the short/generic
# tokens that made bare substring risky for English. New non-English
# aliases should still avoid short/generic single words (same spirit as the
# "no 2-char token" rule) since this path has no boundary protection.
# `kw` and `t` must be in scope. Regex metachars escaped SQL-side.
_ACRONYM_MATCH = r"""t.title_display ~ ('\m' || regexp_replace(kw, '([.^$*+?()\[\]{}|\\])', '\\\1', 'g') || '\M')"""
_WORD_START_MATCH = r"""t.title_display ~* ('\m' || regexp_replace(kw, '([.^$*+?()\[\]{}|\\])', '\\\1', 'g'))"""
_SUBSTRING_MATCH = r"""t.title_display ILIKE '%%' || kw || '%%'"""

# EN path: short all-caps acronyms (<=4 chars) get case-SENSITIVE whole-word
# matching -- REPO stops matching "report", POW stops matching "power".
# Everything else: case-insensitive word-START anchor; prefix match is kept
# deliberately so stems still work (dron -> drone/dronow).
ALIAS_MATCH_EN_SQL = f"""(CASE
    WHEN kw ~ '^[A-Z0-9][A-Z0-9-]{{0,3}}$' THEN {_ACRONYM_MATCH}
    ELSE {_WORD_START_MATCH} END)"""

# Other-language path (de/es/fr/it/ru/zh/ar/ja/hi): same acronym protection
# (acronyms are acronyms regardless of source language), else substring --
# no word-boundary requirement, so German/compounding languages match
# correctly and CJK/Arabic/Hindi (no boundary concept) are unaffected.
ALIAS_MATCH_OTHER_SQL = f"""(CASE
    WHEN kw ~ '^[A-Z0-9][A-Z0-9-]{{0,3}}$' THEN {_ACRONYM_MATCH}
    ELSE {_SUBSTRING_MATCH} END)"""


def flatten_aliases(aliases_json: dict | None) -> tuple[list[str], list[str]]:
    """Split a fn_anchor aliases jsonb into (en_aliases, other_aliases),
    deduped, preserving first-seen order. The split -- not just the
    flattened union -- is what lets EN and non-EN route through different
    match semantics (see ALIAS_MATCH_EN_SQL / ALIAS_MATCH_OTHER_SQL)."""
    en_aliases: list[str] = []
    other_aliases: list[str] = []
    if not aliases_json:
        return en_aliases, other_aliases
    seen: set[str] = set()
    for a in aliases_json.get("en") or []:
        if a and a not in seen:
            seen.add(a)
            en_aliases.append(a)
    for lang, lang_aliases in aliases_json.items():
        if lang == "en":
            continue
        for a in lang_aliases or []:
            if a and a not in seen:
                seen.add(a)
                other_aliases.append(a)
    return en_aliases, other_aliases


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--fn-id", required=True, help="friction_nodes.id")
    p.add_argument(
        "--window-days",
        type=int,
        default=180,
        help="title + event window for attribution (default 180)",
    )
    return p.parse_args()


def fetch_fn(cur, fn_id: str) -> dict:
    cur.execute(
        """SELECT id, name_en, fn_type, centroid_ids, primary_target
             FROM friction_nodes
            WHERE id = %s AND is_active = true""",
        (fn_id,),
    )
    row = cur.fetchone()
    if not row:
        raise SystemExit(f"friction_node id={fn_id} not found or inactive")
    return row


def fetch_narratives(cur, fn_id: str) -> list[dict]:
    cur.execute(
        """SELECT id, name_en, publishers, framing_keywords, framing_required
             FROM narratives_v2
            WHERE fn_id = %s AND is_active = true
            ORDER BY display_order""",
        (fn_id,),
    )
    return cur.fetchall()


def link_events(cur, fn: dict, window_days: int, incremental: bool = False) -> int:
    """Apply the FN's event gate to populate event_friction_nodes.

    Uses the same shape as title attribution:
      - centroid scope: ANY member title of the event must overlap fn.centroid_ids
      - primary target scope: at least one title must contain primary_target centroid (if set)
      - topic gate: event canonical title matches any fn_anchor bundle alias

    incremental=True (daemon path): skip the DELETE and only INSERT (ON
    CONFLICT DO NOTHING) over a short recent window. Additive and cheap --
    never wipes existing attribution. Full recompute (incremental=False)
    is the CLI path.
    """
    fn_centroid_ids = fn["centroid_ids"] or []
    if not fn_centroid_ids:
        raise FNConfigError(
            f"FN {fn['id']} has no centroid_ids configured; cannot scope event attribution"
        )

    # Fetch the fn_anchor bundle aliases (flattened across all 10 languages).
    cur.execute(
        """SELECT aliases FROM taxonomy_v3
           WHERE taxonomy_function = 'fn_anchor'
             AND linked_id = %s
             AND is_active = true""",
        (fn["id"],),
    )
    row = cur.fetchone()
    en_aliases, other_aliases = flatten_aliases(row["aliases"] if row else None)
    if not en_aliases and not other_aliases:
        raise FNConfigError(f"FN {fn['id']} has no fn_anchor bundle in taxonomy_v3")

    if not incremental:
        cur.execute(
            "DELETE FROM event_friction_nodes WHERE fn_id = %s",
            (fn["id"],),
        )

    # Build primary_target filter: if set, require at least 50% of event titles
    # contain the primary_target centroid (semantic check that event is really about that region).
    primary_target_filter = ""
    primary_target = fn.get("primary_target")
    if primary_target:
        primary_target_filter = """
              AND (
                SELECT COUNT(*) FILTER (WHERE t2.centroid_ids @> ARRAY[%(primary_target)s::text])::float
                / NULLIF(COUNT(*), 0)
                FROM event_v3_titles et2
                JOIN titles_v3 t2 ON t2.id = et2.title_id
                WHERE et2.event_id = e.id
              ) >= 0.5
        """

    sql = (
        """INSERT INTO event_friction_nodes (event_id, fn_id)
           SELECT e.id, %(fn_id)s
             FROM events_v3 e
            WHERE e.is_promoted = true
              AND e.merged_into IS NULL
              AND e.date > (CURRENT_DATE - (%(window)s || ' days')::interval)
              AND EXISTS (
                SELECT 1 FROM event_v3_titles et
                JOIN titles_v3 t ON t.id = et.title_id
                WHERE et.event_id = e.id
                  AND t.centroid_ids && %(centroids)s::text[]
              )
              AND EXISTS (
                SELECT 1 FROM event_v3_titles et
                JOIN titles_v3 t ON t.id = et.title_id
                WHERE et.event_id = e.id
                  AND (
                    EXISTS (SELECT 1 FROM unnest(%(en_aliases)s::text[]) kw WHERE """
        + ALIAS_MATCH_EN_SQL
        + """)
                    OR EXISTS (SELECT 1 FROM unnest(%(other_aliases)s::text[]) kw WHERE """
        + ALIAS_MATCH_OTHER_SQL
        + """)
                  )
              )"""
        + primary_target_filter
        + """
           ON CONFLICT (event_id, fn_id) DO NOTHING"""
    )

    cur.execute(
        sql,
        {
            "fn_id": fn["id"],
            "window": str(window_days),
            "centroids": fn_centroid_ids,
            "primary_target": primary_target,
            "en_aliases": en_aliases,
            "other_aliases": other_aliases,
        },
    )
    return cur.rowcount


def link_titles(
    cur, fn: dict, narratives: list[dict], window_days: int, incremental: bool = False
) -> dict[str, int]:
    """Apply per-narrative title attribution rules.

    Each narrative's titles must:
      - come from a publisher in narrative.publishers
      - mention any alias from the FN's fn_anchor bundle in taxonomy_v3
      - have centroid_ids overlapping fn.centroid_ids
      - if fn.primary_target is set, the title itself must carry that
        centroid (symmetric with link_events' 50%-of-event-titles check,
        simplified to a direct check since a title is atomic)

    framing_keywords are NOT a hard attribution filter by default -- under
    the 1-to-1 model pro/con narratives on one FN have disjoint publisher
    lists, so publisher alone disambiguates, and framing_keywords stay on the
    narrative for sample-title ranking + the "Loaded vocabulary" UI.

    EXCEPTION -- framing_required=true: when narratives on one FN SHARE a
    publisher coalition but compete on stance (the "friendly-critic" own-goal
    case, e.g. Western outlets voicing both reform-progress and systemic-alarm
    framings of Ukraine corruption), publisher cannot disambiguate. Setting
    framing_required makes a framing_keyword hit an additional AND-condition,
    so the title attributes only to the narrative whose framing it matches.
    Opt-in per narrative; default false leaves every other narrative unchanged.

    For fn_type='theater' (catch-all), titles already attributed to any
    atomic FN are excluded — atomic FNs claim their content first.
    """
    narrative_ids = [n["id"] for n in narratives]
    if not narrative_ids:
        return {}

    # FN-level alias bundle (taxonomy_v3 fn_anchor row for this FN).
    cur.execute(
        """SELECT aliases FROM taxonomy_v3
           WHERE taxonomy_function = 'fn_anchor'
             AND linked_id = %s
             AND is_active = true""",
        (fn["id"],),
    )
    row = cur.fetchone()
    en_aliases, other_aliases = flatten_aliases(row["aliases"] if row else None)

    if not incremental:
        cur.execute(
            "DELETE FROM title_narratives WHERE narrative_id = ANY(%s)",
            (narrative_ids,),
        )

    is_theater = fn.get("fn_type") == "theater"
    centroids = fn["centroid_ids"] or []
    primary_target = fn.get("primary_target")
    counts: dict[str, int] = {}
    for n in narratives:
        publishers = n["publishers"] or []

        if not publishers or (not en_aliases and not other_aliases) or not centroids:
            counts[n["id"]] = 0
            continue

        cur.execute(
            """INSERT INTO title_narratives (title_id, narrative_id)
               SELECT t.id, %(narrative_id)s
                 FROM titles_v3 t
                WHERE t.publisher_name = ANY(%(publishers)s)
                  AND t.pubdate_utc > NOW() - (%(window)s || ' days')::interval
                  AND t.centroid_ids && %(centroids)s::text[]
                  AND (
                    EXISTS (SELECT 1 FROM unnest(%(en_aliases)s::text[]) kw WHERE """
            + ALIAS_MATCH_EN_SQL
            + """)
                    OR EXISTS (SELECT 1 FROM unnest(%(other_aliases)s::text[]) kw WHERE """
            + ALIAS_MATCH_OTHER_SQL
            + """)
                  )
                  AND (%(primary_target)s::text IS NULL OR %(primary_target)s = ANY(t.centroid_ids))
                  AND (NOT %(framing_required)s OR EXISTS (
                      SELECT 1 FROM unnest(%(framing_keywords)s::text[]) fk
                       WHERE t.title_display ILIKE '%%' || fk || '%%'
                  ))
                  AND (NOT %(is_theater)s OR NOT EXISTS (
                      SELECT 1
                        FROM title_narratives tn2
                        JOIN narratives_v2 n2 ON n2.id = tn2.narrative_id
                        JOIN friction_nodes fn2 ON fn2.id = n2.fn_id
                       WHERE tn2.title_id = t.id
                         AND fn2.fn_type = 'atomic'
                  ))
               ON CONFLICT (title_id, narrative_id) DO NOTHING""",
            {
                "narrative_id": n["id"],
                "publishers": publishers,
                "window": str(window_days),
                "centroids": list(centroids),
                "en_aliases": en_aliases,
                "other_aliases": other_aliases,
                "is_theater": is_theater,
                "primary_target": primary_target,
                "framing_required": bool(n.get("framing_required")),
                "framing_keywords": n["framing_keywords"] or [],
            },
        )
        counts[n["id"]] = cur.rowcount

    return counts


def refresh_all_active(conn, window_days: int = 7, incremental: bool = True) -> dict:
    """Re-attribute EVERY active friction node in one transaction.

    Called by the daemon's fn_refresh slot. Atomics run first so theater
    title attribution (which excludes titles already claimed by an atomic)
    sees the fresh atomic sets. FNs missing config (no bundle/centroids)
    are skipped, not fatal.

    Default is INCREMENTAL over a short window (additive, ON CONFLICT DO
    NOTHING, no DELETE) -- the daemon path, cheap enough to run every few
    hours. A full recompute (incremental=False, window_days=180) is the
    manual/CLI reconciliation for when centroids/anchors/publishers change
    or to catch old-dated events that were promoted late; it deletes and
    rebuilds every FN's attribution and is slow (~25 min over 150 FNs), so
    it is NOT the daemon default.
    """
    n_fns = n_events = n_titles = n_skipped = 0
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # (fn_type='theater') sorts False(atomic) before True(theater).
        cur.execute(
            """SELECT id, name_en, fn_type, centroid_ids, primary_target
                 FROM friction_nodes
                WHERE is_active = true
                ORDER BY (fn_type = 'theater'), id"""
        )
        fns = cur.fetchall()
        for fn in fns:
            narratives = fetch_narratives(cur, fn["id"])
            if fn.get("fn_type") != "theater":
                try:
                    n_events += link_events(cur, fn, window_days, incremental)
                except FNConfigError:
                    n_skipped += 1  # no bundle/centroids -> no event attribution
            counts = link_titles(cur, fn, narratives, window_days, incremental)
            n_titles += sum(counts.values())
            n_fns += 1
    conn.commit()
    return {
        "fns": n_fns,
        "events": n_events,
        "titles": n_titles,
        "skipped_events": n_skipped,
    }


def main() -> None:
    args = parse_args()
    conn = psycopg2.connect(**config.db_connect_kwargs(), cursor_factory=RealDictCursor)
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            fn = fetch_fn(cur, args.fn_id)
            print(f"FN: {fn['id']} ({fn['name_en']})")

            narratives = fetch_narratives(cur, args.fn_id)
            print(f"Narratives linked: {len(narratives)}")
            for n in narratives:
                pubs = len(n["publishers"] or [])
                framing = len(n["framing_keywords"] or [])
                print(f"  - {n['id']} pubs={pubs} framing={framing}")

            if fn.get("fn_type") == "theater":
                # Theaters have no event markers (events live on the atomic FNs
                # they group). Title attribution still happens via the theater's
                # narratives + bundle.
                print("\nfn_type=theater — skipping event_friction_nodes step.")
            else:
                try:
                    n_events = link_events(cur, fn, args.window_days)
                    print(f"\nevent_friction_nodes inserted: {n_events}")
                except FNConfigError as e:
                    raise SystemExit(str(e))

            counts = link_titles(cur, fn, narratives, args.window_days)
            print("title_narratives inserted:")
            for nid, c in counts.items():
                print(f"  - {nid}: {c}")

        conn.commit()
        print("\nCommitted.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
