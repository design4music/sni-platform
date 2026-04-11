"""
Phase 4.1: Event Family Assembly (mechanical, spine-based)

Groups clusters into event families by detecting the dominant signal (spine)
in each cluster's title_labels profile. No LLM calls.

Pipeline position: after Phase 4 clustering, before Phase 4.2 merge.

Usage:
    python pipeline/phase_4/assemble_families.py --ctm-id <uuid>
    python pipeline/phase_4/assemble_families.py --centroid AMERICAS-USA --track geo_security
    python pipeline/phase_4/assemble_families.py --centroid AMERICAS-USA --track geo_security --dry-run
    python pipeline/phase_4/assemble_families.py --ctm-id <uuid> --force
"""

import argparse
import math
import re
import sys
import uuid
from collections import Counter, defaultdict
from pathlib import Path

import psycopg2

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config

# --- Constants ---

# Spine priority by track (which entity type is most discriminating)
TRACK_ENTITY_PRIORITY = {
    "geo_security": ["place", "person", "org"],
    "geo_politics": ["person", "org", "place"],
    "geo_economy": ["org", "person", "place"],
    "geo_society": ["person", "org", "place"],
}

VAGUE_PLACES = frozenset(
    [
        "middle east",
        "gulf",
        "asia",
        "europe",
        "africa",
        "americas",
        "the west",
        "the east",
    ]
)

DEFINING_THRESHOLD = 0.35
UBIQUITY_THRESHOLD = 0.15

STOP_WORDS = frozenset(
    "the a an in of on for to and is are was were with from at by as its it be "
    "has had have that this or but not no new over after into about up out more "
    "says said will could would may amid us set than been also".split()
)


# --- Helpers ---


def tokenize(text):
    words = set(re.findall(r"[a-z][a-z0-9]+", (text or "").lower()))
    return words - STOP_WORDS


def dice(a, b):
    if not a or not b:
        return 0.0
    return 2 * len(a & b) / (len(a) + len(b))


# --- DB connection ---


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def get_ctm_info(conn, ctm_id=None, centroid=None, track=None):
    """Get CTM info by ID or by centroid+track (most recent unfrozen month)."""
    cur = conn.cursor()
    if ctm_id:
        cur.execute(
            "SELECT id, centroid_id, track, month, title_count "
            "FROM ctm WHERE id = %s",
            (ctm_id,),
        )
    else:
        cur.execute(
            "SELECT id, centroid_id, track, month, title_count "
            "FROM ctm WHERE centroid_id = %s AND track = %s "
            "ORDER BY month DESC LIMIT 1",
            (centroid, track),
        )
    row = cur.fetchone()
    cur.close()
    if not row:
        return None
    return {
        "id": row[0],
        "centroid_id": row[1],
        "track": row[2],
        "month": row[3],
        "title_count": row[4],
    }


# --- Step 1: Load clusters and aggregate title_labels ---


