import { query } from './db';
import { Centroid, CTM, Title, TitleAssignment } from './types';

export async function getAllCentroids(): Promise<Centroid[]> {
  return query<Centroid>(
    'SELECT * FROM centroids_v3 WHERE is_active = true ORDER BY class, label'
  );
}

export async function getCentroidById(id: string): Promise<Centroid | null> {
  const results = await query<Centroid>(
    'SELECT * FROM centroids_v3 WHERE id = $1 AND is_active = true',
    [id]
  );
  return results[0] || null;
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
  return results[0] || null;
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
      track,
      TO_CHAR(MAX(month), 'YYYY-MM') as latest_month,
      SUM(title_count) as title_count
    FROM ctm
    WHERE centroid_id = $1
      AND is_frozen = false
    GROUP BY track
    ORDER BY MAX(month) DESC`,
    [centroidId]
  );

  return results.map(r => ({
    track: r.track,
    latestMonth: r.latest_month,
    totalTitles: r.title_count,
  }));
}
