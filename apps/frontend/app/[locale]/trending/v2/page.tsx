import type { Metadata } from 'next';
import Link from 'next/link';
import { Suspense } from 'react';
import { notFound } from 'next/navigation';
import DashboardLayout from '@/components/DashboardLayout';
import TrendingHero from '@/components/TrendingHero';
import {
  getGlobalMonthView,
  getGlobalAvailableMonths,
  getActiveNarrativesGlobal,
  getFastestGrowingEvents,
  getTrendingSignals,
} from '@/lib/queries';
import type { GlobalMonthView, GlobalTrackSummary, GlobalTrackTopEvent } from '@/lib/queries';
import { setRequestLocale, getTranslations, getLocale } from 'next-intl/server';
import { buildPageMetadata, formatMonthLabel as formatMonthLabelSeo, humanizeEnum, formatCount, joinList, truncateDescription, type Locale as SeoLocale } from '@/lib/seo';

export const revalidate = 1800;

interface TrendingV2Props {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ month?: string }>;
}

// ─────────────────────────────────────────────────────────────
// Metadata
// ─────────────────────────────────────────────────────────────

export async function generateMetadata({ searchParams }: TrendingV2Props): Promise<Metadata> {
  const { month: requestedMonth } = await searchParams;
  const locale = (await getLocale()) as SeoLocale;
  const months = await getGlobalAvailableMonths();
  const activeMonth = requestedMonth && months.includes(requestedMonth)
    ? requestedMonth
    : months[0] || null;

  if (!activeMonth) {
    return buildPageMetadata({
      title: locale === 'de' ? 'Globales Briefing' : 'Global Briefing',
      description: locale === 'de'
        ? 'Das globale Nachrichtenbriefing von WorldBrief — Top-Themen und Trendgeschichten.'
        : "WorldBrief's global news briefing — top themes and trending stories.",
      path: '/trending/v2',
      locale,
    });
  }

  const monthLabel = formatMonthLabelSeo(activeMonth, locale);
  const view = await getGlobalMonthView(activeMonth, locale);
  let description: string;
  if (view) {
    const sectorCounts = new Map<string, number>();
    for (const tr of view.tracks) {
      for (const chip of tr.theme_chips) {
        sectorCounts.set(chip.sector, (sectorCounts.get(chip.sector) || 0) + chip.weight);
      }
    }
    const topSectors = [...sectorCounts.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([s]) => humanizeEnum(s));
    if (locale === 'de') {
      const parts = [`Globales Nachrichtenbriefing, ${monthLabel}: ${formatCount(view.total_sources, 'de')} Quellen aus ${view.active_centroid_count} Ländern.`];
      if (topSectors.length) parts.push(`Schwerpunkte: ${joinList(topSectors, 'de')}.`);
      parts.push('Mehrsprachige Übersicht.');
      description = truncateDescription(parts.join(' '));
    } else {
      const parts = [`Global news briefing, ${monthLabel}: ${formatCount(view.total_sources)} sources across ${view.active_centroid_count} countries.`];
      if (topSectors.length) parts.push(`Top themes: ${joinList(topSectors)}.`);
      parts.push('Multilingual overview.');
      description = truncateDescription(parts.join(' '));
    }
  } else {
    description = locale === 'de'
      ? `Globales Nachrichtenbriefing, ${monthLabel}.`
      : `Global news briefing, ${monthLabel}.`;
  }

  return buildPageMetadata({
    title: locale === 'de'
      ? `Globales Briefing — ${monthLabel}`
      : `Global Briefing — ${monthLabel}`,
    description,
    path: '/trending/v2',
    locale,
  });
}

// ─────────────────────────────────────────────────────────────
// Mechanical overview prose (v1 prototype — LLM version comes later via
// a global_summaries table mirroring centroid_summaries / D-065)
// ─────────────────────────────────────────────────────────────