def load_clusters(cur, ctm_id):
    """Load all non-catchall visible clusters with their title_labels aggregated."""
    cur.execute(
        """SELECT e.id, e.source_batch_count, e.title, e.event_type,
                  e.bucket_key, e.tags
           FROM events_v3 e
           WHERE e.ctm_id = %s AND NOT e.is_catchall AND e.merged_into IS NULL
           ORDER BY e.source_batch_count DESC""",
        (ctm_id,),
    )

    clusters = {}
    for r in cur.fetchall():
        clusters[r[0]] = {
            "id": r[0],
            "src": r[1],
            "title": r[2] or "",
            "event_type": r[3],
            "bucket_key": r[4],
            "tags": set(r[5] or []),
            "words": tokenize(r[2]),
            "n_titles": 0,
            "max_importance": 0.0,
            "places": Counter(),
            "persons": Counter(),
            "orgs": Counter(),
            "subjects": Counter(),
            "actors": Counter(),
            "targets": Counter(),
            "action_classes": Counter(),
            "named_events": Counter(),
        }

    if not clusters:
        return clusters

    cluster_ids = list(clusters.keys())
    cur.execute(
        """SELECT et.event_id,
                  tl.importance_score,
                  tl.actor, tl.target, tl.subject, tl.action_class,
                  tl.places, tl.persons, tl.orgs, tl.named_events
           FROM event_v3_titles et
           JOIN title_labels tl ON tl.title_id = et.title_id
           WHERE et.event_id = ANY(%s::uuid[])""",
        ([str(cid) for cid in cluster_ids],),
    )

    for r in cur.fetchall():
        c = clusters.get(r[0])
        if not c:
            continue
        c["n_titles"] += 1
        imp = r[1] or 0.0
        if imp > c["max_importance"]:
            c["max_importance"] = imp
        if r[2]:
            c["actors"][r[2]] += 1
        if r[3]:
            c["targets"][r[3]] += 1
        if r[4]:
            c["subjects"][r[4]] += 1
        if r[5]:
            c["action_classes"][r[5]] += 1
        for p in r[6] or []:
            c["places"][p] += 1
        for p in r[7] or []:
            c["persons"][p] += 1
        for o in r[8] or []:
            c["orgs"][o] += 1
        for ne in r[9] or []:
            c["named_events"][ne] += 1

    # Approximate avg importance
    for c in clusters.values():
        if c["n_titles"] > 0:
            c["avg_importance"] = c["max_importance"] * 0.6

    return clusters


# --- Step 2: Detect ubiquitous signals ---


def detect_ubiquitous(clusters):
    """Find signals that appear in >15% of all titles across the CTM."""
    total_titles = sum(c["n_titles"] for c in clusters.values())
    if total_titles == 0:
        return set()

    threshold = total_titles * UBIQUITY_THRESHOLD

    person_totals = Counter()
    place_totals = Counter()
    org_totals = Counter()

    for c in clusters.values():
        for p, cnt in c["persons"].items():
            person_totals[p] += cnt
        for p, cnt in c["places"].items():
            place_totals[p] += cnt
        for o, cnt in c["orgs"].items():
            org_totals[o] += cnt

    ubiquitous = set()
    for p, cnt in person_totals.items():
        if cnt >= threshold:
            ubiquitous.add(("person", p))
    for p, cnt in place_totals.items():
        if cnt >= threshold:
            ubiquitous.add(("place", p))
    for o, cnt in org_totals.items():
        if cnt >= threshold:
            ubiquitous.add(("org", o))

    return ubiquitous


# --- Step 2b: Normalize place aliases ---


def normalize_places(clusters):
    """Merge place aliases where one name is a variant of another."""
    all_places = Counter()
    for c in clusters.values():
        for p, cnt in c["places"].items():
            all_places[p] += cnt

    # Case normalization
    case_map = {}
    by_lower = defaultdict(list)
    for p in all_places:
        by_lower[p.lower()].append(p)
    for lower, variants in by_lower.items():
        if len(variants) > 1:
            best = max(variants, key=lambda v: all_places[v])
            for v in variants:
                if v != best:
                    case_map[v] = best

    # Structural aliases
    suffixes = [
        " Island",
        " City",
        " Port",
        " Airport",
        " Strait",
        " Straits",
        " Air Base",
        " D.C.",
        " DC",
    ]
    struct_map = {}
    place_lower_set = {p.lower() for p in all_places}
    for p in all_places:
        for suffix in suffixes:
            if p.endswith(suffix):
                base = p[: -len(suffix)].strip()
                if base.lower() in place_lower_set:
                    struct_map[p] = base
                    break

    alias_map = {**case_map, **struct_map}
    if alias_map:
        print("  Place aliases: %s" % {k: v for k, v in sorted(alias_map.items())})

    for c in clusters.values():
        merged = Counter()
        for p, cnt in c["places"].items():
            canonical = alias_map.get(p, p)
            merged[canonical] += cnt
        c["places"] = merged


