"""
Build cross-centroid epics from tag co-occurrence.

Detects bridge tags spanning multiple centroids, clusters them via
Jaccard similarity on event sets, filters with LLM, generates
titles/summaries, and stores in the database.

Usage:
    python -m pipeline.epics.build_epics                    # latest month
    python -m pipeline.epics.build_epics --month 2025-01    # specific month
    python -m pipeline.epics.build_epics --dry-run           # preview only
    python -m pipeline.epics.build_epics --min-centroids 3   # tuning
"""

import argparse
import json
import re
from collections import defaultdict

import httpx
import psycopg2

from core.config import config

# First-class signal prefixes: specific entities that can anchor an epic.
# topic: tags (talks, sanctions, trade) are too generic to define a story.
SIGNAL_PREFIXES = ("org:", "place:", "person:")

# Tags that appear in too many unrelated stories to be useful anchors.
UBIQUITOUS_TAGS = {
    "person:trump",
}


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


# --- Step 1: Find bridge tags for a month ---

BRIDGE_QUERY = """
WITH event_tags AS (
    SELECT e.id AS event_id, unnest(e.tags) AS tag, c.centroid_id,
           e.source_batch_count
    FROM events_v3 e
    JOIN ctm c ON e.ctm_id = c.id
    WHERE c.month = %s AND e.tags IS NOT NULL
      AND e.source_batch_count >= %s
)
SELECT tag, count(DISTINCT centroid_id) AS spread,
       count(*) AS event_count, sum(source_batch_count) AS total_sources
FROM event_tags
GROUP BY tag
HAVING count(DISTINCT centroid_id) >= %s
ORDER BY spread DESC, total_sources DESC
"""


def find_bridge_tags(conn, month, min_sources=5, min_centroids=8):
    cur = conn.cursor()
    cur.execute(BRIDGE_QUERY, (month, min_sources, min_centroids))
    rows = cur.fetchall()
    results = []
    for tag, spread, count, sources in rows:
        if not tag.startswith(SIGNAL_PREFIXES):
            continue
        if tag in UBIQUITOUS_TAGS:
            continue
        results.append((tag, spread, count, sources))
    return results


# --- Step 2: Build event sets per tag and Jaccard graph ---

MONTH_EVENTS_QUERY = """
SELECT e.id, e.tags
FROM events_v3 e
JOIN ctm c ON e.ctm_id = c.id
WHERE c.month = %s AND e.tags IS NOT NULL AND e.source_batch_count >= 3
"""


def build_tag_event_sets(events, bridge_tag_set):
    """Map each bridge tag to the set of event IDs it appears in."""
    tag_events = defaultdict(set)
    for event_id, tags in events:
        for tag in tags:
            if tag in bridge_tag_set:
                tag_events[tag].add(event_id)
    return tag_events


def build_jaccard_graph(tag_events, min_jaccard=0.15):
    """Build edges between tags using Jaccard similarity on event sets."""
    tags = list(tag_events.keys())
    edges = {}
    for i in range(len(tags)):
        for j in range(i + 1, len(tags)):
            a_set = tag_events[tags[i]]
            b_set = tag_events[tags[j]]
            intersection = len(a_set & b_set)
            union = len(a_set | b_set)
            if union == 0:
                continue
            jaccard = intersection / union
            if jaccard >= min_jaccard:
                edges[(tags[i], tags[j])] = jaccard
    return edges


# --- Step 3: Find connected components via BFS ---


def find_components(edges, all_tags):
    """BFS on Jaccard edges. Tags with no edges become single-tag epics."""
    adj = defaultdict(set)
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)

    visited = set()
    components = []

    # First: connected components from edges
    for node in adj:
        if node in visited:
            continue
        queue = [node]
        component = set()
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            component.add(current)
            for neighbor in adj[current]:
                if neighbor not in visited:
                    queue.append(neighbor)
        components.append(sorted(component))

    # Second: single-tag epics for high-spread tags not in any component
    for tag in all_tags:
        if tag not in visited:
            components.append([tag])

    return components


# --- Step 4: Pull events per component ---

COMPONENT_EVENTS_QUERY = """
SELECT e.id, e.title, e.summary, e.tags, e.source_batch_count, e.date,
       c.centroid_id, c.track
FROM events_v3 e
JOIN ctm c ON e.ctm_id = c.id
WHERE c.month = %s AND e.tags && %s AND e.source_batch_count >= 3
ORDER BY e.source_batch_count DESC
"""


