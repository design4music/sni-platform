'use client';

import { useMemo } from 'react';
import Link from 'next/link';
import { useLocale, useTranslations } from 'next-intl';
import type { OutletStanceEntity, OutletStanceEvidence } from '@/lib/queries';
import { getCountryName } from '@/lib/countries';
import FlagImg from './FlagImg';
import PersonIcon from './PersonIcon';

interface Props {
  /** Required for the optional in-section prev/next switcher: switcher
   *  generates URLs of the form /sources/[feedSlug]/[YYYY-MM]. */
  feedName: string;
  feedSlug: string;
  initialMonth: string; // 'YYYY-MM'
  initialEntities: OutletStanceEntity[];
  availableMonths: string[]; // newest first
  locale?: string;
  /** When true, the section's own prev/next month switcher is suppressed.
   *  Use when the parent page already drives month navigation. */
  hideMonthSwitcher?: boolean;
  /** When true, the section title omits the active month (because the
   *  page's H1 already shows it). */
  hideMonthInTitle?: boolean;
}

/* ---------- helpers ---------- */

function formatMonthLong(month: string, loc: string): string {
  const [y, m] = month.split('-').map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString(
    loc === 'de' ? 'de-DE' : 'en-US',
    { month: 'long', year: 'numeric' }
  );
}

function formatMonthShort(month: string, loc: string): string {
  const [y, m] = month.split('-').map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString(
    loc === 'de' ? 'de-DE' : 'en-US',
    { month: 'short' }
  );
}

// FlagImg is now a shared component — see components/FlagImg.tsx.

// Stance badge: full opaque pill, colour-coded −2..+2.
function stanceBadgeClass(score: number | null): string {
  if (score === null)
    return 'bg-dashboard-border/40 text-dashboard-text-muted border-dashboard-border';
  if (score <= -2) return 'bg-red-500/30 text-red-200 border-red-500/60';
  if (score === -1) return 'bg-red-500/15 text-red-300 border-red-500/40';
  if (score === 0)
    return 'bg-dashboard-border/50 text-dashboard-text-muted border-dashboard-border';
  if (score === 1) return 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40';
  return 'bg-emerald-500/30 text-emerald-200 border-emerald-500/60';
}

function stanceLabel(score: number | null, t: (k: string) => string): string {
  if (score === null) return t('stanceUnknown');
  if (score <= -2) return t('stanceHostile');
  if (score === -1) return t('stanceCritical');
  if (score === 0) return t('stanceNeutral');
  if (score === 1) return t('stanceFavorable');
  return t('stanceSupportive');
}

function stanceSign(score: number | null): string {
  if (score === null) return '—';
  if (score > 0) return `+${score}`;
  return String(score);
}

/* ---------- evidence line ---------- */

function EvidenceLine({ ev }: { ev: OutletStanceEvidence }) {
  const body = <span className="text-sm text-dashboard-text">{ev.title_display}</span>;
  const lang =
    ev.language && ev.language !== 'en' ? (
      <span className="ml-2 text-[10px] uppercase text-dashboard-text-muted">
        {ev.language}
      </span>
    ) : null;
  return (
    <li className="flex items-start gap-2 py-0.5">
      <span className="text-dashboard-text-muted text-xs pt-0.5 flex-shrink-0">→</span>
      <span className="min-w-0 flex-1">
        {ev.url_gnews ? (
          <a
            href={ev.url_gnews}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-blue-400 transition"
          >
            {body}
          </a>
        ) : (
          body
        )}
        {lang}
      </span>
    </li>
  );
}

/* ---------- entity card (TrackCard-inspired, always expanded) ---------- */

