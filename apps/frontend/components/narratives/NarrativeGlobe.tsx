'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { MapContainer, GeoJSON, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { normalizeIso } from '@/lib/narrative-map-utils';

interface NarrativeGlobeProps {
  /** ISO codes -> centroid ID lookup */
  isoToCentroidId: Record<string, string>;
  /** Centroid IDs of the selected actor */
  selectedIsos: Set<string>;
  /** Centroid IDs of targets/sources */
  highlightedIsos: Set<string>;
  /** Called when a country is clicked with its centroid ID */
  onCountryClick: (centroidId: string) => void;
  mode: 'outgoing' | 'incoming';
}

function MapController() {
  const map = useMap();
  useEffect(() => { map.invalidateSize(); }, [map]);
  return null;
}

const DEFAULT_COLOR = '#374151';
const SELECTED_COLOR = '#3b82f6';
const HIGHLIGHT_COLOR = '#f59e0b';

export default function NarrativeGlobe({
  isoToCentroidId,
  selectedIsos,
  highlightedIsos,
  onCountryClick,
  mode,
}: NarrativeGlobeProps) {
  const [geoData, setGeoData] = useState<GeoJSON.FeatureCollection | null>(null);
  const [isClient, setIsClient] = useState(false);
  const mapInitialized = useRef(false);
  const geoJsonRef = useRef<L.GeoJSON | null>(null);

  useEffect(() => { setIsClient(true); }, []);

  useEffect(() => {
    if (!mapInitialized.current) {
      fetch('/geo/countries.geojson')
        .then(res => res.json())
        .then(data => setGeoData(data));
      mapInitialized.current = true;
    }
  }, []);

  // Re-style layers when selection changes
  useEffect(() => {
    if (!geoJsonRef.current) return;
    geoJsonRef.current.eachLayer((layer: L.Layer) => {
      const geoLayer = layer as L.GeoJSON & { feature: GeoJSON.Feature };
      if (!geoLayer.feature) return;
      const iso = normalizeIso(geoLayer.feature as { properties: Record<string, string> });
      const style = getFeatureStyle(iso);
      (geoLayer as unknown as L.Path).setStyle(style);
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedIsos, highlightedIsos]);

  const getFeatureStyle = useCallback((iso: string): L.PathOptions => {
    if (selectedIsos.has(iso)) {
      return { fillColor: SELECTED_COLOR, fillOpacity: 0.7, color: '#1f2937', weight: 1 };
    }
    if (highlightedIsos.has(iso)) {
      return { fillColor: HIGHLIGHT_COLOR, fillOpacity: 0.6, color: '#1f2937', weight: 1 };
    }
    const hasCentroid = !!isoToCentroidId[iso];
    return {
      fillColor: DEFAULT_COLOR,
      fillOpacity: hasCentroid ? 0.4 : 0.2,
      color: '#1f2937',
      weight: 1,
    };
  }, [selectedIsos, highlightedIsos, isoToCentroidId]);

  const style = useCallback((feature: GeoJSON.Feature | undefined) => {
    if (!feature) return { fillColor: DEFAULT_COLOR, fillOpacity: 0.2, color: '#1f2937', weight: 1 };
    const iso = normalizeIso(feature as { properties: Record<string, string> });
    return getFeatureStyle(iso);
  }, [getFeatureStyle]);

  const onEachFeature = useCallback((feature: GeoJSON.Feature, layer: L.Layer) => {
    const iso = normalizeIso(feature as { properties: Record<string, string> });
    const centroidId = isoToCentroidId[iso];

    if (centroidId) {
      layer.on({
        mouseover: (e: L.LeafletMouseEvent) => {
          const path = e.target as L.Path;
          if (!selectedIsos.has(iso) && !highlightedIsos.has(iso)) {
            path.setStyle({ fillColor: '#6b7280', fillOpacity: 0.5 });
          }
        },
        mouseout: (e: L.LeafletMouseEvent) => {
          const path = e.target as L.Path;
          const s = getFeatureStyle(iso);
          path.setStyle(s);
        },
        click: () => {
          onCountryClick(centroidId);
        },
      });
    }
  }, [isoToCentroidId, selectedIsos, highlightedIsos, onCountryClick, getFeatureStyle]);

  if (!isClient || !geoData) {
    return (
      <div className="w-full h-full bg-dashboard-surface rounded-lg flex items-center justify-center">
        <p className="text-dashboard-text-muted">Loading map...</p>
      </div>
    );
  }

  return (
    <div className="w-full h-full rounded-lg overflow-hidden relative">
      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-dashboard-surface/90 backdrop-blur-sm border border-dashboard-border rounded-lg p-3 z-[1000]">
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: SELECTED_COLOR, opacity: 0.7 }} />
            <span className="text-xs text-dashboard-text-muted">Selected</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: HIGHLIGHT_COLOR, opacity: 0.6 }} />
            <span className="text-xs text-dashboard-text-muted">
              {mode === 'outgoing' ? 'Targets' : 'Sources'}
            </span>
          </div>
        </div>
      </div>

      <MapContainer
        key="narrative-globe"
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
          key={`geojson-${selectedIsos.size}-${highlightedIsos.size}`}
          ref={geoJsonRef as React.Ref<L.GeoJSON>}
          data={geoData}
          style={style}
          onEachFeature={onEachFeature}
        />
      </MapContainer>
    </div>
  );
}
