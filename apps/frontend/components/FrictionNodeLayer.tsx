'use client';

import { useEffect, useRef } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import type { FnMapData } from './WorldMap';

type Theater = FnMapData['theaters'][0];

interface Props {
  data: FnMapData;
  onSelect: (theater: Theater | null) => void;
  selectedTheaterId: string | null;
}

const THEATER_COORDS: Record<string, [number, number]> = {
  iran_theater:          [32.0, 53.0],
  israel_theater:        [31.7, 35.2],
  syria_theater:         [33.5, 37.5],
  ukraine_war_theater:   [48.5, 33.0],
  turkey_theater:        [39.0, 35.5],
  yemen_red_sea_theater: [15.0, 44.5],
};

// Circle radius scales with coverage intensity: 500km (quiet) → 950km (peak).
// Range chosen so Ukraine/Israel are visibly larger than Yemen/Turkey without
// neighboring theaters (Israel/Syria/Iran) overlapping so much they merge.
const RADIUS_MIN_M = 500_000;
const RADIUS_MAX_M = 950_000;
function theaterRadius(intensity: number): number {
  return RADIUS_MIN_M + (RADIUS_MAX_M - RADIUS_MIN_M) * intensity;
}

// Fixed border weight — circles all use the same stroke width regardless of size/intensity.
// Only fill opacity and border alpha shift with intensity so the ring stays crisp.
const BORDER_W = 2;

// Ghost: always gray + dashed regardless of intensity.
const GHOST_DEFAULT  = { color: 'rgba(110,110,120,0.45)', weight: BORDER_W, fillColor: 'rgba(110,110,120,1)', fillOpacity: 0.04, dashArray: '7 6' };
const GHOST_HOVER    = { color: 'rgba(160,160,170,0.65)', weight: BORDER_W, fillColor: 'rgba(160,160,170,1)', fillOpacity: 0.08, dashArray: '7 6' };
const GHOST_SELECTED = { color: 'rgba(180,180,190,0.80)', weight: BORDER_W, fillColor: 'rgba(180,180,190,1)', fillOpacity: 0.14, dashArray: '7 6' };

const SPOKE_GHOST_DEFAULT  = { color: 'rgba(130,130,140,0.18)', weight: 1, dashArray: '4 6' };
const SPOKE_GHOST_SELECTED = { color: 'rgba(255,255,255,0.35)', weight: 1.5 };   // solid white when selected
const DOT_GHOST_DEFAULT    = { color: 'rgba(130,130,140,0.4)',  fillColor: 'rgba(130,130,140,0.4)',  fillOpacity: 1, weight: 0 };
const DOT_GHOST_SELECTED   = { color: 'rgba(255,255,255,0.7)',  fillColor: 'rgba(255,255,255,0.7)',  fillOpacity: 1, weight: 0 };

// Active default: border alpha and fill scale with intensity; weight stays fixed.
function activeDefault(intensity: number): L.PathOptions {
  const alpha = 0.4 + 0.45 * intensity;
  const fill  = 0.03 + 0.13 * intensity;
  return {
    color: `rgba(251,146,60,${alpha.toFixed(2)})`,
    weight: BORDER_W,
    fillColor: 'rgba(251,146,60,1)',
    fillOpacity: fill,
  };
}
// Hover: slightly brighter border + more fill. Weight still fixed.
function activeHover(intensity: number): L.PathOptions {
  return {
    color: `rgba(251,146,60,${Math.min(1, 0.75 + 0.25 * intensity).toFixed(2)})`,
    weight: BORDER_W,
    fillColor: 'rgba(251,146,60,1)',
    fillOpacity: 0.13 + 0.08 * intensity,
  };
}
// Selected: bright solid orange ring + clear fill. Weight stays same.
const ACTIVE_SELECTED: L.PathOptions = {
  color: '#fb923c',
  weight: BORDER_W,
  fillColor: 'rgba(251,146,60,1)',
  fillOpacity: 0.28,
};

// Default spokes: dim dashed orange lines.
function spokeDefault(intensity: number): L.PathOptions {
  return { color: `rgba(251,146,60,${(0.14 + 0.18 * intensity).toFixed(2)})`, weight: 1, dashArray: '4 6' };
}
// Selected spokes: solid white — unmistakably distinct from unselected.
const SPOKE_SELECTED: L.PathOptions = { color: 'rgba(255,255,255,0.55)', weight: 1.5 };

function dotDefault(intensity: number): L.PathOptions {
  const a = (0.3 + 0.3 * intensity).toFixed(2);
  return { color: `rgba(251,146,60,${a})`, fillColor: `rgba(251,146,60,${a})`, fillOpacity: 1, weight: 0 };
}
const DOT_SELECTED: L.PathOptions = { color: 'rgba(255,255,255,0.85)', fillColor: 'rgba(255,255,255,0.85)', fillOpacity: 1, weight: 0 };

