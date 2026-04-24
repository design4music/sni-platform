import type { Metadata } from 'next';
import DashboardLayout from '@/components/DashboardLayout';
import { getOutletProfile, getPublisherStats } from '@/lib/queries';
import { getCountryName } from '@/lib/countries';
import { getOutletLogoUrl } from '@/lib/logos';
import { buildPageMetadata, type Locale as SeoLocale } from '@/lib/seo';
import { getTrackLabel, getCentroidLabel, Track, PublisherStats } from '@/lib/types';
import { getTranslations, getLocale } from 'next-intl/server';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import OutletMapSection from './OutletMapSection';
import OutletLogo from '@/components/OutletLogo';

export const dynamic = 'force-dynamic';

interface OutletPageProps {
  params: Promise<{ feed_name: string }>;
}

export async function generateMetadata({ params }: OutletPageProps): Promise<Metadata> {
  const { feed_name } = await params;
  const locale = (await getLocale()) as SeoLocale;
  const name = decodeURIComponent(feed_name);
  return buildPageMetadata({
    title: locale === 'de' ? `${name} — Medienprofil` : `${name} — Media Profile`,
    description: locale === 'de'
      ? `Berichterstattungsanalyse für ${name}: Themen, Regionen und Medien-Frames.`
      : `Coverage analysis for ${name}: topics, regions, and narrative frames.`,
    path: `/sources/${feed_name}`,
    locale,
  });
}

