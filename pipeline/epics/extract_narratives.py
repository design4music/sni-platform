"""
Epic Narrative Extraction

Two-pass LLM approach to extract media framing narratives from epic titles.
Pass 1: Discover 3-7 narrative frames from sampled titles.
Pass 2: Classify ALL titles into discovered frames.

Usage:
    python -m pipeline.epics.extract_narratives --month 2026-01 --dry-run
    python -m pipeline.epics.extract_narratives --month 2026-01 --apply
"""

import argparse
import json
import math
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

import httpx

# Windows console encoding fix
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import psycopg2
import psycopg2.extras

from core.config import config
from core.prompts import (
    NARRATIVE_PASS1_SYSTEM,
    NARRATIVE_PASS1_USER,
    NARRATIVE_PASS2_SYSTEM,
    NARRATIVE_PASS2_USER,
)

SKIP_SLUGS = {"xi-2026-01"}
MAX_EPICS = 12
MIN_TITLES = 20
SAMPLE_SIZE = 150
CLASSIFY_BATCH_SIZE = 60


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def fetch_epics(conn, month):
    """Top epics by total_sources, excluding skip slugs."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT id, slug, title, summary, total_sources "
        "FROM epics WHERE month = %s "
        "ORDER BY total_sources DESC LIMIT %s",
        (month + "-01", MAX_EPICS),
    )
    rows = cur.fetchall()
    cur.close()
    return [r for r in rows if r["slug"] not in SKIP_SLUGS]


def fetch_epic_titles(conn, epic_id):
    """All titles for an epic via: epic_events -> events_v3 -> event_v3_titles -> titles_v3 + ctm -> centroids_v3."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT DISTINCT t.id AS title_id, t.title_display, t.publisher_name, "
        "       t.pubdate_utc, c.centroid_id, cv.iso_codes "
        "FROM epic_events ee "
        "JOIN events_v3 e ON e.id = ee.event_id "
        "JOIN event_v3_titles et ON et.event_id = e.id "
        "JOIN titles_v3 t ON t.id = et.title_id "
        "LEFT JOIN ctm c ON e.ctm_id = c.id "
        "LEFT JOIN centroids_v3 cv ON c.centroid_id = cv.id "
        "WHERE ee.epic_id = %s AND ee.is_included = true "
        "ORDER BY t.pubdate_utc DESC",
        (str(epic_id),),
    )
    rows = cur.fetchall()
    cur.close()
    return rows


def sample_titles_for_discovery(titles, n=SAMPLE_SIZE):
    """Proportional sample across centroids, round-robin across publishers within each centroid."""
    if len(titles) <= n:
        return titles

    # Group by centroid
    by_centroid = defaultdict(list)
    for t in titles:
        key = t["centroid_id"] or "unknown"
        by_centroid[key].append(t)

    total = len(titles)
    sampled = []

    for centroid_key, ctitles in by_centroid.items():
        # Proportional allocation
        alloc = max(1, round(n * len(ctitles) / total))

        # Round-robin across publishers within this centroid
        by_pub = defaultdict(list)
        for t in ctitles:
            by_pub[t["publisher_name"] or "unknown"].append(t)

        pubs = list(by_pub.values())
        picked = 0
        idx = 0
        while picked < alloc and picked < len(ctitles):
            bucket = pubs[idx % len(pubs)]
            if bucket:
                sampled.append(bucket.pop(0))
                picked += 1
            idx += 1
            # Safety: if we've gone through all pubs with no items
            if idx > alloc + len(pubs):
                break

    return sampled[:n]


def strip_json_fences(content):
    """Strip markdown fences if present."""
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        content = content.rsplit("```", 1)[0]
    return content.strip()


