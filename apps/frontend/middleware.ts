import createMiddleware from 'next-intl/middleware';
import { routing } from './i18n/routing';

export default createMiddleware(routing);

export const config = {
  // Match all paths except api, _next, public static assets, and any
  // top-level file with an extension (sitemap.xml, robots.txt, favicon.ico,
  // opengraph-image.png, etc.). The ".*\\..*" rule keeps next-intl from
  // 404ing those — they're served by the framework, not the [locale] tree.
  matcher: ['/((?!api|_next|flags/|geo/|logos/|.*\\..*).*)'],
};
