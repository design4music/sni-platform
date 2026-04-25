/**
 * Pure slug helpers (no DB, no Node-only imports).
 *
 * Safe to import from BOTH client and server components. The DB-bound
 * helpers (resolveSlug, feedNameToSlug) live in slug-server.ts so they
 * don't drag pg into the client bundle.
 */

const UMLAUTS: Record<string, string> = {
  'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'ae', 'Ö': 'oe', 'Ü': 'ue', 'ß': 'ss',
};

/** Pure-function slugify. Mirrors scripts/backfill_feed_slugs.py exactly. */
export function generateSlug(name: string): string {
  if (!name) return '';
  let s = name;
  for (const [k, v] of Object.entries(UMLAUTS)) {
    s = s.replaceAll(k, v);
  }
  s = s.normalize('NFKD').replace(/[\u0300-\u036f]/g, '');
  s = s.toLowerCase();
  s = s.replace(/[^a-z0-9]+/g, '-');
  return s.replace(/^-+|-+$/g, '');
}
