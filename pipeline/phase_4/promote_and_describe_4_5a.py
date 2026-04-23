"""Phase 4.5a (day-centric rewrite, 2026-04-15)

Promote top-N clusters per day and generate LLM prose (title + optional description).
Replaces the full-scan generate_event_summaries_4_5a.py for the new day-centric flow.

Pipeline per CTM:
  1. Rank events per (ctm_id, date) by source_count DESC, first_date ASC
  2. Mark top TOP_CLUSTERS_PER_DAY as is_promoted=true
  3. For each promoted event choose a path:
     a. source_count >= 5: LLM title + LLM description (EN+DE in one call)
     b. source_count <  5, has English source: mechanical title (pick most central English),
        queue for DE batch translation. No description.
     c. source_count <  5, no English source: LLM title only (EN+DE). No description.
  4. Run LLM calls (async, concurrent)
  5. Batch-translate mechanical EN titles to DE
  6. Write back to events_v3: title, title_de, summary, summary_de, is_promoted=true
"""

import argparse
import asyncio
import json
import sys
from collections import Counter
from pathlib import Path

import httpx
import psycopg2

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.config import (
    DE_TITLE_BATCH_SIZE,
    LLM_CLUSTER_TITLE_MIN_SOURCES,
    TOP_CLUSTERS_PER_DAY,
    config,
)
from core.llm_logger import log_llm_call
from core.llm_utils import async_check_rate_limit, extract_json, fix_role_hallucinations
from core.prompts import (
    DE_TITLE_BATCH_SYSTEM_PROMPT,
    DE_TITLE_BATCH_USER_PROMPT,
    EVENT_SUMMARY_PROMPT_MAXI,
    EVENT_SUMMARY_PROMPT_MEDIUM,
    EVENT_SUMMARY_PROMPT_MINI,
    EVENT_SUMMARY_PROMPT_TITLE_ONLY,
    EVENT_SUMMARY_USER_PROMPT,
    EVENT_SUMMARY_USER_PROMPT_TITLE,
)

MAX_TITLES_TO_LLM = 10
LLM_CONCURRENCY = 6


def get_conn():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


# ---------------------------------------------------------------------------
# STAGE 1: Ranking + promotion flag
# ---------------------------------------------------------------------------


def promote_top_clusters(conn, ctm_id: str) -> int:
    """One-way promotion: mark top-N unpromoted events per (ctm_id, date).

    Already-promoted events stay promoted (never demoted). Only NEW events
    that rank in the top-N for their day get promoted. This is safe to call
    after every incremental clustering cycle — existing LLM prose and
    daily briefs are never invalidated.

    Returns: total promoted count (existing + newly promoted).
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            WITH ranked AS (
                SELECT id,
                       row_number() OVER (
                           PARTITION BY date
                           ORDER BY source_batch_count DESC, first_seen ASC, id ASC
                       ) AS rnk
                  FROM events_v3
                 WHERE ctm_id = %s
                   AND merged_into IS NULL
            )
            UPDATE events_v3 e
               SET is_promoted = true
              FROM ranked r
             WHERE e.id = r.id
               AND r.rnk <= %s
               AND e.is_promoted = false
            """,
            (ctm_id, TOP_CLUSTERS_PER_DAY),
        )
        newly = cur.rowcount
        cur.execute(
            "SELECT COUNT(*) FROM events_v3 WHERE ctm_id = %s AND is_promoted = true",
            (ctm_id,),
        )
        total = cur.fetchone()[0]
    conn.commit()
    if newly > 0:
        print("  promoted %d new (total %d)" % (newly, total))
    return total


# ---------------------------------------------------------------------------
# STAGE 2: Load promoted events with their titles
# ---------------------------------------------------------------------------


