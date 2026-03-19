'use client';

import { useMemo, useState, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { useTranslations } from 'next-intl';
import type { NarrativeMapEntry } from '@/lib/types';
import { deriveTargetCentroids } from '@/lib/narrative-map-utils';
import NarrativePanel from './NarrativePanel';

// Dynamic import for Leaflet (SSR-incompatible)
const NarrativeGlobe = dynamic(() => import('./NarrativeGlobe'), { ssr: false });

interface NarrativeMapViewProps {
  narratives: NarrativeMapEntry[];
  centroidIsoMap: { id: string; iso_codes: string[] }[];
  centroidLabels?: Record<string, string>;
}

type Mode = 'outgoing' | 'incoming';

export default function NarrativeMapView({ narratives, centroidIsoMap, centroidLabels: centroidLabelsProp }: NarrativeMapViewProps) {
  const t = useTranslations('narrativeMap');
  const [mode, setMode] = useState<Mode>('outgoing');
  const [selectedCentroidId, setSelectedCentroidId] = useState<string | null>(null);

  // Build ISO -> centroid ID lookup (for map clicks)
  const isoToCentroidId = useMemo(() => {
    const map: Record<string, string> = {};
    for (const c of centroidIsoMap) {
      for (const iso of c.iso_codes) {
        map[iso.toUpperCase()] = c.id;
      }
    }
    return map;
  }, [centroidIsoMap]);

  // Build centroid ID -> ISO codes lookup (for highlighting)
  const centroidToIsos = useMemo(() => {
    const map: Record<string, string[]> = {};
    for (const c of centroidIsoMap) {
      map[c.id] = c.iso_codes.map(iso => iso.toUpperCase());
    }
    return map;
  }, [centroidIsoMap]);

  // Build centroid ID -> label lookup (prefer server-translated labels)
  const centroidLabels = useMemo(() => {
    if (centroidLabelsProp && Object.keys(centroidLabelsProp).length > 0) return centroidLabelsProp;
    const map: Record<string, string> = {};
    for (const n of narratives) {
      if (n.actor_centroid && n.actor_label) {
        map[n.actor_centroid] = n.actor_label;
      }
    }
    return map;
  }, [narratives, centroidLabelsProp]);

  // Pre-compute outgoing map: centroidId -> narratives where centroid is actor
  const outgoingMap = useMemo(() => {
    const map = new Map<string, NarrativeMapEntry[]>();
    for (const n of narratives) {
      if (!n.actor_centroid) continue;
      if (!map.has(n.actor_centroid)) map.set(n.actor_centroid, []);
      map.get(n.actor_centroid)!.push(n);
    }
    return map;
  }, [narratives]);

  // Pre-compute incoming map: centroidId -> narratives that target this centroid
  const incomingMap = useMemo(() => {
    const map = new Map<string, NarrativeMapEntry[]>();
    for (const n of narratives) {
      const targets = deriveTargetCentroids(n);
      for (const targetId of targets) {
        if (!map.has(targetId)) map.set(targetId, []);
        map.get(targetId)!.push(n);
      }
    }
    return map;
  }, [narratives]);

  // Compute selected ISOs and highlighted ISOs
  const { selectedIsos, highlightedIsos, panelNarratives } = useMemo(() => {
    const selected = new Set<string>();
    const highlighted = new Set<string>();
    let panel: NarrativeMapEntry[] = [];

    if (!selectedCentroidId) return { selectedIsos: selected, highlightedIsos: highlighted, panelNarratives: panel };

    // Highlight selected country's ISOs
    const selIsos = centroidToIsos[selectedCentroidId] || [];
    for (const iso of selIsos) selected.add(iso);

    if (mode === 'outgoing') {
      panel = outgoingMap.get(selectedCentroidId) || [];
      // Highlight target countries
      for (const n of panel) {
        const targets = deriveTargetCentroids(n);
        for (const targetId of targets) {
          const isos = centroidToIsos[targetId] || [];
          for (const iso of isos) highlighted.add(iso);
        }
      }
    } else {
      panel = incomingMap.get(selectedCentroidId) || [];
      // Highlight source countries (actors of narratives targeting us)
      for (const n of panel) {
        if (n.actor_centroid) {
          const isos = centroidToIsos[n.actor_centroid] || [];
          for (const iso of isos) highlighted.add(iso);
        }
      }
    }

    return { selectedIsos: selected, highlightedIsos: highlighted, panelNarratives: panel };
  }, [selectedCentroidId, mode, outgoingMap, incomingMap, centroidToIsos]);

  const selectedLabel = selectedCentroidId ? (centroidLabels[selectedCentroidId] || selectedCentroidId) : '';

  const handleCountryClick = useCallback((centroidId: string) => {
    setSelectedCentroidId(prev => prev === centroidId ? null : centroidId);
  }, []);

  const handleClose = useCallback(() => {
    setSelectedCentroidId(null);
  }, []);

  return (
    <div className="flex flex-col h-full">
      {/* Toggle */}
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-dashboard-text-muted hidden md:block">
          {selectedCentroidId ? '' : t('clickCountry')}
        </p>
        <div className="flex bg-dashboard-surface-raised rounded-lg p-0.5">
          <button
            onClick={() => setMode('outgoing')}
            className={`px-3 py-1.5 text-sm rounded-md transition ${
              mode === 'outgoing'
                ? 'bg-blue-600 text-white'
                : 'text-dashboard-text-muted hover:text-dashboard-text'
            }`}
          >
            {t('outgoing')}
          </button>
          <button
            onClick={() => setMode('incoming')}
            className={`px-3 py-1.5 text-sm rounded-md transition ${
              mode === 'incoming'
                ? 'bg-blue-600 text-white'
                : 'text-dashboard-text-muted hover:text-dashboard-text'
            }`}
          >
            {t('incoming')}
          </button>
        </div>
      </div>

      {/* Map + Panel layout */}
      <div className="flex flex-col md:flex-row flex-1 gap-4 min-h-0">
        {/* Map */}
        <div className={`${selectedCentroidId ? 'md:flex-1' : 'w-full'} h-[50vh] md:h-full`}>
          <NarrativeGlobe
            isoToCentroidId={isoToCentroidId}
            selectedIsos={selectedIsos}
            highlightedIsos={highlightedIsos}
            onCountryClick={handleCountryClick}
            mode={mode}
          />
        </div>

        {/* Panel */}
        {selectedCentroidId && (
          <div className="w-full md:w-96 md:h-full h-auto md:max-h-full overflow-hidden bg-dashboard-surface border border-dashboard-border rounded-lg">
            <NarrativePanel
              countryLabel={selectedLabel}
              narratives={panelNarratives}
              mode={mode}
              onClose={handleClose}
            />
          </div>
        )}
      </div>
    </div>
  );
}
