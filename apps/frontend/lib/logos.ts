/**
 * Logo/Favicon utilities for news outlets
 */

/**
 * Get logo URL for a news outlet
 * Priority: Manual override > Google Favicon Service
 */
export function getOutletLogoUrl(domain: string, size: number = 32): string {
  if (!domain) return '';

  // Clean domain (remove protocol, www, trailing slashes)
  const cleanDomain = domain
    .replace(/^https?:\/\//, '')
    .replace(/^www\./, '')
    .replace(/\/$/, '');

  // Check for manual override (you can add logos to /public/logos/)
  // Format: /logos/domain.png or /logos/domain.svg
  // Example: /logos/bbc.com.png
  // Falls back to Google Favicon if manual logo doesn't exist

  // For now, use Google Favicon Service (most reliable)
  // To add manual overrides, place PNGs/SVGs in /public/logos/[domain].png
  return `https://www.google.com/s2/favicons?domain=${cleanDomain}&sz=${size}`;
}

/**
 * Check if manual logo exists for a domain
 * Note: This is a client-side check - actual file must exist in /public/logos/
 */
export function getManualLogoUrl(domain: string): string | null {
  const cleanDomain = domain
    .replace(/^https?:\/\//, '')
    .replace(/^www\./, '')
    .replace(/\/$/, '');

  // Try PNG first, then SVG
  // In production, you'd want to check if these files exist
  // For now, return null (use automated service)
  return null;

  // Uncomment below to enable manual logos:
  // return `/logos/${cleanDomain}.png`;
}

/**
 * Alternative logo services (use as fallbacks if needed)
 */
export const LOGO_SERVICES = {
  // Google - Most reliable
  google: (domain: string, size = 32) =>
    `https://www.google.com/s2/favicons?domain=${domain}&sz=${size}`,

  // DuckDuckGo - Good alternative
  duckduckgo: (domain: string) =>
    `https://icons.duckduckgo.com/ip3/${domain}.ico`,

  // Clearbit - Higher quality but rate limited
  clearbit: (domain: string) =>
    `https://logo.clearbit.com/${domain}`,

  // Favicon.io - Community sourced
  faviconio: (domain: string, size = 32) =>
    `https://favicone.com/${domain}?s=${size}`,
};

/**
 * Get logo with fallback chain
 */
export function getLogoWithFallback(domain: string): string {
  return getOutletLogoUrl(domain, 32);
}