def load_promoted_events(conn, ctm_id: str) -> list:
    """Return promoted events with titles + language per title."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT e.id, e.source_batch_count
              FROM events_v3 e
             WHERE e.ctm_id = %s AND e.is_promoted = true
             ORDER BY e.date, e.source_batch_count DESC
            """,
            (ctm_id,),
        )
        events = [{"id": str(r[0]), "source_count": r[1]} for r in cur.fetchall()]

        for ev in events:
            cur.execute(
                """
                SELECT t.id::text, t.title_display, t.detected_language, t.pubdate_utc
                  FROM event_v3_titles evt
                  JOIN titles_v3 t ON t.id = evt.title_id
                 WHERE evt.event_id = %s
                """,
                (ev["id"],),
            )
            titles = []
            for tid, td, lang, pub in cur.fetchall():
                titles.append(
                    {
                        "id": tid,
                        "text": td or "",
                        "lang": (lang or "").lower(),
                        "pubdate": pub,
                    }
                )
            ev["titles"] = titles

        # Backbone signals (simple: top persons / orgs / places per event)
        for ev in events:
            cur.execute(
                """
                SELECT tl.persons, tl.orgs, tl.places, tl.named_events
                  FROM event_v3_titles evt
                  JOIN title_labels tl ON tl.title_id = evt.title_id
                 WHERE evt.event_id = %s
                """,
                (ev["id"],),
            )
            persons, orgs, places, named = Counter(), Counter(), Counter(), Counter()
            for row in cur.fetchall():
                for p in row[0] or []:
                    persons[p] += 1
                for o in row[1] or []:
                    orgs[o] += 1
                for pl in row[2] or []:
                    places[pl] += 1
                for ne in row[3] or []:
                    named[ne] += 1
            ev["backbone"] = {
                "persons": [p for p, _ in persons.most_common(3)],
                "orgs": [o for o, _ in orgs.most_common(3)],
                "places": [pl for pl, _ in places.most_common(3)],
                "named_events": [ne for ne, _ in named.most_common(2)],
            }
    return events


# ---------------------------------------------------------------------------
# STAGE 3: Path decision
# ---------------------------------------------------------------------------


def classify_event(ev: dict) -> str:
    """Return one of: 'llm_full', 'llm_title_only', 'mechanical_en'."""
    src = ev["source_count"]
    has_english = any(t["lang"] == "en" for t in ev["titles"])
    if src >= LLM_CLUSTER_TITLE_MIN_SOURCES:
        return "llm_full"
    if has_english:
        return "mechanical_en"
    return "llm_title_only"


# ---------------------------------------------------------------------------
# STAGE 4: Text selection (mechanical English pick)
# ---------------------------------------------------------------------------


def select_core_titles(
    titles: list[str], max_core: int = MAX_TITLES_TO_LLM
) -> list[int]:
    """Centrality ranking: titles with the most shared discriminating content words."""
    if len(titles) <= max_core:
        return list(range(len(titles)))
    n = len(titles)
    word_sets = []
    for t in titles:
        ws = set()
        for w in t.lower().split():
            w = w.strip(".,;:!?\"'()[]{}|-")
            if w and len(w) > 2:
                ws.add(w)
        word_sets.append(ws)
    df = Counter()
    for ws in word_sets:
        for w in ws:
            df[w] += 1
    min_df = max(2, int(n * 0.02))
    max_df = int(n * 0.6)
    valid = {w for w, c in df.items() if min_df <= c <= max_df}
    scores = []
    for ws in word_sets:
        content = ws & valid
        scores.append(sum(df[w] for w in content) / max(len(content), 1))
    return sorted(range(n), key=lambda i: -scores[i])[:max_core]


def pick_mechanical_english_title(titles: list[dict]) -> str:
    """Pick most-central English title for small clusters without LLM."""
    english = [t for t in titles if t["lang"] == "en" and t["text"]]
    if not english:
        return ""
    if len(english) == 1:
        return english[0]["text"]
    texts = [t["text"] for t in english]
    ranked = select_core_titles(texts, max_core=1)
    return english[ranked[0]]["text"]


# ---------------------------------------------------------------------------
# STAGE 5: LLM calls
# ---------------------------------------------------------------------------


async def _call_llm(payload: dict, phase: str = "event_prose") -> dict:
    import time as _time

    headers = {
        "Authorization": "Bearer %s" % config.deepseek_api_key,
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=120) as client:
        for attempt in range(3):
            t0 = _time.time()
            response = await client.post(
                "%s/chat/completions" % config.deepseek_api_url,
                headers=headers,
                json=payload,
            )
            if await async_check_rate_limit(response, attempt):
                continue
            if response.status_code != 200:
                raise RuntimeError(
                    "LLM error %d: %s" % (response.status_code, response.text[:200])
                )
            data = response.json()
            log_llm_call(phase, data.get("usage"), int((_time.time() - t0) * 1000))
            return extract_json(data["choices"][0]["message"]["content"])
        raise RuntimeError("LLM retries exhausted")


def _format_titles(titles_sample: list[dict]) -> str:
    return "\n".join("- %s" % t["text"] for t in titles_sample if t["text"])


def _format_backbone(backbone: dict) -> str:
    parts = []
    if backbone["persons"]:
        parts.append("persons=%s" % ",".join(backbone["persons"]))
    if backbone["orgs"]:
        parts.append("orgs=%s" % ",".join(backbone["orgs"]))
    if backbone["places"]:
        parts.append("places=%s" % ",".join(backbone["places"]))
    if backbone["named_events"]:
        parts.append("named=%s" % ",".join(backbone["named_events"]))
    return "; ".join(parts) or "none"