def get_component_events(conn, month, anchor_tags):
    cur = conn.cursor()
    cur.execute(COMPONENT_EVENTS_QUERY, (month, anchor_tags))
    return cur.fetchall()


# --- Step 5: LLM filter ---

BATCH_SIZE = 50


def _llm_filter_batch(tag_str, batch, start_num):
    """Filter a single batch of events. Returns set of global event numbers to exclude."""
    lines = []
    for i, ev in enumerate(batch, 1):
        eid, title, summary, tags, src, date, centroid, track = ev
        lines.append("%d. [%s | %s] %s" % (i, centroid, track, title))

    event_list = "\n".join(lines)

    prompt = (
        "You are filtering events for a cross-centroid news epic.\n\n"
        "The anchor signals are: %s\n"
        "Below are %d events that share these tags. Some genuinely belong "
        "to the epic (they are about the same geopolitical development). "
        "Others merely mention the keywords in passing.\n\n"
        "EVENTS:\n%s\n\n"
        "For each event, respond with ONLY a JSON array of objects:\n"
        '[{"n": 1, "keep": true}, {"n": 2, "keep": false}, ...]\n\n'
        "Rules:\n"
        "- keep=true if the event is primarily about this story\n"
        "- keep=true if the event covers a direct consequence or reaction\n"
        "- keep=false if the event mentions the topic in passing\n"
        "- keep=false if the event is a roundup where this is one of many items\n\n"
        "Return ONLY the JSON array, no other text."
    ) % (tag_str, len(batch), event_list)

    headers = {
        "Authorization": "Bearer %s" % config.deepseek_api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.llm_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 2000,
    }

    resp = httpx.post(
        "%s/chat/completions" % config.deepseek_api_url,
        headers=headers,
        json=payload,
        timeout=90,
    )

    if resp.status_code != 200:
        print(
            "    batch %d-%d: ERROR %d"
            % (start_num, start_num + len(batch) - 1, resp.status_code)
        )
        return set(), 0, 0

    data = resp.json()
    content = data["choices"][0]["message"]["content"].strip()
    usage = data.get("usage", {})

    # Strip markdown fences if present
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        content = content.rsplit("```", 1)[0]

    try:
        decisions = json.loads(content)
    except json.JSONDecodeError:
        print(
            "    batch %d-%d: parse error, retrying..."
            % (start_num, start_num + len(batch) - 1)
        )
        return None, 0, 0  # signal retry

    # Map local batch numbers back to global event numbers
    exclude = set()
    for d in decisions:
        if not d.get("keep", True):
            global_num = start_num + d["n"] - 1
            exclude.add(global_num)

    tok_in = usage.get("prompt_tokens", 0)
    tok_out = usage.get("completion_tokens", 0)
    return exclude, tok_in, tok_out


