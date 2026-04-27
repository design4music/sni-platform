import Link from 'next/link';
import { ReactNode } from 'react';
import { getTranslations } from 'next-intl/server';
import { getCountryName } from '@/lib/countries';
import FlagImg from './FlagImg';
import PersonIcon from './PersonIcon';
import InfoTip from './InfoTip';
import type { OutletStanceTimelineRow, OutletEntityDailyRow } from '@/lib/queries';

interface Props {
  feedSlug: string;
  locale: string;
  /** Stance rows — entity selection + ordering only (matches heatmap). */
  stanceRows: OutletStanceTimelineRow[];
  /** Day-level coverage rows for those entities, full title lifetime. */
  dailyRows: OutletEntityDailyRow[];
  topN?: number;
}

const W = 1100;
const H = 380;
const PAD_L = 40;
const PAD_R = 16;
const PAD_T = 18;
const PAD_B = 30;

const COLORS = [
  '#f87171', // red-400
  '#38bdf8', // sky-400
  '#fbbf24', // amber-400
  '#34d399', // emerald-400
  '#a78bfa', // violet-400
  '#f472b6', // pink-400
  '#22d3ee', // cyan-400
  '#fb923c', // orange-400
  '#818cf8', // indigo-400
  '#a3e635', // lime-400
  '#fb7185', // rose-400
  '#2dd4bf', // teal-400
];

const LOG_TICK_VALUES = [1, 2, 5, 10, 25, 50, 100, 250, 500, 1000, 2500];

function parseDayUtc(s: string): number {
  return Date.parse(s + 'T00:00:00Z');
}

/** Monday of the ISO week containing the given UTC day. */
function mondayOfWeek(dayMs: number): number {
  const d = new Date(dayMs);
  const dow = d.getUTCDay();           // 0 = Sun, 1 = Mon, ..., 6 = Sat
  const offset = dow === 0 ? -6 : 1 - dow;
  return dayMs + offset * 86400000;
}

function isoDay(ms: number): string {
  return new Date(ms).toISOString().slice(0, 10);
}

function formatWeekLabel(weekStart: string, locale: string): string {
  const d = new Date(parseDayUtc(weekStart));
  return d.toLocaleDateString(locale === 'de' ? 'de-DE' : 'en-US', {
    month: 'short',
    day: 'numeric',
    timeZone: 'UTC',
  });
}

function formatMonthLabel(month: string, locale: string): string {
  const [y, mm] = month.split('-').map(Number);
  return new Date(y, mm - 1, 1).toLocaleDateString(
    locale === 'de' ? 'de-DE' : 'en-US',
    { month: 'short' }
  );
}

interface DrawnEntity {
  color: string;
  label: string;
  countryIso: string | null;
  isPerson: boolean;
  code: string;
  total: number;
  activeWeeks: number;
  peakWeek: string;          // weekStart 'YYYY-MM-DD'
  peakValue: number;
  peakX: number;
  peakY: number;
  peakMonth: string;          // 'YYYY-MM' for legend link
  monthlyTotals: Map<string, number>;  // 'YYYY-MM' → titles
  linePath: string;
  tooltipText: string;       // for SVG <title>
  tooltipNode: ReactNode;    // rich tooltip rendered by InfoTip
}

