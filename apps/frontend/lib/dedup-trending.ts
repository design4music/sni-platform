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
 * Group trending events by title similarity.
 * The highest-scoring event becomes the primary; similar events from other
 * centroids are attached as perspectives (input must be pre-sorted by score).
 * Threshold 0.55 catches cross-centroid near-duplicates while keeping distinct stories.
 */
export function dedupTrendingEvents(events: TrendingEvent[], threshold = 0.55): TrendingEvent[] {
  const groups: TrendingEvent[] = [];
  for (const ev of events) {
    const match = groups.find(k => titleDice(k.title, ev.title) >= threshold);
    if (match) {
      // Attach as perspective if from a different centroid
      if (ev.centroid_id !== match.centroid_id) {
        if (!match.perspectives) match.perspectives = [];
        match.perspectives.push(ev);
      }
    } else {
      groups.push({ ...ev });
    }
  }
  return groups;
}
