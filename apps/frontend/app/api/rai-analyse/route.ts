import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/auth';
import { query } from '@/lib/db';
import {
  buildAnalysisPrompt,
  callDeepSeek,
  parseAnalysisResponse,
  selectModules,
  resolveModules,
  CORE_MODULE_IDS,
  NarrativeInput,
  AnalysisContext,
} from '@/lib/rai-engine';
import type { SignalStats } from '@/lib/types';

export async function POST(req: NextRequest) {
  try {
    // Auth check
    const session = await auth();
    if (!session?.user) {
      return NextResponse.json({ error: 'Sign in to analyse' }, { status: 401 });
    }

    const { narrative_id } = await req.json();
    if (!narrative_id) {
      return NextResponse.json({ error: 'Missing narrative_id' }, { status: 400 });
    }

    // Check cache: if already analysed, return immediately
    const cached = await query<{
      rai_full_analysis: unknown;
      rai_adequacy: number | null;
      rai_synthesis: string | null;
      rai_conflicts: string[] | null;
      rai_blind_spots: string[] | null;
      rai_shifts: unknown;
    }>(
      `SELECT rai_full_analysis, rai_adequacy, rai_synthesis, rai_conflicts,
              rai_blind_spots, rai_shifts
       FROM narratives WHERE id = $1`,
      [narrative_id]
    );

    if (cached.length === 0) {
      return NextResponse.json({ error: 'Narrative not found' }, { status: 404 });
    }

    if (cached[0].rai_full_analysis) {
      // Column is TEXT, so parse if it's a JSON string
      let sections = cached[0].rai_full_analysis;
      if (typeof sections === 'string') {
        try { sections = JSON.parse(sections); } catch { /* use as-is */ }
      }
      return NextResponse.json({
        sections,
        scores: {
          adequacy: cached[0].rai_adequacy,
          synthesis: cached[0].rai_synthesis,
          conflicts: cached[0].rai_conflicts,
          blind_spots: cached[0].rai_blind_spots,
          shifts: cached[0].rai_shifts,
        },
      });
    }

    // Fetch narrative + parent entity context
    const rows = await query<{
      label: string;
      moral_frame: string | null;
      description: string | null;
      sample_titles: unknown;
      top_sources: string[] | null;
      title_count: number;
      entity_type: string;
      signal_stats: SignalStats | null;
      centroid_id: string | null;
      centroid_name: string | null;
      track: string | null;
      event_title: string | null;
    }>(
      `SELECT n.label, n.moral_frame, n.description, n.sample_titles,
              n.top_sources, n.title_count, n.entity_type, n.signal_stats,
              COALESCE(ct.centroid_id, c.centroid_id) as centroid_id,
              c2.label as centroid_name,
              COALESCE(ct.track, c.track) as track,
              COALESCE(e.title, e.topic_core) as event_title
       FROM narratives n
       LEFT JOIN events_v3 e ON n.entity_type = 'event' AND n.entity_id = e.id
       LEFT JOIN ctm ct ON n.entity_type = 'event' AND e.ctm_id = ct.id
       LEFT JOIN ctm c ON n.entity_type = 'ctm' AND n.entity_id = c.id
       LEFT JOIN centroids_v3 c2 ON c2.id = COALESCE(ct.centroid_id, c.centroid_id)
       WHERE n.id = $1`,
      [narrative_id]
    );

    if (rows.length === 0) {
      return NextResponse.json({ error: 'Narrative not found' }, { status: 404 });
    }

    const row = rows[0];

    // Build narrative + context for prompt
    const sampleTitles = typeof row.sample_titles === 'string'
      ? JSON.parse(row.sample_titles)
      : row.sample_titles || [];

    const narrative: NarrativeInput = {
      label: row.label,
      moral_frame: row.moral_frame,
      description: row.description,
      sample_titles: sampleTitles,
      source_count: row.title_count,
      top_sources: row.top_sources || [],
    };

    const context: AnalysisContext = {
      centroid_id: row.centroid_id || '',
      centroid_name: row.centroid_name || '',
      track: row.track || '',
      event_title: row.event_title || '',
      entity_type: row.entity_type,
    };

    // Parse signal_stats (JSONB comes as object or string)
    let stats: SignalStats | null = null;
    if (row.signal_stats) {
      stats = typeof row.signal_stats === 'string'
        ? JSON.parse(row.signal_stats)
        : row.signal_stats;
    }

    // Select modules: 3 core + 3 LLM-selected
    const selectedIds = await selectModules(narrative, context, stats);
    const modules = resolveModules([...CORE_MODULE_IDS, ...selectedIds]);

    // Build prompt, call DeepSeek, parse response
    const prompt = buildAnalysisPrompt(narrative, context, modules, stats);
    const raw = await callDeepSeek(prompt);
    const { sections, scores } = parseAnalysisResponse(raw);

    if (sections.length === 0) {
      console.error('DeepSeek returned no parseable sections');
      return NextResponse.json({ error: 'Analysis returned no content' }, { status: 502 });
    }

    // Save to DB
    await query(
      `UPDATE narratives SET
        rai_full_analysis = $2,
        rai_adequacy = $3,
        rai_synthesis = $4,
        rai_conflicts = $5,
        rai_blind_spots = $6,
        rai_shifts = $7,
        rai_analyzed_at = NOW()
       WHERE id = $1`,
      [
        narrative_id,
        JSON.stringify(sections),
        scores.adequacy ?? null,
        scores.synthesis ?? null,
        scores.conflicts?.length ? scores.conflicts : null,
        scores.blind_spots?.length ? scores.blind_spots : null,
        scores.bias_detected != null || scores.coherence != null
          ? JSON.stringify(scores)
          : null,
      ]
    );

    return NextResponse.json({ sections, scores });
  } catch (err: unknown) {
    if (err instanceof Error && err.name === 'AbortError') {
      return NextResponse.json({ error: 'Analysis timed out' }, { status: 504 });
    }
    console.error('RAI analyse error:', err);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
