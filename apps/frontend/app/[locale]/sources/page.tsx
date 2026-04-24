import type { Metadata } from 'next';
import { getAllActiveFeeds, getAllPublisherStats } from '@/lib/queries';
import DashboardLayout from '@/components/DashboardLayout';
import { Feed, PublisherStats } from '@/lib/types';
import { COUNTRY_TO_REGION, getCountryName } from '@/lib/countries';
import { getOutletLogoUrl } from '@/lib/logos';
import { buildAlternates } from '@/lib/seo';
import SourceSuggestionForm from '@/components/SourceSuggestionForm';
import SourceCountryAccordion from '@/components/SourceCountryAccordion';
import { getTranslations } from 'next-intl/server';
import Link from 'next/link';

export const dynamic = 'force-dynamic';

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('sources');
  return {
    title: t('title'),
    description: t('metaDescription'),
    alternates: buildAlternates('/sources'),
  };
}

function groupFeedsByRegionAndCountry(feeds: (Feed & { total_titles: number; assigned_titles: number })[]) {
  const grouped: Record<string, Record<string, typeof feeds>> = {};

  feeds.forEach(feed => {
    const countryCode = feed.country_code || 'GLOBAL';
    const region = COUNTRY_TO_REGION[countryCode] || 'Global';

    if (!grouped[region]) grouped[region] = {};
    if (!grouped[region][countryCode]) grouped[region][countryCode] = [];

    grouped[region][countryCode].push(feed);
  });

  return grouped;
}

export default async function SourcesPage() {
  const t = await getTranslations('sources');
  const [feeds, statsMap] = await Promise.all([
    getAllActiveFeeds(),
    getAllPublisherStats(),
  ]);
  const groupedFeeds = groupFeedsByRegionAndCountry(feeds);

  const regionOrder = ['Americas', 'Europe', 'Asia', 'Middle East', 'Africa', 'Oceania', 'International Organizations'];
  const sortedRegions = regionOrder.filter(r => groupedFeeds[r]);

  // Collect all i18n strings needed by the client component
  const labels = {
    statArticles: t('statArticles'),
    statGeoFocus: t('statGeoFocus'),
    statSignalRichness: t('statSignalRichness'),
    focusBroad: t('focusBroad'),
    focusModerate: t('focusModerate'),
    focusNarrow: t('focusNarrow'),
  };

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-dashboard-text mb-4">
            {t('heading')}
          </h1>
          <p className="text-lg text-dashboard-text-muted leading-relaxed max-w-3xl">
            {t('description')}</p>
          <p className="text-lg text-dashboard-text-muted leading-relaxed max-w-3xl mb-4">
            {t('disclaimer')}</p>
          {/* D-071: /sources/alignment link retired with the stance matrix. */}
        </div>

        {sortedRegions.map(region => (
          <div key={region} className="mb-10">
            <h2 className="text-2xl font-bold text-dashboard-text mb-4 border-b border-dashboard-border pb-2">
              {region === 'International Organizations' ? t('regionIntlOrgs') : region}
            </h2>

            {Object.entries(groupedFeeds[region]).sort(([a], [b]) => {
              const nameA = getCountryName(a);
              const nameB = getCountryName(b);
              return nameA.localeCompare(nameB);
            }).map(([countryCode, countryFeeds]) => {
              const feedsWithMeta = countryFeeds.map(feed => {
                const domain = feed.source_domain || feed.url.replace(/^https?:\/\//, '').split('/')[0];
                const s = statsMap[feed.name];
                return {
                  ...feed,
                  domain,
                  logoUrl: getOutletLogoUrl(domain, 32),
                  geo_hhi: s?.geo_hhi ?? null,
                  signal_richness: s?.signal_richness ?? null,
                  top_track: s ? Object.entries(s.track_distribution).sort((a, b) => b[1] - a[1])[0]?.[0] || null : null,
                };
              });
              return (
                <SourceCountryAccordion
                  key={countryCode}
                  countryCode={countryCode}
                  countryName={getCountryName(countryCode)}
                  feeds={feedsWithMeta}
                  labels={labels}
                />
              );
            })}
          </div>
        ))}

        <div className="mt-16 bg-dashboard-surface border border-dashboard-border rounded-lg p-8">
          <h2 className="text-2xl font-bold text-dashboard-text mb-4">
            {t('suggestHeading')}
          </h2>
          <p className="text-dashboard-text-muted mb-6">
            {t('suggestDescription')}
          </p>

          <SourceSuggestionForm />
        </div>
      </div>
    </DashboardLayout>
  );
}
