'use client';

import { useEffect, useState, useRef } from 'react';
import { MapContainer, GeoJSON, useMap } from 'react-leaflet';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import Link from 'next/link';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import FrictionNodeLayer from './FrictionNodeLayer';

export interface FnMapData {
  theaters: Array<{
    id: string;
    name_en: string;
    intensity: number;
    is_ghost: boolean;
    last_active_date: string | null;
    total_events: number;
    atomicFNs: Array<{ id: string; name_en: string }>;
    countries: Array<{
      id: string;
      label: string;
      flag_iso2: string | null;
      lat: number | null;
      lon: number | null;
    }>;
    radialTargets: Array<{
      id: string;
      label: string;
      lat: number;
      lon: number;
    }>;
  }>;
}

type Theater = FnMapData['theaters'][0];

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
  fnData?: FnMapData | null;
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
  const [selectedTheater, setSelectedTheater] = useState<Theater | null>(null);
  const mapInitialized = useRef(false);
  const fnModeRef = useRef(fnMode);
  const router = useRouter();
  const t = useTranslations('map');

  useEffect(() => { fnModeRef.current = fnMode; }, [fnMode]);
  useEffect(() => { if (!fnMode) setSelectedTheater(null); }, [fnMode]);
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

      {/* FN mode: info panel (fixed right side) */}
      {fnMode && selectedTheater && (
        <div className={`absolute right-3 top-3 bottom-3 w-64 z-[1000] flex flex-col border rounded-lg overflow-hidden ${
          selectedTheater.is_ghost
            ? 'bg-[#0d0f14]/95 border-gray-600/30'
            : 'bg-[#0a1220]/95 border-orange-500/30'
        }`}>
          <div className={`flex items-start justify-between p-4 pb-2 border-b ${
            selectedTheater.is_ghost ? 'border-gray-600/15' : 'border-orange-500/15'
          }`}>
            <div className="flex-1 pr-3">
              <Link
                href={`/friction-nodes/${selectedTheater.id}`}
                className={`font-semibold text-sm leading-snug ${
                  selectedTheater.is_ghost
                    ? 'text-gray-400 hover:text-gray-200'
                    : 'text-orange-400 hover:text-orange-300'
                }`}
              >
                {selectedTheater.name_en} &rarr;
              </Link>
              <div className="flex items-center gap-2 mt-1.5">
                {selectedTheater.is_ghost ? (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-700/60 text-gray-400 border border-gray-600/40">
                    Dormant
                  </span>
                ) : (
                  <div className="flex items-center gap-1" title={`${selectedTheater.total_events} events tracked`}>
                    {[1, 2, 3, 4, 5].map(pip => (
                      <div
                        key={pip}
                        className="w-1.5 h-1.5 rounded-full"
                        style={{
                          backgroundColor: selectedTheater.intensity * 5 >= pip
                            ? 'rgba(251,146,60,0.9)'
                            : 'rgba(251,146,60,0.15)',
                        }}
                      />
                    ))}
                  </div>
                )}
                {selectedTheater.last_active_date && (
                  <span className="text-[10px] text-gray-600">
                    {new Date(selectedTheater.last_active_date).toLocaleDateString('en', { month: 'short', year: 'numeric' })}
                  </span>
                )}
              </div>
            </div>
            <button
              onClick={() => setSelectedTheater(null)}
              className="text-gray-600 hover:text-gray-300 text-lg leading-none flex-shrink-0 mt-0.5"
              aria-label="Close"
            >
              &times;
            </button>
          </div>
          <div className="overflow-y-auto flex-1 p-4 space-y-4">
            <div>
              <div className="text-[10px] uppercase tracking-wider text-gray-500 mb-2">
                Conflicts in this zone
              </div>
              <div className="space-y-0.5">
                {selectedTheater.atomicFNs.map(fn => (
                  <Link
                    key={fn.id}
                    href={`/friction-nodes/${fn.id}`}
                    className={`flex items-start gap-2 py-1.5 text-xs border-b border-white/5 last:border-0 leading-snug ${
                      selectedTheater.is_ghost
                        ? 'text-gray-500 hover:text-gray-300'
                        : 'text-gray-300 hover:text-orange-400'
                    }`}
                  >
                    <span className={`mt-0.5 flex-shrink-0 ${selectedTheater.is_ghost ? 'text-gray-600' : 'text-orange-500'}`}>
                      &#9654;
                    </span>
                    {fn.name_en}
                  </Link>
                ))}
              </div>
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wider text-gray-500 mb-2">
                Key actors
              </div>
              <div className="flex flex-wrap gap-1">
                {selectedTheater.countries.map(c => (
                  c.flag_iso2 ? (
                    // Flagged country: flag icon only with tooltip via title.
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      key={c.id}
                      src={`https://flagcdn.com/20x15/${c.flag_iso2.toLowerCase()}.png`}
                      width={20}
                      height={15}
                      alt={c.label}
                      title={c.label}
                      className="rounded-sm opacity-70 hover:opacity-100 transition-opacity"
                    />
                  ) : (
                    // Non-country centroid (EU, NATO, Levant…): compact text pill.
                    <span
                      key={c.id}
                      title={c.label}
                      className="text-[9px] text-gray-500 bg-white/5 rounded px-1 py-0.5 leading-none"
                    >
                      {c.label.slice(0, 3).toUpperCase()}
                    </span>
                  )
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

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
          <FrictionNodeLayer
            data={fnData}
            onSelect={setSelectedTheater}
            selectedTheaterId={selectedTheater?.id ?? null}
          />
        )}
      </MapContainer>
    </div>
  );
}
