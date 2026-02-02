import { query } from './db';
import { Centroid, CTM, Title, TitleAssignment, Feed, Event } from './types';

export async function getAllCentroids(): Promise<Centroid[]> {
  return query<Centroid>(
    'SELECT * FROM centroids_v3 WHERE is_active = true ORDER BY class, label'
  );
}

export async function getCentroidById(id: string): Promise<Centroid | null> {
  const results = await query<Centroid>(
    'SELECT id, label, class, primary_theater, is_active, iso_codes, track_config_id, description, profile_json, updated_at FROM centroids_v3 WHERE id = $1 AND is_active = true',
    [id]
  );
  return results[0] || null;
}

export async function getCentroidsByIds(ids: string[]): Promise<Centroid[]> {
  if (ids.length === 0) return [];
  return query<Centroid>(
    'SELECT id, label, class, primary_theater, is_active, iso_codes FROM centroids_v3 WHERE id = ANY($1)',
    [ids]
  );
}

export async function getCentroidsByClass(centroidClass: 'geo' | 'systemic'): Promise<Centroid[]> {
  return query<Centroid>(
    `SELECT
      c.*,
      COALESCE((SELECT SUM(title_count) FROM ctm WHERE ctm.centroid_id = c.id), 0)::int as article_count,
      (
        SELECT COUNT(DISTINCT t.publisher_name)
        FROM ctm
        JOIN title_assignments ta ON ctm.id = ta.ctm_id
        JOIN titles_v3 t ON ta.title_id = t.id
        WHERE ctm.centroid_id = c.id AND t.publisher_name IS NOT NULL
      )::int as source_count,
      (
        SELECT COUNT(DISTINCT t.detected_language)
        FROM ctm
        JOIN title_assignments ta ON ctm.id = ta.ctm_id
        JOIN titles_v3 t ON ta.title_id = t.id
        WHERE ctm.centroid_id = c.id AND t.detected_language IS NOT NULL
      )::int as language_count,
      (
        SELECT MAX(t.pubdate_utc)
        FROM ctm
        JOIN title_assignments ta ON ctm.id = ta.ctm_id
        JOIN titles_v3 t ON ta.title_id = t.id
        WHERE ctm.centroid_id = c.id
      ) as last_article_date
     FROM centroids_v3 c
     WHERE c.class = $1 AND c.is_active = true
     ORDER BY c.label`,
    [centroidClass]
  );
}

export async function getCentroidsByTheater(theater: string): Promise<Centroid[]> {
  return query<Centroid>(
    `SELECT
      c.*,
      COALESCE((SELECT SUM(title_count) FROM ctm WHERE ctm.centroid_id = c.id), 0)::int as article_count,
      (
        SELECT COUNT(DISTINCT t.publisher_name)
        FROM ctm
        JOIN title_assignments ta ON ctm.id = ta.ctm_id
        JOIN titles_v3 t ON ta.title_id = t.id
        WHERE ctm.centroid_id = c.id AND t.publisher_name IS NOT NULL
      )::int as source_count,
      (
        SELECT COUNT(DISTINCT t.detected_language)
        FROM ctm
        JOIN title_assignments ta ON ctm.id = ta.ctm_id
        JOIN titles_v3 t ON ta.title_id = t.id
        WHERE ctm.centroid_id = c.id AND t.detected_language IS NOT NULL
      )::int as language_count,
      (
        SELECT MAX(t.pubdate_utc)
        FROM ctm
        JOIN title_assignments ta ON ctm.id = ta.ctm_id
        JOIN titles_v3 t ON ta.title_id = t.id
        WHERE ctm.centroid_id = c.id
      ) as last_article_date
     FROM centroids_v3 c
     WHERE c.primary_theater = $1 AND c.is_active = true
     ORDER BY c.label`,
    [theater]
  );
}

export async function getCTMsByCentroid(centroidId: string): Promise<CTM[]> {
  return query<CTM>(
    `SELECT * FROM ctm
     WHERE centroid_id = $1
     ORDER BY month DESC, track`,
    [centroidId]
  );
}

/**
 * Fetch events from events_v3 normalized tables
 * Returns events in same format as events_digest JSONB with bucket metadata
 */