def call_llm(system, user, temperature, max_tokens):
    """Sync LLM call to DeepSeek."""
    headers = {
        "Authorization": "Bearer %s" % config.deepseek_api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    resp = httpx.post(
        "%s/chat/completions" % config.deepseek_api_url,
        headers=headers,
        json=payload,
        timeout=120,
    )
    if resp.status_code != 200:
        raise Exception("LLM error: %d - %s" % (resp.status_code, resp.text))

    data = resp.json()
    usage = data.get("usage", {})
    tok_in = usage.get("prompt_tokens", 0)
    tok_out = usage.get("completion_tokens", 0)
    content = data["choices"][0]["message"]["content"].strip()
    return content, tok_in, tok_out


def pass1_discover_frames(epic_title, epic_summary, month, sampled_titles):
    """Pass 1: Discover 3-7 narrative frames from sampled titles."""
    lines = []
    for t in sampled_titles:
        pub = t["publisher_name"] or "unknown"
        lines.append("[%s] %s" % (pub, t["title_display"]))
    titles_block = "\n".join(lines)

    user_msg = NARRATIVE_PASS1_USER.format(
        epic_title=epic_title,
        epic_summary=epic_summary or "N/A",
        month=month,
        sample_count=len(sampled_titles),
        titles_block=titles_block,
    )

    content, tok_in, tok_out = call_llm(NARRATIVE_PASS1_SYSTEM, user_msg, 0.4, 1500)
    content = strip_json_fences(content)

    try:
        frames = json.loads(content)
    except json.JSONDecodeError:
        print("    WARN: Pass 1 JSON parse failed, retrying...")
        content, tok_in2, tok_out2 = call_llm(
            NARRATIVE_PASS1_SYSTEM, user_msg, 0.3, 1500
        )
        tok_in += tok_in2
        tok_out += tok_out2
        content = strip_json_fences(content)
        frames = json.loads(content)

    print(
        "    Pass 1: %d frames, %d tok in, %d tok out" % (len(frames), tok_in, tok_out),
        flush=True,
    )
    return frames, tok_in, tok_out


def pass2_classify_titles(epic_title, frames, all_titles):
    """Pass 2: Classify all titles into frames in batches."""
    frame_desc = "\n".join("- %s: %s" % (f["label"], f["description"]) for f in frames)

    # Batch titles, grouped by publisher for better coherence
    sorted_titles = sorted(all_titles, key=lambda t: t["publisher_name"] or "")
    classifications = []
    total_tok_in = 0
    total_tok_out = 0

    total_batches = math.ceil(len(sorted_titles) / CLASSIFY_BATCH_SIZE)
    for batch_num, offset in enumerate(
        range(0, len(sorted_titles), CLASSIFY_BATCH_SIZE), 1
    ):
        batch = sorted_titles[offset : offset + CLASSIFY_BATCH_SIZE]
        print(
            "    Pass 2 batch %d/%d (%d titles)..."
            % (batch_num, total_batches, len(batch)),
            flush=True,
        )
        lines = []
        for i, t in enumerate(batch, 1):
            pub = t["publisher_name"] or "unknown"
            lines.append("%d. [%s] %s" % (i, pub, t["title_display"]))
        titles_block = "\n".join(lines)

        user_msg = NARRATIVE_PASS2_USER.format(
            epic_title=epic_title,
            frame_desc=frame_desc,
            titles_block=titles_block,
        )

        content, tok_in, tok_out = call_llm(NARRATIVE_PASS2_SYSTEM, user_msg, 0.1, 2000)
        total_tok_in += tok_in
        total_tok_out += tok_out
        content = strip_json_fences(content)

        try:
            batch_result = json.loads(content)
        except json.JSONDecodeError:
            print(
                "    WARN: Pass 2 batch parse failed at offset %d, retrying..." % offset
            )
            content, tok_in2, tok_out2 = call_llm(
                NARRATIVE_PASS2_SYSTEM, user_msg, 0.1, 2000
            )
            total_tok_in += tok_in2
            total_tok_out += tok_out2
            content = strip_json_fences(content)
            try:
                batch_result = json.loads(content)
            except json.JSONDecodeError:
                print(
                    "    ERROR: Pass 2 batch at offset %d failed twice, skipping"
                    % offset
                )
                batch_result = [
                    {"n": i + 1, "frame": "neutral"} for i in range(len(batch))
                ]

        # Map back to global title info
        for item in batch_result:
            idx = item.get("n", 1) - 1
            if 0 <= idx < len(batch):
                classifications.append(
                    {
                        "title": batch[idx],
                        "frame": item.get("frame", "neutral"),
                    }
                )

    batch_count = math.ceil(len(sorted_titles) / CLASSIFY_BATCH_SIZE)
    print(
        "    Pass 2: %d batches, %d classified, %d tok in, %d tok out"
        % (batch_count, len(classifications), total_tok_in, total_tok_out),
        flush=True,
    )
    return classifications, total_tok_in, total_tok_out


def aggregate_results(frames, classifications, all_titles):
    """Aggregate classifications into narrative records with TF-IDF style source scoring."""
    frame_labels = {f["label"] for f in frames}

    # Group classifications by frame
    by_frame = defaultdict(list)
    for c in classifications:
        frame = c["frame"]
        if frame in frame_labels:
            by_frame[frame].append(c["title"])

    # Compute global source distribution across ALL classified titles
    global_source_counts = defaultdict(int)
    total_classified = 0
    for label in frame_labels:
        for t in by_frame.get(label, []):
            pub = t["publisher_name"] or "unknown"
            global_source_counts[pub] += 1
            total_classified += 1

    narratives = []
    for f in frames:
        label = f["label"]
        matched = by_frame.get(label, [])
        if not matched:
            continue

        frame_total = len(matched)

        # Count sources in this frame
        source_counts = defaultdict(int)
        country_counts = defaultdict(int)
        for t in matched:
            pub = t["publisher_name"] or "unknown"
            source_counts[pub] += 1
            for code in t.get("iso_codes") or []:
                country_counts[code] += 1

        # Compute over-index score for each source
        # over_index = (source_share_in_frame) / (source_share_in_epic)
        # > 1.0 means source favors this frame more than average
        source_scores = {}
        proportional_sources_list = []
        for pub, count in source_counts.items():
            if count < 3:  # minimum threshold
                continue
            share_in_frame = count / frame_total
            share_in_epic = global_source_counts[pub] / total_classified
            if share_in_epic > 0:
                over_index = share_in_frame / share_in_epic
                source_scores[pub] = over_index
                # Proportional sources: over-index between 0.85 and 1.15
                # These sources cover this frame at roughly their baseline rate
                if 0.85 <= over_index <= 1.15 and global_source_counts[pub] >= 20:
                    proportional_sources_list.append((pub, global_source_counts[pub]))

        # Sort by over-index score, take top 10 that over-index (>= 1.3)
        over_indexed = [(p, s) for p, s in source_scores.items() if s >= 1.3]
        top_sources = sorted(
            [p for p, s in over_indexed], key=lambda x: source_scores[x], reverse=True
        )[:10]

        # Proportional sources: sorted by total volume (most prominent first)
        proportional_sources = sorted(
            proportional_sources_list, key=lambda x: x[1], reverse=True
        )
        proportional_sources = [p for p, _ in proportional_sources][:5]

        # Fallback: if no sources over-index, use raw counts
        if not top_sources:
            top_sources = sorted(source_counts, key=source_counts.get, reverse=True)[:5]

        top_countries = sorted(country_counts, key=country_counts.get, reverse=True)[
            :10
        ]

        # Sample titles: pick diverse set
        sample = []
        seen_pubs = set()
        for t in matched:
            pub = t["publisher_name"] or "unknown"
            if pub not in seen_pubs and len(sample) < 15:
                sample.append(
                    {
                        "title": t["title_display"],
                        "publisher": pub,
                        "date": (
                            str(t["pubdate_utc"].date()) if t["pubdate_utc"] else None
                        ),
                    }
                )
                seen_pubs.add(pub)
        # Fill remaining slots if needed
        for t in matched:
            if len(sample) >= 15:
                break
            pub = t["publisher_name"] or "unknown"
            entry = {
                "title": t["title_display"],
                "publisher": pub,
                "date": str(t["pubdate_utc"].date()) if t["pubdate_utc"] else None,
            }
            if entry not in sample:
                sample.append(entry)

        narratives.append(
            {
                "label": label,
                "description": f["description"],
                "moral_frame": f.get("moral_frame"),
                "title_count": len(matched),
                "top_sources": top_sources,
                "proportional_sources": proportional_sources,
                "top_countries": top_countries,
                "sample_titles": sample[:15],
            }
        )

    narratives.sort(key=lambda x: x["title_count"], reverse=True)
    return narratives


def save_narratives(conn, epic_id, narratives):
    """DELETE existing + INSERT (idempotent re-run)."""
    cur = conn.cursor()
    cur.execute("DELETE FROM epic_narratives WHERE epic_id = %s", (str(epic_id),))
    for n in narratives:
        cur.execute(
            "INSERT INTO epic_narratives "
            "(epic_id, label, description, moral_frame, title_count, "
            " top_sources, proportional_sources, top_countries, sample_titles) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                str(epic_id),
                n["label"],
                n["description"],
                n["moral_frame"],
                n["title_count"],
                n["top_sources"],
                n["proportional_sources"],
                n["top_countries"],
                json.dumps(n["sample_titles"]),
            ),
        )
    conn.commit()
    cur.close()


