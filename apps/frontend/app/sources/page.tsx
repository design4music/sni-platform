import type { Metadata } from 'next';
import { getAllActiveFeeds } from '@/lib/queries';
import DashboardLayout from '@/components/DashboardLayout';
import { Feed } from '@/lib/types';
import { COUNTRY_TO_REGION, getCountryName } from '@/lib/countries';
import { getOutletLogoUrl } from '@/lib/logos';
import SourceSuggestionForm from '@/components/SourceSuggestionForm';
import Link from 'next/link';

export const revalidate = 600;

export const metadata: Metadata = {
  title: 'Media Sources',
  description: 'Curated list of 180+ international media sources powering WorldBrief, spanning 6 continents and dozens of languages.',
  alternates: { canonical: '/sources' },
};

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
  const feeds = await getAllActiveFeeds();
  const groupedFeeds = groupFeedsByRegionAndCountry(feeds);

  const regionOrder = ['Americas', 'Europe', 'Asia', 'Middle East', 'Africa', 'Oceania', 'Global'];
  const sortedRegions = regionOrder.filter(r => groupedFeeds[r]);

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-dashboard-text mb-4">
            Our Sources
          </h1>
          <p className="text-lg text-dashboard-text-muted leading-relaxed max-w-3xl">
            WorldBrief aggregates reporting from a curated network of international media and strategic communication channels. By combining multilingual and regionally diverse sources, the system aims to reduce informational blind spots and reflect the world&apos;s civilizational plurality.</p>
          <p className="text-lg text-dashboard-text-muted leading-relaxed max-w-3xl mb-6">
            Inclusion does not imply endorsement.</p>
        </div>

        {sortedRegions.map(region => (
          <div key={region} className="mb-10">
            <h2 className="text-2xl font-bold text-dashboard-text mb-4 border-b border-dashboard-border pb-2">
              {region}
            </h2>

            {Object.entries(groupedFeeds[region]).sort(([a], [b]) => {
              const nameA = getCountryName(a);
              const nameB = getCountryName(b);
              return nameA.localeCompare(nameB);
            }).map(([countryCode, countryFeeds]) => (
              <div key={countryCode} className="mb-6">
                <h3 className="text-lg font-semibold text-dashboard-text mb-2">
                  {getCountryName(countryCode)}
                </h3>

                <div className="divide-y divide-dashboard-border/50">
                  {countryFeeds.map(feed => {
                    const domain = feed.source_domain || feed.url.replace(/^https?:\/\//, '').split('/')[0];
                    const logoUrl = getOutletLogoUrl(domain, 32);

                    return (
                      <div
                        key={feed.id}
                        className="flex items-center gap-4 py-3 px-2 -mx-2 rounded hover:bg-dashboard-surface transition-colors group"
                      >
                        <img
                          src={logoUrl}
                          alt=""
                          className="w-5 h-5 flex-shrink-0 object-contain"
                        />
                        <Link
                          href={`/sources/${encodeURIComponent(feed.name)}`}
                          className="font-medium text-dashboard-text group-hover:text-blue-400 transition-colors flex-1 min-w-0 truncate"
                        >
                          {feed.name}
                        </Link>
                        <span className="text-xs text-dashboard-text-muted flex-shrink-0 uppercase">
                          {feed.language_code}
                        </span>
                        {feed.total_titles > 0 && (
                          <span className="text-xs text-dashboard-text-muted flex-shrink-0 tabular-nums w-24 text-right">
                            {feed.assigned_titles.toLocaleString()} / {feed.total_titles.toLocaleString()}
                          </span>
                        )}
                        <a
                          href={`https://${domain}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex-shrink-0"
                        >
                          <svg
                            className="w-3.5 h-3.5 text-dashboard-text-muted/50 hover:text-white transition-colors"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                        </a>
                      </div>
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
