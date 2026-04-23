import createMiddleware from 'next-intl/middleware';
import { NextResponse, type NextRequest } from 'next/server';
import { routing } from './i18n/routing';

const intlMiddleware = createMiddleware(routing);

// YYYY-MM-DD slug with calendar-valid date. Inlined here because
// middleware runs in Edge runtime and can't import from lib/seo (which
// depends on next-intl server internals indirectly).
function isValidDateSlug(s: string | null): s is string {
  if (!s || !/^\d{4}-\d{2}-\d{2}$/.test(s)) return false;
  const [y, m, d] = s.split('-').map(n => parseInt(n, 10));
  if (m < 1 || m > 12 || d < 1 || d > 31 || y < 2000 || y > 2100) return false;
  const dt = new Date(Date.UTC(y, m - 1, d));
  return dt.getUTCFullYear() === y && dt.getUTCMonth() === m - 1 && dt.getUTCDate() === d;
}

// Matches /c/[centroid]/t/[track] or /de/c/[centroid]/t/[track]
// (with optional trailing slash). Intentionally NOT matching
// /c/[centroid]/t/[track]/[date] — those are the canonical day URLs.
const LEGACY_TRACK_PATH = /^\/(?:de\/)?c\/[^/]+\/t\/[^/]+\/?$/;

export default function middleware(req: NextRequest) {
  const { pathname, searchParams } = req.nextUrl;

  // Legacy ?day=YYYY-MM-DD → 308 to canonical day URL. Done at the edge
  // so crawlers see a real HTTP redirect (not a meta refresh, which is
  // what Server-Component `permanentRedirect` emits in Next 16).
  if (LEGACY_TRACK_PATH.test(pathname)) {
    const day = searchParams.get('day');
    if (isValidDateSlug(day)) {
      const target = req.nextUrl.clone();
      target.pathname = `${pathname.replace(/\/$/, '')}/${day}`;
      target.searchParams.delete('day');
      return NextResponse.redirect(target, 308);
    }
  }

  return intlMiddleware(req);
}

export const config = {
  // Match all paths except api, _next, public static assets, and any
  // top-level file with an extension (sitemap.xml, robots.txt, favicon.ico,
  // opengraph-image.png, etc.). The ".*\\..*" rule keeps next-intl from
  // 404ing those — they're served by the framework, not the [locale] tree.
  matcher: ['/((?!api|_next|flags/|geo/|logos/|.*\\..*).*)'],
};
