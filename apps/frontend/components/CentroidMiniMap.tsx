'use client';

import { useEffect, useState } from 'react';
import { MapContainer, GeoJSON, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

interface Props {
  isoCodes: string[];
}

function normalizeIso(feature: any): string | null {
  let iso = feature.properties['ISO3166-1-Alpha-2'];
  const name = feature.properties.name;
  if (name === 'France') iso = 'FR';
  if (name === 'Norway') iso = 'NO';
  if (name === 'Kosovo') iso = 'XK';
  if (iso === 'CN-TW') iso = 'TW';
  return iso || null;
}

function FitBounds({ isoCodes, geoData }: { isoCodes: string[]; geoData: any }) {
  const map = useMap();
  useEffect(() => {
    const isoSet = new Set(isoCodes.map(c => c.toUpperCase()));
    const matching = geoData.features.filter((f: any) => {
      const iso = normalizeIso(f);
      return iso && isoSet.has(iso);
    });
    if (matching.length > 0) {
      const group = L.geoJSON({ type: 'FeatureCollection', features: matching } as any);
      map.fitBounds(group.getBounds().pad(0.5), { animate: false });
    }
  }, [map, isoCodes, geoData]);
  return null;
}

export default function CentroidMiniMap({ isoCodes }: Props) {
  const [geoData, setGeoData] = useState<any>(null);

  useEffect(() => {
    fetch('/geo/countries.geojson')
      .then(res => res.json())
      .then(data => setGeoData(data));
  }, []);

  if (!geoData) {
    return (
      <div className="w-full h-[180px] bg-dashboard-surface rounded-lg animate-pulse" />
    );
  }

  const isoSet = new Set(isoCodes.map(c => c.toUpperCase()));

  const style = (feature: any) => {
    const iso = normalizeIso(feature);
    const isTarget = iso && isoSet.has(iso);
    return {
      fillColor: isTarget ? '#3b82f6' : '#374151',
      fillOpacity: isTarget ? 0.7 : 0.15,
      color: '#1f2937',
      weight: 0.5,
    };
  };

  return (
    <div className="w-full h-[180px] rounded-lg overflow-hidden">
      <MapContainer
        center={[20, 0]}
        zoom={2}
        style={{ height: '100%', width: '100%', background: '#0a0e1a' }}
        zoomControl={false}
        attributionControl={false}
        dragging={false}
        scrollWheelZoom={false}
        doubleClickZoom={false}
        touchZoom={false}
        keyboard={false}
      >
        <FitBounds isoCodes={isoCodes} geoData={geoData} />
        <GeoJSON data={geoData} style={style} />
      </MapContainer>
    </div>
  );
}
