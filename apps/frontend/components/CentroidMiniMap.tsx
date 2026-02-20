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

// Extend bounds by ~500km in each direction.
// 1 degree latitude ~ 111km, so 500km ~ 4.5 degrees.
// Longitude degrees shrink with cos(lat), so we adjust.
function extendBounds(bounds: L.LatLngBounds, km: number): L.LatLngBounds {
  const degLat = km / 111;
  const centerLat = bounds.getCenter().lat;
  const degLng = km / (111 * Math.cos((centerLat * Math.PI) / 180));
  return L.latLngBounds(
    [bounds.getSouth() - degLat, bounds.getWest() - degLng],
    [bounds.getNorth() + degLat, bounds.getEast() + degLng]
  );
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
      const extended = extendBounds(group.getBounds(), 500);
      map.fitBounds(extended, { animate: false });
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
      <div className="w-full h-[200px] bg-dashboard-surface rounded-lg animate-pulse" />
    );
  }

  const isoSet = new Set(isoCodes.map(c => c.toUpperCase()));

  const style = (feature: any) => {
    const iso = normalizeIso(feature);
    const isTarget = iso && isoSet.has(iso);
    return {
      fillColor: isTarget ? '#3b82f6' : '#475569',
      fillOpacity: isTarget ? 0.65 : 0.35,
      color: isTarget ? '#60a5fa' : '#334155',
      weight: isTarget ? 1.5 : 0.5,
    };
  };

  return (
    <div className="w-full h-[200px] rounded-lg overflow-hidden border border-dashboard-border">
      <MapContainer
        center={[20, 0]}
        zoom={2}
        style={{ height: '100%', width: '100%', background: '#0f172a' }}
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
