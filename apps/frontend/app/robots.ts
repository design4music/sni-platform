import { MetadataRoute } from 'next';

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        disallow: ['/api/'],
      },
    ],
    // Single index entry point. The two underlying sitemaps
    // (sitemap.xml + sitemap-days.xml) are referenced from the index;
    // they keep working at their direct URLs but we no longer advertise
    // them here. Standard pattern for multi-sitemap sites and gives GSC
    // a fresh URL after both individual sitemaps got stuck on
    // "Couldn't fetch" yesterday.
    sitemap: ['https://www.worldbrief.info/sitemap-index.xml'],
  };
}
