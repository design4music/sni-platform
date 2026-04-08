"""Test detailed giant prompt for USA security family assembly."""

import json
import re
import sys

import httpx
import psycopg2

sys.path.insert(0, ".")
sys.stdout.reconfigure(errors="replace")

from core.config import config  # noqa: E402

conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/sni_v2")
cur = conn.cursor()

cur.execute(
    "SELECT id FROM ctm WHERE centroid_id = 'AMERICAS-USA' "
    "AND track = 'geo_security' AND month = '2026-03-01'"
)
ctm_id = cur.fetchone()[0]

cur.execute(
    """
    SELECT e.id, e.source_batch_count, e.title,
           min(t.pubdate_utc)::date as first, max(t.pubdate_utc)::date as last
    FROM events_v3 e
    JOIN event_v3_titles et ON et.event_id = e.id
    JOIN titles_v3 t ON t.id = et.title_id
    WHERE e.ctm_id = %s AND NOT e.is_catchall AND e.merged_into IS NULL
    GROUP BY e.id, e.source_batch_count, e.title
    ORDER BY e.source_batch_count DESC
""",
    (ctm_id,),
)

clusters = []
for r in cur.fetchall():
    clusters.append(
        {"src": r[1], "title": r[2] or "Untitled", "first": r[3], "last": r[4]}
    )

top_n = 200
send = clusters[:top_n]

lines = []
for i, c in enumerate(send, 1):
    lines.append("%d. [%d src, %s] %s" % (i, c["src"], c["first"], c["title"][:80]))

GIANT_SYSTEM = (
    "You are an intelligence analyst organizing a large set of news clusters into "
    "EVENT FAMILIES for a monthly strategic briefing.\n\n"
    "THREE LEVELS OF GROUPING (you work at level 2):\n\n"
    "Level 1 (above you): THEATERS -- major geopolitical friction zones. A war, a "
    "standoff, a crisis. Multiple countries involved. You do NOT create these -- "
    "but you should be aware that your families will later be grouped into theaters. "
    "So families about the same theater should be distinguishable sub-stories, not "
    "duplicates of the theater itself.\n\n"
    "Level 2 (YOUR JOB): EVENT FAMILIES -- the spine of a specific developing story. "
    "What makes a family:\n"
    "- It has a CORE IDENTITY: a specific place, operation, incident, or decision "
    "that is the spine. Everything in the family connects to that spine.\n"
    "- A blockade of a vital waterway is a family. Strikes on a specific target are "
    "a family. A political scandal is a family. A deployment decision is a family.\n"
    "- The family can span multiple domains: naval, air, diplomatic, economic actions "
    "all related to the same spine belong together.\n"
    "- The family unfolds over days or weeks. Same spine, different days = same family.\n"
    "- BUT: different spines in the same theater = DIFFERENT families. Strikes on "
    "City A and strikes on Island B are different families even if same war.\n\n"
    "Level 3 (below you): TOPICS -- mechanically clustered headlines. These are your "
    "input. Many topics are fragments of the same family. Your job is to recognize "
    "which topics share a spine and group them.\n\n"
    "HOW TO IDENTIFY THE SPINE:\n"
    "Ask: what is the ONE thing a reader would remember about this story?\n"
    "- A specific geographic chokepoint being blocked\n"
    "- A specific leader being killed or making a decision\n"
    "- A specific military asset being destroyed or deployed\n"
    "- A specific policy debate in government\n"
    "- A specific domestic incident (attack, scandal, protest)\n"
    "If two clusters share the same spine, they are ONE family.\n"
    "If they have different spines but same theater, they are DIFFERENT families.\n\n"
    "DOMESTIC vs INTERNATIONAL:\n"
    "Domestic stories (immigration enforcement, domestic terrorism, political scandals) "
    "are separate from international theaters. Each domestic story with its own spine "
    "is its own family.\n\n"
    "EXPECTED OUTPUT: 30-60 families for a high-volume CTM.\n\n"
    "RULES:\n"
    "- Every cluster belongs to exactly one family. No orphans.\n"
    "- Small clusters (1-3 sources) are fragments -- absorb into nearest matching family.\n"
    "- Do NOT create a catch-all 'miscellaneous' family. Find the right home for every cluster.\n"
    "- Do NOT merge different spines into mega-families.\n\n"
    'Return JSON: {"families": [{"title": "5-15 word title naming the spine", '
    '"ids": [1,3,7], "summary": "2-3 sentences covering the full story arc"}]}'
)

print("USA security: %d clusters sent" % len(send))
print("Calling LLM...")

resp = httpx.post(
    config.deepseek_api_url + "/chat/completions",
    headers={"Authorization": "Bearer " + config.deepseek_api_key},
    json={
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": GIANT_SYSTEM},
            {"role": "user", "content": "\n".join(lines)},
        ],
        "temperature": 0.1,
        "max_tokens": 8000,
    },
    timeout=180,
)

text = resp.json()["choices"][0]["message"]["content"].strip()
result = None
try:
    result = json.loads(text)
except Exception:
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            result = json.loads(m.group(0))
        except Exception:
            pass

if result and "families" in result:
    families = result["families"]
    assigned = set()
    for f in families:
        assigned.update(f.get("ids", []))
    orphans = top_n - len(assigned)

    print()
    print(
        "=== %d CLUSTERS -> %d FAMILIES (orphans: %d) ==="
        % (top_n, len(families), orphans)
    )
    print()

    for f in sorted(
        families,
        key=lambda f: -sum(send[i - 1]["src"] for i in f["ids"] if i <= len(send)),
    ):
        ids = f["ids"]
        src = sum(send[i - 1]["src"] for i in ids if i <= len(send))
        print("[%3d clusters, %4d src] %s" % (len(ids), src, f["title"]))
        if f.get("summary"):
            print("  %s" % f["summary"][:140])
        print()
else:
    print("Failed")
    print(text[:500])

conn.close()