function TrackBar({ distribution, tTracks }: { distribution: Record<string, number>; tTracks: (key: string) => string }) {
  const mainTracks: Record<string, number> = {};
  const trackMapping: Record<string, string> = {
    geo_politics: 'politics', geo_security: 'security', geo_economy: 'economy', geo_society: 'society',
  };
  for (const [track, share] of Object.entries(distribution)) {
    const main = trackMapping[track] || track;
    mainTracks[main] = (mainTracks[main] || 0) + share;
  }

  const COLORS: Record<string, string> = {
    politics: 'bg-purple-500/70', security: 'bg-red-500/70', economy: 'bg-green-500/70', society: 'bg-yellow-500/70',
  };

  const entries = Object.entries(mainTracks).filter(([, s]) => s >= 0.01).sort((a, b) => b[1] - a[1]);
  if (entries.length === 0) return null;
  return (
    <div className="flex h-7 rounded-full overflow-hidden">
      {entries.map(([track, share]) => (
        <div
          key={track}
          className={`${COLORS[track] || 'bg-gray-500/70'} relative group cursor-default`}
          style={{ width: `${Math.max(share * 100, 3)}%` }}
          title={`${track}: ${(share * 100).toFixed(1)}%`}
        >
          {share >= 0.08 && (
            <span className="absolute inset-0 flex items-center justify-center text-[10px] text-white font-medium truncate px-1">
              {track}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}

function InfoTip({ text }: { text: string }) {
  return (
    <span className="group relative inline-block ml-1 cursor-help">
      <span className="text-blue-400/70 text-[9px] font-semibold border border-blue-400/30 rounded-full w-3.5 h-3.5 inline-flex items-center justify-center leading-none">i</span>
      <span className="invisible group-hover:visible absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 bg-dashboard-surface border border-dashboard-border rounded text-[11px] text-dashboard-text-muted whitespace-nowrap z-50 shadow-lg">
        {text}
      </span>
    </span>
  );
}

function StatCard({ label, value, tooltip, sub }: { label: string; value: string | number; tooltip?: string; sub?: string }) {
  return (
    <div className="p-3 bg-dashboard-surface border border-dashboard-border rounded-lg">
      <div className="text-xl font-bold tabular-nums">{value}</div>
      <div className="text-xs text-dashboard-text-muted">
        {label}
        {tooltip && <InfoTip text={tooltip} />}
      </div>
      {sub && <div className="text-[10px] text-dashboard-text-muted mt-0.5">{sub}</div>}
    </div>
  );
}

function DowChart({ distribution }: { distribution: Record<string, number> }) {
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const values = days.map(d => distribution[d] || 0);
  const max = Math.max(...values, 0.001);
  return (
    <div className="flex items-end gap-1 h-12">
      {days.map((day, i) => (
        <div key={day} className="flex-1 flex flex-col items-center gap-0.5">
          <div
            className="w-full bg-blue-500/60 rounded-t"
            style={{ height: `${(values[i] / max) * 40}px` }}
          />
          <span className="text-[9px] text-dashboard-text-muted">{day.charAt(0)}</span>
        </div>
      ))}
    </div>
  );
}

// D-071: stanceColor / stanceLabel / StanceGrid retired with the per-(publisher,
// centroid, month) LLM score feature. Will be replaced by a new outlet × entity
// matrix component in Phase B.

export default async function OutletPage({ params }: OutletPageProps) {
  const { feed_name } = await params;
  const name = decodeURIComponent(feed_name);

  const tCentroids = await getTranslations('centroids');
  const tTracks = await getTranslations('tracks');
  const tSources = await getTranslations('sources');

  const [profile, stats] = await Promise.all([
    getOutletProfile(name),
    getPublisherStats(name),
  ]);

  if (!profile) notFound();

  const domain = profile.source_domain || '';
  const logoUrl = getOutletLogoUrl(domain, 64);

  // Prepare map data: convert centroid_coverage to WorldMap format
  const mapCentroids = profile.centroid_coverage
    .filter(c => c.iso_codes && c.iso_codes.length > 0)
    .map(c => ({
      id: c.centroid_id,
      label: getCentroidLabel(c.centroid_id, c.label, tCentroids),
      iso_codes: c.iso_codes!,
      source_count: c.count,
    }));

  const focusLabel = stats
    ? (stats.geo_hhi >= 0.5 ? tSources('focusNarrow') : stats.geo_hhi >= 0.2 ? tSources('focusModerate') : tSources('focusBroad'))
    : null;

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8 pb-8 border-b border-dashboard-border">
          <Link href="/sources" className="text-blue-400 hover:text-blue-300 text-sm">
            &larr; {tSources('allSources')}
          </Link>
          <div className="flex items-center gap-4 mt-4">
            <OutletLogo src={logoUrl} name={profile.feed_name} size={48} className="rounded" />
            <div>
              <h1 className="text-3xl md:text-4xl font-bold">{profile.feed_name}</h1>
              <div className="flex flex-wrap items-center gap-3 text-dashboard-text-muted mt-1">
                {profile.country_code && <span>{getCountryName(profile.country_code)}</span>}
                {profile.language_code && (
                  <span className="uppercase text-xs bg-dashboard-border/50 px-2 py-0.5 rounded">
                    {profile.language_code}
                  </span>
                )}
                {domain && (
                  <a
                    href={`https://${domain}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-400 hover:text-blue-300 text-sm"
                  >
                    {domain}
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Unified stats grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 mb-8">
          <StatCard
            label={tSources('statArticles')}
            value={profile.article_count.toLocaleString()}
            tooltip={tSources('statArticlesTooltip')}
          />
          <StatCard
            label={tSources('statRegions')}
            value={stats?.centroid_count || profile.centroid_coverage.length}
            tooltip={tSources('statRegionsTooltip')}
          />
          <StatCard
            label={tSources('statActiveTopics')}
            value={profile.top_ctms.length}
            tooltip={tSources('statActiveTopicsTooltip')}
          />
          {stats && (
            <>
              <StatCard
                label={tSources('statGeoFocus')}
                value={stats.geo_hhi.toFixed(2)}
                tooltip={tSources('statGeoFocusTooltip')}
                sub={focusLabel!}
              />
              <StatCard
                label={tSources('statSignalRichness')}
                value={stats.signal_richness.toFixed(1)}
                tooltip={tSources('statSignalRichnessTooltip')}
              />
            </>
          )}
        </div>

        {/* Track distribution */}
        {stats && Object.keys(stats.track_distribution).length > 0 && (
          <div className="mb-8">
            <h3 className="text-sm font-medium text-dashboard-text-muted mb-2">
              {tSources('trackDistribution')}
              <InfoTip text={tSources('trackDistributionTooltip')} />
            </h3>
            <TrackBar distribution={stats.track_distribution} tTracks={tTracks} />
          </div>
        )}

        {/* Coverage heatmap */}
        {mapCentroids.length > 0 && (
          <div className="mb-10">
            <h2 className="text-2xl font-bold mb-4">{tSources('coverageByRegion')}</h2>
            <OutletMapSection centroids={mapCentroids} />
          </div>
        )}

        {/* D-071: Stance scores block retired pending new outlet stance matrix. */}

        {/* Two-column: actors + domains */}
        {stats && (
          <div className="grid md:grid-cols-2 gap-6 mb-10">
            {stats.top_actors.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-dashboard-text-muted mb-2">
                  {tSources('topActors')}
                  <InfoTip text={tSources('topActorsTooltip')} />
                </h3>
                <div className="space-y-1.5">
                  {stats.top_actors.slice(0, 8).map(a => {
                    const barW = Math.round(a.share / (stats.top_actors[0]?.share || 1) * 100);
                    return (
                      <div key={a.name} className="flex items-center gap-2 text-sm">
                        <span className="w-40 truncate text-dashboard-text">{a.name.replace(/_/g, ' ')}</span>
                        <div className="flex-1 bg-dashboard-border/30 rounded-full h-3 overflow-hidden">
                          <div className="bg-purple-500/60 h-full rounded-full" style={{ width: `${barW}%` }} />
                        </div>
                        <span className="text-dashboard-text-muted tabular-nums text-xs w-12 text-right">
                          {(a.share * 100).toFixed(1)}%
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
            {Object.keys(stats.domain_distribution).length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-dashboard-text-muted mb-2">
                  {tSources('domainFocus')}
                  <InfoTip text={tSources('domainFocusTooltip')} />
                </h3>
                <div className="space-y-1.5">
                  {Object.entries(stats.domain_distribution)
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 8)
                    .map(([domain, share]) => {
                      const maxShare = Math.max(...Object.values(stats.domain_distribution));
                      const barW = Math.round(share / maxShare * 100);
                      return (
                        <div key={domain} className="flex items-center gap-2 text-sm">
                          <span className="w-40 truncate text-dashboard-text">{domain.replace(/_/g, ' ')}</span>
                          <div className="flex-1 bg-dashboard-border/30 rounded-full h-3 overflow-hidden">
                            <div className="bg-blue-500/60 h-full rounded-full" style={{ width: `${barW}%` }} />
                          </div>
                          <span className="text-dashboard-text-muted tabular-nums text-xs w-12 text-right">
                            {(share * 100).toFixed(1)}%
                          </span>
                        </div>
                      );
                    })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Temporal pattern */}
        {stats && Object.keys(stats.dow_distribution).length > 0 && (
          <div className="mb-10">
            <h3 className="text-sm font-medium text-dashboard-text-muted mb-2">
              {tSources('publicationPattern')}
              <InfoTip text={tSources('publicationPatternTooltip')} />
              {stats.peak_hour !== null && (
                <span className="ml-2 font-normal">
                  ({tSources('peakHour', { hour: `${String(stats.peak_hour).padStart(2, '0')}:00` })})
                </span>
              )}
            </h3>
            <DowChart distribution={stats.dow_distribution} />
          </div>
        )}

        {/* Top Topics (aggregated by centroid+track across months, max 9) */}
        {profile.top_ctms.length > 0 && (() => {
          const agg = new Map<string, { centroid_id: string; track: string; label: string; total: number; months: string[] }>();
          for (const ctm of profile.top_ctms) {
            const key = `${ctm.centroid_id}::${ctm.track}`;
            const existing = agg.get(key);
            if (existing) {
              existing.total += ctm.count;
              if (!existing.months.includes(ctm.month)) existing.months.push(ctm.month);
            } else {
              agg.set(key, { centroid_id: ctm.centroid_id, track: ctm.track, label: ctm.label, total: ctm.count, months: [ctm.month] });
            }
          }
          const topics = [...agg.values()].sort((a, b) => b.total - a.total).slice(0, 9);
          return (
            <div className="mb-10">
              <h2 className="text-2xl font-bold mb-4">{tSources('topTopics')}</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {topics.map(t => {
                  const latestMonth = t.months.sort().reverse()[0];
                  return (
                    <Link
                      key={`${t.centroid_id}::${t.track}`}
                      href={`/c/${t.centroid_id}/t/${t.track}?month=${latestMonth}`}
                      className="block p-4 bg-dashboard-surface border border-dashboard-border rounded-lg hover:border-blue-500/50 transition"
                    >
                      <div className="font-medium truncate">{getCentroidLabel(t.centroid_id, t.label, tCentroids)}</div>
                      <div className="text-sm text-dashboard-text-muted mt-0.5">
                        {getTrackLabel(t.track as Track, tTracks)}
                      </div>
                      <div className="flex items-center justify-between mt-2 text-xs text-dashboard-text-muted">
                        <span className="tabular-nums">{t.total} {tSources('articles')}</span>
                        <span>{t.months.length > 1 ? `${t.months.length} months` : latestMonth}</span>
                      </div>
                    </Link>
                  );
                })}
              </div>
            </div>
          );
        })()}

        {/* D-071: Narrative Frames block retired. 96% of rows were orphans
            after Jan-Apr reprocessing; will be replaced by per-outlet stance
            matrix against top entities. */}
      </div>
    </DashboardLayout>
  );
}
