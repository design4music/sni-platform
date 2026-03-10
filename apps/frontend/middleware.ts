import createMiddleware from 'next-intl/middleware';
import { routing } from './i18n/routing';

export default createMiddleware(routing);

export const config = {
  // Match all paths except api, _next, and static files (ending with known extensions)
  matcher: ['/((?!api|_next|.*\\.(?:js|css|ico|png|jpg|jpeg|gif|svg|webp|woff2?|ttf|map|xml|txt|webmanifest)$).*)'],
};
