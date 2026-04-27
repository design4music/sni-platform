import Link from 'next/link';
import { getTranslations } from 'next-intl/server';
import { getCountryName } from '@/lib/countries';
import FlagImg from './FlagImg';
import PersonIcon from './PersonIcon';
import type { OutletStanceTimelineRow } from '@/lib/queries';

interface Props {
  /** Slug for building cell links to monthly detail pages. */
  feedSlug: string;
  /** Locale for routing. */
  locale: string;
  rows: OutletStanceTimelineRow[];
  /** Cap number of entity rows. Selection: most months covered DESC,
   *  then total volume DESC. Default 12. */
  topN?: number;
}

const CELL_BORDER = '#1f2937';
const CELL_H = 34;

/** Hue from stance score (matches WorldMap palette). null/undefined = neutral. */
function stanceHue(stance: number | null): string {
  if (stance == null) return '#71717a'; // zinc-500
  if (stance <= -2) return '#b91c1c';
  if (stance === -1) return '#ef4444';
  if (stance === 0) return '#71717a';
  if (stance === 1) return '#10b981';
  return '#15803d';
}

/** Opacity from coverage volume; logarithmic with a 0.30 floor so colour stays
 *  visible. Cells with no coverage that month return ~0 (rendered separately). */
function cellOpacity(n: number, max: number): number {
  if (n <= 0 || max <= 0) return 0;
  const t = Math.log10(n + 1) / Math.log10(max + 1);
  return 0.35 + 0.55 * t;
}

interface EntityKey {
  kind: 'country' | 'person';
  code: string;
  country: string | null;
}

/** Extends a list of months with placeholders through Dec of the latest
 *  year present in the data. e.g. ['2026-01', ..., '2026-04'] →
 *  ['2026-01', ..., '2026-04', '2026-05', ..., '2026-12'].
 *  Months that fall *between* min and max but have no data stay in the
 *  list as well (no-stance cells render as dashed empties). */
function expandToYearEnd(dataMonths: string[]): { months: string[]; lastDataMonth: string } {
  if (dataMonths.length === 0) return { months: [], lastDataMonth: '' };
  const sorted = [...dataMonths].sort();
  const first = sorted[0];
  const last = sorted[sorted.length - 1];
  const lastYear = Number(last.slice(0, 4));
  let [yr, mo] = first.split('-').map(Number);
  const out: string[] = [];
  while (yr < lastYear || (yr === lastYear && mo <= 12)) {
    out.push(`${yr}-${String(mo).padStart(2, '0')}`);
    mo += 1;
    if (mo > 12) {
      mo = 1;
      yr += 1;
    }
  }
  return { months: out, lastDataMonth: last };
}

