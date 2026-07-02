'use client';

import { useEffect, useState, useRef } from 'react';
import { MapContainer, GeoJSON, useMap } from 'react-leaflet';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import Link from 'next/link';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import StrategicAssetLayer from './StrategicAssetLayer';

export interface AssetMapData {
  assets: Array<{
    id: string;
    name_en: string;
    name_de: string | null;
    asset_type: string;
    geometry: unknown; // GeoJSON Point | LineString | Polygon
    commodities: string[];
    criticality: number;
    description_en: string | null;
    description_de: string | null;
    stress: number; // 0-1
    fns: Array<{
      id: string;
      name_en: string;
      total_events: number;
      last_active: string | null;
      is_ghost: boolean;
    }>;
  }>;
  conflicts: Array<{
    id: string;
    name_en: string;
    anchor: unknown; // GeoJSON Point
    affected_asset_ids: string[];
    total_events: number;
    last_active: string | null;
    is_ghost: boolean;
    intensity: number;
  }>;
  competitions: Array<{
    id: string;
    name_en: string;
    total_events: number;
    last_active: string | null;
    is_ghost: boolean;
    intensity: number;
  }>;
}

type Asset = AssetMapData['assets'][0];
type Conflict = AssetMapData['conflicts'][0];

export type MapSelection =
  | { kind: 'asset'; asset: Asset }
  | { kind: 'conflict'; conflict: Conflict };

interface WorldMapProps {
  centroids: Array<{
    id: string;
    label: string;
    iso_codes?: string[];
    source_count?: number;
    stance?: number | null;
    tone?: string | null;
    confidence?: 'low' | 'medium' | 'high' | null;
    n_headlines?: number;
  }>;
  fnMode?: boolean;
  fnData?: AssetMapData | null;
}

function getHeatmapColor(sourceCount: number, maxCount: number): string {
  if (sourceCount === 0 || maxCount === 0) return '#4a4a3a';
  const intensity = Math.log10(sourceCount + 1) / Math.log10(maxCount + 1);
  if (intensity < 0.2) return '#6b6b4a';
  if (intensity < 0.4) return '#eab308';
  if (intensity < 0.6) return '#f59e0b';
  if (intensity < 0.8) return '#f97316';
  return '#dc2626';
}

function stanceFill(
  stance: number | null | undefined,
  sourceCount: number,
  maxCount: number,
): { fillColor: string; fillOpacity: number } {
  let hue = '#71717a';
  if (stance != null) {
    if (stance <= -2) hue = '#b91c1c';
    else if (stance === -1) hue = '#ef4444';
    else if (stance === 0) hue = '#71717a';
    else if (stance === 1) hue = '#10b981';
    else if (stance >= 2) hue = '#15803d';
  }
  if (sourceCount === 0 || maxCount === 0) return { fillColor: hue, fillOpacity: 0.15 };
  const t = Math.log10(sourceCount + 1) / Math.log10(maxCount + 1);
  return { fillColor: hue, fillOpacity: 0.3 + 0.55 * t };
}

function MapController() {
  const map = useMap();
  useEffect(() => { map.invalidateSize(); }, [map]);
  return null;
}


