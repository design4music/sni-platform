'use client';

import { useEffect, useRef } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import type { AssetMapData } from './WorldMap';
import { buildBadge, stressColor } from './assetIcons';

type Asset = AssetMapData['assets'][0];

interface Props {
  data: AssetMapData;
  onSelect: (asset: Asset | null) => void;
  selectedAssetId: string | null;
}

// ---------------------------------------------------------------------
// Geometry helpers. GeoJSON is [lon, lat]; Leaflet wants [lat, lon].
// ---------------------------------------------------------------------

function toLatLng(pos: number[]): [number, number] {
  return [pos[1], pos[0]];
}

// Pipelines and corridors render as lines; every other geometry collapses
// to an icon badge at its representative point (a strait is a place at
// world zoom, not a 40km line; a mining belt reads better as a glyph
// than a coarse polygon).
function isLinear(asset: Asset): boolean {
  return asset.asset_type === 'pipeline' || asset.asset_type === 'corridor';
}

function representativePoint(asset: Asset): [number, number] | null {
  const geom = asset.geometry as { type: string; coordinates: unknown };
  if (!geom?.type || !geom.coordinates) return null;
  switch (geom.type) {
    case 'Point':
      return toLatLng(geom.coordinates as number[]);
    case 'LineString': {
      const coords = geom.coordinates as number[][];
      return toLatLng(coords[Math.floor(coords.length / 2)]);
    }
    case 'Polygon': {
      const ring = (geom.coordinates as number[][][])[0];
      const pts = ring.slice(0, -1); // drop closing duplicate
      const lon = pts.reduce((s, p) => s + p[0], 0) / pts.length;
      const lat = pts.reduce((s, p) => s + p[1], 0) / pts.length;
      return [lat, lon];
    }
    default:
      return null;
  }
}

// Catmull-Rom spline through the waypoints — hand-placed pipeline routes
// come out as smooth curves instead of angular segments.
function smoothLine(pts: [number, number][], segments = 8): [number, number][] {
  if (pts.length < 3) return pts;
  const P = [pts[0], ...pts, pts[pts.length - 1]];
  const out: [number, number][] = [];
  for (let i = 0; i < P.length - 3; i++) {
    const [p0, p1, p2, p3] = [P[i], P[i + 1], P[i + 2], P[i + 3]];
    for (let t = 0; t < segments; t++) {
      const u = t / segments;
      const u2 = u * u;
      const u3 = u2 * u;
      out.push([
        0.5 * (2 * p1[0] + (-p0[0] + p2[0]) * u + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * u2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * u3),
        0.5 * (2 * p1[1] + (-p0[1] + p2[1]) * u + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * u2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * u3),
      ]);
    }
  }
  out.push(pts[pts.length - 1]);
  return out;
}

function lineStyle(asset: Asset, selected: boolean, hover = false): L.PathOptions {
  return {
    color: selected ? '#ffffff' : stressColor(asset.stress),
    weight: selected ? 4 : hover ? 3.5 : 2.5,
    opacity: selected ? 1 : hover ? 0.95 : asset.stress > 0 ? 0.85 : 0.45,
    dashArray: asset.stress > 0 || selected ? undefined : '5 7',
  };
}

// Declutter: the world view shows only what matters at that scale.
// Stressed assets and criticality-5 always; criticality 4 from zoom 3;
// the rest from zoom 4.
function minZoomFor(asset: Asset): number {
  if (asset.stress > 0 || asset.criticality >= 5) return 0;
  if (asset.criticality === 4) return 3;
  return 4;
}

function tooltipHtml(asset: Asset): string {
  const type = asset.asset_type.replace(/_/g, ' ');
  const pressure = asset.stress > 0 ? ' &middot; under pressure' : '';
  return `<strong>${asset.name_en}</strong><br/><span style="opacity:0.7">${type}${pressure}</span>`;
}

// ---------------------------------------------------------------------

export default function StrategicAssetLayer({ data, onSelect, selectedAssetId }: Props) {
  const map = useMap();
  const markersRef = useRef<Map<string, { marker: L.Marker; asset: Asset }>>(new Map());
  const linesRef = useRef<Map<string, { line: L.Polyline; asset: Asset }>>(new Map());
  const selectedRef = useRef<string | null>(selectedAssetId);
  const onSelectRef = useRef(onSelect);

  useEffect(() => { selectedRef.current = selectedAssetId; }, [selectedAssetId]);
  useEffect(() => { onSelectRef.current = onSelect; }, [onSelect]);

  // Restyle on selection change.
  useEffect(() => {
    for (const [id, { marker, asset }] of markersRef.current) {
      const { html, size } = buildBadge(asset, id === selectedAssetId);
      marker.setIcon(L.divIcon({ html, className: 'asset-marker', iconSize: [size, size], iconAnchor: [size / 2, size / 2] }));
    }
    for (const [id, { line, asset }] of linesRef.current) {
      line.setStyle(lineStyle(asset, id === selectedAssetId));
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

    for (const asset of data.assets) {
      if (isLinear(asset)) {
        const geom = asset.geometry as { type: string; coordinates: number[][] };
        if (geom?.type !== 'LineString') continue;
        const line = L.polyline(smoothLine(geom.coordinates.map(toLatLng)), {
          ...lineStyle(asset, false),
          interactive: true,
        });
        line.bindTooltip(tooltipHtml(asset), { direction: 'top', className: 'map-tooltip', sticky: true });
        line.on('mouseover', () => {
          if (asset.id !== selectedRef.current) line.setStyle(lineStyle(asset, false, true));
        });
        line.on('mouseout', () => {
          if (asset.id !== selectedRef.current) line.setStyle(lineStyle(asset, false));
        });
        line.on('click', () => {
          justClicked = true;
          onSelectRef.current(asset);
        });
        line.addTo(map);
        allLayers.push(line);
        linesRef.current.set(asset.id, { line, asset });
        continue;
      }

      const pos = representativePoint(asset);
      if (!pos) continue;

      const { html, size } = buildBadge(asset, false);
      const marker = L.marker(pos, {
        icon: L.divIcon({ html, className: 'asset-marker', iconSize: [size, size], iconAnchor: [size / 2, size / 2] }),
        interactive: true,
      });
      marker.bindTooltip(tooltipHtml(asset), { direction: 'top', className: 'map-tooltip' });
      marker.on('mouseover', () => {
        const badge = marker.getElement()?.firstElementChild as HTMLElement | null;
        if (badge) badge.style.transform = 'scale(1.2)';
      });
      marker.on('mouseout', () => {
        const badge = marker.getElement()?.firstElementChild as HTMLElement | null;
        if (badge) badge.style.transform = '';
      });
      marker.on('click', () => {
        justClicked = true;
        onSelectRef.current(asset);
      });
      markersRef.current.set(asset.id, { marker, asset });
      allLayers.push(marker);
    }

    // Zoom-dependent visibility for markers (lines are few; always shown).
    const applyZoomFilter = () => {
      const zoom = map.getZoom();
      for (const { marker, asset } of markersRef.current.values()) {
        const visible = zoom >= minZoomFor(asset);
        const onMap = map.hasLayer(marker);
        if (visible && !onMap) marker.addTo(map);
        if (!visible && onMap) map.removeLayer(marker);
      }
    };
    applyZoomFilter();
    map.on('zoomend', applyZoomFilter);

    return () => {
      map.off('click', mapClickHandler);
      map.off('zoomend', applyZoomFilter);
      allLayers.forEach(l => { try { map.removeLayer(l); } catch { /* gone */ } });
      markersRef.current.clear();
      linesRef.current.clear();
    };
  }, [map, data]);

  return null;
}
