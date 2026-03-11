"""
Test script for comparative RAI analysis.

Fetches stance-clustered narratives for an entity, builds the comparative
prompt, calls DeepSeek, and prints the result. Saves to entity_analyses table.

Usage:
    python scripts/test_comparative_analysis.py --entity-type event --entity-id <UUID>
    python scripts/test_comparative_analysis.py --entity-type event --entity-id <UUID> --prompt-only
"""

import argparse
import json
import sys
from pathlib import Path

import httpx
import psycopg2
from psycopg2.extras import RealDictCursor

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config
from pipeline.epics.build_epics import fetch_wikipedia_context


def get_conn():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        dbname=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def fetch_cluster_narratives(conn, entity_type, entity_id):
    """Fetch stance-clustered narratives for an entity."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT label, description, moral_frame, sample_titles, title_count,
                   cluster_label, cluster_publishers, cluster_score_avg, signal_stats
            FROM narratives
            WHERE entity_type = %s AND entity_id = %s
              AND extraction_method = 'stance_clustered'
            ORDER BY cluster_score_avg ASC
            """,
            (entity_type, str(entity_id)),
        )
        return cur.fetchall()


def fetch_entity_context(conn, entity_type, entity_id):
    """Fetch entity context for prompt."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        if entity_type == "event":
            cur.execute(
                """
                SELECT cv.label as centroid_name, c.centroid_id, c.track,
                       COALESCE(e.title, e.topic_core) as event_title
                FROM events_v3 e
                JOIN ctm c ON c.id = e.ctm_id
                JOIN centroids_v3 cv ON cv.id = c.centroid_id
                WHERE e.id = %s
                """,
                (str(entity_id),),
            )
        else:
            cur.execute(
                """
                SELECT cv.label as centroid_name, c.centroid_id, c.track,
                       '' as event_title
                FROM ctm c
                JOIN centroids_v3 cv ON cv.id = c.centroid_id
                WHERE c.id = %s
                """,
                (str(entity_id),),
            )
        return cur.fetchone()


# -- Inline RAI engine (mirrors rai-engine.ts logic) --

# Core modules always included
CORE_MODULES = ["CL-0", "CL-6", "NL-3", "SL-8"]
FALLBACK_MODULES = ["NL-1", "FL-2", "FL-3", "CL-5", "CL-7", "SL-1", "FL-10", "NL-4"]

MODULE_CATALOG = [
    ("CL-1", "Trace fact-to-narrative linkage and compression distortion"),
    ("CL-2", "Test assumption burden and hidden inference gaps"),
    ("CL-3", "Map layered/nested narratives and meta-narrative shields"),
    ("CL-4", "Detect moral language fused with strategic motives"),
    ("CL-5", "Enforce consistent evaluation standards across all actors"),
    (
        "CL-7",
        "Diagnose coverage ecosystem for bloc alignment vs epistemic independence",
    ),
    ("FL-1", "Isolate, verify, and anchor core factual claims"),
    ("FL-2", "Detect unnatural amplification or suppression patterns"),
    ("FL-3", "Audit source independence, diversity, and coordination"),
    ("FL-4", "Evaluate strategic fact selection and cherry-picking"),
    ("FL-5", "Prevent scale inflation/minimization in fact framing"),
    ("FL-6", "Identify omitted or misrepresented primary actor speech"),
    ("FL-7", "Calibrate skepticism by stakes and risk context"),
    ("FL-8", "Anchor claims in specific verifiable time and place"),
    ("FL-9", "Detect judgment-distorting toxic labels"),
    ("FL-10", "Audit descriptive vocabulary for invisible bias and asymmetric naming"),
    (
        "FL-11",
        "Compare stated positions with observable actions, timing, and resource allocation",
    ),
    ("NL-1", "Evaluate cause-effect chain logic and start-point bias"),
    ("NL-2", "Test narrative internal coherence and plausibility"),
    ("NL-4", "Identify group identity and historical trauma framing"),
    ("NL-5", "Flag distorting metaphors, analogies, and symbols"),
    ("NL-6", "Identify strategic narrative gaps and omissions"),
    ("NL-7", "Audit legal/institutional legitimacy claims and selective enforcement"),
    ("SL-1", "Map power, incentive, and benefit structures"),
    ("SL-2", "Examine institutional enforcement and suppression"),
    ("SL-3", "Uncover collective memory and identity exploitation"),
    ("SL-4", "Determine deeper purpose: mobilize, justify, distract"),
    ("SL-5", "Detect performative resistance masking power structures"),
    ("SL-6", "Identify recursive reinforcement loops and false consensus"),
    ("SL-7", "Project future outcomes to test claim validity"),
    ("SL-9", "Track claim evolution under pressure and contradiction"),
    ("SL-10", "Map distortion in closed information loops"),
    ("SL-11", "Evaluate technocratic and algorithmic governance claims"),
    ("SL-12", "Assess digital infrastructure control and dependencies"),
]


def select_modules_llm(narratives, context):
    """LLM selects 4 comparative modules."""
    lines = [
        "You are selecting analytical modules for a COMPARATIVE media framing analysis.",
        "Multiple editorial clusters are being analysed simultaneously.",
        "",
    ]
    for n in narratives:
        pubs = ", ".join((n["cluster_publishers"] or [])[:5])
        lines.append('CLUSTER "%s" (%s): %s' % (n["cluster_label"], pubs, n["label"]))
        if n.get("moral_frame"):
            lines.append("  Moral frame: %s" % n["moral_frame"])

    lines.append("")
    lines.append(
        "EVENT: %s | REGION: %s | TRACK: %s"
        % (
            context.get("event_title") or "N/A",
            context.get("centroid_name") or "N/A",
            context.get("track") or "N/A",
        )
    )
    lines.append("")
    lines.append("4 core modules already included (CL-0, CL-6, NL-3, SL-8).")
    lines.append("Select exactly 8 additional modules for CROSS-CLUSTER comparison.")
    lines.append("Prioritize modules that reveal power asymmetry, coverage imbalance,")
    lines.append("evaluative double standards, and structural blind spots.")
    lines.append("")
    lines.append("AVAILABLE MODULES:")
    for mid, summary in MODULE_CATALOG:
        lines.append("%s: %s" % (mid, summary))
    lines.append("")
    lines.append("Respond with exactly 8 module IDs, one per line.")

    prompt = "\n".join(lines)

    resp = httpx.post(
        "%s/chat/completions" % config.deepseek_api_url,
        headers={
            "Authorization": "Bearer %s" % config.deepseek_api_key,
            "Content-Type": "application/json",
        },
        json={
            "model": config.llm_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": 250,
        },
        timeout=30,
    )

    if resp.status_code != 200:
        print("Module selector failed, using fallback")
        return FALLBACK_MODULES

    content = resp.json()["choices"][0]["message"]["content"]
    import re

    matches = re.findall(r"(CL-\d+|FL-\d+|NL-\d+|SL-\d+)", content)
    valid = set(m[0] for m in MODULE_CATALOG)
    selected = []
    for m in matches:
        if m in valid and m not in selected and m not in CORE_MODULES:
            selected.append(m)
            if len(selected) == 8:
                break

    while len(selected) < 8:
        for fb in FALLBACK_MODULES:
            if fb not in selected:
                selected.append(fb)
                break

    return selected


def build_comparative_prompt(narratives, context, modules, wiki_context=None):
    """Build the comparative analysis prompt."""
    parts = []

    parts.append(
        "You are operating under the **Real Artificial Intelligence (RAI) Framework**."
    )
    parts.append(
        "This is a **comparative media framing analysis** of news coverage "
        "from the WorldBrief intelligence platform."
    )
    parts.append("")
    parts.append(
        "You are analysing %d competing narrative clusters for the same event."
        % len(narratives)
    )
    parts.append("Each cluster groups publishers with similar editorial stance.")
    parts.append("")
    parts.append("Your task:")
    parts.append("- For each analytical module, write a SINGLE comparative assessment")
    parts.append("- Identify where the clusters CONVERGE (shared assumptions)")
    parts.append("- Identify where they DIVERGE (contested elements)")
    parts.append("- Note what each cluster OMITS that another includes")
    parts.append("- Note what ALL clusters omit (collective blind spots)")
    parts.append("")
    parts.append(
        "Do NOT analyse each cluster separately. Write as a strategic analyst "
        "producing one integrated comparative brief."
    )
    parts.append("")
    parts.append(
        "**CORE RULE -- ACTOR MAPPING:** Identify ALL actors -- whether direct "
        "parties, indirect influencers, or background beneficiaries -- whose "
        "interests, lobbying, or actions have a significant impact on the "
        "situation. Do not limit your analysis to the actors the coverage names. "
        "Examine who is missing from the frame and why. Actors who benefit from "
        "being invisible in the narrative are often the most important to surface. "
        "Pay special attention to actors who: (a) lobby for or against resolution, "
        "(b) take military or economic actions that contradict stated diplomatic "
        "goals, (c) shape the policy of direct parties through institutional "
        "influence. If such actors are downplayed or absent in coverage, dedicate "
        "a separate subsection to their structural role."
    )
    parts.append("")
    parts.append(
        "**REPORTORIAL CLUSTER NOTE:** The reportorial cluster represents outlets "
        "that avoid strong editorial framing. Mention it briefly where relevant "
        "(what it covers that others omit, what it avoids taking a position on) "
        "but do NOT dedicate equal analysis space to it. Focus your comparative "
        "depth on clusters with active editorial framing."
    )
    parts.append("")

    # Context
    parts.append("**GEOPOLITICAL CONTEXT:**")
    if context.get("centroid_name"):
        parts.append("Region: %s" % context["centroid_name"])
    if context.get("track"):
        parts.append("Track: %s" % context["track"])
    if context.get("event_title"):
        parts.append("Event: %s" % context["event_title"])
    parts.append("")

    # Wikipedia grounding
    if wiki_context:
        parts.append("**BACKGROUND CONTEXT (Wikipedia):**")
        parts.append(
            "Use this as a reality check when assessing claims made by each cluster."
        )
        parts.append(wiki_context)
        parts.append("")

    # Cluster narratives
    parts.append("**COMPETING NARRATIVE CLUSTERS:**")
    parts.append("")
    for n in narratives:
        pubs = (n["cluster_publishers"] or [])[:8]
        pub_str = ", ".join(pubs)
        extra = len(n["cluster_publishers"] or []) - 8
        if extra > 0:
            pub_str += " (+%d more)" % extra
        parts.append(
            "**%s cluster** (avg stance: %.1f)"
            % (n["cluster_label"].upper(), n["cluster_score_avg"])
        )
        parts.append("Publishers: %s" % pub_str)
        parts.append('Frame: "%s"' % n["label"])
        if n.get("description"):
            parts.append("Stance: %s" % n["description"])
        if n.get("moral_frame"):
            parts.append("Moral framing: %s" % n["moral_frame"])
        parts.append("Titles: %d" % n["title_count"])

        sample = n.get("sample_titles") or []
        if isinstance(sample, str):
            sample = json.loads(sample)
        if sample:
            parts.append("Sample headlines:")
            for h in sample[:8]:
                parts.append('- "%s" (%s)' % (h["title"], h.get("publisher", "")))
        parts.append("")

    # Modules (simplified -- just IDs and summaries)
    parts.append("**SELECTED RAI ANALYSIS COMPONENTS:**")
    parts.append("")
    all_mods = CORE_MODULES + modules
    cat_dict = dict(MODULE_CATALOG)
    for mid in all_mods:
        summary = cat_dict.get(mid, "Core module")
        parts.append("**%s**: %s" % (mid, summary))
    parts.append("")

    # Output format
    parts.append("**OUTPUT FORMAT INSTRUCTIONS:**")
    parts.append("- Use `## ` (h2) for each module heading")
    parts.append("- Each section must be COMPARATIVE -- reference multiple clusters")
    parts.append("- Use bullet lists for specific findings")
    parts.append("- Mark philosophical insights with `> ` blockquote syntax")
    parts.append("- Keep each section to 2-4 paragraphs max")
    parts.append("- After all module sections, add `## Actors Beyond the Frame`")
    parts.append(
        "  Dedicate this section to actors whose influence is significant but "
        "who are underrepresented or absent in coverage. For each, explain their "
        "structural interest, observable actions, and why coverage minimizes them."
    )
    parts.append("- Then add `## Convergence & Collective Blind Spots`")
    parts.append("- Then add `## Unstated Assumptions & Structural Questions`")
    parts.append(
        "  For each cluster, identify the foundational assumption that is "
        "TAKEN FOR GRANTED rather than argued. Then ask: what structural, "
        "historical, or strategic context -- if true -- would fundamentally "
        "change the interpretation? You are not asserting these alternatives "
        "are true. You are noting that the coverage does not examine them."
    )
    parts.append("")
    parts.append("- Finally add `## Further Investigation`")
    parts.append(
        "  This section helps readers develop their OWN structural understanding. "
        "Include:"
    )
    parts.append(
        "  1. **Historical context to study** (2-3 specific periods or events "
        "essential for understanding this topic -- e.g. treaties, coups, wars, "
        "economic shifts)"
    )
    parts.append(
        "  2. **Recommended reading** (2-3 well-known, widely-cited books or "
        "academic works directly relevant to the structural dynamics at play. "
        "Only recommend books you are HIGHLY CONFIDENT exist and are widely "
        "cited. If unsure about a specific title, suggest the topic area instead.)"
    )
    parts.append(
        "  3. **Questions to investigate** (3-4 specific questions the reader "
        "should research independently -- focused on structural factors, "
        "economic interests, historical patterns, and power dynamics that "
        "the coverage does not examine)"
    )
    parts.append(
        "  4. **Economic and structural factors** (key economic relationships, "
        "dependencies, or leverage points that shape the actors' real constraints "
        "-- often invisible in media coverage)"
    )
    parts.append("")

    # Scoring -- structural metrics only, no per-cluster scores
    parts.append("**STRUCTURAL METRICS:**")
    parts.append("")
    parts.append(
        "Do NOT score individual clusters. The prose analysis IS the assessment."
    )
    parts.append("")
    parts.append("**At the end of your analysis**, output a metrics block:")
    parts.append("")
    parts.append(
        'SCORES: {"frame_divergence": <0-1>, '
        '"collective_blind_spots": ["...", "..."], '
        '"synthesis": "<1-2 sentence overall assessment>"}'
    )
    parts.append("")
    parts.append("frame_divergence: 0 = clusters agree, 1 = maximally opposed.")
    parts.append("The metrics must reflect your actual analysis.")

    return "\n".join(parts)


def call_deepseek(prompt):
    """Call DeepSeek for analysis."""
    resp = httpx.post(
        "%s/chat/completions" % config.deepseek_api_url,
        headers={
            "Authorization": "Bearer %s" % config.deepseek_api_key,
            "Content-Type": "application/json",
        },
        json={
            "model": config.llm_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 7000,
        },
        timeout=120,
    )

    if resp.status_code != 200:
        raise Exception("DeepSeek error: %d - %s" % (resp.status_code, resp.text[:200]))

    data = resp.json()
    usage = data.get("usage", {})
    content = data["choices"][0]["message"]["content"]
    return content, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


def parse_scores(raw):
    """Extract SCORES JSON from response."""
    import re

    m = re.search(r"SCORES:\s*(\{[\s\S]*?\})\s*$", raw, re.MULTILINE)
    if not m:
        m = re.search(r'```(?:json)?\s*(\{[^`]*"cluster_scores"[^`]*\})\s*```', raw)
    if not m:
        return {}
    try:
        return json.loads(m.group(1))
    except Exception:
        return {}


def save_analysis(conn, entity_type, entity_id, cluster_count, sections_raw, scores):
    """Save to entity_analyses table."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO entity_analyses
                (entity_type, entity_id, cluster_count, sections, scores,
                 synthesis, blind_spots)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (entity_type, entity_id) DO UPDATE SET
                cluster_count = EXCLUDED.cluster_count,
                sections = EXCLUDED.sections,
                scores = EXCLUDED.scores,
                synthesis = EXCLUDED.synthesis,
                blind_spots = EXCLUDED.blind_spots,
                created_at = NOW()
            """,
            (
                entity_type,
                str(entity_id),
                cluster_count,
                sections_raw,
                json.dumps(scores),
                scores.get("synthesis"),
                scores.get("collective_blind_spots"),
            ),
        )
    conn.commit()


def main():
    parser = argparse.ArgumentParser(description="Test comparative RAI analysis")
    parser.add_argument("--entity-type", required=True, choices=["event", "ctm"])
    parser.add_argument("--entity-id", required=True)
    parser.add_argument(
        "--prompt-only", action="store_true", help="Print prompt without calling LLM"
    )
    args = parser.parse_args()

    conn = get_conn()

    # 1. Fetch narratives
    narratives = fetch_cluster_narratives(conn, args.entity_type, args.entity_id)
    if not narratives:
        print(
            "No stance-clustered narratives found for %s %s"
            % (args.entity_type, args.entity_id)
        )
        conn.close()
        return

    print("Found %d cluster narratives:" % len(narratives))
    for n in narratives:
        print(
            "  [%s] %s (%d titles, %d publishers)"
            % (
                n["cluster_label"],
                n["label"],
                n["title_count"],
                len(n["cluster_publishers"] or []),
            )
        )

    # 2. Fetch context
    context = fetch_entity_context(conn, args.entity_type, args.entity_id)
    if not context:
        print("Entity not found")
        conn.close()
        return

    print(
        "Context: %s / %s / %s"
        % (
            context["centroid_name"],
            context["track"],
            context.get("event_title", "")[:60],
        )
    )

    # 3. Fetch Wikipedia background
    event_title = context.get("event_title", "")
    centroid_name = context.get("centroid_name", "")
    wiki_tags = ["country:%s" % centroid_name] if centroid_name else []
    print("\nFetching Wikipedia context...")
    wiki_context = fetch_wikipedia_context(event_title, wiki_tags)
    if wiki_context:
        print("Wikipedia context: %d chars" % len(wiki_context))
    else:
        print("No Wikipedia context found")

    # 4. Select modules
    print("\nSelecting modules...")
    extra_modules = select_modules_llm(narratives, context)
    all_modules = CORE_MODULES + extra_modules
    print("Modules: %s" % " + ".join(all_modules))

    # 5. Build prompt
    prompt = build_comparative_prompt(narratives, context, extra_modules, wiki_context)

    if args.prompt_only:
        print("\n" + "=" * 60)
        print("PROMPT (%d chars):" % len(prompt))
        print("=" * 60)
        print(prompt)
        conn.close()
        return

    # 6. Call LLM
    print("\nCalling DeepSeek for comparative analysis...")
    raw, tok_in, tok_out = call_deepseek(prompt)
    print("Tokens: %d in, %d out" % (tok_in, tok_out))

    # 7. Parse scores
    scores = parse_scores(raw)

    # 8. Print report
    print("\n" + "=" * 60)
    print("COMPARATIVE ANALYSIS REPORT")
    print("=" * 60)

    # Strip the SCORES block from display
    import re

    display = re.sub(r"\nSCORES:.*$", "", raw, flags=re.DOTALL).strip()
    print(display)

    if scores:
        print("\n" + "-" * 40)
        print("METRICS:")
        print(json.dumps(scores, indent=2))

    # 9. Save (store stripped content, not raw with SCORES block)
    save_analysis(
        conn, args.entity_type, args.entity_id, len(narratives), display, scores
    )
    print("\nSaved to entity_analyses table")

    conn.close()


if __name__ == "__main__":
    main()
