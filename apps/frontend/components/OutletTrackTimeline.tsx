import Link from 'next/link';
import { getTranslations } from 'next-intl/server';
import InfoTip from './InfoTip';
import StackedTrackAreaChart, { type StackedTrackPoint } from './StackedTrackAreaChart';
import type { OutletTrackTimelineRow } from '@/lib/queries';

interface Props {
  feedSlug: string;
  locale: string;
  rows: OutletTrackTimelineRow[];
}

const TRACKS = [
  { key: 'security', main: 'geo_security', fill: '#f87171' },
  { key: 'politics', main: 'geo_politics', fill: '#38bdf8' },
  { key: 'economy',  main: 'geo_economy',  fill: '#fbbf24' },
  { key: 'society',  main: 'geo_society',  fill: '#34d399' },
] as const;

type TrackKey = (typeof TRACKS)[number]['key'];

const TRACK_KEY_MAP: Record<string, TrackKey> = {
  geo_security: 'security',
  geo_politics: 'politics',
  geo_economy: 'economy',
  geo_society: 'society',
};

function shareByTrack(dist: Record<string, number>): Record<TrackKey, number> {
  const out: Record<TrackKey, number> = {
    security: 0, politics: 0, economy: 0, society: 0,
  };
  let total = 0;
  for (const [k, v] of Object.entries(dist)) {
    const main = TRACK_KEY_MAP[k];
    if (!main) continue;
    out[main] += v;
    total += v;
  }
  if (total > 0 && total < 0.999) {
    for (const k of Object.keys(out) as TrackKey[]) out[k] /= total;
  }
  return out;
}

function fmtPct(x: number): string {
  return `${(x * 100).toFixed(1)}%`;
}

function formatMonthLabel(month: string, locale: string): string {
  const [y, mm] = month.split('-').map(Number);
  return new Date(y, mm - 1, 1).toLocaleDateString(
    locale === 'de' ? 'de-DE' : 'en-US',
    { month: 'short', year: 'numeric' }
  );
}

export default async function OutletTrackTimeline({
  feedSlug,
  locale,
  rows,
}: Props) {
  const t = await getTranslations('sources');
  const tTracks = await getTranslations('tracks');

  if (rows.length < 1) return null;

  // Per-month shares + raw count.
  const shares = rows.map(r => ({
    month: r.month,
    title_count: r.title_count,
    s: shareByTrack(r.track_distribution),
  }));

  // Lifetime shares — weighted by title_count so heavier months count more.
  const lifetimeWeighted: Record<TrackKey, number> = {
    security: 0, politics: 0, economy: 0, society: 0,
  };
  let lifetimeTotal = 0;
  for (const row of shares) {
    lifetimeTotal += row.title_count;
    for (const k of Object.keys(lifetimeWeighted) as TrackKey[]) {
      lifetimeWeighted[k] += row.s[k] * row.title_count;
    }
  }
  const lifetime: Record<TrackKey, number> = lifetimeTotal > 0
    ? {
        security: lifetimeWeighted.security / lifetimeTotal,
        politics: lifetimeWeighted.politics / lifetimeTotal,
        economy: lifetimeWeighted.economy / lifetimeTotal,
        society: lifetimeWeighted.society / lifetimeTotal,
      }
    : { security: 0, politics: 0, economy: 0, society: 0 };

  // Per-month points for the stacked area chart. Volume * share = raw
  // count per track (rounded). Same shape as CentroidActivityChart so
  // we can share the chart component.
  const chartData: StackedTrackPoint[] = shares.map(row => ({
    x: row.month,
    geo_security: Math.round(row.s.security * row.title_count),
    geo_politics: Math.round(row.s.politics * row.title_count),
    geo_economy:  Math.round(row.s.economy  * row.title_count),
    geo_society:  Math.round(row.s.society  * row.title_count),
  }));

  return (
    <section className="mb-10">
      <h2 className="text-2xl font-bold mb-2">{t('trackTimelineTitle')}</h2>
      <p className="text-sm text-dashboard-text-muted mb-4 max-w-3xl leading-snug">
        {t('trackTimelineDescription')}
      </p>

      <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-3">
        {rows.length >= 2 ? (
          <StackedTrackAreaChart
            data={chartData}
            xTickFormatter={(raw) => formatMonthLabel(raw, locale)}
            xTooltipFormatter={(raw) => formatMonthLabel(raw, locale)}
          />
        ) : (
          // 1-month fallback: simple horizontal bar with the lifetime
          // distribution. Same colors so the visual stays consistent.
          <div className="flex h-7 rounded-full overflow-hidden">
            {TRACKS.filter(tr => lifetime[tr.key] >= 0.01).map(tr => (
              <div
                key={tr.key}
                style={{
                  width: `${Math.max(lifetime[tr.key] * 100, 3)}%`,
                  backgroundColor: tr.fill,
                  opacity: 0.85,
                }}
                title={`${tTracks(tr.main)} · ${fmtPct(lifetime[tr.key])}`}
              />
            ))}
          </div>
        )}

        {/* Lifetime % legend — exact percentages always visible */}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-3 text-xs">
          <span className="text-[10px] uppercase tracking-wider text-dashboard-text-muted/80 mr-1">
            {t('lifetimeLabel')}
          </span>
          {TRACKS.map(tr => (
            <span key={tr.key} className="inline-flex items-center gap-1.5">
              <span
                className="w-3 h-3 rounded flex-shrink-0"
                style={{ backgroundColor: tr.fill, opacity: 0.85 }}
              />
              <span className="text-dashboard-text">{tTracks(tr.main)}</span>
              <span className="tabular-nums text-dashboard-text-muted">
                {fmtPct(lifetime[tr.key])}
              </span>
            </span>
          ))}
        </div>

        {/* Per-month strip — each chip clickable, with InfoTip showing
            exact per-month percentages and headline count. */}
        {shares.length > 0 && (
          <div className="flex flex-wrap gap-x-1 gap-y-2 mt-3 text-[10px]">
            <span className="text-[10px] uppercase tracking-wider text-dashboard-text-muted/80 mr-1 self-center">
              {t('byMonthLabel')}
            </span>
            {shares.map(s => {
              const tooltipNode = (
                <div className="text-left">
                  <div className="font-semibold text-dashboard-text mb-1">
                    {formatMonthLabel(s.month, locale)}
                  </div>
                  <div className="mb-1.5">
                    {s.title_count.toLocaleString()} {t('titles')}
                  </div>
                  <ul className="space-y-0.5">
                    {TRACKS.map(tr => (
                      <li key={tr.key} className="flex items-center gap-2">
                        <span
                          className="w-2.5 h-2.5 rounded flex-shrink-0"
                          style={{ backgroundColor: tr.fill, opacity: 0.85 }}
                        />
                        <span className="flex-1">{tTracks(tr.main)}</span>
                        <span className="tabular-nums">{fmtPct(s.s[tr.key])}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              );
              return (
                <span key={s.month} className="inline-flex items-center">
                  <Link
                    href={`/${locale}/sources/${feedSlug}/${s.month}`}
                    className="px-2 py-0.5 rounded tabular-nums text-dashboard-text-muted hover:text-blue-400 transition"
                  >
                    {s.month}
                  </Link>
                  <InfoTip>{tooltipNode}</InfoTip>
                </span>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