function buildMechanicalOverview(view: GlobalMonthView, locale: SeoLocale): string[] {
  const paragraphs: string[] = [];

  // Paragraph 1: scale + dominant tracks
  const topTracks = [...view.tracks]
    .sort((a, b) => b.source_count - a.source_count)
    .slice(0, 2);
  if (locale === 'de') {
    paragraphs.push(
      `Im Berichtszeitraum sammelten ${view.active_centroid_count} Länder zusammen ${formatCount(view.total_events, 'de')} Topereignisse, gestützt auf ${formatCount(view.total_sources, 'de')} Quellenerwähnungen. ` +
      `Die Agenda wurde vor allem von ${topTracks.map(t => formatTrackLabel(t.track).toLowerCase()).join(' und ')} geprägt.`
    );
  } else {
    paragraphs.push(
      `Across ${view.active_centroid_count} countries this period, ${formatCount(view.total_events)} headline-level events surfaced, backed by ${formatCount(view.total_sources)} source mentions. ` +
      `The agenda leaned heavily on ${topTracks.map(t => formatTrackLabel(t.track).toLowerCase()).join(' and ')}.`
    );
  }

  // Paragraph 2: top 3 events by source count
  const flatTops = view.tracks
    .flatMap(t => t.top_events.map(e => ({ ...e, track: t.track })))
    .sort((a, b) => b.source_count - a.source_count)
    .slice(0, 3);
  if (flatTops.length > 0) {
    const lines = flatTops.map(e =>
      `${e.title.trim()} (${e.centroid_label}, ${formatCount(e.source_count, locale)} sources)`
    );
    if (locale === 'de') {
      paragraphs.push(`Drei Stories dominierten die Reichweite: ${lines.join('; ')}.`);
    } else {
      paragraphs.push(`Three stories dominated reach: ${lines.join('; ')}.`);
    }
  }

  // Paragraph 3: top themes composite
  const sectorCounts = new Map<string, number>();
  for (const tr of view.tracks) {
    for (const chip of tr.theme_chips) {
      sectorCounts.set(chip.sector, (sectorCounts.get(chip.sector) || 0) + chip.weight);
    }
  }
  const topSectors = [...sectorCounts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4)
    .map(([s]) => humanizeEnum(s));
  if (topSectors.length > 0) {
    if (locale === 'de') {
      paragraphs.push(`Wiederkehrende Themen: ${joinList(topSectors, 'de')}.`);
    } else {
      paragraphs.push(`Recurring themes this period: ${joinList(topSectors)}.`);
    }
  }

  return paragraphs;
}

