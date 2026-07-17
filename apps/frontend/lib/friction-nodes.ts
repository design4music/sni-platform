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
  CentroidLookupEntry,
  TheaterPointer,
  TheaterMemberFn,
} from './friction-nodes-shared';

// ============================================================
// Queries
// ============================================================

const TTL = 12 * 3600;
const SAMPLE_TITLES_PER_NARRATIVE = 6;

// Theater coalition roll-up: a theater carries no fn_anchor bundle of its own
// (spec: theaters never match). Its coalition cards source sample titles +
// counts from the member atomics -- a title qualifies for coalition N iff its
// publisher is in N.publishers AND it is attributed to a member-atomic
// narrative of the same stance sign. Ranking mirrors the atomic sample-title
// query (framing tier -> publisher diversity -> promoted -> source consensus
// -> framing strength -> recency). total_count is the uncapped distinct-title
// count for the coalition (the card's "N titles" figure).
// Params: $1 framing_keywords[], $2 member_fn_ids[], $3 theater stance,
//         $4 publishers[], $5 limit.
const THEATER_ROLLUP_SQL = `
  WITH src AS (
    SELECT DISTINCT ON (t.id)
      t.id AS title_id,
      t.title_display,
      t.publisher_name,
      t.pubdate_utc::text AS pubdate_utc,
      COALESCE(e.source_batch_count, 1) AS sbc,
      CASE WHEN e.is_promoted = true THEN 1 ELSE 0 END AS promoted_int,
      (SELECT COUNT(*) FROM unnest($1::text[]) kw
        WHERE t.title_display ILIKE '%' || kw || '%') AS framing_strength
    FROM title_narratives tn
    JOIN narratives_v2 an ON an.id = tn.narrative_id
    JOIN friction_nodes afn ON afn.id = an.fn_id
    JOIN titles_v3 t ON t.id = tn.title_id
    LEFT JOIN event_v3_titles et ON et.title_id = t.id
    LEFT JOIN events_v3 e ON e.id = et.event_id AND e.merged_into IS NULL
    WHERE afn.id = ANY($2::text[]) AND afn.fn_type = 'atomic'
      AND an.stance IS NOT NULL AND sign(an.stance)::int = sign($3::int)
      AND t.publisher_name = ANY($4::text[])
    ORDER BY t.id,
      CASE WHEN e.is_promoted = true THEN 0 ELSE 1 END,
      COALESCE(e.source_batch_count, 0) DESC NULLS LAST
  ),
  publisher_ranked AS (
    SELECT *,
      ROW_NUMBER() OVER (
        PARTITION BY publisher_name
        ORDER BY promoted_int DESC, sbc DESC, framing_strength DESC, pubdate_utc DESC
      ) AS pub_rn,
      COUNT(*) OVER () AS total_count
    FROM src
  ),
  ranked AS (
    SELECT *,
      ROW_NUMBER() OVER (
        ORDER BY
          CASE WHEN framing_strength > 0 THEN 0 ELSE 1 END,
          CASE WHEN pub_rn <= 2 THEN 0 ELSE 1 END,
          promoted_int DESC, sbc DESC, framing_strength DESC, pubdate_utc DESC
      ) AS rn
    FROM publisher_ranked
  )
  SELECT title_id AS id, title_display AS title, publisher_name,
         pubdate_utc, total_count::int AS total_count
  FROM ranked
  WHERE rn <= $5
  ORDER BY rn`;

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

    const countByNarrative = new Map<string, number>();
    const titlesByNarrative = new Map<string, SampleTitle[]>();

    // Theater branch: roll sample titles + counts up from the member atomics
    // (theaters carry no bundle of their own). See THEATER_ROLLUP_SQL.
    if (fn.fn_type === 'theater') {
      const memberIds = fn.member_fn_ids ?? [];
      for (const n of narrativeRows) {
        const publishers = n.publishers ?? [];
        if (!memberIds.length || !publishers.length || n.stance == null) {
          countByNarrative.set(n.narrative_id, 0);
          continue;
        }
        const rows = await query<{
          id: string;
          title: string;
          publisher_name: string | null;
          pubdate_utc: string;
          total_count: number;
        }>(THEATER_ROLLUP_SQL, [
          n.framing_keywords ?? [],
          memberIds,
          n.stance,
          publishers,
          SAMPLE_TITLES_PER_NARRATIVE,
        ]);
        countByNarrative.set(n.narrative_id, rows[0]?.total_count ?? 0);
        titlesByNarrative.set(
          n.narrative_id,
          rows.map((r) => ({
            id: r.id,
            title: r.title,
            publisher_name: r.publisher_name,
            pubdate_utc: r.pubdate_utc,
          })),
        );
      }
      const event_count = 0; // theaters have no direct events
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
    }

    // --- Atomic FN path -------------------------------------------------
    // Aggregate match counts per narrative (uncapped).
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

    // Sample titles per narrative — composite ranking:
    //   1. Publisher diversity tier (max 2 per publisher in the preferred
    //      tier; undersized narratives fall through to fill remaining slots)
    //   2. Promoted-event preference (titles attached to is_promoted events
    //      rank first, but unpromoted still eligible — no hard filter)
    //   3. Source consensus (events_v3.source_batch_count desc)
    //   4. Framing-keyword strength (count of narrative.framing_keywords
    //      present in the title — original signal, now a tiebreaker)
    //   5. Recency
    //
    // Event-level deduplication picks one title per event so near-duplicate
    // headlines from the same clustered story don't dominate the top 6.
    if (narrativeIds.length) {
      const titleRows = await query<{
        narrative_id: string;
        id: string;
        title: string;
        publisher_name: string | null;
        pubdate_utc: string;
      }>(
        `WITH titles_with_event AS (
            -- One row per (narrative, title). Pick the best event when a
            -- title is attached to multiple events (e.g. Phase 3.2 sibling
            -- reconciliation keeps pre- and post-merge attachments).
            SELECT DISTINCT ON (tn.narrative_id, t.id)
              tn.narrative_id,
              t.id AS title_id,
              t.title_display,
              t.publisher_name,
              t.pubdate_utc::text AS pubdate_utc,
              COALESCE(e.id::text, t.id::text) AS dedup_key,
              COALESCE(e.source_batch_count, 1) AS sbc,
              CASE WHEN e.is_promoted = true THEN 1 ELSE 0 END AS promoted_int,
              (SELECT COUNT(*) FROM unnest(n.framing_keywords) kw
               WHERE t.title_display ILIKE '%' || kw || '%') AS framing_strength
            FROM title_narratives tn
            JOIN titles_v3 t ON t.id = tn.title_id
            JOIN narratives_v2 n ON n.id = tn.narrative_id
            LEFT JOIN event_v3_titles et ON et.title_id = t.id
            LEFT JOIN events_v3 e ON e.id = et.event_id AND e.merged_into IS NULL
            WHERE tn.narrative_id = ANY($1)
            ORDER BY tn.narrative_id, t.id,
              CASE WHEN e.is_promoted = true THEN 0 ELSE 1 END,
              COALESCE(e.source_batch_count, 0) DESC NULLS LAST
         ),
         deduped AS (
            SELECT *,
              ROW_NUMBER() OVER (
                PARTITION BY narrative_id, dedup_key
                ORDER BY framing_strength DESC, pubdate_utc DESC
              ) AS event_rn
            FROM titles_with_event
         ),
         publisher_ranked AS (
            SELECT *,
              ROW_NUMBER() OVER (
                PARTITION BY narrative_id, publisher_name
                ORDER BY promoted_int DESC, sbc DESC, framing_strength DESC, pubdate_utc DESC
              ) AS pub_rn
            FROM deduped
            WHERE event_rn = 1
         ),
         ranked AS (
            -- Tier priority: titles whose own text matches narrative
            -- framing_keywords come first (loaded-vocabulary tier). Within
            -- each tier, publisher diversity, then quality signals.
            -- Counts (brick row, activity chart, publisher list) come from
            -- title_narratives directly and are NOT affected by this sort.
            SELECT *,
              ROW_NUMBER() OVER (
                PARTITION BY narrative_id
                ORDER BY
                  CASE WHEN framing_strength > 0 THEN 0 ELSE 1 END,
                  CASE WHEN pub_rn <= 2 THEN 0 ELSE 1 END,
                  promoted_int DESC,
                  sbc DESC,
                  framing_strength DESC,
                  pubdate_utc DESC
              ) AS rn
            FROM publisher_ranked
         )
         SELECT narrative_id, title_id AS id, title_display AS title,
                publisher_name, pubdate_utc, framing_strength
         FROM ranked
         WHERE rn <= $2
         ORDER BY narrative_id, rn`,
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

export interface FrictionNodeWithActivity {
  id: string;
  name: string;
  description: string | null;
  editorial_summary: string | null;
  fn_type: 'atomic' | 'theater';
  event_count: number;
  last_activity_date: string | null;
}

export interface TheaterWithMembers {
  id: string;
  name: string;
  description: string | null;
  editorial_summary: string | null;
  event_count: number;
  last_activity_date: string | null;
  members: FrictionNodeWithActivity[];
  /**
   * True for an atomic FN that no theater bundles, surfaced here as a
   * top-level zone in its own right. Conflicts whose real coverage supports
   * only one atomic (South China Sea) have no theater to nest under; without
   * this they load but never render. `members` is always empty — the entry
   * links straight to the atomic's own page.
   */
  standalone?: boolean;
}

export interface FnByRegion {
  region: string;
  theaters: TheaterWithMembers[];
}

/**
 * Get all active FNs organized by region, with theaters and their atomic members.
 * Includes event counts and last activity dates for each FN.
 */
export async function getAllFrictionNodesByRegion(
  locale?: string,
): Promise<FnByRegion[]> {
  const loc = locale2(locale);
  return cached(`fn:by_region:${loc}`, TTL, async () => {
    // Get all active theaters
    const theaterRows = await query<{
      id: string;
      name: string;
      description: string | null;
      editorial_summary: string | null;
      centroid_ids: string[];
      member_fn_ids: string[] | null;
    }>(
      `SELECT id,
              ${loc === 'de' ? 'COALESCE(name_de, name_en)' : 'name_en'} AS name,
              ${loc === 'de' ? 'COALESCE(description_de, description_en)' : 'description_en'} AS description,
              ${loc === 'de' ? 'COALESCE(editorial_summary_de, editorial_summary_en)' : 'editorial_summary_en'} AS editorial_summary,
              centroid_ids,
              member_fn_ids
       FROM friction_nodes
       WHERE is_active = true AND fn_type = 'theater'
       ORDER BY display_order NULLS LAST, name_en`,
    );

    // Get all atomic FNs
    const atomicRows = await query<{
      id: string;
      name: string;
      description: string | null;
      editorial_summary: string | null;
      centroid_ids: string[];
    }>(
      `SELECT id,
              ${loc === 'de' ? 'COALESCE(name_de, name_en)' : 'name_en'} AS name,
              ${loc === 'de' ? 'COALESCE(description_de, description_en)' : 'description_en'} AS description,
              ${loc === 'de' ? 'COALESCE(editorial_summary_de, editorial_summary_en)' : 'editorial_summary_en'} AS editorial_summary,
              centroid_ids
       FROM friction_nodes
       WHERE is_active = true AND fn_type = 'atomic'`,
    );
    const centroidsByAtomic = new Map<string, string[]>(
      atomicRows.map((r) => [r.id, r.centroid_ids ?? []]),
    );

    // Get event counts for atomic FNs only (theaters don't have direct events)
    const eventCountRows = await query<{ fn_id: string; n: number }>(
      `SELECT fn_id, COUNT(*)::int AS n
       FROM event_friction_nodes
       GROUP BY fn_id`,
    );
    const eventCountByFn = new Map<string, number>();
    for (const r of eventCountRows) eventCountByFn.set(r.fn_id, r.n);

    // Get last activity date for atomic FNs only
    const lastActivityRows = await query<{
      fn_id: string;
      last_date: string;
    }>(
      `SELECT fn_id, MAX(e.date)::text AS last_date
       FROM event_friction_nodes efn
       JOIN events_v3 e ON efn.event_id = e.id
       GROUP BY fn_id`,
    );
    const lastActivityByFn = new Map<string, string>();
    for (const r of lastActivityRows) lastActivityByFn.set(r.fn_id, r.last_date);

    // Build atomic FN map
    const atomicById = new Map<string, FrictionNodeWithActivity>();
    for (const r of atomicRows) {
      atomicById.set(r.id, {
        id: r.id,
        name: r.name,
        description: r.description,
        editorial_summary: r.editorial_summary,
        fn_type: 'atomic',
        event_count: eventCountByFn.get(r.id) ?? 0,
        last_activity_date: lastActivityByFn.get(r.id) ?? null,
      });
    }

    // Build theaters with members, aggregating event counts and dates from members
    const byRegion = new Map<string, TheaterWithMembers[]>();
    for (const theater of theaterRows) {
      const region = extractRegion(theater.centroid_ids);
      const memberIds = theater.member_fn_ids ?? [];
      const members: FrictionNodeWithActivity[] = memberIds
        .map((id) => atomicById.get(id))
        .filter((m): m is FrictionNodeWithActivity => Boolean(m));

      // Theater's event count is sum of its members' event counts
      const theaterEventCount = members.reduce((sum, m) => sum + m.event_count, 0);

      // Theater's last activity is the latest of all its members
      const allMemberDates = members
        .map((m) => m.last_activity_date)
        .filter((d): d is string => Boolean(d));
      const lastDate = allMemberDates.length
        ? allMemberDates.sort().reverse()[0]
        : null;

      const theaterRecord: TheaterWithMembers = {
        id: theater.id,
        name: theater.name,
        description: theater.description,
        editorial_summary: theater.editorial_summary,
        event_count: theaterEventCount,
        last_activity_date: lastDate,
        members,
      };

      if (!byRegion.has(region)) byRegion.set(region, []);
      byRegion.get(region)!.push(theaterRecord);
    }

    // Atomics no theater claims stand on their own. Their detail page already
    // renders (getTheaterForAtomicFn just returns null); this is the only
    // place they would otherwise drop out of the UI entirely.
    const bundledIds = new Set(theaterRows.flatMap((t) => t.member_fn_ids ?? []));
    for (const [id, atomic] of atomicById) {
      if (bundledIds.has(id)) continue;
      const region = extractRegion(centroidsByAtomic.get(id) ?? []);
      if (!byRegion.has(region)) byRegion.set(region, []);
      byRegion.get(region)!.push({
        id: atomic.id,
        name: atomic.name,
        description: atomic.description,
        editorial_summary: atomic.editorial_summary,
        event_count: atomic.event_count,
        last_activity_date: atomic.last_activity_date,
        members: [],
        standalone: true,
      });
    }

    // Sort regions in display order, sort theaters within region
    const regionOrder = [
      'EUROPE',
      'MIDEAST',
      'AFRICA',
      'ASIA',
      'AMERICAS',
      'OCEANIA',
      'NON-STATE',
    ];
    const result: FnByRegion[] = [];
    for (const region of regionOrder) {
      const theaters = byRegion.get(region);
      if (theaters && theaters.length > 0) {
        result.push({
          region,
          theaters: theaters.sort((a, b) => a.name.localeCompare(b.name)),
        });
      }
    }

    return result;
  });
}

function extractRegion(centroidIds: string[]): string {
  if (!centroidIds.length) return 'OTHER';
  const prefix = centroidIds[0].split('-')[0];
  const regionMap: Record<string, string> = {
    EUROPE: 'EUROPE',
    MIDEAST: 'MIDEAST',
    AFRICA: 'AFRICA',
    ASIA: 'ASIA',
    AMERICAS: 'AMERICAS',
    OCEANIA: 'OCEANIA',
  };
  return regionMap[prefix] || 'NON-STATE';
}
