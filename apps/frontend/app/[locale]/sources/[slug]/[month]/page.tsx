import type { Metadata } from 'next';
import DashboardLayout from '@/components/DashboardLayout';
import {
  getOutletProfile,
  getPublisherStats,
  getPublisherStatsMonthly,
  getOutletStance,
  getOutletStanceMonths,
  getSiblingOutlets,
  type PublisherStatsMonthly,
} from '@/lib/queries';
import { resolveSlug } from '@/lib/slug-server';
import { getCountryName } from '@/lib/countries';
import { getOutletLogoUrl } from '@/lib/logos';
import { buildPageMetadata, type Locale as SeoLocale } from '@/lib/seo';
import { getTranslations } from 'next-intl/server';
import { notFound, redirect } from 'next/navigation';
import Link from 'next/link';
import OutletLogo from '@/components/OutletLogo';
import OutletStanceSection from '@/components/OutletStanceSection';
import OutletStanceBricks from '@/components/OutletStanceBricks';
import SiblingOutletsDropdown from '@/components/SiblingOutletsDropdown';
import FlagImg from '@/components/FlagImg';
import InfoTip from '@/components/InfoTip';

export const dynamic = 'force-dynamic';

interface OutletMonthPageProps {
  params: Promise<{ locale: string; slug: string; month: string }>;
}

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

function isValidMonth(s: string): boolean {
  return /^\d{4}-\d{2}$/.test(s);
}

function formatMonthLong(month: string, locale: string): string {
  const [y, m] = month.split('-').map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString(
    locale === 'de' ? 'de-DE' : 'en-US',
    { month: 'long', year: 'numeric' }
  );
}

function formatMonthShort(month: string, locale: string): string {
  const [y, m] = month.split('-').map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString(
    locale === 'de' ? 'de-DE' : 'en-US',
    { month: 'short' }
  );
}

const LIVE_TRACK_COLORS: Record<string, string> = {
  security: 'bg-red-400',
  politics: 'bg-sky-400',
  economy: 'bg-amber-400',
  society: 'bg-emerald-400',
};

