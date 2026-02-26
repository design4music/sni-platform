import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import SessionWrapper from '@/components/SessionWrapper';
import CookieBanner from '@/components/CookieBanner';
import Analytics from '@/components/Analytics';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

const SITE_URL = 'https://worldbrief.info';

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: 'WorldBrief - Understand the world. Briefly.',
    template: '%s | WorldBrief',
  },
  description: 'AI-powered global news intelligence. Multilingual coverage from 180+ sources organized by country, theme, and narrative frame.',
  openGraph: {
    type: 'website',
    siteName: 'WorldBrief',
    locale: 'en_US',
  },
  twitter: {
    card: 'summary',
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              '@context': 'https://schema.org',
              '@type': 'WebSite',
              name: 'WorldBrief',
              url: SITE_URL,
              description: 'AI-powered global news intelligence. Multilingual coverage from 180+ sources organized by country, theme, and narrative frame.',
              publisher: {
                '@type': 'Organization',
                name: 'WorldBrief',
                url: SITE_URL,
              },
            }),
          }}
        />
      </head>
      <body className={inter.className}>
        <SessionWrapper>{children}</SessionWrapper>
        <CookieBanner />
        <Analytics />
      </body>
    </html>
  );
}
