import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/auth';
import { query } from '@/lib/db';

const EXTRACTION_API_URL = process.env.EXTRACTION_API_URL || '';
const EXTRACTION_API_KEY = process.env.EXTRACTION_API_KEY || '';

export async function POST(req: NextRequest) {
  try {
    const session = await auth();
    if (!session?.user) {
      return NextResponse.json({ error: 'Sign in required' }, { status: 401 });
    }

    const { entity_type, entity_id } = await req.json();
    if (!entity_type || !entity_id) {
      return NextResponse.json({ error: 'Missing entity_type or entity_id' }, { status: 400 });
    }

    if (!['event', 'ctm'].includes(entity_type)) {
      return NextResponse.json({ error: 'entity_type must be event or ctm' }, { status: 400 });
    }

    // Check for existing stance-clustered narratives
    const stanceRows = await query<{ id: string; label: string; title_count: number; signal_stats: Record<string, unknown> | null }>(
      `SELECT id, label, title_count, signal_stats FROM narratives
       WHERE entity_type = $1 AND entity_id = $2
         AND extraction_method = 'stance_clustered'
       ORDER BY title_count DESC`,
      [entity_type, entity_id]
    );

    if (stanceRows.length > 0) {
      // Staleness check: compare source count at extraction vs current
      const extractedCount = Number(stanceRows[0].signal_stats?.source_count_at_extraction || 0);

      let currentCount = 0;
      if (entity_type === 'event') {
        const rows = await query<{ source_batch_count: number }>(
          'SELECT source_batch_count FROM events_v3 WHERE id = $1',
          [entity_id]
        );
        currentCount = rows[0]?.source_batch_count || 0;
      }

      const growth = currentCount - extractedCount;
      const growthPct = extractedCount > 0 ? growth / extractedCount : 0;
      const isStale = growth >= 100 || growthPct >= 0.5;

      if (!isStale) {
        return NextResponse.json({
          status: 'cached',
          has_stance: true,
          narratives: stanceRows,
          first_narrative_id: stanceRows[0].id,
        });
      }

      // Stale -- force re-extraction
      const resp = await fetch(`${EXTRACTION_API_URL}/extract`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${EXTRACTION_API_KEY}`,
        },
        body: JSON.stringify({ entity_type, entity_id, force: true }),
      });

      if (!resp.ok) {
        const errBody = await resp.json().catch(() => ({ detail: 'Re-extraction failed' }));
        return NextResponse.json(
          { error: errBody.detail || 'Re-extraction failed' },
          { status: resp.status }
        );
      }

      const data = await resp.json();
      const narratives = data.narratives || [];
      return NextResponse.json({
        status: 'extracted',
        has_stance: true,
        narratives,
        first_narrative_id: narratives[0]?.id || null,
      });
    }

    // No stance narratives -- extract fresh
    const resp = await fetch(`${EXTRACTION_API_URL}/extract`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${EXTRACTION_API_KEY}`,
      },
      body: JSON.stringify({ entity_type, entity_id }),
    });

    if (!resp.ok) {
      const errBody = await resp.json().catch(() => ({ detail: 'Extraction failed' }));
      return NextResponse.json(
        { error: errBody.detail || 'Extraction failed' },
        { status: resp.status }
      );
    }

    const data = await resp.json();

    // Coherence check: LLM detected unrelated topics
    if (data.coherent === false) {
      return NextResponse.json({
        coherent: false,
        reason: data.reason || 'Headlines cover unrelated topics',
        topics: data.topics || [],
      });
    }

    const narratives = data.narratives || [];

    return NextResponse.json({
      status: 'extracted',
      has_stance: true,
      narratives,
      first_narrative_id: narratives[0]?.id || null,
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    console.error('[extract-narratives] error:', err);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
