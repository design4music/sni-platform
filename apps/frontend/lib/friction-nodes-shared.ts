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
  topic_keywords: string[];
  /** Event-FN gate: title must match (any actor) AND (any topic), OR (any anchor). */
  event_actor_markers: string[];
  event_topic_markers: string[];
  event_title_anchors: string[];
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
 * Stable colour palette for narratives on a single FN. Indexed by the
 * FN-narrative link's display_order (1..N). Five distinguishable vivid
 * colours that avoid the existing blue-track palette and the stance
 * red/green semantics on the outlet pages.
 *
 * Two parallel palettes:
 *   ALL_IN  — vibrant; the strategic, FN-specific contest. White text legible.
 *   STAND_BY — desaturated mid-tones ("milky"); cross-FN backdrop frames.
 *              Same hue family as the all-in slot so the visual link is
 *              preserved, but sat ~30% / luminance set so white text still
 *              passes WCAG AA against this background.
 */
export const NARRATIVE_COLORS = [
  '#ef4444', // red-500     — slot 1 (typical: hostile/existential frame)
  '#f59e0b', // amber-500   — slot 2 (typical: actor's own self-frame)
  '#38bdf8', // sky-400     — slot 3 (typical: diplomatic/preservation frame)
  '#a78bfa', // violet-400  — slot 4 (typical: systemic/multipolar frame)
  '#34d399', // emerald-400 — slot 5 (typical: hedging/regional frame)
  '#fb7185', // rose-400    — slot 6 fallback
  '#22d3ee', // cyan-400    — slot 7 fallback
] as const;

export const NARRATIVE_COLORS_MUTED = [
  '#9a6868', // muted red
  '#9a7a3f', // muted amber
  '#5f8b9a', // muted sky
  '#7d72a3', // muted violet
  '#5e9580', // muted emerald
  '#9a6873', // muted rose
  '#5b8e96', // muted cyan
] as const;

export function colorForNarrative(
  displayOrder: number,
  isStandBy = false,
): string {
  const idx = Math.max(0, (displayOrder - 1) % NARRATIVE_COLORS.length);
  return isStandBy ? NARRATIVE_COLORS_MUTED[idx] : NARRATIVE_COLORS[idx];
}