def main():
    parser = argparse.ArgumentParser(description="Extract epic narrative frames")
    parser.add_argument("--month", required=True, help="YYYY-MM format")
    parser.add_argument(
        "--dry-run", action="store_true", help="Pass 1 only, print frames"
    )
    parser.add_argument("--apply", action="store_true", help="Full run + save")
    parser.add_argument("--slug", help="Process only this epic slug")
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print("ERROR: specify --dry-run or --apply")
        sys.exit(1)

    conn = get_connection()
    epics = fetch_epics(conn, args.month)
    if args.slug:
        epics = [e for e in epics if e["slug"] == args.slug]
    print("Found %d epics for %s" % (len(epics), args.month), flush=True)

    grand_tok_in = 0
    grand_tok_out = 0

    for epic in epics:
        print(
            "\n--- %s (%d sources)"
            % (epic["title"] or epic["slug"], epic["total_sources"]),
            flush=True,
        )

        titles = fetch_epic_titles(conn, epic["id"])
        if len(titles) < MIN_TITLES:
            print("  Skipping: only %d titles (min %d)" % (len(titles), MIN_TITLES))
            continue
        print("  %d titles" % len(titles), flush=True)

        # Pass 1: Discover frames
        sampled = sample_titles_for_discovery(titles)
        print("  Sampled %d titles for discovery" % len(sampled))

        frames, tok_in, tok_out = pass1_discover_frames(
            epic["title"], epic["summary"], args.month, sampled
        )
        grand_tok_in += tok_in
        grand_tok_out += tok_out

        for f in frames:
            print("    [%s] %s" % (f["label"], f["description"]))

        if args.dry_run:
            continue

        # Pass 2: Classify all titles
        classifications, tok_in, tok_out = pass2_classify_titles(
            epic["title"], frames, titles
        )
        grand_tok_in += tok_in
        grand_tok_out += tok_out

        # Aggregate and save
        narratives = aggregate_results(frames, classifications, titles)
        print("  %d narratives with titles:" % len(narratives))
        for n in narratives:
            print(
                "    %s: %d titles, top sources: %s"
                % (n["label"], n["title_count"], ", ".join(n["top_sources"][:3]))
            )

        save_narratives(conn, epic["id"], narratives)
        print("  Saved to DB", flush=True)

        time.sleep(1)  # rate limit courtesy

    conn.close()
    print("\nDone. Total tokens: %d in, %d out" % (grand_tok_in, grand_tok_out))


if __name__ == "__main__":
    main()
