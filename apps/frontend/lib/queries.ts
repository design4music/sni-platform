import { query } from './db';
import { cached } from './cache';
import { Centroid, CTM, Title, TitleAssignment, Feed, Event, Epic, EpicEvent, EpicCentroidStat, TopSignal, SignalType, FramedNarrative, NarrativeDetail, EventDetail, RelatedEvent, OutletProfile, OutletNarrativeFrame, SearchResult, TrendingEvent, TrendingSignal, SignalNode, SignalEdge, SignalWeekly, SignalProfile, SignalCategoryEntry, SignalGraph, RelationshipCluster } from './types';

export async function getAllCentroids(): Promise<Centroid[]> {
  return cached('centroids:all', 300, () =>
    query<Centroid>(
      'SELECT * FROM centroids_v3 WHERE is_active = true ORDER BY class, label'
    )
  );
}

export async function getCentroidById(id: string): Promise<Centroid | null> {
  return cached(`centroid:${id}`, 300, async () => {
    const results = await query<Centroid>(
      'SELECT id, label, class, primary_theater, is_active, iso_codes, track_config_id, description, profile_json, updated_at FROM centroids_v3 WHERE id = $1 AND is_active = true',
      [id]
    );
    return results[0] || null;
  });
}

export async function getCentroidsByIds(ids: string[]): Promise<Centroid[]> {
  if (ids.length === 0) return [];
  return query<Centroid>(
    'SELECT id, label, class, primary_theater, is_active, iso_codes FROM centroids_v3 WHERE id = ANY($1)',
    [ids]
  );
}

export async function getCentroidsByClass(centroidClass: 'geo' | 'systemic'): Promise<Centroid[]> {
  return cached(`centroids:class:${centroidClass}`, 300, () =>
    query<Centroid>(
      `WITH centroid_stats AS (
        SELECT
          ctm.centroid_id,
          COUNT(DISTINCT t.id)::int AS article_count,
          COUNT(DISTINCT t.publisher_name) FILTER (WHERE t.publisher_name IS NOT NULL)::int AS source_count,
          COUNT(DISTINCT t.detected_language) FILTER (WHERE t.detected_language IS NOT NULL)::int AS language_count,
          MAX(t.pubdate_utc) AS last_article_date
        FROM ctm
        JOIN title_assignments ta ON ctm.id = ta.ctm_id
        JOIN titles_v3 t ON ta.title_id = t.id
        GROUP BY ctm.centroid_id
      )
      SELECT c.*,
        COALESCE(cs.article_count, 0) AS article_count,
        COALESCE(cs.source_count, 0) AS source_count,
        COALESCE(cs.language_count, 0) AS language_count,
        cs.last_article_date
      FROM centroids_v3 c
      LEFT JOIN centroid_stats cs ON cs.centroid_id = c.id
      WHERE c.class = $1 AND c.is_active = true
      ORDER BY c.label`,
      [centroidClass]
    )
  );
}

