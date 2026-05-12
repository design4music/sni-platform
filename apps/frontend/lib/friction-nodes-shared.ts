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
    narrative_type: 'all_in' | 'stand_by' | null;
    stance: 'support' | 'criticism' | 'neutral' | null;
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
  tier: 'operational' | 'ideological' | null;
  narrative_type: 'all_in' | 'stand_by' | null;
  framing_keywords: string[];
  publishers: string[];          // editorial outlets carrying this stance (curated)
  stance_label: string;
  /** Reader-facing stance: support / criticism / neutral (drives colour). */
  stance: 'support' | 'criticism' | 'neutral' | null;
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

export interface RelatedFn {
  id: string;
  name: string;
  shared_narratives: number;
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
 * Stance-based narrative colours.
 *
 * support  = #10b981 (emerald, pro-actor framing)
 * criticism = #ef4444 (red, anti-actor framing)
 * neutral  = #71717a (zinc, diplomatic / not-aligned)
 *
 * Stand-by narratives use desaturated variants so cross-cluster bridges
 * read as backdrop framing against the dark UI.
 */
export const STANCE_COLORS = {
  support: '#10b981',
  criticism: '#ef4444',
  neutral: '#b76f84', // dusty rose (RGB 183,111,132) — diplomatic / not-aligned bridges
} as const;

export const STANCE_COLORS_MUTED = {
  support: '#5e9580',
  criticism: '#9a6868',
  neutral: '#a66878',
} as const;

export function colorForNarrative(
  stance: 'support' | 'criticism' | 'neutral' | null,
  isStandBy = false,
): string {
  const key = stance ?? 'neutral';
  return isStandBy ? STANCE_COLORS_MUTED[key] : STANCE_COLORS[key];
}
