import type { Metadata } from 'next';
import DashboardLayout from '@/components/DashboardLayout';
import { getOutletProfile, getOutletNarrativeFrames, getPublisherStats, getPublisherStance } from '@/lib/queries';
import { getCountryName } from '@/lib/countries';
import { getOutletLogoUrl } from '@/lib/logos';
import { getTrackLabel, getCentroidLabel, Track, PublisherStats, StanceScore } from '@/lib/types';
import { getTranslations } from 'next-intl/server';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import OutletMapSection from './OutletMapSection';

export const revalidate = 3600;

interface OutletPageProps {
  params: Promise<{ feed_name: string }>;
}

export async function generateMetadata({ params }: OutletPageProps): Promise<Metadata> {
  const { feed_name } = await params;
  const name = decodeURIComponent(feed_name);
  return {
    title: `${name} - Media Profile`,
    description: `Coverage analysis for ${name}: topics, regions, and narrative frames.`,
    alternates: { canonical: `/sources/${feed_name}` },
  };
}

function TrackBar({ distribution, tTracks }: { distribution: Record<string, number>; tTracks: (key: string) => string }) {
  const mainTracks: Record<string, number> = {};
  const trackMapping: Record<string, string> = {
    geo_politics: 'politics', geo_security: 'security', geo_economy: 'economy',
    geo_information: 'information', geo_humanitarian: 'humanitarian', geo_energy: 'energy',
  };
  for (const [track, share] of Object.entries(distribution)) {
    const main = trackMapping[track] || track;
    mainTracks[main] = (mainTracks[main] || 0) + share;
  }

  const COLORS: Record<string, string> = {
    politics: 'bg-purple-500/70', security: 'bg-red-500/70', economy: 'bg-green-500/70',
    information: 'bg-blue-500/70', humanitarian: 'bg-yellow-500/70', energy: 'bg-orange-500/70',
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

function stanceColor(score: number): string {
  if (score >= 1.0) return 'bg-green-500/80 text-white';
  if (score >= 0.3) return 'bg-green-500/40 text-green-200';
  if (score > -0.3) return 'bg-gray-500/30 text-gray-300';
  if (score > -1.0) return 'bg-red-500/40 text-red-200';
  return 'bg-red-500/80 text-white';
}

function stanceLabel(score: number, t: (key: string) => string): string {
  if (score >= 1.0) return t('stanceSupportive');
  if (score >= 0.3) return t('stanceFavorable');
  if (score > -0.3) return t('stanceNeutral');
  if (score > -1.0) return t('stanceCritical');
  return t('stanceHostile');
}

function StanceGrid({ scores, tSources, tCentroids }: { scores: StanceScore[]; tSources: (key: string) => string; tCentroids: (key: string) => string }) {
  if (scores.length === 0) return null;

  // Sort by absolute score descending (most opinionated first)
  const sorted = [...scores].sort((a, b) => Math.abs(b.score) - Math.abs(a.score));

  return (
    <div className="mb-10">
      <h2 className="text-2xl font-bold mb-2">{tSources('stanceTitle')}</h2>
      <p className="text-sm text-dashboard-text-muted mb-4">{tSources('stanceDesc')}</p>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
        {sorted.map(s => {
          const sign = s.score > 0 ? '+' : '';
          return (
            <div
              key={s.centroid_id}
              className={`rounded-lg px-3 py-2.5 ${stanceColor(s.score)} transition-colors`}
              title={`${(s.confidence * 100).toFixed(0)}% conf | ${s.sample_size} titles sampled`}
            >
              <div className="font-medium text-sm truncate">
                {getCentroidLabel(s.centroid_id, s.centroid_label, tCentroids)}
              </div>
              <div className="flex items-center justify-between mt-1">
                <span className="text-lg font-bold tabular-nums">
                  {sign}{s.score.toFixed(1)}
                </span>
                <span className="text-[10px] opacity-75">
                  {stanceLabel(s.score, tSources)}
                </span>
              </div>
            </div>
          );
        })}
      </div>
      <div className="flex items-center justify-center gap-4 mt-3 text-[10px] text-dashboard-text-muted">
        <span className="flex items-center gap-1"><span className="w-3 h-2 rounded bg-red-500/80 inline-block" /> -2 {tSources('stanceHostile')}</span>
        <span className="flex items-center gap-1"><span className="w-3 h-2 rounded bg-red-500/40 inline-block" /> -1 {tSources('stanceCritical')}</span>
        <span className="flex items-center gap-1"><span className="w-3 h-2 rounded bg-gray-500/30 inline-block" /> 0 {tSources('stanceNeutral')}</span>
        <span className="flex items-center gap-1"><span className="w-3 h-2 rounded bg-green-500/40 inline-block" /> +1 {tSources('stanceFavorable')}</span>
        <span className="flex items-center gap-1"><span className="w-3 h-2 rounded bg-green-500/80 inline-block" /> +2 {tSources('stanceSupportive')}</span>
      </div>
    </div>
  );
}

export default async function OutletPage({ params }: OutletPageProps) {
  const { feed_name } = await params;
  const name = decodeURIComponent(feed_name);

  const tCentroids = await getTranslations('centroids');
  const tTracks = await getTranslations('tracks');
  const tSources = await getTranslations('sources');

  const [profile, narrativeFrames, stats, stanceScores] = await Promise.all([
    getOutletProfile(name),
    getOutletNarrativeFrames(name),
    getPublisherStats(name),
    getPublisherStance(name),
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
            {domain && (
              <img src={logoUrl} alt="" className="w-12 h-12 object-contain rounded" />
            )}
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
              <StatCard
                label={tSources('statNarrativeFrames')}
                value={stats.narrative_frame_count}
                tooltip={tSources('statNarrativeFramesTooltip')}
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

        {/* Stance scores */}
        {stanceScores.length > 0 && (
          <StanceGrid scores={stanceScores} tSources={tSources} tCentroids={tCentroids} />
        )}

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

        {/* Narrative Frames */}
        {narrativeFrames.length > 0 && (
          <div className="mb-10">
            <h2 className="text-2xl font-bold mb-4">{tSources('narrativeFrames')}</h2>
            <p className="text-sm text-dashboard-text-muted mb-4">
              {tSources('narrativeFramesDesc')}
            </p>
            <div className="grid gap-3">
              {narrativeFrames.slice(0, 5).map((frame, i) => {
                const content = (
                  <div className="p-4 bg-dashboard-surface border border-dashboard-border rounded-lg hover:border-blue-500/50 transition">
                    <div className="font-medium">{frame.label}</div>
                    {frame.description && (
                      <p className="text-sm text-dashboard-text-muted mt-1 line-clamp-2">
                        {frame.description}
                      </p>
                    )}
                    <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-dashboard-text-muted">
                      <span className="uppercase bg-dashboard-border/50 px-1.5 py-0.5 rounded">
                        {frame.entity_type}
                      </span>
                      <span>{frame.entity_label}</span>
                      <span>{frame.title_count} {tSources('titles')}</span>
                    </div>
                  </div>
                );

                if (frame.entity_type === 'event') {
                  return (
                    <Link key={i} href={`/events/${frame.entity_id}`} className="block">
                      {content}
                    </Link>
                  );
                }
                return <div key={i}>{content}</div>;
              })}
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
