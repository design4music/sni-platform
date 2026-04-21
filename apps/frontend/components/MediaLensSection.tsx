'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useTranslations, useLocale } from 'next-intl';
import OutletLogo from '@/components/OutletLogo';
import type { MediaLens, MediaLensTarget, MediaLensForeignOutlet } from '@/lib/queries';
import { getOutletLogoUrl } from '@/lib/logos';

interface MediaLensSectionProps {
  centroidId: string;
  centroidLabel: string;
  initialMonth: string; // 'YYYY-MM'
  initialLens: MediaLens;
}

// ---------------------------------------------------------------------------
// Score helpers — score range is [-2 .. +2], 5 editorial buckets.
// ---------------------------------------------------------------------------

type BucketKey = 'adversarial' | 'skeptical' | 'reportorial' | 'constructive' | 'promotional';

function bucketOf(score: number): BucketKey {
  if (score <= -1.0) return 'adversarial';
  if (score < -0.3) return 'skeptical';
  if (score <= 0.3) return 'reportorial';
  if (score < 1.0) return 'constructive';
  return 'promotional';
}

const BUCKET_FILL: Record<BucketKey, string> = {
  adversarial: 'bg-red-500/80',
  skeptical: 'bg-red-500/40',
  reportorial: 'bg-gray-500/40',
  constructive: 'bg-green-500/40',
  promotional: 'bg-green-500/80',
};

const BUCKET_TEXT: Record<BucketKey, string> = {
  adversarial: 'text-red-400',
  skeptical: 'text-red-300',
  reportorial: 'text-gray-300',
  constructive: 'text-green-300',
  promotional: 'text-green-400',
};

function bucketLabel(bucket: BucketKey, loc: string): string {
  const en: Record<BucketKey, string> = {
    adversarial: 'Adversarial',
    skeptical: 'Skeptical',
    reportorial: 'Reportorial',
    constructive: 'Constructive',
    promotional: 'Promotional',
  };
  const de: Record<BucketKey, string> = {
    adversarial: 'Feindlich',
    skeptical: 'Skeptisch',
    reportorial: 'Berichtend',
    constructive: 'Konstruktiv',
    promotional: 'Wohlwollend',
  };
  return loc === 'de' ? de[bucket] : en[bucket];
}

function formatScore(score: number): string {
  const sign = score > 0 ? '+' : '';
  return `${sign}${score.toFixed(1)}`;
}

// Maps score to a 0..100% horizontal position for the bar marker.
function scorePosition(score: number): number {
  const clamped = Math.max(-2, Math.min(2, score));
  return ((clamped + 2) / 4) * 100;
}

