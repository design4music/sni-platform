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
    sitemap: [
      'https://www.worldbrief.info/sitemap.xml',
      'https://www.worldbrief.info/sitemap-days.xml',
    ],
  };
}