export default function FrictionNodeLayer({ data, onSelect, selectedTheaterId }: Props) {
  const map = useMap();
  const circlesRef    = useRef<Map<string, { circle: L.Circle; theater: Theater }>>(new Map());
  const spokesRef     = useRef<Map<string, Array<L.Polyline | L.CircleMarker>>>(new Map());
  const selectedIdRef = useRef<string | null>(selectedTheaterId);
  const onSelectRef   = useRef(onSelect);

  useEffect(() => { selectedIdRef.current = selectedTheaterId; }, [selectedTheaterId]);
  useEffect(() => { onSelectRef.current = onSelect; }, [onSelect]);

  // Update visual styles whenever selection changes.
  useEffect(() => {
    for (const [id, { circle, theater }] of circlesRef.current) {
      const sel = id === selectedTheaterId;
      circle.setStyle(
        theater.is_ghost
          ? (sel ? GHOST_SELECTED : GHOST_DEFAULT)
          : (sel ? ACTIVE_SELECTED : activeDefault(theater.intensity)),
      );
    }
    for (const [id, layers] of spokesRef.current) {
      const entry  = circlesRef.current.get(id);
      const theater = entry?.theater;
      if (!theater) continue;
      const sel = id === selectedTheaterId;
      for (const layer of layers) {
        const isDot = layer instanceof L.CircleMarker && !(layer instanceof L.Circle);
        if (theater.is_ghost) {
          layer.setStyle(isDot
            ? (sel ? DOT_GHOST_SELECTED : DOT_GHOST_DEFAULT)
            : (sel ? SPOKE_GHOST_SELECTED : SPOKE_GHOST_DEFAULT));
        } else {
          layer.setStyle(isDot
            ? (sel ? DOT_SELECTED : dotDefault(theater.intensity))
            : (sel ? SPOKE_SELECTED : spokeDefault(theater.intensity)));
        }
      }
    }
  }, [selectedTheaterId]);

  // Create all Leaflet layers; own the map-level deselect handler.
  useEffect(() => {
    const allLayers: L.Layer[] = [];

    // justClicked: suppresses the map 'click' that Leaflet always fires after a
    // layer click via its internal _propagateEvent (bypasses DOM stopPropagation).
    let justClicked = false;
    const mapClickHandler = () => {
      if (!justClicked) onSelectRef.current(null);
      justClicked = false;
    };
    map.on('click', mapClickHandler);

    for (const theater of data.theaters) {
      const center = THEATER_COORDS[theater.id];
      if (!center) continue;

      const spokeLayers: Array<L.Polyline | L.CircleMarker> = [];
      const sdStyle = theater.is_ghost ? SPOKE_GHOST_DEFAULT : spokeDefault(theater.intensity);
      const ddStyle = theater.is_ghost ? DOT_GHOST_DEFAULT   : dotDefault(theater.intensity);

      for (const target of theater.radialTargets) {
        const pos: [number, number] = [target.lat, target.lon];
        const spoke = L.polyline([center, pos], sdStyle);
        spoke.addTo(map);
        spokeLayers.push(spoke);
        allLayers.push(spoke);

        const dot = L.circleMarker(pos, { ...ddStyle, radius: 3, interactive: true });
        dot.bindTooltip(target.label, { direction: 'top', className: 'map-tooltip' });
        dot.addTo(map);
        spokeLayers.push(dot);
        allLayers.push(dot);
      }
      spokesRef.current.set(theater.id, spokeLayers);

      const defStyle  = theater.is_ghost ? GHOST_DEFAULT  : activeDefault(theater.intensity);
      const hovStyle  = theater.is_ghost ? GHOST_HOVER    : activeHover(theater.intensity);
      const selStyle  = theater.is_ghost ? GHOST_SELECTED : ACTIVE_SELECTED;

      const circle = L.circle(center, { ...defStyle, radius: theaterRadius(theater.intensity), interactive: true });
      circle.bindTooltip(theater.name_en, { direction: 'top', className: 'map-tooltip' });

      circle.on('mouseover', () => {
        if (selectedIdRef.current !== theater.id) circle.setStyle(hovStyle);
      });
      circle.on('mouseout', () => {
        if (selectedIdRef.current !== theater.id) circle.setStyle(defStyle);
      });
      circle.on('click', () => {
        justClicked = true;
        onSelectRef.current(theater);
      });

      circle.addTo(map);
      allLayers.push(circle);
      circlesRef.current.set(theater.id, { circle, theater });
    }

    return () => {
      map.off('click', mapClickHandler);
      allLayers.forEach(l => { try { map.removeLayer(l); } catch (_) { /* already gone */ } });
      circlesRef.current.clear();
      spokesRef.current.clear();
    };
  }, [map, data]);

  return null;
}
