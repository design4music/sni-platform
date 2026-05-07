// Shadow architecture: friction nodes + narratives_v2. (cache-bust 2026-05-07-r13-events-byweek)
// Separate module from queries.ts to keep the shadow concerns isolated until
// the wider rollout decides on naming and integration.
//
// Tables (see db/migrations/20260507_friction_nodes_v2.sql):
//   friction_nodes            — contested phenomena
//   narratives_v2             — framing-explicit narrative library
//   friction_node_narratives  — which narratives apply, with stance label
//   event_friction_nodes      — events about a phenomenon (topic match)
//   title_narratives          — titles framed through a narrative's lens
//
// No matcher integration: title_narratives + event_friction_nodes are
// populated by scripts/bootstrap_fn2_demo_links.sql for the demo.

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
  FnEventVolumePoint,
  FnWeekBucket,
  RelatedFn,
  CentroidLookupEntry,
} from './friction-nodes-shared';
export { NARRATIVE_COLORS, colorForNarrative } from './friction-nodes-shared';

import type {
  FrictionNode,
  SampleTitle,
  NarrativeOnFn,
  FrictionNodeView,
  NarrativeWeeklyPoint,
  FnRecentEvent,
  FnEventVolumePoint,
  FnWeekBucket,
  RelatedFn,
  CentroidLookupEntry,
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
      topic_keywords: string[];
    }>(
      `SELECT id,
              ${loc === 'de' ? 'COALESCE(name_de, name_en)' : 'name_en'} AS name,
              ${loc === 'de' ? 'COALESCE(description_de, description_en)' : 'description_en'} AS description,
              ${loc === 'de' ? 'COALESCE(editorial_summary_de, editorial_summary_en)' : 'editorial_summary_en'} AS editorial_summary,
              centroid_ids,
              topic_keywords
       FROM friction_nodes
       WHERE id = $1 AND is_active = true`,
      [slug],
    );
    return rows[0] || null;
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
      tier: 'operational' | 'ideological' | null;
      narrative_type: 'all_in' | 'stand_by' | null;
      framing_keywords: string[];
      publishers: string[] | null;
      stance_label: string;
      display_order: number;
    }>(
      `SELECT n.id AS narrative_id,
              ${loc === 'de' ? 'COALESCE(n.name_de, n.name_en)' : 'n.name_en'} AS narrative_name,
              ${loc === 'de' ? 'COALESCE(n.claim_de, n.claim_en)' : 'n.claim_en'} AS narrative_claim,
              n.actor_centroids,
              n.tier,
              n.narrative_type,
              n.framing_keywords,
              n.publishers,
              ${loc === 'de' ? 'COALESCE(fnn.stance_label_de, fnn.stance_label_en)' : 'fnn.stance_label_en'} AS stance_label,
              fnn.display_order
       FROM friction_node_narratives fnn
       JOIN narratives_v2 n ON n.id = fnn.narrative_id
       WHERE fnn.fn_id = $1 AND n.is_active = true
       ORDER BY fnn.display_order`,
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
      `SELECT narrative_id FROM friction_node_narratives
       WHERE fn_id = $1 ORDER BY display_order`,
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
 * Recent events on this FN.
 *
 * Tightened filter: the EVENT'S OWN canonical title must be substantively
 * about the FN, not just contain some member title that mentions it.
 * For Iran nuclear specifically: title must have an Iran-marker
 * (Iran/Tehran/Iranian) AND a nuclear-domain word (nuclear/enrichment/
 * uranium/atomic/centrifuge), OR a site/program name that's Iran-specific
 * (Natanz/Fordow/Bushehr/Arak/JCPOA).
 *
 * The hardcoded predicate is FN2-specific. When more FNs land we'll
 * want this to be configurable per-FN (e.g. via a JSONB column on
 * friction_nodes carrying a "title-match grammar"). For now a single
 * branch keyed off the slug.
 *
 * source_count comes from event_v3_titles (events_v3.summary_source_count
 * is NULL on events that haven't been through the LLM describe step).
 */
export async function getFrictionNodeRecentEvents(
  slug: string,
  locale?: string,
  limit = 12,
): Promise<FnRecentEvent[]> {
  const loc = locale2(locale);
  return cached(`fn_recent_events:${slug}:${loc}:${limit}`, TTL, async () => {
    // FN-specific event-title gate (hardcoded for now — see docstring).
    // event_friction_nodes is now itself the strict set (bootstrap applies
    // the FN-specific title gate at link time), so no extra title filter
    // needed in the page query.
    return query<FnRecentEvent>(
      `SELECT e.id::text,
              e.date::text,
              ${loc === 'de' ? 'COALESCE(e.title_de, e.title)' : 'e.title'} AS title,
              (SELECT COUNT(DISTINCT t.publisher_name)
                 FROM event_v3_titles et
                 JOIN titles_v3 t ON t.id = et.title_id
                 WHERE et.event_id = e.id)::int AS source_count,
              e.importance_score AS importance
       FROM event_friction_nodes efn
       JOIN events_v3 e ON e.id = efn.event_id
       WHERE efn.fn_id = $1
         AND e.is_promoted = true
         AND e.merged_into IS NULL
       ORDER BY (SELECT COUNT(*) FROM event_v3_titles et WHERE et.event_id = e.id) DESC,
                e.date DESC
       LIMIT $2`,
      [slug, limit],
    );
  });
}

/**
 * Weekly event volume on this FN. Buckets by ISO week (Monday).
 * Currently unused on the page (replaced by getFrictionNodeEventsByWeek
 * which returns total + events together) but kept for any caller that
 * just wants counts.
 */
export async function getFrictionNodeEventVolume(
  slug: string,
): Promise<FnEventVolumePoint[]> {
  return cached(`fn_event_volume:${slug}`, TTL, async () => {
    return query<FnEventVolumePoint>(
      `SELECT to_char(date_trunc('week', e.date::timestamp), 'YYYY-MM-DD') AS week,
              COUNT(*)::int AS count
       FROM event_friction_nodes efn
       JOIN events_v3 e ON e.id = efn.event_id
       WHERE efn.fn_id = $1
       GROUP BY 1
       ORDER BY 1`,
      [slug],
    );
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
 * Other friction nodes that share >=2 narratives with this FN.
 * The "theater grouping" concept from the concept doc — when several
 * FNs are contested by the same narrative coalitions, they form a
 * cluster worth navigating across.
 *
 * With only one FN in the system this returns []. Empty state on the
 * page is fine; the function exposes the structure for when more FNs land.
 */
export async function getRelatedFrictionNodes(
  slug: string,
  locale?: string,
): Promise<RelatedFn[]> {
  const loc = locale2(locale);
  return cached(`fn_related:${slug}:${loc}`, TTL, async () => {
    return query<RelatedFn>(
      `WITH this_narratives AS (
         SELECT narrative_id FROM friction_node_narratives WHERE fn_id = $1
       )
       SELECT fn.id,
              ${loc === 'de' ? 'COALESCE(fn.name_de, fn.name_en)' : 'fn.name_en'} AS name,
              COUNT(fnn.narrative_id)::int AS shared_narratives
       FROM friction_node_narratives fnn
       JOIN friction_nodes fn ON fn.id = fnn.fn_id
       WHERE fnn.narrative_id IN (SELECT narrative_id FROM this_narratives)
         AND fnn.fn_id != $1
         AND fn.is_active = true
       GROUP BY fn.id, fn.name_en, fn.name_de
       HAVING COUNT(fnn.narrative_id) >= 2
       ORDER BY shared_narratives DESC, name`,
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
    return query<FrictionNode>(
      `SELECT id,
              ${loc === 'de' ? 'COALESCE(name_de, name_en)' : 'name_en'} AS name,
              ${loc === 'de' ? 'COALESCE(description_de, description_en)' : 'description_en'} AS description,
              ${loc === 'de' ? 'COALESCE(editorial_summary_de, editorial_summary_en)' : 'editorial_summary_en'} AS editorial_summary,
              centroid_ids,
              topic_keywords
       FROM friction_nodes
       WHERE is_active = true
       ORDER BY display_order NULLS LAST, name_en`,
    );
  });
}
