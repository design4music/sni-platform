import { getAllActiveFeeds } from '@/lib/queries';
import DashboardLayout from '@/components/DashboardLayout';
import { Feed } from '@/lib/types';
import { COUNTRY_NAMES, COUNTRY_TO_REGION, getCountryName } from '@/lib/countries';
import { getOutletLogoUrl } from '@/lib/logos';
import SourceSuggestionForm from '@/components/SourceSuggestionForm';
import Image from 'next/image';

export const dynamic = 'force-dynamic';

function groupFeedsByRegionAndCountry(feeds: Feed[]) {
  const grouped: Record<string, Record<string, Feed[]>> = {};

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
  const feeds = await getAllActiveFeeds();
  const groupedFeeds = groupFeedsByRegionAndCountry(feeds);

  const regionOrder = ['Americas', 'Europe', 'Asia', 'Middle East', 'Africa', 'Oceania', 'Global'];
  const sortedRegions = regionOrder.filter(r => groupedFeeds[r]);

  return (
    <DashboardLayout>
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-dashboard-text mb-4">
            Our Sources
          </h1>
          <p className="text-lg text-dashboard-text-muted leading-relaxed max-w-3xl">
            WorldBrief aggregates reporting from a curated network of international media and strategic communication channels. By combining multilingual and regionally diverse sources, the system aims to reduce informational blind spots and reflect the world’s civilizational plurality.</p>
          <p className="text-lg text-dashboard-text-muted leading-relaxed max-w-3xl mb-6">
            Inclusion does not imply endorsement.</p>
        </div>

        {sortedRegions.map(region => (
          <div key={region} className="mb-12">
            <h2 className="text-2xl font-bold text-dashboard-text mb-6 border-b border-dashboard-border pb-2">
              {region}
            </h2>

            {Object.entries(groupedFeeds[region]).sort(([a], [b]) => {
              const nameA = getCountryName(a);
              const nameB = getCountryName(b);
              return nameA.localeCompare(nameB);
            }).map(([countryCode, countryFeeds]) => (
              <div key={countryCode} className="mb-8">
                <h3 className="text-xl font-semibold text-dashboard-text mb-4">
                  {getCountryName(countryCode)}
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {countryFeeds.map(feed => {
                    const domain = feed.source_domain || feed.url.replace(/^https?:\/\//, '').split('/')[0];
                    const logoUrl = getOutletLogoUrl(domain, 32);

                    return (
                      <a
                        key={feed.id}
                        href={feed.source_domain || feed.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="bg-dashboard-surface border border-dashboard-border rounded p-4 hover:border-dashboard-text-muted transition-colors group"
                      >
                        <div className="flex items-start gap-3">
                          <div className="w-8 h-8 flex-shrink-0 bg-dashboard-border rounded flex items-center justify-center overflow-hidden">
                            <img
                              src={logoUrl}
                              alt=""
                              className="w-6 h-6 object-contain opacity-70 grayscale group-hover:opacity-100 group-hover:grayscale-0 transition-all"
                            />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-dashboard-text group-hover:text-white transition-colors truncate">
                              {feed.name}
                            </p>
                            <p className="text-sm text-dashboard-text-muted mt-1">
                              {feed.language_code.toUpperCase()}
                            </p>
                          </div>
                          <svg
                            className="w-4 h-4 text-dashboard-text-muted group-hover:text-white transition-colors flex-shrink-0"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                        </div>
                      </a>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        ))}

        <div className="mt-16 bg-dashboard-surface border border-dashboard-border rounded-lg p-8">
          <h2 className="text-2xl font-bold text-dashboard-text mb-4">
            Suggest a Source
          </h2>
          <p className="text-dashboard-text-muted mb-6">
            Know a source we should track? Submit your suggestion below.
          </p>

          <SourceSuggestionForm />
        </div>
      </div>
    </DashboardLayout>
  );
}
