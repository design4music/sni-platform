/**
 * /sources/[slug] — Outlet landing dashboard.
 *
 * Cross-month overview: lifetime stats, months strip, stance heatmap,
 * publication pattern. Each month link goes to the canonical, indexable
 * /sources/[slug]/[YYYY-MM] detail page.
 *
 * Slug resolution: try the slug as-is (lowercased); if no match, slugify
 * the input (handles legacy URLs like /sources/Der%20Spiegel) and 308 to
 * the canonical form. If the outlet has no per-month data yet, redirect
 * to the /sources index.
 */

import type { Metadata } from 'next';
import Link from 'next/link';
import { redirect, notFound } from 'next/navigation';
import { getTranslations } from 'next-intl/server';
import DashboardLayout from '@/components/DashboardLayout';
import OutletLogo from '@/components/OutletLogo';
import OutletStanceHeatmap from '@/components/OutletStanceHeatmap';
import OutletEntityVolume from '@/components/OutletEntityVolume';
import OutletTrackTimeline from '@/components/OutletTrackTimeline';
import SiblingOutletsDropdown from '@/components/SiblingOutletsDropdown';
import FlagImg from '@/components/FlagImg';
import InfoTip from '@/components/InfoTip';
import {
  getOutletProfile,
  getPublisherStats,
  getOutletStanceMonths,
  getOutletStanceTimeline,
  getOutletTrackTimeline,
  getOutletEntityDailyVolume,
  getOutletMinorEntities,
  getSiblingOutlets,
} from '@/lib/queries';
import { resolveSlug } from '@/lib/slug-server';
import { getCountryName } from '@/lib/countries';
import { getOutletLogoUrl } from '@/lib/logos';
import { buildPageMetadata, type Locale as SeoLocale } from '@/lib/seo';

interface Props {
  params: Promise<{ locale: string; slug: string }>;
}

export const dynamic = 'force-dynamic';

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

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
/* Metadata                                                            */
/* ------------------------------------------------------------------ */

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale: localeRaw, slug } = await params;
  const locale = (localeRaw || 'en') as SeoLocale;
  const feedName = await resolveSlug(decodeURIComponent(slug).toLowerCase());
  if (!feedName) return { title: 'Not Found' };
  return buildPageMetadata({
    title:
      locale === 'de'
        ? `${feedName} — Redaktionelles Profil | WorldBrief`
        : `${feedName} — Editorial Profile | WorldBrief`,
    description:
      locale === 'de'
        ? `Monatsuebergreifendes Redaktionsprofil von ${feedName}: Haltung gegenueber Laendern und Personen, Themenverteilung, Berichterstattungsmuster.`
        : `Cross-month editorial profile of ${feedName}: stance toward countries and persons, topic distribution, coverage patterns.`,
    path: `/sources/${slug}`,
    locale,
  });
}

/* ------------------------------------------------------------------ */
/* Page                                                                */
/* ------------------------------------------------------------------ */

