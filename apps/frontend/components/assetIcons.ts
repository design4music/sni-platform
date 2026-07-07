// Visual language for the strategic-asset map layer.
//
// Assets render as small uniform category-colored dots — always visible,
// at every zoom level, no icons on the map itself. The glyph appears in
// the hover tooltip. Conflicts are the only large markers (red warning
// badges). Red is reserved exclusively for conflicts and for assets lit
// up by the selected conflict.

// Asset categories: one color per category, drawn from the hues the
// dashboard already uses (Tailwind blue-400 / violet-400 / amber-500 /
// cyan-400 / pink-400 / emerald-400 / gray-200).
export const ASSET_CATEGORIES: Record<string, { label: string; color: string }> = {
  port:        { label: 'Ports & logistics',   color: '#60a5fa' },
  chokepoint:  { label: 'Chokepoints',         color: '#a78bfa' },
  oil:         { label: 'Oil',                 color: '#f59e0b' },
  gas:         { label: 'Gas & LNG',           color: '#22d3ee' },
  minerals:    { label: 'Mining & minerals',   color: '#f472b6' },
  agriculture: { label: 'Agriculture & food',  color: '#34d399' },
  power:       { label: 'Power generation',    color: '#a3e635' },
  industry:    { label: 'Industry & tech',     color: '#e5e7eb' },
};

const MINERAL_RE = /ore|copper|cobalt|nickel|bauxite|uranium|rare|platinum|palladium|gold|coal|iron|lithium|tin|graphite|zinc|pgm/;
// Fertilizer feedstocks (potash/phosphate) and food crops read as agriculture,
// matching the registry's food-security framing rather than mining.
const AGRICULTURE_RE = /grain|corn|soy|palm_oil|wheat|rice|fish|sugar|coffee|cocoa|potash|phosphate/;

export function categoryFor(assetType: string, commodities: string[]): string {
  if (assetType === 'port') return 'port';
  if (assetType === 'chokepoint') return 'chokepoint';
  // Power plants carry {'electricity', <generation type>} — checked before
  // the commodity loop so a coal plant lands in power, not minerals.
  if (commodities.includes('electricity')) return 'power';
  for (const c of commodities) {
    if (c === 'oil' || c === 'refined_products') return 'oil';
    if (c === 'gas' || c === 'lng') return 'gas';
    if (AGRICULTURE_RE.test(c)) return 'agriculture';
    if (MINERAL_RE.test(c)) return 'minerals';
    if (c === 'semiconductors' || c === 'chemicals' || c === 'autos') return 'industry';
  }
  return 'industry';
}

// Stroke-based glyphs (24x24 viewBox) — shown in tooltips, not on the map.
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
  gem:
    '<path d="M8 4h8l4 6-8 10L4 10l4-6z"/><path d="M4 10h16"/><path d="M12 20L9 10l3-6 3 6-3 10"/>',
  factory:
    '<path d="M3.5 20V9.5l5 3.5V9.5l5 3.5V6H20v14H3.5z"/>',
  bolt:
    '<path d="M13 2.5L5 13.5h5.5L10 21.5l8-11h-5.5l.5-8z"/>',
};

const CATEGORY_GLYPH: Record<string, string> = {
  port: 'anchor',
  chokepoint: 'narrows',
  oil: 'droplet',
  gas: 'flame',
  minerals: 'gem',
  agriculture: 'wheat',
  power: 'bolt',
  industry: 'factory',
};

export interface BadgeAsset {
  asset_type: string;
  commodities: string[];
  criticality: number;
  stress: number;
}

// Tooltip content: category glyph + name + type line.
export function assetTooltipHtml(asset: BadgeAsset & { name_en: string }): string {
  const cat = categoryFor(asset.asset_type, asset.commodities);
  const { color } = ASSET_CATEGORIES[cat];
  const glyph = GLYPHS[CATEGORY_GLYPH[cat]];
  const type = asset.asset_type.replace(/_/g, ' ');
  const pressure = asset.stress > 0 ? ' &middot; under pressure' : '';
  return (
    `<span style="display:inline-flex;align-items:center;gap:6px">` +
    `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="${color}" ` +
    `stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${glyph}</svg>` +
    `<strong>${asset.name_en}</strong></span>` +
    `<br/><span style="opacity:0.7">${type}${pressure}</span>`
  );
}

// Uniform asset dot: 12px (twice the 6px capital dots, well under the
// conflict badges). Category color fill; soft amber halo when any live FN
// presses on it; red ring + glow when related to the selected FN.
const DOT_SIZE = 12;

export function buildDot(asset: BadgeAsset, related: boolean): { html: string; size: number } {
  const cat = categoryFor(asset.asset_type, asset.commodities);
  const { color } = ASSET_CATEGORIES[cat];
  // Criticality-5 = systemic chokepoint: thin white outer ring, any type.
  const chokeRing = asset.criticality >= 5 ? '0 0 0 2px rgba(226,232,240,0.55)' : '';
  const halo = related
    ? '0 0 0 3px rgba(239,68,68,0.9), 0 0 10px 2px rgba(239,68,68,0.8)'
    : asset.stress > 0
      ? '0 0 7px 1px rgba(245,158,11,0.65)'
      : '';
  const shadow = [chokeRing, halo].filter(Boolean).join(', ');
  return {
    size: DOT_SIZE,
    html:
      `<div style="width:${DOT_SIZE}px;height:${DOT_SIZE}px;border-radius:50%;` +
      `background:${color};border:1.5px solid rgba(10,14,26,0.9);` +
      (shadow ? `box-shadow:${shadow};` : '') +
      `transition:transform 0.1s;cursor:pointer;"></div>`,
  };
}

// Conflict badge: warning triangle, constant size (not intensity-scaled —
// hierarchy against assets comes from size class, glow carries intensity).
const CONFLICT_GLYPH =
  '<path d="M12 4L2.5 20h19L12 4z"/><path d="M12 10.5v4"/><path d="M12 17.3h.01"/>';

export function buildConflictBadge(
  c: { intensity: number; is_ghost: boolean },
  selected: boolean,
): { html: string; size: number } {
  const size = c.is_ghost ? 24 : 34;
  const color = c.is_ghost ? 'rgba(148,163,184,0.6)' : '#ef4444';
  const border = selected ? '#ffffff' : color;
  const glow = c.is_ghost ? '' : `box-shadow: 0 0 ${8 + c.intensity * 14}px rgba(239,68,68,${0.35 + c.intensity * 0.45});`;
  const iconColor = c.is_ghost ? 'rgba(203,213,225,0.7)' : '#fecaca';

  return {
    size,
    html:
      `<div style="width:${size}px;height:${size}px;border-radius:50%;` +
      `background:rgba(26,10,10,0.92);border:2px solid ${border};${glow}` +
      `display:flex;align-items:center;justify-content:center;` +
      `transition:transform 0.1s;cursor:pointer;">` +
      `<svg viewBox="0 0 24 24" width="${size - 10}" height="${size - 10}" ` +
      `fill="none" stroke="${iconColor}" stroke-width="2" ` +
      `stroke-linecap="round" stroke-linejoin="round">${CONFLICT_GLYPH}</svg></div>`,
  };
}
