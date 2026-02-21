"""
On-demand Narrative Extraction API

FastAPI service wrapping existing extraction functions. Deployed on Render
as a separate web service called by the Next.js frontend.

POST /extract
  Body: {"entity_type": "event"|"ctm", "entity_id": "<UUID>"}
  Auth: Bearer <EXTRACTION_API_KEY>
"""

import json
import os
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.signal_stats import compute_ctm_stats, compute_event_stats
from pipeline.epics.build_epics import fetch_wikipedia_context
from pipeline.phase_4.extract_ctm_narratives import (
    extract_narratives_llm as ctm_extract_llm,
)
from pipeline.phase_4.extract_ctm_narratives import (
    fetch_ctm_by_id,
    fetch_ctm_titles,
    sample_titles,
)
from pipeline.phase_4.extract_ctm_narratives import (
    save_narratives as ctm_save_narratives,
)
from pipeline.phase_4.extract_event_narratives import (
    extract_narratives_llm as event_extract_llm,
)
from pipeline.phase_4.extract_event_narratives import (
    fetch_event_by_id,
    fetch_event_titles,
    get_db_connection,
)
from pipeline.phase_4.extract_event_narratives import (
    save_narratives as event_save_narratives,
)

EXTRACTION_API_KEY = os.environ.get("EXTRACTION_API_KEY", "")

COHERENCE_CHECK = """IMPORTANT: Before extracting frames, assess whether these headlines \
cover a SINGLE coherent story or MULTIPLE UNRELATED topics.

If the headlines are about different, unrelated subjects (not just different angles on \
the same story), respond ONLY with this JSON object:
{"coherent": false, "reason": "one sentence explaining the topic mix", \
"topics": ["Topic A", "Topic B"]}

Only proceed with frame extraction if the headlines genuinely cover the same overarching \
event or story from different editorial stances."""

app = FastAPI(title="SNI Extraction API")


class ExtractRequest(BaseModel):
    entity_type: str  # "event" or "ctm"
    entity_id: str


def _check_auth(request: Request):
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer ") or auth_header[7:] != EXTRACTION_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


def _frame_hint(title_count: int) -> str | None:
    """Return adaptive frame instruction based on title count."""
    if title_count < 20:
        return "Identify exactly 2 OPPOSING NARRATIVE FRAMES"
    if title_count <= 50:
        return "Identify exactly 3 OPPOSING NARRATIVE FRAMES"
    return None  # use default prompt (3-5 for CTM, exactly 3 for event)


def _is_incoherent(result) -> dict | None:
    """Check if LLM returned a coherence warning instead of frames."""
    if isinstance(result, dict) and result.get("coherent") is False:
        return {
            "coherent": False,
            "reason": result.get("reason", "Headlines cover unrelated topics"),
            "topics": result.get("topics", []),
        }
    return None


def _extract_event(conn, entity_id: str) -> dict:
    """Extract narratives for an event."""
    event = fetch_event_by_id(conn, entity_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    titles = fetch_event_titles(conn, event["id"])
    if len(titles) < 5:
        raise HTTPException(
            status_code=422,
            detail="Only %d titles - need at least 5" % len(titles),
        )

    sampled = sample_titles(titles, time_stratify=True)
    hint = _frame_hint(len(sampled))

    # Wikipedia context
    wiki_context = None
    try:
        wiki_context = fetch_wikipedia_context(event["title"], [], month_str=None)
    except Exception:
        pass

    frames, _, _ = event_extract_llm(
        event,
        sampled,
        wiki_context,
        frame_hint=hint,
        pre_instructions=COHERENCE_CHECK,
    )

    # Check coherence
    incoherent = _is_incoherent(frames)
    if incoherent:
        return incoherent

    if not frames or not isinstance(frames, list):
        raise HTTPException(status_code=500, detail="LLM returned no frames")

    event_save_narratives(
        conn, event["id"], frames, sampled, event["source_batch_count"]
    )

    # Compute signal stats for each narrative
    stats = compute_event_stats(conn, event["id"])
    if stats:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE narratives SET signal_stats = %s
                   WHERE entity_type = 'event' AND entity_id = %s""",
                (json.dumps(stats), str(event["id"])),
            )
        conn.commit()

    return {"narratives": _fetch_saved_narratives(conn, "event", entity_id)}


def _extract_ctm(conn, entity_id: str) -> dict:
    """Extract narratives for a CTM."""
    ctm = fetch_ctm_by_id(conn, entity_id)
    if not ctm:
        raise HTTPException(status_code=404, detail="CTM not found")

    titles = fetch_ctm_titles(conn, ctm["id"])
    if len(titles) < 5:
        raise HTTPException(
            status_code=422,
            detail="Only %d titles - need at least 5" % len(titles),
        )

    sampled = sample_titles(titles)
    hint = _frame_hint(len(sampled))

    frames, _, _ = ctm_extract_llm(
        ctm,
        sampled,
        frame_hint=hint,
        pre_instructions=COHERENCE_CHECK,
    )

    # Check coherence
    incoherent = _is_incoherent(frames)
    if incoherent:
        return incoherent

    if not frames or not isinstance(frames, list):
        raise HTTPException(status_code=500, detail="LLM returned no frames")

    ctm_save_narratives(conn, ctm["id"], frames, sampled)

    # Compute signal stats for each narrative
    stats = compute_ctm_stats(conn, ctm["id"])
    if stats:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE narratives SET signal_stats = %s
                   WHERE entity_type = 'ctm' AND entity_id = %s""",
                (json.dumps(stats), str(ctm["id"])),
            )
        conn.commit()

    return {"narratives": _fetch_saved_narratives(conn, "ctm", entity_id)}


def _fetch_saved_narratives(conn, entity_type: str, entity_id: str) -> list[dict]:
    """Fetch narratives just saved to return as response."""
    from psycopg2.extras import RealDictCursor

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """SELECT id, label, title_count
               FROM narratives
               WHERE entity_type = %s AND entity_id = %s
               ORDER BY title_count DESC""",
            (entity_type, str(entity_id)),
        )
        rows = cur.fetchall()
    return [
        {"id": str(r["id"]), "label": r["label"], "title_count": r["title_count"]}
        for r in rows
    ]


@app.post("/extract")
async def extract(body: ExtractRequest, request: Request):
    _check_auth(request)

    if body.entity_type not in ("event", "ctm"):
        raise HTTPException(status_code=400, detail="entity_type must be event or ctm")

    conn = get_db_connection()
    try:
        if body.entity_type == "event":
            result = _extract_event(conn, body.entity_id)
        else:
            result = _extract_ctm(conn, body.entity_id)

        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)[:300])
    finally:
        conn.close()


@app.get("/health")
async def health():
    return {"status": "ok"}
