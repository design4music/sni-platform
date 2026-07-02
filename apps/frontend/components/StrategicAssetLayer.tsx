'use client';

import { useEffect, useRef } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import type { AssetMapData } from './WorldMap';

type Asset = AssetMapData['assets'][0];

interface Props {
  data: AssetMapData;
  onSelect: (asset: Asset | null) => void;
  selectedAssetId: string | null;
}

// Stress → color. Calm assets stay visible but quiet (slate); stress moves
// through amber to red. Bands, not gradients — legibility over precision.
function stressColor(stress: number): string {
  if (stress <= 0)   return 'rgba(148,163,184,0.55)'; // slate — calm
  if (stress < 0.35) return '#f59e0b';                // amber
  if (stress < 0.65) return '#f97316';                // orange
  return '#dc2626';                                   // red
}

function stressFillOpacity(stress: number): number {
  return stress <= 0 ? 0.06 : 0.10 + 0.18 * stress;
}

// Point markers scale slightly with criticality (1-5 → 4-8px).
function pointRadius(criticality: number): number {
  return 3 + criticality;
}

const SELECTED_RING = '#ffffff';

// GeoJSON is [lon, lat]; Leaflet wants [lat, lon].
function toLatLng(pos: number[]): [number, number] {
  return [pos[1], pos[0]];
}

function buildLayer(asset: Asset): L.Path | null {
  const geom = asset.geometry as { type: string; coordinates: unknown };
  if (!geom?.type || !geom.coordinates) return null;

  switch (geom.type) {
    case 'Point':
      return L.circleMarker(toLatLng(geom.coordinates as number[]), {
        radius: pointRadius(asset.criticality),
        interactive: true,
      });
    case 'LineString':
      return L.polyline((geom.coordinates as number[][]).map(toLatLng), {
        interactive: true,
      });
    case 'Polygon':
      return L.polygon(
        (geom.coordinates as number[][][]).map(ring => ring.map(toLatLng)),
        { interactive: true },
      );
    default:
      return null;
  }
}

function styleFor(asset: Asset, selected: boolean, hover = false): L.PathOptions {
  const color = selected ? SELECTED_RING : stressColor(asset.stress);
  const geomType = (asset.geometry as { type?: string })?.type;

  if (geomType === 'LineString') {
    return {
      color,
      weight: selected ? 4 : hover ? 3.5 : 2.5,
      opacity: selected ? 1 : hover ? 0.95 : asset.stress > 0 ? 0.85 : 0.5,
      dashArray: asset.stress > 0 ? undefined : '5 6',
    };
  }
  if (geomType === 'Polygon') {
    return {
      color,
      weight: selected ? 2.5 : 1.5,
      opacity: selected ? 1 : asset.stress > 0 ? 0.8 : 0.45,
      fillColor: stressColor(asset.stress),
      fillOpacity: selected ? 0.3 : hover ? 0.22 : stressFillOpacity(asset.stress),
    };
  }
  // Point
  return {
    color,
    weight: selected ? 3 : 1.5,
    opacity: 1,
    fillColor: stressColor(asset.stress),
    fillOpacity: selected ? 0.95 : hover ? 0.9 : asset.stress > 0 ? 0.8 : 0.45,
  };
}

export default function StrategicAssetLayer({ data, onSelect, selectedAssetId }: Props) {
  const map = useMap();
  const layersRef = useRef<Map<string, { layer: L.Path; asset: Asset }>>(new Map());
  const selectedRef = useRef<string | null>(selectedAssetId);
  const onSelectRef = useRef(onSelect);

  useEffect(() => { selectedRef.current = selectedAssetId; }, [selectedAssetId]);
  useEffect(() => { onSelectRef.current = onSelect; }, [onSelect]);

  // Restyle on selection change.
  useEffect(() => {
    for (const [id, { layer, asset }] of layersRef.current) {
      layer.setStyle(styleFor(asset, id === selectedAssetId));
    }
  }, [selectedAssetId]);

  useEffect(() => {
    const allLayers: L.Layer[] = [];

    // Suppress the map click Leaflet propagates after a layer click.
    let justClicked = false;
    const mapClickHandler = () => {
      if (!justClicked) onSelectRef.current(null);
      justClicked = false;
    };
    map.on('click', mapClickHandler);

    // Lines/polygons first, points last so port markers stay clickable
    // on top of overlapping cluster polygons.
    const ordered = [...data.assets].sort((a, b) => {
      const rank = (g: unknown) => ((g as { type?: string })?.type === 'Point' ? 1 : 0);
      return rank(a.geometry) - rank(b.geometry);
    });

    for (const asset of ordered) {
      const layer = buildLayer(asset);
      if (!layer) continue;

      layer.setStyle(styleFor(asset, false));
      layer.bindTooltip(
        `<strong>${asset.name_en}</strong><br/><span style="opacity:0.7">${asset.asset_type.replace(/_/g, ' ')}${asset.stress > 0 ? ' &middot; under pressure' : ''}</span>`,
        { direction: 'top', className: 'map-tooltip', sticky: true },
      );

      layer.on('mouseover', () => {
        if (asset.id !== selectedRef.current) layer.setStyle(styleFor(asset, false, true));
      });
      layer.on('mouseout', () => {
        if (asset.id !== selectedRef.current) layer.setStyle(styleFor(asset, false));
      });
      layer.on('click', () => {
        justClicked = true;
        onSelectRef.current(asset);
      });

      layer.addTo(map);
      allLayers.push(layer);
      layersRef.current.set(asset.id, { layer, asset });
    }

    return () => {
      map.off('click', mapClickHandler);
      allLayers.forEach(l => { try { map.removeLayer(l); } catch { /* gone */ } });
      layersRef.current.clear();
    };
  }, [map, data]);

  return null;
}
