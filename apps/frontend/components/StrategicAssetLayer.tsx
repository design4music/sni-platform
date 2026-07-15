'use client';

import { useEffect, useRef } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import type { AssetMapData, MapSelection } from './WorldMap';
import { buildDot, buildConflictBadge, assetTooltipHtml, categoryFor } from './assetIcons';

type Asset = AssetMapData['assets'][0];
type Conflict = AssetMapData['conflicts'][0];
type Competition = AssetMapData['competitions'][0];
type Flow = AssetMapData['flows'][0];

interface Props {
  data: AssetMapData;
  onSelect: (selection: MapSelection | null) => void;
  selectedId: string | null;
  hiddenCategories: string[];
  showRoutes: boolean;
  showPipelines: boolean;
}

// GeoJSON is [lon, lat]; Leaflet wants [lat, lon].
function toLatLng(pos: number[]): [number, number] {
  return [pos[1], pos[0]];
}

function isLinear(asset: Asset): boolean {
  return asset.asset_type === 'corridor' || asset.asset_type === 'pipeline';
}

// Line styling: sea corridors in the centroid-border tone (reads against
// the dark ocean); pipelines in white (distinct from landmass, borders,
// and trade routes when crossing water). Red when pressed.
const CORRIDOR_CALM = '#3d5166';
const PIPELINE_CALM = 'rgba(226,232,240,0.75)';
const LINE_PRESSED = '#ef4444';

function routeStyle(assetType: string, pressed: boolean, hover = false): L.PathOptions {
  const calm = assetType === 'pipeline' ? PIPELINE_CALM : CORRIDOR_CALM;
  return {
    color: pressed ? LINE_PRESSED : calm,
    weight: pressed ? 2.8 : hover ? 2.2 : 1.1,
    opacity: pressed ? 1 : hover ? 1 : 0.85,
  };
}

// Every point-like asset collapses to a dot at its representative point.
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
      const pts = ring.slice(0, -1);
      const lon = pts.reduce((s, p) => s + p[0], 0) / pts.length;
      const lat = pts.reduce((s, p) => s + p[1], 0) / pts.length;
      return [lat, lon];
    }
    default:
      return null;
  }
}

// Declutter: co-located assets (Benelux port cluster, Gulf terminals) get
// spread on a small ring so dots never fully stack.
function declutter(assets: Asset[]): Map<string, [number, number]> {
  const CELL = 1.1; // degrees
  const cells = new Map<string, Array<{ id: string; pos: [number, number] }>>();
  for (const a of assets) {
    const pos = representativePoint(a);
    if (!pos) continue;
    const key = `${Math.round(pos[0] / CELL)}:${Math.round(pos[1] / CELL)}`;
    if (!cells.has(key)) cells.set(key, []);
    cells.get(key)!.push({ id: a.id, pos });
  }
  const out = new Map<string, [number, number]>();
  for (const members of cells.values()) {
    if (members.length === 1) {
      out.set(members[0].id, members[0].pos);
      continue;
    }
    const cLat = members.reduce((s, m) => s + m.pos[0], 0) / members.length;
    const cLon = members.reduce((s, m) => s + m.pos[1], 0) / members.length;
    const r = 0.55;
    members.forEach((m, i) => {
      const angle = (2 * Math.PI * i) / members.length;
      out.set(m.id, [cLat + r * Math.sin(angle), cLon + r * Math.cos(angle)]);
    });
  }
  return out;
}

// Quadratic arc between two capitals ([lat, lon]), bowed toward the pole.
function arcPoints(a: [number, number], b: [number, number], steps = 40): [number, number][] {
  const dist = Math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2);
  const ctrl: [number, number] = [(a[0] + b[0]) / 2 + dist * 0.22, (a[1] + b[1]) / 2];
  const out: [number, number][] = [];
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const s = 1 - t;
    out.push([
      s * s * a[0] + 2 * s * t * ctrl[0] + t * t * b[0],
      s * s * a[1] + 2 * s * t * ctrl[1] + t * t * b[1],
    ]);
  }
  return out;
}

function divIconFor(html: string, size: number): L.DivIcon {
  return L.divIcon({ html, className: 'asset-marker', iconSize: [size, size], iconAnchor: [size / 2, size / 2] });
}

