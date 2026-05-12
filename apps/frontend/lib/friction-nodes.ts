// Friction nodes + narratives_v2 (1-to-1 collapsed model).
//
// Tables:
//   friction_nodes         — contested phenomena (curated)
//   narratives_v2          — FN-specific narratives (one per FN, ordered)
//   event_friction_nodes   — events substantively about an FN
//   title_narratives       — titles framed through a narrative's lens
//
// Narratives carry fn_id directly (the legacy friction_node_narratives
// join table was retired 2026-05-12 when we committed to FN-specific
// prose). Per-narrative attribution scope override lives in
// narratives_v2.scope_centroid_ids; if NULL the parent FN's
// centroid_ids applies.

import { query } from './db';
import { cached } from './cache';

// Re-export client-safe types and the colour palette so existing
// server-side imports of NARRATIVE_COLORS / FrictionNode etc. keep
// working. Client components MUST import from './friction-nodes-shared'
// directly to avoid pulling pg into the browser bundle.
export type {
  FrictionNode,
  SampleTitle,
  NarrativeOnFn,
  FrictionNodeView,
  NarrativeWeeklyPoint,
  FnRecentEvent,
  FnWeekBucket,
  RelatedFn,
  CentroidLookupEntry,
  TheaterPointer,
  TheaterMemberFn,
} from './friction-nodes-shared';
export { colorForNarrative } from './friction-nodes-shared';

import type {
  FrictionNode,
  SampleTitle,
  NarrativeOnFn,
  FrictionNodeView,
  NarrativeWeeklyPoint,
  FnRecentEvent,
  FnWeekBucket,
  RelatedFn,
  CentroidLookupEntry,
  TheaterPointer,
  TheaterMemberFn,
} from './friction-nodes-shared';

// ============================================================
// Queries
// ============================================================

const TTL = 12 * 3600;
const SAMPLE_TITLES_PER_NARRATIVE = 6;

function locale2(locale?: string): 'en' | 'de' {
  return locale === 'de' ? 'de' : 'en';
}

export async function getFrictionNodeBySlug(
  slug: string,
  locale?: string,
): Promise<FrictionNode | null> {
  const loc = locale2(locale);
  return cached(`fn:${slug}:${loc}`, TTL, async () => {
    const rows = await query<{
      id: string;
      name: string;
      description: string | null;
      editorial_summary: string | null;
      centroid_ids: string[];
      fn_type: 'atomic' | 'theater';
      member_fn_ids: string[] | null;
    }>(
      `SELECT id,
              ${loc === 'de' ? 'COALESCE(name_de, name_en)' : 'name_en'} AS name,
              ${loc === 'de' ? 'COALESCE(description_de, description_en)' : 'description_en'} AS description,
              ${loc === 'de' ? 'COALESCE(editorial_summary_de, editorial_summary_en)' : 'editorial_summary_en'} AS editorial_summary,
              centroid_ids,
              fn_type,
              member_fn_ids
       FROM friction_nodes
       WHERE id = $1 AND is_active = true`,
      [slug],
    );
    const r = rows[0];
    if (!r) return null;
    return {
      ...r,
      member_fn_ids: r.member_fn_ids ?? [],
    };
  });
}

/**
 * If this atomic FN is bundled inside a theater (a friction_node row with
 * fn_type='theater' whose member_fn_ids contains this FN's id), return a
 * compact pointer for the "Part of: X" pill. NULL if no theater bundles it.
 */
export async function getTheaterForAtomicFn(
  fnId: string,
  locale?: string,
): Promise<TheaterPointer | null> {
  const loc = locale2(locale);
  return cached(`fn_theater:${fnId}:${loc}`, TTL, async () => {
    const rows = await query<{ id: string; name: string }>(
      `SELECT id,
              ${loc === 'de' ? 'COALESCE(name_de, name_en)' : 'name_en'} AS name
       FROM friction_nodes
       WHERE fn_type = 'theater'
         AND is_active = true
         AND $1 = ANY(member_fn_ids)
       LIMIT 1`,
      [fnId],
    );
    return rows[0] ?? null;
  });
}

