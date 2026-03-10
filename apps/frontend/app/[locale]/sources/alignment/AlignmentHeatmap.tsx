'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import OutletLogo from '@/components/OutletLogo';

interface Publisher {
  name: string;
  domain: string | null;
  country: string | null;
  logoUrl: string;
  scores: Record<string, number>;
}

interface AlignmentHeatmapProps {
  publishers: Publisher[];
  centroids: [string, string][]; // [id, label][]
}

function scoreColor(score: number): string {
  if (score >= 1.0) return 'bg-green-500';
  if (score >= 0.5) return 'bg-green-500/70';
  if (score >= 0.15) return 'bg-green-500/40';
  if (score > -0.15) return 'bg-gray-500/30';
  if (score > -0.5) return 'bg-red-500/40';
  if (score > -1.0) return 'bg-red-500/70';
  return 'bg-red-500';
}

function cosineSimilarity(a: Record<string, number>, b: Record<string, number>): number {
  const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
  let dot = 0, magA = 0, magB = 0;
  for (const k of keys) {
    const va = a[k] || 0;
    const vb = b[k] || 0;
    dot += va * vb;
    magA += va * va;
    magB += vb * vb;
  }
  if (magA === 0 || magB === 0) return 0;
  return dot / (Math.sqrt(magA) * Math.sqrt(magB));
}

type SortMode = 'coverage' | 'name' | 'similarity';

