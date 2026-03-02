import type { TrendingEvent } from './types';

/** Word-level Dice coefficient between two titles (words > 2 chars) */
function titleDice(a: string, b: string): number {
  const words = (s: string) =>
    new Set(s.toLowerCase().replace(/[^\w\s]/g, '').split(/\s+/).filter(w => w.length > 2));
  const setA = words(a);
  const setB = words(b);
  if (setA.size === 0 && setB.size === 0) return 0;
  let overlap = 0;
  for (const w of setA) if (setB.has(w)) overlap++;
  return (2 * overlap) / (setA.size + setB.size);
}

/**
 * Deduplicate trending events by title similarity.
 * Keeps the highest-scoring event from each cluster (input must be pre-sorted by score).
 * Threshold 0.55 catches cross-centroid near-duplicates while keeping distinct stories.
 */
export function dedupTrendingEvents(events: TrendingEvent[], threshold = 0.55): TrendingEvent[] {
  const kept: TrendingEvent[] = [];
  for (const ev of events) {
    if (!kept.some(k => titleDice(k.title, ev.title) >= threshold)) {
      kept.push(ev);
    }
  }
  return kept;
}