function formatTrackLabel(track: string): string {
  return track.replace(/^geo_/, '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

const TRACK_COLORS: Record<string, string> = {
  geo_security: 'border-red-400/60 bg-red-400/5',
  geo_politics: 'border-sky-400/60 bg-sky-400/5',
  geo_economy: 'border-amber-400/60 bg-amber-400/5',
  geo_society: 'border-emerald-400/60 bg-emerald-400/5',
};
const TRACK_ACCENT: Record<string, string> = {
  geo_security: 'text-red-300',
  geo_politics: 'text-sky-300',
  geo_economy: 'text-amber-300',
  geo_society: 'text-emerald-300',
};

// ─────────────────────────────────────────────────────────────
// Track card: global track summary with top 5 events + theme chips.
// Events deep-link to their origin centroid-track page.
// ─────────────────────────────────────────────────────────────

function GlobalTrackCard({ track, activeMonth }: { track: GlobalTrackSummary; activeMonth: string }) {
  const label = formatTrackLabel(track.track);
  const accent = TRACK_ACCENT[track.track] || 'text-dashboard-text';
  const border = TRACK_COLORS[track.track] || 'border-dashboard-border bg-dashboard-surface';

  return (
    <div className={`rounded-lg border p-4 ${border}`}>
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <h3 className={`text-lg font-semibold ${accent}`}>{label}</h3>
          <div className="text-[11px] text-dashboard-text-muted tabular-nums">
            {track.event_count.toLocaleString('en-US')} events · {track.source_count.toLocaleString('en-US')} sources
          </div>
        </div>
      </div>

      {track.theme_chips.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {track.theme_chips.map((chip, i) => (
            <span
              key={`${chip.sector}-${i}`}
              className="text-[10px] px-1.5 py-0.5 rounded bg-dashboard-border/40 text-dashboard-text-muted"
            >
              {humanizeEnum(chip.sector)}
              {' · '}
              {humanizeEnum(chip.subject)}
              <span className="ml-1 tabular-nums opacity-70">{Math.round(chip.weight * 100)}%</span>
            </span>
          ))}
        </div>
      )}

      <ul className="space-y-1.5">
        {track.top_events.map(ev => (
          <TopEventRow key={ev.id} ev={ev} activeMonth={activeMonth} />
        ))}
      </ul>
    </div>
  );
}

function TopEventRow({ ev, activeMonth }: { ev: GlobalTrackTopEvent; activeMonth: string }) {
  const href = ev.has_event_page
    ? `/events/${ev.id}`
    : `/c/${ev.centroid_id}/t/geo_politics?month=${activeMonth}`; // fallback: origin centroid
  return (
    <li>
      <Link
        href={href}
        className="block px-2 py-1.5 rounded hover:bg-dashboard-border/30 transition group"
      >
        <div className="text-sm text-dashboard-text group-hover:text-blue-300 leading-snug">
          {ev.title}
        </div>
        <div className="text-[10px] text-dashboard-text-muted tabular-nums mt-0.5">
          {ev.centroid_label} · {ev.source_count} sources · {ev.date}
        </div>
      </Link>
    </li>
  );
}

// ─────────────────────────────────────────────────────────────
// Fastest-growing panel (only meaningful on current month)
// ─────────────────────────────────────────────────────────────

async function FastestGrowingPanel({ month, locale, isCurrentMonth }: { month: string; locale: string; isCurrentMonth: boolean }) {
  if (!isCurrentMonth) return null;
  const events = await getFastestGrowingEvents(month, 10, locale);
  if (events.length === 0) {
    return (
      <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-4">
        <h3 className="text-base font-semibold text-amber-300 mb-2">Fastest-growing · last 7 days</h3>
        <p className="text-sm text-dashboard-text-muted">No surging stories meet the threshold yet.</p>
      </div>
    );
  }
  return (
    <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-4">
      <h3 className="text-base font-semibold text-amber-300 mb-3">Fastest-growing · last 7 days</h3>
      <ul className="space-y-2">
        {events.map(ev => (
          <li key={ev.id}>
            <Link
              href={`/events/${ev.id}`}
              className="block px-2 py-1.5 rounded hover:bg-amber-500/10 transition group"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="text-sm text-dashboard-text group-hover:text-amber-200 leading-snug">
                    {ev.title}
                  </div>
                  <div className="text-[10px] text-dashboard-text-muted tabular-nums mt-0.5">
                    {ev.centroid_label} · {formatTrackLabel(ev.track).toLowerCase()}
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <div className="text-sm font-semibold text-amber-300 tabular-nums">
                    +{ev.recent_7d_sources}
                  </div>
                  <div className="text-[10px] text-dashboard-text-muted tabular-nums">
                    {ev.total_sources} total · {Math.round(ev.growth_ratio * 100)}% new
                  </div>
                </div>
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Sidebar rails
// ─────────────────────────────────────────────────────────────

async function ActiveNarrativesRail({ month, locale }: { month: string; locale: string }) {
  const narratives = await getActiveNarrativesGlobal(month, 10, locale);
  if (narratives.length === 0) return null;
  return (
    <div>
      <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-2">
        Active Narratives
      </h3>
      <ul className="space-y-1.5">
        {narratives.map(n => (
          <li key={n.id}>
            <Link
              href={`/narratives/${n.id}`}
              className="flex items-start justify-between gap-2 text-sm py-0.5 rounded hover:text-blue-400 transition"
            >
              <span className="text-dashboard-text line-clamp-2 leading-snug">{n.name}</span>
              <span className="text-xs text-dashboard-text-muted shrink-0 tabular-nums">
                {n.event_count}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

async function TrendingSignalsRail() {
  const signals = await getTrendingSignals();
  const SIGNAL_LABELS: Record<string, string> = {
    persons: 'Top Persons',
    orgs: 'Top Organizations',
    places: 'Top Places',
    commodities: 'Top Commodities',
    policies: 'Top Policies',
  };
  const types = Object.keys(SIGNAL_LABELS);

  return (
    <div>
      <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-2">
        <Link href="/signals" className="hover:text-blue-400 transition">
          Trending Signals
        </Link>
      </h3>
      <div className="space-y-3">
        {types.map(type => {
          const items = signals[type];
          if (!items || items.length === 0) return null;
          return (
            <div key={type}>
              <div className="text-[10px] font-semibold text-dashboard-text-muted uppercase tracking-wider mb-1">
                <Link href={`/signals/${type}`} className="hover:text-blue-400 transition">
                  {SIGNAL_LABELS[type]}
                </Link>
              </div>
              <ul className="space-y-1">
                {items.slice(0, 5).map(item => (
                  <li key={item.value}>
                    <Link
                      href={`/signals/${item.signal_type}/${encodeURIComponent(item.value)}`}
                      className="flex items-center justify-between text-sm py-0.5 rounded hover:text-blue-400 transition"
                    >
                      <span className="truncate text-dashboard-text">{item.value}</span>
                      <span className="text-xs text-dashboard-text-muted shrink-0 ml-2 tabular-nums">
                        {item.event_count}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Page
// ─────────────────────────────────────────────────────────────

export default async function TrendingV2Page({ params, searchParams }: TrendingV2Props) {
  const { locale } = await params;
  const { month: requestedMonth } = await searchParams;
  setRequestLocale(locale);
  const seoLocale = locale as SeoLocale;

  const months = await getGlobalAvailableMonths();
  if (months.length === 0) return notFound();

  const activeMonth = requestedMonth && months.includes(requestedMonth)
    ? requestedMonth
    : months[0];

  const view = await getGlobalMonthView(activeMonth, locale);
  if (!view) return notFound();

  // Current month = latest available month with any activity. Treat it as MTD
  // for UX copy + fastest-growing panel promotion.
  const isCurrentMonth = activeMonth === months[0];

  const overviewParagraphs = buildMechanicalOverview(view, seoLocale);
  const totalLabel = locale === 'de'
    ? `Globales Briefing · ${formatMonthLabelSeo(activeMonth, 'de')}`
    : `Global Briefing · ${formatMonthLabelSeo(activeMonth, 'en')}`;

  const sidebar = (
    <div className="lg:sticky lg:top-24 space-y-6">
      <Suspense fallback={null}>
        <ActiveNarrativesRail month={activeMonth} locale={locale} />
      </Suspense>
      <Suspense fallback={null}>
        <TrendingSignalsRail />
      </Suspense>
    </div>
  );

  return (
    <DashboardLayout sidebar={sidebar}>
      {/* Hero */}
      <div className="mb-8">
        <TrendingHero
          view={view}
          activeMonth={activeMonth}
          isCurrentMonth={isCurrentMonth}
          totalLabel={totalLabel}
        />
      </div>

      {/* Overview prose (mechanical stub for v1) */}
      <div className="mb-8 prose prose-invert max-w-none">
        <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-3">
          {locale === 'de' ? 'Überblick' : 'Overview'}
        </h3>
        {overviewParagraphs.map((p, i) => (
          <p key={i} className="text-base leading-relaxed text-dashboard-text mb-3">
            {p}
          </p>
        ))}
        <p className="text-[11px] text-dashboard-text-muted mt-2 italic">
          Mechanical summary · editorial version to follow.
        </p>
      </div>

      {/* Fastest-growing panel — hero-prominence on current month only */}
      {isCurrentMonth && (
        <div className="mb-8">
          <Suspense fallback={null}>
            <FastestGrowingPanel month={activeMonth} locale={locale} isCurrentMonth={isCurrentMonth} />
          </Suspense>
        </div>
      )}

      {/* 4 track cards in 2x2 grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        {view.tracks.map(t => (
          <GlobalTrackCard key={t.track} track={t} activeMonth={activeMonth} />
        ))}
      </div>

      {/* On past months, fastest-growing was omitted above — render a closing
          note so the layout doesn't feel truncated. */}
      {!isCurrentMonth && (
        <p className="text-[11px] text-dashboard-text-muted italic mb-8">
          Fastest-growing panel is only shown for the live month.
        </p>
      )}
    </DashboardLayout>
  );
}
