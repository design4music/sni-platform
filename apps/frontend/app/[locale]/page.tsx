import { Suspense } from 'react';
import type { Metadata } from 'next';
import DashboardLayout from '@/components/DashboardLayout';
import TrendingCarousel from '@/components/TrendingCarousel';
import MapSection from '@/components/MapSection';
import SourceCarousel from '@/components/SourceCarousel';
import AnimatedStats from '@/components/AnimatedStats';
import EpicCard from '@/components/EpicCard';
import FocusCountrySection from '@/components/FocusCountrySection';
import { getCentroidsByClass, getAllActiveFeeds, getLatestEpics } from '@/lib/queries';
import { REGIONS, getCentroidLabel } from '@/lib/types';
import Link from 'next/link';
import { getTranslations, setRequestLocale, getLocale } from 'next-intl/server';

export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: 'WorldBrief - Understand the world. Briefly.',
  description: 'AI-powered global news intelligence. Multilingual coverage from 180+ sources, organized by country, theme, and narrative frame. Updated daily.',
  alternates: { canonical: '/' },
};

/* Deferred async server component for cross-country epics */
async function CrossCountryEpics() {
  const locale = await getLocale();
  const t = await getTranslations('home');
  const latestEpics = await getLatestEpics(3, locale);
  if (latestEpics.length === 0) return null;
  return (
    <section>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-3xl font-bold">{t('crossCountry')}</h2>
        <Link
          href="/epics"
          className="text-sm text-blue-400 hover:text-blue-300 transition"
        >
          {t('viewAll')}
        </Link>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {latestEpics.map(epic => (
          <EpicCard key={epic.id} epic={epic} />
        ))}
      </div>
    </section>
  );
}

export default async function HomePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);

  const t = await getTranslations('home');
  const tRegions = await getTranslations('regions');
  const tCentroids = await getTranslations('centroids');

  const [geoCentroids, feeds] = await Promise.all([
    getCentroidsByClass('geo', locale),
    getAllActiveFeeds(),
  ]);

  const geoCentroidsWithMap = geoCentroids
    .filter(c => c.iso_codes && c.iso_codes.length > 0 && !c.id.startsWith('NON-STATE-'))
    .map(c => ({ ...c, label: getCentroidLabel(c.id, c.label, tCentroids) }));

  // Group centroids by region for region cards
  const centroidsByRegion: Record<string, string[]> = {};
  for (const c of geoCentroids) {
    if (c.primary_theater && !c.id.startsWith('NON-STATE-')) {
      if (!centroidsByRegion[c.primary_theater]) centroidsByRegion[c.primary_theater] = [];
      centroidsByRegion[c.primary_theater].push(getCentroidLabel(c.id, c.label, tCentroids));
    }
  }

  // Region key mapping for translations
  const regionKeyMap: Record<string, string> = {
    EUROPE: 'europe',
    ASIA: 'asia',
    AFRICA: 'africa',
    AMERICAS: 'americas',
    OCEANIA: 'oceania',
    MIDEAST: 'mideast',
  };

  return (
    <DashboardLayout>
      <div className="space-y-12">
        {/* Introduction */}
        <section className="max-w-3xl">
          <h1 className="text-5xl font-bold mb-6">{t('heroTitle')}</h1>
          <p className="text-xl text-dashboard-text-muted mb-4">
            {t('heroSubtitle')}
          </p>
          <div className="flex gap-4">
            <Link href="/methodology" className="text-blue-400 hover:text-blue-300 underline">
              {t('howItWorks')}
            </Link>
          </div>
        </section>

        {/* Trending Now (deferred via Suspense) */}
        <Suspense fallback={
          <div className="animate-pulse">
            <div className="h-8 w-48 bg-dashboard-border rounded mb-6" />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-56 bg-dashboard-surface border border-dashboard-border rounded-lg" />
              ))}
            </div>
          </div>
        }>
          <TrendingCarousel />
        </Suspense>

        {/* Focus Country (logged-in users with focus centroid) */}
        <Suspense fallback={null}>
          <FocusCountrySection />
        </Suspense>

        {/* Map */}
        <MapSection centroids={geoCentroidsWithMap} />

        {/* Regions */}
        <section>
          <h2 className="text-3xl font-bold mb-6">{t('worldRegions')}</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(REGIONS).map(([key, _label]) => {
              const names = centroidsByRegion[key] || [];
              const tKey = regionKeyMap[key] || key.toLowerCase();
              return (
                <Link
                  key={key}
                  href={`/region/${key.toLowerCase()}`}
                  className="relative overflow-hidden p-6 border border-dashboard-border bg-dashboard-surface rounded-lg hover:border-blue-500 transition group"
                >
                  <div
                    className="absolute inset-0 opacity-40 pointer-events-none"
                    style={{
                      backgroundImage: `url(/geo/regions/${key.toLowerCase()}.png)`,
                      backgroundSize: 'cover',
                      backgroundPosition: 'center',
                    }}
                  />
                  <h3 className="relative text-xl font-semibold mb-2">{tRegions(tKey)}</h3>
                  <p className="relative text-sm text-dashboard-text-muted leading-relaxed">
                    {names.join(', ')}
                  </p>
                </Link>
              );
            })}
          </div>
          <p className="text-sm text-dashboard-text-muted mt-4">
            {t('coverageNote')}
          </p>
        </section>

        {/* Cross-Country Epics (deferred via Suspense) */}
        <Suspense fallback={
          <div className="animate-pulse">
            <div className="h-8 w-64 bg-dashboard-border rounded mb-6" />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-48 bg-dashboard-surface border border-dashboard-border rounded-lg" />
              ))}
            </div>
          </div>
        }>
          <CrossCountryEpics />
        </Suspense>

        {/* Sources Carousel */}
        <SourceCarousel feedCount={feeds.length} />

        {/* Animated Stats */}
        <AnimatedStats
          feedCount={feeds.length}
          languageCount={20}
          dailyArticles={5000}
          centroidCount={85}
        />
      </div>
    </DashboardLayout>
  );
}
