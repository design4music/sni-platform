'use client';

import { useMemo, useState } from 'react';
import type { Event } from '@/lib/types';

const IRAN_KEYWORDS = /\b(iran|tehran|khamenei|hormuz|kharg|isfahan|persian|natanz|strait|gulf|iraq|kuwait|israel|mideast|middle\s+east|pezeshkian|irgc|ayatollah)\b/i;

function isIranWar(title?: string, summary?: string, bucket?: string | null): boolean {
  if (bucket === 'MIDEAST-IRAN' || bucket === 'MIDEAST-GULF' || bucket === 'MIDEAST-IRAQ' || bucket === 'MIDEAST-ISRAEL') return true;
  return IRAN_KEYWORDS.test(title || '') || IRAN_KEYWORDS.test(summary || '');
}

interface FamilyRow {
  id: string;
  title: string;
  events: Event[];
  totalSources: number;
  dominantBucket: string | null;
  peakDay: number;
  firstDay: number;
}

interface Props {
  events: Event[];
  month: string; // "2026-03"
}

const MIN_SRC = 5;
const LABEL_W = 260;
const DAY_W = 26;
const ROW_H = 28;
const HEADER_H = 32;
const PAD_Y = 12;

function dotRadius(sources: number): number {
  return Math.max(3, Math.min(13, 2 + Math.log2(Math.max(1, sources)) * 1.2));
}

function shortenBucket(b: string | null): string {
  if (!b) return 'domestic';
  return b.replace(/^MIDEAST-/, '').replace(/^AMERICAS-/, '').replace(/^EUROPE-/, '').replace(/^ASIA-/, '').toLowerCase();
}

