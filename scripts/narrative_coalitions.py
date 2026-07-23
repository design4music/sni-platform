"""Resolve a narrative's coalition from its publisher bloc.

A coalition is a named set of ISO country codes (db/registry/coalitions.yaml).
A narrative's coalition is MEASURED, not assigned: its `publishers[]` resolve to
countries via `feeds.country_code`, and the countries resolve to coalitions.

Deliberately NOT derived from `narratives_v2.actor_centroids` -- that field says
who the dispute is about, not who is speaking, and it is identical on both sides
of 25% of opposing narrative pairs.

Publisher names in `narratives_v2.publishers` do not always match `feeds.name`
exactly (`tass.com` vs `TASS`, `WSJ`, `Bloomberg.com`), so matching is done on a
normalized key against both `feeds.name` and `feeds.source_domain`. That takes
unresolved narrative-publisher pairs from 9% to ~5%. The remainder are real
outlets absent from `feeds` -- they are reported, never hand-mapped (Rule 5).
"""

from __future__ import annotations

import collections
import re
from pathlib import Path

import yaml

REGISTRY = Path(__file__).parent.parent / "db" / "registry" / "coalitions.yaml"
# A coalition must hold this share of a narrative's resolved publishers to be
# called its primary. Below it the narrative is reported as `mixed`.
PRIMARY_SHARE = 0.45
# A second coalition at or above this share is reported alongside the primary.
SECONDARY_SHARE = 0.25


def _norm(s: str | None) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"^(the|le|la|el)\s+", "", s)
    s = re.sub(r"\.(com|ru|au|co\.uk|net|org|de|fr|cn)$", "", s)
    s = re.sub(r"\s*\((en|de|uk|eng)\)$", "", s)
    return re.sub(r"[^a-z0-9]", "", s)


def load_registry() -> tuple[dict[str, str], dict[str, str]]:
    """(iso code -> coalition id, coalition id -> parent id)."""
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    iso2c, parent = {}, {}
    for c in data["coalitions"]:
        for iso in c["iso_codes"]:
            iso2c[iso] = c["id"]
        if c.get("parent"):
            parent[c["id"]] = c["parent"]
    return iso2c, parent


DOMESTIC_FN_SQL = """
    SELECT f.id, c.iso_codes[1] AS iso
      FROM friction_nodes f
      JOIN centroids_v3 c ON c.id = f.primary_target
     WHERE f.is_active
       AND f.primary_target = ANY(f.centroid_ids)
       AND cardinality(f.centroid_ids) = 1
       AND cardinality(c.iso_codes) = 1
"""


def domestic_fns(cur) -> dict[str, str]:
    """fn_id -> home ISO code, for friction nodes whose dispute is INTERNAL.

    The test is `primary_target` sitting inside the FN's own `centroid_ids`:
    `us_interior_immigration_enforcement` has terrain USA and target USA, while
    `us_china_ai_primacy` has terrain USA and target China. `friction_nodes.scope`
    does not answer this (152 rows say 'regional', 5 say 'global').

    Why it matters: on a domestic node the publisher bloc is dominated by FOREIGN
    outlets covering someone else's internal fight. `usdom_ice_due_process` --
    the American mainstream position -- carries 77 publishers of which only 7 are
    American and 33 European, so a plain publisher-majority resolves it to
    `west_eu`. Restricting to home-country publishers gives `west_us`, correctly.
    """
    cur.execute(DOMESTIC_FN_SQL)
    return {r["id"]: r["iso"] for r in cur.fetchall()}


def publisher_countries(cur) -> dict[str, str]:
    """normalized publisher key -> iso country code."""
    cur.execute(
        "SELECT name, source_domain, country_code FROM feeds "
        "WHERE country_code IS NOT NULL"
    )
    out: dict[str, str] = {}
    for f in cur.fetchall():
        out.setdefault(_norm(f["name"]), f["country_code"])
        if f["source_domain"]:
            out.setdefault(_norm(f["source_domain"]), f["country_code"])
    return out


def resolve(
    rows: list[dict],
    pub2country: dict,
    iso2coalition: dict,
    parents: dict,
    fn_home: dict | None = None,
) -> dict:
    """rows need: id, publishers (and fn_id if fn_home is given).

    Most specific coalition wins; if none holds PRIMARY_SHARE, the publishers
    are re-tallied at parent level and the parent is used when it does. Only
    then is a narrative called `mixed`.

    On a domestic friction node (see `domestic_fns`) the tally is restricted to
    home-country publishers, so the narrative is attributed to whoever is having
    the argument rather than to whoever is reporting on it. A narrative on a
    domestic node with NO home-country publishers keeps the global tally -- that
    is the external framing of someone else's internal affairs, and naming the
    foreign bloc there is the correct answer, not a fallback.
    """
    fn_home = fn_home or {}
    out = {}
    for r in rows:
        pubs = r.get("publishers") or []
        home = fn_home.get(r.get("fn_id"))
        home_restricted = False
        if home:
            local = [p for p in pubs if pub2country.get(_norm(p)) == home]
            if local:
                pubs, home_restricted = local, True
        counts: collections.Counter = collections.Counter()
        unresolved = 0
        for p in pubs:
            iso = pub2country.get(_norm(p))
            coalition = iso2coalition.get(iso) if iso else None
            if coalition:
                counts[coalition] += 1
            else:
                unresolved += 1
        total = sum(counts.values())
        ranked = counts.most_common()
        primary, primary_share, level = None, 0.0, None
        secondary: list[str] = []
        if total:
            top, n = ranked[0]
            if n / total >= PRIMARY_SHARE:
                primary, primary_share, level = top, n / total, "specific"
            else:
                rolled: collections.Counter = collections.Counter()
                for c, m in counts.items():
                    rolled[parents.get(c, c)] += m
                ptop, pn = rolled.most_common(1)[0]
                if pn / total >= PRIMARY_SHARE:
                    primary, primary_share, level = ptop, pn / total, "parent"
                else:
                    primary, primary_share, level = "mixed", n / total, "mixed"
            secondary = [c for c, m in ranked[1:] if m / total >= SECONDARY_SHARE]
        out[r["id"]] = {
            "coalition": primary,
            "scope": "domestic" if home_restricted else "global",
            "share": round(primary_share, 2),
            "level": level,
            "secondary": secondary,
            "resolved_publishers": total,
            "unresolved_publishers": unresolved,
            "breakdown": dict(ranked),
        }
    return out