# --- Step 3: Assign spine per cluster ---


def _best_signal(counter, min_count, excluded):
    """Pick the most frequent non-excluded signal above min_count."""
    for signal, count in counter.most_common():
        if count < min_count:
            return None
        if signal.lower() in excluded or signal in excluded:
            continue
        return signal
    return None


def assign_spines(clusters, ubiquitous, track, cur=None):
    """Assign a spine to each cluster based on its signal profile."""
    entity_priority = TRACK_ENTITY_PRIORITY.get(track, ["place", "person", "org"])

    # Build set of country/region names from centroids
    country_names = set()
    if cur:
        cur.execute("SELECT id, label FROM centroids_v3 WHERE is_active")
        for row in cur.fetchall():
            country_names.add(row[1].lower())
            parts = row[0].split("-")
            if len(parts) >= 2:
                country_names.add(parts[-1].lower())

    country_names.update(
        [
            "spain",
            "france",
            "germany",
            "italy",
            "greece",
            "turkey",
            "japan",
            "india",
            "china",
            "russia",
            "brazil",
            "mexico",
            "canada",
            "australia",
            "romania",
            "poland",
            "norway",
            "sweden",
            "denmark",
            "finland",
            "pakistan",
            "afghanistan",
            "syria",
            "egypt",
            "libya",
            "morocco",
            "singapore",
            "vietnam",
            "philippines",
            "indonesia",
            "thailand",
            "colombia",
            "peru",
            "chile",
            "argentina",
            "nigeria",
            "kenya",
            "united states",
            "united kingdom",
            "south korea",
            "north korea",
            "saudi arabia",
            "united arab emirates",
        ]
    )

    for c in clusters.values():
        n = c["n_titles"]
        if n == 0:
            n = max(c["src"], 1)

        min_count = max(2, math.ceil(n * DEFINING_THRESHOLD))

        # 1. Named events
        best_ne = _best_signal(c["named_events"], min_count, set())
        if best_ne:
            c["spine_type"] = "named_event"
            c["spine_value"] = best_ne
            continue

        # 2-4. Entity types in track-specific priority
        place_excluded = {p for t, p in ubiquitous if t == "place"} | VAGUE_PLACES
        if c["bucket_key"]:
            bucket_lower = c["bucket_key"].lower().replace("-", " ")
            for place_name, place_count in list(c["places"].items()):
                pn = place_name.lower()
                if pn in bucket_lower or bucket_lower.endswith(pn):
                    continue
                if pn in country_names and n > 0 and place_count < n * 0.4:
                    place_excluded.add(pn)

        entity_sources = {
            "place": (c["places"], place_excluded),
            "person": (c["persons"], {p for t, p in ubiquitous if t == "person"}),
            "org": (c["orgs"], {p for t, p in ubiquitous if t == "org"}),
        }

        spine_found = False
        for etype in entity_priority:
            signals, excluded = entity_sources[etype]
            best = _best_signal(signals, min_count, excluded)
            if best:
                c["spine_type"] = etype
                c["spine_value"] = best
                spine_found = True
                break

        if spine_found:
            continue

        # 5. Subject as compound spine
        generic_subjects = {
            "BILATERAL_RELATIONS",
            "DEFENSE_POLICY",
            "MEDIA_PRESS",
            "EXECUTIVE_ACTION",
        }
        best_subj = _best_signal(c["subjects"], min_count, generic_subjects)
        prefix = c["bucket_key"] or c["event_type"] or "unknown"

        if best_subj:
            c["spine_type"] = "compound"
            c["spine_value"] = "%s:%s" % (prefix, best_subj)
            continue

        # 6. Bucket key alone
        if c["bucket_key"]:
            c["spine_type"] = "bucket"
            c["spine_value"] = c["bucket_key"]
            continue

        # 7. Event type alone (last resort)
        c["spine_type"] = "type"
        c["spine_value"] = c["event_type"] or "unknown"


# --- Step 4: Group into families ---


