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
  }>;
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

  const isoToCentroid = new Map<string, { id: string; label: string; allIsoCodes: string[] }>();
  const centroidRef = useRef<Map<string, { id: string; label: string; allIsoCodes: string[] }>>(new Map());

  centroids.forEach(c => {
    if (c.iso_codes) {
      const centroidData = { id: c.id, label: c.label, allIsoCodes: c.iso_codes };
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
          // Reset all countries in this centroid
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
                  fillColor: '#6b7280',
                  fillOpacity: 0.5,
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

    const hasCentroid = isoToCentroid.has(iso2);

    return {
      fillColor: hasCentroid ? '#6b7280' : '#374151',
      fillOpacity: hasCentroid ? 0.5 : 0.2,
      color: '#1f2937',
      weight: 1,
      cursor: hasCentroid ? 'pointer' : 'default',
    };
  };

  return (
    <div className="w-full h-[500px] rounded-lg overflow-hidden">
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
