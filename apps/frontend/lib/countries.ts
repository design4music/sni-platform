// ISO 3166-1 alpha-2 country codes to names
// Also includes special codes for international organizations
export const COUNTRY_NAMES: Record<string, string> = {
  // International Organizations
  EU: 'European Union',
  UN: 'United Nations',
  WOR: 'World Bank',
  BRI: 'BRICS',

  // Americas
  US: 'United States',
  CA: 'Canada',
  BR: 'Brazil',
  AR: 'Argentina',
  MX: 'Mexico',
  CL: 'Chile',
  CO: 'Colombia',
  VE: 'Venezuela',
  PE: 'Peru',
  UY: 'Uruguay',
  EC: 'Ecuador',

  // Europe
  GB: 'United Kingdom',
  FR: 'France',
  DE: 'Germany',
  IT: 'Italy',
  ES: 'Spain',
  RU: 'Russia',
  UA: 'Ukraine',
  PL: 'Poland',
  NL: 'Netherlands',
  SE: 'Sweden',
  NO: 'Norway',
  FI: 'Finland',
  DK: 'Denmark',
  BE: 'Belgium',
  AT: 'Austria',
  CH: 'Switzerland',
  GR: 'Greece',
  PT: 'Portugal',
  CZ: 'Czech Republic',
  RO: 'Romania',
  HU: 'Hungary',
  BG: 'Bulgaria',
  RS: 'Serbia',
  HR: 'Croatia',
  SK: 'Slovakia',
  SI: 'Slovenia',
  EE: 'Estonia',
  LV: 'Latvia',
  LT: 'Lithuania',
  IE: 'Ireland',

  // Asia
  CN: 'China',
  JP: 'Japan',
  KR: 'South Korea',
  KP: 'North Korea',
  IN: 'India',
  ID: 'Indonesia',
  TH: 'Thailand',
  VN: 'Vietnam',
  MY: 'Malaysia',
  SG: 'Singapore',
  PH: 'Philippines',
  PK: 'Pakistan',
  BD: 'Bangladesh',
  MM: 'Myanmar',
  KH: 'Cambodia',
  LA: 'Laos',
  NP: 'Nepal',
  LK: 'Sri Lanka',
  AF: 'Afghanistan',
  KZ: 'Kazakhstan',
  UZ: 'Uzbekistan',
  TM: 'Turkmenistan',
  TJ: 'Tajikistan',
  KG: 'Kyrgyzstan',
  MN: 'Mongolia',

  // Middle East
  SA: 'Saudi Arabia',
  AE: 'United Arab Emirates',
  TR: 'Turkey',
  IL: 'Israel',
  IR: 'Iran',
  IQ: 'Iraq',
  EG: 'Egypt',
  JO: 'Jordan',
  LB: 'Lebanon',
  SY: 'Syria',
  YE: 'Yemen',
  QA: 'Qatar',
  KW: 'Kuwait',
  OM: 'Oman',
  BH: 'Bahrain',
  PS: 'Palestine',

  // Africa
  ZA: 'South Africa',
  NG: 'Nigeria',
  KE: 'Kenya',
  ET: 'Ethiopia',
  GH: 'Ghana',
  TZ: 'Tanzania',
  UG: 'Uganda',
  DZ: 'Algeria',
  MA: 'Morocco',
  TN: 'Tunisia',
  LY: 'Libya',
  SD: 'Sudan',
  ZW: 'Zimbabwe',
  AO: 'Angola',
  MZ: 'Mozambique',
  ZM: 'Zambia',
  BW: 'Botswana',
  NA: 'Namibia',
  SN: 'Senegal',
  CI: 'Ivory Coast',
  CM: 'Cameroon',

  // Oceania
  AU: 'Australia',
  NZ: 'New Zealand',
  FJ: 'Fiji',
  PG: 'Papua New Guinea',
  NC: 'New Caledonia',
  PF: 'French Polynesia',
};

// Country code to region mapping
export const COUNTRY_TO_REGION: Record<string, string> = {
  // International Organizations
  EU: 'Global', UN: 'Global', WOR: 'Global', BRI: 'Global',

  // Americas
  US: 'Americas', CA: 'Americas', BR: 'Americas', AR: 'Americas', MX: 'Americas',
  CL: 'Americas', CO: 'Americas', VE: 'Americas', PE: 'Americas', UY: 'Americas',
  EC: 'Americas',

  // Europe
  GB: 'Europe', FR: 'Europe', DE: 'Europe', IT: 'Europe', ES: 'Europe',
  RU: 'Europe', UA: 'Europe', PL: 'Europe', NL: 'Europe', SE: 'Europe',
  NO: 'Europe', FI: 'Europe', DK: 'Europe', BE: 'Europe', AT: 'Europe',
  CH: 'Europe', GR: 'Europe', PT: 'Europe', CZ: 'Europe', RO: 'Europe',
  HU: 'Europe', BG: 'Europe', RS: 'Europe', HR: 'Europe', SK: 'Europe',
  SI: 'Europe', EE: 'Europe', LV: 'Europe', LT: 'Europe', IE: 'Europe',

  // Asia
  CN: 'Asia', JP: 'Asia', KR: 'Asia', KP: 'Asia', IN: 'Asia', ID: 'Asia',
  TH: 'Asia', VN: 'Asia', MY: 'Asia', SG: 'Asia', PH: 'Asia',
  PK: 'Asia', BD: 'Asia', MM: 'Asia', KH: 'Asia', LA: 'Asia',
  NP: 'Asia', LK: 'Asia', AF: 'Asia', KZ: 'Asia', UZ: 'Asia',
  TM: 'Asia', TJ: 'Asia', KG: 'Asia', MN: 'Asia',

  // Middle East
  SA: 'Middle East', AE: 'Middle East', TR: 'Middle East', IL: 'Middle East',
  IR: 'Middle East', IQ: 'Middle East', EG: 'Middle East', JO: 'Middle East',
  LB: 'Middle East', SY: 'Middle East', YE: 'Middle East', QA: 'Middle East',
  KW: 'Middle East', OM: 'Middle East', BH: 'Middle East', PS: 'Middle East',

  // Africa
  ZA: 'Africa', NG: 'Africa', KE: 'Africa', ET: 'Africa', GH: 'Africa',
  TZ: 'Africa', UG: 'Africa', DZ: 'Africa', MA: 'Africa', TN: 'Africa',
  LY: 'Africa', SD: 'Africa', ZW: 'Africa', AO: 'Africa', MZ: 'Africa',
  ZM: 'Africa', BW: 'Africa', NA: 'Africa', SN: 'Africa', CI: 'Africa',
  CM: 'Africa',

  // Oceania
  AU: 'Oceania', NZ: 'Oceania', FJ: 'Oceania', PG: 'Oceania',
  NC: 'Oceania', PF: 'Oceania',
};

// Helper function to get country name from code
export function getCountryName(code: string | null | undefined): string {
  if (!code) return 'Global';
  return COUNTRY_NAMES[code.toUpperCase()] || code;
}

// Helper function to get region from country code
export function getRegionFromCountry(code: string | null | undefined): string {
  if (!code) return 'Global';
  return COUNTRY_TO_REGION[code.toUpperCase()] || 'Global';
}
