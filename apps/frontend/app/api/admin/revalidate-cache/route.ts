/**
 * POST /api/admin/revalidate-cache
 *
 * Drops the in-memory query cache (apps/frontend/lib/cache.ts) so the
 * next request repopulates from the DB. Use after force-refreshing
 * `mv_*` tables on the worker — without this the Node process serves
 * stale blobs for up to 12h (the cached() TTL).
 *
 * Auth: header `x-revalidate-token: <REVALIDATE_API_KEY>`.
 *
 * Body: optional JSON `{ "prefix": "centroid_cal" }` to scope to one
 * cache-key prefix. Empty body clears every key in the store.
 *
 * Examples:
 *   # bust everything
 *   curl -X POST https://worldbrief.app/api/admin/revalidate-cache \
 *        -H "x-revalidate-token: $REVALIDATE_API_KEY"
 *
 *   # bust just the centroid month-view blobs
 *   curl -X POST https://worldbrief.app/api/admin/revalidate-cache \
 *        -H "x-revalidate-token: $REVALIDATE_API_KEY" \
 *        -H "content-type: application/json" \
 *        -d '{"prefix":"centroid_cal"}'
 */

import { NextRequest, NextResponse } from 'next/server';
import { clearAllCache, invalidateCache } from '@/lib/cache';

export async function POST(req: NextRequest) {
  const token = req.headers.get('x-revalidate-token');
  const expected = process.env.REVALIDATE_API_KEY;
  if (!expected) {
    return NextResponse.json(
      { error: 'REVALIDATE_API_KEY env var not set' },
      { status: 500 }
    );
  }
  if (token !== expected) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 });
  }

  let prefix: string | undefined;
  try {
    const body = await req.json().catch(() => null);
    if (body && typeof body.prefix === 'string' && body.prefix.length > 0) {
      prefix = body.prefix;
    }
  } catch {
    // empty body is fine
  }

  const cleared = prefix ? invalidateCache(prefix) : clearAllCache();

  return NextResponse.json({
    ok: true,
    revalidated_at: new Date().toISOString(),
    scope: prefix ? `prefix=${prefix}` : 'all',
    cleared,
  });
}
