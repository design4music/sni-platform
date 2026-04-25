import type { Metadata } from 'next';
import DashboardLayout from '@/components/DashboardLayout';
import { getOutletProfile, getPublisherStats, getOutletStance, getOutletStanceMonths } from '@/lib/queries';
import { getCountryName } from '@/lib/countries';
import { getOutletLogoUrl } from '@/lib/logos';
import { buildPageMetadata, type Locale as SeoLocale } from '@/lib/seo';
import { getTrackLabel, getCentroidLabel, Track, PublisherStats } from '@/lib/types';
import { getTranslations, getLocale } from 'next-intl/server';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import OutletMapSection from './OutletMapSection';
import OutletLogo from '@/components/OutletLogo';
import OutletStanceSection from '@/components/OutletStanceSection';
import FlagImg from '@/components/FlagImg';
import SiblingOutlets from '@/components/SiblingOutlets';

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

// Live track palette (matches CentroidHero / TrackCard). Four tracks only —
// legacy geo_energy/_humanitarian/_information values are dropped rather than
// surfaced, per D-067.
const LIVE_TRACK_COLORS: Record<string, string> = {
  security: 'bg-red-400',
  politics: 'bg-sky-400',
  economy:  'bg-amber-400',
  society:  'bg-emerald-400',
};

