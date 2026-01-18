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
  article_count?: number;
  source_count?: number;
  language_count?: number;
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

export interface Event {
  date: string;
  summary: string;
  event_id?: string;
  source_title_ids?: string[];
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
export function getTrackLabel(track: string): string {
  // Remove "geo_" prefix if present (geographic tracks)
  const withoutPrefix = track.replace(/^geo_/, '');

  // Convert underscore to space and title case each word
  return withoutPrefix
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

// Legacy TRACK_LABELS for backward compatibility - now uses dynamic function
export const TRACK_LABELS = new Proxy({} as Record<string, string>, {
  get(_target, prop: string) {
    return getTrackLabel(prop);
  }
});

export const REGIONS = {
  EUROPE: 'Europe',
  ASIA: 'Asia',
  AFRICA: 'Africa',
  AMERICAS: 'Americas',
  OCEANIA: 'Oceania',
  MIDEAST: 'Middle East',
} as const;

export type RegionKey = keyof typeof REGIONS;

// Utility function to format relative time
export function formatTimeAgo(date: Date | null | undefined): string {
  if (!date) return '';

  const now = new Date();
  const diffMs = now.getTime() - new Date(date).getTime();
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffHours / 24);

  if (diffHours < 1) {
    return 'Just now';
  } else if (diffHours < 24) {
    return `${diffHours}h ago`;
  } else if (diffDays < 30) {
    return `${diffDays}d ago`;
  } else {
    const diffMonths = Math.floor(diffDays / 30);
    return `${diffMonths}mo ago`;
  }
}