async def llm_title_and_summary(ev: dict) -> dict:
    """Full title + summary generation (EN+DE). Source count >= 5."""
    texts = [t["text"] for t in ev["titles"] if t["text"]]
    core_idx = select_core_titles(texts, max_core=MAX_TITLES_TO_LLM)
    sample = [ev["titles"][i] for i in core_idx]
    num = len(texts)

    if num <= 10:
        system_prompt = EVENT_SUMMARY_PROMPT_MINI
        max_tokens = 600
    elif num <= 50:
        system_prompt = EVENT_SUMMARY_PROMPT_MEDIUM
        max_tokens = 1000
    else:
        system_prompt = EVENT_SUMMARY_PROMPT_MAXI
        max_tokens = 1400

    user_prompt = EVENT_SUMMARY_USER_PROMPT.format(
        num_titles=num,
        titles_text=_format_titles(sample),
        backbone_signals=_format_backbone(ev["backbone"]),
    )
    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.4,
        "max_tokens": max_tokens,
    }
    result = await _call_llm(payload, phase="event_prose_full")
    return {
        "title_en": fix_role_hallucinations((result.get("title_en") or "").strip()),
        "title_de": (result.get("title_de") or "").strip(),
        "summary_en": fix_role_hallucinations((result.get("summary_en") or "").strip()),
        "summary_de": (result.get("summary_de") or "").strip(),
        "coherent": bool(result.get("coherent", True)),
    }


async def llm_title_only(ev: dict) -> dict:
    """Title-only generation (EN+DE). Source count < 5, no English source."""
    texts = [t["text"] for t in ev["titles"] if t["text"]]
    core_idx = select_core_titles(texts, max_core=MAX_TITLES_TO_LLM)
    sample = [ev["titles"][i] for i in core_idx]
    user_prompt = EVENT_SUMMARY_USER_PROMPT_TITLE.format(
        num_titles=len(texts),
        titles_text=_format_titles(sample),
    )
    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": EVENT_SUMMARY_PROMPT_TITLE_ONLY},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.4,
        "max_tokens": 200,
    }
    result = await _call_llm(payload, phase="event_prose_title")
    return {
        "title_en": fix_role_hallucinations((result.get("title_en") or "").strip()),
        "title_de": (result.get("title_de") or "").strip(),
        "summary_en": "",
        "summary_de": "",
        "coherent": bool(result.get("coherent", True)),
    }


async def batch_translate_titles_de(titles: list[str]) -> list[str]:
    """Batch-translate EN titles to DE via numbered-line format (JSON-free)."""
    if not titles:
        return []
    out: list[str] = [""] * len(titles)
    headers = {
        "Authorization": "Bearer %s" % config.deepseek_api_key,
        "Content-Type": "application/json",
    }
    for i in range(0, len(titles), DE_TITLE_BATCH_SIZE):
        batch = titles[i : i + DE_TITLE_BATCH_SIZE]
        # 1-based numbering for better LLM compliance
        lines_in = "\n".join("%d. %s" % (k + 1, t) for k, t in enumerate(batch))
        payload = {
            "model": config.llm_model,
            "messages": [
                {"role": "system", "content": DE_TITLE_BATCH_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": DE_TITLE_BATCH_USER_PROMPT.format(titles_text=lines_in),
                },
            ],
            "temperature": 0.2,
            "max_tokens": DE_TITLE_BATCH_SIZE * 80,
        }
        try:
            import time as _time

            async with httpx.AsyncClient(timeout=120) as client:
                for attempt in range(3):
                    t0 = _time.time()
                    response = await client.post(
                        "%s/chat/completions" % config.deepseek_api_url,
                        headers=headers,
                        json=payload,
                    )
                    if await async_check_rate_limit(response, attempt):
                        continue
                    if response.status_code != 200:
                        raise RuntimeError("LLM error %d" % response.status_code)
                    data = response.json()
                    log_llm_call(
                        "de_batch_translate",
                        data.get("usage"),
                        int((_time.time() - t0) * 1000),
                    )
                    content = data["choices"][0]["message"]["content"].strip()
                    break
                else:
                    continue
            # Parse numbered lines: "1. Translation" / "12. Translation"
            for line in content.split("\n"):
                line = line.strip()
                if not line:
                    continue
                parts = line.split(". ", 1)
                if len(parts) == 2 and parts[0].strip().isdigit():
                    num = int(parts[0].strip()) - 1
                    if 0 <= num < len(batch):
                        out[i + num] = parts[1].strip()
        except Exception as e:
            print("  DE batch error: %s" % e)
    return out


# ---------------------------------------------------------------------------
# STAGE 6: Orchestration
# ---------------------------------------------------------------------------