def build_families(clusters):
    """Group clusters by spine into proto-families."""
    spine_groups = defaultdict(list)
    for c in clusters.values():
        key = (c.get("spine_type", "none"), c.get("spine_value", "none"))
        spine_groups[key].append(c)

    families = []
    for (stype, svalue), members in spine_groups.items():
        members.sort(key=lambda c: -c["src"])
        total_src = sum(c["src"] for c in members)
        families.append(
            {
                "spine_type": stype,
                "spine_value": svalue,
                "clusters": members,
                "n_clusters": len(members),
                "total_src": total_src,
            }
        )

    families.sort(key=lambda f: -f["total_src"])

    # Within-family Dice merge
    for f in families:
        if f["n_clusters"] >= 2:
            f["clusters"] = _merge_within_family(f["clusters"])
            f["n_clusters"] = len(f["clusters"])

    # Split oversized families
    final_families = []
    for f in families:
        if f["n_clusters"] > 20 or (f["n_clusters"] > 15 and f["total_src"] > 500):
            if f["spine_type"] in ("compound", "bucket", "type"):
                sub = _split_by_action_class(f)
            else:
                sub = _split_by_subject(f)
            final_families.extend(sub)
        else:
            final_families.append(f)

    # Dissolve tiny families
    result = []
    for f in final_families:
        if f["n_clusters"] >= 2 and f["total_src"] < 10:
            for c in f["clusters"]:
                result.append(
                    {
                        "spine_type": f["spine_type"],
                        "spine_value": f["spine_value"],
                        "clusters": [c],
                        "n_clusters": 1,
                        "total_src": c["src"],
                    }
                )
        else:
            result.append(f)

    # Absorb standalones into families
    result = _absorb_standalones(result)
    result.sort(key=lambda f: -f["total_src"])
    return result


def _merge_within_family(members):
    """Merge near-duplicate clusters within a family (Dice >= 0.45)."""
    if len(members) < 2:
        return members

    kept = []
    absorbed = set()

    for c in members:
        if c["id"] in absorbed:
            continue
        for other in members:
            if other["id"] in absorbed or other["id"] == c["id"]:
                continue
            if dice(c["words"], other["words"]) >= 0.45:
                c["src"] += other["src"]
                c.setdefault("merged_members", []).append(other)
                absorbed.add(other["id"])
        kept.append(c)

    return kept


def _absorb_standalones(families):
    """Absorb standalone topics into multi-cluster families in the same bucket."""
    real = [f for f in families if f["n_clusters"] >= 2]
    solos = [f for f in families if f["n_clusters"] == 1]

    if not real or not solos:
        return families

    fam_words = []
    fam_buckets = []
    for f in real:
        words = set()
        buckets = set()
        for c in f["clusters"]:
            words.update(c["words"])
            if c["bucket_key"]:
                buckets.add(c["bucket_key"])
            if c["event_type"] == "domestic":
                buckets.add("DOMESTIC")
        fam_words.append(words)
        fam_buckets.append(buckets)

    absorbed_count = 0
    remaining_solos = []

    for solo in solos:
        c = solo["clusters"][0]
        solo_bucket = c["bucket_key"] or (
            "DOMESTIC" if c["event_type"] == "domestic" else None
        )
        if not solo_bucket or not c["words"]:
            remaining_solos.append(solo)
            continue

        best_score = 0.0
        best_idx = -1
        for i, f in enumerate(real):
            if solo_bucket not in fam_buckets[i]:
                continue
            if real[i]["n_clusters"] >= 25:
                continue

            stype = f["spine_type"]
            sval = f["spine_value"]
            if stype in ("place", "person", "org", "named_event"):
                spine_word = sval.lower().split("/")[0]
                if spine_word not in c["title"].lower():
                    continue

            shared = len(c["words"] & fam_words[i])
            if not c["words"]:
                continue
            score = shared / len(c["words"])
            if score > best_score:
                best_score = score
                best_idx = i

        if best_score >= 0.30 and best_idx >= 0:
            real[best_idx]["clusters"].append(c)
            real[best_idx]["n_clusters"] += 1
            real[best_idx]["total_src"] += c["src"]
            fam_words[best_idx].update(c["words"])
            absorbed_count += 1
        else:
            remaining_solos.append(solo)

    if absorbed_count:
        print("  Absorbed %d standalones into existing families" % absorbed_count)

    return real + remaining_solos