function shiftMonth(month: string, delta: number): string {
  const [y, m] = month.split('-').map(Number);
  const d = new Date(y, m - 1 + delta, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

function formatMonthLong(month: string, loc: string): string {
  const [y, m] = month.split('-').map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString(loc === 'de' ? 'de-DE' : 'en-US', {
    month: 'long',
    year: 'numeric',
  });
}

function formatMonthShort(month: string, loc: string): string {
  const [y, m] = month.split('-').map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString(loc === 'de' ? 'de-DE' : 'en-US', {
    month: 'short',
  });
}

// ---------------------------------------------------------------------------
// Score bar — horizontal 5-segment track with marker dot
// ---------------------------------------------------------------------------

function ScoreBar({ score }: { score: number }) {
  const pos = scorePosition(score);
  return (
    <div className="relative flex h-1.5 rounded-full overflow-hidden w-full">
      <div className="flex-1 bg-red-500/60" />
      <div className="flex-1 bg-red-500/30" />
      <div className="flex-1 bg-gray-500/30" />
      <div className="flex-1 bg-green-500/30" />
      <div className="flex-1 bg-green-500/60" />
      <span
        className="absolute top-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-dashboard-text ring-1 ring-dashboard-surface"
        style={{ left: `calc(${pos}% - 4px)` }}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Local target row (self or abroad)
// ---------------------------------------------------------------------------

function LocalTargetRow({
  label,
  score,
  sampleSize,
  feedCount,
  href,
  emphasis,
}: {
  label: string;
  score: number;
  sampleSize: number;
  feedCount: number;
  href?: string;
  emphasis?: boolean;
}) {
  const content = (
    <div className={`grid grid-cols-[minmax(0,1fr)_56px_72px] items-center gap-3 py-1.5 ${
      href ? 'hover:bg-dashboard-border/20 -mx-2 px-2 rounded' : ''
    }`}>
      <div className={`text-sm truncate ${emphasis ? 'font-medium text-dashboard-text' : 'text-dashboard-text'}`}>
        {label}
      </div>
      <div className="w-full">
        <ScoreBar score={score} />
      </div>
      <div className="flex items-center justify-end gap-2 text-[11px] text-dashboard-text-muted tabular-nums">
        <span>{formatScore(score)}</span>
        <span className="opacity-70">· {sampleSize}</span>
      </div>
    </div>
  );
  if (href) {
    return (
      <Link href={href} className="block">
        {content}
      </Link>
    );
  }
  return content;
}

// ---------------------------------------------------------------------------
// Foreign outlets — grouped into buckets, collapsible per bucket
// ---------------------------------------------------------------------------

function ForeignBucket({
  bucket,
  outlets,
  loc,
}: {
  bucket: BucketKey;
  outlets: MediaLensForeignOutlet[];
  loc: string;
}) {
  const [expanded, setExpanded] = useState(false);
  if (outlets.length === 0) return null;
  const visible = expanded ? outlets : outlets.slice(0, 6);
  const remaining = outlets.length - 6;

  return (
    <div className="mb-3 last:mb-0">
      <div className="flex items-center gap-2 mb-1.5">
        <span className={`w-2.5 h-2.5 rounded-full ${BUCKET_FILL[bucket]} flex-shrink-0`} />
        <span className={`text-xs font-medium ${BUCKET_TEXT[bucket]}`}>
          {bucketLabel(bucket, loc)}
        </span>
        <span className="text-[10px] text-dashboard-text-muted">({outlets.length})</span>
      </div>
      <div className="flex flex-wrap gap-1 pl-4">
        {visible.map(o => {
          const logoUrl = o.source_domain ? getOutletLogoUrl(o.source_domain, 16) : null;
          return (
            <Link
              key={o.feed_name}
              href={`/sources/${encodeURIComponent(o.feed_name).replace(/\./g, '%2E')}`}
              className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-dashboard-border/40 hover:bg-dashboard-border transition text-[11px]"
              title={`${o.feed_name}: ${formatScore(o.score)} · ${o.sample_size} samples`}
            >
              <OutletLogo src={logoUrl || ''} name={o.feed_name} size={14} className="rounded-sm" />
              <span className="text-dashboard-text truncate max-w-[80px]">{o.feed_name}</span>
              <span className="text-dashboard-text-muted tabular-nums">{formatScore(o.score)}</span>
            </Link>
          );
        })}
        {remaining > 0 && !expanded && (
          <button
            type="button"
            onClick={() => setExpanded(true)}
            className="text-[10px] text-blue-400 hover:text-blue-300 px-1.5 py-0.5"
          >
            +{remaining} more
          </button>
        )}
        {expanded && remaining > 0 && (
          <button
            type="button"
            onClick={() => setExpanded(false)}
            className="text-[10px] text-blue-400 hover:text-blue-300 px-1.5 py-0.5"
          >
            show less
          </button>
        )}
      </div>
    </div>
  );
}

function bucketizeForeign(outlets: MediaLensForeignOutlet[]): Record<BucketKey, MediaLensForeignOutlet[]> {
  const buckets: Record<BucketKey, MediaLensForeignOutlet[]> = {
    adversarial: [],
    skeptical: [],
    reportorial: [],
    constructive: [],
    promotional: [],
  };
  for (const o of outlets) {
    buckets[bucketOf(o.score)].push(o);
  }
  for (const k of Object.keys(buckets) as BucketKey[]) {
    buckets[k].sort((a, b) => Math.abs(b.score) - Math.abs(a.score));
  }
  return buckets;
}

// ---------------------------------------------------------------------------
// MediaLensSection — main component
// ---------------------------------------------------------------------------

export default function MediaLensSection({
  centroidId,
  centroidLabel,
  initialMonth,
  initialLens,
}: MediaLensSectionProps) {
  const t = useTranslations('centroid');
  const locale = useLocale();

  const [month, setMonth] = useState<string>(initialMonth);
  const [lens, setLens] = useState<MediaLens>(initialLens);
  const [loading, setLoading] = useState<boolean>(false);

  const prevMonth = shiftMonth(month, -1);
  const nextMonth = shiftMonth(month, 1);

  useEffect(() => {
    if (month === initialMonth) {
      setLens(initialLens);
      return;
    }
    let cancelled = false;
    setLoading(true);
    fetch(`/api/centroid/${encodeURIComponent(centroidId)}/media-lens?month=${month}`)
      .then(r => r.json())
      .then((body: MediaLens) => {
        if (cancelled) return;
        setLens(body);
      })
      .catch(() => {
        if (cancelled) return;
        setLens({ local_self: null, local_abroad: [], foreign: [] });
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [month, centroidId, initialMonth, initialLens]);

  const hasLocal = !!lens.local_self || lens.local_abroad.length > 0;
  const hasForeign = lens.foreign.length > 0;
  const hasAnything = hasLocal || hasForeign;

  const foreignBuckets = bucketizeForeign(lens.foreign);

  return (
    <section className={`bg-dashboard-surface border border-dashboard-border rounded-lg p-5 ${loading ? 'opacity-80' : ''}`}>
      {/* Header: title + month nav */}
      <div className="flex items-start justify-between gap-4 mb-4">
        <div className="min-w-0">
          <h2 className="text-xl font-semibold text-dashboard-text">
            {locale === 'de' ? 'Medienperspektive' : 'Media Lens'}
          </h2>
          <p className="text-[11px] text-dashboard-text-muted mt-0.5">
            {formatMonthLong(month, locale)}
            <span className="opacity-60"> · </span>
            {locale === 'de' ? 'Skala' : 'Scale'} −2 … +2
          </p>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <button
            type="button"
            onClick={() => setMonth(prevMonth)}
            disabled={loading}
            className="px-2 py-1 text-[11px] text-dashboard-text-muted hover:text-dashboard-text border border-dashboard-border rounded hover:bg-dashboard-border/30 transition disabled:opacity-50"
            aria-label="Previous month"
          >
            ‹ {formatMonthShort(prevMonth, locale)}
          </button>
          <button
            type="button"
            onClick={() => setMonth(nextMonth)}
            disabled={loading}
            className="px-2 py-1 text-[11px] text-dashboard-text-muted hover:text-dashboard-text border border-dashboard-border rounded hover:bg-dashboard-border/30 transition disabled:opacity-50"
            aria-label="Next month"
          >
            {formatMonthShort(nextMonth, locale)} ›
          </button>
        </div>
      </div>

      {!hasAnything ? (
        <p className="text-sm text-dashboard-text-muted italic py-4">
          {loading
            ? (locale === 'de' ? 'Lade…' : 'Loading…')
            : (locale === 'de'
                ? 'Keine Medienstandsdaten für diesen Monat.'
                : 'No media-stance data available for this month.')}
        </p>
      ) : (
      /* Two-column grid on md+, stacked on mobile */
      <div className={`grid gap-6 ${hasLocal && hasForeign ? 'md:grid-cols-2' : 'grid-cols-1'}`}>
        {hasLocal && (
          <div>
            <h3 className="text-[11px] font-semibold text-dashboard-text-muted uppercase tracking-wider mb-2">
              {locale === 'de' ? 'Lokale Perspektive' : 'Local perspective'}
            </h3>
            <p className="text-[11px] text-dashboard-text-muted mb-3">
              {locale === 'de'
                ? `Wie ${centroidLabel}s Medien berichten`
                : `How ${centroidLabel}'s outlets report`}
            </p>
            {lens.local_self && (
              <LocalTargetRow
                label={locale === 'de' ? 'Über sich selbst' : 'On itself'}
                score={lens.local_self.score}
                sampleSize={lens.local_self.sample_size}
                feedCount={lens.local_self.feed_count}
                emphasis
              />
            )}
            {lens.local_abroad.length > 0 && (
              <>
                {lens.local_self && <div className="h-px bg-dashboard-border my-2" />}
                <div className="text-[10px] font-medium text-dashboard-text-muted uppercase tracking-wider mb-1">
                  {locale === 'de' ? 'Über andere Länder' : 'On other countries'}
                </div>
                {lens.local_abroad.map(t => (
                  <LocalTargetRow
                    key={t.centroid_id}
                    label={t.label}
                    score={t.score}
                    sampleSize={t.sample_size}
                    feedCount={t.feed_count}
                    href={`/c/${t.centroid_id}?month=${month}`}
                  />
                ))}
              </>
            )}
          </div>
        )}

        {hasForeign && (
          <div>
            <h3 className="text-[11px] font-semibold text-dashboard-text-muted uppercase tracking-wider mb-2">
              {locale === 'de' ? 'Ausländische Perspektive' : 'Foreign perspective'}
            </h3>
            <p className="text-[11px] text-dashboard-text-muted mb-3">
              {locale === 'de'
                ? `Wie ausländische Medien über ${centroidLabel} berichten`
                : `How foreign outlets cover ${centroidLabel}`}
            </p>
            <div className="flex h-1.5 rounded-full overflow-hidden mb-3">
              <div className="flex-1 bg-red-500/80" />
              <div className="flex-1 bg-red-500/40" />
              <div className="flex-1 bg-gray-500/40" />
              <div className="flex-1 bg-green-500/40" />
              <div className="flex-1 bg-green-500/80" />
            </div>
            {(Object.keys(foreignBuckets) as BucketKey[]).map(k => (
              <ForeignBucket key={k} bucket={k} outlets={foreignBuckets[k]} loc={locale} />
            ))}
          </div>
        )}
      </div>
      )}
    </section>
  );
}