export default async function OutletEntityVolume({
  feedSlug,
  locale,
  stanceRows,
  dailyRows,
  topN = 12,
}: Props) {
  const t = await getTranslations('sources');

  if (stanceRows.length === 0 || dailyRows.length === 0) return null;

  /* ------- Entity selection (matches heatmap order) ------- */
  interface EntityKey {
    kind: 'country' | 'person';
    code: string;
    country: string | null;
  }
  type Agg = { key: EntityKey; monthCount: number; total: number };
  const stanceAgg = new Map<string, Agg>();
  for (const r of stanceRows) {
    const id = `${r.entity_kind}:${r.entity_code}`;
    let a = stanceAgg.get(id);
    if (!a) {
      a = {
        key: { kind: r.entity_kind, code: r.entity_code, country: r.entity_country },
        monthCount: 0,
        total: 0,
      };
      stanceAgg.set(id, a);
    }
    a.monthCount += 1;
    a.total += r.n_headlines;
  }
  const selected = [...stanceAgg.values()]
    .sort((a, b) => b.monthCount - a.monthCount || b.total - a.total)
    .slice(0, topN);
  if (selected.length === 0) return null;
  const selectedIds = new Set(selected.map(e => `${e.key.kind}:${e.key.code}`));

  /* ------- Per-entity daily map + lifetime range ------- */
  const dailyByEntity = new Map<string, Map<string, number>>();
  let minDay: string | null = null;
  let maxDay: string | null = null;
  for (const r of dailyRows) {
    const id = `${r.entity_kind}:${r.entity_code}`;
    if (!selectedIds.has(id)) continue;
    let m = dailyByEntity.get(id);
    if (!m) {
      m = new Map();
      dailyByEntity.set(id, m);
    }
    m.set(r.day, r.n);
    if (!minDay || r.day < minDay) minDay = r.day;
    if (!maxDay || r.day > maxDay) maxDay = r.day;
  }
  if (!minDay || !maxDay) return null;

  /* ------- Build week buckets across the full lifetime ------- */
  const firstWeekStart = mondayOfWeek(parseDayUtc(minDay));
  const lastWeekStart = mondayOfWeek(parseDayUtc(maxDay));
  const weekStarts: string[] = [];
  for (let t = firstWeekStart; t <= lastWeekStart; t += 7 * 86400000) {
    weekStarts.push(isoDay(t));
  }
  const weekIndex = new Map<string, number>();
  weekStarts.forEach((w, i) => weekIndex.set(w, i));

  /* ------- Aggregate per entity into weeks + monthly totals ------- */
  const entityWeekCounts = new Map<string, number[]>();
  const entityMonthTotals = new Map<string, Map<string, number>>();
  for (const ent of selected) {
    const id = `${ent.key.kind}:${ent.key.code}`;
    const weekly = new Array<number>(weekStarts.length).fill(0);
    const monthly = new Map<string, number>();
    const days = dailyByEntity.get(id);
    if (days) {
      for (const [day, n] of days) {
        const wk = isoDay(mondayOfWeek(parseDayUtc(day)));
        const idx = weekIndex.get(wk);
        if (idx != null) weekly[idx] += n;
        const month = day.slice(0, 7);
        monthly.set(month, (monthly.get(month) || 0) + n);
      }
    }
    entityWeekCounts.set(id, weekly);
    entityMonthTotals.set(id, monthly);
  }

  /* ------- Y scale (log) ------- */
  let rawMax = 0;
  for (const arr of entityWeekCounts.values()) {
    for (const v of arr) if (v > rawMax) rawMax = v;
  }
  if (rawMax === 0) return null;
  const logMax = Math.log10(rawMax + 1);
  const innerW = W - PAD_L - PAD_R;
  const innerH = H - PAD_T - PAD_B;
  const stepX =
    weekStarts.length > 1 ? innerW / (weekStarts.length - 1) : 0;
  const xAt = (i: number) => PAD_L + i * stepX;
  const yAt = (v: number) =>
    PAD_T + (1 - Math.log10(v + 1) / logMax) * innerH;

  /* ------- Y tick selection (log scale) ------- */
  const yTicks = LOG_TICK_VALUES.filter(v => v <= rawMax);
  // Always include the rawMax band so the chart top is labelled.
  if (yTicks[yTicks.length - 1] !== rawMax) yTicks.push(rawMax);

  /* ------- X tick selection (month boundaries) ------- */
  const monthTicks: { x: number; label: string; year: string }[] = [];
  const startDate = new Date(parseDayUtc(minDay));
  const endDate = new Date(parseDayUtc(maxDay));
  const cursor = new Date(
    Date.UTC(startDate.getUTCFullYear(), startDate.getUTCMonth(), 1)
  );
  while (cursor.getTime() <= endDate.getTime()) {
    // Snap to the nearest week start whose week contains the 1st.
    const monthStartMs = cursor.getTime();
    const wkOfMonthStart = isoDay(mondayOfWeek(monthStartMs));
    const idx = weekIndex.get(wkOfMonthStart);
    if (idx != null) {
      const label = cursor.toLocaleDateString(
        locale === 'de' ? 'de-DE' : 'en-US',
        { month: 'short', timeZone: 'UTC' }
      );
      monthTicks.push({
        x: xAt(idx),
        label,
        year: String(cursor.getUTCFullYear()).slice(2),
      });
    }
    cursor.setUTCMonth(cursor.getUTCMonth() + 1);
  }

  /* ------- Per-entity drawing data + tooltip ------- */
  const drawn: DrawnEntity[] = selected.map((ent, idx) => {
    const id = `${ent.key.kind}:${ent.key.code}`;
    const color = COLORS[idx % COLORS.length];
    const isPerson = ent.key.kind === 'person';
    const countryIso = isPerson ? ent.key.country : ent.key.code;
    const label = isPerson
      ? ent.key.code
      : getCountryName(ent.key.code) || ent.key.code;

    const weekly = entityWeekCounts.get(id) || [];
    const monthly = entityMonthTotals.get(id) || new Map();

    // Build a path that breaks on zero weeks. One entity → one line
    // (possibly interrupted), no standalone dots.
    let path = '';
    let prev = false;
    let total = 0;
    let active = 0;
    let peakIdx = 0;
    let peakValue = 0;

    weekly.forEach((v, i) => {
      total += v;
      if (v > 0) {
        active += 1;
        if (v > peakValue) {
          peakValue = v;
          peakIdx = i;
        }
        const x = xAt(i);
        const y = yAt(v);
        path += `${prev ? 'L' : 'M'} ${x.toFixed(1)} ${y.toFixed(1)} `;
        prev = true;
      } else {
        prev = false;
      }
    });

    const peakWeek = weekStarts[peakIdx] || weekStarts[0];
    const peakMonth = peakWeek.slice(0, 7);

    // Tooltip — both a plain string for SVG <title> (desktop hover on
    // peak markers) and a rich ReactNode for the InfoTip in the
    // legend (mobile-tappable).
    const monthsSorted = [...monthly.entries()].sort((a, b) =>
      a[0].localeCompare(b[0])
    );
    const tooltipText = [
      label,
      `Peak: week of ${formatWeekLabel(peakWeek, locale)} — ${peakValue} titles`,
      `Total: ${total} titles · ${active} active weeks`,
      '',
      'By month:',
      ...monthsSorted.map(([m, n]) => `  ${formatMonthLabel(m, locale)}: ${n}`),
    ].join('\n');

    const tooltipNode = (
      <div className="text-left">
        <div className="font-semibold text-dashboard-text mb-1">{label}</div>
        <div>
          Peak: week of {formatWeekLabel(peakWeek, locale)} — {peakValue} titles
        </div>
        <div className="mb-1">
          Total: {total.toLocaleString()} · {active} active weeks
        </div>
        {monthsSorted.length > 0 && (
          <>
            <div className="text-dashboard-text-muted/80 mt-1.5">By month:</div>
            <ul className="grid grid-cols-2 gap-x-3 gap-y-0.5 mt-0.5 tabular-nums">
              {monthsSorted.map(([m, n]) => (
                <li key={m} className="flex justify-between gap-2">
                  <span>{formatMonthLabel(m, locale)}</span>
                  <span>{n}</span>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    );

    return {
      color,
      label,
      countryIso,
      isPerson,
      code: ent.key.code,
      total,
      activeWeeks: active,
      peakWeek,
      peakValue,
      peakX: xAt(peakIdx),
      peakY: yAt(peakValue),
      peakMonth,
      monthlyTotals: monthly,
      linePath: path.trim(),
      tooltipText,
      tooltipNode,
    };
  });

  return (
    <section className="mb-10">
      <h2 className="text-2xl font-bold mb-2">{t('volumeTitle')}</h2>
      <p className="text-sm text-dashboard-text-muted mb-4 max-w-3xl leading-snug">
        {t('volumeDescription')}
      </p>

      <div className="overflow-x-auto -mx-4 md:mx-0 px-4 md:px-0">
        <div className="min-w-[820px] md:min-w-0 bg-dashboard-surface border border-dashboard-border rounded-lg p-3">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          preserveAspectRatio="none"
          className="w-full"
          style={{ height: 'auto', aspectRatio: `${W} / ${H}` }}
          role="img"
          aria-label={t('volumeTitle')}
        >
          {/* Y log gridlines */}
          {yTicks.map((v, i) => {
            const y = yAt(v);
            return (
              <g key={i}>
                <line
                  x1={PAD_L}
                  x2={W - PAD_R}
                  y1={y}
                  y2={y}
                  stroke="#27272a"
                  strokeWidth={1}
                  strokeDasharray="2 3"
                />
                <text
                  x={PAD_L - 6}
                  y={y + 3}
                  textAnchor="end"
                  fontSize={10}
                  fill="#71717a"
                >
                  {v}
                </text>
              </g>
            );
          })}
          {/* Baseline at v=0 (solid) */}
          <line
            x1={PAD_L}
            x2={W - PAD_R}
            y1={yAt(0)}
            y2={yAt(0)}
            stroke="#27272a"
            strokeWidth={1}
          />

          {/* X month ticks */}
          {monthTicks.map((tk, i) => (
            <g key={i}>
              <line
                x1={tk.x}
                x2={tk.x}
                y1={PAD_T + innerH}
                y2={PAD_T + innerH + 3}
                stroke="#52525b"
                strokeWidth={1}
              />
              <text
                x={tk.x}
                y={PAD_T + innerH + 14}
                textAnchor="middle"
                fontSize={10}
                fill="#a1a1aa"
              >
                {tk.label} {tk.year}
              </text>
            </g>
          ))}

          {/* Lines */}
          {drawn.map(d => (
            <path
              key={`line-${d.code}`}
              d={d.linePath}
              fill="none"
              stroke={d.color}
              strokeWidth={1.8}
              strokeLinejoin="round"
              strokeLinecap="round"
              opacity={0.9}
            />
          ))}

          {/* Peak markers — sit ON the line (same yAt as the polyline) */}
          {drawn.map(d =>
            d.peakValue > 0 ? (
              <circle
                key={`peak-${d.code}`}
                cx={d.peakX}
                cy={d.peakY}
                r={5}
                fill={d.color}
                stroke="#0a0a0a"
                strokeWidth={1.5}
              >
                <title>{d.tooltipText}</title>
              </circle>
            ) : null
          )}
        </svg>
        </div>
      </div>

      {/* Legend — 1 col on phones, scales up on larger viewports.
          Each row: clickable label that navigates to peak month +
          shared InfoTip with rich peak/total/monthly breakdown
          (works on hover and tap). */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-x-4 gap-y-2 mt-3 text-xs">
        {drawn.map(d => (
          <div
            key={`leg-${d.code}`}
            className="flex items-center gap-2 min-w-0"
          >
            <span
              className="inline-block w-3 h-3 rounded-sm flex-shrink-0"
              style={{ backgroundColor: d.color }}
            />
            {d.isPerson ? (
              <span className="inline-flex items-center gap-1 flex-shrink-0">
                <PersonIcon className="w-3.5 h-3.5 text-dashboard-text-muted" />
                {d.countryIso && <FlagImg iso2={d.countryIso} size={14} />}
              </span>
            ) : (
              <FlagImg iso2={d.countryIso} size={16} className="flex-shrink-0" />
            )}
            <Link
              href={`/${locale}/sources/${feedSlug}/${d.peakMonth}`}
              className="truncate text-dashboard-text hover:text-blue-400 transition flex-shrink"
            >
              {d.label}
            </Link>
            <span className="ml-auto text-dashboard-text-muted/70 tabular-nums whitespace-nowrap text-[10px] sm:text-xs">
              {formatWeekLabel(d.peakWeek, locale)} · {d.peakValue}
            </span>
            <InfoTip width="wide">{d.tooltipNode}</InfoTip>
          </div>
        ))}
      </div>
    </section>
  );
}
