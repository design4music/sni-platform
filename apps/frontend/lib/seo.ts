import type { Metadata } from 'next';

export type Locale = 'en' | 'de';

export const SITE_URL = 'https://www.worldbrief.info';

const MONTH_NAMES_EN = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];
const MONTH_NAMES_DE = [
  'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
  'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember',
];

// "2026-04" or "2026-04-01" → "April 2026" / "April 2026"
export function formatMonthLabel(monthStr: string, locale: Locale = 'en'): string {
  const [year, month] = monthStr.split('-');
  const idx = Math.max(0, Math.min(11, parseInt(month, 10) - 1));
  const names = locale === 'de' ? MONTH_NAMES_DE : MONTH_NAMES_EN;
  return `${names[idx]} ${year}`;
}

// "2026-04-09" → "9 April 2026" / "9. April 2026"
export function formatDayLabel(dateStr: string, locale: Locale = 'en'): string {
  const [year, month, day] = dateStr.split('-');
  const idx = Math.max(0, Math.min(11, parseInt(month, 10) - 1));
  const names = locale === 'de' ? MONTH_NAMES_DE : MONTH_NAMES_EN;
  const d = parseInt(day, 10);
  return locale === 'de' ? `${d}. ${names[idx]} ${year}` : `${d} ${names[idx]} ${year}`;
}

// YYYY-MM-DD format validator.
export function isValidDateSlug(s: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(s)) return false;
  const [y, m, d] = s.split('-').map(n => parseInt(n, 10));
  if (m < 1 || m > 12 || d < 1 || d > 31 || y < 2000 || y > 2100) return false;
  // Reject clearly invalid calendar dates (e.g. 2026-02-30).
  const dt = new Date(Date.UTC(y, m - 1, d));
  return dt.getUTCFullYear() === y && dt.getUTCMonth() === m - 1 && dt.getUTCDate() === d;
}

// Turn SECTOR_SUBJECT style labels into readable lowercase phrases.
export function humanizeEnum(s: string): string {
  return s.replace(/_/g, ' ').toLowerCase();
}

// Truncate for meta description. Google shows ~155-160 chars; we cap at 160.
export function truncateDescription(s: string, max = 160): string {
  const clean = s.replace(/\s+/g, ' ').trim();
  if (clean.length <= max) return clean;
  // Cut at the last word boundary before the limit, add ellipsis.
  const slice = clean.slice(0, max - 1);
  const lastSpace = slice.lastIndexOf(' ');
  return (lastSpace > 40 ? slice.slice(0, lastSpace) : slice) + '…';
}

// Returns a Metadata["alternates"] block with canonical + EN/DE hreflang.
// `path` is the route without locale prefix (e.g. "/c/usa").
export function buildAlternates(path: string): NonNullable<Metadata['alternates']> {
  const clean = path.startsWith('/') ? path : `/${path}`;
  return {
    canonical: clean,
    languages: {
      en: clean,
      de: `/de${clean}`,
      'x-default': clean,
    },
  };
}

// Combine title/description with canonical + hreflang + OpenGraph + Twitter.
// Callers pass the route path (without /de/ prefix); we mirror title/description
// into og/twitter and emit language alternates consistently.
export function buildPageMetadata(args: {
  title: string;
  description: string;
  path: string;
  locale: Locale;
  ogType?: 'website' | 'article';
  publishedTime?: string; // ISO date for articles
  ogImage?: string;       // absolute URL
}): Metadata {
  const { title, description, path, locale, ogType = 'website', publishedTime, ogImage } = args;
  const localePath = locale === 'de' ? `/de${path.startsWith('/') ? path : `/${path}`}` : path;
  const url = `${SITE_URL}${localePath}`;

  return {
    title,
    description,
    alternates: buildAlternates(path),
    openGraph: {
      type: ogType,
      title,
      description,
      url,
      siteName: 'WorldBrief',
      locale: locale === 'de' ? 'de_DE' : 'en_US',
      ...(ogType === 'article' && publishedTime ? { publishedTime } : {}),
      ...(ogImage ? { images: [{ url: ogImage }] } : {}),
    },
    twitter: {
      card: ogImage ? 'summary_large_image' : 'summary',
      title,
      description,
      ...(ogImage ? { images: [ogImage] } : {}),
    },
  };
}