async function getEventsFromV3(ctmId: string): Promise<Event[]> {
  const results = await query<{
    id: string;
    date: string;
    last_active: string | null;
    title: string | null;
    summary: string;
    tags: string[] | null;
    source_title_ids: string[];
    event_type: string | null;
    bucket_key: string | null;
    source_batch_count: number;
    is_catchall: boolean;
  }>(
    `SELECT
      e.id,
      e.date::text as date,
      e.last_active::text as last_active,
      e.title,
      e.summary,
      e.tags,
      e.event_type,
      e.bucket_key,
      e.source_batch_count,
      e.is_catchall,
      array_agg(evt.title_id ORDER BY evt.title_id) as source_title_ids
    FROM events_v3 e
    LEFT JOIN event_v3_titles evt ON e.id = evt.event_id
    WHERE e.ctm_id = $1
    GROUP BY e.id, e.date, e.last_active, e.title, e.summary, e.tags, e.event_type, e.bucket_key, e.source_batch_count, e.is_catchall
    ORDER BY e.is_catchall ASC, e.source_batch_count DESC`,
    [ctmId]
  );

  return results.map(r => ({
    date: r.date,
    last_active: r.last_active || undefined,
    title: r.title || undefined,
    summary: r.summary,
    tags: r.tags || undefined,
    event_id: r.id,
    source_title_ids: r.source_title_ids.filter(id => id !== null),
    event_type: r.event_type as Event['event_type'],
    bucket_key: r.bucket_key,
    source_count: r.source_batch_count,
    is_catchall: r.is_catchall,
  }));
}

export async function getCTM(
  centroidId: string,
  track: string,
  month?: string
): Promise<CTM | null> {
  let queryText = `
    SELECT * FROM ctm
    WHERE centroid_id = $1 AND track = $2
  `;

  const params: any[] = [centroidId, track];

  if (month) {
    queryText += ` AND TO_CHAR(month, 'YYYY-MM') = $3`;
    params.push(month);
  } else {
    queryText += ' ORDER BY month DESC LIMIT 1';
  }

  const results = await query<CTM>(queryText, params);
  const ctm = results[0] || null;

  if (ctm) {
    ctm.events_digest = await getEventsFromV3(ctm.id);
  }

  return ctm;
}

export async function getCTMMonths(centroidId: string, track: string): Promise<string[]> {
  const results = await query<{ month: string }>(
    `SELECT DISTINCT TO_CHAR(month, 'YYYY-MM') as month FROM ctm
     WHERE centroid_id = $1 AND track = $2
     ORDER BY month DESC`,
    [centroidId, track]
  );
  return results.map(r => r.month);
}

export async function getTitlesByCTM(ctmId: string): Promise<Title[]> {
  return query<Title>(
    `SELECT t.* FROM titles_v3 t
     JOIN title_assignments ta ON t.id = ta.title_id
     WHERE ta.ctm_id = $1
     ORDER BY t.pubdate_utc DESC`,
    [ctmId]
  );
}

export async function getTracksByCentroid(centroidId: string): Promise<string[]> {
  const results = await query<{ track: string }>(
    `SELECT DISTINCT track FROM ctm
     WHERE centroid_id = $1
     ORDER BY track`,
    [centroidId]
  );
  return results.map(r => r.track);
}

export async function getCentroidsWithTrack(track: string): Promise<Centroid[]> {
  return query<Centroid>(
    `SELECT DISTINCT c.* FROM centroids_v3 c
     JOIN ctm ON c.id = ctm.centroid_id
     WHERE ctm.track = $1 AND c.is_active = true
     ORDER BY c.class, c.label`,
    [track]
  );
}

export async function getLatestCTMMonth(): Promise<string | null> {
  const results = await query<{ month: Date }>(
    'SELECT MAX(month) as month FROM ctm'
  );
  if (!results[0]?.month) return null;
  const date = new Date(results[0].month);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
}

export async function getTrackSummaryByCentroid(
  centroidId: string
): Promise<Array<{ track: string; latestMonth: string; totalTitles: number }>> {
  const results = await query<{ track: string; latest_month: string; title_count: number }>(
    `SELECT
      c.track,
      TO_CHAR(MAX(c.month), 'YYYY-MM') as latest_month,
      COUNT(DISTINCT ta.title_id)::int as title_count
    FROM ctm c
    LEFT JOIN title_assignments ta ON c.id = ta.ctm_id
    WHERE c.centroid_id = $1
      AND c.is_frozen = false
    GROUP BY c.track
    ORDER BY MAX(c.month) DESC`,
    [centroidId]
  );

  return results.map(r => ({
    track: r.track,
    latestMonth: r.latest_month,
    totalTitles: r.title_count,
  }));
}