function TrackBar({ distribution, tTracks }: { distribution: Record<string, number>; tTracks: (key: string) => string }) {
  const trackMapping: Record<string, string> = {
    geo_politics: 'politics',
    geo_security: 'security',
    geo_economy:  'economy',
    geo_society:  'society',
  };
  const mainTracks: Record<string, number> = {};
  let totalLive = 0;
  for (const [track, share] of Object.entries(distribution)) {
    const main = trackMapping[track];
    if (!main) continue; // drop legacy/unknown tracks
    mainTracks[main] = (mainTracks[main] || 0) + share;
    totalLive += share;
  }
  // Renormalise to 100% over the four live tracks (legacy slices are hidden).
  if (totalLive > 0 && totalLive < 0.999) {
    for (const k of Object.keys(mainTracks)) mainTracks[k] = mainTracks[k] / totalLive;
  }

  const entries = Object.entries(mainTracks).filter(([, s]) => s >= 0.01).sort((a, b) => b[1] - a[1]);
  if (entries.length === 0) return null;
  return (
    <div className="flex h-7 rounded-full overflow-hidden">
      {entries.map(([track, share]) => (
        <div
          key={track}
          className={`${LIVE_TRACK_COLORS[track] || 'bg-zinc-400'} relative group cursor-default`}
          style={{ width: `${Math.max(share * 100, 3)}%` }}
          title={`${tTracks('geo_' + track)}: ${(share * 100).toFixed(1)}%`}
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
  // Tooltip wraps within a hard max-width so it never extends past the viewport
  // and can never push the page layout sideways (root cause of the prior "white
  // vertical strip on the right" on mobile).
  return (
    <span className="group relative inline-block ml-1 cursor-help">
      <span className="text-blue-400/70 text-[9px] font-semibold border border-blue-400/30 rounded-full w-3.5 h-3.5 inline-flex items-center justify-center leading-none">i</span>
      <span className="invisible group-hover:visible absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 bg-dashboard-surface border border-dashboard-border rounded text-[11px] text-dashboard-text-muted z-50 shadow-lg w-56 max-w-[80vw] text-left leading-snug pointer-events-none">
        {text}
      </span>
    </span>
  );
}

function StatCard({ label, value, tooltip, sub, className = '' }: { label: string; value: string | number; tooltip?: string; sub?: string; className?: string }) {
  return (
    <div className={`px-3 py-2 bg-dashboard-surface border border-dashboard-border rounded-lg min-w-0 overflow-visible ${className}`}>
      <div className="text-base font-bold tabular-nums leading-tight truncate">{value}</div>
      <div className="text-[11px] text-dashboard-text-muted whitespace-nowrap">
        {label}
        {tooltip && <InfoTip text={tooltip} />}
      </div>
      {sub && <div className="text-[10px] text-dashboard-text-muted truncate">{sub}</div>}
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

  const [profile, stats, stanceMonths] = await Promise.all([
    getOutletProfile(name),
    getPublisherStats(name),
    getOutletStanceMonths(name),
  ]);

  if (!profile) notFound();

  const activeStanceMonth = stanceMonths[0] || null;
  const stanceEntities = activeStanceMonth
    ? await getOutletStance(name, activeStanceMonth)
    : [];

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

  // Mobile: horizontal-scroll carousel that bleeds to edges with -mx-4 / px-4.
  // md+: 5-up grid. Cards opt into a min-width on mobile only so they don't
  // collapse below readable size in the flex container.
  const cardClass = 'flex-shrink-0 min-w-[8.5rem] snap-start md:min-w-0';
  const statsGrid = (
    <div
      className="
        flex gap-2 overflow-x-auto -mx-4 px-4 snap-x snap-mandatory scrollbar-thin
        md:grid md:grid-cols-5 md:overflow-visible md:mx-0 md:px-0 md:snap-none
      "
    >
      <StatCard
        className={cardClass}
        label={tSources('statArticles')}
        value={profile.article_count.toLocaleString()}
        tooltip={tSources('statArticlesTooltip')}
      />
      <StatCard
        className={cardClass}
        label={tSources('statRegions')}
        value={stats?.centroid_count || profile.centroid_coverage.length}
        tooltip={tSources('statRegionsTooltip')}
      />
      <StatCard
        className={cardClass}
        label={tSources('statActiveTopics')}
        value={profile.top_ctms.length}
        tooltip={tSources('statActiveTopicsTooltip')}
      />
      {stats && (
        <>
          <StatCard
            className={cardClass}
            label={tSources('statGeoFocus')}
            value={stats.geo_hhi.toFixed(2)}
            tooltip={tSources('statGeoFocusTooltip')}
            sub={focusLabel!}
          />
          <StatCard
            className={cardClass}
            label={tSources('statSignalRichness')}
            value={stats.signal_richness.toFixed(1)}
            tooltip={tSources('statSignalRichnessTooltip')}
          />
        </>
      )}
    </div>
  );

  const trackDistributionBlock = stats && Object.keys(stats.track_distribution).length > 0 ? (
    <div>
      <h3 className="text-sm font-medium text-dashboard-text-muted mb-2">
        {tSources('trackDistribution')}
        <InfoTip text={tSources('trackDistributionTooltip')} />
      </h3>
      <TrackBar distribution={stats.track_distribution} tTracks={tTracks} />
    </div>
  ) : null;

  const coverageMapBlock = mapCentroids.length > 0 ? (
    <div>
      <h2 className="text-2xl font-bold mb-4">{tSources('coverageByRegion')}</h2>
      <OutletMapSection centroids={mapCentroids} />
    </div>
  ) : null;

  const publicationPatternBlock = stats && Object.keys(stats.dow_distribution).length > 0 ? (
    <div>
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
  ) : null;

  const topActorsBlock = stats && stats.top_actors.length > 0 ? (
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
              <span className="w-28 truncate text-dashboard-text">{a.name.replace(/_/g, ' ')}</span>
              <div className="flex-1 bg-dashboard-border/30 rounded-full h-3 overflow-hidden min-w-0">
                <div className="bg-purple-500/60 h-full rounded-full" style={{ width: `${barW}%` }} />
              </div>
              <span className="text-dashboard-text-muted tabular-nums text-xs w-10 text-right">
                {(a.share * 100).toFixed(1)}%
              </span>
            </div>
          );
        })}
      </div>
    </div>
  ) : null;

  const domainFocusBlock = stats && Object.keys(stats.domain_distribution).length > 0 ? (
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
                <span className="w-28 truncate text-dashboard-text">{domain.replace(/_/g, ' ')}</span>
                <div className="flex-1 bg-dashboard-border/30 rounded-full h-3 overflow-hidden min-w-0">
                  <div className="bg-blue-500/60 h-full rounded-full" style={{ width: `${barW}%` }} />
                </div>
                <span className="text-dashboard-text-muted tabular-nums text-xs w-10 text-right">
                  {(share * 100).toFixed(1)}%
                </span>
              </div>
            );
          })}
      </div>
    </div>
  ) : null;

  // Fallback to Top Topics when stance data is missing (small outlets
  // below the 15-title gate, or not yet backfilled for this outlet).
  const fallbackTopTopics = (!activeStanceMonth || stanceEntities.length === 0)
    && profile.top_ctms.length > 0 ? (() => {
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
        <div>
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
    })() : null;

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">
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
                {profile.country_code && (
                  <span className="inline-flex items-center gap-1.5">
                    <FlagImg iso2={profile.country_code} size={18} />
                    {getCountryName(profile.country_code)}
                  </span>
                )}
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

        {/* Upper section: main column (stats + map + pub pattern + track bar)
            | sidebar (actors + domains). Mirrors the centroid-page 2-col shape. */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-10">
          <div className="lg:col-span-2 space-y-8 min-w-0">
            {statsGrid}
            {trackDistributionBlock}
            {coverageMapBlock}
            {publicationPatternBlock}
          </div>
          <aside className="space-y-8 min-w-0">
            {topActorsBlock}
            {domainFocusBlock}
            <SiblingOutlets
              countryCode={profile.country_code}
              excludeFeedName={name}
              parentLanguageCode={profile.language_code}
            />
          </aside>
        </div>

        {/* Editorial Stance — full width, TrackCard-inspired cards 2 per row */}
        {activeStanceMonth && stanceEntities.length > 0 ? (
          <OutletStanceSection
            feedName={name}
            initialMonth={activeStanceMonth}
            initialEntities={stanceEntities}
            availableMonths={stanceMonths}
          />
        ) : fallbackTopTopics}
      </div>
    </DashboardLayout>
  );
}