// Format a number for embedding in descriptions: "1,234".
export function formatCount(n: number, locale: Locale = 'en'): string {
  return n.toLocaleString(locale === 'de' ? 'de-DE' : 'en-US');
}

// Join a list of strings with locale-appropriate conjunction for the final item.
// ["a","b","c"] → "a, b and c" / "a, b und c". Capped for readability.
export function joinList(items: string[], locale: Locale = 'en'): string {
  const list = items.filter(Boolean);
  if (list.length === 0) return '';
  if (list.length === 1) return list[0];
  const and = locale === 'de' ? 'und' : 'and';
  return `${list.slice(0, -1).join(', ')} ${and} ${list[list.length - 1]}`;
}

// ──────────────────────────────────────────────────────────────
// JSON-LD structured data builders
// ──────────────────────────────────────────────────────────────

const PUBLISHER_SCHEMA = {
  '@type': 'Organization',
  name: 'WorldBrief',
  url: SITE_URL,
  logo: {
    '@type': 'ImageObject',
    url: `${SITE_URL}/favicon.ico`,
  },
};

export function breadcrumbList(items: Array<{ name: string; path: string }>) {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((it, idx) => ({
      '@type': 'ListItem',
      position: idx + 1,
      name: it.name,
      item: it.path.startsWith('http') ? it.path : `${SITE_URL}${it.path}`,
    })),
  };
}

export function newsArticleJsonLd(args: {
  headline: string;
  description: string;
  datePublished: string; // ISO
  dateModified?: string; // ISO
  path: string;
  locale: Locale;
  keywords?: string[];
  articleSection?: string;
}) {
  const url = `${SITE_URL}${args.path}`;
  return {
    '@context': 'https://schema.org',
    '@type': 'NewsArticle',
    headline: args.headline,
    description: args.description,
    datePublished: args.datePublished,
    ...(args.dateModified ? { dateModified: args.dateModified } : {}),
    inLanguage: args.locale === 'de' ? 'de' : 'en',
    mainEntityOfPage: {
      '@type': 'WebPage',
      '@id': url,
    },
    url,
    publisher: PUBLISHER_SCHEMA,
    ...(args.articleSection ? { articleSection: args.articleSection } : {}),
    ...(args.keywords && args.keywords.length ? { keywords: args.keywords.join(', ') } : {}),
  };
}

export function articleJsonLd(args: {
  headline: string;
  description: string;
  path: string;
  locale: Locale;
  datePublished?: string;
  dateModified?: string;
}) {
  const url = `${SITE_URL}${args.path}`;
  return {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: args.headline,
    description: args.description,
    ...(args.datePublished ? { datePublished: args.datePublished } : {}),
    ...(args.dateModified ? { dateModified: args.dateModified } : {}),
    inLanguage: args.locale === 'de' ? 'de' : 'en',
    mainEntityOfPage: { '@type': 'WebPage', '@id': url },
    url,
    publisher: PUBLISHER_SCHEMA,
  };
}

// Website + SearchAction — emitted once in the root layout.
export function websiteJsonLd() {
  return {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: 'WorldBrief',
    url: SITE_URL,
    description: 'AI-powered global news intelligence. Multilingual coverage from 180+ sources organized by country, theme, and narrative frame.',
    publisher: PUBLISHER_SCHEMA,
    potentialAction: {
      '@type': 'SearchAction',
      target: {
        '@type': 'EntryPoint',
        urlTemplate: `${SITE_URL}/search?q={search_term_string}`,
      },
      'query-input': 'required name=search_term_string',
    },
  };
}