function TrackBar({
  distribution,
  tTracks,
}: {
  distribution: Record<string, number>;
  tTracks: (key: string) => string;
}) {
  const trackMapping: Record<string, string> = {
    geo_politics: 'politics',
    geo_security: 'security',
    geo_economy: 'economy',
    geo_society: 'society',
  };
  const mainTracks: Record<string, number> = {};
  let totalLive = 0;
  for (const [track, share] of Object.entries(distribution)) {
    const main = trackMapping[track];
    if (!main) continue;
    mainTracks[main] = (mainTracks[main] || 0) + share;
    totalLive += share;
  }
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

function StatCard({
  label,
  value,
  tooltip,
  sub,
  className = '',
}: {
  label: string;
  value: string | number;
  tooltip?: string;
  sub?: string;
  className?: string;
}) {
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

/* ------------------------------------------------------------------ */
/* Month switcher                                                      */
/* ------------------------------------------------------------------ */

function MonthSwitcher({
  slug,
  locale,
  current,
  available,
  prefix,
}: {
  slug: string;
  locale: string;
  current: string;
  available: string[];
  prefix: string;
}) {
  const idx = available.indexOf(current);
  const newer = idx > 0 ? available[idx - 1] : null;
  const older = idx >= 0 && idx < available.length - 1 ? available[idx + 1] : null;
  if (available.length === 0) return null;

  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6 pb-4 border-b border-dashboard-border">
      {/* Timeline of months */}
      <nav className="flex items-center gap-1 flex-wrap min-w-0" aria-label={prefix}>
        {available.slice().reverse().map(m => {
          const active = m === current;
          return (
            <Link
              key={m}
              href={`/${locale}/sources/${slug}/${m}`}
              aria-current={active ? 'page' : undefined}
              className={`px-2.5 py-1 rounded-md text-xs tabular-nums transition ${
                active
                  ? 'bg-blue-500 text-white cursor-default font-medium'
                  : 'bg-dashboard-surface border border-dashboard-border text-dashboard-text-muted hover:text-dashboard-text hover:border-blue-500/40'
              }`}
            >
              {formatMonthShort(m, locale)} {m.split('-')[0].slice(2)}
            </Link>
          );
        })}
      </nav>
      {/* Prev / Next */}
      <div className="flex items-center gap-1 shrink-0">
        {older ? (
          <Link
            href={`/${locale}/sources/${slug}/${older}`}
            className="px-3 py-1.5 text-sm text-dashboard-text-muted hover:text-dashboard-text border border-dashboard-border rounded hover:bg-dashboard-border/30 transition"
          >
            ‹ {formatMonthShort(older, locale)}
          </Link>
        ) : null}
        {newer ? (
          <Link
            href={`/${locale}/sources/${slug}/${newer}`}
            className="px-3 py-1.5 text-sm text-dashboard-text-muted hover:text-dashboard-text border border-dashboard-border rounded hover:bg-dashboard-border/30 transition"
          >
            {formatMonthShort(newer, locale)} ›
          </Link>
        ) : null}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Metadata                                                            */
/* ------------------------------------------------------------------ */

export async function generateMetadata({ params }: OutletMonthPageProps): Promise<Metadata> {
  const { locale: localeRaw, slug, month } = await params;
  const locale = (localeRaw || 'en') as SeoLocale;
  if (!isValidMonth(month)) return { title: 'Not Found' };
  const feedName = await resolveSlug(decodeURIComponent(slug).toLowerCase());
  if (!feedName) return { title: 'Not Found' };
  const monthLabel = formatMonthLong(month, locale);

  // Months without stance data are kept reachable but excluded from
  // search indexes — they are useful as deep-links from existing URLs
  // but not as canonical pages we want surfaced.
  const stanceMonths = await getOutletStanceMonths(feedName);
  const isStanceMonth = stanceMonths.includes(month);

  const meta = buildPageMetadata({
    title:
      locale === 'de'
        ? `${feedName} — ${monthLabel} | Redaktionelle Haltung`
        : `${feedName} — ${monthLabel} | Editorial Stance`,
    description:
      locale === 'de'
        ? `Berichterstattungsanalyse für ${feedName} im ${monthLabel}: redaktionelle Haltung, Themen, Regionen und Akteure.`
        : `Coverage analysis for ${feedName} in ${monthLabel}: editorial stance, topics, regions, and key actors.`,
    path: `/sources/${slug}/${month}`,
    locale,
  });
  if (!isStanceMonth) {
    meta.robots = { index: false, follow: true };
  }
  return meta;
}

/* ------------------------------------------------------------------ */
/* Page                                                                */
/* ------------------------------------------------------------------ */

export default async function OutletMonthPage({ params }: OutletMonthPageProps) {
  const { locale, slug: rawSlug, month } = await params;
  if (!isValidMonth(month)) notFound();

  const slug = decodeURIComponent(rawSlug).toLowerCase();
  const feedName = await resolveSlug(slug);
  if (!feedName) notFound();

  const tCentroids = await getTranslations('centroids');
  const tTracks = await getTranslations('tracks');
  const tSources = await getTranslations('sources');

  const [profile, lifetimeStats, monthlyStats, stanceMonths, stanceEntities] = await Promise.all([
    getOutletProfile(feedName),
    getPublisherStats(feedName),  // lifetime — used for publication pattern only
    getPublisherStatsMonthly(feedName, month),
    getOutletStanceMonths(feedName),  // only stance months are linkable
    getOutletStance(feedName, month),
  ]);

  if (!profile) notFound();

  // If the requested month has no data of any kind, redirect to the
  // most recent stance month — that's the canonical entry. If no
  // stance months exist either, bounce to the outlet landing.
  if (!monthlyStats && stanceEntities.length === 0) {
    if (stanceMonths.length > 0 && stanceMonths[0] !== month) {
      redirect(`/${locale}/sources/${slug}/${stanceMonths[0]}`);
    }
    if (stanceMonths.length === 0) {
      redirect(`/${locale}/sources/${slug}`);
    }
  }

  // Available months for the in-page switcher = stance months only.
  // Stats-only months are reachable by direct URL but are noindex and
  // not linked from anywhere on this site.
  const availableMonths = stanceMonths;

  // Sibling outlets — same as landing page; surfaced in header dropdown.
  const siblings = profile.country_code
    ? await getSiblingOutlets(profile.country_code, feedName, 50)
    : [];
  const hasSiblings = siblings.length > 0;

  const domain = profile.source_domain || '';
  const logoUrl = getOutletLogoUrl(domain, 64);
  const monthLabel = formatMonthLong(month, locale);

  const stats: PublisherStatsMonthly | null = monthlyStats;
  const focusLabel = stats
    ? stats.geo_hhi >= 0.5
      ? tSources('focusNarrow')
      : stats.geo_hhi >= 0.2
      ? tSources('focusModerate')
      : tSources('focusBroad')
    : null;

  /* ---------------- Stats grid (mobile carousel, md grid) ---------------- */
  const cardClass = 'flex-shrink-0 min-w-[8.5rem] snap-start md:min-w-0';
  const statsGrid = stats ? (
    <div className="flex gap-2 overflow-x-auto -mx-4 px-4 snap-x snap-mandatory scrollbar-thin md:grid md:grid-cols-5 md:overflow-visible md:mx-0 md:px-0 md:snap-none">
      <StatCard className={cardClass} label={tSources('statArticles')} value={stats.title_count.toLocaleString()} tooltip={tSources('statArticlesTooltip')} />
      <StatCard className={cardClass} label={tSources('statRegions')} value={stats.centroid_count} tooltip={tSources('statRegionsTooltip')} />
      <StatCard className={cardClass} label={tSources('statActiveTopics')} value={Object.keys(stats.action_distribution).length} tooltip={tSources('statActiveTopicsTooltip')} />
      <StatCard className={cardClass} label={tSources('statGeoFocus')} value={stats.geo_hhi.toFixed(2)} tooltip={tSources('statGeoFocusTooltip')} sub={focusLabel || undefined} />
      <StatCard className={cardClass} label={tSources('statSignalRichness')} value={stats.signal_richness.toFixed(1)} tooltip={tSources('statSignalRichnessTooltip')} />
    </div>
  ) : null;

  const trackDistributionBlock = stats && Object.keys(stats.track_distribution).length > 0 ? (
    <div>
      <h3 className="text-sm font-medium text-dashboard-text-muted mb-2">
        {tSources('trackDistribution')}
        <InfoTip text={tSources('trackDistributionTooltip')} />
      </h3>
      <TrackBar distribution={stats.track_distribution} tTracks={tTracks} />
    </div>
  ) : null;


  // Publication pattern stays lifetime — DoW per single month is too
  // sparse to be meaningful. Vertical bar list matches Top actors /
  // Domain focus styling so the 3-col footer reads as one block.
  const publicationPatternBlock = lifetimeStats && Object.keys(lifetimeStats.dow_distribution).length > 0 ? (
    (() => {
      const dayKeys = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'] as const;
      const dayLabels: Record<(typeof dayKeys)[number], string> = {
        Mon: tSources('dayMon'),
        Tue: tSources('dayTue'),
        Wed: tSources('dayWed'),
        Thu: tSources('dayThu'),
        Fri: tSources('dayFri'),
        Sat: tSources('daySat'),
        Sun: tSources('daySun'),
      };
      const values = dayKeys.map(d => lifetimeStats.dow_distribution[d] || 0);
      const max = Math.max(...values, 0.001);
      return (
        <div>
          <h3 className="text-sm font-medium text-dashboard-text-muted mb-2">
            {tSources('publicationPattern')}
            <InfoTip text={tSources('publicationPatternTooltip')} />
            <span className="ml-2 text-[10px] uppercase tracking-wider text-dashboard-text-muted/70">
              {tSources('allTime')}
            </span>
          </h3>
          <div className="space-y-1.5">
            {dayKeys.map((d, i) => {
              const share = values[i];
              const barW = Math.round((share / max) * 100);
              return (
                <div key={d} className="flex items-center gap-2 text-sm">
                  <span className="w-28 truncate text-dashboard-text">
                    {dayLabels[d]}
                  </span>
                  <div className="flex-1 bg-dashboard-border/30 rounded-full h-3 overflow-hidden min-w-0">
                    <div
                      className="bg-blue-500/60 h-full rounded-full"
                      style={{ width: `${barW}%` }}
                    />
                  </div>
                  <span className="text-dashboard-text-muted tabular-nums text-xs w-10 text-right">
                    {(share * 100).toFixed(1)}%
                  </span>
                </div>
              );
            })}
          </div>
          {lifetimeStats.peak_hour !== null && (
            <p className="mt-2 text-[11px] text-dashboard-text-muted">
              {tSources('peakHour', {
                hour: `${String(lifetimeStats.peak_hour).padStart(2, '0')}:00`,
              })}
            </p>
          )}
        </div>
      );
    })()
  ) : null;

  const topActorsBlock = stats && stats.top_actors.length > 0 ? (
    <div>
      <h3 className="text-sm font-medium text-dashboard-text-muted mb-2">
        {tSources('topActors')}
        <InfoTip text={tSources('topActorsTooltip')} />
      </h3>
      <div className="space-y-1.5">
        {stats.top_actors.slice(0, 8).map(a => {
          const barW = Math.round((a.share / (stats.top_actors[0]?.share || 1)) * 100);
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
          .map(([dom, share]) => {
            const maxShare = Math.max(...Object.values(stats.domain_distribution));
            const barW = Math.round((share / maxShare) * 100);
            return (
              <div key={dom} className="flex items-center gap-2 text-sm">
                <span className="w-28 truncate text-dashboard-text">{dom.replace(/_/g, ' ')}</span>
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

  /* ---------------- Page render ---------------- */
  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">
        {/* Header — permanent identity */}
        <div className="mb-6 pb-6 border-b border-dashboard-border">
          <nav
            aria-label="Breadcrumb"
            className="flex flex-wrap items-center gap-1.5 text-sm text-dashboard-text-muted"
          >
            <Link
              href={`/${locale}/sources`}
              className="text-blue-400 hover:text-blue-300"
            >
              &larr; {tSources('allSources')}
            </Link>
            <span aria-hidden>/</span>
            <Link
              href={`/${locale}/sources/${slug}`}
              className="text-blue-400 hover:text-blue-300"
            >
              {profile.feed_name}
            </Link>
          </nav>
          <div className="flex items-center gap-4 mt-4">
            <OutletLogo src={logoUrl} name={profile.feed_name} size={48} className="rounded" />
            <div>
              <h1 className="text-3xl md:text-4xl font-bold">
                {profile.feed_name}
                <span className="text-dashboard-text-muted font-normal">
                  {' · '}
                  {monthLabel}
                </span>
              </h1>
              <div className="flex flex-wrap items-center gap-3 text-dashboard-text-muted mt-1">
                {profile.country_code && (
                  <span className="inline-flex items-center gap-1.5">
                    <FlagImg iso2={profile.country_code} size={18} />
                    {getCountryName(profile.country_code)}
                  </span>
                )}
                {profile.language_code && (
                  <span className="uppercase text-xs bg-dashboard-border/50 px-2 py-0.5 rounded">{profile.language_code}</span>
                )}
                {domain && (
                  <a href={`https://${domain}`} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300 text-sm">
                    {domain}
                  </a>
                )}
                {hasSiblings && profile.country_code && (
                  <SiblingOutletsDropdown
                    outlets={siblings}
                    countryName={getCountryName(profile.country_code) || profile.country_code}
                    parentLanguageCode={profile.language_code}
                  />
                )}
              </div>
            </div>
          </div>

          <p className="mt-4 text-sm text-dashboard-text-muted max-w-3xl leading-snug">
            {tSources('monthlyIntro', { name: profile.feed_name, month: monthLabel })}
          </p>
        </div>

        {/* Prominent month switcher (timeline + prev/next) */}
        <MonthSwitcher
          slug={slug}
          locale={locale}
          current={month}
          available={availableMonths}
          prefix={tSources('monthSwitcherLabel')}
        />

        {/* Empty state when this month has no data of any kind */}
        {!stats && stanceEntities.length === 0 ? (
          <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-8 text-center text-dashboard-text-muted">
            {tSources('noDataForMonth', { month: monthLabel })}
          </div>
        ) : (
          <>
            {/* Editorial-stance brick grid — quick visual summary, anchors
                to detailed cards below */}
            {stanceEntities.length > 0 && (
              <OutletStanceBricks entities={stanceEntities} />
            )}

            {/* Editorial-stance detail cards — full text, patterns,
                evidence. Section drops its own month label and switcher
                (page H1 + the strip above already cover that). */}
            {stanceEntities.length > 0 && (
              <OutletStanceSection
                feedName={feedName}
                feedSlug={slug}
                initialMonth={month}
                initialEntities={stanceEntities}
                availableMonths={availableMonths}
                locale={locale}
                hideMonthSwitcher
                hideMonthInTitle
              />
            )}

            {/* {Month} overview */}
            {stats && (
              <div className="mb-8">
                <h2 className="text-2xl font-bold mb-3">
                  {tSources('monthOverview', { month: monthLabel })}
                </h2>
                <div className="space-y-6">
                  {statsGrid}
                  {trackDistributionBlock}
                </div>
              </div>
            )}

            {/* 3-col footer — top actors / domain focus / publication pattern */}
            {(topActorsBlock || domainFocusBlock || publicationPatternBlock) && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
                {topActorsBlock && <div>{topActorsBlock}</div>}
                {domainFocusBlock && <div>{domainFocusBlock}</div>}
                {publicationPatternBlock && <div>{publicationPatternBlock}</div>}
              </div>
            )}
          </>
        )}
      </div>
    </DashboardLayout>
  );
}

