// Shadow architecture: friction nodes + narratives_v2. (cache-bust 2026-05-07-r8-drop-gulf)
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
} from './friction-nodes-shared';
export { NARRATIVE_COLORS, colorForNarrative } from './friction-nodes-shared';

import type {
  FrictionNode,
  SampleTitle,
  NarrativeOnFn,
  FrictionNodeView,
  NarrativeWeeklyPoint,
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
      centroid_ids: string[];
      topic_keywords: string[];
    }>(
      `SELECT id,
              ${loc === 'de' ? 'COALESCE(name_de, name_en)' : 'name_en'} AS name,
              ${loc === 'de' ? 'COALESCE(description_de, description_en)' : 'description_en'} AS description,
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

export async function getActiveFrictionNodes(
  locale?: string,
): Promise<FrictionNode[]> {
  const loc = locale2(locale);
  return cached(`fn:list:${loc}`, TTL, async () => {
    return query<FrictionNode>(
      `SELECT id,
              ${loc === 'de' ? 'COALESCE(name_de, name_en)' : 'name_en'} AS name,
              ${loc === 'de' ? 'COALESCE(description_de, description_en)' : 'description_en'} AS description,
              centroid_ids,
              topic_keywords
       FROM friction_nodes
       WHERE is_active = true
       ORDER BY display_order NULLS LAST, name_en`,
    );
  });
}
