export interface Centroid {
  id: string;
  label: string;
  class: 'geo' | 'systemic';
  primary_theater?: string;
  is_superpower?: boolean;
  is_active: boolean;
  iso_codes?: string[];
  track_config_id?: string;
  description?: string;
  source_count?: number;
  month_source_count?: number;
  last_article_date?: Date;
  profile_json?: GeoBriefProfile;
  updated_at?: Date;
}

export interface GeoBriefProfile {
  schema_version: string;
  visuals?: {
    flag_iso2?: string;
    map_units_iso2?: string[];
  };
  snapshot?: Array<{
    label: string;
    value: string;
  }>;
  sections?: Array<{
    key: string;
    title: string;
    intro?: string;
    bullets?: string[];
    default_open?: boolean;
    groups?: Array<{
      title: string;
      bullets: string[];
    }>;
  }>;
  footer_note?: string;
}

export interface CTM {
  id: string;
  centroid_id: string;
  track: Track;
  month: Date;
  title_count: number;
  events_digest: Event[];
  summary_text?: string;
  is_frozen: boolean;
}

// Calendar-day frontend redesign (docs/FRONTEND_CALENDAR_REDESIGN.md, Workstream A)
export interface CalendarClusterSource {
  id: string;
  title_display: string;
  url: string | null;
  publisher_name: string | null;
  publisher_domain: string | null; // feeds.source_domain — used for favicon
  detected_language: string | null;
}

export interface CalendarClusterCard {
  id: string;
  title: string | null;
  source_count: number;
  first_date: string; // YYYY-MM-DD
  last_date: string; // YYYY-MM-DD
  event_type: 'bilateral' | 'other_international' | 'domestic' | null;
  bucket_key: string | null;
  has_event_page: boolean; // source_count >= K (5)
  is_substrate: boolean;
  has_narratives: boolean;
  // Populated for small clusters (source_count < 5) that won't have their own
  // event page, so users can still click through to original publications.
  sources?: CalendarClusterSource[];
}

export interface CalendarDayView {
  date: string; // YYYY-MM-DD
  total_sources: number;
  cluster_count: number;
  daily_brief: string | null; // null until Phase 4.5-day lands
  clusters: CalendarClusterCard[];
}

// Per-day theme segment for the stacked activity chart.
// Comes from daily_briefs.themes (sector + subject + weight). Weights sum to ~1.
// Empty for days without a brief (< 5 promoted clusters).
export interface CalendarThemeSegment {
  sector: string;  // e.g. "SECURITY"
  subject: string; // e.g. "LAW_ENFORCEMENT"
  weight: number;  // 0..1
}

export interface CalendarStripeEntry {
  date: string; // YYYY-MM-DD, every day of the month
  total_sources: number;
  themes: CalendarThemeSegment[]; // from daily_briefs.themes; empty for days without a brief
}

export interface CalendarAnalysisScope {
  total_sources: number;         // total title_assignments for this CTM
  outlet_count: number;          // distinct feeds for this CTM
  active_days: number;           // days with >= 1 promoted event
}

export interface CalendarMonthView {
  ctm: CTM;
  days: CalendarDayView[]; // only days with >= 1 promoted cluster
  activity_stripe: CalendarStripeEntry[]; // every day of month incl. empty
  scope: CalendarAnalysisScope;
}

// Per-day track share for the centroid-level activity chart.
// Weights sum to ~1 when any track had coverage that day.
export interface CentroidStripeEntry {
  date: string; // YYYY-MM-DD, every day of the month
  total_sources: number;
  tracks: Array<{ track: string; weight: number }>;
}

export interface CentroidTrackSummary {
  track: string;
  title_count: number;
  summary_text: string | null;
  last_active: string | null;
  top_events: Array<{
    id: string;
    title: string;
    date: string;
    source_count: number;
    has_event_page: boolean;
  }>;
}

export interface CentroidMonthView {
  centroid_id: string;
  month: string; // YYYY-MM-DD
  activity_stripe: CentroidStripeEntry[];
  tracks: CentroidTrackSummary[];
  prev_month: string | null;
  next_month: string | null;
}