export default function WorldMap({ centroids, fnMode = false, fnData = null }: WorldMapProps) {
  const [geoData, setGeoData] = useState<any>(null);
  const [isClient, setIsClient] = useState(false);
  const [selected, setSelected] = useState<MapSelection | null>(null);
  const mapInitialized = useRef(false);
  const fnModeRef = useRef(fnMode);
  const router = useRouter();
  const t = useTranslations('map');

  useEffect(() => { fnModeRef.current = fnMode; }, [fnMode]);
  useEffect(() => { if (!fnMode) setSelected(null); }, [fnMode]);
  useEffect(() => { setIsClient(true); }, []);

  useEffect(() => {
    if (!mapInitialized.current) {
      fetch('/geo/countries.geojson')
        .then(res => res.json())
        .then(data => setGeoData(data));
      mapInitialized.current = true;
    }
  }, []);

  const stanceMode = centroids.some(c => 'stance' in c);

  type CentroidEntry = {
    id: string; label: string; allIsoCodes: string[];
    sourceCount: number; stance: number | null | undefined;
    tone: string | null | undefined; confidence: 'low' | 'medium' | 'high' | null | undefined;
  };
  const isoToCentroid = new Map<string, CentroidEntry>();
  const centroidRef = useRef<Map<string, CentroidEntry>>(new Map());
  const maxSourceCount = Math.max(...centroids.map(c => c.source_count || 0), 1);

  centroids.forEach(c => {
    if (c.iso_codes) {
      const entry: CentroidEntry = {
        id: c.id, label: c.label, allIsoCodes: c.iso_codes,
        sourceCount: c.source_count || 0, stance: c.stance,
        tone: c.tone, confidence: c.confidence,
      };
      c.iso_codes.forEach(iso => isoToCentroid.set(iso.toUpperCase(), entry));
    }
  });
  centroidRef.current = isoToCentroid;

  if (!isClient || !geoData) {
    return (
      <div className="w-full h-[500px] bg-dashboard-surface rounded-lg flex items-center justify-center">
        <p className="text-dashboard-text-muted">{t('loading')}</p>
      </div>
    );
  }

  const onEachFeature = (feature: any, layer: any) => {
    if (fnMode) return;

    let iso2 = feature.properties['ISO3166-1-Alpha-2'];
    const name = feature.properties.name;
    if (name === 'France') iso2 = 'FR';
    if (name === 'Norway') iso2 = 'NO';
    if (name === 'Kosovo') iso2 = 'XK';
    if (iso2 === 'CN-TW') iso2 = 'TW';

    const centroid = isoToCentroid.get(iso2);
    if (!centroid) return;

    let tipHTML = `<strong>${centroid.label}</strong><br/><span style="opacity:0.7">${centroid.sourceCount.toLocaleString()} ${t('articles')}</span>`;
    if (stanceMode && centroid.stance != null) {
      const sign = centroid.stance > 0 ? `+${centroid.stance}` : `${centroid.stance}`;
      tipHTML += `<br/><span style="opacity:0.85">stance: ${sign}`;
      if (centroid.confidence) tipHTML += ` (${centroid.confidence})`;
      tipHTML += `</span>`;
      if (centroid.tone) tipHTML += `<br/><span style="opacity:0.65;font-style:italic">${centroid.tone}</span>`;
    } else if (stanceMode && centroid.sourceCount > 0) {
      tipHTML += `<br/><span style="opacity:0.5;font-style:italic">${t('belowStanceFloor')}</span>`;
    }
    layer.bindTooltip(tipHTML, { permanent: false, direction: 'top', className: 'map-tooltip' });

    layer.on({
      mouseover: (e: any) => {
        const map = e.target._map;
        map.eachLayer((l: any) => {
          if (!l.feature?.properties) return;
          let li = l.feature.properties['ISO3166-1-Alpha-2'];
          const ln = l.feature.properties.name;
          if (ln === 'France') li = 'FR';
          if (ln === 'Norway') li = 'NO';
          if (ln === 'Kosovo') li = 'XK';
          if (li === 'CN-TW') li = 'TW';
          if (centroid.allIsoCodes.includes(li)) l.setStyle({ fillColor: '#3b82f6', fillOpacity: 0.7 });
        });
      },
      mouseout: (e: any) => {
        const map = e.target._map;
        map.eachLayer((l: any) => {
          if (!l.feature?.properties) return;
          let li = l.feature.properties['ISO3166-1-Alpha-2'];
          const ln = l.feature.properties.name;
          if (ln === 'France') li = 'FR';
          if (ln === 'Norway') li = 'NO';
          if (ln === 'Kosovo') li = 'XK';
          if (li === 'CN-TW') li = 'TW';
          if (centroid.allIsoCodes.includes(li)) {
            if (stanceMode) {
              const s = stanceFill(centroid.stance, centroid.sourceCount, maxSourceCount);
              l.setStyle({ fillColor: s.fillColor, fillOpacity: s.fillOpacity });
            } else {
              l.setStyle({ fillColor: getHeatmapColor(centroid.sourceCount, maxSourceCount), fillOpacity: 0.6 });
            }
          }
        });
      },
      click: () => { if (!fnModeRef.current) router.push(`/c/${centroid.id}`); },
    });
  };

  const style = (feature: any) => {
    if (fnMode) {
      return { fillColor: '#243447', fillOpacity: 0.72, color: '#3d5166', weight: 0.6 };
    }

    let iso2 = feature.properties['ISO3166-1-Alpha-2'];
    const name = feature.properties.name;
    if (name === 'France') iso2 = 'FR';
    if (name === 'Norway') iso2 = 'NO';
    if (name === 'Kosovo') iso2 = 'XK';
    if (iso2 === 'CN-TW') iso2 = 'TW';

    const centroid = isoToCentroid.get(iso2);
    if (!centroid) return { fillColor: '#374151', fillOpacity: 0.2, color: '#1f2937', weight: 1 };

    if (stanceMode) {
      const { fillColor, fillOpacity } = stanceFill(centroid.stance, centroid.sourceCount, maxSourceCount);
      return { fillColor, fillOpacity, color: '#1f2937', weight: 1, cursor: 'pointer' };
    }

    return {
      fillColor: getHeatmapColor(centroid.sourceCount, maxSourceCount),
      fillOpacity: 0.6, color: '#1f2937', weight: 1, cursor: 'pointer',
    };
  };

  return (
    <div className="w-full h-[500px] rounded-lg overflow-hidden relative">
      {/* Coverage / stance legend (hidden in FN mode) */}
      {!fnMode && (
        stanceMode ? (
          <div className="absolute bottom-4 left-4 bg-dashboard-surface/90 backdrop-blur-sm border border-dashboard-border rounded-lg p-3 z-[1000]">
            <div className="text-xs font-semibold mb-2 text-dashboard-text">{t('stanceLegend')}</div>
            <div className="flex flex-col gap-1">
              {([['#b91c1c', `-2 ${t('stanceHostile')}`], ['#ef4444', `-1 ${t('stanceCritical')}`], ['#71717a', `0 ${t('stanceNeutral')}`], ['#10b981', `+1 ${t('stanceFavorable')}`], ['#15803d', `+2 ${t('stanceSupportive')}`]] as [string, string][]).map(([color, label]) => (
                <div key={color} className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded" style={{ backgroundColor: color }} />
                  <span className="text-xs text-dashboard-text-muted">{label}</span>
                </div>
              ))}
              <div className="flex items-center gap-2 mt-1 pt-1 border-t border-dashboard-border/60">
                <div className="w-4 h-4 rounded opacity-30" style={{ backgroundColor: '#71717a' }} />
                <span className="text-[10px] text-dashboard-text-muted/80 leading-tight">{t('belowStanceFloor')}</span>
              </div>
            </div>
            <div className="mt-2 pt-2 border-t border-dashboard-border/60 text-[10px] text-dashboard-text-muted/80 leading-tight max-w-[10rem]">
              {t('opacityNote')}
            </div>
          </div>
        ) : (
          <div className="absolute bottom-4 left-4 bg-dashboard-surface/90 backdrop-blur-sm border border-dashboard-border rounded-lg p-3 z-[1000]">
            <div className="text-xs font-semibold mb-2 text-dashboard-text">{t('coverageIntensity')}</div>
            <div className="flex flex-col gap-1">
              {([['#dc2626', t('veryHigh')], ['#f97316', t('high')], ['#f59e0b', t('medium')], ['#eab308', t('low')], ['#6b6b4a', t('minimal')]] as [string, string][]).map(([color, label]) => (
                <div key={color} className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded" style={{ backgroundColor: color }} />
                  <span className="text-xs text-dashboard-text-muted">{label}</span>
                </div>
              ))}
            </div>
          </div>
        )
      )}

      {/* FN mode: asset info panel (fixed right side) */}
      {fnMode && selected?.kind === 'asset' && (() => {
        const a = selected.asset;
        return (
        <div className={`absolute right-3 top-3 bottom-3 w-64 z-[1000] flex flex-col border rounded-lg overflow-hidden ${
          a.stress > 0
            ? 'bg-[#0a1220]/95 border-orange-500/30'
            : 'bg-[#0d0f14]/95 border-gray-600/30'
        }`}>
          <div className={`flex items-start justify-between p-4 pb-2 border-b ${
            a.stress > 0 ? 'border-orange-500/15' : 'border-gray-600/15'
          }`}>
            <div className="flex-1 pr-3">
              <div className={`font-semibold text-sm leading-snug ${
                a.stress > 0 ? 'text-orange-400' : 'text-gray-300'
              }`}>
                {a.name_en}
              </div>
              <div className="flex items-center gap-2 mt-1.5">
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 text-gray-400 border border-white/10 uppercase tracking-wider">
                  {a.asset_type.replace(/_/g, ' ')}
                </span>
                {a.stress > 0 && (
                  <div className="flex items-center gap-1" title="Pressure level">
                    {[1, 2, 3, 4, 5].map(pip => (
                      <div
                        key={pip}
                        className="w-1.5 h-1.5 rounded-full"
                        style={{
                          backgroundColor: a.stress * 5 >= pip
                            ? 'rgba(251,146,60,0.9)'
                            : 'rgba(251,146,60,0.15)',
                        }}
                      />
                    ))}
                  </div>
                )}
              </div>
            </div>
            <button
              onClick={() => setSelected(null)}
              className="text-gray-600 hover:text-gray-300 text-lg leading-none flex-shrink-0 mt-0.5"
              aria-label="Close"
            >
              &times;
            </button>
          </div>
          <div className="overflow-y-auto flex-1 p-4 space-y-4">
            {a.description_en && (
              <p className="text-xs text-gray-400 leading-relaxed">
                {a.description_en}
              </p>
            )}
            {a.commodities.length > 0 && (
              <div>
                <div className="text-[10px] uppercase tracking-wider text-gray-500 mb-2">
                  Commodities
                </div>
                <div className="flex flex-wrap gap-1">
                  {a.commodities.map(c => (
                    <span
                      key={c}
                      className="text-[10px] text-gray-300 bg-white/5 border border-white/10 rounded px-1.5 py-0.5 leading-none"
                    >
                      {c.replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              </div>
            )}
            <div>
              <div className="text-[10px] uppercase tracking-wider text-gray-500 mb-2">
                {a.fns.length ? 'Pressure from' : 'No active pressure'}
              </div>
              <div className="space-y-0.5">
                {a.fns.map(fn => (
                  <Link
                    key={fn.id}
                    href={`/friction-nodes/${fn.id}`}
                    className={`flex items-start gap-2 py-1.5 text-xs border-b border-white/5 last:border-0 leading-snug ${
                      fn.is_ghost
                        ? 'text-gray-500 hover:text-gray-300'
                        : 'text-gray-300 hover:text-orange-400'
                    }`}
                  >
                    <span className={`mt-0.5 flex-shrink-0 ${fn.is_ghost ? 'text-gray-600' : 'text-orange-500'}`}>
                      &#9654;
                    </span>
                    <span className="flex-1">
                      {fn.name_en}
                      <span className="block text-[10px] text-gray-600 mt-0.5">
                        {fn.is_ghost ? 'dormant' : `${fn.total_events.toLocaleString()} events`}
                      </span>
                    </span>
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </div>
        );
      })()}

      {/* FN mode: conflict info panel */}
      {fnMode && selected?.kind === 'conflict' && (() => {
        const c = selected.conflict;
        const pressured = fnData?.assets.filter(a => c.affected_asset_ids.includes(a.id)) ?? [];
        return (
        <div className={`absolute right-3 top-3 bottom-3 w-64 z-[1000] flex flex-col border rounded-lg overflow-hidden ${
          c.is_ghost ? 'bg-[#0d0f14]/95 border-gray-600/30' : 'bg-[#160a0a]/95 border-red-500/30'
        }`}>
          <div className={`flex items-start justify-between p-4 pb-2 border-b ${
            c.is_ghost ? 'border-gray-600/15' : 'border-red-500/15'
          }`}>
            <div className="flex-1 pr-3">
              <Link
                href={`/friction-nodes/${c.id}`}
                className={`font-semibold text-sm leading-snug ${
                  c.is_ghost ? 'text-gray-400 hover:text-gray-200' : 'text-red-400 hover:text-red-300'
                }`}
              >
                {c.name_en} &rarr;
              </Link>
              <div className="flex items-center gap-2 mt-1.5">
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 text-gray-400 border border-white/10 uppercase tracking-wider">
                  Conflict zone
                </span>
                {c.is_ghost ? (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-700/60 text-gray-400">
                    dormant
                  </span>
                ) : (
                  <div className="flex items-center gap-1" title={`${c.total_events.toLocaleString()} events tracked`}>
                    {[1, 2, 3, 4, 5].map(pip => (
                      <div
                        key={pip}
                        className="w-1.5 h-1.5 rounded-full"
                        style={{
                          backgroundColor: c.intensity * 5 >= pip
                            ? 'rgba(239,68,68,0.9)'
                            : 'rgba(239,68,68,0.15)',
                        }}
                      />
                    ))}
                  </div>
                )}
              </div>
            </div>
            <button
              onClick={() => setSelected(null)}
              className="text-gray-600 hover:text-gray-300 text-lg leading-none flex-shrink-0 mt-0.5"
              aria-label="Close"
            >
              &times;
            </button>
          </div>
          <div className="overflow-y-auto flex-1 p-4 space-y-4">
            <div className="text-xs text-gray-400">
              {c.is_ghost
                ? 'No tracked events in the last 90 days.'
                : `${c.total_events.toLocaleString()} events tracked.`}
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wider text-gray-500 mb-2">
                {pressured.length ? 'Assets under pressure' : 'No strategic assets linked'}
              </div>
              <div className="space-y-0.5">
                {pressured.map(a => (
                  <div key={a.id} className="flex items-start gap-2 py-1.5 text-xs border-b border-white/5 last:border-0 leading-snug text-gray-300">
                    <span className="mt-0.5 flex-shrink-0 text-orange-500">&#9670;</span>
                    <span className="flex-1">
                      {a.name_en}
                      <span className="block text-[10px] text-gray-600 mt-0.5">
                        {a.asset_type.replace(/_/g, ' ')}
                      </span>
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
        );
      })()}

      <MapContainer
        key="world-map"
        center={[20, 0]}
        zoom={2}
        minZoom={1.5}
        maxZoom={6}
        maxBounds={[[-85, -180], [85, 180]]}
        maxBoundsViscosity={0.5}
        style={{ height: '100%', width: '100%', background: '#0a0e1a' }}
        zoomControl={false}
        attributionControl={false}
      >
        <MapController />
        <GeoJSON
          key={`geojson-${fnMode ? 'fn' : 'normal'}`}
          data={geoData}
          style={style}
          onEachFeature={onEachFeature}
        />
        {fnMode && fnData && (
          <StrategicAssetLayer
            data={fnData}
            onSelect={setSelected}
            selectedId={
              selected?.kind === 'asset' ? selected.asset.id
              : selected?.kind === 'conflict' ? selected.conflict.id
              : null
            }
          />
        )}
      </MapContainer>
    </div>
  );
}
