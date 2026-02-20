/**
 * Logo/Favicon utilities for news outlets
 *
 * Logos are stored locally in /public/logos/{domain}.png (downloaded from
 * Google Favicon Service at 64px). Falls back to Google if local file
 * is missing.
 */

/**
 * Get logo URL for a news outlet.
 * Returns local path /logos/{domain}.png. The caller should use onError
 * fallback or accept a broken image for the ~5% of feeds with no logo.
 */
export function getOutletLogoUrl(domain: string, _size: number = 32): string {
  if (!domain) return '';

  const cleanDomain = domain
    .replace(/^https?:\/\//, '')
    .replace(/^www\./, '')
    .replace(/\/$/, '');

  return `/logos/${cleanDomain}.png`;
}