export interface Event {
  date: string;
  last_active?: string;
  title?: string;
  summary: string;
  tags?: string[];
  event_id?: string;
  source_title_ids?: string[];
  event_type?: 'bilateral' | 'other_international' | 'domestic' | null;
  bucket_key?: string | null;
  alias?: string | null;
  source_count?: number;
  importance_score?: number;
  is_catchall?: boolean;
  has_narratives?: boolean;
  topic_core?: string;
  family_id?: string;
  family_title?: string;
  family_domain?: string;
  family_summary?: string;
  resolvedTitles?: Title[];
  // Bilateral badge (populated by track page for display)
  bucketLabel?: string;
  bucketIsoCodes?: string[];
  bucketLink?: string;
  bucketDomestic?: boolean;
}

export interface Title {
  id: string;
  title_display: string;
  url_gnews?: string;
  publisher_name?: string;
  pubdate_utc: Date;
  detected_language?: string;
  processing_status: 'pending' | 'assigned' | 'out_of_scope';
}

export interface TitleAssignment {
  id: string;
  title_id: string;
  centroid_id: string;
  track: Track;
  ctm_id: string;
}

export interface Feed {
  id: string;
  name: string;
  url: string;
  language_code: string;
  country_code?: string;
  source_domain?: string;
  is_active: boolean;
}

// Track is a string - actual values come from database
export type Track = string;