export default function IranWarSwimlane({ events, month }: Props) {
  const [hovered, setHovered] = useState<{ famId: string; idx: number } | null>(null);
  const [hoveredRow, setHoveredRow] = useState<string | null>(null);

  const { families, days } = useMemo(() => {
    const famMap = new Map<string, FamilyRow>();

    for (const e of events) {
      if (!e.family_id || !e.family_title) continue;
      if (!isIranWar(e.family_title, e.family_summary, e.bucket_key)) continue;
      const src = e.source_title_ids?.length || 0;
      if (src < MIN_SRC) continue;
      let row = famMap.get(e.family_id);
      if (!row) {
        row = { id: e.family_id, title: e.family_title, events: [], totalSources: 0, dominantBucket: null, peakDay: 0, firstDay: 99 };
        famMap.set(e.family_id, row);
      }
      row.events.push(e);
      row.totalSources += src;
    }

    for (const row of famMap.values()) {
      const bucketCounts = new Map<string, number>();
      for (const e of row.events) {
        const b = e.bucket_key || '__domestic';
        bucketCounts.set(b, (bucketCounts.get(b) || 0) + (e.source_title_ids?.length || 0));
      }
      let bestBucket: string | null = null, bestN = -1;
      for (const [b, n] of bucketCounts) {
        if (n > bestN) { bestN = n; bestBucket = b === '__domestic' ? null : b; }
      }
      row.dominantBucket = bestBucket;

      const dayBins = new Map<number, number>();
      let minDay = 99;
      for (const e of row.events) {
        const d = new Date(e.date + 'T00:00:00').getUTCDate();
        if (d < minDay) minDay = d;
        dayBins.set(d, (dayBins.get(d) || 0) + (e.source_title_ids?.length || 0));
      }
      let pd = 0, pv = -1;
      for (const [d, v] of dayBins) if (v > pv) { pv = v; pd = d; }
      row.peakDay = pd;
      row.firstDay = minDay;
    }

    const [y, m] = month.split('-').map(Number);
    const daysInMonth = new Date(y, m, 0).getDate();
    const dayList = Array.from({ length: daysInMonth }, (_, i) => i + 1);

    const sorted = [...famMap.values()].sort((a, b) => {
      if (a.firstDay !== b.firstDay) return a.firstDay - b.firstDay;
      return b.totalSources - a.totalSources;
    });
    return { families: sorted, days: dayList };
  }, [events, month]);

  if (families.length === 0) return null;

  const gridW = days.length * DAY_W;
  const totalW = LABEL_W + gridW + 110;
  const totalH = HEADER_H + families.length * ROW_H + PAD_Y * 2;
  const totalTopics = families.reduce((s, f) => s + f.events.length, 0);
  const totalSources = families.reduce((s, f) => s + f.totalSources, 0);

  const hoveredEvent = hovered
    ? families.find(f => f.id === hovered.famId)?.events[hovered.idx]
    : null;

  return (
    <section className="w-full bg-dashboard-surface border border-dashboard-border rounded-lg p-5 mb-8">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-dashboard-text">Iran War — March 2026 Timeline</h2>
          <p className="text-xs text-dashboard-text-muted mt-0.5">
            {families.length} families · {totalTopics} topics · {totalSources.toLocaleString()} sources · dot size = sources, hover for detail
          </p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <svg width={totalW} height={totalH} className="block select-none">
          {/* Day header + week grid */}
          {days.map(d => {
            const x = LABEL_W + (d - 1) * DAY_W + DAY_W / 2;
            const isWeekStart = (d - 1) % 7 === 0;
            const showLabel = d === 1 || d % 5 === 0 || d === days.length;
            return (
              <g key={d}>
                {isWeekStart && d > 1 && (
                  <line
                    x1={x - DAY_W / 2} y1={HEADER_H - 4}
                    x2={x - DAY_W / 2} y2={HEADER_H + families.length * ROW_H + PAD_Y}
                    stroke="currentColor" className="text-dashboard-border" strokeWidth={0.5}
                  />
                )}
                {showLabel && (
                  <text x={x} y={HEADER_H - 14} textAnchor="middle" fontSize={11}
                    className="fill-dashboard-text-muted">{d}</text>
                )}
              </g>
            );
          })}

          {/* "Mar" label */}
          <text x={LABEL_W - 8} y={HEADER_H - 14} textAnchor="end" fontSize={10}
            className="fill-dashboard-text-muted uppercase tracking-wider">Mar</text>

          {/* Rows */}
          {families.map((f, rowIdx) => {
            const rowTop = HEADER_H + PAD_Y + rowIdx * ROW_H;
            const y = rowTop + ROW_H / 2;
            const label = f.title.length > 42 ? f.title.slice(0, 40) + '…' : f.title;
            const bucketPillX = LABEL_W + gridW + 10;
            const isRowHov = hoveredRow === f.id;
            const zebra = rowIdx % 2 === 1;
            return (
              <g key={f.id}
                onMouseEnter={() => setHoveredRow(f.id)}
                onMouseLeave={() => setHoveredRow(null)}>
                {/* zebra background */}
                <rect x={0} y={rowTop} width={LABEL_W + gridW + 100} height={ROW_H}
                  className={isRowHov ? 'fill-blue-500/10' : (zebra ? 'fill-white/[0.015]' : 'fill-transparent')} />
                {/* top separator */}
                <line x1={0} y1={rowTop} x2={LABEL_W + gridW + 100} y2={rowTop}
                  stroke="currentColor" className="text-dashboard-border opacity-40" strokeWidth={0.5} />

                <text x={LABEL_W - 10} y={y + 4} textAnchor="end" fontSize={12}
                  className={isRowHov ? 'fill-blue-300' : 'fill-dashboard-text'}>
                  {label}
                </text>
                {/* bucket pill */}
                <text x={bucketPillX} y={y + 4} fontSize={10}
                  className="fill-dashboard-text-muted">
                  {shortenBucket(f.dominantBucket)}
                </text>

                {f.events.map((e, i) => {
                  const day = new Date(e.date + 'T00:00:00').getUTCDate();
                  const cx = LABEL_W + (day - 1) * DAY_W + DAY_W / 2;
                  const src = e.source_title_ids?.length || 0;
                  const r = dotRadius(src);
                  const isHov = hovered?.famId === f.id && hovered?.idx === i;
                  return (
                    <circle
                      key={`${f.id}-${i}`} cx={cx} cy={y} r={r}
                      className={`cursor-pointer transition-all ${isHov ? 'fill-blue-300' : 'fill-blue-500/75 hover:fill-blue-400'}`}
                      stroke={isHov ? 'white' : 'none'} strokeWidth={1.5}
                      onMouseEnter={() => setHovered({ famId: f.id, idx: i })}
                      onMouseLeave={() => setHovered(null)}
                      onClick={() => { if (e.event_id) window.location.href = `/events/${e.event_id}`; }}
                    />
                  );
                })}
              </g>
            );
          })}
          {/* bottom border */}
          <line
            x1={0} y1={HEADER_H + PAD_Y + families.length * ROW_H}
            x2={LABEL_W + gridW + 100} y2={HEADER_H + PAD_Y + families.length * ROW_H}
            stroke="currentColor" className="text-dashboard-border opacity-40" strokeWidth={0.5} />
        </svg>
      </div>

      {(hoveredEvent || hoveredRow) && (
        <div className="mt-3 pt-3 border-t border-dashboard-border text-sm space-y-1">
          {hoveredRow && !hoveredEvent && (() => {
            const fam = families.find(f => f.id === hoveredRow);
            return fam ? (
              <div className="flex items-baseline gap-3">
                <span className="text-xs text-dashboard-text-muted whitespace-nowrap uppercase tracking-wider">family</span>
                <span className="text-dashboard-text font-medium">{fam.title}</span>
              </div>
            ) : null;
          })()}
          {hoveredEvent && (
            <div className="flex items-baseline gap-3">
              <span className="text-xs text-dashboard-text-muted whitespace-nowrap">
                {new Date(hoveredEvent.date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                {' · '}{hoveredEvent.source_title_ids?.length || 0} src
              </span>
              <span className="text-dashboard-text">{hoveredEvent.title}</span>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
