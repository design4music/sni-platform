'use client';

import { useEffect, useState, useRef } from 'react';
import { MapContainer, GeoJSON, useMap } from 'react-leaflet';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

interface WorldMapProps {
  centroids: Array<{
    id: string;
    label: string;
    iso_codes?: string[];
    source_count?: number;
    /** Optional stance overlay: when ANY centroid in the array has a
     *  `stance` field present (even null), the map switches to stance
     *  mode — country hue tracks editorial stance, opacity tracks
     *  coverage volume. Used by /sources/[slug]/[month]. */
    stance?: number | null;
    tone?: string | null;
    confidence?: 'low' | 'medium' | 'high' | null;
    n_headlines?: number;
  }>;
}

// Heatmap color function - uses logarithmic scale for better distribution
// All colors in warm tones (yellow to red) for cohesive look
function getHeatmapColor(sourceCount: number, maxCount: number): string {
  if (sourceCount === 0 || maxCount === 0) {
    return '#4a4a3a'; // very pale warm gray for no coverage
  }

  // Use log scale to compress the range and show more color variation
  // Adding 1 to avoid log(0)
  const logCount = Math.log10(sourceCount + 1);
  const logMax = Math.log10(maxCount + 1);
  const intensity = logCount / logMax;

  if (intensity < 0.2) {
    return '#6b6b4a'; // pale warm brown - minimal (1-10 articles)
  } else if (intensity < 0.4) {
    return '#eab308'; // yellow - low (10-50 articles)
  } else if (intensity < 0.6) {
    return '#f59e0b'; // orange - medium (50-200 articles)
  } else if (intensity < 0.8) {
    return '#f97316'; // dark orange - high (200-500 articles)
  } else {
    return '#dc2626'; // red - very high (500+ articles)
  }
}

// Stance-mode colour: hue from stance (-2..+2), opacity from log(coverage).
// Returns CSS values to drop into a Leaflet style block.
function stanceFill(
  stance: number | null | undefined,
  sourceCount: number,
  maxCount: number,
): { fillColor: string; fillOpacity: number } {
  // Hue: red gradient for negative, neutral grey for 0/null, emerald for positive.
  let hue = '#71717a'; // zinc-500: neutral / no stance signal
  if (stance != null) {
    if (stance <= -2) hue = '#b91c1c';      // red-700
    else if (stance === -1) hue = '#ef4444'; // red-500
    else if (stance === 0) hue = '#71717a';  // zinc-500
    else if (stance === 1) hue = '#10b981';  // emerald-500
    else if (stance >= 2) hue = '#15803d';   // emerald-700
  }
  // Opacity: log scale on coverage, floored so the stance hue stays visible
  // even on lightly-covered countries.
  if (sourceCount === 0 || maxCount === 0) {
    return { fillColor: hue, fillOpacity: 0.15 };
  }
  const logCount = Math.log10(sourceCount + 1);
  const logMax = Math.log10(maxCount + 1);
  const t = logCount / logMax; // 0..1
  // Map [0..1] to [0.30..0.85] so even tiny coverage stays readable.
  const fillOpacity = 0.3 + 0.55 * t;
  return { fillColor: hue, fillOpacity };
}

function MapController() {
  const map = useMap();
  useEffect(() => {
    map.invalidateSize();
  }, [map]);
  return null;
}