// Convert track slug to human-readable label
// Pass a translation function (from useTranslations('tracks') or getTranslations('tracks')) for locale-aware labels
export function getTrackLabel(track: string, t?: (key: string) => string): string {
  if (t) {
    try { return t(track); } catch { /* fallback below */ }
  }
  const withoutPrefix = track.replace(/^geo_/, '');
  return withoutPrefix
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

// Get localized centroid display name, falling back to DB label
export function getCentroidLabel(centroidId: string, dbLabel: string, t?: (key: string) => string): string {
  if (t) {
    try { return t(centroidId); } catch { /* fallback below */ }
  }
  return dbLabel;
}

// Legacy TRACK_LABELS for backward compatibility - now uses dynamic function
export const TRACK_LABELS = new Proxy({} as Record<string, string>, {
  get(_target, prop: string) {
    return getTrackLabel(prop);
  }
});

export interface EventDetail {
  id: string;
  date: string;
  last_active: string | null;
  title: string | null;
  summary: string | null;
  tags: string[] | null;
  source_batch_count: number;
  event_type: string | null;
  bucket_key: string | null;
  saga: string | null;
  ctm_id: string;
  centroid_id: string;
  centroid_label: string;
  track: string;
  month: string;
  coherence_check: { coherent: false; reason: string; topics: string[] } | null;
  absorbed_centroids: string[] | null;
}

export interface RelatedEvent {
  id: string;
  title: string | null;
  source_batch_count: number;
  centroid_id: string;
  centroid_label: string;
  iso_codes: string[] | null;
  track: string;
  shared_titles: number;
}

export interface RaiSection {
  heading: string;
  paragraphs: string[];
}

export interface EpicNarrative {
  title: string;
  description: string;
}

export interface FramedNarrative {
  id: string;
  label: string;
  description: string | null;
  moral_frame: string | null;
  title_count: number;
  top_sources: string[] | null;
  proportional_sources: string[] | null;
  top_countries: string[] | null;
  sample_titles: Array<{ title: string; publisher: string; date: string | null }> | null;
  // RAI Analysis fields
  rai_adequacy: number | null;
  rai_synthesis: string | null;
  rai_conflicts: string[] | null;
  rai_blind_spots: string[] | null;
  rai_shifts: {
    overall_score?: number;
    bias_score?: number;
    coherence_score?: number;
    credibility_score?: number;
    evidence_quality?: number;
    relevance_score?: number;
    safety_score?: number;
  } | null;
  rai_full_analysis: RaiSection[] | string | null;
  rai_analyzed_at: string | null;
  // New signal fields (for event/CTM narratives)
  signal_stats: SignalStats | null;
  rai_signals: RaiSignals | null;
  rai_signals_at: string | null;
  // Stance-clustered extraction fields
  extraction_method: string | null;
  cluster_label: string | null;
  cluster_publishers: string[] | null;
  cluster_score_avg: number | null;
}

// Per-frame stats computed at extraction time (stored in signal_stats JSONB)
export interface FrameStats {
  frame_title_count: number;
  frame_pct: number;
  frame_languages: Record<string, number>;
  frame_publishers: Array<{ name: string; count: number }>;
  frame_date_first: string | null;
  frame_date_last: string | null;
}

export interface SignalStatsEntry {
  name: string;
  count: number;
  share: number;
}

export interface SignalStats {
  title_count: number;
  publisher_count: number;
  publisher_hhi: number;
  language_count: number;
  language_distribution: Record<string, number>;
  domain_distribution: Record<string, number>;
  date_range_days: number;
  top_publishers: SignalStatsEntry[];
  top_persons: SignalStatsEntry[];
  top_orgs: SignalStatsEntry[];
  top_actors: SignalStatsEntry[];
  entity_country_distribution: Record<string, number>;
  person_count: number;
  actor_count: number;
  narrative_frame_count: number;
  label_coverage: number;
  action_class_distribution?: Record<string, number>;
}

export interface RaiSignals {
  adequacy: number;
  adequacy_reason: string;
  framing_bias: string;
  source_concentration: string;
  geographic_blind_spots: string[];
  findings: string[];
  follow_the_gain: string;
  missing_perspectives: string[];
}

export interface Epic {
  id: string;
  slug: string;
  month: string;
  title: string | null;
  summary: string | null;
  anchor_tags: string[];
  centroid_count: number;
  event_count: number;
  total_sources: number;
  timeline: string | null;
  narratives: EpicNarrative[] | null;
  centroid_summaries: Record<string, string> | null;
  centroid_summaries_de: Record<string, string> | null;
}

export interface EpicEvent {
  event_id: string;
  title: string | null;
  summary: string;
  tags: string[] | null;
  source_batch_count: number;
  date: string;
  centroid_id: string;
  track: string;
  centroid_label: string;
  iso_codes: string[] | null;
}

export interface EpicCentroidStat {
  centroid_id: string;
  centroid_label: string;
  event_count: number;
  total_sources: number;
  iso_codes: string[] | null;
}

export type SignalType = 'persons' | 'orgs' | 'places' | 'commodities' | 'policies' | 'systems' | 'named_events';

export interface TopSignal {
  signal_type: SignalType;
  value: string;
  count: number;
  context?: string;
}

export interface OutletProfile {
  feed_name: string;
  source_domain: string | null;
  country_code: string | null;
  language_code: string | null;
  article_count: number;
  centroid_coverage: { centroid_id: string; label: string; iso_codes: string[] | null; count: number }[];
  top_ctms: { ctm_id: string; centroid_id: string; track: string; month: string; label: string; count: number }[];
}

export interface PublisherStats {
  title_count: number;
  centroid_count: number;
  track_distribution: Record<string, number>;
  geo_hhi: number;
  geo_gini: number;
  top_centroids: { name: string; count: number; share: number }[];
  top_actors: { name: string; count: number; share: number }[];
  action_distribution: Record<string, number>;
  domain_distribution: Record<string, number>;
  language_distribution: Record<string, number>;
  signal_richness: number;
  dow_distribution: Record<string, number>;
  peak_hour: number | null;
  narrative_frame_count: number;
}

export interface StanceScore {
  centroid_id: string;
  centroid_label: string;
  score: number;
  confidence: number;
  sample_size: number;
  month?: string;
}

export interface OutletNarrativeFrame {
  entity_type: string;
  entity_id: string;
  label: string;
  description: string | null;
  title_count: number;
  entity_label: string;
}

export interface TrendingEvent {
  id: string;
  title: string;
  date: string;
  last_active: string;
  source_batch_count: number;
  tags: string[];
  summary: string | null;
  centroid_id: string;
  centroid_label: string;
  iso_codes: string[];
  track: string;
  trending_score: number;
  top_signals?: string[];
  perspectives?: TrendingEvent[];
}

export interface TrendingSignal {
  signal_type: string;
  value: string;
  event_count: number;
}

export interface SearchResult {
  type: 'event' | 'centroid' | 'epic';
  id: string;
  title: string;
  snippet: string;
  sources: number | null;
  date: string | null;
  centroid_label: string | null;
  slug: string | null;
  rank: number;
}

// Signal Observatory types

export interface SignalNode {
  signal_type: SignalType;
  value: string;
  event_count: number;
  context?: string;
}

export interface SignalEdge {
  source: string;
  target: string;
  source_type: SignalType;
  target_type: SignalType;
  weight: number;
}

export interface SignalWeekly {
  week: string;
  count: number;
}

export interface RelationshipCluster {
  signal_type: SignalType;
  value: string;
  event_count: number;
  label: string;
  top_events: Array<{ id: string; title: string; date: string; source_batch_count: number }>;
}

export interface SignalDetailStats {
  total: number;
  weekly: SignalWeekly[];
  geo: Array<{ country: string; count: number }>;
  tracks: Array<{ track: string; count: number }>;
}


export interface SignalCategoryEntry extends SignalNode {
  weekly: SignalWeekly[];
}

export interface SignalGraph {
  nodes: SignalNode[];
  edges: SignalEdge[];
}

export const SIGNAL_LABELS: Record<SignalType, string> = {
  persons: 'Top Persons',
  orgs: 'Top Organizations',
  places: 'Top Places',
  commodities: 'Top Commodities',
  policies: 'Top Policies',
  systems: 'Top Systems',
  named_events: 'Top Events',
};

// Narrative Mapping types
export interface MetaNarrative {
  id: string;
  name: string;
  description: string;
  signals: Record<string, unknown> | null;
  sort_order: number;
}

export interface StrategicNarrative {
  id: string;
  meta_narrative_id: string;
  meta_name?: string;
  category: string | null;
  actor_centroid: string | null;
  actor_label?: string;
  name: string;
  claim: string | null;
  normative_conclusion: string | null;
  keywords: string[] | null;
  action_classes: string[] | null;
  domains: string[] | null;
  event_count?: number;
  tier?: 'operational' | 'ideological';
  matching_guidance?: string | null;
  aligned_with?: string[] | null;
  opposes?: string[] | null;
}

export interface NarrativeMapEntry {
  id: string;
  meta_narrative_id: string;
  meta_name: string;
  actor_centroid: string | null;
  actor_label: string | null;
  actor_iso_codes: string[] | null;
  name: string;
  claim: string | null;
  actor_prefixes: string[] | null;
  related_centroids: string[] | null;
  tier: 'operational' | 'ideological' | null;
  event_count: number;
}

export interface EventNarrativeLink {
  narrative_id: string;
  narrative_name: string;
  actor_centroid: string | null;
  actor_label: string | null;
  confidence: number;
}

export const REGIONS = {
  EUROPE: 'Europe',
  ASIA: 'Asia',
  AFRICA: 'Africa',
  AMERICAS: 'Americas',
  OCEANIA: 'Oceania',
  MIDEAST: 'Middle East',
} as const;

export type RegionKey = keyof typeof REGIONS;

// ISO code to country name mapping
const ISO_TO_COUNTRY: Record<string, string> = {
  // Major powers & orgs
  US: 'United States', CN: 'China', RU: 'Russia', GB: 'United Kingdom', UK: 'United Kingdom',
  EU: 'European Union',
  DE: 'Germany', FR: 'France', JP: 'Japan', IN: 'India', BR: 'Brazil',
  // Europe
  IT: 'Italy', ES: 'Spain', PL: 'Poland', NL: 'Netherlands', BE: 'Belgium',
  SE: 'Sweden', NO: 'Norway', DK: 'Denmark', FI: 'Finland', AT: 'Austria',
  CH: 'Switzerland', PT: 'Portugal', GR: 'Greece', CZ: 'Czechia', RO: 'Romania',
  HU: 'Hungary', IE: 'Ireland', SK: 'Slovakia', BG: 'Bulgaria', HR: 'Croatia',
  RS: 'Serbia', UA: 'Ukraine', BY: 'Belarus', LT: 'Lithuania', LV: 'Latvia',
  EE: 'Estonia', SI: 'Slovenia', BA: 'Bosnia', AL: 'Albania', MK: 'North Macedonia',
  ME: 'Montenegro', XK: 'Kosovo', MD: 'Moldova', LU: 'Luxembourg', MT: 'Malta',
  CY: 'Cyprus', IS: 'Iceland', GL: 'Greenland',
  // Middle East
  IL: 'Israel', SA: 'Saudi Arabia', IR: 'Iran', TR: 'Turkey', AE: 'UAE',
  EG: 'Egypt', IQ: 'Iraq', SY: 'Syria', JO: 'Jordan', LB: 'Lebanon',
  KW: 'Kuwait', QA: 'Qatar', BH: 'Bahrain', OM: 'Oman', YE: 'Yemen',
  PS: 'Palestine',
  // Asia
  KR: 'South Korea', KP: 'North Korea', TW: 'Taiwan', HK: 'Hong Kong',
  SG: 'Singapore', MY: 'Malaysia', ID: 'Indonesia', TH: 'Thailand',
  VN: 'Vietnam', PH: 'Philippines', MM: 'Myanmar', KH: 'Cambodia',
  LA: 'Laos', BD: 'Bangladesh', PK: 'Pakistan', AF: 'Afghanistan',
  NP: 'Nepal', LK: 'Sri Lanka', MN: 'Mongolia', KZ: 'Kazakhstan',
  UZ: 'Uzbekistan', TM: 'Turkmenistan', KG: 'Kyrgyzstan', TJ: 'Tajikistan',
  AZ: 'Azerbaijan', GE: 'Georgia', AM: 'Armenia',
  // Africa
  ZA: 'South Africa', NG: 'Nigeria', KE: 'Kenya', ET: 'Ethiopia',
  GH: 'Ghana', TZ: 'Tanzania', UG: 'Uganda', DZ: 'Algeria', MA: 'Morocco',
  TN: 'Tunisia', LY: 'Libya', SD: 'Sudan', SS: 'South Sudan', AO: 'Angola',
  MZ: 'Mozambique', ZW: 'Zimbabwe', ZM: 'Zambia', BW: 'Botswana',
  NA: 'Namibia', SN: 'Senegal', CI: 'Ivory Coast', CM: 'Cameroon',
  CD: 'DR Congo', CG: 'Congo', RW: 'Rwanda', MG: 'Madagascar',
  MU: 'Mauritius', ML: 'Mali', NE: 'Niger', BF: 'Burkina Faso',
  // Americas
  CA: 'Canada', MX: 'Mexico', AR: 'Argentina', CL: 'Chile', CO: 'Colombia',
  PE: 'Peru', VE: 'Venezuela', EC: 'Ecuador', BO: 'Bolivia', PY: 'Paraguay',
  UY: 'Uruguay', CU: 'Cuba', DO: 'Dominican Republic', HT: 'Haiti',
  GT: 'Guatemala', HN: 'Honduras', SV: 'El Salvador', NI: 'Nicaragua',
  CR: 'Costa Rica', PA: 'Panama', JM: 'Jamaica', TT: 'Trinidad',
  PR: 'Puerto Rico', BS: 'Bahamas', BB: 'Barbados', GY: 'Guyana', SR: 'Suriname',
  // Oceania
  AU: 'Australia', NZ: 'New Zealand', PG: 'Papua New Guinea', FJ: 'Fiji',
};

// Get full country name from ISO code or bucket key
export function getCountryName(codeOrBucketKey: string): string {
  // If it's a bucket key like "ASIA-CN" or "EUROPE-DE", extract the ISO code
  const parts = codeOrBucketKey.split('-');
  const isoCode = parts.length > 1 ? parts[parts.length - 1] : codeOrBucketKey;

  // Look up in mapping, fall back to the code itself (title-cased)
  const name = ISO_TO_COUNTRY[isoCode.toUpperCase()];
  if (name) return name;

  // If not found, title-case whatever we have
  return isoCode.charAt(0).toUpperCase() + isoCode.slice(1).toLowerCase();
}

// Extract ISO code from bucket key (e.g., "EUROPE-DE" -> "DE", "SYS-ENERGY" -> "ENERGY")
export function getIsoFromBucketKey(bucketKey: string): string {
  const parts = bucketKey.split('-');
  return parts.length > 1 ? parts[parts.length - 1] : bucketKey;
}

// Utility function to format relative time
// t: a next-intl translator for the 'common' namespace
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function formatTimeAgo(date: Date | null | undefined, t: (key: string, values?: any) => string): string {
  if (!date) return '';

  const now = new Date();
  const diffMs = now.getTime() - new Date(date).getTime();
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffHours / 24);

  if (diffHours < 1) {
    return t('justNow');
  } else if (diffHours < 24) {
    return t('hoursAgo', { count: diffHours });
  } else if (diffDays < 30) {
    return t('daysAgo', { count: diffDays });
  } else {
    const diffMonths = Math.floor(diffDays / 30);
    return t('monthsAgo', { count: diffMonths });
  }
}