def _split_by_action_class(family):
    """Split an oversized family into sub-families by dominant action_class."""
    sub_groups = defaultdict(list)
    for c in family["clusters"]:
        top_ac = c["action_classes"].most_common(1)
        ac = top_ac[0][0] if top_ac else "OTHER"
        sub_groups[ac].append(c)

    sub_families = []
    for ac, members in sub_groups.items():
        members.sort(key=lambda c: -c["src"])
        total_src = sum(c["src"] for c in members)
        sub_families.append(
            {
                "spine_type": family["spine_type"],
                "spine_value": "%s/%s" % (family["spine_value"], ac),
                "clusters": members,
                "n_clusters": len(members),
                "total_src": total_src,
            }
        )
    return sub_families


def _split_by_subject(family):
    """Split an oversized entity-spine family by dominant subject."""
    sub_groups = defaultdict(list)
    for c in family["clusters"]:
        top_subj = c["subjects"].most_common(1)
        subj = top_subj[0][0] if top_subj else "OTHER"
        sub_groups[subj].append(c)

    if len(sub_groups) < 2:
        return [family]

    sub_families = []
    for subj, members in sub_groups.items():
        members.sort(key=lambda c: -c["src"])
        total_src = sum(c["src"] for c in members)
        sub_families.append(
            {
                "spine_type": family["spine_type"],
                "spine_value": "%s/%s" % (family["spine_value"], subj),
                "clusters": members,
                "n_clusters": len(members),
                "total_src": total_src,
            }
        )
    return sub_families


# --- Step 5: Priority tagging ---


def assign_priority(clusters):
    """Assign display priority A/B/C/D to each cluster."""
    for c in clusters.values():
        imp = c["max_importance"]
        src = c["src"]
        has_entity = bool(
            c["places"] or any(p for p in c["persons"] if p != "TRUMP") or c["orgs"]
        )

        if imp >= 0.5 or src >= 20:
            c["priority"] = "A"
        elif imp >= 0.3 or src >= 10:
            c["priority"] = "B"
        elif imp >= 0.15 and has_entity:
            c["priority"] = "C"
        else:
            c["priority"] = "D"


# --- DB Write (incremental) ---


