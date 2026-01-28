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
  is_catchall?: boolean;
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