/**
 * For a theater FN: return constituent atomic FNs with their stance bricks
 * (narrative_id + stance_label + display_order + match_count). Used by the
 * theater landing page to render one row per atomic FN with a colored
 * stance-brick preview underneath.
 */
export async function getTheaterMembers(
  theaterId: string,
  locale?: string,
): Promise<TheaterMemberFn[]> {
  const loc = locale2(locale);
  return cached(`fn_theater_members:${theaterId}:${loc}`, TTL, async () => {
    // Resolve the member_fn_ids list.
    const tRows = await query<{ member_fn_ids: string[] | null }>(
      `SELECT member_fn_ids FROM friction_nodes WHERE id = $1`,
      [theaterId],
    );
    const memberIds = tRows[0]?.member_fn_ids ?? [];
    if (!memberIds.length) return [];

    const fnRows = await query<{
      id: string;
      name: string;
      description: string | null;
      editorial_summary: string | null;
    }>(
      `SELECT id,
              ${loc === 'de' ? 'COALESCE(name_de, name_en)' : 'name_en'} AS name,
              ${loc === 'de' ? 'COALESCE(description_de, description_en)' : 'description_en'} AS description,
              ${loc === 'de' ? 'COALESCE(editorial_summary_de, editorial_summary_en)' : 'editorial_summary_en'} AS editorial_summary
       FROM friction_nodes WHERE id = ANY($1) AND is_active = true`,
      [memberIds],
    );

    const stanceRows = await query<{
      fn_id: string;
      narrative_id: string;
      label: string;
      display_order: number;
      stance: number | null;
    }>(
      `SELECT n.fn_id, n.id AS narrative_id,
              ${loc === 'de' ? 'COALESCE(n.stance_label_de, n.stance_label_en)' : 'n.stance_label_en'} AS label,
              n.display_order,
              n.stance
       FROM narratives_v2 n
       WHERE n.fn_id = ANY($1) AND n.is_active = true
       ORDER BY n.fn_id, n.display_order`,
      [memberIds],
    );

    const eventCountRows = await query<{ fn_id: string; n: number }>(
      `SELECT fn_id, COUNT(*)::int AS n
       FROM event_friction_nodes WHERE fn_id = ANY($1)
       GROUP BY fn_id`,
      [memberIds],
    );

    const allNarrativeIds = Array.from(new Set(stanceRows.map((r) => r.narrative_id)));
    const matchCountByNarrative = new Map<string, number>();
    if (allNarrativeIds.length) {
      const mRows = await query<{ narrative_id: string; n: number }>(
        `SELECT narrative_id, COUNT(*)::int AS n
         FROM title_narratives
         WHERE narrative_id = ANY($1)
         GROUP BY narrative_id`,
        [allNarrativeIds],
      );
      for (const r of mRows) matchCountByNarrative.set(r.narrative_id, r.n);
    }

    const eventCountByFn = new Map<string, number>();
    for (const r of eventCountRows) eventCountByFn.set(r.fn_id, r.n);

    const stancesByFn = new Map<string, TheaterMemberFn['stances']>();
    for (const r of stanceRows) {
      const arr = stancesByFn.get(r.fn_id) ?? [];
      arr.push({
        narrative_id: r.narrative_id,
        label: r.label,
        display_order: r.display_order,
        match_count: matchCountByNarrative.get(r.narrative_id) ?? 0,
        stance: r.stance,
      });
      stancesByFn.set(r.fn_id, arr);
    }

    // Preserve member_fn_ids order.
    const byId = new Map(fnRows.map((r) => [r.id, r]));
    return memberIds
      .map((id) => byId.get(id))
      .filter((r): r is NonNullable<typeof r> => Boolean(r))
      .map((r) => ({
        id: r.id,
        name: r.name,
        description: r.description,
        editorial_summary: r.editorial_summary,
        event_count: eventCountByFn.get(r.id) ?? 0,
        stances: stancesByFn.get(r.id) ?? [],
      }));
  });
}

