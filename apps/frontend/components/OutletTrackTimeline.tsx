import Link from 'next/link';
import { getTranslations } from 'next-intl/server';
import InfoTip from './InfoTip';
import type { OutletTrackTimelineRow } from '@/lib/queries';

interface Props {
  feedSlug: string;
  locale: string;
  rows: OutletTrackTimelineRow[];
}

const TRACKS = [
  { key: 'security', fill: '#f87171' },
  { key: 'politics', fill: '#38bdf8' },
  { key: 'economy', fill: '#fbbf24' },
  { key: 'society', fill: '#34d399' },
] as const;

type TrackKey = (typeof TRACKS)[number]['key'];

const TRACK_KEY_MAP: Record<string, TrackKey> = {
  geo_security: 'security',
  geo_politics: 'politics',
  geo_economy: 'economy',
  geo_society: 'society',
};

const W = 800;
const H = 200;
const PAD_L = 24;
const PAD_R = 8;
const PAD_T = 8;
const PAD_B = 22;

function shareByTrack(dist: Record<string, number>): Record<TrackKey, number> {
  const out: Record<TrackKey, number> = {
    security: 0,
    politics: 0,
    economy: 0,
    society: 0,
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

  const innerW = W - PAD_L - PAD_R;
  const innerH = H - PAD_T - PAD_B;
  const stepX = rows.length > 1 ? innerW / (rows.length - 1) : 0;

  // Per-month shares + raw count.
  const shares = rows.map(r => ({
    month: r.month,
    title_count: r.title_count,
    s: shareByTrack(r.track_distribution),
  }));

  // Lifetime shares — weighted by title_count so heavier months count more.
  const lifetimeWeighted: Record<TrackKey, number> = {
    security: 0,
    politics: 0,
    economy: 0,
    society: 0,
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

  // Build cumulative bands: each track gets its own polygon.
  const trackBands = rows.length >= 2
    ? TRACKS.map(track => {
        let topPath = '';
        let bottomPath = '';
        shares.forEach((row, i) => {
          const x = PAD_L + i * stepX;
          let bottomShare = 0;
          for (const t2 of TRACKS) {
            if (t2.key === track.key) break;
            bottomShare += row.s[t2.key];
          }
          const topShare = bottomShare + row.s[track.key];
          const yBottom = PAD_T + (1 - bottomShare) * innerH;
          const yTop = PAD_T + (1 - topShare) * innerH;
          topPath += `${i === 0 ? 'M' : 'L'} ${x} ${yTop} `;
          bottomPath = ` L ${x} ${yBottom}` + bottomPath;
        });
        return { ...track, d: topPath + bottomPath + ' Z' };
      })
    : [];

  // X-axis tick labels: first, last, and ~quarter points
  const tickIdx: number[] = [];
  if (shares.length <= 6) {
    shares.forEach((_, i) => tickIdx.push(i));
  } else {
    const stride = Math.max(1, Math.floor(shares.length / 5));
    for (let i = 0; i < shares.length; i += stride) tickIdx.push(i);
    if (tickIdx[tickIdx.length - 1] !== shares.length - 1) {
      tickIdx.push(shares.length - 1);
    }
  }

  return (
    <section className="mb-10">
      <h2 className="text-2xl font-bold mb-2">{t('trackTimelineTitle')}</h2>
      <p className="text-sm text-dashboard-text-muted mb-4 max-w-3xl leading-snug">
        {t('trackTimelineDescription')}
      </p>

      <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-3">
        {rows.length >= 2 ? (
          <svg
            viewBox={`0 0 ${W} ${H}`}
            preserveAspectRatio="none"
            className="w-full h-48"
            role="img"
            aria-label={t('trackTimelineTitle')}
          >
            {[0, 0.25, 0.5, 0.75, 1].map(g => {
              const y = PAD_T + (1 - g) * innerH;
              return (
                <g key={g}>
                  <line
                    x1={PAD_L}
                    x2={W - PAD_R}
                    y1={y}
                    y2={y}
                    stroke="#27272a"
                    strokeWidth={1}
                    strokeDasharray={g === 0 || g === 1 ? '' : '2 3'}
                  />
                  <text
                    x={PAD_L - 4}
                    y={y + 3}
                    textAnchor="end"
                    fontSize={9}
                    fill="#71717a"
                  >
                    {Math.round(g * 100)}%
                  </text>
                </g>
              );
            })}

            {trackBands.map(band => (
              <path key={band.key} d={band.d} fill={band.fill} fillOpacity={0.85}>
                <title>{`${tTracks('geo_' + band.key)} · ${fmtPct(lifetime[band.key])} lifetime`}</title>
              </path>
            ))}

            {tickIdx.map(i => {
              const x = PAD_L + i * stepX;
              const m = shares[i].month;
              const [y, mm] = m.split('-');
              const label = new Date(Number(y), Number(mm) - 1, 1).toLocaleDateString(
                locale === 'de' ? 'de-DE' : 'en-US',
                { month: 'short' }
              );
              return (
                <g key={m}>
                  <line
                    x1={x}
                    x2={x}
                    y1={PAD_T + innerH}
                    y2={PAD_T + innerH + 3}
                    stroke="#52525b"
                    strokeWidth={1}
                  />
                  <text
                    x={x}
                    y={PAD_T + innerH + 14}
                    textAnchor="middle"
                    fontSize={9}
                    fill="#a1a1aa"
                  >
                    {label} {y.slice(2)}
                  </text>
                </g>
              );
            })}
          </svg>
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
                title={`${tTracks('geo_' + tr.key)} · ${fmtPct(lifetime[tr.key])}`}
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
              <span className="text-dashboard-text">{tTracks('geo_' + tr.key)}</span>
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
                        <span className="flex-1">{tTracks('geo_' + tr.key)}</span>
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
