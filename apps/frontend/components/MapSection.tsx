'use client';

import { useState } from 'react';
import dynamic from 'next/dynamic';
import { useTranslations } from 'next-intl';
import type { FnMapData } from './WorldMap';

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
  const [fnData, setFnData] = useState<FnMapData | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleToggle() {
    if (!fnMode && !fnData) {
      setLoading(true);
      try {
        const res = await fetch('/api/friction-nodes-map');
        const data: FnMapData = await res.json();
        setFnData(data);
      } catch (err) {
        console.error('Failed to load friction nodes:', err);
        setLoading(false);
        return;
      }
      setLoading(false);
    }
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
      <WorldMap centroids={centroids} fnMode={fnMode} fnData={fnData} />
    </section>
  );
}
