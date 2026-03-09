import type { Metadata } from 'next';
import { getAllActiveFeeds } from '@/lib/queries';
import DashboardLayout from '@/components/DashboardLayout';
import { Feed } from '@/lib/types';
import { COUNTRY_TO_REGION, getCountryName } from '@/lib/countries';
import { getOutletLogoUrl } from '@/lib/logos';
import SourceSuggestionForm from '@/components/SourceSuggestionForm';
import SourceCountryAccordion from '@/components/SourceCountryAccordion';
import { getTranslations } from 'next-intl/server';

export const revalidate = 3600;

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('sources');
  return {
    title: t('title'),
    description: t('metaDescription'),
    alternates: { canonical: '/sources' },
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
  const feeds = await getAllActiveFeeds();
  const groupedFeeds = groupFeedsByRegionAndCountry(feeds);

  const regionOrder = ['Americas', 'Europe', 'Asia', 'Middle East', 'Africa', 'Oceania', 'International Organizations'];
  const sortedRegions = regionOrder.filter(r => groupedFeeds[r]);

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-dashboard-text mb-4">
            {t('heading')}
          </h1>
          <p className="text-lg text-dashboard-text-muted leading-relaxed max-w-3xl">
            {t('description')}</p>
          <p className="text-lg text-dashboard-text-muted leading-relaxed max-w-3xl mb-6">
            {t('disclaimer')}</p>
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
                return { ...feed, domain, logoUrl: getOutletLogoUrl(domain, 32) };
              });
              return (
                <SourceCountryAccordion
                  key={countryCode}
                  countryCode={countryCode}
                  countryName={getCountryName(countryCode)}
                  feeds={feedsWithMeta}
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
