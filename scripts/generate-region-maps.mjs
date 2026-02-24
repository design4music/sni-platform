/**
 * Generate PNG map backgrounds for the 6 world region cards.
 *
 * Reads the full-resolution GeoJSON, filters features by bounding box,
 * renders high-quality SVG, then converts to small PNGs via sharp.
 *
 * Usage: node scripts/generate-region-maps.mjs
 */

import { readFileSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import sharp from 'sharp';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
const GEOJSON_PATH = join(ROOT, 'apps/frontend/public/geo/countries.geojson');
const OUTPUT_DIR = join(ROOT, 'apps/frontend/public/geo/regions');

// Region bounding boxes (longitude / latitude)
const REGIONS = {
  europe:   { minLng: -25, maxLng: 50,  minLat: 33,  maxLat: 72 },
  asia:     { minLng: 55,  maxLng: 155, minLat: -15, maxLat: 58 },
  africa:   { minLng: -22, maxLng: 55,  minLat: -37, maxLat: 38 },
  americas: { minLng: -170,maxLng: -30, minLat: -58, maxLat: 75 },
  oceania:  { minLng: 95,  maxLng: 180, minLat: -50, maxLat: 5  },
  mideast:  { minLng: 22,  maxLng: 78,  minLat: 8,   maxLat: 48 },
};

const SVG_W = 800;
const SVG_H = 600;
const PNG_W = 400;
const SIMPLIFY_FACTOR = 15; // moderate -- keeps shapes clean
const STROKE_COLOR = '#3b82f6';
const FILL_COLOR = '#2563eb';

// ---- projection helpers ----

function projectX(lng, b) {
  return ((lng - b.minLng) / (b.maxLng - b.minLng)) * SVG_W;
}
function projectY(lat, b) {
  return ((b.maxLat - lat) / (b.maxLat - b.minLat)) * SVG_H;
}

function simplifyRing(ring) {
  if (ring.length <= 6) return ring;
  const out = [ring[0]];
  for (let i = 1; i < ring.length - 1; i++) {
    if (i % SIMPLIFY_FACTOR === 0) out.push(ring[i]);
  }
  out.push(ring[ring.length - 1]);
  return out;
}

function ringToPathD(ring, b) {
  const pts = simplifyRing(ring);
  if (pts.length < 3) return '';
  return pts
    .map((c, i) => {
      const x = projectX(c[0], b).toFixed(1);
      const y = projectY(c[1], b).toFixed(1);
      return (i === 0 ? 'M' : 'L') + x + ',' + y;
    })
    .join('') + 'Z';
}

function featureTouches(feature, b) {
  const pad = 10;
  const ex = {
    minLng: b.minLng - pad, maxLng: b.maxLng + pad,
    minLat: b.minLat - pad, maxLat: b.maxLat + pad,
  };
  const geom = feature.geometry;
  const polys = geom.type === 'MultiPolygon' ? geom.coordinates : [geom.coordinates];
  for (const poly of polys) {
    for (const ring of poly) {
      for (const c of ring) {
        if (c[0] >= ex.minLng && c[0] <= ex.maxLng &&
            c[1] >= ex.minLat && c[1] <= ex.maxLat) return true;
      }
    }
  }
  return false;
}

function buildSVG(features, b) {
  const dParts = [];
  for (const f of features) {
    if (!featureTouches(f, b)) continue;
    const geom = f.geometry;
    const polys = geom.type === 'MultiPolygon' ? geom.coordinates : [geom.coordinates];
    for (const poly of polys) {
      const d = ringToPathD(poly[0], b);
      if (d) dParts.push(d);
    }
  }
  return [
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${SVG_W} ${SVG_H}">`,
    `  <rect width="${SVG_W}" height="${SVG_H}" fill="transparent"/>`,
    `  <path d="${dParts.join(' ')}"`,
    `    fill="${FILL_COLOR}" fill-opacity="0.35"`,
    `    stroke="${STROKE_COLOR}" stroke-width="0.5" stroke-opacity="0.6"/>`,
    `</svg>`,
  ].join('\n');
}

// ---- main ----

const geojson = JSON.parse(readFileSync(GEOJSON_PATH, 'utf-8'));
const features = geojson.features.filter(
  f => f.geometry && (f.geometry.type === 'Polygon' || f.geometry.type === 'MultiPolygon')
);

mkdirSync(OUTPUT_DIR, { recursive: true });

for (const [key, bounds] of Object.entries(REGIONS)) {
  const svg = buildSVG(features, bounds);

  const pngPath = join(OUTPUT_DIR, `${key}.png`);
  await sharp(Buffer.from(svg))
    .resize(PNG_W)
    .png({ compressionLevel: 9 })
    .toFile(pngPath);

  const { size } = await sharp(pngPath).metadata().then(() =>
    import('fs').then(fs => fs.statSync(pngPath))
  );
  const kb = (size / 1024).toFixed(1);
  console.log(`${key}: ${kb} KB`);
}

console.log('\nDone! PNGs written to ' + OUTPUT_DIR);
