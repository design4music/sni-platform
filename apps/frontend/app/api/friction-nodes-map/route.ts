import { NextResponse } from 'next/server';
import { query } from '@/lib/db';

interface FnRow {
  id: string;
  name_en: string;
  fn_type: string;
  centroid_ids: string[] | null;
  member_fn_ids: string[] | null;
}

interface CentroidRow {
  id: string;
  label: string;
  iso_codes: string[] | null;
}

interface TheaterStats {
  theater_id: string;
  total_events: string; // pg returns bigint as string
  last_active: string | null;
}

export const revalidate = 3600;

const CENTROID_POSITIONS: Record<string, [number, number]> = {
  'MIDEAST-IRAN':        [32.4,  53.7],
  'MIDEAST-ISRAEL':      [31.8,  35.2],
  'MIDEAST-PALESTINE':   [31.9,  35.3],
  'MIDEAST-LEVANT':      [33.5,  36.3],
  'MIDEAST-TURKEY':      [39.9,  32.9],
  'MIDEAST-IRAQ':        [33.3,  44.4],
  'MIDEAST-SAUDI':       [24.7,  46.7],
  'MIDEAST-GULF':        [25.2,  55.3],
  'MIDEAST-EGYPT':       [30.1,  31.2],
  'MIDEAST-SUDAN':       [15.6,  32.5],
  'MIDEAST-YEMEN':       [15.4,  44.2],
  'EUROPE-UKRAINE':      [50.5,  30.5],
  'EUROPE-RUSSIA':       [55.8,  37.6],
  'EUROPE-GERMANY':      [52.5,  13.4],
  'EUROPE-FRANCE':       [48.9,   2.3],
  'EUROPE-UK':           [51.5,  -0.1],
  'EUROPE-GREECE':       [37.9,  23.7],
  'AMERICAS-USA':        [38.9, -77.0],
  'AMERICAS-VENEZUELA':  [10.5, -66.9],
  'AMERICAS-GREENLAND':  [64.2, -51.7],
  'NON-STATE-EU':        [50.8,   4.4],
  'NON-STATE-NATO':      [50.9,   4.5],
  'NON-STATE-ISIS':      [35.5,  40.0],
  'NON-STATE-KURDISTAN': [36.2,  43.5],
};

const GHOST_DAYS = 90;

function fallbackLabel(cid: string): string {
  return cid
    .replace(/^[^-]+-/, '')
    .toLowerCase()
    .replace(/\b\w/g, ch => ch.toUpperCase());
}

export async function GET() {
  const [rows, statsRows] = await Promise.all([
    query<FnRow>(`
      SELECT id, name_en, fn_type, centroid_ids, member_fn_ids
      FROM friction_nodes
      WHERE is_active = true
      ORDER BY fn_type, display_order
    `),
    // Aggregate event volume + recency for each theater through its member atomic FNs.
    // Events link only to atomics; theaters are aggregated here.
    query<TheaterStats>(`
      SELECT
        t.id AS theater_id,
        COUNT(efn.event_id) AS total_events,
        MAX(e.last_active)::text AS last_active
      FROM friction_nodes t
      LEFT JOIN event_friction_nodes efn ON efn.fn_id = ANY(t.member_fn_ids)
      LEFT JOIN events_v3 e ON e.id = efn.event_id
      WHERE t.fn_type = 'theater' AND t.is_active = true
      GROUP BY t.id
    `),
  ]);

  const theaters = rows.filter(r => r.fn_type === 'theater');
  const atomics  = new Map(rows.filter(r => r.fn_type === 'atomic').map(r => [r.id, r]));
  const statsMap = new Map(statsRows.map(s => [s.theater_id, s]));

  // Centroid labels + ISO codes for the info panel.
  const allCentroidIds = new Set<string>();
  for (const t of theaters) for (const c of t.centroid_ids ?? []) allCentroidIds.add(c);
  const centroidRows = allCentroidIds.size > 0
    ? await query<CentroidRow>(`SELECT id, label, iso_codes FROM centroids_v3 WHERE id = ANY($1)`, [[...allCentroidIds]])
    : [];
  const centroidMap = new Map(centroidRows.map(r => [r.id, r]));

  // Compute sqrt-normalized intensity across all theaters.
  // Sqrt gives good spread: sqrt(3839) ≈ 62, sqrt(402) ≈ 20 — a 3x visual range.
  const maxEvents = Math.max(
    ...statsRows.map(s => parseInt(s.total_events, 10)),
    1,
  );

  const now = Date.now();

  const theaterData = theaters.map(t => {
    const stats = statsMap.get(t.id);
    const totalEvents = parseInt(stats?.total_events ?? '0', 10);
    const lastActive  = stats?.last_active ?? null;

    const daysSinceLast = lastActive
      ? (now - new Date(lastActive).getTime()) / 86_400_000
      : Infinity;

    const is_ghost  = daysSinceLast > GHOST_DAYS;
    const intensity = Math.sqrt(totalEvents / maxEvents); // 0 – 1

    const directIds = t.centroid_ids ?? [];

    // Effective reach for radial spokes (own centroid_ids + member atomic FN centroid_ids).
    const effectiveIds = new Set<string>(directIds);
    for (const id of t.member_fn_ids ?? []) {
      const fn = atomics.get(id);
      if (fn) for (const c of fn.centroid_ids ?? []) effectiveIds.add(c);
    }

    return {
      id: t.id,
      name_en: t.name_en,
      intensity,
      is_ghost,
      last_active_date: lastActive,
      total_events: totalEvents,
      atomicFNs: (t.member_fn_ids ?? [])
        .map(id => atomics.get(id))
        .filter((fn): fn is FnRow => !!fn)
        .map(fn => ({ id: fn.id, name_en: fn.name_en })),
      countries: directIds.map(cid => {
        const c   = centroidMap.get(cid);
        const pos = CENTROID_POSITIONS[cid];
        return {
          id: cid,
          label:     c?.label ?? fallbackLabel(cid),
          flag_iso2: c?.iso_codes?.length === 1 ? c.iso_codes[0] : null,
          lat: pos?.[0] ?? null,
          lon: pos?.[1] ?? null,
        };
      }),
      radialTargets: [...effectiveIds]
        .map(cid => {
          const pos = CENTROID_POSITIONS[cid];
          const c   = centroidMap.get(cid);
          return {
            id: cid,
            label: c?.label ?? fallbackLabel(cid),
            lat: pos?.[0] ?? null,
            lon: pos?.[1] ?? null,
          };
        })
        .filter((c): c is { id: string; label: string; lat: number; lon: number } => c.lat !== null)
        .slice(0, 10),
    };
  });

  return NextResponse.json({ theaters: theaterData });
}
