"""Generate titles and descriptions for topics + assign first-headline for small topics."""

import subprocess
import sys
from collections import Counter

import psycopg2

sys.path.insert(0, ".")
sys.stdout.reconfigure(errors="replace")

conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/sni_v2")
cur = conn.cursor()

DRY_RUN = "--dry-run" in sys.argv

# --- Dynamic thresholds by centroid volume ---
# Count strategic titles per centroid to determine tier
cur.execute(
    """
    SELECT c.id,
           count(DISTINCT t.id) as strategic
    FROM centroids_v3 c
    JOIN titles_v3 t ON c.id = ANY(t.centroid_ids)
    JOIN title_labels tl ON tl.title_id = t.id
    WHERE t.pubdate_utc >= '2026-03-01' AND t.pubdate_utc < '2026-04-01'
    AND t.processing_status = 'assigned'
    AND tl.sector IS NOT NULL AND tl.sector != 'NON_STRATEGIC'
    GROUP BY c.id
"""
)
centroid_volume = {r[0]: r[1] for r in cur.fetchall()}


def get_min_sources(centroid_id):
    vol = centroid_volume.get(centroid_id, 0)
    if vol >= 10000:
        return 10  # mega
    if vol >= 3000:
        return 5  # large
    if vol >= 1000:
        return 3  # medium
    return 2  # small


# --- Step 1: Assign first-headline titles for ALL events without titles ---
cur.execute(
    """
    SELECT e.id, e.ctm_id,
           (SELECT t.title_display FROM event_v3_titles et
            JOIN titles_v3 t ON t.id = et.title_id
            WHERE et.event_id = e.id
            ORDER BY t.pubdate_utc DESC LIMIT 1) as first_title
    FROM events_v3 e
    JOIN ctm ON e.ctm_id = ctm.id
    WHERE ctm.month = '2026-03-01'
    AND e.merged_into IS NULL
    AND e.title IS NULL
"""
)
no_title = cur.fetchall()
print("Events without title: %d" % len(no_title))

if not DRY_RUN:
    for eid, ctm_id, first_title in no_title:
        if first_title:
            cur.execute(
                "UPDATE events_v3 SET title = %s, updated_at = NOW() WHERE id = %s",
                (first_title[:200], eid),
            )
    conn.commit()
    print("Assigned first-headline titles to all events.")

# --- Step 2: Generate LLM titles+descriptions for big topics ---
# Get CTMs with their centroid for threshold lookup
cur.execute(
    """
    SELECT ctm.id, ctm.centroid_id, ctm.track FROM ctm
    WHERE ctm.month = '2026-03-01'
"""
)
ctm_centroids = {r[0]: (r[1], r[2]) for r in cur.fetchall()}

# Find events above threshold that need LLM prose
events_for_llm = []
cur.execute(
    """
    SELECT e.id, e.ctm_id, e.source_batch_count
    FROM events_v3 e
    JOIN ctm ON e.ctm_id = ctm.id
    WHERE ctm.month = '2026-03-01'
    AND e.merged_into IS NULL AND NOT e.is_catchall
    AND e.source_batch_count >= 2
"""
)
for eid, ctm_id, src in cur.fetchall():
    centroid_id = ctm_centroids.get(ctm_id, ("", ""))[0]
    min_src = get_min_sources(centroid_id)
    if src >= min_src:
        events_for_llm.append((eid, ctm_id, src, centroid_id))

print("Events qualifying for LLM prose: %d" % len(events_for_llm))

# Tier breakdown


tier_counts = Counter()
for _, _, src, cid in events_for_llm:
    vol = centroid_volume.get(cid, 0)
    if vol >= 10000:
        tier_counts["mega (>=10 src)"] += 1
    elif vol >= 3000:
        tier_counts["large (>=5 src)"] += 1
    elif vol >= 1000:
        tier_counts["medium (>=3 src)"] += 1
    else:
        tier_counts["small (>=2 src)"] += 1
for tier, count in sorted(tier_counts.items()):
    print("  %s: %d events" % (tier, count))

if DRY_RUN:
    print("\nDRY RUN. Use without --dry-run to generate prose.")
    conn.close()
    sys.exit(0)

# Run Phase 4.5a for events above threshold
# 4.5a processes events where title IS NULL, so we need to:
# 1. Set first-headline titles on ALL events (done above)
# 2. Clear titles on events above threshold so 4.5a picks them up
print("\nClearing titles on %d events for LLM regeneration..." % len(events_for_llm))
llm_eids = [e[0] for e in events_for_llm]
batch_size = 500
for i in range(0, len(llm_eids), batch_size):
    batch = llm_eids[i : i + batch_size]
    cur.execute(
        "UPDATE events_v3 SET title = NULL, summary = NULL WHERE id = ANY(%s::uuid[])",
        (batch,),
    )
conn.commit()
print("Cleared. Phase 4.5a will generate LLM prose for these.")

# Now run 4.5a - it picks up events with NULL title

print("\nRunning Phase 4.5a...")
result = subprocess.run(
    [
        sys.executable,
        "-m",
        "pipeline.phase_4.generate_event_summaries_4_5a",
        "--max-events",
        str(len(events_for_llm) + 100),
    ],
    text=True,
    errors="replace",
    timeout=7200,
)
print("Phase 4.5a exit code: %d" % result.returncode)
conn.close()
