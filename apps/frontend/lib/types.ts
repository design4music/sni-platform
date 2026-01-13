export interface Centroid {
  id: string;
  label: string;
  class: 'geo' | 'systemic';
  primary_theater?: string;
  is_superpower?: boolean;
  is_active: boolean;
  iso_codes?: string[];
  track_config_id?: string;
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

// Track is a string - actual values come from database
export type Track = string;

// Convert track slug to human-readable label
export function getTrackLabel(track: string): string {
  // Convert underscore to space and title case each word
  return track
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
