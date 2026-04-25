/**
 * Server-only slug helpers. Imports pg via lib/db.
 * Never import this file from a 'use client' component — that pulls
 * pg/dns into the browser bundle and the build fails.
 *
 * For client-safe slug logic, use lib/slug.ts (pure functions, no DB).
 */

import { query } from './db';
import { generateSlug } from './slug';

const _slugCache = new Map<string, string | null>();

/** Resolve a slug to its feed_name. Returns null when no match. */
export async function resolveSlug(slug: string): Promise<string | null> {
  const key = slug.toLowerCase();
  if (_slugCache.has(key)) return _slugCache.get(key) ?? null;
  const rows = await query<{ name: string }>(
    'SELECT name FROM feeds WHERE slug = $1 LIMIT 1',
    [key]
  );
  const name = rows[0]?.name ?? null;
  _slugCache.set(key, name);
  return name;
}

/** feed_name → slug. Looks up the canonical column first; falls back to
 *  the deterministic generator when the row hasn't been backfilled yet. */
export async function feedNameToSlug(feedName: string): Promise<string> {
  const rows = await query<{ slug: string | null }>(
    'SELECT slug FROM feeds WHERE name = $1 LIMIT 1',
    [feedName]
  );
  return rows[0]?.slug || generateSlug(feedName);
}
