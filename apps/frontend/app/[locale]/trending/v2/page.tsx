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
  getGlobalDayTopEvents,
} from '@/lib/queries';
import type { GlobalMonthView, GlobalTrackSummary, GlobalTrackTopEvent, GlobalDayTopEvent } from '@/lib/queries';
import { setRequestLocale, getTranslations, getLocale } from 'next-intl/server';
import { buildPageMetadata, formatMonthLabel as formatMonthLabelSeo, humanizeEnum, truncateDescription, type Locale as SeoLocale } from '@/lib/seo';

export const revalidate = 1800;

interface TrendingV2Props {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ month?: string; day?: string }>;
}

// "Today" anchor for live vs archive decisions. Month view's last stripe entry
// is the latest day with any activity — treat that as today even if the real
// clock is ahead. Prevents weekend/late-pipeline flicker.
function resolveTodayIso(view: GlobalMonthView): string {
  const dates = view.activity_stripe.map(e => e.date).sort();
  return dates[dates.length - 1] || new Date().toISOString().slice(0, 10);
}

function isValidDay(day: string | undefined, view: GlobalMonthView): day is string {
  if (!day) return false;
  if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) return false;
  return view.activity_stripe.some(e => e.date === day);
}

function formatDayLong(day: string, locale: SeoLocale): string {
  const [y, m, d] = day.split('-').map(Number);
  return new Date(y, m - 1, d).toLocaleDateString(locale === 'de' ? 'de-DE' : 'en-US', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
  });
}

// ─────────────────────────────────────────────────────────────
// Metadata
// ─────────────────────────────────────────────────────────────

// Shared strings for live-view title/description. Keep under ~60 / 160 chars
// respectively to avoid Google truncation.
const LIVE_TITLE_EN = 'Most covered international news and emerging stories';
const LIVE_TITLE_DE = 'Meistberichtete Weltnachrichten und aufkommende Stories';
const LIVE_DESC_EN =
  'See what the world is covering right now: top stories across politics, security, economy, and society, plus emerging stories gaining traction. Click any past day to open its archive.';
const LIVE_DESC_DE =
  'Sehen Sie, was die Welt gerade berichtet: Top-Meldungen aus Politik, Sicherheit, Wirtschaft und Gesellschaft sowie aufkommende Stories. Klicken Sie einen Tag für das Archiv.';

export async function generateMetadata({ searchParams }: TrendingV2Props): Promise<Metadata> {
  const { month: requestedMonth, day: requestedDay } = await searchParams;
  const locale = (await getLocale()) as SeoLocale;
  const months = await getGlobalAvailableMonths();
  const activeMonth = requestedMonth && months.includes(requestedMonth)
    ? requestedMonth
    : months[0] || null;

  if (!activeMonth) {
    return buildPageMetadata({
      title: locale === 'de' ? LIVE_TITLE_DE : LIVE_TITLE_EN,
      description: truncateDescription(locale === 'de' ? LIVE_DESC_DE : LIVE_DESC_EN),
      path: '/trending/v2',
      locale,
    });
  }

  const monthLabel = formatMonthLabelSeo(activeMonth, locale);
  const view = await getGlobalMonthView(activeMonth, locale);

  // Archive day — distinct indexable page per closed day. Self-referential
  // canonical preserving the ?day= param so Google ranks days individually.
  if (view && isValidDay(requestedDay, view)) {
    const dayLabel = formatDayLong(requestedDay, locale);
    const title = locale === 'de'
      ? `Top-Weltnachrichten am ${dayLabel}`
      : `Top world news on ${dayLabel}`;
    const description = locale === 'de'
      ? `Top-Weltnachrichten am ${dayLabel}: die meistberichteten Stories des Tages aus allen Ländern und Themen, mit Rang-Änderungen im Vergleich zum Vortag.`
      : `Top international news on ${dayLabel}: the most-covered stories that day, cross-centroid, with rank-change indicators vs the prior day.`;
    const canonicalPath = `/trending/v2?month=${activeMonth}&day=${requestedDay}`;
    return buildPageMetadata({
      title,
      description: truncateDescription(description),
      path: canonicalPath,
      locale,
      ogType: 'article',
    });
  }

  // Live view: static explainer description + month in the title.
  // Keep total title under ~60 chars so Google doesn't truncate.
  const title = locale === 'de'
    ? `${LIVE_TITLE_DE} · ${monthLabel}`
    : `${LIVE_TITLE_EN} · ${monthLabel}`;
  return buildPageMetadata({
    title,
    description: truncateDescription(locale === 'de' ? LIVE_DESC_DE : LIVE_DESC_EN),
    path: '/trending/v2',
    locale,
  });
}

