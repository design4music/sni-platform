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

    // Check if narratives already exist (prevent duplicates)
    const existing = await query<{ id: string; label: string; title_count: number }>(
      `SELECT id, label, title_count FROM narratives
       WHERE entity_type = $1 AND entity_id = $2
       ORDER BY title_count DESC`,
      [entity_type, entity_id]
    );

    if (existing.length > 0) {
      return NextResponse.json({
        narratives: existing,
        first_narrative_id: existing[0].id,
      });
    }

    // Call Python extraction service
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
      narratives,
      first_narrative_id: narratives[0]?.id || null,
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
