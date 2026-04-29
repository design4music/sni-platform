/**
 * POST /api/cron/revalidate-sitemap
 *
 * Forces Next to regenerate /sitemap.xml on the next request. The sitemap
 * itself is set to revalidate=false (cache indefinitely) so it never
 * regenerates inline during a user-facing request — that regeneration
 * serializes ~10k URL entries into a single XML string and was a likely
 * trigger of the 2026-04-29 production OOMs.
 *
 * Hit this endpoint once a day from a cron (GitHub Actions workflow lives
 * at .github/workflows/revalidate-sitemap.yml). Sitemap will be re-rendered
 * on the very next /sitemap.xml request after the call.
 *
 * Auth: header `x-revalidate-token: <REVALIDATE_API_KEY>`.
 *
 * Example:
 *   curl -X POST https://www.worldbrief.info/api/cron/revalidate-sitemap \
 *        -H "x-revalidate-token: $REVALIDATE_API_KEY"
 */

import { NextRequest, NextResponse } from 'next/server';
import { revalidatePath } from 'next/cache';

export async function POST(req: NextRequest) {
  const token = req.headers.get('x-revalidate-token');
  const expected = process.env.REVALIDATE_API_KEY;
  if (!expected) {
    return NextResponse.json(
      { error: 'REVALIDATE_API_KEY env var not set' },
      { status: 500 },
    );
  }
  if (token !== expected) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 });
  }

  revalidatePath('/sitemap.xml');

  return NextResponse.json({
    ok: true,
    revalidated_at: new Date().toISOString(),
    path: '/sitemap.xml',
  });
}
