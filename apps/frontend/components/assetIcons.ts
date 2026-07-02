// Visual language for the strategic-asset map layer.
//
// Point-like assets (ports, chokepoints, production clusters, facilities)
// render as icon badges: a small dark disc with a commodity/type glyph,
// ringed and glowing by stress. Linear assets (pipelines, corridors)
// render as smoothed lines — see StrategicAssetLayer.

// Asset color language: slate when calm, amber when under pressure.
// Red is reserved exclusively for conflicts — assets never turn red.
export function stressColor(stress: number): string {
  return stress > 0 ? '#f59e0b' : 'rgba(148,163,184,0.6)';
}

// Stroke-based glyphs (24x24 viewBox, drawn with stroke=currentColor).
const GLYPHS: Record<string, string> = {
  anchor:
    '<circle cx="12" cy="5" r="2.2"/><path d="M12 7.2V20"/><path d="M5 13a7 7 0 0 0 14 0"/><path d="M9 10h6"/>',
  narrows:
    '<path d="M5 4l6 8-6 8"/><path d="M19 4l-6 8 6 8"/>',
  droplet:
    '<path d="M12 3.5c-3.2 4.2-5.5 7-5.5 9.8a5.5 5.5 0 0 0 11 0c0-2.8-2.3-5.6-5.5-9.8z"/>',
  flame:
    '<path d="M12 3.5c.8 3-4 5.5-4 9.5a4.8 4.8 0 0 0 9.6 0c0-1.8-.9-3.2-1.9-4.7-.6 1.4-1.4 2-2.4 2 .8-2.3.3-4.6-1.3-6.8z"/>',
  wheat:
    '<path d="M12 21V7"/><path d="M12 11C9 11 7 9.2 7 6.5 10 6.5 12 8.3 12 11z"/><path d="M12 11c3 0 5-1.8 5-4.5-3 0-5 1.8-5 4.5z"/><path d="M12 16c-3 0-5-1.8-5-4.5 3 0 5 1.8 5 4.5z"/><path d="M12 16c3 0 5-1.8 5-4.5-3 0-5 1.8-5 4.5z"/>',
  chip:
    '<rect x="8" y="8" width="8" height="8" rx="1"/><path d="M5 10h3M5 14h3M16 10h3M16 14h3M10 5v3M14 5v3M10 16v3M14 16v3"/>',
  battery:
    '<rect x="3.5" y="8" width="15" height="8" rx="1.5"/><path d="M20.5 11v2"/><path d="M11.5 9.5l-2 2.5h3l-2 2.5"/>',
  gem:
    '<path d="M8 4h8l4 6-8 10L4 10l4-6z"/><path d="M4 10h16"/><path d="M12 20L9 10l3-6 3 6-3 10"/>',
  flask:
    '<path d="M10 3h4"/><path d="M10 3v6l-4.6 8.6A2 2 0 0 0 7.2 21h9.6a2 2 0 0 0 1.8-3.4L14 9V3"/><path d="M8 15h8"/>',
  boxes:
    '<rect x="4" y="13" width="7" height="6.5"/><rect x="13" y="13" width="7" height="6.5"/><rect x="8.5" y="5.5" width="7" height="6.5"/>',
  factory:
    '<path d="M3.5 20V9.5l5 3.5V9.5l5 3.5V6H20v14H3.5z"/>',
};

// Commodity → glyph. Anything mined falls back to the gem.
const COMMODITY_GLYPH: Record<string, string> = {
  oil: 'droplet',
  refined_products: 'droplet',
  gas: 'flame',
  lng: 'flame',
  grain: 'wheat',
  corn: 'wheat',
  soy: 'wheat',
  palm_oil: 'wheat',
  lithium: 'battery',
  semiconductors: 'chip',
  chemicals: 'flask',
  containers: 'boxes',
};

