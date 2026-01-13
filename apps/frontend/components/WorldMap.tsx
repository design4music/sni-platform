'use client';

import { useEffect, useState, useRef } from 'react';
import { MapContainer, GeoJSON, useMap } from 'react-leaflet';
import { useRouter } from 'next/navigation';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

interface WorldMapProps {
  centroids: Array<{
    id: string;
    label: string;
    iso_codes?: string[];
    article_count?: number;
  }>;
}

// Heatmap color function - uses logarithmic scale for better distribution
// All colors in warm tones (yellow to red) for cohesive look
function getHeatmapColor(articleCount: number, maxCount: number): string {
  if (articleCount === 0 || maxCount === 0) {
    return '#4a4a3a'; // very pale warm gray for no coverage
  }

  // Use log scale to compress the range and show more color variation
  // Adding 1 to avoid log(0)
  const logCount = Math.log10(articleCount + 1);
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

  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    if (!mapInitialized.current) {
      fetch('https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson')
        .then(res => res.json())
        .then(data => setGeoData(data));
      mapInitialized.current = true;
    }
  }, []);

  const isoToCentroid = new Map<string, { id: string; label: string; allIsoCodes: string[]; articleCount: number }>();
  const centroidRef = useRef<Map<string, { id: string; label: string; allIsoCodes: string[]; articleCount: number }>>(new Map());

  // Calculate max article count for heatmap scaling
  const maxArticleCount = Math.max(...centroids.map(c => c.article_count || 0), 1);

  centroids.forEach(c => {
    if (c.iso_codes) {
      const centroidData = {
        id: c.id,
        label: c.label,
        allIsoCodes: c.iso_codes,
        articleCount: c.article_count || 0
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
        <p className="text-dashboard-text-muted">Loading map...</p>
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
      layer.bindTooltip(centroid.label, {
        permanent: false,
        direction: 'center',
        className: 'custom-tooltip',
      });

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
                const heatmapColor = getHeatmapColor(centroid.articleCount, maxArticleCount);
                l.setStyle({
                  fillColor: heatmapColor,
                  fillOpacity: 0.6,
                });
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

    // Handle GeoJSON quirks (countries with -99 or wrong codes)
    if (name === 'France') iso2 = 'FR';
    if (name === 'Norway') iso2 = 'NO';
    if (name === 'Kosovo') iso2 = 'XK';
    if (iso2 === 'CN-TW') iso2 = 'TW';

    const centroid = isoToCentroid.get(iso2);
    const heatmapColor = centroid
      ? getHeatmapColor(centroid.articleCount, maxArticleCount)
      : '#374151';

    return {
      fillColor: heatmapColor,
      fillOpacity: centroid ? 0.6 : 0.2,
      color: '#1f2937',
      weight: 1,
      cursor: centroid ? 'pointer' : 'default',
    };
  };

  return (
    <div className="w-full h-[500px] rounded-lg overflow-hidden relative">
      {/* Heatmap Legend */}
      <div className="absolute bottom-4 left-4 bg-dashboard-surface/90 backdrop-blur-sm border border-dashboard-border rounded-lg p-3 z-[1000]">
        <div className="text-xs font-semibold mb-2 text-dashboard-text">Coverage Intensity</div>
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#dc2626' }}></div>
            <span className="text-xs text-dashboard-text-muted">Very High</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#f97316' }}></div>
            <span className="text-xs text-dashboard-text-muted">High</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#f59e0b' }}></div>
            <span className="text-xs text-dashboard-text-muted">Medium</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#eab308' }}></div>
            <span className="text-xs text-dashboard-text-muted">Low</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#6b6b4a' }}></div>
            <span className="text-xs text-dashboard-text-muted">Minimal</span>
          </div>
        </div>
      </div>
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