export default async function OutletLandingPage({ params }: Props) {
  const { locale, slug: rawSlug } = await params;

  // Slug must be canonical (lowercase, no URL-encoding). All in-site
  // links from /sources point straight at the canonical slug, so we
  // don't accept fuzzy matches here — anything that doesn't resolve
  // straight to a feed is a 404. Keeps the navigation a one-hop request.
  const canonicalSlug = decodeURIComponent(rawSlug).toLowerCase();
  const feedName = await resolveSlug(canonicalSlug);
  if (!feedName) notFound();

  const tCentroids = await getTranslations('centroids');
  void tCentroids;
  const tSources = await getTranslations('sources');

  const [
    profile,
    lifetimeStats,
    stanceMonths,
    stanceTimeline,
    trackTimeline,
    entityDaily,
    minorEntities,
  ] = await Promise.all([
    getOutletProfile(feedName),
    getPublisherStats(feedName),
    getOutletStanceMonths(feedName),
    getOutletStanceTimeline(feedName),
    getOutletTrackTimeline(feedName),
    getOutletEntityDailyVolume(feedName),
    getOutletMinorEntities(feedName),
  ]);

  if (!profile) notFound();

  // Sibling-outlet count drives whether we render the bottom row as
  // 2 or 3 columns. Cached query, so cheap.
  const siblings = profile.country_code
    ? await getSiblingOutlets(profile.country_code, feedName, 50)
    : [];
  const hasSiblings = siblings.length > 0;

  // No data anywhere → bounce to sources index.
  if (stanceMonths.length === 0 && !lifetimeStats) {
    redirect(`/${locale}/sources`);
  }

  // Gating rule: when an outlet has zero stance months, hide all
  // monthly-split content (browse strip, heatmap, sparklines, track
  // timeline). Page becomes a lifetime-only profile.
  const hasMonthlyContent = stanceMonths.length > 0;
  // Track timeline uses every available month from publisher_stats —
  // including months without stance scoring, so low-coverage outlets
  // can still see their topic mix. The chart itself handles the
  // 1-month fallback (renders a horizontal lifetime bar) so we always
  // pass the full timeline.
  const trackTimelineForChart = trackTimeline;

  const domain = profile.source_domain || '';
  const logoUrl = getOutletLogoUrl(domain, 64);

  const focusLabel = lifetimeStats
    ? lifetimeStats.geo_hhi >= 0.5
      ? tSources('focusNarrow')
      : lifetimeStats.geo_hhi >= 0.2
      ? tSources('focusModerate')
      : tSources('focusBroad')
    : null;

  const cardClass = 'flex-shrink-0 min-w-[8.5rem] snap-start md:min-w-0';
  // 5 cards when stance months exist (includes "Months tracked"), else 4.
  const gridColsClass = hasMonthlyContent ? 'md:grid-cols-5' : 'md:grid-cols-4';
  const statsGrid = lifetimeStats ? (
    <div className={`flex gap-2 overflow-x-auto -mx-4 px-4 snap-x snap-mandatory scrollbar-thin md:grid ${gridColsClass} md:overflow-visible md:mx-0 md:px-0 md:snap-none`}>
      <StatCard
        className={cardClass}
        label={tSources('totalArticles')}
        value={lifetimeStats.title_count.toLocaleString()}
        tooltip={tSources('statArticlesTooltip')}
      />
      {hasMonthlyContent && (
        <StatCard
          className={cardClass}
          label={tSources('monthsTracked')}
          value={stanceMonths.length}
        />
      )}
      <StatCard
        className={cardClass}
        label={tSources('statRegions')}
        value={lifetimeStats.centroid_count}
        tooltip={tSources('statRegionsTooltip')}
      />
      <StatCard
        className={cardClass}
        label={tSources('statGeoFocus')}
        value={lifetimeStats.geo_hhi.toFixed(2)}
        tooltip={tSources('statGeoFocusTooltip')}
        sub={focusLabel || undefined}
      />
      <StatCard
        className={cardClass}
        label={tSources('statSignalRichness')}
        value={lifetimeStats.signal_richness.toFixed(1)}
        tooltip={tSources('statSignalRichnessTooltip')}
      />
    </div>
  ) : null;

  const publicationPatternBlock =
    lifetimeStats && Object.keys(lifetimeStats.dow_distribution).length > 0 ? (
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

  const topActorsBlock =
    lifetimeStats && lifetimeStats.top_actors.length > 0 ? (
      <div>
        <h3 className="text-sm font-medium text-dashboard-text-muted mb-2">
          {tSources('topActors')}
          <InfoTip text={tSources('topActorsTooltip')} />
        </h3>
        <div className="space-y-1.5">
          {lifetimeStats.top_actors.slice(0, 8).map(a => {
            const barW = Math.round((a.share / (lifetimeStats.top_actors[0]?.share || 1)) * 100);
            return (
              <div key={a.name} className="flex items-center gap-2 text-sm">
                <span className="w-28 truncate text-dashboard-text">
                  {a.name.replace(/_/g, ' ')}
                </span>
                <div className="flex-1 bg-dashboard-border/30 rounded-full h-3 overflow-hidden min-w-0">
                  <div
                    className="bg-purple-500/60 h-full rounded-full"
                    style={{ width: `${barW}%` }}
                  />
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

  const domainFocusBlock =
    lifetimeStats && Object.keys(lifetimeStats.domain_distribution).length > 0 ? (
      <div>
        <h3 className="text-sm font-medium text-dashboard-text-muted mb-2">
          {tSources('domainFocus')}
          <InfoTip text={tSources('domainFocusTooltip')} />
        </h3>
        <div className="space-y-1.5">
          {Object.entries(lifetimeStats.domain_distribution)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 8)
            .map(([dom, share]) => {
              const maxShare = Math.max(...Object.values(lifetimeStats.domain_distribution));
              const barW = Math.round((share / maxShare) * 100);
              return (
                <div key={dom} className="flex items-center gap-2 text-sm">
                  <span className="w-28 truncate text-dashboard-text">
                    {dom.replace(/_/g, ' ')}
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
      </div>
    ) : null;

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6 pb-6 border-b border-dashboard-border">
          <Link href={`/${locale}/sources`} className="text-blue-400 hover:text-blue-300 text-sm">
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
            {hasMonthlyContent
              ? tSources('landingIntro', { name: profile.feed_name })
              : tSources('landingIntroLowCoverage', {
                  name: profile.feed_name,
                  n: lifetimeStats?.title_count ?? 0,
                })}
          </p>
        </div>

        {/* ---------------- Stance content (only outlets with stance data) ---------------- */}
        {hasMonthlyContent && (
          <>
            {stanceTimeline.length > 0 && (
              <OutletStanceHeatmap
                feedSlug={canonicalSlug}
                locale={locale}
                rows={stanceTimeline}
              />
            )}

            {stanceTimeline.length > 0 && entityDaily.length > 0 && (
              <OutletEntityVolume
                feedSlug={canonicalSlug}
                locale={locale}
                stanceRows={stanceTimeline}
                dailyRows={entityDaily}
                minorEntities={minorEntities}
              />
            )}

            {trackTimelineForChart.length > 0 && (
              <OutletTrackTimeline
                feedSlug={canonicalSlug}
                locale={locale}
                rows={trackTimelineForChart}
              />
            )}
          </>
        )}

        {/* ---------------- Lifetime overview ---------------- */}
        {lifetimeStats && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold mb-3">{tSources('lifetimeOverview')}</h2>
            {statsGrid}
          </div>
        )}

        {/* Track timeline for low-coverage variant — stance variant
            already rendered it above. The same component now shows
            both lifetime % (in the legend) and per-month % (via
            InfoTip on month chips). */}
        {!hasMonthlyContent && trackTimelineForChart.length > 0 && (
          <OutletTrackTimeline
            feedSlug={canonicalSlug}
            locale={locale}
            rows={trackTimelineForChart}
          />
        )}

        {/* ---------------- Bottom 3-col: top actors / domain focus / publication pattern ---------------- */}
        {(topActorsBlock || domainFocusBlock || publicationPatternBlock) && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
            {topActorsBlock && <div>{topActorsBlock}</div>}
            {domainFocusBlock && <div>{domainFocusBlock}</div>}
            {publicationPatternBlock && <div>{publicationPatternBlock}</div>}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