export async function getCentroidsByTheater(theater: string): Promise<Centroid[]> {
  return cached(`centroids:theater:${theater}`, 300, () =>
    query<Centroid>(
      `WITH centroid_stats AS (
        SELECT
          ctm.centroid_id,
          COUNT(DISTINCT t.id)::int AS article_count,
          COUNT(DISTINCT t.publisher_name) FILTER (WHERE t.publisher_name IS NOT NULL)::int AS source_count,
          COUNT(DISTINCT t.detected_language) FILTER (WHERE t.detected_language IS NOT NULL)::int AS language_count,
          MAX(t.pubdate_utc) AS last_article_date
        FROM ctm
        JOIN title_assignments ta ON ctm.id = ta.ctm_id
        JOIN titles_v3 t ON ta.title_id = t.id
        GROUP BY ctm.centroid_id
      )
      SELECT c.*,
        COALESCE(cs.article_count, 0) AS article_count,
        COALESCE(cs.source_count, 0) AS source_count,
        COALESCE(cs.language_count, 0) AS language_count,
        cs.last_article_date
      FROM centroids_v3 c
      LEFT JOIN centroid_stats cs ON cs.centroid_id = c.id
      WHERE c.primary_theater = $1 AND c.is_active = true
      ORDER BY c.label`,
      [theater]
    )
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
    has_narratives: boolean;
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
      EXISTS (SELECT 1 FROM narratives n WHERE n.entity_type = 'event' AND n.entity_id = e.id) as has_narratives,
      array_agg(evt.title_id ORDER BY evt.title_id) as source_title_ids
    FROM events_v3 e
    LEFT JOIN event_v3_titles evt ON e.id = evt.event_id
    WHERE e.ctm_id = $1 AND e.source_batch_count > 0
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
    has_narratives: r.has_narratives,
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

export async function getMonthTimeline(
  centroidId: string, track: string
): Promise<{ month: string; title_count: number; is_frozen: boolean }[]> {
  return query<{ month: string; title_count: number; is_frozen: boolean }>(
    `SELECT TO_CHAR(month, 'YYYY-MM') as month, title_count, is_frozen
     FROM ctm
     WHERE centroid_id = $1 AND track = $2
     ORDER BY month DESC`,
    [centroidId, track]
  );
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

/** Publisher name -> feed name normalization. Maps variant publisher_names to canonical feed names. */
const PUBLISHER_MAP_VALUES = `
  ('ABC News', 'Australian Broadcasting Corporation'), ('ABC News', 'ABC iview'),
  ('AFP', 'AFP Fact Check'), ('AFP', 'afp.com'),
  ('Al-Ahram', 'Ahram Online'), ('Al-Ahram', 'بوابة الأهرام'), ('Al-Ahram', 'الأهرام اوتو'),
  ('Al Arabiya', 'العربية'), ('Al Arabiya', 'Al Arabiya English'), ('Al Arabiya', 'alarabiya.net'),
  ('Al Jazeera', 'الجزيرة نت'),
  ('Anadolu Agency', 'Anadolu Ajansı'), ('Anadolu Agency', 'AA.com.tr'),
  ('Antara News', 'ANTARA News'),
  ('Asahi Shimbun', '朝日新聞'),
  ('Associated Press', 'AP News'), ('Associated Press', 'Associated Press News'),
  ('Bangkok Post', 'bangkokpost.com'),
  ('BBC World', 'BBC'),
  ('BelTA', 'BelTA – News'),
  ('BelTA Russian', 'БелТА'),
  ('Bloomberg', 'Bloomberg.com'),
  ('BRICS Info', 'infobrics.org'),
  ('Carnegie Endowment', 'Carnegie Endowment for International Peace'),
  ('CBC', 'CBC Gem'),
  ('CGTN', 'news.cgtn.com'), ('CGTN', 'newsaf.cgtn.com'), ('CGTN', 'newsus.cgtn.com'),
  ('Channel NewsAsia', 'CNA'), ('Channel NewsAsia', 'CNA Lifestyle'),
  ('China Daily', 'China Daily - Global Edition'),
  ('Clarín', 'Clarin.com'),
  ('CNN', 'cnn.com'),
  ('Copenhagen Post', 'The Copenhagen Post'),
  ('Corriere della Sera', 'corriere.it'), ('Corriere della Sera', 'Corriere Milano'),
  ('Corriere della Sera', 'Corriere Tv'), ('Corriere della Sera', 'Corriere Roma'),
  ('CSIS', 'CSIS | Center for Strategic and International Studies'),
  ('CTV News', 'CTV'), ('CTV News', 'CTV More'),
  ('Daily Mirror', 'Daily Mirror - Sri Lanka'),
  ('Daily Nation', 'nation.africa'),
  ('Daily Sabah', 'dailysabah.com'),
  ('Daily Star', 'The Daily Star'),
  ('Der Spiegel', 'Spiegel'),
  ('Deutsche Welle', 'dw.com'), ('Deutsche Welle', 'DW.com'), ('Deutsche Welle', 'DW'),
  ('Dhaka Tribune', 'dhakatribune.com'),
  ('Die Presse', 'DiePresse.com'),
  ('Die Zeit', 'DIE ZEIT'),
  ('DR', 'dr.dk'), ('DR', 'DR.dk'),
  ('Egypt Today', 'egypttoday.com'),
  ('eKathimerini', 'eKathimerini.com'),
  ('El País', 'EL PAÍS'), ('El País', 'EL PAÍS English'), ('El País', 'elpais.com'),
  ('ERR News', 'ERR'), ('ERR News', 'news | ERR'),
  ('EurActiv', 'Euractiv'),
  ('Euronews', 'Euronews.com'),
  ('Express Tribune', 'The Express Tribune'),
  ('Fars News', 'farsnews.ir'), ('Fars News', 'Fars News Agency'), ('Fars News', 'خبرگزاری فارس'),
  ('Folha de S.Paulo', 'UOL'),
  ('Fox News', 'foxnews.com'),
  ('Frankfurter Allgemeine', 'FAZ'),
  ('Gazeta.ru', 'gazeta.ru'),
  ('Globe and Mail', 'The Globe and Mail'),
  ('Gulf News', 'gulfnews.com'),
  ('Gulf Times', 'gulf-times.com'),
  ('i24NEWS', 'i24news.tv'),
  ('IISS', 'The International Institute for Strategic Studies'),
  ('Indian Express', 'The Indian Express'),
  ('IRNA', 'IRNA English'),
  ('Izvestia', 'iz.ru'), ('Izvestia', 'en.iz.ru'),
  ('Jakarta Globe', 'jakartaglobe.id'),
  ('Jakarta Post', 'The Jakarta Post'),
  ('Japan Times', 'The Japan Times'),
  ('Jerusalem Post', 'The Jerusalem Post'), ('Jerusalem Post', 'jpost.com'),
  ('KBS World', 'KBS WORLD Radio'), ('KBS World', '대한민국 대표 공영미디어 KBS'),
  ('Khaleej Times', 'khaleejtimes.com'),
  ('Kommersant', 'kommersant.ru'),
  ('Korea Herald', 'The Korea Herald'), ('Korea Herald', 'koreaherald.com'),
  ('Kyiv Post', 'kyivpost.com'),
  ('Kyodo News', 'Japan Wire by KYODO NEWS'),
  ('La Repubblica', 'la Repubblica'), ('La Repubblica', 'repubblica.it'),
  ('Le Monde', 'Le Monde.fr'),
  ('Lenta.ru', 'lenta.ru'),
  ('LRT English', 'LRT'),
  ('LSM English', 'LSM'), ('LSM English', 'LSM.lv'),
  ('Mail & Guardian', 'The Mail & Guardian'),
  ('MIA', 'Mia.mk'), ('MIA', 'Медиумска информативна агенција'),
  ('Moldova Live', 'MoldovaLive.md'),
  ('N1 Serbia', 'N1'), ('N1 Serbia', 'Forbes Srbija'), ('N1 Serbia', 'Sportklub'),
  ('NDTV', 'NDTV Sports'),
  ('New Straits Times', 'NST Online'),
  ('New York Times', 'The New York Times'), ('New York Times', 'nytimes.com'),
  ('NHK World', 'nhk.or.jp'),
  ('Novinite', 'Novinite.com'), ('Novinite', 'Novinite.com - Sofia News Agency'),
  ('NRK', 'NRK TV'),
  ('NZZ', 'Neue Zürcher Zeitung'),
  ('O Estado de S. Paulo', 'Estadão'), ('O Estado de S. Paulo', 'Estadão E-Investidor'),
  ('O Globo', 'oglobo.globo.com'),
  ('OilPrice', 'Crude Oil Prices Today | OilPrice.com'),
  ('People''s Daily', 'People''s Daily Online'),
  ('Philippine Daily Inquirer', 'Inquirer.net'), ('Philippine Daily Inquirer', 'INQUIRER.net USA'), ('Philippine Daily Inquirer', 'Cebu Daily News'),
  ('Polska Agencja Prasowa', 'Polska Agencja Prasowa SA'), ('Polska Agencja Prasowa', 'PAP Biznes'),
  ('Press TV', 'PressTV'),
  ('Punch', 'Punch Newspapers'),
  ('Republic TV', 'republic.tv'),
  ('RIA Novosti', 'ria.ru'),
  ('Slovak Spectator', 'The Slovak Spectator'),
  ('Sputnik', 'sputniknews.com'),
  ('Süddeutsche Zeitung', 'SZ.de'), ('Süddeutsche Zeitung', 'SZ Immobilienmarkt'), ('Süddeutsche Zeitung', 'sueddeutsche.de'),
  ('Swissinfo', 'SWI swissinfo.ch'),
  ('Sydney Morning Herald', 'The Sydney Morning Herald'), ('Sydney Morning Herald', 'SMH.com.au'),
  ('Tagesschau', 'tagesschau.de'),
  ('Tasnim News', 'tasnimnews.com'),
  ('TASS', 'tass.com'),
  ('TASS Russian', 'tass.ru'),
  ('Tengrinews', 'Tengrinews.kz'),
  ('The Astana Times', 'astanatimes.com'),
  ('The Hindu', 'thehindu.com'),
  ('The National', 'thenationalnews.com'),
  ('The News', 'The News International'),
  ('The Standard', 'standardmedia.co.ke'),
  ('Times of India', 'The Times of India'),
  ('Times of Israel', 'The Times of Israel'), ('Times of Israel', 'timesofisrael.com'),
  ('Ukraine World', 'UkraineWorld'),
  ('UN News', 'news.un.org'),
  ('Vanguard', 'Vanguard News'),
  ('Vietnam News', 'vietnamnews.vn'),
  ('Vijesti', 'Vijesti.me'),
  ('VN Express', 'VnExpress International'), ('VN Express', 'e.vnexpress.net'),
  ('Voice of America', 'VOA - Voice of America English News'),
  ('Wall Street Journal', 'The Wall Street Journal'), ('Wall Street Journal', 'WSJ'),
  ('Washington Post', 'The Washington Post'), ('Washington Post', 'washingtonpost.com'),
  ('Wired', 'WIRED'),
  ('Xinhua', 'Xinhuanet Deutsch'),
  ('YLE News', 'Yle'), ('YLE News', 'yle.fi'),
  ('Yonhap', 'Yonhap News Agency'), ('Yonhap', 'en.yna.co.kr')`;

export async function getAllActiveFeeds(): Promise<(Feed & { total_titles: number; assigned_titles: number })[]> {
  return cached('feeds:active', 600, () => query<Feed & { total_titles: number; assigned_titles: number }>(
    `WITH publisher_map(feed_name, publisher_name) AS (VALUES
  ${PUBLISHER_MAP_VALUES}
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
  ));
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
  return cached(`overlap:${centroidId}:${track}`, 600, () =>
    query<Centroid & { overlap_count: number }>(
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
    )
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
): Promise<Array<{ track: string; titleCount: number; lastActive: string | null }>> {
  const results = await query<{ track: string; title_count: number; last_active: string | null }>(
    `SELECT
      c.track,
      COUNT(DISTINCT ta.title_id)::int as title_count,
      MAX(e.last_active)::text as last_active
    FROM ctm c
    LEFT JOIN title_assignments ta ON c.id = ta.ctm_id
    LEFT JOIN events_v3 e ON e.ctm_id = c.id
    WHERE c.centroid_id = $1
      AND TO_CHAR(c.month, 'YYYY-MM') = $2
    GROUP BY c.track
    ORDER BY c.track`,
    [centroidId, month]
  );

  return results.map(r => ({
    track: r.track,
    titleCount: r.title_count,
    lastActive: r.last_active,
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
  return cached('epic:months', 600, async () => {
    const results = await query<{ month: string }>(
      "SELECT DISTINCT TO_CHAR(month, 'YYYY-MM') as month FROM epics ORDER BY month DESC"
    );
    return results.map(r => r.month);
  });
}

export async function getEpicsByMonth(month: string): Promise<Epic[]> {
  return cached(`epics:month:${month}`, 300, () =>
    query<Epic>(
      `SELECT id, slug, TO_CHAR(month, 'YYYY-MM') as month, title, summary,
              anchor_tags, centroid_count, event_count, total_sources
       FROM epics
       WHERE TO_CHAR(month, 'YYYY-MM') = $1
       ORDER BY total_sources DESC`,
      [month]
    )
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

export async function getAllEpicSlugs(): Promise<string[]> {
  const results = await query<{ slug: string }>('SELECT slug FROM epics');
  return results.map(r => r.slug);
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
  return cached(`epics:latest:${limit}`, 300, () =>
    query<Epic>(
      `SELECT id, slug, TO_CHAR(month, 'YYYY-MM') as month, title, summary,
              anchor_tags, centroid_count, event_count, total_sources
       FROM epics
       WHERE month = (SELECT MAX(month) FROM epics)
       ORDER BY total_sources DESC
       LIMIT $1`,
      [limit]
    )
  );
}

export async function getEpicFramedNarratives(epicId: string): Promise<FramedNarrative[]> {
  return query<FramedNarrative>(
    `SELECT id, label, description, moral_frame, title_count,
            top_sources, proportional_sources, top_countries, sample_titles,
            rai_adequacy, rai_synthesis, rai_conflicts, rai_blind_spots,
            rai_shifts, rai_full_analysis, rai_analyzed_at::text,
            signal_stats, rai_signals, rai_signals_at::text
     FROM narratives
     WHERE entity_type = 'epic' AND entity_id = $1
     ORDER BY title_count DESC`,
    [epicId]
  );
}

// ========================================================================
// Generic narrative + event detail queries
// ========================================================================

export async function getNarrativeById(id: string): Promise<NarrativeDetail | null> {
  const results = await query<NarrativeDetail>(
    `SELECT n.id, n.label, n.moral_frame, n.description, n.title_count,
            n.sample_titles, n.top_sources, n.proportional_sources, n.top_countries,
            n.entity_type, n.entity_id,
            n.signal_stats, n.rai_signals, n.rai_signals_at::text,
            n.rai_full_analysis, n.rai_adequacy, n.rai_synthesis,
            n.rai_conflicts, n.rai_blind_spots, n.rai_shifts, n.rai_analyzed_at::text,
            COALESCE(ct.centroid_id, c.centroid_id) as centroid_id,
            c2.label as centroid_name,
            COALESCE(ct.track, c.track) as track,
            COALESCE(e.title, e.topic_core) as event_title,
            e.id as event_id
     FROM narratives n
     LEFT JOIN events_v3 e ON n.entity_type = 'event' AND n.entity_id = e.id
     LEFT JOIN ctm ct ON n.entity_type = 'event' AND e.ctm_id = ct.id
     LEFT JOIN ctm c ON n.entity_type = 'ctm' AND n.entity_id = c.id
     LEFT JOIN centroids_v3 c2 ON c2.id = COALESCE(ct.centroid_id, c.centroid_id)
     WHERE n.id = $1`,
    [id]
  );
  return results[0] || null;
}

export async function getFramedNarratives(
  entityType: string, entityId: string
): Promise<FramedNarrative[]> {
  return query<FramedNarrative>(
    `SELECT id, label, description, moral_frame, title_count,
            top_sources, proportional_sources, top_countries, sample_titles,
            rai_adequacy, rai_synthesis, rai_conflicts, rai_blind_spots,
            rai_shifts, rai_full_analysis, rai_analyzed_at::text,
            signal_stats, rai_signals, rai_signals_at::text
     FROM narratives
     WHERE entity_type = $1 AND entity_id = $2
     ORDER BY title_count DESC`,
    [entityType, entityId]
  );
}

export async function getSiblingNarratives(
  entityType: string, entityId: string
): Promise<Array<{ id: string; label: string }>> {
  return query<{ id: string; label: string }>(
    `SELECT id, label FROM narratives
     WHERE entity_type = $1 AND entity_id = $2
     ORDER BY title_count DESC`,
    [entityType, entityId]
  );
}

export async function getEventById(eventId: string): Promise<EventDetail | null> {
  const results = await query<EventDetail>(
    `SELECT
      e.id,
      e.date::text as date,
      e.last_active::text as last_active,
      COALESCE(e.title, e.topic_core) as title,
      e.summary,
      e.tags,
      e.source_batch_count,
      e.event_type,
      e.bucket_key,
      e.saga,
      c.id as ctm_id,
      c.centroid_id,
      cv.label as centroid_label,
      c.track,
      TO_CHAR(c.month, 'YYYY-MM') as month,
      e.coherence_check
    FROM events_v3 e
    JOIN ctm c ON e.ctm_id = c.id
    JOIN centroids_v3 cv ON c.centroid_id = cv.id
    WHERE e.id = $1`,
    [eventId]
  );
  return results[0] || null;
}

export async function getEventSagaSiblings(
  saga: string, currentEventId: string
): Promise<Array<{ id: string; title: string; date: string; source_batch_count: number; month: string }>> {
  return query<{ id: string; title: string; date: string; source_batch_count: number; month: string }>(
    `SELECT e.id, COALESCE(e.title, e.topic_core) as title, e.date::text,
            e.source_batch_count, TO_CHAR(c.month, 'YYYY-MM') as month
     FROM events_v3 e
     JOIN ctm c ON e.ctm_id = c.id
     WHERE e.saga = $1 AND e.id != $2
     ORDER BY e.date ASC`,
    [saga, currentEventId]
  );
}

export async function getEventTitles(eventId: string): Promise<Title[]> {
  return query<Title>(
    `SELECT t.id, t.title_display, t.url_gnews, t.publisher_name,
            t.pubdate_utc, t.detected_language, t.processing_status
     FROM event_v3_titles et
     JOIN titles_v3 t ON et.title_id = t.id
     WHERE et.event_id = $1
     ORDER BY t.pubdate_utc DESC`,
    [eventId]
  );
}

export async function getRelatedEvents(
  eventId: string, centroidId: string, minShared: number = 5
): Promise<RelatedEvent[]> {
  return query<RelatedEvent>(
    `WITH this_titles AS (
       SELECT title_id FROM event_v3_titles WHERE event_id = $1
     )
     SELECT e2.id, e2.title, e2.source_batch_count,
            c2.centroid_id, cv.label as centroid_label, cv.iso_codes,
            c2.track,
            COUNT(DISTINCT et2.title_id)::int as shared_titles
     FROM this_titles tt
     JOIN event_v3_titles et2 ON tt.title_id = et2.title_id
     JOIN events_v3 e2 ON et2.event_id = e2.id
     JOIN ctm c2 ON e2.ctm_id = c2.id
     JOIN centroids_v3 cv ON c2.centroid_id = cv.id
     WHERE c2.centroid_id <> $2
       AND e2.is_catchall = false
     GROUP BY e2.id, e2.title, e2.source_batch_count,
              c2.centroid_id, cv.label, cv.iso_codes, c2.track
     HAVING COUNT(DISTINCT et2.title_id) >= $3
     ORDER BY shared_titles DESC
     LIMIT 10`,
    [eventId, centroidId, minShared]
  );
}

// ========================================================================
// Signal ranking queries
// ========================================================================

const SIGNAL_COLUMNS: SignalType[] = ['persons', 'orgs', 'places', 'commodities', 'policies', 'systems', 'named_events'];

export async function getTopSignalsByMonth(month: string, limit: number = 5): Promise<Record<SignalType, TopSignal[]>> {
  return cached(`signals:${month}`, 600, async () => {
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
  });
}

// ========================================================================
// Outlet profile queries
// ========================================================================

function feedPubsCTE(): string {
  return `WITH publisher_map(feed_name, publisher_name) AS (VALUES
  ${PUBLISHER_MAP_VALUES}
  ),
  feed_pubs AS (
    SELECT publisher_name FROM publisher_map WHERE feed_name = $1
    UNION ALL SELECT $1
  )`;
}

export async function getOutletProfile(feedName: string): Promise<OutletProfile | null> {
  const feedResults = await query<Feed>(
    'SELECT id, name, url, language_code, country_code, source_domain, is_active FROM feeds WHERE name = $1 LIMIT 1',
    [feedName]
  );
  if (feedResults.length === 0) return null;
  const feed = feedResults[0];

  const cte = feedPubsCTE();

  const [coverageRes, ctmsRes, countRes] = await Promise.all([
    query<{ centroid_id: string; label: string; count: number }>(
      `${cte}
       SELECT ta.centroid_id, cv.label, COUNT(*)::int as count
       FROM titles_v3 t
       JOIN feed_pubs fp ON t.publisher_name = fp.publisher_name
       JOIN title_assignments ta ON ta.title_id = t.id
       JOIN centroids_v3 cv ON cv.id = ta.centroid_id
       GROUP BY ta.centroid_id, cv.label
       ORDER BY count DESC`,
      [feedName]
    ),
    query<{ ctm_id: string; centroid_id: string; track: string; month: string; label: string; count: number }>(
      `${cte}
       SELECT ta.ctm_id, c.centroid_id, c.track, TO_CHAR(c.month, 'YYYY-MM') as month,
              cv.label, COUNT(*)::int as count
       FROM titles_v3 t
       JOIN feed_pubs fp ON t.publisher_name = fp.publisher_name
       JOIN title_assignments ta ON ta.title_id = t.id
       JOIN ctm c ON c.id = ta.ctm_id
       JOIN centroids_v3 cv ON cv.id = c.centroid_id
       GROUP BY ta.ctm_id, c.centroid_id, c.track, c.month, cv.label
       ORDER BY count DESC
       LIMIT 20`,
      [feedName]
    ),
    query<{ count: number }>(
      `${cte}
       SELECT COUNT(*)::int as count FROM titles_v3 t
       JOIN feed_pubs fp ON t.publisher_name = fp.publisher_name`,
      [feedName]
    ),
  ]);

  return {
    feed_name: feed.name,
    source_domain: feed.source_domain || null,
    country_code: feed.country_code || null,
    language_code: feed.language_code || null,
    article_count: countRes[0]?.count || 0,
    centroid_coverage: coverageRes,
    top_ctms: ctmsRes,
  };
}

export async function getOutletNarrativeFrames(feedName: string): Promise<OutletNarrativeFrame[]> {
  return query<OutletNarrativeFrame>(
    `${feedPubsCTE()}
     SELECT n.entity_type, n.entity_id, n.label, n.description, n.title_count,
            COALESCE(e.title, cv.label || ' / ' || c.track) as entity_label
     FROM narratives n
     LEFT JOIN events_v3 e ON n.entity_type = 'event' AND n.entity_id = e.id
     LEFT JOIN ctm c ON n.entity_type = 'ctm' AND n.entity_id = c.id
     LEFT JOIN centroids_v3 cv ON cv.id = c.centroid_id
     WHERE EXISTS (
       SELECT 1 FROM feed_pubs fp WHERE fp.publisher_name = ANY(n.top_sources)
     )
     ORDER BY n.title_count DESC
     LIMIT 30`,
    [feedName]
  );
}

// ========================================================================
// Trending events (time-decayed source count)
// ========================================================================

export async function getTrendingEvents(limit: number = 20): Promise<TrendingEvent[]> {
  return cached(`trending:${limit}`, 300, () =>
    query<TrendingEvent>(
      `SELECT e.id, COALESCE(e.title, e.topic_core) as title,
              e.date::text as date, COALESCE(e.last_active, e.date)::text as last_active,
              e.source_batch_count, COALESCE(e.tags, '{}') as tags,
              LEFT(e.summary, 200) as summary,
              c.centroid_id, cv.label as centroid_label, cv.iso_codes,
              c.track,
              (e.source_batch_count
               * pow(0.5, EXTRACT(EPOCH FROM (NOW() - COALESCE(e.last_active, e.date)::timestamp)) / (3 * 86400))
               * CASE WHEN EXTRACT(EPOCH FROM (NOW() - e.date::timestamp)) < 86400
                      THEN 1 + LEAST(e.source_batch_count / GREATEST(EXTRACT(EPOCH FROM (NOW() - e.date::timestamp)) / 3600, 1), 3)
                      ELSE 1 END
              )::numeric(10,2) as trending_score,
              sig.top_signals
       FROM events_v3 e
       JOIN ctm c ON e.ctm_id = c.id
       JOIN centroids_v3 cv ON c.centroid_id = cv.id
       LEFT JOIN LATERAL (
         SELECT array_agg(sig_type || ':' || val ORDER BY cnt DESC) as top_signals
         FROM (
           SELECT sig_type, val, COUNT(*) as cnt FROM (
             SELECT 'persons' as sig_type, unnest(COALESCE(tl.persons, '{}')) as val
             FROM event_v3_titles evt
             JOIN title_labels tl ON tl.title_id = evt.title_id
             WHERE evt.event_id = e.id
             UNION ALL
             SELECT 'orgs' as sig_type, unnest(COALESCE(tl.orgs, '{}')) as val
             FROM event_v3_titles evt
             JOIN title_labels tl ON tl.title_id = evt.title_id
             WHERE evt.event_id = e.id
           ) expanded
           GROUP BY sig_type, val
           ORDER BY cnt DESC
           LIMIT 3
         ) sub
       ) sig ON true
       WHERE e.source_batch_count >= 5
         AND e.is_catchall = false
         AND COALESCE(e.last_active, e.date) >= CURRENT_DATE - INTERVAL '14 days'
         AND c.is_frozen = false
       ORDER BY trending_score DESC
       LIMIT $1`,
      [limit]
    )
  );
}

export async function getTrendingSignals(): Promise<Record<string, TrendingSignal[]>> {
  return cached('trending:signals', 300, async () => {
    const types = ['persons', 'orgs', 'places', 'commodities', 'policies'] as const;
    const parts = types.map(col =>
      `SELECT '${col}' as signal_type, val as value, COUNT(DISTINCT evt.event_id)::int as event_count
       FROM events_v3 e
       JOIN ctm c ON e.ctm_id = c.id
       JOIN event_v3_titles evt ON evt.event_id = e.id
       JOIN title_labels tl ON tl.title_id = evt.title_id
       CROSS JOIN LATERAL unnest(tl.${col}) AS val
       WHERE e.source_batch_count >= 5
         AND e.is_catchall = false
         AND COALESCE(e.last_active, e.date) >= CURRENT_DATE - INTERVAL '14 days'
         AND c.is_frozen = false
       GROUP BY val ORDER BY event_count DESC LIMIT 8`
    );

    const sql = parts.map(p => `(${p})`).join(' UNION ALL ');
    const rows = await query<TrendingSignal>(sql);

    const result: Record<string, TrendingSignal[]> = {};
    for (const col of types) {
      result[col] = rows.filter(r => r.signal_type === col);
    }
    return result;
  });
}

// ========================================================================
// Signal Observatory queries
// ========================================================================

const SIGNAL_COLUMNS_SET = new Set(SIGNAL_COLUMNS);

function signalDateRange(month?: string) {
  if (month) {
    return {
      clause: `e.date >= ($1 || '-01')::date AND e.date < (($1 || '-01')::date + INTERVAL '1 month')`,
      params: [month] as unknown[],
      nextIdx: 2,
    };
  }
  return {
    clause: `e.date >= CURRENT_DATE - INTERVAL '30 days'`,
    params: [] as unknown[],
    nextIdx: 1,
  };
}

// Unnest lateral fragment reused in co-occurrence queries
const UNNEST_ALL_SIGNALS = SIGNAL_COLUMNS.map(col =>
  `SELECT '${col}'::text as sig_type, unnest(COALESCE(tl.${col}, '{}')) as value`
).join(' UNION ALL ');

/** Top N signals per type (nodes for observatory + category index) */
export async function getTopSignalsAll(perType: number = 8, month?: string): Promise<SignalNode[]> {
  const dr = signalDateRange(month);
  return cached(`signals:all:${perType}:${month || 'rolling'}`, 3600, () => {
    const sql = SIGNAL_COLUMNS.map(col =>
      `(SELECT '${col}' as signal_type, val as value, COUNT(DISTINCT evt.event_id)::int as event_count
        FROM events_v3 e
        JOIN event_v3_titles evt ON evt.event_id = e.id
        JOIN title_labels tl ON tl.title_id = evt.title_id
        CROSS JOIN LATERAL unnest(tl.${col}) AS val
        WHERE ${dr.clause} AND e.is_catchall = false
        GROUP BY val ORDER BY event_count DESC LIMIT ${perType})`
    ).join(' UNION ALL ');
    return query<SignalNode>(sql, dr.params);
  });
}

/** Full profile for a single signal (detail page) */
export async function getSignalProfile(
  type: SignalType,
  value: string,
  month?: string,
): Promise<SignalProfile> {
  if (!SIGNAL_COLUMNS_SET.has(type)) throw new Error('Invalid signal type');
  return cached(`signal-profile:${type}:${value}:${month || 'rolling'}`, 3600, async () => {
  const dr = signalDateRange(month);
  const vi = dr.nextIdx; // param index for signalValue
  const params = [...dr.params, value];

  const existsFilter = `
    EXISTS (
      SELECT 1 FROM event_v3_titles evt
      JOIN title_labels tl ON tl.title_id = evt.title_id
      WHERE evt.event_id = e.id AND $${vi} = ANY(tl.${type})
    )`;

  const [totalRow, weekly, geo, tracks, contextRow, relationshipClusters] = await Promise.all([
    // Total event count
    query<{ total: number }>(
      `SELECT COUNT(*)::int as total FROM events_v3 e
       WHERE ${dr.clause} AND e.is_catchall = false AND ${existsFilter}`,
      params
    ),
    // Weekly mentions
    query<SignalWeekly>(
      `SELECT date_trunc('week', e.date)::date::text as week, COUNT(*)::int as count
       FROM events_v3 e
       WHERE ${dr.clause} AND e.is_catchall = false AND ${existsFilter}
       GROUP BY week ORDER BY week`,
      params
    ),
    // Geographic distribution (via centroid iso_codes)
    query<{ country: string; count: number }>(
      `SELECT unnest(cv.iso_codes) as country, COUNT(DISTINCT e.id)::int as count
       FROM events_v3 e
       JOIN ctm c ON e.ctm_id = c.id
       JOIN centroids_v3 cv ON c.centroid_id = cv.id
       WHERE ${dr.clause} AND e.is_catchall = false AND ${existsFilter}
       GROUP BY country ORDER BY count DESC LIMIT 20`,
      params
    ),
    // Track breakdown
    query<{ track: string; count: number }>(
      `SELECT c.track, COUNT(DISTINCT e.id)::int as count
       FROM events_v3 e
       JOIN ctm c ON e.ctm_id = c.id
       WHERE ${dr.clause} AND e.is_catchall = false AND ${existsFilter}
       GROUP BY c.track ORDER BY count DESC`,
      params
    ),
    // Context from monthly_signal_rankings
    query<{ context: string }>(
      `SELECT context FROM monthly_signal_rankings
       WHERE signal_type = '${type}' AND LOWER(value) = LOWER($1)
       ORDER BY month DESC LIMIT 1`,
      [value]
    ),
    // Relationship clusters: top co-occurring signals enriched with shared events
    // 20% density filter on BOTH the primary signal AND each co-signal per event,
    // so displayed events genuinely involve both signals (not just a passing mention)
    query<RelationshipCluster>(
      `WITH signal_events AS (
         SELECT e.id, COALESCE(e.title, e.topic_core) as title,
                e.date::text as date, e.source_batch_count
         FROM events_v3 e
         WHERE ${dr.clause} AND e.is_catchall = false AND (
           SELECT COUNT(*) FILTER (WHERE $${vi} = ANY(tl.${type}))::float
                  / GREATEST(COUNT(*), 1)
           FROM event_v3_titles evt
           JOIN title_labels tl ON tl.title_id = evt.title_id
           WHERE evt.event_id = e.id
         ) >= 0.2
       ),
       event_cosigs AS (
         SELECT se.id as event_id, expanded.sig_type as signal_type, expanded.value
         FROM signal_events se
         JOIN event_v3_titles evt ON evt.event_id = se.id
         JOIN title_labels tl ON tl.title_id = evt.title_id
         CROSS JOIN LATERAL (${UNNEST_ALL_SIGNALS}) expanded(sig_type, value)
         WHERE NOT (expanded.sig_type = '${type}' AND expanded.value = $${vi})
         GROUP BY se.id, expanded.sig_type, expanded.value
         HAVING COUNT(*)::float / GREATEST((SELECT COUNT(*) FROM event_v3_titles e2 WHERE e2.event_id = se.id), 1) >= 0.2
       ),
       top_cosigs AS (
         SELECT signal_type, value, COUNT(DISTINCT event_id)::int as event_count
         FROM event_cosigs
         GROUP BY signal_type, value
         HAVING COUNT(DISTINCT event_id) >= 2
         ORDER BY event_count DESC LIMIT 20
       ),
       title_deduped AS (
         SELECT tc.signal_type, tc.value, tc.event_count,
                se.id, se.title, se.date, se.source_batch_count,
                ROW_NUMBER() OVER (PARTITION BY tc.signal_type, tc.value, se.title ORDER BY se.source_batch_count DESC) as title_pick
         FROM top_cosigs tc
         JOIN event_cosigs ec ON ec.signal_type = tc.signal_type AND ec.value = tc.value
         JOIN signal_events se ON se.id = ec.event_id
       ),
       ranked AS (
         SELECT signal_type, value, event_count, id, title, date, source_batch_count,
                ROW_NUMBER() OVER (PARTITION BY signal_type, value ORDER BY source_batch_count DESC) as rn
         FROM title_deduped WHERE title_pick = 1
       )
       SELECT signal_type, value, event_count,
              MAX(title) FILTER (WHERE rn = 1) as label,
              json_agg(json_build_object(
                'id', id, 'title', title, 'date', date,
                'source_batch_count', source_batch_count
              ) ORDER BY source_batch_count DESC) FILTER (WHERE rn <= 3) as top_events
       FROM ranked
       GROUP BY signal_type, value, event_count
       ORDER BY event_count DESC`,
      params
    ),
  ]);

  return {
    signal_type: type,
    value,
    total_events: totalRow[0]?.total ?? 0,
    context: contextRow[0]?.context,
    weekly,
    geo,
    tracks,
    relationship_clusters: relationshipClusters,
  };
  });
}

/** Co-occurrence graph: nodes + edges for top signals (observatory) */
export async function getSignalGraph(perType: number = 8, month?: string): Promise<SignalGraph> {
  const dr = signalDateRange(month);
  return cached(`signal-graph:${perType}:${month || 'rolling'}`, 3600, async () => {
    const nodes = await getTopSignalsAll(perType, month);

    // Build CTE for top signals, then find co-occurrence edges
    const topCTEs = SIGNAL_COLUMNS.map(col =>
      `top_${col} AS (
        SELECT '${col}'::text as signal_type, val as value
        FROM events_v3 e
        JOIN event_v3_titles evt ON evt.event_id = e.id
        JOIN title_labels tl ON tl.title_id = evt.title_id
        CROSS JOIN LATERAL unnest(tl.${col}) AS val
        WHERE ${dr.clause} AND e.is_catchall = false
        GROUP BY val ORDER BY COUNT(DISTINCT evt.event_id) DESC LIMIT ${perType}
      )`
    );
    const allTopUnion = SIGNAL_COLUMNS.map(col =>
      `SELECT * FROM top_${col}`
    ).join(' UNION ALL ');

    const edgesSQL = `
      WITH ${topCTEs.join(',\n')},
      all_top AS (${allTopUnion}),
      event_sigs AS (
        SELECT DISTINCT evt.event_id, expanded.sig_type as signal_type, expanded.value
        FROM event_v3_titles evt
        JOIN title_labels tl ON tl.title_id = evt.title_id
        JOIN events_v3 e ON e.id = evt.event_id
        CROSS JOIN LATERAL (${UNNEST_ALL_SIGNALS}) expanded(sig_type, value)
        WHERE ${dr.clause} AND e.is_catchall = false
          AND EXISTS (SELECT 1 FROM all_top WHERE all_top.signal_type = expanded.sig_type AND all_top.value = expanded.value)
      )
      SELECT a.value as source, b.value as target,
             a.signal_type as source_type, b.signal_type as target_type,
             COUNT(DISTINCT a.event_id)::int as weight
      FROM event_sigs a
      JOIN event_sigs b ON a.event_id = b.event_id
        AND (a.value, a.signal_type) < (b.value, b.signal_type)
      GROUP BY source, target, source_type, target_type
      HAVING COUNT(DISTINCT a.event_id) >= 3
      ORDER BY weight DESC`;

    const edges = await query<SignalEdge>(edgesSQL, dr.params);
    return { nodes, edges };
  });
}

/** Top signals for an epic's events (epic detail widget) */
export async function getTopSignalsForEpic(epicId: string, limit: number = 10): Promise<SignalNode[]> {
  return cached(`signals:epic:${epicId}:${limit}`, 600, () => {
    const perType = Math.max(limit, 5);
    const sql = SIGNAL_COLUMNS.slice(0, 5).map(col =>
      `(SELECT '${col}' as signal_type, val as value, COUNT(DISTINCT evt.event_id)::int as event_count
        FROM epic_events ee
        JOIN event_v3_titles evt ON evt.event_id = ee.event_id
        JOIN title_labels tl ON tl.title_id = evt.title_id
        CROSS JOIN LATERAL unnest(tl.${col}) AS val
        WHERE ee.epic_id = $1 AND ee.is_included = true
        GROUP BY val ORDER BY event_count DESC LIMIT ${perType})`
    ).join(' UNION ALL ');
    return query<SignalNode>(
      `SELECT * FROM (${sql}) sub ORDER BY event_count DESC LIMIT ${limit}`,
      [epicId]
    );
  });
}

/** Top signals for a specific centroid (country profile widget) */
export async function getTopSignalsForCentroid(centroidId: string, limit: number = 5): Promise<SignalNode[]> {
  return cached(`signals:centroid:${centroidId}:${limit}`, 300, async () => {
    const perType = Math.max(limit, 5);
    const results = await Promise.all(
      SIGNAL_COLUMNS.slice(0, 5).map(col =>
        query<SignalNode>(
          `SELECT '${col}' as signal_type, val as value, COUNT(DISTINCT evt.event_id)::int as event_count
           FROM events_v3 e
           JOIN ctm c ON e.ctm_id = c.id
           JOIN event_v3_titles evt ON evt.event_id = e.id
           JOIN title_labels tl ON tl.title_id = evt.title_id
           CROSS JOIN LATERAL unnest(tl.${col}) AS val
           WHERE c.centroid_id = $1 AND e.is_catchall = false
             AND e.date >= CURRENT_DATE - INTERVAL '30 days'
           GROUP BY val ORDER BY event_count DESC LIMIT ${perType}`,
          [centroidId]
        )
      )
    );
    return results.flat().sort((a, b) => b.event_count - a.event_count).slice(0, limit);
  });
}

/** Weekly heatmap data for top signals (observatory temporal grid) */
export async function getSignalHeatmap(perType: number = 3, month?: string): Promise<SignalCategoryEntry[]> {
  const dr = signalDateRange(month);
  return cached(`signal-heatmap:${perType}:${month || 'rolling'}`, 3600, async () => {
    const nodes = await getTopSignalsAll(perType, month);
    if (nodes.length === 0) return [];

    // Fetch weekly counts for all top signals across all types
    const weeklyParts = SIGNAL_COLUMNS.filter(col => {
      return nodes.some(n => n.signal_type === col);
    }).map(col => {
      const vals = nodes.filter(n => n.signal_type === col).map(n => n.value);
      if (vals.length === 0) return null;
      return `SELECT '${col}'::text as signal_type, val as value,
                     date_trunc('week', e.date)::date::text as week,
                     COUNT(DISTINCT e.id)::int as count
              FROM events_v3 e
              JOIN event_v3_titles evt ON evt.event_id = e.id
              JOIN title_labels tl ON tl.title_id = evt.title_id
              CROSS JOIN LATERAL unnest(tl.${col}) AS val
              WHERE ${dr.clause} AND e.is_catchall = false
                AND val = ANY($${dr.nextIdx})
              GROUP BY signal_type, val, week`;
    }).filter(Boolean);

    if (weeklyParts.length === 0) return nodes.map(n => ({ ...n, weekly: [] }));

    const allValues = nodes.map(n => n.value);
    const weeklyRows = await query<{ signal_type: string; value: string; week: string; count: number }>(
      weeklyParts.join(' UNION ALL ') + ' ORDER BY signal_type, value, week',
      [...dr.params, allValues]
    );

    const weeklyMap = new Map<string, SignalWeekly[]>();
    for (const row of weeklyRows) {
      const key = `${row.signal_type}:${row.value}`;
      if (!weeklyMap.has(key)) weeklyMap.set(key, []);
      weeklyMap.get(key)!.push({ week: row.week, count: row.count });
    }

    return nodes.map(n => ({
      ...n,
      weekly: weeklyMap.get(`${n.signal_type}:${n.value}`) || [],
    }));
  });
}

/** Category listing with sparkline data (category page) */
export async function getSignalCategoryDetail(
  type: SignalType,
  limit: number = 10,
  month?: string,
): Promise<SignalCategoryEntry[]> {
  if (!SIGNAL_COLUMNS_SET.has(type)) throw new Error('Invalid signal type');
  const dr = signalDateRange(month);

  return cached(`signal-cat:${type}:${limit}:${month || 'rolling'}`, 3600, async () => {
    // Top signals for this type
    const top = await query<{ value: string; event_count: number }>(
      `SELECT val as value, COUNT(DISTINCT evt.event_id)::int as event_count
       FROM events_v3 e
       JOIN event_v3_titles evt ON evt.event_id = e.id
       JOIN title_labels tl ON tl.title_id = evt.title_id
       CROSS JOIN LATERAL unnest(tl.${type}) AS val
       WHERE ${dr.clause} AND e.is_catchall = false
       GROUP BY val ORDER BY event_count DESC LIMIT ${limit}`,
      dr.params
    );
    if (top.length === 0) return [];

    const values = top.map(t => t.value);
    const vi = dr.nextIdx;

    // Weekly sparklines + contexts in parallel
    const [weeklyRows, contextRows] = await Promise.all([
      query<{ value: string; week: string; count: number }>(
        `SELECT val as value, date_trunc('week', e.date)::date::text as week, COUNT(DISTINCT e.id)::int as count
         FROM events_v3 e
         JOIN event_v3_titles evt ON evt.event_id = e.id
         JOIN title_labels tl ON tl.title_id = evt.title_id
         CROSS JOIN LATERAL unnest(tl.${type}) AS val
         WHERE ${dr.clause} AND e.is_catchall = false AND val = ANY($${vi})
         GROUP BY val, week ORDER BY val, week`,
        [...dr.params, values]
      ),
      query<{ value: string; context: string }>(
        `SELECT value, context FROM monthly_signal_rankings
         WHERE signal_type = $1 AND value = ANY($2)
         ORDER BY month DESC`,
        [type, values]
      ),
    ]);

    // Group weekly data by signal value
    const weeklyMap = new Map<string, SignalWeekly[]>();
    for (const row of weeklyRows) {
      if (!weeklyMap.has(row.value)) weeklyMap.set(row.value, []);
      weeklyMap.get(row.value)!.push({ week: row.week, count: row.count });
    }

    // Index contexts (case-insensitive)
    const contextMap = new Map<string, string>();
    for (const row of contextRows) {
      contextMap.set(row.value.toLowerCase(), row.context);
    }

    return top.map(t => ({
      signal_type: type,
      value: t.value,
      event_count: t.event_count,
      context: contextMap.get(t.value.toLowerCase()),
      weekly: weeklyMap.get(t.value) || [],
    }));
  });
}

// ========================================================================
// Search
// ========================================================================

export async function searchAll(q: string): Promise<SearchResult[]> {
  if (!q || q.trim().length === 0) return [];

  return query<SearchResult>(
    `WITH q AS (SELECT websearch_to_tsquery('english', $1) AS tsq)
     SELECT * FROM (
       (SELECT 'event' as type, e.id::text, COALESCE(e.title, e.topic_core) as title,
               LEFT(e.summary, 200) as snippet, e.source_batch_count as sources,
               e.date::text as date, cv.label as centroid_label, NULL as slug,
               ts_rank(to_tsvector('english', COALESCE(e.title,'') || ' ' || COALESCE(e.summary,'')), q.tsq) as rank
        FROM events_v3 e
        JOIN ctm c ON e.ctm_id = c.id
        JOIN centroids_v3 cv ON c.centroid_id = cv.id
        CROSS JOIN q
        WHERE to_tsvector('english', COALESCE(e.title,'') || ' ' || COALESCE(e.summary,'')) @@ q.tsq
        ORDER BY rank DESC LIMIT 15)
       UNION ALL
       (SELECT 'centroid' as type, cv.id, cv.label as title,
               COALESCE(cv.description,'') as snippet, NULL::int as sources,
               NULL as date, NULL as centroid_label, NULL as slug,
               ts_rank(to_tsvector('english', cv.label || ' ' || COALESCE(cv.description,'')), q.tsq) as rank
        FROM centroids_v3 cv CROSS JOIN q
        WHERE to_tsvector('english', cv.label || ' ' || COALESCE(cv.description,'')) @@ q.tsq AND cv.is_active
        ORDER BY rank DESC LIMIT 10)
       UNION ALL
       (SELECT 'epic' as type, ep.id::text, COALESCE(ep.title,'') as title,
               LEFT(COALESCE(ep.summary,''),200) as snippet, ep.total_sources as sources,
               NULL as date, NULL as centroid_label, ep.slug,
               ts_rank(to_tsvector('english', COALESCE(ep.title,'') || ' ' || COALESCE(ep.summary,'')), q.tsq) as rank
        FROM epics ep CROSS JOIN q
        WHERE to_tsvector('english', COALESCE(ep.title,'') || ' ' || COALESCE(ep.summary,'')) @@ q.tsq
        ORDER BY rank DESC LIMIT 10)
     ) sub
     ORDER BY rank DESC
     LIMIT 30`,
    [q.trim()]
  );
}
