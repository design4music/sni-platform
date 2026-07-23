// Client-safe shared bits for friction-nodes UI: colour palette + the
// type definitions consumed by both server queries and client components.
//
// lib/friction-nodes.ts (server-only, imports pg) re-exports from here so
// existing import paths still work, but client components MUST import
// from this file to avoid pulling node-only modules into the browser bundle.

export interface FrictionNode {
  id: string;
  name: string;
  description: string | null;
  editorial_summary: string | null;
  centroid_ids: string[];
  fn_type: 'atomic' | 'theater';
  member_fn_ids: string[];
}

/** Compact pointer to a parent theater (for atomic-FN page header pill). */
export interface TheaterPointer {
  id: string;
  name: string;
}

/** Brick row for a constituent atomic FN, used on theater landing pages. */
export interface TheaterMemberFn {
  id: string;
  name: string;
  description: string | null;
  editorial_summary: string | null;
  event_count: number;
  /** Stance bricks: ordered, colored. */
  stances: {
    narrative_id: string;
    label: string;
    display_order: number;
    match_count: number;
    /** Reader-facing stance: -2..+2 (mirrors outlet_entity_stance.stance). */
    stance: number | null;
  }[];
}

export interface SampleTitle {
  id: string;
  title: string;
  publisher_name: string | null;
  pubdate_utc: string;
}

export interface NarrativeOnFn {
  narrative_id: string;
  narrative_name: string;
  narrative_claim: string;
  actor_centroids: string[];
  framing_keywords: string[];
  publishers: string[];          // editorial outlets carrying this stance (curated)
  stance_label: string;
  /** Reader-facing stance: -2..+2 (mirrors outlet_entity_stance.stance). */
  stance: number | null;
  /** Parent position (SPEC v2); the card links up to /narratives/[position_id]. */
  position_id: string | null;
  position_name: string | null;
  display_order: number;
  match_count: number;
  sample_titles: SampleTitle[];
}

export interface FnRecentEvent {
  id: string;
  date: string;            // YYYY-MM-DD
  title: string;
  source_count: number;
  importance: number | null;
}

export interface FnEventVolumePoint {
  /** ISO Monday-of-week (YYYY-MM-DD). */
  week: string;
  count: number;
}

/** Per-week bucket: total event count + top N events for that week. */
export interface FnWeekBucket {
  week: string;        // ISO Monday-of-week, YYYY-MM-DD
  total: number;       // total events that week (full count, not capped)
  events: FnRecentEvent[]; // top N events that week, ordered by importance proxy
}

/** Compact lookup for resolving a centroid_id to a display label + flag. */
export interface CentroidLookupEntry {
  id: string;
  label: string;
  iso2: string | null;     // first iso_code if any (for FlagImg)
}

export interface FrictionNodeView {
  fn: FrictionNode;
  narratives: NarrativeOnFn[];
  event_count: number;
}

export interface NarrativeWeeklyPoint {
  week: string;
  counts: Record<string, number>;
  total: number;
}

/**
 * 5-step stance palette, mirrors OutletStanceBricks.stanceHue.
 *   -2 = #b91c1c  red-700      strong criticism
 *   -1 = #ef4444  red-500      criticism
 *    0 = #71717a  zinc-500     neutral / mixed
 *   +1 = #10b981  emerald-500  support
 *   +2 = #15803d  green-700    strong support
 */
export function colorForNarrative(stance: number | null): string {
  if (stance == null) return '#71717a';
  if (stance <= -2) return '#b91c1c';
  if (stance === -1) return '#ef4444';
  if (stance === 0) return '#71717a';
  if (stance === 1) return '#10b981';
  return '#15803d';
}

/**
 * Card/brick display filter: the first two narratives (by display_order --
 * normally the dominant pro/con pair) always render. A third-or-later
 * narrative (typically a minority nuance stance) is hidden until it
 * accumulates at least `minCount` attributed titles, so a newly-added thin
 * narrative doesn't render as a conspicuously empty card next to populated
 * ones. It reappears on its own once the daemon's incremental attribution
 * crosses the threshold -- no manual toggle needed. Does not affect
 * page-level stats (e.g. "competing narratives" counts) -- apply only to
 * the arrays passed into FrictionNodeNarrativeBricks/Cards.
 */
export function filterNarrativesForDisplay<T extends { match_count: number }>(
  narratives: T[],
  minCount = 5,
): T[] {
  return narratives.filter((n, i) => i < 2 || n.match_count >= minCount);
}