def promote_ctm(ctm_id: str) -> int:
    """Mechanical promotion only: rank + set is_promoted. No LLM. Instant.

    Safe to call from Slot 3 after clustering + merge. Idempotent.
    """
    conn = get_conn()
    try:
        return promote_top_clusters(conn, ctm_id)
    finally:
        conn.close()


async def describe_promoted_events(ctm_id: str) -> dict:
    """LLM prose for promoted events that LACK titles/descriptions.

    Only processes events where title_de IS NULL (never LLM'd before)
    or source_count crossed the 5-source threshold since last run.
    Called from Slot 4 enrichment.
    """
    conn = get_conn()
    try:
        events = load_promoted_events(conn, ctm_id)
        # Filter to events that need LLM work
        events = [
            ev
            for ev in events
            if not any(t["lang"] == "de" and t["text"] for t in ev.get("titles", []))
            # Proxy: if title_de is set in DB, this event was already LLM'd
        ]
        # Re-check from DB which promoted events lack title_de
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id::text FROM events_v3
                   WHERE ctm_id = %s AND is_promoted = true AND title_de IS NULL""",
                (ctm_id,),
            )
            needs_prose = {r[0] for r in cur.fetchall()}
        events = [
            ev for ev in load_promoted_events(conn, ctm_id) if ev["id"] in needs_prose
        ]

        if not events:
            return {"needs_prose": 0, "written": 0}

        print("  %d promoted events need LLM prose" % len(events))

        # classify
        llm_full, llm_title, mech = [], [], []
        for ev in events:
            path = classify_event(ev)
            if path == "llm_full":
                llm_full.append(ev)
            elif path == "llm_title_only":
                llm_title.append(ev)
            else:
                mech.append(ev)
        print(
            "  paths: llm_full=%d  llm_title=%d  mechanical_en=%d"
            % (len(llm_full), len(llm_title), len(mech))
        )

        # Mechanical path: pick English title now
        for ev in mech:
            ev["result"] = {
                "title_en": pick_mechanical_english_title(ev["titles"]),
                "title_de": "",
                "summary_en": "",
                "summary_de": "",
                "coherent": True,
            }

        # LLM paths: run async with concurrency limit
        sem = asyncio.Semaphore(LLM_CONCURRENCY)

        async def run_with_sem(coro, ev):
            async with sem:
                try:
                    ev["result"] = await coro
                except Exception as e:
                    print("  LLM fail event=%s: %s" % (ev["id"][:8], e))
                    ev["result"] = None

        tasks = []
        for ev in llm_full:
            tasks.append(run_with_sem(llm_title_and_summary(ev), ev))
        for ev in llm_title:
            tasks.append(run_with_sem(llm_title_only(ev), ev))
        if tasks:
            await asyncio.gather(*tasks)

        # Batch DE translate for mechanical path
        if mech:
            en_titles = [ev["result"]["title_en"] for ev in mech]
            de_titles = await batch_translate_titles_de(en_titles)
            for ev, de in zip(mech, de_titles):
                ev["result"]["title_de"] = de

        # Write back
        written = 0
        with conn.cursor() as cur:
            for ev in events:
                r = ev.get("result")
                if not r:
                    continue
                cur.execute(
                    """
                    UPDATE events_v3
                       SET title      = %s,
                           title_de   = %s,
                           summary    = %s,
                           summary_de = %s,
                           coherence_check = %s,
                           updated_at = NOW()
                     WHERE id = %s
                    """,
                    (
                        r["title_en"] or None,
                        r["title_de"] or None,
                        r["summary_en"] or None,
                        r["summary_de"] or None,
                        json.dumps({"coherent": r["coherent"]}),
                        ev["id"],
                    ),
                )
                written += 1
        conn.commit()
        return {
            "needs_prose": len(needs_prose),
            "llm_full": len(llm_full),
            "llm_title": len(llm_title),
            "mechanical_en": len(mech),
            "written": written,
        }
    finally:
        conn.close()


async def process_ctm(ctm_id: str) -> dict:
    """Combined promote + describe for batch/rerun scripts."""
    promoted = promote_ctm(ctm_id)
    stats = await describe_promoted_events(ctm_id)
    stats["promoted"] = promoted
    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ctm-id", required=True, help="CTM UUID to process")
    parser.add_argument(
        "--promote-only",
        action="store_true",
        help="Only promote (mechanical), skip LLM prose",
    )
    args = parser.parse_args()
    if args.promote_only:
        n = promote_ctm(args.ctm_id)
        print("DONE promoted=%d" % n)
    else:
        stats = asyncio.run(process_ctm(args.ctm_id))
        print("DONE", stats)


if __name__ == "__main__":
    main()
