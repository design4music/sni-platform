import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import SessionWrapper from '@/components/SessionWrapper';
import Analytics from '@/components/Analytics';
import JsonLd from '@/components/JsonLd';
import { websiteJsonLd } from '@/lib/seo';
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

export default async function RootLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale?: string }>;
}) {
  const { locale } = await params;
  const lang = locale === 'de' ? 'de' : 'en';

  return (
    <html lang={lang}>
      <head>
        <JsonLd data={websiteJsonLd()} />
      </head>
      <body className={inter.className}>
        <SessionWrapper>{children}</SessionWrapper>
        <Analytics />
      </body>
    </html>
  );
}