def write_families(conn, ctm_id, families):
    """Write families to DB with incremental semantics.

    - Existing families matched by (ctm_id, spine_type, spine_value) are updated
    - New spines get new families
    - Families whose spine no longer exists are cleaned up
    - Cluster family_id links are always refreshed
    """
    cur = conn.cursor()

    # Load existing families for this CTM (only those with spine data)
    cur.execute(
        "SELECT id, spine_type, spine_value FROM event_families "
        "WHERE ctm_id = %s AND spine_type IS NOT NULL",
        (ctm_id,),
    )
    existing = {}
    for row in cur.fetchall():
        key = (row[1], row[2])
        existing[key] = row[0]

    # Remove legacy families without spine data (clear FK refs first)
    cur.execute(
        "UPDATE events_v3 SET family_id = NULL "
        "WHERE family_id IN (SELECT id FROM event_families "
        "  WHERE ctm_id = %s AND spine_type IS NULL)",
        (ctm_id,),
    )
    cur.execute(
        "DELETE FROM event_families WHERE ctm_id = %s AND spine_type IS NULL",
        (ctm_id,),
    )
    legacy_deleted = cur.rowcount
    if legacy_deleted:
        print("  Removed %d legacy families (no spine data)" % legacy_deleted)

    # Clear all family_id links for this CTM (will be re-set below)
    cur.execute(
        "UPDATE events_v3 SET family_id = NULL WHERE ctm_id = %s",
        (ctm_id,),
    )

    real_families = [f for f in families if f["n_clusters"] >= 2]
    new_spine_keys = set()
    written = 0
    updated = 0

    for f in real_families:
        spine_key = (f["spine_type"], f["spine_value"])
        new_spine_keys.add(spine_key)
        fam_src = sum(c["src"] for c in f["clusters"])

        if spine_key in existing:
            # Update existing family
            fam_id = existing[spine_key]
            cur.execute(
                """UPDATE event_families
                   SET cluster_count = %s, source_count = %s,
                       domain = %s, updated_at = NOW()
                   WHERE id = %s""",
                (f["n_clusters"], fam_src, f["spine_type"], fam_id),
            )
            updated += 1
        else:
            # Create new family
            fam_id = str(uuid.uuid4())
            cur.execute(
                """INSERT INTO event_families
                   (id, ctm_id, title, domain, cluster_count, source_count,
                    spine_type, spine_value, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())""",
                (
                    fam_id,
                    ctm_id,
                    f["spine_value"],
                    f["spine_type"],
                    f["n_clusters"],
                    fam_src,
                    f["spine_type"],
                    f["spine_value"],
                ),
            )
            written += 1

        # Link clusters to family
        cluster_ids = [str(c["id"]) for c in f["clusters"]]
        cur.execute(
            "UPDATE events_v3 SET family_id = %s WHERE id = ANY(%s::uuid[])",
            (fam_id, cluster_ids),
        )

        # Also link within-family merged members
        for c in f["clusters"]:
            for merged in c.get("merged_members", []):
                cur.execute(
                    "UPDATE events_v3 SET merged_into = %s, family_id = %s WHERE id = %s",
                    (str(c["id"]), fam_id, str(merged["id"])),
                )

    # Clean up orphaned families (spine no longer exists)
    orphaned = [fid for key, fid in existing.items() if key not in new_spine_keys]
    if orphaned:
        orphan_ids = [str(fid) for fid in orphaned]
        cur.execute(
            "UPDATE events_v3 SET family_id = NULL WHERE family_id = ANY(%s::uuid[])",
            (orphan_ids,),
        )
        cur.execute(
            "DELETE FROM event_families WHERE id = ANY(%s::uuid[])",
            (orphan_ids,),
        )
        print("  Removed %d orphaned families" % len(orphaned))

    conn.commit()
    cur.close()

    total_linked = sum(f["n_clusters"] for f in real_families)
    print(
        "  Wrote %d new + %d updated families (%d clusters linked)"
        % (written, updated, total_linked)
    )


# --- Main entry points ---


def assemble_families_for_ctm(conn, ctm_id, track):
    """Core assembly logic. Returns (families, clusters) for reporting."""
    cur = conn.cursor()

    # Load and aggregate
    clusters = load_clusters(cur, ctm_id)
    if not clusters:
        print("  No visible clusters")
        cur.close()
        return [], {}

    with_labels = sum(1 for c in clusters.values() if c["n_titles"] > 0)
    print("  %d clusters (%d with labels)" % (len(clusters), with_labels))

    # Ubiquity detection
    ubiquitous = detect_ubiquitous(clusters)
    for utype, uval in sorted(ubiquitous):
        print("  Ubiquitous: %s:%s" % (utype, uval))

    # Normalize places
    normalize_places(clusters)

    # Assign spines
    assign_spines(clusters, ubiquitous, track, cur)

    # Priority
    assign_priority(clusters)

    # Build families
    families = build_families(clusters)

    cur.close()
    return families, clusters