export default function WorldMap({ centroids }: WorldMapProps) {
  const [geoData, setGeoData] = useState<any>(null);
  const [isClient, setIsClient] = useState(false);
  const mapInitialized = useRef(false);
  const router = useRouter();
  const t = useTranslations('map');

  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    if (!mapInitialized.current) {
      fetch('/geo/countries.geojson')
        .then(res => res.json())
        .then(data => setGeoData(data));
      mapInitialized.current = true;
    }
  }, []);

  // Stance mode kicks in when ANY centroid carries an explicit `stance`
  // field (even null). Outlet pages use this; centroid-page mini-maps
  // don't pass stance, so they keep the legacy heatmap colour scheme.
  const stanceMode = centroids.some(c => 'stance' in c);

  type CentroidEntry = {
    id: string;
    label: string;
    allIsoCodes: string[];
    sourceCount: number;
    stance: number | null | undefined;
    tone: string | null | undefined;
    confidence: 'low' | 'medium' | 'high' | null | undefined;
  };
  const isoToCentroid = new Map<string, CentroidEntry>();
  const centroidRef = useRef<Map<string, CentroidEntry>>(new Map());

  const maxSourceCount = Math.max(...centroids.map(c => c.source_count || 0), 1);

  centroids.forEach(c => {
    if (c.iso_codes) {
      const centroidData: CentroidEntry = {
        id: c.id,
        label: c.label,
        allIsoCodes: c.iso_codes,
        sourceCount: c.source_count || 0,
        stance: c.stance,
        tone: c.tone,
        confidence: c.confidence,
      };
      c.iso_codes.forEach(iso => {
        isoToCentroid.set(iso.toUpperCase(), centroidData);
      });
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
    let iso2 = feature.properties['ISO3166-1-Alpha-2'];
    const name = feature.properties.name;

    // Handle GeoJSON quirks (countries with -99 or wrong codes)
    if (name === 'France') iso2 = 'FR';
    if (name === 'Norway') iso2 = 'NO';
    if (name === 'Kosovo') iso2 = 'XK';
    if (iso2 === 'CN-TW') iso2 = 'TW';

    const centroid = isoToCentroid.get(iso2);

    if (centroid) {
      // Stance-aware tooltip: includes stance score + tone phrase when
      // available; otherwise just article count.
      let tipHTML = `<strong>${centroid.label}</strong><br/><span style="opacity:0.7">${centroid.sourceCount.toLocaleString()} ${t('articles')}</span>`;
      if (stanceMode && centroid.stance != null) {
        const sign = centroid.stance > 0 ? `+${centroid.stance}` : `${centroid.stance}`;
        tipHTML += `<br/><span style="opacity:0.85">stance: ${sign}`;
        if (centroid.confidence) tipHTML += ` (${centroid.confidence})`;
        tipHTML += `</span>`;
        if (centroid.tone) {
          tipHTML += `<br/><span style="opacity:0.65;font-style:italic">${centroid.tone}</span>`;
        }
      } else if (stanceMode && centroid.sourceCount > 0) {
        tipHTML += `<br/><span style="opacity:0.5;font-style:italic">${t('belowStanceFloor')}</span>`;
      }
      layer.bindTooltip(tipHTML, { permanent: false, direction: 'top', className: 'map-tooltip' });

      layer.on({
        mouseover: (e: any) => {
          // Highlight all countries in this centroid
          const map = e.target._map;
          map.eachLayer((l: any) => {
            if (l.feature && l.feature.properties) {
              let layerIso = l.feature.properties['ISO3166-1-Alpha-2'];
              const layerName = l.feature.properties.name;

              // Apply same normalization
              if (layerName === 'France') layerIso = 'FR';
              if (layerName === 'Norway') layerIso = 'NO';
              if (layerName === 'Kosovo') layerIso = 'XK';
              if (layerIso === 'CN-TW') layerIso = 'TW';

              if (centroid.allIsoCodes.includes(layerIso)) {
                l.setStyle({
                  fillColor: '#3b82f6',
                  fillOpacity: 0.7,
                });
              }
            }
          });
        },
        mouseout: (e: any) => {
          // Reset all countries in this centroid to heatmap color
          const map = e.target._map;
          map.eachLayer((l: any) => {
            if (l.feature && l.feature.properties) {
              let layerIso = l.feature.properties['ISO3166-1-Alpha-2'];
              const layerName = l.feature.properties.name;

              // Apply same normalization
              if (layerName === 'France') layerIso = 'FR';
              if (layerName === 'Norway') layerIso = 'NO';
              if (layerName === 'Kosovo') layerIso = 'XK';
              if (layerIso === 'CN-TW') layerIso = 'TW';

              if (centroid.allIsoCodes.includes(layerIso)) {
                if (stanceMode) {
                  const s = stanceFill(centroid.stance, centroid.sourceCount, maxSourceCount);
                  l.setStyle({ fillColor: s.fillColor, fillOpacity: s.fillOpacity });
                } else {
                  l.setStyle({
                    fillColor: getHeatmapColor(centroid.sourceCount, maxSourceCount),
                    fillOpacity: 0.6,
                  });
                }
              }
            }
          });
        },
        click: () => {
          router.push(`/c/${centroid.id}`);
        },
      });
    }
  };

  const style = (feature: any) => {
    let iso2 = feature.properties['ISO3166-1-Alpha-2'];
    const name = feature.properties.name;

    if (name === 'France') iso2 = 'FR';
    if (name === 'Norway') iso2 = 'NO';
    if (name === 'Kosovo') iso2 = 'XK';
    if (iso2 === 'CN-TW') iso2 = 'TW';

    const centroid = isoToCentroid.get(iso2);

    if (!centroid) {
      return {
        fillColor: '#374151',
        fillOpacity: 0.2,
        color: '#1f2937',
        weight: 1,
        cursor: 'default',
      };
    }

    if (stanceMode) {
      const { fillColor, fillOpacity } = stanceFill(
        centroid.stance,
        centroid.sourceCount,
        maxSourceCount,
      );
      return {
        fillColor,
        fillOpacity,
        color: '#1f2937',
        weight: 1,
        cursor: 'pointer',
      };
    }

    return {
      fillColor: getHeatmapColor(centroid.sourceCount, maxSourceCount),
      fillOpacity: 0.6,
      color: '#1f2937',
      weight: 1,
      cursor: 'pointer',
    };
  };

  return (
    <div className="w-full h-[500px] rounded-lg overflow-hidden relative">
      {/* Legend: stance scale in stance mode, coverage intensity otherwise. */}
      {stanceMode ? (
        <div className="absolute bottom-4 left-4 bg-dashboard-surface/90 backdrop-blur-sm border border-dashboard-border rounded-lg p-3 z-[1000]">
          <div className="text-xs font-semibold mb-2 text-dashboard-text">{t('stanceLegend')}</div>
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded" style={{ backgroundColor: '#b91c1c' }}></div>
              <span className="text-xs text-dashboard-text-muted">−2 {t('stanceHostile')}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded" style={{ backgroundColor: '#ef4444' }}></div>
              <span className="text-xs text-dashboard-text-muted">−1 {t('stanceCritical')}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded" style={{ backgroundColor: '#71717a' }}></div>
              <span className="text-xs text-dashboard-text-muted">0 {t('stanceNeutral')}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded" style={{ backgroundColor: '#10b981' }}></div>
              <span className="text-xs text-dashboard-text-muted">+1 {t('stanceFavorable')}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded" style={{ backgroundColor: '#15803d' }}></div>
              <span className="text-xs text-dashboard-text-muted">+2 {t('stanceSupportive')}</span>
            </div>
            <div className="flex items-center gap-2 mt-1 pt-1 border-t border-dashboard-border/60">
              <div className="w-4 h-4 rounded opacity-30" style={{ backgroundColor: '#71717a' }}></div>
              <span className="text-[10px] text-dashboard-text-muted/80 leading-tight">
                {t('belowStanceFloor')}
              </span>
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
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded" style={{ backgroundColor: '#dc2626' }}></div>
              <span className="text-xs text-dashboard-text-muted">{t('veryHigh')}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded" style={{ backgroundColor: '#f97316' }}></div>
              <span className="text-xs text-dashboard-text-muted">{t('high')}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded" style={{ backgroundColor: '#f59e0b' }}></div>
              <span className="text-xs text-dashboard-text-muted">{t('medium')}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded" style={{ backgroundColor: '#eab308' }}></div>
              <span className="text-xs text-dashboard-text-muted">{t('low')}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded" style={{ backgroundColor: '#6b6b4a' }}></div>
              <span className="text-xs text-dashboard-text-muted">{t('minimal')}</span>
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
        <GeoJSON key="geojson" data={geoData} style={style} onEachFeature={onEachFeature} />
      </MapContainer>
    </div>
  );
}