// ─────────────────────────────────────────────────────────────
// "About this page" explainer — replaces the old mechanical month summary.
// Static content (same every visit). Four short paragraphs answering:
// what the page is, what the reader is seeing, what to pay attention to,
// and how to use the archive. Localized EN/DE.
// ─────────────────────────────────────────────────────────────

interface AboutBlock {
  heading: string;
  body: string;
}

function buildAboutBlocks(locale: SeoLocale): AboutBlock[] {
  if (locale === 'de') {
    return [
      {
        heading: 'Worum es hier geht',
        body:
          "WorldBriefs globaler Nachrichten-Puls — was über 200 Medien weltweit im Moment am stärksten berichten, aggregiert über 74 Länder und Regionen sowie vier strategische Tracks: Politik, Sicherheit, Wirtschaft, Gesellschaft.",
      },
      {
        heading: 'Was Sie sehen',
        body:
          'Die Kalender-Grafik oben zeigt das tägliche Quellenvolumen des letzten Monats, farblich aufgeschlüsselt nach dominierendem Track. Die vier Karten unten listen die Top-5-Stories pro Track für den Zeitraum. Das Feld „Fastest-growing" hebt Stories hervor, die in den letzten 7 Tagen am stärksten zugelegt haben — das Nächstliegende zu „aufkommend".',
      },
      {
        heading: 'Worauf Sie achten sollten',
        body:
          '„Active Narratives" (Seitenleiste) zeigt, welchen strategischen Frames diese Ereignisse angehören. „Trending Signals" listet die am häufigsten erwähnten Personen, Orte und Organisationen.',
      },
      {
        heading: 'Das Archiv',
        body:
          'Klicken Sie auf einen vergangenen Tag im Kalender, um die Berichterstattung dieses Tages zu öffnen: die Top 10 Ereignisse, geordnet nach 7-Tage-Quellensumme, mit ★ NEW / ↑ steigend / ↓ fallend / ● gehalten-Kennzeichnungen. Jede Archiv-Seite ist dauerhaft — teilbar und merkbar.',
      },
    ];
  }
  return [
    {
      heading: 'What this is',
      body:
        "WorldBrief's global news pulse — what 200+ media outlets around the world are covering most right now, aggregated across 74 countries and regions and four strategic tracks: politics, security, economy, society.",
    },
    {
      heading: "What you're looking at",
      body:
        "The calendar above shows daily source volume for the last month, color-segmented by the dominant track. The four cards below list the top-5 stories per track for the period. The Fastest-growing panel highlights stories gaining the most new sources in the last 7 days — the closest thing to \"emerging\".",
    },
    {
      heading: 'What to pay attention to',
      body:
        'Active Narratives (sidebar) shows which strategic frames these events fit into. Trending Signals lists the people, places, and organizations appearing in the most stories.',
    },
    {
      heading: 'The archive',
      body:
        'Click any past day on the calendar to open that day\'s coverage: the top 10 events ranked by 7-day cumulative source count, with ★ NEW / ↑ rising / ↓ falling / ● held indicators. Each archive day is a permanent page — shareable, bookmarkable.',
    },
  ];
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

// ─────────────────────────────────────────────────────────────
// Archive day view — list of top events for one closed date.
// Each event gets a mechanical annotation vs the prior day:
//   ★ NEW        — not in yesterday's top list
//   ↑N           — rank improved by N
//   ↓N           — rank dropped by N
//   ● held       — same position
// Prose placeholder lives here; real prose ships with daily_briefs
// global-scope rows (step 3).
// ─────────────────────────────────────────────────────────────

type Annotation =
  | { kind: 'new' }
  | { kind: 'rising'; delta: number }
  | { kind: 'falling'; delta: number }
  | { kind: 'held' };

function annotateDayEvents(
  today: GlobalDayTopEvent[],
  yesterday: GlobalDayTopEvent[]
): Array<{ ev: GlobalDayTopEvent; note: Annotation }> {
  const yRank = new Map<string, number>();
  yesterday.forEach((e, i) => yRank.set(e.id, i + 1));
  return today.map((ev, i) => {
    const prev = yRank.get(ev.id);
    if (prev == null) return { ev, note: { kind: 'new' } as Annotation };
    const delta = prev - (i + 1);
    if (delta === 0) return { ev, note: { kind: 'held' } };
    if (delta > 0) return { ev, note: { kind: 'rising', delta } };
    return { ev, note: { kind: 'falling', delta: -delta } };
  });
}

// Annotation badges: unified shape, project palette. Matches WeeklyDeviationCard
// severity markers (red=negative, amber=warning, green=positive, blue=info,
// muted border=quiet).
const BADGE_BASE =
  'inline-flex items-center justify-center min-w-[52px] px-2 py-0.5 rounded border text-[10px] font-semibold uppercase tracking-wider tabular-nums';

function AnnotationBadge({ note }: { note: Annotation }) {
  if (note.kind === 'new') {
    return (
      <span
        className={`${BADGE_BASE} bg-blue-500/15 border-blue-500/40 text-blue-300`}
      >
        ★ new
      </span>
    );
  }
  if (note.kind === 'rising') {
    return (
      <span
        className={`${BADGE_BASE} bg-green-500/15 border-green-500/40 text-green-300`}
      >
        ↑ {note.delta}
      </span>
    );
  }
  if (note.kind === 'falling') {
    return (
      <span
        className={`${BADGE_BASE} bg-red-500/15 border-red-500/40 text-red-300`}
      >
        ↓ {note.delta}
      </span>
    );
  }
  return (
    <span
      className={`${BADGE_BASE} bg-dashboard-border/20 border-dashboard-border/60 text-dashboard-text-muted`}
    >
      ● held
    </span>
  );
}

function formatTrackBadge(track: string): string {
  return track.replace(/^geo_/, '');
}

// Short day label for prev/next nav buttons. "Mon 6".
function formatDayShort(dateStr: string): string {
  const [y, m, d] = dateStr.split('-').map(Number);
  const dt = new Date(y, m - 1, d);
  const wd = dt.toLocaleDateString('en-US', { weekday: 'short' });
  return `${wd} ${d}`;
}

// Days with any activity (sources > 0), sorted ascending, used for prev/next
// step-through within the month. Anchored to today means same-month days only —
// cross-month day nav is a follow-up.
function activeDaysOf(view: GlobalMonthView): string[] {
  return view.activity_stripe
    .filter(e => e.total_sources > 0)
    .map(e => e.date)
    .sort();
}

async function ArchiveDayView({
  day,
  activeMonth,
  view,
  locale,
}: {
  day: string;
  activeMonth: string;
  view: GlobalMonthView;
  locale: SeoLocale;
}) {
  const [today, yesterday] = await Promise.all([
    getGlobalDayTopEvents(day, 10, locale),
    getGlobalDayTopEvents(
      new Date(new Date(day).getTime() - 86400000).toISOString().slice(0, 10),
      10,
      locale
    ),
  ]);

  const rows = annotateDayEvents(today, yesterday);
  const dayLabel = formatDayLong(day, locale);

  const days = activeDaysOf(view);
  const idx = days.indexOf(day);
  const prevDay = idx > 0 ? days[idx - 1] : null;
  const nextDay = idx >= 0 && idx < days.length - 1 ? days[idx + 1] : null;
  const hrefFor = (d: string) => `/trending/v2?month=${activeMonth}&day=${d}`;
  // "Today" link — jump to live view. Only shown when we're not already on today.
  const todayHref = `/trending/v2?month=${activeMonth}`;

  return (
    <section>
      {/* Day nav: prev/next arrows flanking the current day heading.
          Mirrors CalendarDayPanel pattern. */}
      <div className="flex items-center justify-between gap-2 mb-5">
        {prevDay ? (
          <Link
            href={hrefFor(prevDay)}
            className="flex items-center gap-1 px-2 py-1 text-sm text-dashboard-text-muted hover:text-dashboard-text transition whitespace-nowrap"
            aria-label={`Previous day: ${formatDayShort(prevDay)}`}
          >
            ‹<span className="hidden sm:inline"> {formatDayShort(prevDay)}</span>
          </Link>
        ) : (
          <span
            className="flex items-center gap-1 px-2 py-1 text-sm text-dashboard-text-muted opacity-30 cursor-default whitespace-nowrap"
            aria-hidden="true"
          >
            ‹
          </span>
        )}
        <h2 className="text-2xl font-semibold text-dashboard-text text-center min-w-0 truncate">
          {dayLabel}
        </h2>
        {nextDay ? (
          <Link
            href={hrefFor(nextDay)}
            className="flex items-center gap-1 px-2 py-1 text-sm text-dashboard-text-muted hover:text-dashboard-text transition whitespace-nowrap"
            aria-label={`Next day: ${formatDayShort(nextDay)}`}
          >
            <span className="hidden sm:inline">{formatDayShort(nextDay)} </span>›
          </Link>
        ) : (
          <span
            className="flex items-center gap-1 px-2 py-1 text-sm text-dashboard-text-muted opacity-30 cursor-default whitespace-nowrap"
            aria-hidden="true"
          >
            ›
          </span>
        )}
      </div>

      {/* "Today" link — accessible from any archive day, jumps to live view. */}
      <div className="text-center mb-5 -mt-3">
        <Link
          href={todayHref}
          className="inline-flex items-center gap-1 px-3 py-1 text-xs rounded border border-blue-500/30 bg-blue-500/5 text-blue-300 hover:bg-blue-500/10 hover:text-blue-200 transition"
        >
          {locale === 'de' ? '→ Heute' : '→ Today'}
        </Link>
      </div>

      {today.length === 0 ? (
        <p className="text-sm text-dashboard-text-muted italic">
          {locale === 'de'
            ? 'Keine Ereignisse für diesen Tag verfügbar.'
            : 'No events recorded for this day.'}
        </p>
      ) : (
        <>
          {/* Prose placeholder — real prose comes from daily_briefs (scope='global') */}
          <div className="mb-6 px-4 py-3 border border-dashed border-dashboard-border rounded text-[12px] text-dashboard-text-muted italic">
            {locale === 'de'
              ? 'Redaktionelle Zusammenfassung in Kürze — automatische Generierung nach Tagesabschluss.'
              : 'Editorial day recap coming soon — auto-generated after day closure.'}
          </div>

          <ol className="space-y-2">
            {rows.map(({ ev, note }, i) => (
              <li
                key={ev.id}
                className="flex items-start gap-3 px-3 py-2 rounded border border-dashboard-border/50 hover:bg-dashboard-border/20 transition"
              >
                <span className="text-sm font-semibold text-dashboard-text-muted tabular-nums w-5 shrink-0 pt-0.5">
                  {i + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <Link
                    href={`/events/${ev.id}`}
                    className="block text-sm text-dashboard-text hover:text-blue-300 leading-snug"
                  >
                    {ev.title}
                  </Link>
                  <div className="text-[10px] text-dashboard-text-muted tabular-nums mt-0.5 flex items-center gap-2 flex-wrap">
                    <span>{ev.centroid_label}</span>
                    <span>·</span>
                    <span>{formatTrackBadge(ev.track)}</span>
                    <span>·</span>
                    <span>{ev.window_sources} sources · 7d</span>
                  </div>
                </div>
                <div className="shrink-0 pt-0.5">
                  <AnnotationBadge note={note} />
                </div>
              </li>
            ))}
          </ol>
        </>
      )}
    </section>
  );
}

// ─────────────────────────────────────────────────────────────
// Page
// ─────────────────────────────────────────────────────────────

export default async function TrendingV2Page({ params, searchParams }: TrendingV2Props) {
  const { locale } = await params;
  const { month: requestedMonth, day: requestedDay } = await searchParams;
  setRequestLocale(locale);
  const seoLocale = locale as SeoLocale;

  const months = await getGlobalAvailableMonths();
  if (months.length === 0) return notFound();

  const activeMonth = requestedMonth && months.includes(requestedMonth)
    ? requestedMonth
    : months[0];

  const view = await getGlobalMonthView(activeMonth, locale);
  if (!view) return notFound();

  const todayIso = resolveTodayIso(view);
  const archiveDay = isValidDay(requestedDay, view) && requestedDay !== todayIso
    ? requestedDay
    : null;

  // Current month = latest available month with any activity. Treat it as MTD
  // for UX copy + fastest-growing panel promotion.
  const isCurrentMonth = activeMonth === months[0];

  const totalLabel = locale === 'de'
    ? `Globales Briefing · ${formatMonthLabelSeo(activeMonth, 'de')}`
    : `Global Briefing · ${formatMonthLabelSeo(activeMonth, 'en')}`;

  // Layout: hero is full-width (spans the 2-col grid). Below it, the
  // main column holds either the archive day view OR the live overview;
  // the sidebar always holds Active Narratives + Trending Signals.
  const sidebar = (
    <div className="lg:sticky lg:top-24 space-y-8">
      <Suspense fallback={null}>
        <ActiveNarrativesRail month={activeMonth} locale={locale} />
      </Suspense>
      <Suspense fallback={null}>
        <TrendingSignalsRail />
      </Suspense>
    </div>
  );

  const hero = (
    <TrendingHero
      view={view}
      activeMonth={activeMonth}
      isCurrentMonth={isCurrentMonth}
      totalLabel={totalLabel}
      todayIso={todayIso}
    />
  );

  // Archive day branch — replace overview + fastest-growing + track cards
  // with a single day-specific list. Sidebar + hero stay the same.
  if (archiveDay) {
    return (
      <DashboardLayout sidebar={sidebar} topFullWidthContent={hero}>
        <Suspense fallback={null}>
          <ArchiveDayView
            day={archiveDay}
            activeMonth={activeMonth}
            view={view}
            locale={seoLocale}
          />
        </Suspense>
      </DashboardLayout>
    );
  }

  // Live view (default) — about this page + fastest-growing + track cards.
  const aboutBlocks = buildAboutBlocks(seoLocale);

  return (
    <DashboardLayout sidebar={sidebar} topFullWidthContent={hero}>
      <div className="space-y-8">
        {/* About this page — replaces the old mechanical "Overview" block. */}
        <section className="space-y-4">
          {aboutBlocks.map((b, i) => (
            <div key={i}>
              <h3 className="text-[11px] font-semibold uppercase tracking-wider text-dashboard-text-muted mb-1.5">
                {b.heading}
              </h3>
              <p className="text-[15px] leading-relaxed text-dashboard-text">
                {b.body}
              </p>
            </div>
          ))}
        </section>

        {/* Fastest-growing panel — hero-prominence on current month only */}
        {isCurrentMonth && (
          <Suspense fallback={null}>
            <FastestGrowingPanel month={activeMonth} locale={locale} isCurrentMonth={isCurrentMonth} />
          </Suspense>
        )}

        {/* 4 track cards in 2x2 grid */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {view.tracks.map(t => (
            <GlobalTrackCard key={t.track} track={t} activeMonth={activeMonth} />
          ))}
        </section>

        {!isCurrentMonth && (
          <p className="text-[11px] text-dashboard-text-muted italic">
            Fastest-growing panel is only shown for the live month.
          </p>
        )}
      </div>
    </DashboardLayout>
  );
}