export async function getAllActiveFeeds(): Promise<Feed[]> {
  return query<Feed>(
    `SELECT id, name, url, language_code, country_code, source_domain, is_active
     FROM feeds
     WHERE is_active = true
     ORDER BY country_code, name`
  );
}

export async function getOverlappingCentroids(centroidId: string): Promise<Array<Centroid & { overlap_count: number }>> {
  return query<Centroid & { overlap_count: number }>(
    `SELECT
      c.id, c.label, c.class, c.primary_theater,
      COUNT(DISTINCT t.id) as overlap_count
     FROM centroids_v3 c
     JOIN title_assignments ta1 ON c.id = ta1.centroid_id
     JOIN titles_v3 t ON ta1.title_id = t.id
     WHERE t.id IN (
       SELECT title_id
       FROM title_assignments
       WHERE centroid_id = $1
     )
     AND c.id != $1
     AND c.is_active = true
     GROUP BY c.id, c.label, c.class, c.primary_theater
     ORDER BY overlap_count DESC
     LIMIT 10`,
    [centroidId]
  );
}

export async function getOverlappingCentroidsForTrack(
  centroidId: string,
  track: string
): Promise<Array<Centroid & { overlap_count: number }>> {
  return query<Centroid & { overlap_count: number }>(
    `SELECT
      c.id, c.label, c.class, c.primary_theater,
      COUNT(DISTINCT t.id) as overlap_count
     FROM centroids_v3 c
     JOIN title_assignments ta1 ON c.id = ta1.centroid_id AND ta1.track = $2
     JOIN titles_v3 t ON ta1.title_id = t.id
     WHERE t.id IN (
       SELECT title_id
       FROM title_assignments
       WHERE centroid_id = $1 AND track = $2
     )
     AND c.id != $1
     AND c.is_active = true
     GROUP BY c.id, c.label, c.class, c.primary_theater
     ORDER BY overlap_count DESC
     LIMIT 10`,
    [centroidId, track]
  );
}

/**
 * Get all months that have any CTM data for a centroid (across all tracks)
 */
export async function getAvailableMonthsForCentroid(centroidId: string): Promise<string[]> {
  const results = await query<{ month: string }>(
    `SELECT DISTINCT TO_CHAR(month, 'YYYY-MM') as month
     FROM ctm
     WHERE centroid_id = $1
     ORDER BY month DESC`,
    [centroidId]
  );
  return results.map(r => r.month);
}

/**
 * Get track summary for a specific month
 */
export async function getTrackSummaryByCentroidAndMonth(
  centroidId: string,
  month: string
): Promise<Array<{ track: string; titleCount: number }>> {
  const results = await query<{ track: string; title_count: number }>(
    `SELECT
      c.track,
      COUNT(DISTINCT ta.title_id)::int as title_count
    FROM ctm c
    LEFT JOIN title_assignments ta ON c.id = ta.ctm_id
    WHERE c.centroid_id = $1
      AND TO_CHAR(c.month, 'YYYY-MM') = $2
    GROUP BY c.track
    ORDER BY c.track`,
    [centroidId, month]
  );

  return results.map(r => ({
    track: r.track,
    titleCount: r.title_count,
  }));
}

/**
 * Get centroid-level cross-track summary for a given month
 */
export async function getCentroidMonthlySummary(
  centroidId: string,
  month: string
): Promise<{ summary_text: string; track_count: number; total_events: number } | null> {
  const results = await query<{ summary_text: string; track_count: number; total_events: number }>(
    `SELECT summary_text, track_count, total_events
     FROM centroid_monthly_summaries
     WHERE centroid_id = $1 AND TO_CHAR(month, 'YYYY-MM') = $2`,
    [centroidId, month]
  );
  return results[0] || null;
}

/**
 * Get all configured tracks for a centroid from track_configs
 */
export async function getConfiguredTracksForCentroid(centroidId: string): Promise<string[]> {
  // First try to get tracks from the centroid's assigned track_config
  const results = await query<{ tracks: string[] }>(
    `SELECT tc.tracks
     FROM centroids_v3 c
     JOIN track_configs tc ON c.track_config_id = tc.id
     WHERE c.id = $1`,
    [centroidId]
  );

  if (results.length > 0 && results[0].tracks) {
    return results[0].tracks;
  }

  // Fall back to default track_config
  const defaultResults = await query<{ tracks: string[] }>(
    `SELECT tracks FROM track_configs WHERE is_default = TRUE`
  );

  if (defaultResults.length > 0 && defaultResults[0].tracks) {
    return defaultResults[0].tracks;
  }

  return [];
}
