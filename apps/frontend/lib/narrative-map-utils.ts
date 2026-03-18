// Maps ISO-like prefixes (from actor_prefixes column) to centroid IDs
export const PREFIX_TO_CENTROID: Record<string, string> = {
  US: 'AMERICAS-USA',
  CN: 'ASIA-CHINA',
  RU: 'EUROPE-RUSSIA',
  UK: 'EUROPE-UK',
  IR: 'MIDEAST-IRAN',
  IL: 'MIDEAST-ISRAEL',
  IN: 'ASIA-INDIA',
  JP: 'ASIA-JAPAN',
  TR: 'MIDEAST-TURKEY',
  SA: 'MIDEAST-SAUDI',
  DE: 'EUROPE-GERMANY',
  FR: 'EUROPE-FRANCE',
  BR: 'AMERICAS-BRAZIL',
  AU: 'OCEANIA-AUSTRALIA',
  PK: 'ASIA-PAKISTAN',
  CA: 'AMERICAS-CANADA',
  KR: 'ASIA-SOUTHKOREA',
  KP: 'ASIA-NORKOREA',
  TW: 'ASIA-TAIWAN',
  MX: 'AMERICAS-MEXICO',
  NG: 'AFRICA-NIGERIA',
  ZA: 'AFRICA-SOUTHAFRICA',
  UA: 'EUROPE-UKRAINE',
  BY: 'EUROPE-BELARUS',
  PS: 'MIDEAST-PALESTINE',
  ET: 'AFRICA-ETHIOPIA',
  KE: 'AFRICA-KENYA',
  CD: 'AFRICA-DRC',
  VE: 'AMERICAS-VENEZUELA',
  CU: 'AMERICAS-CUBA',
  EU: 'NON-STATE-EU',
  NATO: 'NON-STATE-NATO',
  HU: 'EUROPE-VISEGRAD',
  MN: 'ASIA-MONGOLIA',
  HK: 'ASIA-HONGKONG',
};

import type { NarrativeMapEntry } from './types';

/**
 * Derive target centroid IDs for a narrative from its actor_prefixes and related_centroids.
 * Targets = non-protagonist prefixes mapped via PREFIX_TO_CENTROID + explicit related_centroids.
 */
export function deriveTargetCentroids(
  narrative: NarrativeMapEntry
): string[] {
  const targets = new Set<string>();
  const protagonist = narrative.actor_centroid;

  // Map non-protagonist prefixes to centroid IDs
  if (narrative.actor_prefixes) {
    for (const prefix of narrative.actor_prefixes) {
      const centroidId = PREFIX_TO_CENTROID[prefix];
      if (centroidId && centroidId !== protagonist) {
        targets.add(centroidId);
      }
    }
  }

  // Add explicit related_centroids (already centroid IDs)
  if (narrative.related_centroids) {
    for (const rc of narrative.related_centroids) {
      if (rc !== protagonist) {
        targets.add(rc);
      }
    }
  }

  return Array.from(targets);
}

/**
 * Normalize GeoJSON ISO code, handling known quirks.
 */
export function normalizeIso(feature: { properties: Record<string, string> }): string {
  let iso2 = feature.properties['ISO3166-1-Alpha-2'];
  const name = feature.properties.name;
  if (name === 'France') iso2 = 'FR';
  if (name === 'Norway') iso2 = 'NO';
  if (name === 'Kosovo') iso2 = 'XK';
  if (iso2 === 'CN-TW') iso2 = 'TW';
  return iso2;
}