export async function getFrictionNodeView(
  slug: string,
  locale?: string,
): Promise<FrictionNodeView | null> {
  const loc = locale2(locale);
  return cached(`fn_view:${slug}:${loc}`, TTL, async () => {
    const fn = await getFrictionNodeBySlug(slug, locale);
    if (!fn) return null;

    // Narratives + stance, ordered.
    const narrativeRows = await query<{
      narrative_id: string;
      narrative_name: string;
      narrative_claim: string;
      actor_centroids: string[];
      framing_keywords: string[];
      publishers: string[] | null;
      stance_label: string;
      stance: number | null;
      display_order: number;
    }>(
      `SELECT n.id AS narrative_id,
              ${loc === 'de' ? 'COALESCE(n.name_de, n.name_en)' : 'n.name_en'} AS narrative_name,
              ${loc === 'de' ? 'COALESCE(n.claim_de, n.claim_en)' : 'n.claim_en'} AS narrative_claim,
              n.actor_centroids,
              n.framing_keywords,
              n.publishers,
              n.stance,
              ${loc === 'de' ? 'COALESCE(n.stance_label_de, n.stance_label_en)' : 'n.stance_label_en'} AS stance_label,
              n.display_order
       FROM narratives_v2 n
       WHERE n.fn_id = $1 AND n.is_active = true
       ORDER BY n.display_order`,
      [slug],
    );

    const narrativeIds = narrativeRows.map((r) => r.narrative_id);

    // Aggregate match counts per narrative (uncapped).
    const countByNarrative = new Map<string, number>();
    if (narrativeIds.length) {
      const countRows2 = await query<{ narrative_id: string; n: number }>(
        `SELECT narrative_id, COUNT(*)::int AS n
         FROM title_narratives
         WHERE narrative_id = ANY($1)
         GROUP BY narrative_id`,
        [narrativeIds],
      );
      for (const r of countRows2) countByNarrative.set(r.narrative_id, r.n);
    }

    // Sample titles per narrative — RANKED by framing-keyword strength
    // (count of narrative.framing_keywords present in the title), then by
    // recency. This surfaces headlines with the strongest visible framing
    // language as representative of the narrative bucket, even though
    // membership itself is decided by publisher stance + FN topic match.
    const titlesByNarrative = new Map<string, SampleTitle[]>();
    if (narrativeIds.length) {
      const titleRows = await query<{
        narrative_id: string;
        id: string;
        title: string;
        publisher_name: string | null;
        pubdate_utc: string;
      }>(
        `SELECT narrative_id, id, title, publisher_name, pubdate_utc FROM (
            SELECT tn.narrative_id,
                   t.id,
                   t.title_display AS title,
                   t.publisher_name,
                   t.pubdate_utc::text AS pubdate_utc,
                   (
                     SELECT COUNT(*) FROM unnest(n.framing_keywords) kw
                     WHERE t.title_display ILIKE '%' || kw || '%'
                   ) AS framing_strength,
                   ROW_NUMBER() OVER (
                     PARTITION BY tn.narrative_id
                     ORDER BY (
                       SELECT COUNT(*) FROM unnest(n.framing_keywords) kw
                       WHERE t.title_display ILIKE '%' || kw || '%'
                     ) DESC, t.pubdate_utc DESC
                   ) AS rn
            FROM title_narratives tn
            JOIN titles_v3 t ON t.id = tn.title_id
            JOIN narratives_v2 n ON n.id = tn.narrative_id
            WHERE tn.narrative_id = ANY($1)
         ) ranked
         WHERE rn <= $2
         ORDER BY narrative_id, framing_strength DESC, pubdate_utc DESC`,
        [narrativeIds, SAMPLE_TITLES_PER_NARRATIVE],
      );
      for (const row of titleRows) {
        const arr = titlesByNarrative.get(row.narrative_id) ?? [];
        arr.push({
          id: row.id,
          title: row.title,
          publisher_name: row.publisher_name,
          pubdate_utc: row.pubdate_utc,
        });
        titlesByNarrative.set(row.narrative_id, arr);
      }
    }

    // Event count for the FN.
    const countRows = await query<{ event_count: number }>(
      `SELECT COUNT(*)::int AS event_count
       FROM event_friction_nodes WHERE fn_id = $1`,
      [slug],
    );
    const event_count = countRows[0]?.event_count ?? 0;

    return {
      fn,
      narratives: narrativeRows.map((r) => ({
        ...r,
        publishers: r.publishers ?? [],
        match_count: countByNarrative.get(r.narrative_id) ?? 0,
        sample_titles: titlesByNarrative.get(r.narrative_id) ?? [],
      })),
      event_count,
    };
  });
}