export default async function OutletStanceHeatmap({
  feedSlug,
  locale,
  rows,
  topN = 12,
}: Props) {
  const t = await getTranslations('sources');

  if (rows.length === 0) {
    return (
      <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-6 text-sm text-dashboard-text-muted">
        {t('heatmapEmpty')}
      </div>
    );
  }

  // Distinct months in chronological order
  const dataMonthsSet = new Set<string>();
  rows.forEach(r => dataMonthsSet.add(r.month));
  const dataMonths = [...dataMonthsSet].sort();
  const { months, lastDataMonth } = expandToYearEnd(dataMonths);

  // Aggregate per entity: total months covered, total volume
  type Agg = {
    key: EntityKey;
    monthCount: number;
    total: number;
    cells: Map<string, OutletStanceTimelineRow>;
  };
  const byEntity = new Map<string, Agg>();
  for (const r of rows) {
    const id = `${r.entity_kind}:${r.entity_code}`;
    let a = byEntity.get(id);
    if (!a) {
      a = {
        key: { kind: r.entity_kind, code: r.entity_code, country: r.entity_country },
        monthCount: 0,
        total: 0,
        cells: new Map(),
      };
      byEntity.set(id, a);
    }
    a.cells.set(r.month, r);
    a.monthCount += 1;
    a.total += r.n_headlines;
  }

  const topEntities = [...byEntity.values()]
    .sort((a, b) => b.monthCount - a.monthCount || b.total - a.total)
    .slice(0, topN);

  if (topEntities.length === 0) return null;

  // Max headline count across all displayed cells, for opacity scaling
  let max = 0;
  for (const ent of topEntities) {
    for (const c of ent.cells.values()) if (c.n_headlines > max) max = c.n_headlines;
  }
  if (max === 0) max = 1;

  // Phone-only horizontal scroll. iPad+ shrinks cells via `table-fixed`
  // so all months fit. Min-width covers the small-phone case (~360px).
  const entityColW = 132;
  const phoneMinWidth =
    entityColW + months.length * 44 + 56; /* total col + paddings */

  return (
    <section className="mb-10">
      <h2 className="text-2xl font-bold mb-2">{t('heatmapTitle')}</h2>
      <p className="text-sm text-dashboard-text-muted mb-4 max-w-3xl leading-snug">
        {t('heatmapDescription')}
      </p>

      <div className="overflow-x-auto md:overflow-x-visible -mx-4 md:mx-0 px-4 md:px-0">
        <div
          className="bg-dashboard-surface border border-dashboard-border rounded-lg p-3"
          style={{ minWidth: 0 }}
        >
        <table
          className="border-separate w-full table-fixed"
          style={{ borderSpacing: 4, minWidth: phoneMinWidth }}
        >
          <colgroup>
            <col style={{ width: entityColW }} />
            {months.map(m => (
              <col key={`col-${m}`} />
            ))}
            <col style={{ width: 56 }} />
          </colgroup>
          <thead>
            <tr>
              <th
                className="text-left text-[11px] uppercase tracking-wider text-dashboard-text-muted font-medium pr-3 pb-2 align-bottom"
              >
                {t('heatmapEntityHeader')}
              </th>
              {months.map(m => {
                const isPlaceholder = m > lastDataMonth;
                const [y, mm] = m.split('-').map(Number);
                const label = new Date(y, mm - 1, 1).toLocaleDateString(
                  locale === 'de' ? 'de-DE' : 'en-US',
                  { month: 'short' }
                );
                return (
                  <th key={m} className="text-center pb-2 px-0">
                    {isPlaceholder ? (
                      <span
                        className="inline-block text-[11px] uppercase tracking-wider text-dashboard-text-muted/40 tabular-nums"
                        title={t('heatmapPlaceholder')}
                      >
                        {label}
                        <span className="block text-[9px] opacity-60">{y}</span>
                      </span>
                    ) : (
                      <Link
                        href={`/${locale}/sources/${feedSlug}/${m}`}
                        className="inline-block text-[11px] uppercase tracking-wider text-dashboard-text-muted hover:text-blue-400 transition tabular-nums"
                        title={t('heatmapMonthLink', { month: m })}
                      >
                        {label}
                        <span className="block text-[9px] opacity-70">{y}</span>
                      </Link>
                    )}
                  </th>
                );
              })}
              <th className="text-right pl-2 pb-2 text-[11px] uppercase tracking-wider text-dashboard-text-muted font-medium">
                {t('heatmapTotal')}
              </th>
            </tr>
          </thead>
          <tbody>
            {topEntities.map(ent => {
              const isPerson = ent.key.kind === 'person';
              const countryIso = isPerson ? ent.key.country : ent.key.code;
              const label = isPerson
                ? ent.key.code
                : getCountryName(ent.key.code) || ent.key.code;
              return (
                <tr key={`${ent.key.kind}:${ent.key.code}`}>
                  <td className="pr-3 py-1.5 text-sm overflow-hidden">
                    <span className="inline-flex items-center gap-1.5 min-w-0 max-w-full">
                      {isPerson ? (
                        <span className="inline-flex items-center gap-1 flex-shrink-0">
                          <PersonIcon className="w-3.5 h-3.5 text-dashboard-text-muted" />
                          {countryIso && <FlagImg iso2={countryIso} size={14} />}
                        </span>
                      ) : (
                        <FlagImg iso2={countryIso} size={16} className="flex-shrink-0" />
                      )}
                      <span className="text-dashboard-text truncate">{label}</span>
                    </span>
                  </td>
                  {months.map(m => {
                    const isPlaceholder = m > lastDataMonth;
                    const cell = ent.cells.get(m);

                    if (isPlaceholder) {
                      return (
                        <td key={m} className="text-center px-0" style={{ height: CELL_H }}>
                          <span
                            className="block rounded text-dashboard-text-muted/30"
                            style={{
                              width: '100%',
                              height: '100%',
                              backgroundImage:
                                'repeating-linear-gradient(45deg,#0f1115,#0f1115 4px,#1a1d23 4px,#1a1d23 8px)',
                            }}
                            title={t('heatmapPlaceholder')}
                          />
                        </td>
                      );
                    }

                    if (!cell) {
                      return (
                        <td key={m} className="text-center px-0" style={{ height: CELL_H }}>
                          <span
                            className="block rounded text-[10px] text-dashboard-text-muted/40"
                            style={{
                              width: '100%',
                              height: '100%',
                              border: `1px dashed ${CELL_BORDER}`,
                              lineHeight: `${CELL_H - 2}px`,
                            }}
                          >
                            ·
                          </span>
                        </td>
                      );
                    }

                    const hue = stanceHue(cell.stance);
                    const op = cellOpacity(cell.n_headlines, max);
                    const stanceText =
                      cell.stance == null
                        ? '?'
                        : (cell.stance > 0 ? `+${cell.stance}` : `${cell.stance}`);
                    const tooltip = `${m} · ${cell.n_headlines} ${t('titles')} · stance ${stanceText}${cell.confidence ? ` (${cell.confidence})` : ''}${cell.tone ? `\n${cell.tone}` : ''}`;
                    return (
                      <td key={m} className="text-center px-0" style={{ height: CELL_H }}>
                        <Link
                          href={`/${locale}/sources/${feedSlug}/${m}`}
                          title={tooltip}
                          className="block rounded text-xs font-semibold tabular-nums hover:ring-2 hover:ring-blue-400 transition"
                          style={{
                            width: '100%',
                            height: '100%',
                            backgroundColor: hue,
                            opacity: op,
                            color: '#ffffff',
                            border: `1px solid ${CELL_BORDER}`,
                            lineHeight: `${CELL_H - 2}px`,
                          }}
                        >
                          {stanceText}
                        </Link>
                      </td>
                    );
                  })}
                  <td className="text-right pl-2 text-xs text-dashboard-text-muted tabular-nums">
                    {ent.total.toLocaleString()}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        </div>
      </div>

      {/* Inline legend */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-3 text-[11px] text-dashboard-text-muted">
        <span className="font-semibold text-dashboard-text">{t('heatmapLegend')}:</span>
        <span className="inline-flex items-center gap-1.5">
          <span className="w-3 h-3 rounded" style={{ backgroundColor: '#b91c1c' }} /> &minus;2 {t('stanceHostile')}
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="w-3 h-3 rounded" style={{ backgroundColor: '#ef4444' }} /> &minus;1
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="w-3 h-3 rounded" style={{ backgroundColor: '#71717a' }} /> 0
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="w-3 h-3 rounded" style={{ backgroundColor: '#10b981' }} /> +1
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="w-3 h-3 rounded" style={{ backgroundColor: '#15803d' }} /> +2 {t('stanceSupportive')}
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span
            className="w-3 h-3 rounded inline-block"
            style={{
              backgroundImage:
                'repeating-linear-gradient(45deg,#0f1115,#0f1115 2px,#1a1d23 2px,#1a1d23 4px)',
            }}
          />
          {t('heatmapPlaceholder')}
        </span>
        <span className="text-dashboard-text-muted/70">{t('heatmapOpacityNote')}</span>
      </div>
    </section>
  );
}
