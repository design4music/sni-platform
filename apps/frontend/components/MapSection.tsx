'use client';

import { useState } from 'react';
import dynamic from 'next/dynamic';
import { useTranslations } from 'next-intl';
import type { AssetMapData, MapSelection } from './WorldMap';
import { ASSET_CATEGORIES } from './assetIcons';

const WorldMap = dynamic(() => import('./WorldMap'), { ssr: false });

interface MapSectionProps {
  centroids: Array<{
    id: string;
    label: string;
    iso_codes?: string[];
  }>;
}

export default function MapSection({ centroids }: MapSectionProps) {
  const t = useTranslations('map');
  const [fnMode, setFnMode] = useState(false);
  const [fnData, setFnData] = useState<AssetMapData | null>(null);
  const [selected, setSelected] = useState<MapSelection | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleToggle() {
    if (!fnMode && !fnData) {
      setLoading(true);
      try {
        const res = await fetch('/api/friction-nodes-map');
        const data: AssetMapData = await res.json();
        setFnData(data);
      } catch (err) {
        console.error('Failed to load strategic assets:', err);
        setLoading(false);
        return;
      }
      setLoading(false);
    }
    setSelected(null);
    setFnMode(m => !m);
  }

  return (
    <section>
      <div className="flex items-start justify-between mb-4 gap-4">
        <div>
          <h2 className="text-3xl font-bold">{t('title')}</h2>
          <p className="text-dashboard-text-muted mt-1">{t('subtitle')}</p>
        </div>
        <button
          onClick={handleToggle}
          disabled={loading}
          className={`shrink-0 mt-1 px-4 py-2 rounded-lg text-sm font-medium border transition-all ${
            fnMode
              ? 'bg-orange-500/20 border-orange-500/60 text-orange-300 hover:bg-orange-500/30'
              : 'bg-dashboard-surface border-dashboard-border text-dashboard-text-muted hover:border-orange-500/40 hover:text-orange-300'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {loading ? 'Loading...' : fnMode ? 'Hide conflicts' : 'Show conflicts'}
        </button>
      </div>
      <WorldMap
        centroids={centroids}
        fnMode={fnMode}
        fnData={fnData}
        selected={selected}
        onSelectChange={setSelected}
      />

      {fnMode && fnData && (
        <>
          {/* Legend: asset category colors + marker classes */}
          <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-[11px] text-dashboard-text-muted">
            <span className="flex items-center gap-1.5">
              <span className="inline-block w-4 h-4 rounded-full border border-red-500 bg-[#1a0a0a]" />
              Conflict zone
            </span>
            {Object.entries(ASSET_CATEGORIES).map(([key, { label, color }]) => (
              <span key={key} className="flex items-center gap-1.5">
                <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
                {label}
              </span>
            ))}
            <span className="flex items-center gap-1.5">
              <span className="inline-block w-2.5 h-2.5 rounded-full bg-slate-500 ring-2 ring-red-500/90" />
              Pressed by selected conflict
            </span>
          </div>

          {/* Strategic competitions: relationships, not places. Clicking a
              chip selects it on the map (arcs to capitals + actor highlight). */}
          {fnData.competitions.length > 0 && (
            <div className="mt-4">
              <div className="text-[11px] uppercase tracking-wider text-dashboard-text-muted mb-2">
                Strategic competitions (not mappable to a single region)
              </div>
              <div className="flex flex-wrap gap-2">
                {fnData.competitions.map(c => {
                  const isSelected = selected?.kind === 'competition' && selected.competition.id === c.id;
                  return (
                    <button
                      key={c.id}
                      onClick={() => setSelected(isSelected ? null : { kind: 'competition', competition: c })}
                      className={`flex items-center gap-2.5 px-3 py-2 rounded-lg border text-sm transition ${
                        isSelected
                          ? 'bg-red-950/50 border-red-500/70 text-dashboard-text'
                          : c.is_ghost
                            ? 'bg-dashboard-surface border-dashboard-border text-dashboard-text-muted hover:text-dashboard-text'
                            : 'bg-orange-950/30 border-orange-700/40 text-dashboard-text hover:border-orange-500/60'
                      }`}
                    >
                      <span>{c.name_en}</span>
                      {c.is_ghost ? (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 text-gray-500">
                          dormant
                        </span>
                      ) : (
                        <span className="flex items-center gap-1" title={`${c.total_events.toLocaleString()} events tracked`}>
                          {[1, 2, 3, 4, 5].map(pip => (
                            <span
                              key={pip}
                              className="w-1 h-1 rounded-full"
                              style={{
                                backgroundColor: c.intensity * 5 >= pip
                                  ? 'rgba(251,146,60,0.9)'
                                  : 'rgba(251,146,60,0.2)',
                              }}
                            />
                          ))}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}
    </section>
  );
}