export default function AlignmentHeatmap({ publishers, centroids }: AlignmentHeatmapProps) {
  const [sortMode, setSortMode] = useState<SortMode>('coverage');
  const [selectedPub, setSelectedPub] = useState<string | null>(null);
  const [minCoverage, setMinCoverage] = useState(3);

  const filtered = useMemo(() =>
    publishers.filter(p => Object.keys(p.scores).length >= minCoverage),
    [publishers, minCoverage]
  );

  const sorted = useMemo(() => {
    if (sortMode === 'name') return [...filtered].sort((a, b) => a.name.localeCompare(b.name));
    if (sortMode === 'similarity' && selectedPub) {
      const ref = filtered.find(p => p.name === selectedPub);
      if (ref) {
        return [...filtered].sort((a, b) => {
          if (a.name === selectedPub) return -1;
          if (b.name === selectedPub) return 1;
          return cosineSimilarity(ref.scores, b.scores) - cosineSimilarity(ref.scores, a.scores);
        });
      }
    }
    return filtered; // default: coverage order from server
  }, [filtered, sortMode, selectedPub]);

  // Visible centroids (only those with at least one score in filtered publishers)
  const visibleCentroids = useMemo(() => {
    const covered = new Set<string>();
    for (const p of filtered) {
      for (const cid of Object.keys(p.scores)) covered.add(cid);
    }
    return centroids.filter(([id]) => covered.has(id));
  }, [centroids, filtered]);

  return (
    <div>
      {/* Controls */}
      <div className="flex flex-wrap items-center gap-4 mb-4">
        <div className="flex items-center gap-2">
          <span className="text-xs text-dashboard-text-muted">Sort:</span>
          {(['coverage', 'name', 'similarity'] as SortMode[]).map(mode => (
            <button
              key={mode}
              onClick={() => setSortMode(mode)}
              className={`text-xs px-2 py-1 rounded transition-colors ${
                sortMode === mode
                  ? 'bg-blue-500/20 text-blue-400 font-medium'
                  : 'text-dashboard-text-muted hover:text-dashboard-text'
              }`}
              disabled={mode === 'similarity' && !selectedPub}
            >
              {mode === 'coverage' ? 'Coverage' : mode === 'name' ? 'A-Z' : 'Similarity'}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-dashboard-text-muted">Min regions:</span>
          {[1, 3, 5, 8].map(n => (
            <button
              key={n}
              onClick={() => setMinCoverage(n)}
              className={`text-xs px-2 py-1 rounded transition-colors ${
                minCoverage === n
                  ? 'bg-blue-500/20 text-blue-400 font-medium'
                  : 'text-dashboard-text-muted hover:text-dashboard-text'
              }`}
            >
              {n}+
            </button>
          ))}
        </div>
        {selectedPub && (
          <button
            onClick={() => { setSelectedPub(null); setSortMode('coverage'); }}
            className="text-xs text-blue-400 hover:text-blue-300"
          >
            Clear selection
          </button>
        )}
        <span className="text-xs text-dashboard-text-muted ml-auto">
          {sorted.length} publishers x {visibleCentroids.length} regions
        </span>
      </div>

      {/* Heatmap */}
      <div className="overflow-x-auto border border-dashboard-border rounded-lg">
        <table className="w-full border-collapse text-[11px]">
          <thead>
            <tr>
              <th className="sticky left-0 z-20 bg-dashboard-bg px-3 py-2 text-left font-medium text-dashboard-text-muted w-48 min-w-[192px]">
                Publisher
              </th>
              {visibleCentroids.map(([id, label]) => (
                <th
                  key={id}
                  className="px-1 py-2 font-medium text-dashboard-text-muted"
                  style={{ writingMode: 'vertical-rl', textOrientation: 'mixed', maxWidth: 28 }}
                >
                  <Link
                    href={`/c/${id}`}
                    className="hover:text-blue-400 transition-colors whitespace-nowrap"
                  >
                    {label.length > 18 ? label.slice(0, 16) + '..' : label}
                  </Link>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map(pub => {
              const isSelected = pub.name === selectedPub;
              return (
                <tr
                  key={pub.name}
                  className={`border-t border-dashboard-border/30 hover:bg-dashboard-surface/50 transition-colors ${
                    isSelected ? 'bg-blue-500/10' : ''
                  }`}
                  onClick={() => {
                    setSelectedPub(pub.name === selectedPub ? null : pub.name);
                    if (pub.name !== selectedPub) setSortMode('similarity');
                  }}
                  style={{ cursor: 'pointer' }}
                >
                  <td className="sticky left-0 z-10 bg-dashboard-bg px-3 py-1.5 whitespace-nowrap">
                    <Link
                      href={`/sources/${encodeURIComponent(pub.name).replace(/\./g, '%2E')}`}
                      className="inline-flex items-center gap-1.5 hover:text-blue-400 transition-colors"
                      onClick={e => e.stopPropagation()}
                    >
                      <OutletLogo src={pub.logoUrl} name={pub.name} size={14} className="rounded-sm" />
                      <span className="truncate max-w-[140px]">{pub.name}</span>
                    </Link>
                  </td>
                  {visibleCentroids.map(([cid]) => {
                    const score = pub.scores[cid];
                    if (score === undefined) {
                      return <td key={cid} className="px-0.5 py-0.5"><div className="w-5 h-5 mx-auto" /></td>;
                    }
                    const sign = score > 0 ? '+' : '';
                    return (
                      <td key={cid} className="px-0.5 py-0.5">
                        <div
                          className={`w-5 h-5 mx-auto rounded-sm ${scoreColor(score)} flex items-center justify-center`}
                          title={`${pub.name} -> ${cid}: ${sign}${score.toFixed(1)}`}
                        >
                          <span className="text-[8px] font-medium text-white/80 tabular-nums">
                            {score.toFixed(1)}
                          </span>
                        </div>
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-3 mt-4 text-[10px] text-dashboard-text-muted">
        <span className="flex items-center gap-1"><span className="w-4 h-3 rounded-sm bg-red-500 inline-block" /> Adversarial</span>
        <span className="flex items-center gap-1"><span className="w-4 h-3 rounded-sm bg-red-500/40 inline-block" /> Skeptical</span>
        <span className="flex items-center gap-1"><span className="w-4 h-3 rounded-sm bg-gray-500/30 inline-block" /> Reportorial</span>
        <span className="flex items-center gap-1"><span className="w-4 h-3 rounded-sm bg-green-500/40 inline-block" /> Constructive</span>
        <span className="flex items-center gap-1"><span className="w-4 h-3 rounded-sm bg-green-500 inline-block" /> Promotional</span>
      </div>
      <p className="text-center text-[10px] text-dashboard-text-muted mt-2">
        Click a publisher row to sort others by editorial similarity (cosine distance).
      </p>
    </div>
  );
}