def llm_filter(anchor_tags, events):
    """Ask DeepSeek to classify which events belong to this epic."""
    tag_str = ", ".join(anchor_tags)
    total = len(events)
    print(
        "  LLM filter on %d events (%d batches)..."
        % (total, (total + BATCH_SIZE - 1) // BATCH_SIZE)
    )

    all_exclude = set()
    total_tok_in = 0
    total_tok_out = 0

    for offset in range(0, total, BATCH_SIZE):
        batch = events[offset : offset + BATCH_SIZE]
        start_num = offset + 1

        # Try up to 2 times per batch
        for attempt in range(2):
            result, tok_in, tok_out = _llm_filter_batch(tag_str, batch, start_num)
            total_tok_in += tok_in
            total_tok_out += tok_out
            if result is not None:
                all_exclude |= result
                break
        else:
            print(
                "    batch %d-%d: failed after retry, keeping all"
                % (start_num, start_num + len(batch) - 1)
            )

    filtered = [ev for i, ev in enumerate(events, 1) if i not in all_exclude]
    print(
        "  LLM: %d keep, %d exclude (tokens: %d in, %d out)"
        % (len(filtered), len(all_exclude), total_tok_in, total_tok_out)
    )
    return filtered


# --- Step 6: Generate title + summary ---


def generate_title_summary(anchor_tags, events):
    """Generate a headline and 2-3 sentence summary for the epic."""
    lines = []
    for ev in events[:30]:
        eid, title, summary, tags, src, date, centroid, track = ev
        lines.append("- [%s] %s" % (centroid, title))

    event_list = "\n".join(lines)
    tag_str = ", ".join(anchor_tags)

    prompt = (
        "You are naming a cross-centroid news story that appeared in many "
        "countries simultaneously.\n\n"
        "Anchor tags: %s\n"
        "Top events:\n%s\n\n"
        "Respond with exactly two lines:\n"
        "TITLE: <5-12 word headline for this story>\n"
        "SUMMARY: <2-3 sentence factual summary of the story>\n\n"
        "Be concise and factual. No editorializing."
    ) % (tag_str, event_list)

    headers = {
        "Authorization": "Bearer %s" % config.deepseek_api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.llm_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 300,
    }

    resp = httpx.post(
        "%s/chat/completions" % config.deepseek_api_url,
        headers=headers,
        json=payload,
        timeout=90,
    )

    if resp.status_code != 200:
        print("  ERROR: title/summary LLM returned %d" % resp.status_code)
        return None, None

    data = resp.json()
    content = data["choices"][0]["message"]["content"].strip()

    title = None
    summary = None
    for line in content.split("\n"):
        line = line.strip()
        if line.upper().startswith("TITLE:"):
            title = line[6:].strip().strip('"')
        elif line.upper().startswith("SUMMARY:"):
            summary = line[8:].strip()

    return title, summary


# --- Step 7: Generate slug ---


def make_slug(anchor_tags, month_str):
    """Extract values from anchor tags, join with dash, append month."""
    parts = []
    for tag in sorted(anchor_tags)[:4]:
        if ":" in tag:
            value = tag.split(":", 1)[1]
        else:
            value = tag
        clean = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        if clean:
            parts.append(clean)
    return "-".join(parts) + "-" + month_str


# --- Step 8: Store in DB ---

UPSERT_EPIC = """
INSERT INTO epics (slug, month, title, summary, anchor_tags,
                   centroid_count, event_count, total_sources, updated_at)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
ON CONFLICT (slug) DO UPDATE SET
    title = EXCLUDED.title,
    summary = EXCLUDED.summary,
    anchor_tags = EXCLUDED.anchor_tags,
    centroid_count = EXCLUDED.centroid_count,
    event_count = EXCLUDED.event_count,
    total_sources = EXCLUDED.total_sources,
    updated_at = NOW()
RETURNING id
"""

DELETE_EPIC_EVENTS = "DELETE FROM epic_events WHERE epic_id = %s"

INSERT_EPIC_EVENT = """
INSERT INTO epic_events (epic_id, event_id, is_included)
VALUES (%s, %s, TRUE)
ON CONFLICT DO NOTHING
"""


def store_epic(conn, slug, month, title, summary, anchor_tags, events):
    centroids = set()
    total_sources = 0
    for ev in events:
        centroids.add(ev[6])  # centroid_id
        total_sources += ev[4]  # source_batch_count

    cur = conn.cursor()
    cur.execute(
        UPSERT_EPIC,
        (
            slug,
            month,
            title,
            summary,
            anchor_tags,
            len(centroids),
            len(events),
            total_sources,
        ),
    )
    epic_id = cur.fetchone()[0]

    cur.execute(DELETE_EPIC_EVENTS, (str(epic_id),))
    for ev in events:
        cur.execute(INSERT_EPIC_EVENT, (str(epic_id), str(ev[0])))

    conn.commit()
    return epic_id


# --- Step 9: Post-build dedup ---


def dedup_epics(conn, stored_epics, month, month_str, overlap_threshold=0.30):
    """Merge epics whose event sets overlap significantly."""
    if len(stored_epics) < 2:
        return stored_epics

    print()
    print("-" * 50)
    print("DEDUP: checking %d epics for event overlap..." % len(stored_epics))

    # Build event ID sets
    event_sets = {}
    for ep in stored_epics:
        event_sets[ep["slug"]] = set(ev[0] for ev in ep["events"])

    # Find merge pairs (smaller absorbed into larger)
    merges = []
    slugs = [ep["slug"] for ep in stored_epics]
    for i in range(len(slugs)):
        for j in range(i + 1, len(slugs)):
            a, b = slugs[i], slugs[j]
            overlap = len(event_sets[a] & event_sets[b])
            smaller_size = min(len(event_sets[a]), len(event_sets[b]))
            if smaller_size == 0:
                continue
            ratio = overlap / smaller_size
            if ratio >= overlap_threshold:
                if len(event_sets[a]) >= len(event_sets[b]):
                    merges.append((a, b, ratio))
                else:
                    merges.append((b, a, ratio))

    if not merges:
        print("  No overlapping epics found.")
        return stored_epics

    merges.sort(key=lambda x: -x[2])

    absorbed = set()
    ep_by_slug = {ep["slug"]: ep for ep in stored_epics}

    for keeper_slug, absorbed_slug, ratio in merges:
        if keeper_slug in absorbed or absorbed_slug in absorbed:
            continue

        keeper = ep_by_slug[keeper_slug]
        victim = ep_by_slug[absorbed_slug]

        print(
            "  MERGE: %s (%.0f%% overlap) into %s"
            % (absorbed_slug, ratio * 100, keeper_slug)
        )

        # Combine anchor tags and events
        combined_tags = sorted(set(keeper["anchor_tags"]) | set(victim["anchor_tags"]))
        existing_ids = set(ev[0] for ev in keeper["events"])
        combined_events = list(keeper["events"])
        for ev in victim["events"]:
            if ev[0] not in existing_ids:
                combined_events.append(ev)
                existing_ids.add(ev[0])

        # Regenerate title + summary for combined epic
        title, summary = generate_title_summary(combined_tags, combined_events)
        new_slug = make_slug(combined_tags, month_str)
        if title:
            print("    Title: %s" % title)
        print("    Slug: %s" % new_slug)
        print(
            "    Events: %d (was %d + %d unique)"
            % (
                len(combined_events),
                len(keeper["events"]),
                len(combined_events) - len(keeper["events"]),
            )
        )

        # Delete both old epics from DB, re-insert merged
        cur = conn.cursor()
        cur.execute("DELETE FROM epics WHERE id = %s", (str(victim["epic_id"]),))
        cur.execute("DELETE FROM epics WHERE id = %s", (str(keeper["epic_id"]),))
        conn.commit()

        epic_id = store_epic(
            conn, new_slug, month, title, summary, combined_tags, combined_events
        )
        print("    Stored: %s" % epic_id)

        absorbed.add(absorbed_slug)

        # Update keeper in-place for potential chained merges
        keeper["anchor_tags"] = combined_tags
        keeper["events"] = combined_events
        keeper["epic_id"] = epic_id
        keeper["slug"] = new_slug
        ep_by_slug[new_slug] = keeper

    final = [ep for ep in stored_epics if ep["slug"] not in absorbed]
    print("  Dedup: %d absorbed, %d final epics." % (len(absorbed), len(final)))
    return final


# --- Step 10: Enrichment (timeline, narratives, centroid summaries) ---

ENRICH_EVENTS_QUERY = """
SELECT e.id, e.title, e.summary, e.tags, e.source_batch_count, e.date,
       c.centroid_id, c.track
FROM epic_events ee
JOIN events_v3 e ON ee.event_id = e.id
JOIN ctm c ON e.ctm_id = c.id
WHERE ee.epic_id = %s AND ee.is_included = true
ORDER BY e.date, c.centroid_id
"""


# --- Wikipedia fact-check reference ---


WIKI_HEADERS = {
    "User-Agent": "WorldBriefBot/1.0 (https://worldbrief.io; contact@worldbrief.io)",
}


def fetch_wikipedia_context(title, anchor_tags, month_str=None):
    """Search Wikipedia for the epic topic and return article content.

    Fetches full article text (not just intros) for the most relevant
    articles. Returns up to ~8000 chars of combined content.
    """
    from urllib.parse import quote

    queries = []
    # Tag + year first: most likely to find specific event articles
    for tag in anchor_tags[:5]:
        if ":" in tag:
            val = tag.split(":", 1)[1]
            if month_str:
                queries.append("%s %s" % (val, month_str[:4]))
    # Then title-based queries as fallback
    if title:
        if month_str:
            queries.append("%s %s" % (title, month_str[:4]))
        queries.append(title)

    seen_pages = set()
    all_extracts = []
    total_chars = 0
    max_chars = 8000

    for query in queries:
        if total_chars >= max_chars:
            break
        try:
            search_url = (
                "https://en.wikipedia.org/w/api.php"
                "?action=query&list=search&srsearch=%s"
                "&srlimit=3&format=json&utf8=1" % quote(query)
            )
            resp = httpx.get(search_url, headers=WIKI_HEADERS, timeout=10)
            if resp.status_code != 200:
                continue

            results = resp.json().get("query", {}).get("search", [])
            new_results = [r for r in results if r["pageid"] not in seen_pages]
            if not new_results:
                continue

            # Fetch full article extracts (no exintro flag)
            page_ids = "|".join(str(r["pageid"]) for r in new_results[:2])
            extract_url = (
                "https://en.wikipedia.org/w/api.php"
                "?action=query&prop=extracts&explaintext=1"
                "&pageids=%s&format=json&utf8=1" % page_ids
            )
            resp = httpx.get(extract_url, headers=WIKI_HEADERS, timeout=15)
            if resp.status_code != 200:
                continue

            pages = resp.json().get("query", {}).get("pages", {})
            for page in pages.values():
                pid = page.get("pageid")
                if pid in seen_pages:
                    continue
                seen_pages.add(pid)

                extract = page.get("extract", "").strip()
                if extract and len(extract) > 300:
                    # Cap per article at 4000 chars
                    if len(extract) > 4000:
                        extract = extract[:4000] + "..."
                    all_extracts.append("## %s\n%s" % (page.get("title", ""), extract))
                    total_chars += len(extract)

        except Exception:
            continue

    if all_extracts:
        return "\n\n".join(all_extracts)
    return None


ENRICH_RULES = (
    "YOU HAVE TWO SOURCES:\n"
    "1. REFERENCE MATERIAL (Wikipedia) - your primary source for facts, names, "
    "dates, and sequence of events. Trust it for accuracy.\n"
    "2. EVENT DATA (news titles from our platform) - shows what topics were "
    "covered and from which countries. Use it to understand geographic spread, "
    "which angles got attention, and cross-country dynamics.\n\n"
    "Synthesize both sources into an accurate, well-informed narrative. "
    "When the reference and event data conflict on facts (names, dates, "
    "sequence), trust the reference. When the event data covers angles or "
    "countries the reference does not, include those perspectives.\n\n"
    "NEVER use facts from your training data. Only the two sources above.\n\n"
    "DATES: Use specific dates only when stated in the reference material. "
    "The dates in the event data are article PUBLISH dates (they lag actual "
    "events by 1+ days) - do not treat them as event dates. When no exact "
    "date is available, use approximate references: 'in early January', "
    "'mid-month', 'by late January'.\n\n"
    "CRITICAL - TITLES AND ROLES:\n"
    "- Your training data may be OUTDATED. Political offices change.\n"
    "- NEVER write 'former president Trump' - Trump is the current US President.\n"
    "- NEVER write 'opposition leader Merz' - Merz is now German Chancellor.\n"
    "- When unsure about someone's current role, use just their name without title.\n"
    "- Safe: 'Trump announced...', 'Merz stated...'\n\n"
    "TONE AND STYLE:\n"
    "- 100%% neutral, balanced. No value judgments. No words like 'cynically', "
    "'brazenly', 'aggressively'. Describe actions and stated positions.\n"
    "- Present all sides' stated positions with equal weight.\n"
    "- Clear, explanatory style. Imagine explaining to a smart reader who "
    "follows the news but might not know specialized terms. Spell out "
    "acronyms on first use and explain context when helpful.\n"
)


def generate_timeline(title, events, wiki_ref=None):
    """Generate a chronological narrative of how the story unfolded."""
    lines = []
    for ev in events:
        eid, etitle, summary, tags, src, date, centroid, track = ev
        lines.append("%s | %-20s | %s" % (date, centroid, etitle or summary[:80]))

    event_list = "\n".join(lines)

    ref_block = "No reference material available.\n\n"
    if wiki_ref:
        ref_block = "REFERENCE MATERIAL:\n%s\n\n" % wiki_ref

    prompt = (
        "You are writing a chronological narrative of a major news story "
        "that unfolded across multiple countries.\n\n"
        "%s\n"
        "Story: %s\n\n"
        "%s"
        "EVENT DATA (news coverage from our platform, sorted by publish date "
        "with country/region):\n"
        "%s\n\n"
        "Write a chronological narrative (3-5 paragraphs) describing how this "
        "story unfolded during the month and across geography. Use the "
        "reference material for accurate facts, names, and dates. Use the "
        "event data to understand which countries covered the story and "
        "what angles received attention. Focus on:\n"
        "- Key developments and escalations\n"
        "- How different countries/regions reacted\n"
        "- Important turning points\n\n"
        "Write in past tense."
    ) % (ENRICH_RULES, title, ref_block, event_list)

    headers = {
        "Authorization": "Bearer %s" % config.deepseek_api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.llm_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 1500,
    }

    resp = httpx.post(
        "%s/chat/completions" % config.deepseek_api_url,
        headers=headers,
        json=payload,
        timeout=90,
    )

    if resp.status_code != 200:
        print("    ERROR: timeline LLM returned %d" % resp.status_code)
        return None

    return resp.json()["choices"][0]["message"]["content"].strip()


def generate_narratives(title, events, wiki_ref=None):
    """Identify main narrative threads within the story."""
    lines = []
    for ev in events[:80]:
        eid, etitle, summary, tags, src, date, centroid, track = ev
        lines.append("[%s] %s" % (centroid, etitle or summary[:80]))

    event_list = "\n".join(lines)

    ref_block = "No reference material available.\n\n"
    if wiki_ref:
        ref_block = "REFERENCE MATERIAL:\n%s\n\n" % wiki_ref

    prompt = (
        "You are analyzing a major news story that spanned multiple countries.\n\n"
        "%s\n"
        "Story: %s\n\n"
        "%s"
        "EVENT DATA (news coverage by country):\n%s\n\n"
        "Identify 3-5 distinct narrative threads or angles within this story. "
        "These should be genuinely different dimensions (e.g. diplomatic, "
        "economic, military, domestic politics, legal, humanitarian). "
        "Use the reference material for accurate details and the event data "
        "to understand cross-country coverage.\n\n"
        "Respond with ONLY a JSON array:\n"
        '[{"title": "short title", "description": "2-3 sentence description"}, ...]\n\n'
        "Return ONLY the JSON array, no other text."
    ) % (ENRICH_RULES, title, ref_block, event_list)

    headers = {
        "Authorization": "Bearer %s" % config.deepseek_api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.llm_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 1000,
    }

    resp = httpx.post(
        "%s/chat/completions" % config.deepseek_api_url,
        headers=headers,
        json=payload,
        timeout=90,
    )

    if resp.status_code != 200:
        print("    ERROR: narratives LLM returned %d" % resp.status_code)
        return None

    content = resp.json()["choices"][0]["message"]["content"].strip()

    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        content = content.rsplit("```", 1)[0]

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        print("    ERROR: narratives JSON parse failed")
        return None


def generate_centroid_summaries(title, events, wiki_ref=None):
    """Generate a short summary for each centroid's perspective."""
    by_centroid = defaultdict(list)
    for ev in events:
        by_centroid[ev[6]].append(ev)

    lines = []
    for cid in sorted(by_centroid):
        cevents = sorted(by_centroid[cid], key=lambda e: -e[4])[:8]
        titles = [e[1] or e[2][:80] for e in cevents]
        lines.append("%s (%d events):" % (cid, len(by_centroid[cid])))
        for t in titles:
            lines.append("  - %s" % t)

    event_list = "\n".join(lines)

    ref_block = "No reference material available.\n\n"
    if wiki_ref:
        ref_block = "REFERENCE MATERIAL:\n%s\n\n" % wiki_ref

    prompt = (
        "You are summarizing how a global news story manifested across "
        "different countries and regions.\n\n"
        "%s\n"
        "Story: %s\n\n"
        "%s"
        "EVENT DATA (news coverage by country):\n%s\n\n"
        "For each country/region, write a 1-2 sentence summary of the key "
        "developments from that perspective. Use the reference material for "
        "accurate details and the event data for country-specific angles.\n\n"
        "Respond with ONLY a JSON object:\n"
        '{"CENTROID_ID": "summary text", ...}\n\n'
        "Use the exact centroid IDs as keys. Return ONLY the JSON, no other text."
    ) % (ENRICH_RULES, title, ref_block, event_list)

    headers = {
        "Authorization": "Bearer %s" % config.deepseek_api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.llm_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 2000,
    }

    resp = httpx.post(
        "%s/chat/completions" % config.deepseek_api_url,
        headers=headers,
        json=payload,
        timeout=90,
    )

    if resp.status_code != 200:
        print("    ERROR: centroid summaries LLM returned %d" % resp.status_code)
        return None

    content = resp.json()["choices"][0]["message"]["content"].strip()

    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        content = content.rsplit("```", 1)[0]

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        print("    ERROR: centroid summaries JSON parse failed")
        return None


UPDATE_ENRICHMENT = """
UPDATE epics SET timeline = %s, narratives = %s, centroid_summaries = %s,
       updated_at = NOW()
WHERE id = %s
"""


def enrich_epic(conn, epic_id, title, events, anchor_tags=None, month_str=None):
    """Generate and store timeline, narratives, centroid summaries."""
    # Fetch Wikipedia reference for fact-checking
    wiki_ref = None
    if anchor_tags:
        print("  Fetching Wikipedia context...")
        wiki_ref = fetch_wikipedia_context(title, anchor_tags, month_str)
        if wiki_ref:
            print("  Wikipedia context: %d chars" % len(wiki_ref))
        else:
            print("  No Wikipedia context found")

    print("  Enriching: timeline...")
    timeline = generate_timeline(title, events, wiki_ref)

    # If LLM rejected the prompt (content filter), retry without Wikipedia
    if timeline is None and wiki_ref:
        print("  Retrying enrichment without Wikipedia context...")
        wiki_ref = None
        timeline = generate_timeline(title, events, None)

    print("  Enriching: narratives...")
    narratives = generate_narratives(title, events, wiki_ref)

    print("  Enriching: centroid summaries...")
    centroid_sums = generate_centroid_summaries(title, events, wiki_ref)

    cur = conn.cursor()
    cur.execute(
        UPDATE_ENRICHMENT,
        (
            timeline,
            json.dumps(narratives) if narratives else None,
            json.dumps(centroid_sums) if centroid_sums else None,
            str(epic_id),
        ),
    )
    conn.commit()

    parts = []
    if timeline:
        parts.append("timeline")
    if narratives:
        parts.append("%d narratives" % len(narratives))
    if centroid_sums:
        parts.append("%d centroid summaries" % len(centroid_sums))
    print("  Enriched: %s" % ", ".join(parts))


def enrich_all(month_str=None):
    """Enrich all epics for a month."""
    conn = get_connection()
    try:
        if month_str:
            month = month_str + "-01"
        else:
            latest = get_latest_month(conn)
            if not latest:
                print("No CTM data found.")
                return
            month = str(latest)
            month_str = month[:7]

        cur = conn.cursor()
        cur.execute(
            "SELECT id, title, slug, anchor_tags FROM epics WHERE month = %s "
            "ORDER BY total_sources DESC",
            (month,),
        )
        epics = cur.fetchall()

        if not epics:
            print("No epics found for %s" % month_str)
            return

        print("=" * 60)
        print("ENRICH EPICS: %s (%d epics)" % (month_str, len(epics)))
        print("=" * 60)

        for epic_id, title, slug, anchor_tags in epics:
            print()
            print("-" * 50)
            print("Epic: %s" % (title or slug))

            cur.execute(ENRICH_EVENTS_QUERY, (str(epic_id),))
            events = cur.fetchall()
            print("  %d events" % len(events))

            enrich_epic(conn, epic_id, title or slug, events, anchor_tags, month_str)

        print()
        print("=" * 60)
        print("Enrichment complete for %d epics." % len(epics))

    finally:
        conn.close()


# --- Main orchestration ---


def get_latest_month(conn):
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT month FROM ctm ORDER BY month DESC LIMIT 1")
    row = cur.fetchone()
    if not row:
        return None
    return row[0]


def run(month_str=None, min_sources=5, min_centroids=8, dry_run=False):
    conn = get_connection()
    try:
        # Resolve month
        if month_str:
            month = month_str + "-01"
        else:
            latest = get_latest_month(conn)
            if not latest:
                print("No CTM data found.")
                return
            month = str(latest)
            month_str = month[:7]
            print("Using latest month: %s" % month_str)

        print("=" * 60)
        print("BUILD EPICS: %s" % month_str)
        print("=" * 60)
        print()

        # Step 1: Find bridge tags
        bridge_tags = find_bridge_tags(conn, month, min_sources, min_centroids)
        if not bridge_tags:
            print("No bridge tags found for %s" % month_str)
            return

        bridge_tag_set = {t[0] for t in bridge_tags}
        print(
            "Found %d bridge tags (min_centroids=%d, min_sources=%d)"
            % (len(bridge_tag_set), min_centroids, min_sources)
        )
        for tag, spread, count, sources in bridge_tags[:20]:
            print(
                "  %-35s spread=%d events=%d sources=%d" % (tag, spread, count, sources)
            )
        if len(bridge_tags) > 20:
            print("  ... +%d more" % (len(bridge_tags) - 20))
        print()

        # Step 2: Build Jaccard similarity graph
        cur = conn.cursor()
        cur.execute(MONTH_EVENTS_QUERY, (month,))
        all_events = cur.fetchall()
        tag_event_sets = build_tag_event_sets(all_events, bridge_tag_set)
        edges = build_jaccard_graph(tag_event_sets, min_jaccard=0.15)

        print(
            "Jaccard graph: %d edges (threshold >= 0.15) from %d events"
            % (len(edges), len(all_events))
        )
        if edges:
            top_edges = sorted(edges.items(), key=lambda x: -x[1])[:10]
            for (a, b), j in top_edges:
                print("  %-25s <-> %-25s J=%.2f" % (a, b, j))
        print()

        # Step 3: Find components (including single-tag epics)
        components = find_components(edges, bridge_tag_set)
        print(
            "Found %d candidates (%d multi-tag, %d single-tag)"
            % (
                len(components),
                sum(1 for c in components if len(c) > 1),
                sum(1 for c in components if len(c) == 1),
            )
        )
        print()

        # Process each component
        epic_count = 0
        stored_epics = []
        for comp_idx, anchor_tags in enumerate(components):
            print("-" * 50)
            print("Candidate %d: %s" % (comp_idx + 1, ", ".join(anchor_tags)))

            # Step 4: Pull events
            events = get_component_events(conn, month, anchor_tags)
            print("  %d raw events" % len(events))

            if len(events) < 5:
                print("  SKIP: fewer than 5 events")
                continue

            # Step 5: LLM filter
            if not dry_run:
                events = llm_filter(anchor_tags, events)

            if len(events) < 5:
                print("  SKIP: fewer than 5 events after filter")
                continue

            centroids_after = len(set(ev[6] for ev in events))
            if centroids_after < min_centroids:
                print(
                    "  SKIP: %d centroids after filter (need %d)"
                    % (centroids_after, min_centroids)
                )
                continue

            total_sources = sum(ev[4] for ev in events)
            print(
                "  ACCEPT: %d events, %d centroids, %d sources"
                % (len(events), centroids_after, total_sources)
            )

            if dry_run:
                for ev in events[:5]:
                    print("    [%3d] %-20s %s" % (ev[4], ev[6], ev[1]))
                print()
                epic_count += 1
                continue

            # Step 6: Generate title + summary
            title, summary = generate_title_summary(anchor_tags, events)
            if title:
                print("  Title: %s" % title)

            # Step 7: Generate slug
            slug = make_slug(anchor_tags, month_str)
            print("  Slug: %s" % slug)

            # Step 8: Store
            epic_id = store_epic(conn, slug, month, title, summary, anchor_tags, events)
            print("  Stored: %s" % epic_id)
            print()

            stored_epics.append(
                {
                    "epic_id": epic_id,
                    "slug": slug,
                    "anchor_tags": anchor_tags,
                    "events": events,
                }
            )
            epic_count += 1

        # Step 9: Dedup overlapping epics
        if not dry_run and len(stored_epics) > 1:
            stored_epics = dedup_epics(conn, stored_epics, month, month_str)

        print()
        print("=" * 60)
        if dry_run:
            print("DRY RUN complete. %d candidates pass thresholds." % epic_count)
        else:
            print("Done. %d epics stored for %s." % (len(stored_epics), month_str))

    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Build cross-centroid epics")
    parser.add_argument(
        "--month",
        help="Month to process (YYYY-MM format, default: latest)",
    )
    parser.add_argument(
        "--min-sources",
        type=int,
        default=5,
        help="Min sources per event for bridge detection (default: 5)",
    )
    parser.add_argument(
        "--min-centroids",
        type=int,
        default=8,
        help="Min centroid spread for bridge tag (default: 8)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview candidates without storing or calling LLM",
    )
    parser.add_argument(
        "--enrich-only",
        action="store_true",
        help="Re-enrich existing epics without re-detecting",
    )
    args = parser.parse_args()

    if args.enrich_only:
        enrich_all(month_str=args.month)
    else:
        run(
            month_str=args.month,
            min_sources=args.min_sources,
            min_centroids=args.min_centroids,
            dry_run=args.dry_run,
        )


if __name__ == "__main__":
    main()