// Supply-flow styling: amber (informational), suspended flows gray dashed.
function flowStyle(f: Flow): L.PathOptions {
  if (f.status !== 'active') {
    return { color: 'rgba(148,163,184,0.65)', weight: 1.4, dashArray: '4 6', opacity: 1, interactive: true };
  }
  return {
    color: '#f59e0b',
    weight: f.magnitude_class === 'major' ? 2.2 : 1.3,
    opacity: f.magnitude_class === 'major' ? 0.9 : 0.7,
    interactive: true,
  };
}

// A route is pressed by the selected FN if the FN lists it directly OR
// presses any chokepoint the route transits (via_asset_ids).
function isPressed(asset: Asset, affected: Set<string>): boolean {
  if (affected.has(asset.id)) return true;
  return asset.via_asset_ids.some(id => affected.has(id));
}

export default function StrategicAssetLayer({
  data, onSelect, selectedId, hiddenCategories, showRoutes, showPipelines,
}: Props) {
  const map = useMap();
  const dotsRef = useRef<Map<string, { marker: L.Marker; asset: Asset }>>(new Map());
  // Dateline-crossing routes render as two shifted copies, hence lines[].
  const linesRef = useRef<Map<string, { lines: L.Polyline[]; asset: Asset }>>(new Map());
  const conflictsRef = useRef<Map<string, { marker: L.Marker; conflict: Conflict }>>(new Map());
  const competitionsRef = useRef<Map<string, Competition>>(new Map());
  const flowsRef = useRef<Flow[]>([]);
  const assetNameRef = useRef<Map<string, string>>(new Map());
  const overlayRef = useRef<L.LayerGroup | null>(null); // selection spokes / arcs
  const affectedRef = useRef<Set<string>>(new Set()); // assets pressed by current selection
  const selectedRef = useRef<string | null>(selectedId);
  const onSelectRef = useRef(onSelect);

  useEffect(() => { selectedRef.current = selectedId; }, [selectedId]);
  useEffect(() => { onSelectRef.current = onSelect; }, [onSelect]);

  const hiddenKey = [...hiddenCategories].sort().join(',');

  // Selection change: restyle markers, light up pressed assets/routes, and
  // draw connector lines to capitals. Connectors exist only while selected.
  useEffect(() => {
    const selConflict = selectedId ? conflictsRef.current.get(selectedId)?.conflict : undefined;
    const selCompetition = selectedId ? competitionsRef.current.get(selectedId) : undefined;
    const affected = new Set(selConflict?.affected_asset_ids ?? selCompetition?.affected_asset_ids ?? []);
    affectedRef.current = affected;

    for (const [id, { marker, asset }] of dotsRef.current) {
      const pressed = affected.size > 0 && isPressed(asset, affected);
      const { html, size } = buildDot(asset, pressed);
      marker.setIcon(divIconFor(html, size));
      marker.setZIndexOffset(pressed ? 400 : 0);
    }
    for (const [, { lines, asset }] of linesRef.current) {
      const style = routeStyle(asset.asset_type, affected.size > 0 && isPressed(asset, affected));
      for (const line of lines) line.setStyle(style);
    }
    for (const [id, { marker, conflict }] of conflictsRef.current) {
      const { html, size } = buildConflictBadge(conflict, id === selectedId);
      marker.setIcon(divIconFor(html, size));
    }

    overlayRef.current?.remove();
    overlayRef.current = null;

    const group = L.layerGroup();
    let hasOverlay = false;

    if (selConflict?.participants.length) {
      const anchor = selConflict.anchor as { type: string; coordinates: number[] };
      if (anchor?.type === 'Point') {
        const from = toLatLng(anchor.coordinates);
        const spokeColor = selConflict.is_ghost ? 'rgba(148,163,184,0.5)' : 'rgba(239,68,68,0.55)';
        for (const p of selConflict.participants) {
          L.polyline([from, [p.lat, p.lon]], { color: spokeColor, weight: 1.2, dashArray: '3 6', interactive: false })
            .addTo(group);
          L.circleMarker([p.lat, p.lon], { radius: 3, color: '#e2e8f0', fillColor: '#e2e8f0', fillOpacity: 0.9, weight: 0 })
            .bindTooltip(p.label, { direction: 'top', className: 'map-tooltip' })
            .addTo(group);
        }
        hasOverlay = true;
      }
    }

    // Supply flows: when an asset is selected, draw every flow that starts
    // here, ends here, or transits here. Selecting Hormuz answers "what
    // dies if this closes"; selecting Jamnagar shows where its crude
    // comes from and where its products go.
    if (selectedId && !selConflict && !selCompetition) {
      const touching = flowsRef.current.filter(f =>
        f.from_asset === selectedId || f.to_asset === selectedId || f.via_asset_ids.includes(selectedId),
      );
      for (const f of touching) {
        const geom = f.geometry as { type: string; coordinates: number[][] };
        if (geom?.type !== 'LineString') continue;
        const nameOf = (id: string) => assetNameRef.current.get(id) ?? id;
        const line = L.polyline(geom.coordinates.map(toLatLng), flowStyle(f));
        line.bindTooltip(
          `<strong>${f.commodity.replace(/_/g, ' ')}</strong>: ${nameOf(f.from_asset)} &rarr; ${nameOf(f.to_asset)}` +
          `<br/><span style="opacity:0.7">${f.magnitude_class}${f.status !== 'active' ? ` &middot; ${f.status}` : ''}` +
          ` &middot; as of ${f.as_of.slice(0, 10)}</span>` +
          `<br/><span style="opacity:0.55">${f.source}</span>`,
          { direction: 'top', className: 'map-tooltip', sticky: true },
        );
        line.addTo(group);
      }
      if (touching.length) hasOverlay = true;
    }

    if (selCompetition && selCompetition.participants.length >= 2) {
      const [hub, ...rest] = selCompetition.participants;
      const arcColor = selCompetition.is_ghost ? 'rgba(148,163,184,0.4)' : 'rgba(239,68,68,0.6)';
      for (const p of rest) {
        L.polyline(arcPoints([hub.lat, hub.lon], [p.lat, p.lon]), {
          color: arcColor, weight: 1.6, dashArray: '6 8', interactive: false,
        }).addTo(group);
      }
      for (const p of selCompetition.participants) {
        L.circleMarker([p.lat, p.lon], { radius: 3, color: '#e2e8f0', fillColor: '#e2e8f0', fillOpacity: 0.9, weight: 0 })
          .bindTooltip(p.label, { direction: 'top', className: 'map-tooltip' })
          .addTo(group);
      }
      hasOverlay = true;
    }

    if (hasOverlay) {
      group.addTo(map);
      overlayRef.current = group;
    }

    // Keep pressed routes above the selection overlay/spokes. Otherwise, if
    // pipelines were made visible BEFORE activating the theater, the overlay is
    // added on top of them and they read muted / feel unclickable. Bringing the
    // pressed lines to front makes the result order-independent.
    for (const { lines, asset } of linesRef.current.values()) {
      if (affected.size > 0 && isPressed(asset, affected)) {
        for (const l of lines) l.bringToFront();
      }
    }
  }, [selectedId, map]);

  // Build all layers. Point assets are visible at every zoom level
  // (predictability); categories and route/pipeline lines are filtered by
  // the legend toggles.
  useEffect(() => {
    const allLayers: L.Layer[] = [];
    const hidden = new Set(hiddenKey ? hiddenKey.split(',') : []);

    let justClicked = false;
    const mapClickHandler = () => {
      if (!justClicked) onSelectRef.current(null);
      justClicked = false;
    };
    map.on('click', mapClickHandler);

    const pointAssets = data.assets.filter(a => !isLinear(a));
    const lineAssets = data.assets.filter(isLinear);
    const positions = declutter(pointAssets);

    // Lines first so dots and badges stay clickable above them.
    for (const asset of lineAssets) {
      if (asset.asset_type === 'corridor' && !showRoutes) continue;
      if (asset.asset_type === 'pipeline' && !showPipelines) continue;
      const geom = asset.geometry as { type: string; coordinates: number[][] };
      if (geom?.type !== 'LineString') continue;

      // searoute emits unwrapped longitudes (>180) for dateline-crossing
      // routes; render a second copy shifted 360 deg so both halves show.
      const latlngs = geom.coordinates.map(toLatLng);
      const lons = geom.coordinates.map(c => c[0]);
      const copies: [number, number][][] = [latlngs];
      if (Math.max(...lons) > 180) copies.push(latlngs.map(([lat, lon]) => [lat, lon - 360]));
      if (Math.min(...lons) < -180) copies.push(latlngs.map(([lat, lon]) => [lat, lon + 360]));

      // Preserve current selection's pressed state across rebuilds (toggling
      // routes/pipelines re-runs this effect but not the selection effect).
      const linePressed = affectedRef.current.size > 0 && isPressed(asset, affectedRef.current);
      const lines: L.Polyline[] = [];
      for (const pts of copies) {
        const line = L.polyline(pts, { ...routeStyle(asset.asset_type, linePressed), interactive: true });
        line.bindTooltip(assetTooltipHtml(asset), { direction: 'top', className: 'map-tooltip', sticky: true });
        line.on('mouseover', () => lines.forEach(l => l.setStyle(routeStyle(asset.asset_type, isPressed(asset, affectedRef.current), true))));
        line.on('mouseout', () => lines.forEach(l => l.setStyle(routeStyle(asset.asset_type, isPressed(asset, affectedRef.current)))));
        line.on('click', () => {
          justClicked = true;
          onSelectRef.current({ kind: 'asset', asset });
        });
        line.addTo(map);
        lines.push(line);
        allLayers.push(line);
      }
      linesRef.current.set(asset.id, { lines, asset });
    }

    for (const asset of pointAssets) {
      if (hidden.has(categoryFor(asset.asset_type, asset.commodities))) continue;
      const pos = positions.get(asset.id);
      if (!pos) continue;

      const dotPressed = affectedRef.current.size > 0 && isPressed(asset, affectedRef.current);
      const { html, size } = buildDot(asset, dotPressed);
      const marker = L.marker(pos, { icon: divIconFor(html, size), interactive: true });
      marker.bindTooltip(assetTooltipHtml(asset), { direction: 'top', className: 'map-tooltip' });
      marker.on('mouseover', () => {
        const el = marker.getElement()?.firstElementChild as HTMLElement | null;
        if (el) el.style.transform = 'scale(1.35)';
      });
      marker.on('mouseout', () => {
        const el = marker.getElement()?.firstElementChild as HTMLElement | null;
        if (el) el.style.transform = '';
      });
      marker.on('click', () => {
        justClicked = true;
        onSelectRef.current({ kind: 'asset', asset });
      });
      marker.addTo(map);
      dotsRef.current.set(asset.id, { marker, asset });
      allLayers.push(marker);
    }

    for (const conflict of data.conflicts) {
      const geom = conflict.anchor as { type: string; coordinates: number[] };
      if (geom?.type !== 'Point' || !geom.coordinates) continue;

      const { html, size } = buildConflictBadge(conflict, conflict.id === selectedRef.current);
      const marker = L.marker(toLatLng(geom.coordinates), {
        icon: divIconFor(html, size),
        interactive: true,
        zIndexOffset: 500,
      });
      marker.bindTooltip(
        `<strong>${conflict.name_en}</strong><br/><span style="opacity:0.7">conflict zone${conflict.is_ghost ? ' &middot; dormant' : ''}</span>`,
        { direction: 'top', className: 'map-tooltip' },
      );
      marker.on('mouseover', () => {
        const el = marker.getElement()?.firstElementChild as HTMLElement | null;
        if (el) el.style.transform = 'scale(1.15)';
      });
      marker.on('mouseout', () => {
        const el = marker.getElement()?.firstElementChild as HTMLElement | null;
        if (el) el.style.transform = '';
      });
      marker.on('click', () => {
        justClicked = true;
        onSelectRef.current({ kind: 'conflict', conflict });
      });
      marker.addTo(map);
      conflictsRef.current.set(conflict.id, { marker, conflict });
      allLayers.push(marker);
    }

    // Competitions have no map marker — selected from the strip below the
    // map; their arcs draw via the selection effect.
    competitionsRef.current = new Map(data.competitions.map(c => [c.id, c]));
    flowsRef.current = data.flows ?? [];
    assetNameRef.current = new Map(data.assets.map(a => [a.id, a.name_en]));

    return () => {
      map.off('click', mapClickHandler);
      allLayers.forEach(l => { try { map.removeLayer(l); } catch { /* gone */ } });
      overlayRef.current?.remove();
      overlayRef.current = null;
      dotsRef.current.clear();
      linesRef.current.clear();
      conflictsRef.current.clear();
      competitionsRef.current.clear();
    };
  }, [map, data, hiddenKey, showRoutes, showPipelines]);

  return null;
}