function EntityCard({
  e,
  t,
}: {
  e: OutletStanceEntity;
  t: (k: string) => string;
}) {
  const label =
    e.entity_kind === 'country'
      ? getCountryName(e.entity_code) || e.entity_code
      : e.entity_code; // persons already display-ready (Trump, Putin, …)

  const countryIso = e.entity_kind === 'country' ? e.entity_code : e.entity_country;

  // Uniform identity pill: image/icon + label, bordered. Persons get a small
  // PersonIcon inside the pill + a flag for their country; countries get just
  // the country flag.
  const identityPill = (
    <span className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full border border-dashboard-border bg-dashboard-border/30 text-sm font-medium text-dashboard-text">
      {e.entity_kind === 'person' ? (
        <span className="inline-flex items-center gap-1.5">
          <span className="inline-flex items-center justify-center w-3.5 h-3.5 text-dashboard-text-muted">
            <PersonIcon />
          </span>
          {countryIso && <FlagImg iso2={countryIso} size={14} />}
        </span>
      ) : (
        <FlagImg iso2={countryIso} size={16} />
      )}
      <span className="truncate max-w-[16rem]">{label}</span>
    </span>
  );

  return (
    <div
      id={`stance-${e.entity_kind}-${e.entity_code}`}
      className="p-6 border border-dashboard-border bg-dashboard-surface rounded-lg scroll-mt-20"
    >
      {/* Header: identity pill + count */}
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        {identityPill}
        <span
          className="ml-auto inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-xs font-medium bg-dashboard-border/50 border-dashboard-border text-dashboard-text-muted tabular-nums"
          title={`${e.n_headlines} ${t('titles')}`}
        >
          {e.n_headlines} {t('titles')}
        </span>
      </div>

      {/* Stance pill + tone */}
      <div className="flex items-start gap-3 mb-4 flex-wrap">
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border text-xs font-medium tabular-nums ${stanceBadgeClass(e.stance)}`}
          title={e.confidence ? `${t('confidence')}: ${e.confidence}` : undefined}
        >
          <span>{stanceSign(e.stance)}</span>
          <span>{stanceLabel(e.stance, t)}</span>
        </span>
        {e.tone && (
          <span className="text-xs italic text-dashboard-text-muted leading-snug">
            “{e.tone}”
          </span>
        )}
      </div>

      {/* Patterns */}
      {e.patterns.length > 0 && (
        <div className="mb-4">
          <div className="text-[11px] uppercase tracking-wider text-dashboard-text-muted mb-1.5">
            {t('patterns')}
          </div>
          <ul className="list-disc pl-5 space-y-1 text-sm text-dashboard-text">
            {e.patterns.map((p, i) => (
              <li key={i} className="leading-snug">
                {p}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Caveats */}
      {e.caveats && (
        <div className="mb-4">
          <div className="text-[11px] uppercase tracking-wider text-dashboard-text-muted mb-1.5">
            {t('caveats')}
          </div>
          <p className="text-sm text-dashboard-text-muted leading-snug">{e.caveats}</p>
        </div>
      )}

      {/* Evidence */}
      {e.evidence.length > 0 && (
        <div>
          <div className="text-[11px] uppercase tracking-wider text-dashboard-text-muted mb-1.5">
            {t('representativeHeadlines')}
          </div>
          <ul className="space-y-0.5">
            {e.evidence.map((ev) => (
              <EvidenceLine key={ev.title_id} ev={ev} />
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

/* ---------- main section ---------- */

export default function OutletStanceSection({
  feedSlug,
  initialMonth,
  initialEntities,
  availableMonths,
  locale: localeProp,
  hideMonthSwitcher = false,
  hideMonthInTitle = false,
}: Props) {
  const t = useTranslations('sources');
  const localeHook = useLocale();
  const locale = localeProp || localeHook;

  // Pure presentation — month state lives in the URL.
  const month = initialMonth;
  const entities = initialEntities;

  const idx = useMemo(() => availableMonths.indexOf(month), [availableMonths, month]);
  const newerMonth = idx > 0 ? availableMonths[idx - 1] : null;
  const olderMonth = idx >= 0 && idx < availableMonths.length - 1 ? availableMonths[idx + 1] : null;

  // Header (h2 + description) is suppressed by the parent page since
  // OutletStanceBricks above already titles the section. The optional
  // prev/next switcher is also suppressed in our current usage; both
  // controlled via the hideMonthInTitle / hideMonthSwitcher props.
  const renderHeader = !hideMonthInTitle || !hideMonthSwitcher;

  return (
    <section className="mb-10">
      {renderHeader && (
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 sm:gap-4 mb-4">
          {!hideMonthInTitle && (
            <div className="min-w-0 flex-1">
              <h2 className="text-2xl font-bold">
                {t('editorialStanceTitle')}
                <span className="text-dashboard-text-muted font-normal">
                  {' · '}
                  {formatMonthLong(month, locale)}
                </span>
              </h2>
              <p className="text-sm text-dashboard-text-muted mt-1 max-w-3xl">
                {t('editorialStanceDesc')}
              </p>
            </div>
          )}

          {!hideMonthSwitcher && (
            <div className="flex items-center gap-1 self-start sm:shrink-0">
              {olderMonth ? (
                <Link
                  href={`/${locale}/sources/${feedSlug}/${olderMonth}`}
                  className="px-3 py-1.5 text-sm text-dashboard-text-muted hover:text-dashboard-text border border-dashboard-border rounded hover:bg-dashboard-border/30 transition"
                  aria-label={t('previousMonth')}
                >
                  ‹ {formatMonthShort(olderMonth, locale)}
                </Link>
              ) : null}
              {newerMonth ? (
                <Link
                  href={`/${locale}/sources/${feedSlug}/${newerMonth}`}
                  className="px-3 py-1.5 text-sm text-dashboard-text-muted hover:text-dashboard-text border border-dashboard-border rounded hover:bg-dashboard-border/30 transition"
                  aria-label={t('nextMonth')}
                >
                  {formatMonthShort(newerMonth, locale)} ›
                </Link>
              ) : null}
            </div>
          )}
        </div>
      )}

      {entities.length === 0 ? (
        <div className="text-sm text-dashboard-text-muted bg-dashboard-surface border border-dashboard-border rounded-lg p-4">
          {t('noStanceData')}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {entities.map((e) => (
            <EntityCard key={`${e.entity_kind}-${e.entity_code}`} e={e} t={t} />
          ))}
        </div>
      )}
    </section>
  );
}
