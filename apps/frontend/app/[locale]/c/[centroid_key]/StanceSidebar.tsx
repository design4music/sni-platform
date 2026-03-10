'use client';

import { useState } from 'react';
import Link from 'next/link';
import OutletLogo from '@/components/OutletLogo';

interface StanceEntry {
  feed_name: string;
  source_domain: string | null;
  score: number;
  logoUrl: string | null;
}

interface StanceBucket {
  label: string;
  color: string;
  bg: string;
  entries: StanceEntry[];
}

interface StanceSidebarProps {
  scores: StanceEntry[];
  month: string;
  title: string;
}

function bucketize(scores: StanceEntry[]): StanceBucket[] {
  const buckets: StanceBucket[] = [
    { label: 'Adversarial', color: 'text-red-400', bg: 'bg-red-500/80', entries: [] },
    { label: 'Skeptical', color: 'text-red-300', bg: 'bg-red-500/40', entries: [] },
    { label: 'Reportorial', color: 'text-gray-400', bg: 'bg-gray-500/30', entries: [] },
    { label: 'Constructive', color: 'text-green-300', bg: 'bg-green-500/40', entries: [] },
    { label: 'Promotional', color: 'text-green-400', bg: 'bg-green-500/80', entries: [] },
  ];

  for (const s of scores) {
    if (s.score <= -1.0) buckets[0].entries.push(s);
    else if (s.score < -0.3) buckets[1].entries.push(s);
    else if (s.score <= 0.3) buckets[2].entries.push(s);
    else if (s.score < 1.0) buckets[3].entries.push(s);
    else buckets[4].entries.push(s);
  }

  // Sort entries within each bucket by absolute score descending
  for (const b of buckets) {
    b.entries.sort((a, b) => Math.abs(b.score) - Math.abs(a.score));
  }

  return buckets;
}

function BucketRow({ bucket }: { bucket: StanceBucket }) {
  const [expanded, setExpanded] = useState(false);
  if (bucket.entries.length === 0) return null;

  const visible = expanded ? bucket.entries : bucket.entries.slice(0, 5);
  const remaining = bucket.entries.length - 5;

  return (
    <div className="mb-3 last:mb-0">
      <div className="flex items-center gap-2 mb-1.5">
        <span className={`w-2.5 h-2.5 rounded-full ${bucket.bg} flex-shrink-0`} />
        <span className={`text-xs font-medium ${bucket.color}`}>{bucket.label}</span>
        <span className="text-[10px] text-dashboard-text-muted">({bucket.entries.length})</span>
      </div>
      <div className="flex flex-wrap gap-1 pl-4">
        {visible.map(s => {
          const sign = s.score > 0 ? '+' : '';
          return (
            <Link
              key={s.feed_name}
              href={`/sources/${encodeURIComponent(s.feed_name).replace(/\./g, '%2E')}`}
              className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-dashboard-border/40 hover:bg-dashboard-border transition text-[11px]"
              title={`${s.feed_name}: ${sign}${s.score.toFixed(1)}`}
            >
              <OutletLogo src={s.logoUrl || ''} name={s.feed_name} size={14} className="rounded-sm" />
              <span className="text-dashboard-text truncate max-w-[70px]">{s.feed_name}</span>
              <span className="text-dashboard-text-muted tabular-nums">{sign}{s.score.toFixed(1)}</span>
            </Link>
          );
        })}
        {remaining > 0 && !expanded && (
          <button
            onClick={() => setExpanded(true)}
            className="text-[10px] text-blue-400 hover:text-blue-300 px-1.5 py-0.5"
          >
            +{remaining} more
          </button>
        )}
        {expanded && remaining > 0 && (
          <button
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

export default function StanceSidebar({ scores, month, title }: StanceSidebarProps) {
  if (scores.length === 0) return null;

  const buckets = bucketize(scores);
  const nonEmpty = buckets.filter(b => b.entries.length > 0);
  if (nonEmpty.length === 0) return null;

  return (
    <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider">
          {title}
        </h3>
        <span className="text-[10px] text-dashboard-text-muted">{month}</span>
      </div>
      {/* Spectrum bar */}
      <div className="flex h-1.5 rounded-full overflow-hidden mb-3">
        <div className="flex-1 bg-red-500/80" />
        <div className="flex-1 bg-red-500/40" />
        <div className="flex-1 bg-gray-500/30" />
        <div className="flex-1 bg-green-500/40" />
        <div className="flex-1 bg-green-500/80" />
      </div>
      {buckets.map(b => (
        <BucketRow key={b.label} bucket={b} />
      ))}
    </div>
  );
}
