const createNextIntlPlugin = require('next-intl/plugin');
const withNextIntl = createNextIntlPlugin('./i18n/request.ts');

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,
  // Hard cap on Next's in-process ISR cache. Render web service is on the
  // 512MB plan; with ~150MB Node baseline the ISR cache must stay well
  // under ~200MB or bot-driven cache fill OOMs the instance. Default in
  // Next 14+ was 50MB; setting it explicitly so future Next upgrades or
  // new ISR routes can't silently change the budget. LRU-evicts oldest
  // entries when full instead of growing.
  cacheMaxMemorySize: 80 * 1024 * 1024, // 80 MB
  async redirects() {
    return [
      // Legacy /calendar route was folded into the track URL itself.
      // 301 preserves SEO equity from existing backlinks + prior sitemap.
      {
        source: '/c/:centroid/t/:track/calendar',
        destination: '/c/:centroid/t/:track',
        permanent: true,
      },
      {
        source: '/de/c/:centroid/t/:track/calendar',
        destination: '/de/c/:centroid/t/:track',
        permanent: true,
      },
      // Event families (D-051/D-053/D-059) removed. Graceful fallback for
      // any stray backlinks.
      {
        source: '/families/:id',
        destination: '/trending',
        permanent: true,
      },
      {
        source: '/de/families/:id',
        destination: '/de/trending',
        permanent: true,
      },
    ];
  },
  async headers() {
    return [
      {
        source: '/c/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, s-maxage=300, stale-while-revalidate=600',
          },
        ],
      },
      {
        source: '/events/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, s-maxage=600, stale-while-revalidate=1200',
          },
        ],
      },
      {
        source: '/epics/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, s-maxage=3600, stale-while-revalidate=7200',
          },
        ],
      },
      {
        source: '/region/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, s-maxage=300, stale-while-revalidate=600',
          },
        ],
      },
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://www.googletagmanager.com https://www.google-analytics.com",
              "style-src 'self' 'unsafe-inline'",
              "img-src 'self' data: https://lh3.googleusercontent.com https://media.licdn.com https://platform-lookaside.fbsbx.com https://flagcdn.com https://www.google.com https://*.gstatic.com",
              "font-src 'self'",
              "connect-src 'self' https://*.google-analytics.com https://www.googletagmanager.com",
              "frame-src 'none'",
              "object-src 'none'",
              "base-uri 'self'",
            ].join('; '),
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()',
          },
        ],
      },
    ];
  },
}

module.exports = withNextIntl(nextConfig)
