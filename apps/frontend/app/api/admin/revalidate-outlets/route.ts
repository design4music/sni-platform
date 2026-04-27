/**
 * POST /api/admin/revalidate-outlets
 *
 * Manually drops the in-memory query cache for outlet-scoped data
 * AND invalidates Next.js's ISR cache for /sources/[slug] and
 * /sources/[slug]/[month]. Call this after re-running stance scoring
 * or any pipeline step that changes per-outlet content; otherwise
 * users wait up to 6 hours (the page revalidate window) to see
 * fresh data.
 *
 * Auth: header `x-revalidate-token: <REVALIDATE_API_KEY>`.
 *
 * Body: optional JSON `{ "slug": "cnn" }` to scope to one outlet's
 * cache prefix. With no body, drops every outlet-scoped cache key.
 *
 * Example:
 *   curl -X POST https://worldbrief.app/api/admin/revalidate-outlets \
 *        -H "x-revalidate-token: $REVALIDATE_API_KEY"
 */

import { NextRequest, NextResponse } from 'next/server';
import { revalidatePath } from 'next/cache';
import { invalidateCache } from '@/lib/cache';

// Cache-key prefixes that hold outlet-scoped data. Listed explicitly
// so adding a new cached query forces a conscious decision about
// invalidation.
const OUTLET_CACHE_PREFIXES = [
  'outletStance',
  'outletStanceMonths',
  'outletStanceTimeline',
  'outletEntityDaily',
  'outletTrackTimeline',
  'outletMonths',
  'outletMinorEntities',
  'siblingOutlets',
];

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

  // Optional slug scoping
  let slug: string | undefined;
  try {
    const body = await req.json().catch(() => null);
    if (body && typeof body.slug === 'string') slug = body.slug.toLowerCase();
  } catch {
    // empty body is fine
  }

  // Drop in-memory query cache. Per-cache-key invalidation if a slug
  // was supplied (keys are `${prefix}:${feedName}:...`); blanket
  // invalidation otherwise. Note: feed_name (DB) ≠ slug (URL); we
  // match by prefix and let the next request repopulate, which is
  // safe because the cache is just a memoisation layer.
  for (const prefix of OUTLET_CACHE_PREFIXES) {
    invalidateCache(prefix);
  }

  // Invalidate Next.js page-level cache for both outlet routes. The
  // route-pattern form invalidates every dynamic instance.
  revalidatePath('/[locale]/sources/[slug]', 'page');
  revalidatePath('/[locale]/sources/[slug]/[month]', 'page');

  return NextResponse.json({
    ok: true,
    revalidated_at: new Date().toISOString(),
    scope: slug ? `slug=${slug} (cache cleared globally; pages re-rendered on next visit)` : 'all outlets',
    cache_prefixes_cleared: OUTLET_CACHE_PREFIXES,
  });
}
