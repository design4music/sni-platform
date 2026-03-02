import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

const DEEPSEEK_API_KEY = process.env.DEEPSEEK_API_KEY || '';
const DEEPSEEK_API_URL = process.env.DEEPSEEK_API_URL || 'https://api.deepseek.com/v1';

// Allowed entity_type -> table/column mappings
const FIELD_MAP: Record<string, Record<string, { table: string; pk: string; src: string; dest: string }>> = {
  event: {
    summary: { table: 'events_v3', pk: 'id', src: 'summary', dest: 'summary_de' },
    title: { table: 'events_v3', pk: 'id', src: 'title', dest: 'title_de' },
  },
  ctm: {
    summary: { table: 'ctm', pk: 'id', src: 'summary_text', dest: 'summary_text_de' },
  },
  epic: {
    summary: { table: 'epics', pk: 'id', src: 'summary', dest: 'summary_de' },
    title: { table: 'epics', pk: 'id', src: 'title', dest: 'title_de' },
    timeline: { table: 'epics', pk: 'id', src: 'timeline', dest: 'timeline_de' },
  },
};

async function translateText(text: string): Promise<string | null> {
  try {
    const response = await fetch(`${DEEPSEEK_API_URL}/chat/completions`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${DEEPSEEK_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'deepseek-chat',
        messages: [
          {
            role: 'system',
            content: 'Translate the following text to German. Return only the translation, nothing else. Preserve any markdown formatting.',
          },
          { role: 'user', content: text },
        ],
        temperature: 0.2,
        max_tokens: Math.min(text.length * 2, 4000),
      }),
    });

    if (!response.ok) return null;

    const data = await response.json();
    return data.choices?.[0]?.message?.content?.trim() || null;
  } catch {
    return null;
  }
}

export async function POST(req: NextRequest) {
  try {
    const { entity_type, entity_id, field, locale } = await req.json();

    if (locale !== 'de') {
      return NextResponse.json({ error: 'Only de locale supported' }, { status: 400 });
    }

    if (!entity_type || !entity_id || !field) {
      return NextResponse.json({ error: 'Missing entity_type, entity_id, or field' }, { status: 400 });
    }

    const entityFields = FIELD_MAP[entity_type];
    if (!entityFields) {
      return NextResponse.json({ error: 'Invalid entity_type' }, { status: 400 });
    }

    const mapping = entityFields[field];
    if (!mapping) {
      return NextResponse.json({ error: 'Invalid field for entity_type' }, { status: 400 });
    }

    // Check if DE translation already exists
    const existing = await query<Record<string, string>>(
      `SELECT ${mapping.dest} FROM ${mapping.table} WHERE ${mapping.pk} = $1`,
      [entity_id]
    );

    if (!existing[0]) {
      return NextResponse.json({ error: 'Entity not found' }, { status: 404 });
    }

    if (existing[0][mapping.dest]) {
      return NextResponse.json({ translated: existing[0][mapping.dest] });
    }

    // Fetch English source text
    const srcRows = await query<Record<string, string>>(
      `SELECT ${mapping.src} FROM ${mapping.table} WHERE ${mapping.pk} = $1`,
      [entity_id]
    );

    const sourceText = srcRows[0]?.[mapping.src];
    if (!sourceText) {
      return NextResponse.json({ error: 'No source text to translate' }, { status: 404 });
    }

    // Translate
    const translated = await translateText(sourceText);
    if (!translated) {
      return NextResponse.json({ error: 'Translation failed' }, { status: 502 });
    }

    // Cache in DB
    await query(
      `UPDATE ${mapping.table} SET ${mapping.dest} = $1 WHERE ${mapping.pk} = $2`,
      [translated, entity_id]
    );

    return NextResponse.json({ translated });
  } catch (e: any) {
    return NextResponse.json({ error: e.message || 'Internal error' }, { status: 500 });
  }
}