/**
 * Weekly per-narrative title counts for the FN's linked narratives.
 * Used by the stacked-area activity chart. Buckets by ISO week (Monday).
 * Returns a flat list ordered by week ascending; counts are present for
 * every narrative on every week (zeros included) so Recharts can stack.
 */
export async function getFrictionNodeWeeklyActivity(
  slug: string,
): Promise<NarrativeWeeklyPoint[]> {
  return cached(`fn_weekly:${slug}`, TTL, async () => {
    // First find the narrative_ids on this FN.
    const narrativeIdRows = await query<{ narrative_id: string }>(
      `SELECT id AS narrative_id FROM narratives_v2
       WHERE fn_id = $1 AND is_active = true
       ORDER BY display_order`,
      [slug],
    );
    const narrativeIds = narrativeIdRows.map((r) => r.narrative_id);
    if (!narrativeIds.length) return [];

    // Weekly buckets per narrative.
    const rows = await query<{
      week: string;
      narrative_id: string;
      n: number;
    }>(
      `SELECT
          to_char(date_trunc('week', t.pubdate_utc), 'YYYY-MM-DD') AS week,
          tn.narrative_id,
          COUNT(*)::int AS n
       FROM title_narratives tn
       JOIN titles_v3 t ON t.id = tn.title_id
       WHERE tn.narrative_id = ANY($1)
       GROUP BY 1, 2
       ORDER BY 1`,
      [narrativeIds],
    );

    // Pivot into one point per week with all narratives keyed.
    const byWeek = new Map<string, Record<string, number>>();
    for (const r of rows) {
      const slot = byWeek.get(r.week) ?? {};
      slot[r.narrative_id] = r.n;
      byWeek.set(r.week, slot);
    }
    const weeks = Array.from(byWeek.keys()).sort();
    return weeks.map((week) => {
      const counts: Record<string, number> = {};
      let total = 0;
      for (const id of narrativeIds) {
        const c = byWeek.get(week)?.[id] ?? 0;
        counts[id] = c;
        total += c;
      }
      return { week, counts, total };
    });
  });
}

/**
 * Per-week event buckets for the FN: each week carries its TOTAL event
 * count + the top-N events for that week (ordered by member-title
 * count, our importance proxy). Used by the combined volume-bars +
 * per-week events component.
 *
 * Implementation: pulls all events for the FN (date / title / source
 * count), buckets server-side by ISO week, sorts within each bucket by
 * member-title count DESC, caps at perWeek.
 */
