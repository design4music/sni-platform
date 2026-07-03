import { NextResponse } from 'next/server';
import { query } from '@/lib/db';

// Strategic-asset map layer (fn-map branch prototype).
//
// Model: strategic_assets are the static ground truth (chokepoints, ports,
// pipelines, production clusters). Friction nodes press on assets via
// friction_nodes.affected_asset_ids. The map renders assets colored by
// stress; it never draws conflict shapes of its own.
//
// scope='global' theaters (US-China, US-Russia...) are relationships, not
// places — they are returned separately as `competitions` and rendered in
// a strip below the map, never as geometry.

interface AssetRow {
  id: string;
  name_en: string;
  name_de: string | null;
  asset_type: string;
  geometry: unknown; // GeoJSON Point | LineString | Polygon
  commodities: string[];
  criticality: number;
  description_en: string | null;
  description_de: string | null;
}

interface TheaterRow {
  id: string;
  name_en: string;
  scope: string;
  affected_asset_ids: string[];
  centroid_ids: string[];
  anchor_point: unknown | null; // GeoJSON Point — conflict epicenter
  total_events: string; // pg bigint
  last_active: string | null;
}

interface CentroidRow {
  id: string;
  label: string;
  iso_codes: string[] | null;
  map_point: { coordinates: [number, number] } | null;
}

export const revalidate = 3600;

const GHOST_DAYS = 90;

export async function GET() {
  const [assetRows, theaterRows] = await Promise.all([
    query<AssetRow>(`
      SELECT id, name_en, name_de, asset_type, geometry, commodities,
             criticality, description_en, description_de
      FROM strategic_assets
      WHERE is_active = true
    `),
    // Events link only to atomic FNs; theaters aggregate through member_fn_ids.
    query<TheaterRow>(`
      SELECT t.id, t.name_en, t.scope, t.affected_asset_ids, t.centroid_ids, t.anchor_point,
             COUNT(efn.event_id) AS total_events,
             MAX(e.last_active)::text AS last_active
      FROM friction_nodes t
      LEFT JOIN event_friction_nodes efn ON efn.fn_id = ANY(t.member_fn_ids)
      LEFT JOIN events_v3 e ON e.id = efn.event_id
      WHERE t.fn_type = 'theater' AND t.is_active = true
      GROUP BY t.id
    `),
  ]);

  // Participant capitals for conflict spokes and rivalry arcs.
  const allCentroidIds = Array.from(new Set(theaterRows.flatMap(t => t.centroid_ids ?? [])));
  const centroidRows = allCentroidIds.length
    ? await query<CentroidRow>(
        `SELECT id, label, iso_codes, map_point FROM centroids_v3 WHERE id = ANY($1) AND map_point IS NOT NULL`,
        [allCentroidIds],
      )
    : [];
  const centroidById = new Map(centroidRows.map(c => [c.id, c]));

  function participantsFor(centroidIds: string[]) {
    return (centroidIds ?? [])
      .map(id => centroidById.get(id))
      .filter((c): c is CentroidRow & { map_point: { coordinates: [number, number] } } => Boolean(c?.map_point))
      .map(c => ({
        id: c.id,
        label: c.label,
        iso_codes: c.iso_codes ?? [],
        lon: c.map_point.coordinates[0],
        lat: c.map_point.coordinates[1],
      }));
  }

  const now = Date.now();
  const maxEvents = Math.max(...theaterRows.map(t => parseInt(t.total_events, 10)), 1);

  const theaters = theaterRows.map(t => {
    const totalEvents = parseInt(t.total_events, 10);
    const daysSinceLast = t.last_active
      ? (now - new Date(t.last_active).getTime()) / 86_400_000
      : Infinity;
    return {
      id: t.id,
      name_en: t.name_en,
      scope: t.scope,
      affected_asset_ids: t.affected_asset_ids ?? [],
      centroid_ids: t.centroid_ids ?? [],
      anchor_point: t.anchor_point,
      total_events: totalEvents,
      last_active: t.last_active,
      is_ghost: daysSinceLast > GHOST_DAYS,
      intensity: Math.sqrt(totalEvents / maxEvents), // 0 – 1
    };
  });

  // Asset stress = max intensity over live (non-ghost) FNs pressing on it.
  // Ghost FNs still appear in the asset's fn list, flagged dormant.
  const assets = assetRows.map(a => {
    const pressing = theaters.filter(t => t.affected_asset_ids.includes(a.id));
    const live = pressing.filter(t => !t.is_ghost);
    const stress = live.length ? Math.max(...live.map(t => t.intensity)) : 0;
    return {
      id: a.id,
      name_en: a.name_en,
      name_de: a.name_de,
      asset_type: a.asset_type,
      geometry: a.geometry,
      commodities: a.commodities ?? [],
      criticality: a.criticality,
      description_en: a.description_en,
      description_de: a.description_de,
      stress,
      fns: pressing
        .sort((x, y) => y.total_events - x.total_events)
        .map(t => ({
          id: t.id,
          name_en: t.name_en,
          total_events: t.total_events,
          last_active: t.last_active,
          is_ghost: t.is_ghost,
        })),
    };
  });

  // Conflict markers: regional theaters with an anchor point. A conflict
  // is a place too — Gaza spins no commodities but must be on the map.
  const conflicts = theaters
    .filter(t => t.scope === 'regional' && t.anchor_point)
    .sort((x, y) => y.total_events - x.total_events)
    .map(t => ({
      id: t.id,
      name_en: t.name_en,
      anchor: t.anchor_point,
      affected_asset_ids: t.affected_asset_ids,
      participants: participantsFor(t.centroid_ids),
      total_events: t.total_events,
      last_active: t.last_active,
      is_ghost: t.is_ghost,
      intensity: t.intensity,
    }));

  const competitions = theaters
    .filter(t => t.scope === 'global')
    .sort((x, y) => y.total_events - x.total_events)
    .map(t => ({
      id: t.id,
      name_en: t.name_en,
      participants: participantsFor(t.centroid_ids),
      affected_asset_ids: t.affected_asset_ids,
      total_events: t.total_events,
      last_active: t.last_active,
      is_ghost: t.is_ghost,
      intensity: t.intensity,
    }));

  return NextResponse.json({ assets, conflicts, competitions });
}
