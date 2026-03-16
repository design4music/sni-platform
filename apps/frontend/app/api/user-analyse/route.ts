export const maxDuration = 180;

import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/auth';
import { query } from '@/lib/db';
import {
  buildUserInputPrompt,
  callDeepSeek,
  parseAnalysisResponse,
  parseComparativeScores,
  selectModulesByLabels,
  resolveModules,
} from '@/lib/rai-engine';

export async function GET() {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
  }

  const rows = await query<{
    id: string;
    title: string | null;
    created_at: string;
  }>(
    `SELECT entity_id as id, title, created_at
     FROM entity_analyses
     WHERE entity_type = 'user_input' AND user_id = $1
     ORDER BY created_at DESC
     LIMIT 20`,
    [session.user.id]
  );

  return NextResponse.json(rows);
}

export async function POST(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Sign in to use the analyst' }, { status: 401 });
  }

  const { input_text } = await req.json();
  if (!input_text || typeof input_text !== 'string' || input_text.trim().length < 20) {
    return NextResponse.json(
      { error: 'Please provide at least 20 characters of text to analyse' },
      { status: 400 }
    );
  }

  const trimmed = input_text.trim().slice(0, 5000); // Cap at 5000 chars

  // Build RAI prompt for user-submitted text
  const moduleIds = selectModulesByLabels(null);
  const modules = resolveModules(moduleIds);
  const prompt = buildUserInputPrompt(trimmed, modules);

  const raw = await callDeepSeek(prompt, 4000);
  const { sections } = parseAnalysisResponse(raw);
  const scores = parseComparativeScores(raw);

  if (sections.length === 0) {
    return NextResponse.json({ error: 'Analysis returned no content' }, { status: 502 });
  }

  // Auto-generate title from first 80 chars
  const autoTitle = trimmed.length > 80 ? trimmed.slice(0, 77) + '...' : trimmed;

  // Save with entity_type = 'user_input'
  const entityId = crypto.randomUUID();
  await query(
    `INSERT INTO entity_analyses
       (entity_type, entity_id, user_id, input_text, title, cluster_count, sections, scores,
        synthesis, blind_spots, conflicts)
     VALUES ('user_input', $1, $2, $3, $4, 0, $5, $6, $7, $8, $9)`,
    [
      entityId,
      session.user.id,
      trimmed,
      autoTitle,
      JSON.stringify(sections),
      JSON.stringify(scores),
      scores.synthesis || null,
      scores.collective_blind_spots?.length ? scores.collective_blind_spots : null,
      null,
    ]
  );

  return NextResponse.json({
    id: entityId,
    sections,
    scores,
    synthesis: scores.synthesis,
    blind_spots: scores.collective_blind_spots,
  });
}
