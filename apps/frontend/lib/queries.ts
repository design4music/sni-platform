import { query } from './db';
import { Centroid, CTM, Title, TitleAssignment, Feed, Event, Epic, EpicEvent, EpicCentroidStat, TopSignal, SignalType, FramedNarrative } from './types';

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
      COALESCE(e.title, e.topic_core) as title,
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
    GROUP BY e.id, e.date, e.last_active, e.title, e.topic_core, e.summary, e.tags, e.event_type, e.bucket_key, e.source_batch_count, e.is_catchall
    ORDER BY e.is_catchall ASC, e.source_batch_count DESC`,
    [ctmId]
  );

  return results.map(r => ({
    date: r.date,
    last_active: r.last_active || undefined,
    title: r.title || undefined,
    summary: r.summary || '',
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

export async function getAllActiveFeeds(): Promise<(Feed & { total_titles: number; assigned_titles: number })[]> {
  return query<Feed & { total_titles: number; assigned_titles: number }>(
    `WITH publisher_map(feed_name, publisher_name) AS (VALUES
       ('Al-Ahram', 'Ahram Online'), ('Al-Ahram', 'بوابة الأهرام'), ('Al-Ahram', 'الأهرام اوتو'),
       ('Al Arabiya', 'العربية'), ('Al Arabiya', 'Al Arabiya English'),
       ('Al Jazeera', 'الجزيرة نت'),
       ('Anadolu Agency', 'Anadolu Ajansı'),
       ('ABC News', 'Australian Broadcasting Corporation'), ('ABC News', 'ABC iview'),
       ('Associated Press', 'AP News'), ('AFP', 'AFP Fact Check'),
       ('Asahi Shimbun', '朝日新聞'),
       ('BBC World', 'BBC'),
       ('CGTN', 'news.cgtn.com'), ('CGTN', 'newsaf.cgtn.com'),
       ('Channel NewsAsia', 'CNA'),
       ('Clarín', 'Clarin.com'),
       ('CTV News', 'CTV'),
       ('Daily Mirror', 'Daily Mirror - Sri Lanka'),
       ('Daily Star', 'The Daily Star'),
       ('Deutsche Welle', 'dw.com'), ('Deutsche Welle', 'DW.com'), ('Deutsche Welle', 'DW'),
       ('El País', 'EL PAÍS'), ('El País', 'EL PAÍS English'),
       ('EurActiv', 'Euractiv'),
       ('Euronews', 'Euronews.com'),
       ('Express Tribune', 'The Express Tribune'),
       ('Fars News', 'farsnews.ir'), ('Fars News', 'Fars News Agency'),
       ('Frankfurter Allgemeine', 'FAZ'),
       ('Globe and Mail', 'The Globe and Mail'),
       ('Indian Express', 'The Indian Express'),
       ('Jakarta Post', 'The Jakarta Post'),
       ('Japan Times', 'The Japan Times'),
       ('Jerusalem Post', 'The Jerusalem Post'), ('Jerusalem Post', 'jpost.com'),
       ('KBS World', 'KBS WORLD Radio'),
       ('Korea Herald', 'The Korea Herald'), ('Korea Herald', 'koreaherald.com'),
       ('Kyodo News', 'Japan Wire by KYODO NEWS'),
       ('La Repubblica', 'la Repubblica'), ('La Repubblica', 'Corriere Tv'), ('La Repubblica', 'Corriere Roma'),
       ('Le Monde', 'Le Monde.fr'),
       ('New Straits Times', 'NST Online'),
       ('New York Times', 'The New York Times'), ('New York Times', 'nytimes.com'),
       ('NHK World', 'nhk.or.jp'),
       ('O Estado de S. Paulo', 'Estadão'), ('O Estado de S. Paulo', 'Estadão E-Investidor'),
       ('People''s Daily', 'People''s Daily Online'),
       ('Philippine Daily Inquirer', 'Inquirer.net'), ('Philippine Daily Inquirer', 'INQUIRER.net USA'), ('Philippine Daily Inquirer', 'Cebu Daily News'),
       ('Punch', 'Punch Newspapers'),
       ('Republic TV', 'republic.tv'),
       ('Sputnik', 'sputniknews.com'),
       ('Süddeutsche Zeitung', 'SZ.de'), ('Süddeutsche Zeitung', 'SZ Immobilienmarkt'),
       ('Sydney Morning Herald', 'The Sydney Morning Herald'), ('Sydney Morning Herald', 'SMH.com.au'),
       ('Tasnim News', 'tasnimnews.com'),
       ('TASS', 'tass.com'),
       ('The National', 'thenationalnews.com'),
       ('The News', 'The News International'),
       ('The Standard', 'standardmedia.co.ke'),
       ('Times of Israel', 'The Times of Israel'), ('Times of Israel', 'timesofisrael.com'),
       ('Ukraine World', 'UkraineWorld'),
       ('Vanguard', 'Vanguard News'),
       ('Vietnam News', 'vietnamnews.vn'),
       ('VN Express', 'VnExpress International'),
       ('Voice of America', 'VOA - Voice of America English News'),
       ('Wall Street Journal', 'The Wall Street Journal'),
       ('Washington Post', 'The Washington Post'),
       ('Xinhua', 'Xinhuanet Deutsch'),
       ('Yonhap', 'Yonhap News Agency')
     ),
     feed_publishers AS (
       SELECT feed_name, publisher_name FROM publisher_map
       UNION ALL
       SELECT name, name FROM feeds WHERE is_active = true
     ),
     stats AS (
       SELECT fp.feed_name,
         SUM(s.total)::int as total,
         SUM(s.assigned)::int as assigned
       FROM feed_publishers fp
       JOIN (
         SELECT publisher_name, COUNT(*) as total,
           COUNT(CASE WHEN processing_status = 'assigned' THEN 1 END) as assigned
         FROM titles_v3 WHERE publisher_name IS NOT NULL
         GROUP BY publisher_name
       ) s ON s.publisher_name = fp.publisher_name
       GROUP BY fp.feed_name
     )
     SELECT f.id, f.name, f.url, f.language_code, f.country_code, f.source_domain, f.is_active,
       COALESCE(st.total, 0)::int as total_titles,
       COALESCE(st.assigned, 0)::int as assigned_titles
     FROM feeds f
     LEFT JOIN stats st ON st.feed_name = f.name
     WHERE f.is_active = true
     ORDER BY f.country_code, f.name`
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

// ========================================================================
// Epic queries
// ========================================================================

export async function getEpicMonths(): Promise<string[]> {
  const results = await query<{ month: string }>(
    "SELECT DISTINCT TO_CHAR(month, 'YYYY-MM') as month FROM epics ORDER BY month DESC"
  );
  return results.map(r => r.month);
}

export async function getEpicsByMonth(month: string): Promise<Epic[]> {
  return query<Epic>(
    `SELECT id, slug, TO_CHAR(month, 'YYYY-MM') as month, title, summary,
            anchor_tags, centroid_count, event_count, total_sources
     FROM epics
     WHERE TO_CHAR(month, 'YYYY-MM') = $1
     ORDER BY total_sources DESC`,
    [month]
  );
}

export async function getEpicBySlug(slug: string): Promise<Epic | null> {
  const results = await query<Epic>(
    `SELECT id, slug, TO_CHAR(month, 'YYYY-MM') as month, title, summary,
            anchor_tags, centroid_count, event_count, total_sources,
            timeline, narratives, centroid_summaries
     FROM epics
     WHERE slug = $1`,
    [slug]
  );
  return results[0] || null;
}

export async function getEpicEvents(epicId: string): Promise<EpicEvent[]> {
  return query<EpicEvent>(
    `SELECT e.id as event_id, e.title, e.summary, e.tags,
            e.source_batch_count, e.date::text as date,
            c.centroid_id, c.track,
            cv.label as centroid_label,
            cv.iso_codes
     FROM epic_events ee
     JOIN events_v3 e ON ee.event_id = e.id
     JOIN ctm c ON e.ctm_id = c.id
     JOIN centroids_v3 cv ON c.centroid_id = cv.id
     WHERE ee.epic_id = $1 AND ee.is_included = true
     ORDER BY cv.label, e.source_batch_count DESC`,
    [epicId]
  );
}

export async function getEpicCentroidBreakdown(epicId: string): Promise<EpicCentroidStat[]> {
  return query<EpicCentroidStat>(
    `SELECT c.centroid_id, cv.label as centroid_label,
            COUNT(*)::int as event_count,
            SUM(e.source_batch_count)::int as total_sources,
            cv.iso_codes
     FROM epic_events ee
     JOIN events_v3 e ON ee.event_id = e.id
     JOIN ctm c ON e.ctm_id = c.id
     JOIN centroids_v3 cv ON c.centroid_id = cv.id
     WHERE ee.epic_id = $1 AND ee.is_included = true
     GROUP BY c.centroid_id, cv.label, cv.iso_codes
     ORDER BY total_sources DESC`,
    [epicId]
  );
}

export async function getLatestEpics(limit: number = 3): Promise<Epic[]> {
  return query<Epic>(
    `SELECT id, slug, TO_CHAR(month, 'YYYY-MM') as month, title, summary,
            anchor_tags, centroid_count, event_count, total_sources
     FROM epics
     WHERE month = (SELECT MAX(month) FROM epics)
     ORDER BY total_sources DESC
     LIMIT $1`,
    [limit]
  );
}

export async function getEpicFramedNarratives(epicId: string): Promise<FramedNarrative[]> {
  return query<FramedNarrative>(
    `SELECT id, label, description, moral_frame, title_count,
            top_sources, proportional_sources, top_countries, sample_titles,
            rai_adequacy, rai_synthesis, rai_conflicts, rai_blind_spots,
            rai_shifts, rai_full_analysis, rai_analyzed_at::text
     FROM epic_narratives
     WHERE epic_id = $1
     ORDER BY title_count DESC`,
    [epicId]
  );
}

// ========================================================================
// Signal ranking queries
// ========================================================================

const SIGNAL_COLUMNS: SignalType[] = ['persons', 'orgs', 'places', 'commodities', 'policies', 'systems', 'named_events'];

export async function getTopSignalsByMonth(month: string, limit: number = 5): Promise<Record<SignalType, TopSignal[]>> {
  // Try pre-computed rankings first (has LLM context)
  const precomputed = await query<TopSignal>(
    `SELECT signal_type, value, count, context
     FROM monthly_signal_rankings
     WHERE month = ($1 || '-01')::date
     ORDER BY signal_type, rank`,
    [month]
  );

  if (precomputed.length > 0) {
    const result = {} as Record<SignalType, TopSignal[]>;
    for (const col of SIGNAL_COLUMNS) {
      result[col] = precomputed.filter(r => r.signal_type === col);
    }
    return result;
  }

  // Fallback: live query (no context)
  const parts = SIGNAL_COLUMNS.map(col =>
    `SELECT '${col}' as signal_type, val as value, COUNT(*)::int as count
     FROM title_labels tl
     JOIN titles_v3 t ON t.id = tl.title_id
     CROSS JOIN LATERAL unnest(tl.${col}) AS val
     WHERE t.pubdate_utc >= ($1 || '-01')::date
       AND t.pubdate_utc < (($1 || '-01')::date + INTERVAL '1 month')
     GROUP BY val ORDER BY count DESC LIMIT ${limit}`
  );

  const sql = parts.map(p => `(${p})`).join(' UNION ALL ');
  const rows = await query<TopSignal>(sql, [month]);

  const result = {} as Record<SignalType, TopSignal[]>;
  for (const col of SIGNAL_COLUMNS) {
    result[col] = rows.filter(r => r.signal_type === col);
  }
  return result;
}