function glyphKeyFor(assetType: string, commodities: string[]): string {
  if (assetType === 'port') return 'anchor';
  if (assetType === 'chokepoint') return 'narrows';
  for (const c of commodities) {
    if (COMMODITY_GLYPH[c]) return COMMODITY_GLYPH[c];
    if (/ore|copper|cobalt|nickel|bauxite|uranium|rare|platinum|palladium|potash|phosphate|gold|coal|iron/.test(c)) {
      return 'gem';
    }
  }
  return assetType === 'facility' ? 'factory' : 'gem';
}

export interface BadgeAsset {
  asset_type: string;
  commodities: string[];
  criticality: number;
  stress: number;
}

// Conflict markers: crossed swords in a red badge. Visually distinct from
// assets — conflicts are the dynamic layer (why), assets the static one
// (what's at risk).
const SWORDS_GLYPH =
  '<path d="M5 4l14 14"/><path d="M19 4L5 18"/><path d="M4 17l3 3"/><path d="M20 17l-3 3"/>';

export function buildConflictBadge(
  c: { intensity: number; is_ghost: boolean },
  selected: boolean,
): { html: string; size: number } {
  // Conflicts are the headline layer: 2-3x the (uniform) asset badge size.
  const size = c.is_ghost ? 30 : 40 + c.intensity * 14; // 40-54px live, 30px dormant
  const color = c.is_ghost ? 'rgba(148,163,184,0.6)' : '#ef4444';
  const border = selected ? '#ffffff' : color;
  const glow = c.is_ghost ? '' : `box-shadow: 0 0 ${8 + c.intensity * 12}px rgba(239,68,68,${0.4 + c.intensity * 0.4});`;
  const iconColor = c.is_ghost ? 'rgba(203,213,225,0.7)' : '#fecaca';

  return {
    size,
    html:
      `<div style="width:${size}px;height:${size}px;border-radius:50%;` +
      `background:rgba(26,10,10,0.92);border:2px solid ${border};${glow}` +
      `display:flex;align-items:center;justify-content:center;` +
      `transition:transform 0.1s;cursor:pointer;">` +
      `<svg viewBox="0 0 24 24" width="${size - 9}" height="${size - 9}" ` +
      `fill="none" stroke="${iconColor}" stroke-width="2" ` +
      `stroke-linecap="round" stroke-linejoin="round">${SWORDS_GLYPH}</svg></div>`,
  };
}

// All asset badges are the same size — hierarchy comes from color
// (calm/pressured) and the double ring on systemic chokepoints, not size.
// Conflicts are the only large markers on the map.
const ASSET_BADGE_SIZE = 22;

// Full HTML for a Leaflet divIcon. Size returned so the caller can center
// the icon anchor.
export function buildBadge(asset: BadgeAsset, selected: boolean): { html: string; size: number } {
  const size = ASSET_BADGE_SIZE;
  const color = stressColor(asset.stress);
  const border = selected ? '#ffffff' : color;
  // Criticality-5 assets are systemic chokepoints (strait, canal, or a
  // single fab) — they carry a second outer ring regardless of type.
  const chokepointRing = asset.criticality >= 5
    ? `0 0 0 3.5px rgba(10,18,32,0.9), 0 0 0 5px ${selected ? '#ffffff' : color}`
    : '';
  const glow = asset.stress > 0 ? `0 0 ${8 + asset.stress * 8}px ${color}` : '';
  const shadow = [chokepointRing, glow].filter(Boolean).join(', ');
  const iconColor = asset.stress > 0 ? '#fde68a' : 'rgba(203,213,225,0.85)';
  const glyph = GLYPHS[glyphKeyFor(asset.asset_type, asset.commodities)];

  return {
    size,
    html:
      `<div style="width:${size}px;height:${size}px;border-radius:50%;` +
      `background:rgba(10,18,32,0.92);border:2px solid ${border};` +
      (shadow ? `box-shadow:${shadow};` : '') +
      `display:flex;align-items:center;justify-content:center;` +
      `transition:transform 0.1s;cursor:pointer;">` +
      `<svg viewBox="0 0 24 24" width="${size - 9}" height="${size - 9}" ` +
      `fill="none" stroke="${iconColor}" stroke-width="2" ` +
      `stroke-linecap="round" stroke-linejoin="round">${glyph}</svg></div>`,
  };
}