export async function getFrictionNodeEventsByWeek(
  slug: string,
  locale?: string,
  perWeek = 10,
): Promise<FnWeekBucket[]> {
  const loc = locale2(locale);
  return cached(`fn_events_by_week:${slug}:${loc}:${perWeek}`, TTL, async () => {
    const rows = await query<{
      id: string;
      date: string;
      week: string;
      title: string;
      source_count: number;
      title_count: number;
      importance: number | null;
    }>(
      `SELECT e.id::text,
              e.date::text,
              to_char(date_trunc('week', e.date::timestamp), 'YYYY-MM-DD') AS week,
              ${loc === 'de' ? 'COALESCE(e.title_de, e.title)' : 'e.title'} AS title,
              (SELECT COUNT(DISTINCT t.publisher_name)
                 FROM event_v3_titles et
                 JOIN titles_v3 t ON t.id = et.title_id
                 WHERE et.event_id = e.id)::int AS source_count,
              (SELECT COUNT(*) FROM event_v3_titles et WHERE et.event_id = e.id)::int AS title_count,
              e.importance_score AS importance
       FROM event_friction_nodes efn
       JOIN events_v3 e ON e.id = efn.event_id
       WHERE efn.fn_id = $1
         AND e.is_promoted = true
         AND e.merged_into IS NULL
       ORDER BY week, title_count DESC, e.date DESC`,
      [slug],
    );

    const byWeek = new Map<string, FnWeekBucket>();
    for (const r of rows) {
      let bucket = byWeek.get(r.week);
      if (!bucket) {
        bucket = { week: r.week, total: 0, events: [] };
        byWeek.set(r.week, bucket);
      }
      bucket.total += 1;
      if (bucket.events.length < perWeek) {
        bucket.events.push({
          id: r.id,
          date: r.date,
          title: r.title,
          source_count: r.source_count,
          importance: r.importance,
        });
      }
    }
    return Array.from(byWeek.values()).sort((a, b) => a.week.localeCompare(b.week));
  });
}

/**
 * Other atomic conflicts in the same theater (siblings under the same
 * fn_type='theater' row whose member_fn_ids contains this slug).
 * Returns empty for theater rows themselves.
 */
export async function getSiblingFrictionNodes(
  slug: string,
  locale?: string,
): Promise<RelatedFn[]> {
  const loc = locale2(locale);
  return cached(`fn_siblings:${slug}:${loc}`, TTL, async () => {
    return query<RelatedFn>(
      `WITH theater AS (
         SELECT member_fn_ids
         FROM friction_nodes
         WHERE fn_type = 'theater'
           AND is_active = true
           AND $1 = ANY(member_fn_ids)
         LIMIT 1
       )
       SELECT fn.id,
              ${loc === 'de' ? 'COALESCE(fn.name_de, fn.name_en)' : 'fn.name_en'} AS name,
              0::int AS shared_narratives
       FROM friction_nodes fn, theater
       WHERE fn.id = ANY(theater.member_fn_ids)
         AND fn.id != $1
         AND fn.is_active = true
       ORDER BY fn.name_en`,
      [slug],
    );
  });
}

/**
 * Resolve a list of centroid IDs to display label + first iso2 code so we
 * can render country pills with flags + names instead of raw centroid IDs.
 */
export async function getCentroidLookup(ids: string[]): Promise<CentroidLookupEntry[]> {
  if (!ids.length) return [];
  return query<{ id: string; label: string; iso_codes: string[] | null }>(
    `SELECT id, label, iso_codes FROM centroids_v3 WHERE id = ANY($1)`,
    [ids],
  ).then((rows) =>
    rows.map((r) => ({
      id: r.id,
      label: r.label,
      iso2: r.iso_codes && r.iso_codes.length > 0 ? r.iso_codes[0] : null,
    })),
  );
}

export async function getActiveFrictionNodes(
  locale?: string,
): Promise<FrictionNode[]> {
  const loc = locale2(locale);
  return cached(`fn:list:${loc}`, TTL, async () => {
    const rows = await query<{
      id: string;
      name: string;
      description: string | null;
      editorial_summary: string | null;
      centroid_ids: string[];
      fn_type: 'atomic' | 'theater';
      member_fn_ids: string[] | null;
    }>(
      `SELECT id,
              ${loc === 'de' ? 'COALESCE(name_de, name_en)' : 'name_en'} AS name,
              ${loc === 'de' ? 'COALESCE(description_de, description_en)' : 'description_en'} AS description,
              ${loc === 'de' ? 'COALESCE(editorial_summary_de, editorial_summary_en)' : 'editorial_summary_en'} AS editorial_summary,
              centroid_ids,
              fn_type,
              member_fn_ids
       FROM friction_nodes
       WHERE is_active = true
       ORDER BY display_order NULLS LAST, name_en`,
    );
    return rows.map((r) => ({
      ...r,
      member_fn_ids: r.member_fn_ids ?? [],
    }));
  });
}