def print_report(families, clusters):
    """Print summary report."""
    if not clusters:
        return

    real_families = [f for f in families if f["n_clusters"] >= 2]
    standalones = [f for f in families if f["n_clusters"] == 1]

    # Spine distribution
    spine_dist = Counter()
    for c in clusters.values():
        spine_dist[c.get("spine_type", "none")] += 1

    print(
        "\n  Spine types: %s"
        % ", ".join("%s=%d" % (k, v) for k, v in spine_dist.most_common())
    )

    # Family summary
    in_families = sum(f["n_clusters"] for f in real_families)
    print(
        "  %d families (%d clusters), %d standalone"
        % (
            len(real_families),
            in_families,
            len(standalones),
        )
    )

    for f in real_families[:10]:
        print(
            "    [%2d clusters, %5d src] (%s) %s"
            % (
                f["n_clusters"],
                f["total_src"],
                f["spine_type"],
                f["spine_value"],
            )
        )
    if len(real_families) > 10:
        print("    ... +%d more" % (len(real_families) - 10))

    # Checks
    mega = [f for f in real_families if f["n_clusters"] > 15]
    if mega:
        print("  WARNING: %d families >15 clusters" % len(mega))
    else:
        print("  OK: no mega-families")


def process_ctm(ctm_id=None, centroid=None, track=None, dry_run=False, force=False):
    """
    Main entry point. Compatible with daemon pattern.
    Returns number of families written, or 0 if skipped/dry-run.
    """
    conn = get_connection()
    try:
        ctm = get_ctm_info(conn, ctm_id, centroid, track)
        if not ctm:
            print("CTM not found")
            return 0

        print("=== Family Assembly %s ===" % ("(DRY RUN)" if dry_run else ""))
        print(
            "  %s / %s / %s (%d titles)"
            % (
                ctm["centroid_id"],
                ctm["track"],
                ctm["month"],
                ctm["title_count"],
            )
        )

        # Incremental guard: skip if no new clusters since last assembly
        if not force and not dry_run:
            cur = conn.cursor()
            cur.execute(
                """SELECT COUNT(*) FROM events_v3
                   WHERE ctm_id = %s AND NOT is_catchall AND merged_into IS NULL""",
                (ctm["id"],),
            )
            current_count = cur.fetchone()[0]

            cur.execute(
                """SELECT SUM(cluster_count) FROM event_families WHERE ctm_id = %s""",
                (ctm["id"],),
            )
            row = cur.fetchone()
            previous_count = row[0] if row[0] else 0
            cur.close()

            # Also check if there are clusters without family_id
            cur2 = conn.cursor()
            cur2.execute(
                """SELECT COUNT(*) FROM events_v3
                   WHERE ctm_id = %s AND NOT is_catchall AND merged_into IS NULL
                     AND family_id IS NULL""",
                (ctm["id"],),
            )
            unassigned = cur2.fetchone()[0]
            cur2.close()

            if current_count == previous_count and unassigned == 0:
                print(
                    "  Skipped: no changes (%d clusters, all assigned)" % current_count
                )
                return 0

        families, clusters = assemble_families_for_ctm(conn, ctm["id"], ctm["track"])
        print_report(families, clusters)

        if dry_run:
            return 0

        write_families(conn, ctm["id"], families)

        real_count = len([f for f in families if f["n_clusters"] >= 2])
        return real_count
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Phase 4.1: Event Family Assembly (mechanical, spine-based)"
    )
    parser.add_argument("--ctm-id", type=str, help="CTM ID to process")
    parser.add_argument("--centroid", type=str, help="Centroid ID")
    parser.add_argument("--track", type=str, help="Track name")
    parser.add_argument(
        "--dry-run", action="store_true", help="Report only, no DB writes"
    )
    parser.add_argument("--force", action="store_true", help="Skip incremental guard")
    args = parser.parse_args()

    if not args.ctm_id and not (args.centroid and args.track):
        print("ERROR: provide --ctm-id or --centroid + --track")
        sys.exit(1)

    result = process_ctm(
        ctm_id=args.ctm_id,
        centroid=args.centroid,
        track=args.track,
        dry_run=args.dry_run,
        force=args.force,
    )
    print("\nDone. %d families." % result)
