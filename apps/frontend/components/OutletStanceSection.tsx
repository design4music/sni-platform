'use client';

import { useEffect, useMemo, useState } from 'react';
import { useLocale, useTranslations } from 'next-intl';
import type { OutletStanceEntity, OutletStanceEvidence } from '@/lib/queries';
import { getCountryName } from '@/lib/countries';
import FlagImg from './FlagImg';

interface Props {
  feedName: string;
  initialMonth: string; // 'YYYY-MM'
  initialEntities: OutletStanceEntity[];
  availableMonths: string[]; // newest first
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

/* ---------- person icon (matches the flag-emoji "collection" visually) ---------- */

function PersonIcon({ className = 'w-3.5 h-3.5' }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="7" r="3.5" />
      <path d="M4 21c0-4.418 3.582-7 8-7s8 2.582 8 7" />
    </svg>
  );
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
    <div className="p-6 border border-dashboard-border bg-dashboard-surface rounded-lg">
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
  feedName,
  initialMonth,
  initialEntities,
  availableMonths,
}: Props) {
  const t = useTranslations('sources');
  const locale = useLocale();

  const [month, setMonth] = useState(initialMonth);
  const [entities, setEntities] = useState<OutletStanceEntity[]>(initialEntities);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (month === initialMonth) {
      setEntities(initialEntities);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    (async () => {
      try {
        const res = await fetch(
          `/api/outlet/${encodeURIComponent(feedName)}/stance?month=${month}`
        );
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (!cancelled) setEntities(data.entities || []);
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : 'error');
          setEntities([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [month, feedName, initialMonth, initialEntities]);

  const idx = useMemo(() => availableMonths.indexOf(month), [availableMonths, month]);
  const newerMonth = idx > 0 ? availableMonths[idx - 1] : null;
  const olderMonth = idx >= 0 && idx < availableMonths.length - 1 ? availableMonths[idx + 1] : null;

  return (
    <section className="mb-10">
      {/* Header + month switcher (matches CentroidHero pattern: active month in
          the title, prev/next buttons show sibling month names with chevrons).
          On phones the controls wrap onto their own row below the title so
          they don't compete with it for horizontal space. */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 sm:gap-4 mb-4">
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

        <div className="flex items-center gap-1 self-start sm:shrink-0">
          {olderMonth ? (
            <button
              onClick={() => setMonth(olderMonth)}
              className="px-3 py-1.5 text-sm text-dashboard-text-muted hover:text-dashboard-text border border-dashboard-border rounded hover:bg-dashboard-border/30 transition"
              aria-label={t('previousMonth')}
            >
              ‹ {formatMonthShort(olderMonth, locale)}
            </button>
          ) : null}
          {newerMonth ? (
            <button
              onClick={() => setMonth(newerMonth)}
              className="px-3 py-1.5 text-sm text-dashboard-text-muted hover:text-dashboard-text border border-dashboard-border rounded hover:bg-dashboard-border/30 transition"
              aria-label={t('nextMonth')}
            >
              {formatMonthShort(newerMonth, locale)} ›
            </button>
          ) : null}
        </div>
      </div>

      {/* Body. Keep the previous grid visible while loading so switching
          months doesn't cause a layout collapse — a thin overlay just dims
          the existing cards. */}
      {error ? (
        <div className="text-sm text-red-400">{error}</div>
      ) : entities.length === 0 && !loading ? (
        <div className="text-sm text-dashboard-text-muted bg-dashboard-surface border border-dashboard-border rounded-lg p-4">
          {t('noStanceData')}
        </div>
      ) : (
        <div className={`relative ${loading ? 'opacity-50 pointer-events-none transition-opacity' : ''}`}>
          {loading && (
            <div className="absolute top-2 right-2 text-xs text-dashboard-text-muted bg-dashboard-surface border border-dashboard-border rounded px-2 py-0.5 z-10">
              {t('loading')}
            </div>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {entities.map((e) => (
              <EntityCard key={`${e.entity_kind}-${e.entity_code}`} e={e} t={t} />
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
