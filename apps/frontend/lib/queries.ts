import { query, queryNoJIT } from './db';
import { cached } from './cache';
import { Centroid, CTM, Title, TitleAssignment, Feed, Event, Epic, EpicEvent, EpicCentroidStat, TopSignal, SignalType, FramedNarrative, EventDetail, RelatedEvent, OutletProfile, OutletNarrativeFrame, PublisherStats, StanceScore, SearchResult, TrendingEvent, TrendingSignal, SignalNode, SignalEdge, SignalWeekly, SignalDetailStats, SignalCategoryEntry, SignalGraph, RelationshipCluster, MetaNarrative, StrategicNarrative, EventNarrativeLink, NarrativeMapEntry, CalendarMonthView, CalendarDayView, CalendarClusterCard, CalendarClusterSource, CalendarStripeEntry, CalendarThemeSegment, CalendarAnalysisScope, CentroidMonthView, CentroidStripeEntry, CentroidTrackSummary, CtmThemeChip } from './types';

// Locked thresholds for the calendar-day frontend.
// See docs/FRONTEND_CALENDAR_REDESIGN.md.
const CALENDAR_EVENT_PAGE_MIN_SOURCES = 5; // K

export type Locale = 'en' | 'de';

// Helper: returns SQL expression that prefers _de column when locale is 'de'
function locCol(table: string, col: string, locale?: string): string {
  if (locale === 'de') return `COALESCE(${table}.${col}_de, ${table}.${col})`;
  return `${table}.${col}`;
}

export async function getAllCentroids(locale?: string): Promise<Centroid[]> {
  return cached(`centroids:all:${locale || 'en'}`, 3600, () =>
    query<Centroid>(
      `SELECT id, label, class, primary_theater, is_active, iso_codes, track_config_id,
              ${locCol('centroids_v3', 'description', locale)} as description,
              ${locale === 'de' ? 'COALESCE(profile_json_de, profile_json)' : 'profile_json'} as profile_json,
              updated_at
       FROM centroids_v3 WHERE is_active = true ORDER BY class, label`
    )
  );
}

export async function getCentroidById(id: string, locale?: string): Promise<Centroid | null> {
  return cached(`centroid:${id}:${locale || 'en'}`, 3600, async () => {
    const results = await query<Centroid>(
      `SELECT id, label, class, primary_theater, is_active, iso_codes, track_config_id,
              ${locCol('centroids_v3', 'description', locale)} as description,
              ${locale === 'de' ? 'COALESCE(profile_json_de, profile_json)' : 'profile_json'} as profile_json,
              updated_at
       FROM centroids_v3 WHERE id = $1 AND is_active = true`,
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

export async function getCentroidsByClass(centroidClass: 'geo' | 'systemic', locale?: string): Promise<Centroid[]> {
  return cached(`centroids:class:${centroidClass}:${locale || 'en'}`, 3600, () =>
    query<Centroid>(
      `WITH target_centroids AS (
        SELECT id FROM centroids_v3 WHERE class = $1 AND is_active = true
      ),
      centroid_stats AS (
        SELECT
          ctm.centroid_id,
          SUM(e.source_batch_count)::int AS source_count,
          SUM(CASE WHEN ctm.month = date_trunc('month', CURRENT_DATE) THEN e.source_batch_count ELSE 0 END)::int AS month_source_count,
          MAX(COALESCE(e.last_active, e.date)) AS last_article_date
        FROM ctm
        JOIN target_centroids tc ON ctm.centroid_id = tc.id
        LEFT JOIN events_v3 e ON e.ctm_id = ctm.id
        GROUP BY ctm.centroid_id
      )
      SELECT c.id, c.label, c.class, c.primary_theater, c.is_active, c.iso_codes,
        c.track_config_id, c.updated_at,
        ${locCol('c', 'description', locale)} as description,
        COALESCE(cs.source_count, 0) AS source_count,
        COALESCE(cs.month_source_count, 0) AS month_source_count,
        cs.last_article_date
      FROM centroids_v3 c
      LEFT JOIN centroid_stats cs ON cs.centroid_id = c.id
      WHERE c.class = $1 AND c.is_active = true
      ORDER BY c.label`,
      [centroidClass]
    )
  );
}

export async function getCentroidsByTheater(theater: string, locale?: string): Promise<Centroid[]> {
  return cached(`centroids:theater:${theater}:${locale || 'en'}`, 3600, () =>
    query<Centroid>(
      `WITH target_centroids AS (
        SELECT id FROM centroids_v3 WHERE primary_theater = $1 AND is_active = true
      ),
      centroid_stats AS (
        SELECT
          ctm.centroid_id,
          SUM(e.source_batch_count)::int AS source_count,
          SUM(CASE WHEN ctm.month = date_trunc('month', CURRENT_DATE) THEN e.source_batch_count ELSE 0 END)::int AS month_source_count,
          MAX(COALESCE(e.last_active, e.date)) AS last_article_date
        FROM ctm
        JOIN target_centroids tc ON ctm.centroid_id = tc.id
        LEFT JOIN events_v3 e ON e.ctm_id = ctm.id
        GROUP BY ctm.centroid_id
      )
      SELECT c.id, c.label, c.class, c.primary_theater, c.is_active, c.iso_codes,
        c.track_config_id, c.updated_at,
        ${locCol('c', 'description', locale)} as description,
        COALESCE(cs.source_count, 0) AS source_count,
        COALESCE(cs.month_source_count, 0) AS month_source_count,
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
  return cached(`ctms:centroid:${centroidId}`, 3600, () =>
    query<CTM>(
      `SELECT * FROM ctm
       WHERE centroid_id = $1
       ORDER BY month DESC, track`,
      [centroidId]
    )
  );
}

/**
 * Fetch events from events_v3 normalized tables
 * Returns events in same format as events_digest JSONB with bucket metadata
 */
async function getEventsFromV3(ctmId: string, locale?: string): Promise<Event[]> {
  return cached(`events:v3:${ctmId}:${locale || 'en'}`, 3600, async () => {
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
    importance_score: number | null;
    is_catchall: boolean;
    has_narratives: boolean;
    topic_core: string | null;
    family_id: string | null;
    family_title: string | null;
    family_domain: string | null;
    family_summary: string | null;
  }>(
    `SELECT id, date, last_active, title, summary, tags, event_type, bucket_key,
      source_batch_count, importance_score, is_catchall, has_narratives, source_title_ids, topic_core,
      family_id, family_title, family_domain, family_summary
    FROM (
      -- Native events for this CTM
      SELECT
        e.id, e.date::text as date, e.last_active::text as last_active,
        COALESCE(
          ${locale === 'de' ? 'e.title_de, ' : ''}
          e.title,
          (SELECT t2.title_display FROM event_v3_titles evt2
           JOIN titles_v3 t2 ON t2.id = evt2.title_id
           WHERE evt2.event_id = e.id
           AND (t2.detected_language = 'en' OR t2.detected_language IS NULL)
           ORDER BY t2.pubdate_utc DESC LIMIT 1),
          (SELECT t2.title_display FROM event_v3_titles evt2
           JOIN titles_v3 t2 ON t2.id = evt2.title_id
           WHERE evt2.event_id = e.id
           ORDER BY t2.pubdate_utc DESC LIMIT 1)
        ) as title,
        ${locCol('e', 'summary', locale)} as summary,
        e.tags, e.event_type, e.bucket_key, e.source_batch_count, e.importance_score,
        e.is_catchall, e.topic_core,
        e.family_id::text as family_id,
        ef.title as family_title,
        ef.domain as family_domain,
        ${locale === 'de' ? 'COALESCE(ef.summary_de, ef.summary)' : 'ef.summary'} as family_summary,
        EXISTS(SELECT 1 FROM narratives n WHERE n.entity_type = 'event' AND n.entity_id = e.id) as has_narratives,
        COALESCE((SELECT array_agg(evt.title_id ORDER BY evt.title_id) FROM event_v3_titles evt WHERE evt.event_id = e.id), '{}') as source_title_ids
      FROM events_v3 e
      LEFT JOIN event_families ef ON ef.id = e.family_id
      WHERE e.ctm_id = $1 AND e.source_batch_count > 0 AND e.merged_into IS NULL

      UNION ALL

      -- Anchor events that absorbed an event from this CTM
      SELECT
        e.id, e.date::text as date, e.last_active::text as last_active,
        COALESCE(
          ${locale === 'de' ? 'e.title_de, ' : ''}
          e.title,
          (SELECT t2.title_display FROM event_v3_titles evt2
           JOIN titles_v3 t2 ON t2.id = evt2.title_id
           WHERE evt2.event_id = e.id
           AND (t2.detected_language = 'en' OR t2.detected_language IS NULL)
           ORDER BY t2.pubdate_utc DESC LIMIT 1),
          (SELECT t2.title_display FROM event_v3_titles evt2
           JOIN titles_v3 t2 ON t2.id = evt2.title_id
           WHERE evt2.event_id = e.id
           ORDER BY t2.pubdate_utc DESC LIMIT 1)
        ) as title,
        ${locCol('e', 'summary', locale)} as summary,
        e.tags, ab.event_type, ab.bucket_key, e.source_batch_count, e.importance_score,
        e.is_catchall, e.topic_core,
        e.family_id::text as family_id,
        ef.title as family_title,
        ef.domain as family_domain,
        ${locale === 'de' ? 'COALESCE(ef.summary_de, ef.summary)' : 'ef.summary'} as family_summary,
        EXISTS(SELECT 1 FROM narratives n WHERE n.entity_type = 'event' AND n.entity_id = e.id) as has_narratives,
        COALESCE((SELECT array_agg(evt.title_id ORDER BY evt.title_id) FROM event_v3_titles evt WHERE evt.event_id = e.id), '{}') as source_title_ids
      FROM events_v3 ab
      JOIN events_v3 e ON e.id = ab.merged_into
      LEFT JOIN event_families ef ON ef.id = e.family_id
      WHERE ab.ctm_id = $1 AND ab.merged_into IS NOT NULL
        AND e.ctm_id <> $1 AND e.merged_into IS NULL AND e.source_batch_count > 0
    ) combined
    ORDER BY is_catchall ASC, CASE WHEN importance_score >= 0.5 THEN 0 ELSE 1 END, source_batch_count DESC`,
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
    importance_score: r.importance_score || undefined,
    is_catchall: r.is_catchall,
    has_narratives: r.has_narratives,
    topic_core: r.topic_core || undefined,
    family_id: r.family_id || undefined,
    family_title: r.family_title || undefined,
    family_domain: r.family_domain || undefined,
    family_summary: r.family_summary || undefined,
  }));
  });
}

export async function getCTM(
  centroidId: string,
  track: string,
  month?: string,
  locale?: string
): Promise<CTM | null> {
  return cached(`ctm:${centroidId}:${track}:${month || 'latest'}:${locale || 'en'}`, 3600, async () => {
    // When locale=de, use COALESCE for summary_text
    const summaryCol = locale === 'de'
      ? 'COALESCE(summary_text_de, summary_text) as summary_text'
      : 'summary_text';
    let queryText = `
      SELECT id, centroid_id, track, month, title_count, ${summaryCol}, is_frozen
      FROM ctm
      WHERE centroid_id = $1 AND track = $2
    `;

    const params: any[] = [centroidId, track];

    if (month) {
      queryText += ` AND month = ($3 || '-01')::date`;
      params.push(month);
    } else {
      queryText += ' ORDER BY month DESC LIMIT 1';
    }

    const results = await query<CTM>(queryText, params);
    const ctm = results[0] || null;

    if (ctm) {
      ctm.events_digest = await getEventsFromV3(ctm.id, locale);
    }

    return ctm;
  });
}

export async function getCTMMonths(centroidId: string, track: string): Promise<string[]> {
  return cached(`ctmMonths:${centroidId}:${track}`, 3600, async () => {
    const results = await query<{ month: string }>(
      `SELECT DISTINCT TO_CHAR(month, 'YYYY-MM') as month FROM ctm
       WHERE centroid_id = $1 AND track = $2
       ORDER BY month DESC`,
      [centroidId, track]
    );
    return results.map(r => r.month);
  });
}

export async function getMonthTimeline(
  centroidId: string, track: string
): Promise<{ month: string; title_count: number; is_frozen: boolean }[]> {
  return cached(`monthTimeline:${centroidId}:${track}`, 3600, () =>
    query<{ month: string; title_count: number; is_frozen: boolean }>(
      `SELECT TO_CHAR(month, 'YYYY-MM') as month, title_count, is_frozen
       FROM ctm
       WHERE centroid_id = $1 AND track = $2
       ORDER BY month DESC`,
      [centroidId, track]
    )
  );
}

export async function getTitlesByCTM(ctmId: string): Promise<Title[]> {
  return cached(`titles:ctm:${ctmId}`, 3600, () =>
    query<Title>(
      `SELECT DISTINCT t.* FROM titles_v3 t
       JOIN event_v3_titles evt ON t.id = evt.title_id
       JOIN events_v3 e ON evt.event_id = e.id
       WHERE e.ctm_id = $1
       ORDER BY t.pubdate_utc DESC`,
      [ctmId]
    )
  );
}

export async function getTracksByCentroid(centroidId: string, month?: string): Promise<string[]> {
  // Normalize month to first-of-month date format (2026-03 -> 2026-03-01)
  const monthDate = month ? (month.length === 7 ? month + '-01' : month) : undefined;
  const cacheKey = monthDate ? `tracks:centroid:${centroidId}:${monthDate}` : `tracks:centroid:${centroidId}`;
  return cached(cacheKey, 3600, async () => {
    const results = await query<{ track: string }>(
      monthDate
        ? `SELECT DISTINCT track FROM ctm
           WHERE centroid_id = $1 AND month = $2::date
           ORDER BY track`
        : `SELECT DISTINCT track FROM ctm
           WHERE centroid_id = $1 AND month = (SELECT MAX(month) FROM ctm WHERE centroid_id = $1)
           ORDER BY track`,
      monthDate ? [centroidId, monthDate] : [centroidId]
    );
    return results.map(r => r.track);
  });
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
  ('France 24', 'France24'), ('France 24', 'france24.com'),
  ('France 24 (EN)', 'France 24'),
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
  ('RT', 'rt.com'), ('RT', 'Russia Today'),
  ('Slovak Spectator', 'The Slovak Spectator'),
  ('Sputnik', 'sputniknews.com'),
  ('Süddeutsche Zeitung', 'SZ.de'), ('Süddeutsche Zeitung', 'SZ Immobilienmarkt'), ('Süddeutsche Zeitung', 'sueddeutsche.de'),
  ('Swissinfo', 'SWI swissinfo.ch'),
  ('Sydney Morning Herald', 'The Sydney Morning Herald'), ('Sydney Morning Herald', 'SMH.com.au'),
  ('Tagesschau', 'tagesschau.de'),
  ('Tasnim News', 'tasnimnews.com'),
  ('TASS (EN)', 'tass.com'),
  ('TASS', 'tass.ru'),
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
  return cached('feeds:active', 3600, () => query<Feed & { total_titles: number; assigned_titles: number }>(
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
  return cached(`overlap:${centroidId}:${track}`, 3600, () =>
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
  return cached(`months:centroid:${centroidId}`, 3600, async () => {
    const results = await query<{ month: string }>(
      `SELECT DISTINCT TO_CHAR(month, 'YYYY-MM') as month
       FROM ctm
       WHERE centroid_id = $1
       ORDER BY month DESC`,
      [centroidId]
    );
    return results.map(r => r.month);
  });
}

/**
 * Get track summary for a specific month
 */
export async function getTrackSummaryByCentroidAndMonth(
  centroidId: string,
  month: string
): Promise<Array<{ track: string; titleCount: number; lastActive: string | null }>> {
  return cached(`trackSummary:${centroidId}:${month}`, 3600, async () => {
    const results = await query<{ track: string; title_count: number; last_active: string | null }>(
      `SELECT
        c.track,
        COUNT(DISTINCT ta.title_id)::int as title_count,
        MAX(e.last_active)::text as last_active
      FROM ctm c
      LEFT JOIN title_assignments ta ON c.id = ta.ctm_id
      LEFT JOIN events_v3 e ON e.ctm_id = c.id
      WHERE c.centroid_id = $1
        AND c.month = ($2 || '-01')::date
      GROUP BY c.track
      ORDER BY c.track`,
      [centroidId, month]
    );

    return results.map(r => ({
      track: r.track,
      titleCount: r.title_count,
      lastActive: r.last_active,
    }));
  });
}

/**
 * Get centroid-level cross-track summary for a given month
 */
export async function getCentroidMonthlySummary(
  centroidId: string,
  month: string
): Promise<{ summary_text: string; track_count: number; total_events: number } | null> {
  return cached(`centroidSummary:${centroidId}:${month}`, 3600, async () => {
    const results = await query<{ summary_text: string; track_count: number; total_events: number }>(
      `SELECT summary_text, track_count, total_events
       FROM centroid_monthly_summaries
       WHERE centroid_id = $1 AND month = ($2 || '-01')::date`,
      [centroidId, month]
    );
    return results[0] || null;
  });
}

/**
 * Get all configured tracks for a centroid from track_configs
 */
export async function getConfiguredTracksForCentroid(centroidId: string): Promise<string[]> {
  return cached(`configTracks:${centroidId}`, 3600, async () => {
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
  });
}

// ========================================================================
// Epic queries
// ========================================================================

export async function getEpicMonths(): Promise<string[]> {
  return cached('epic:months', 3600, async () => {
    const results = await query<{ month: string }>(
      "SELECT DISTINCT TO_CHAR(month, 'YYYY-MM') as month FROM epics ORDER BY month DESC"
    );
    return results.map(r => r.month);
  });
}

export async function getEpicsByMonth(month: string, locale?: string): Promise<Epic[]> {
  return cached(`epics:month:${month}:${locale || 'en'}`, 3600, () =>
    query<Epic>(
      `SELECT id, slug, TO_CHAR(month, 'YYYY-MM') as month,
              ${locCol('epics', 'title', locale)} as title,
              ${locCol('epics', 'summary', locale)} as summary,
              anchor_tags, centroid_count, event_count, total_sources
       FROM epics
       WHERE TO_CHAR(month, 'YYYY-MM') = $1
       ORDER BY total_sources DESC`,
      [month]
    )
  );
}

export async function getEpicBySlug(slug: string, locale?: string): Promise<Epic | null> {
  const results = await query<Epic>(
    `SELECT id, slug, TO_CHAR(month, 'YYYY-MM') as month,
            ${locCol('epics', 'title', locale)} as title,
            ${locCol('epics', 'summary', locale)} as summary,
            anchor_tags, centroid_count, event_count, total_sources,
            ${locCol('epics', 'timeline', locale)} as timeline,
            narratives, centroid_summaries, centroid_summaries_de
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

export async function getEpicEvents(epicId: string, locale?: string): Promise<EpicEvent[]> {
  return query<EpicEvent>(
    `SELECT e.id as event_id,
            ${locCol('e', 'title', locale)} as title,
            ${locCol('e', 'summary', locale)} as summary,
            e.tags,
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

export async function getLatestEpics(limit: number = 3, locale?: string): Promise<Epic[]> {
  return cached(`epics:latest:${limit}:${locale || 'en'}`, 3600, () =>
    query<Epic>(
      `SELECT id, slug, TO_CHAR(month, 'YYYY-MM') as month,
              ${locCol('epics', 'title', locale)} as title,
              ${locCol('epics', 'summary', locale)} as summary,
              anchor_tags, centroid_count, event_count, total_sources
       FROM epics
       WHERE month = (SELECT MAX(month) FROM epics)
       ORDER BY total_sources DESC
       LIMIT $1`,
      [limit]
    )
  );
}

export async function getFramedNarratives(
  entityType: string, entityId: string, locale?: string
): Promise<FramedNarrative[]> {
  return query<FramedNarrative>(
    `SELECT id, ${locCol('narratives', 'label', locale)} as label,
            ${locCol('narratives', 'description', locale)} as description,
            ${locCol('narratives', 'moral_frame', locale)} as moral_frame,
            title_count,
            top_sources, proportional_sources, top_countries, sample_titles,
            rai_adequacy, rai_synthesis, rai_conflicts, rai_blind_spots,
            rai_shifts, rai_full_analysis, rai_analyzed_at::text,
            signal_stats, rai_signals, rai_signals_at::text,
            extraction_method, cluster_label, cluster_publishers, cluster_score_avg
     FROM narratives
     WHERE entity_type = $1 AND entity_id = $2
     ORDER BY title_count DESC`,
    [entityType, entityId]
  );
}

export interface StanceNarrative {
  id: string;
  label: string;
  description: string | null;
  moral_frame: string | null;
  title_count: number;
  cluster_label: string;
  cluster_publishers: string[];
  cluster_score_avg: number;
}

export async function getStanceNarratives(
  entityType: string, entityId: string, locale?: string
): Promise<StanceNarrative[]> {
  return query<StanceNarrative>(
    `SELECT id, ${locCol('narratives', 'label', locale)} as label,
            ${locCol('narratives', 'description', locale)} as description,
            ${locCol('narratives', 'moral_frame', locale)} as moral_frame,
            title_count, cluster_label, cluster_publishers, cluster_score_avg
     FROM narratives
     WHERE entity_type = $1 AND entity_id = $2
       AND extraction_method = 'stance_clustered'
     ORDER BY cluster_score_avg ASC`,
    [entityType, entityId]
  );
}

export interface EntityAnalysis {
  id: string;
  entity_type: string;
  entity_id: string;
  cluster_count: number;
  sections: string | null;
  scores: { frame_divergence?: number; collective_blind_spots?: string[]; synthesis?: string } | null;
  synthesis: string | null;
  blind_spots: string[] | null;
  conflicts: string[] | null;
  created_at: string;
}

export async function getEntityAnalysis(
  entityType: string, entityId: string, locale?: string
): Promise<EntityAnalysis | null> {
  const rows = await query<EntityAnalysis>(
    `SELECT id, entity_type, entity_id, cluster_count,
            ${locale === 'de' ? 'COALESCE(sections_de, sections)' : 'sections'} as sections,
            scores,
            ${locale === 'de' ? 'COALESCE(synthesis_de, synthesis)' : 'synthesis'} as synthesis,
            ${locale === 'de' ? 'COALESCE(blind_spots_de, blind_spots)' : 'blind_spots'} as blind_spots,
            ${locale === 'de' ? 'COALESCE(conflicts_de, conflicts)' : 'conflicts'} as conflicts,
            created_at::text
     FROM entity_analyses
     WHERE entity_type = $1 AND entity_id = $2`,
    [entityType, entityId]
  );
  return rows.length > 0 ? rows[0] : null;
}

export interface TimelineEvent {
  title: string;
  date: string;
  importance_score: number | null;
  source_count: number;
  tags: string[] | null;
}

export async function getCentroidTimeline(
  centroidId: string,
  excludeEventIds: string[] = [],
  relevanceTags: string[] = [],
  days: number = 90,
  limit: number = 15,
  boostBucketKeys: string[] = [],
  beforeDate?: string,
): Promise<TimelineEvent[]> {
  // Fetch events BEFORE the analyzed event (or before NOW if no date given)
  // This prevents "future" events from contaminating the analysis context
  const anchor = beforeDate || new Date().toISOString().slice(0, 10);

  if (relevanceTags.length === 0) {
    const params: unknown[] = [centroidId, excludeEventIds, days, limit, anchor];
    if (boostBucketKeys.length > 0) params.push(boostBucketKeys);
    const bucketBoost = boostBucketKeys.length > 0
      ? `+ CASE WHEN e.bucket_key = ANY($6::text[]) THEN 0.3 ELSE 0 END` : '';
    const rows = await query<TimelineEvent>(
      `SELECT
         COALESCE(e.title, e.topic_core) as title,
         e.date::text as date,
         e.importance_score,
         e.source_batch_count as source_count,
         e.tags
       FROM events_v3 e
       JOIN ctm ON ctm.id = e.ctm_id
       WHERE ctm.centroid_id = $1
         AND e.date >= $5::date - ($3 || ' days')::interval
         AND e.date <= $5::date
         AND e.merged_into IS NULL
         AND NOT (e.id = ANY($2::uuid[]))
         AND e.source_batch_count >= 15
       ORDER BY (COALESCE(e.importance_score, 0.1) ${bucketBoost}) DESC
       LIMIT $4`,
      params
    );
    return rows;
  }

  const params: unknown[] = [centroidId, excludeEventIds, days, relevanceTags, limit, anchor];
  if (boostBucketKeys.length > 0) params.push(boostBucketKeys);
  const bucketBoost = boostBucketKeys.length > 0
    ? `+ CASE WHEN e.bucket_key = ANY($7::text[]) THEN 0.3 ELSE 0 END` : '';
  const rows = await query<TimelineEvent>(
    `SELECT
       COALESCE(e.title, e.topic_core) as title,
       e.date::text as date,
       e.importance_score,
       e.source_batch_count as source_count,
       e.tags
     FROM events_v3 e
     JOIN ctm ON ctm.id = e.ctm_id
     WHERE ctm.centroid_id = $1
       AND e.date >= $6::date - ($3 || ' days')::interval
       AND e.date <= $6::date
       AND e.merged_into IS NULL
       AND NOT (e.id = ANY($2::uuid[]))
       AND e.source_batch_count >= 15
     ORDER BY (COALESCE(e.importance_score, 0.1) + 0.3 * COALESCE(array_length(
       ARRAY(SELECT unnest(COALESCE(e.tags, ARRAY[]::text[])) INTERSECT SELECT unnest($4::text[])), 1
     ), 0) ${bucketBoost}) DESC
     LIMIT $5`,
    params
  );
  return rows;
}

// --- Event Family queries ---

export interface FamilyDetail {
  id: string;
  title: string;
  summary: string | null;
  domain: string | null;
  cluster_count: number;
  source_count: number;
  first_seen: string | null;
  last_active: string | null;
  centroid_id: string;
  centroid_label: string;
  track: string;
  month: string;
}

export interface FamilyEvent {
  id: string;
  title: string;
  date: string | null;
  source_batch_count: number;
  event_type: string;
  bucket_key: string | null;
  summary: string | null;
}

export async function getFamilyById(familyId: string, locale?: string): Promise<FamilyDetail | null> {
  const results = await query<FamilyDetail>(
    `SELECT f.id, ${locCol('f', 'title', locale)} as title,
            ${locCol('f', 'summary', locale)} as summary,
            f.domain, f.cluster_count, f.source_count,
            f.first_seen::text, f.last_active::text,
            c.centroid_id, cv.label as centroid_label, c.track,
            TO_CHAR(c.month, 'YYYY-MM') as month
     FROM event_families f
     JOIN ctm c ON c.id = f.ctm_id
     JOIN centroids_v3 cv ON cv.id = c.centroid_id
     WHERE f.id = $1`,
    [familyId]
  );
  return results[0] || null;
}

export async function getFamilyEvents(familyId: string, locale?: string): Promise<FamilyEvent[]> {
  return query<FamilyEvent>(
    `SELECT e.id,
            COALESCE(${locale === 'de' ? 'e.title_de, ' : ''}e.title) as title,
            e.date::text, e.source_batch_count, e.event_type, e.bucket_key,
            ${locCol('e', 'summary', locale)} as summary
     FROM events_v3 e
     WHERE e.family_id = $1 AND e.merged_into IS NULL
     ORDER BY e.source_batch_count DESC`,
    [familyId]
  );
}

export async function getEventById(eventId: string, locale?: string): Promise<EventDetail | null> {
  return cached(`event:${eventId}:${locale || 'en'}`, 3600, async () => {
  const results = await query<EventDetail>(
    `SELECT
      e.id,
      e.date::text as date,
      e.last_active::text as last_active,
      COALESCE(${locale === 'de' ? 'e.title_de, ' : ''}e.title, e.topic_core) as title,
      ${locCol('e', 'summary', locale)} as summary,
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
      e.coherence_check,
      e.absorbed_centroids
    FROM events_v3 e
    JOIN ctm c ON e.ctm_id = c.id
    JOIN centroids_v3 cv ON c.centroid_id = cv.id
    WHERE e.id = $1`,
    [eventId]
  );
  return results[0] || null;
  });
}

export async function getEventSagaSiblings(
  saga: string, currentEventId: string, locale?: string
): Promise<Array<{ id: string; title: string; date: string; source_batch_count: number; month: string }>> {
  return query<{ id: string; title: string; date: string; source_batch_count: number; month: string }>(
    `SELECT e.id, COALESCE(${locale === 'de' ? 'e.title_de, ' : ''}e.title, e.topic_core) as title, e.date::text,
            e.source_batch_count, TO_CHAR(c.month, 'YYYY-MM') as month
     FROM events_v3 e
     JOIN ctm c ON e.ctm_id = c.id
     WHERE e.saga = $1 AND e.id != $2 AND e.merged_into IS NULL
     ORDER BY e.date ASC`,
    [saga, currentEventId]
  );
}

export async function getEventTitles(eventId: string): Promise<Title[]> {
  return cached(`eventTitles:${eventId}`, 3600, () =>
    query<Title>(
      `SELECT t.id, t.title_display, t.url_gnews, t.publisher_name,
              t.pubdate_utc, t.detected_language, t.processing_status
       FROM event_v3_titles et
       JOIN titles_v3 t ON et.title_id = t.id
       WHERE et.event_id = $1
       ORDER BY t.pubdate_utc DESC`,
      [eventId]
    )
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

export async function getTopSignalsByMonth(month: string, limit: number = 5, locale?: string): Promise<Record<SignalType, TopSignal[]>> {
  return cached(`signals:${month}:${locale || 'en'}`, 3600, async () => {
  // Try pre-computed rankings first (has LLM context)
  const contextCol = locale === 'de' ? 'COALESCE(context_de, context)' : 'context';
  const precomputed = await query<TopSignal>(
    `SELECT signal_type, value, count, ${contextCol} as context
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
    query<{ centroid_id: string; label: string; iso_codes: string[] | null; count: number }>(
      `${cte}
       SELECT ta.centroid_id, cv.label, cv.iso_codes, COUNT(*)::int as count
       FROM titles_v3 t
       JOIN feed_pubs fp ON t.publisher_name = fp.publisher_name
       JOIN title_assignments ta ON ta.title_id = t.id
       JOIN centroids_v3 cv ON cv.id = ta.centroid_id
       GROUP BY ta.centroid_id, cv.label, cv.iso_codes
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

export async function getPublisherStats(feedName: string): Promise<PublisherStats | null> {
  const rows = await query<{ stats: PublisherStats }>(
    'SELECT stats FROM mv_publisher_stats WHERE feed_name = $1',
    [feedName]
  );
  return rows[0]?.stats || null;
}

export async function getPublisherStance(feedName: string): Promise<StanceScore[]> {
  return query<StanceScore>(
    `SELECT ps.centroid_id, cv.label as centroid_label,
            ps.score, ps.confidence, ps.sample_size,
            TO_CHAR(ps.month, 'YYYY-MM') as month
     FROM publisher_stance ps
     JOIN centroids_v3 cv ON cv.id = ps.centroid_id
     WHERE ps.feed_name = $1
     ORDER BY ps.month DESC, ABS(ps.score) DESC`,
    [feedName]
  );
}

export interface CentroidStanceScore {
  feed_name: string;
  source_domain: string | null;
  score: number;
  confidence: number;
  sample_size: number;
  month: string;
}

export async function getStanceForCentroid(centroidId: string): Promise<CentroidStanceScore[]> {
  // Get latest month's stance data for this centroid
  return query<CentroidStanceScore>(
    `SELECT ps.feed_name, f.source_domain, ps.score, ps.confidence,
            ps.sample_size, TO_CHAR(ps.month, 'YYYY-MM') as month
     FROM publisher_stance ps
     LEFT JOIN feeds f ON f.name = ps.feed_name
     WHERE ps.centroid_id = $1
       AND ps.month = (SELECT MAX(month) FROM publisher_stance WHERE centroid_id = $1)
     ORDER BY ps.score ASC`,
    [centroidId]
  );
}

export interface DeviationFlag {
  type: string;
  z?: number;
  current?: number;
  baseline_mean?: number;
  actor?: string;
}

export interface CentroidDeviation {
  centroid_id: string;
  week: string;
  metrics: Record<string, unknown>;
  deviations: DeviationFlag[];
}

export async function getCentroidDeviations(centroidId: string): Promise<CentroidDeviation | null> {
  const rows = await query<CentroidDeviation>(
    `SELECT centroid_id, TO_CHAR(week, 'YYYY-MM-DD') as week, metrics, deviations
     FROM mv_centroid_baselines
     WHERE centroid_id = $1 AND deviations IS NOT NULL
     ORDER BY week DESC
     LIMIT 1`,
    [centroidId]
  );
  return rows[0] || null;
}

export interface AlignmentRow {
  feed_name: string;
  source_domain: string | null;
  country_code: string | null;
  centroid_id: string;
  centroid_label: string;
  score: number;
  confidence: number;
}

export async function getStanceMatrix(): Promise<AlignmentRow[]> {
  return cached('stance-matrix:latest', 3600, () =>
    query<AlignmentRow>(
      `SELECT ps.feed_name, f.source_domain, f.country_code,
              ps.centroid_id, cv.label as centroid_label,
              ps.score, ps.confidence
       FROM publisher_stance ps
       JOIN centroids_v3 cv ON cv.id = ps.centroid_id
       LEFT JOIN feeds f ON f.name = ps.feed_name AND f.is_active = true
       WHERE ps.month = (SELECT MAX(month) FROM publisher_stance)
       ORDER BY ps.feed_name, cv.label`
    )
  );
}

export async function getAllPublisherStats(): Promise<Record<string, PublisherStats>> {
  return cached('publisher-stats:all', 3600, async () => {
    const rows = await query<{ feed_name: string; stats: PublisherStats }>(
      'SELECT feed_name, stats FROM mv_publisher_stats'
    );
    const map: Record<string, PublisherStats> = {};
    for (const r of rows) map[r.feed_name] = r.stats;
    return map;
  });
}

// ========================================================================
// Trending events (time-decayed source count)
// ========================================================================

export async function getTrendingEvents(limit: number = 20, locale?: string): Promise<TrendingEvent[]> {
  return cached(`trending:${limit}:${locale || 'en'}`, 3600, () =>
    query<TrendingEvent>(
      `SELECT e.id, COALESCE(${locale === 'de' ? 'e.title_de, ' : ''}e.title, e.topic_core, (
                SELECT t.title_display FROM event_v3_titles evt
                JOIN titles_v3 t ON t.id = evt.title_id
                WHERE evt.event_id = e.id LIMIT 1
              )) as title,
              e.date::text as date, COALESCE(e.last_active, e.date)::text as last_active,
              e.source_batch_count, COALESCE(e.tags, '{}') as tags,
              LEFT(${locCol('e', 'summary', locale)}, 200) as summary,
              c.centroid_id, cv.label as centroid_label, cv.iso_codes,
              c.track,
              (ln(e.source_batch_count + 1)
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
         AND e.merged_into IS NULL
         AND COALESCE(e.last_active, e.date) >= CURRENT_DATE - INTERVAL '7 days'
       ORDER BY trending_score DESC
       LIMIT $1`,
      [limit]
    )
  );
}

export async function getTrendingSignals(): Promise<Record<string, TrendingSignal[]>> {
  return cached('trending:signals', 3600, async () => {
    const types = ['persons', 'orgs', 'places', 'commodities', 'policies'] as const;
    const parts = types.map(col =>
      `SELECT '${col}' as signal_type, val as value, COUNT(DISTINCT evt.event_id)::int as event_count,
              SUM(pow(0.5, EXTRACT(EPOCH FROM (NOW() - COALESCE(e.last_active, e.date)::timestamp)) / (3 * 86400)))::numeric(10,2) as score
       FROM events_v3 e
       JOIN ctm c ON e.ctm_id = c.id
       JOIN event_v3_titles evt ON evt.event_id = e.id
       JOIN title_labels tl ON tl.title_id = evt.title_id
       CROSS JOIN LATERAL unnest(tl.${col}) AS val
       WHERE e.source_batch_count >= 5
         AND e.is_catchall = false
         AND e.merged_into IS NULL
         AND COALESCE(e.last_active, e.date) >= CURRENT_DATE - INTERVAL '7 days'
       GROUP BY val ORDER BY score DESC LIMIT 5`
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
        WHERE ${dr.clause} AND e.is_catchall = false AND e.merged_into IS NULL
        GROUP BY val
        ORDER BY SUM(pow(0.5, EXTRACT(EPOCH FROM (NOW() - COALESCE(e.last_active, e.date)::timestamp)) / (3 * 86400))) DESC
        LIMIT ${perType})`
    ).join(' UNION ALL ');
    return query<SignalNode>(sql, dr.params);
  });
}

/** Stats for a single signal: total, weekly, geo, tracks (single CTE scan) */
export async function getSignalStats(
  type: SignalType,
  value: string,
  month?: string,
): Promise<SignalDetailStats> {
  if (!SIGNAL_COLUMNS_SET.has(type)) throw new Error('Invalid signal type');
  return cached(`signal-stats:${type}:${value}:${month || 'rolling'}`, 3600, async () => {
    const dr = signalDateRange(month);
    const vi = dr.nextIdx;
    const params = [...dr.params, value];

    const rows = await query<{ total: number; weekly: SignalWeekly[] | null; geo: Array<{ country: string; count: number }> | null; tracks: Array<{ track: string; count: number }> | null }>(
      `WITH signal_events AS (
         SELECT DISTINCT e.id, e.date, e.ctm_id
         FROM events_v3 e
         JOIN event_v3_titles evt ON evt.event_id = e.id
         JOIN title_labels tl ON tl.title_id = evt.title_id
         WHERE ${dr.clause} AND e.is_catchall = false AND e.merged_into IS NULL AND $${vi} = ANY(tl.${type})
       )
       SELECT
         (SELECT COUNT(*)::int FROM signal_events) as total,
         (SELECT json_agg(w ORDER BY w.week) FROM (
           SELECT date_trunc('week', date)::date::text as week, COUNT(*)::int as count
           FROM signal_events GROUP BY 1
         ) w) as weekly,
         (SELECT json_agg(g ORDER BY g.count DESC) FROM (
           SELECT unnest(cv.iso_codes) as country, COUNT(DISTINCT se.id)::int as count
           FROM signal_events se JOIN ctm c ON se.ctm_id = c.id
           JOIN centroids_v3 cv ON c.centroid_id = cv.id
           GROUP BY country ORDER BY count DESC LIMIT 20
         ) g) as geo,
         (SELECT json_agg(t ORDER BY t.count DESC) FROM (
           SELECT c.track, COUNT(DISTINCT se.id)::int as count
           FROM signal_events se JOIN ctm c ON se.ctm_id = c.id
           GROUP BY c.track ORDER BY count DESC
         ) t) as tracks`,
      params
    );

    const row = rows[0];
    return {
      total: row?.total ?? 0,
      weekly: row?.weekly ?? [],
      geo: row?.geo ?? [],
      tracks: row?.tracks ?? [],
    };
  });
}

/** Co-occurring signals enriched with shared events (detail page, heavy query) */
export async function getRelationshipClusters(
  type: SignalType,
  value: string,
  month?: string,
  locale?: string,
): Promise<RelationshipCluster[]> {
  if (!SIGNAL_COLUMNS_SET.has(type)) throw new Error('Invalid signal type');
  return cached(`signal-relationships:${type}:${value}:${month || 'rolling'}:${locale || 'en'}`, 3600, async () => {
    const dr = signalDateRange(month);
    const vi = dr.nextIdx;
    const params = [...dr.params, value];

    const titleExpr = locale === 'de'
      ? 'COALESCE(e.title_de, e.title, e.topic_core)'
      : 'COALESCE(e.title, e.topic_core)';

    // 20% density filter on BOTH the primary signal AND each co-signal per event,
    // so displayed events genuinely involve both signals (not just a passing mention)
    return queryNoJIT<RelationshipCluster>(
      `WITH signal_events AS (
         SELECT e.id, ${titleExpr} as title,
                e.date::text as date, e.source_batch_count
         FROM events_v3 e
         WHERE ${dr.clause} AND e.is_catchall = false AND e.merged_into IS NULL AND (
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
    );
  });
}

/** Co-occurrence graph: nodes + edges for top signals (observatory) */
export async function getSignalGraph(perType: number = 5, month?: string): Promise<SignalGraph> {
  const period = month || 'rolling';
  const rows = await query<{ nodes: SignalNode[]; edges: SignalEdge[] }>(
    `SELECT nodes, edges FROM mv_signal_graph WHERE period = $1`,
    [period]
  );
  if (rows[0]) return rows[0];
  // Fallback: empty graph if not yet materialized
  return { nodes: [], edges: [] };
}

/** Top signals for an epic's events (epic detail widget) */
export async function getTopSignalsForEpic(epicId: string, limit: number = 10): Promise<SignalNode[]> {
  return cached(`signals:epic:${epicId}:${limit}`, 3600, () => {
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

/** Top signals for a specific centroid (pre-computed by pipeline Phase 4.2) */
export async function getTopSignalsForCentroid(centroidId: string, month?: string): Promise<SignalNode[]> {
  const rows = await query<{ signals: SignalNode[] }>(
    `SELECT signals FROM mv_centroid_signals
     WHERE centroid_id = $1 AND month = ($2 || '-01')::date`,
    [centroidId, month || new Date().toISOString().slice(0, 7)]
  );
  return rows[0]?.signals || [];
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
              WHERE ${dr.clause} AND e.is_catchall = false AND e.merged_into IS NULL
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
       WHERE ${dr.clause} AND e.is_catchall = false AND e.merged_into IS NULL
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
         WHERE ${dr.clause} AND e.is_catchall = false AND e.merged_into IS NULL AND val = ANY($${vi})
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
  const trimmed = q.trim();

  return cached(`search:${trimmed.toLowerCase()}`, 3600, () => query<SearchResult>(
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
          AND e.merged_into IS NULL
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
    [trimmed]
  ));
}

// ========================================================================
// Focus country: top recent events for a centroid
export interface FocusEvent {
  id: string;
  title: string;
  date: string;
  source_batch_count: number;
  tags: string[];
  summary: string | null;
}

export async function getFocusCountryEvents(
  centroidId: string,
  limit: number = 5,
  locale?: string
): Promise<FocusEvent[]> {
  return query<FocusEvent>(
    `SELECT e.id,
            COALESCE(${locale === 'de' ? 'e.title_de, ' : ''}e.title, e.topic_core) as title,
            e.date::text as date, e.source_batch_count,
            COALESCE(e.tags, '{}') as tags,
            LEFT(${locCol('e', 'summary', locale)}, 200) as summary
     FROM events_v3 e
     JOIN ctm c ON e.ctm_id = c.id
     WHERE c.centroid_id = $1
       AND e.is_catchall = false
       AND e.merged_into IS NULL
       AND e.source_batch_count >= 5
       AND e.title IS NOT NULL
       AND e.summary IS NOT NULL
     ORDER BY COALESCE(e.last_active, e.date) DESC
     LIMIT $2`,
    [centroidId, limit]
  );
}

// ── Narrative Mapping queries ──────────────────────────────────────

export async function getAllMetaNarratives(locale?: string): Promise<MetaNarrative[]> {
  return cached(`meta_narratives:all:${locale || 'en'}`, 3600, () =>
    query<MetaNarrative>(
      `SELECT id, ${locCol('meta_narratives', 'name', locale)} as name,
              ${locCol('meta_narratives', 'description', locale)} as description,
              signals, sort_order
       FROM meta_narratives ORDER BY sort_order`
    )
  );
}

export async function getMetaNarrativeById(id: string, locale?: string): Promise<MetaNarrative | null> {
  return cached(`meta_narrative:${id}:${locale || 'en'}`, 3600, async () => {
    const rows = await query<MetaNarrative>(
      `SELECT id, ${locCol('meta_narratives', 'name', locale)} as name,
              ${locCol('meta_narratives', 'description', locale)} as description,
              signals, sort_order
       FROM meta_narratives WHERE id = $1`,
      [id]
    );
    return rows[0] || null;
  });
}

export async function getStrategicNarratives(locale?: string): Promise<StrategicNarrative[]> {
  return cached(`strategic_narratives:all:${locale || 'en'}`, 1800, () =>
    query<StrategicNarrative>(
      `SELECT sn.id, sn.meta_narrative_id, ${locCol('mn', 'name', locale)} as meta_name,
              sn.category, sn.actor_centroid, c.label as actor_label,
              ${locCol('sn', 'name', locale)} as name,
              ${locCol('sn', 'claim', locale)} as claim,
              sn.normative_conclusion, sn.keywords, sn.action_classes, sn.domains,
              sn.tier, sn.aligned_with, sn.opposes,
              COUNT(esn.event_id)::int as event_count
       FROM strategic_narratives sn
       JOIN meta_narratives mn ON mn.id = sn.meta_narrative_id
       LEFT JOIN centroids_v3 c ON c.id = sn.actor_centroid
       LEFT JOIN event_strategic_narratives esn ON esn.narrative_id = sn.id
       WHERE sn.is_active = true
       GROUP BY sn.id, mn.id, c.label, mn.name, mn.name_de
       ORDER BY mn.sort_order, sn.name`
    )
  );
}

export async function getStrategicNarrativeById(id: string, locale?: string): Promise<StrategicNarrative | null> {
  return cached(`strategic_narrative:${id}:${locale || 'en'}`, 3600, async () => {
    const rows = await query<StrategicNarrative>(
      `SELECT sn.id, sn.meta_narrative_id, ${locCol('mn', 'name', locale)} as meta_name,
              sn.category, sn.actor_centroid, c.label as actor_label,
              ${locCol('sn', 'name', locale)} as name,
              ${locCol('sn', 'claim', locale)} as claim,
              sn.normative_conclusion, sn.keywords, sn.action_classes, sn.domains,
              COUNT(esn.event_id)::int as event_count
       FROM strategic_narratives sn
       JOIN meta_narratives mn ON mn.id = sn.meta_narrative_id
       LEFT JOIN centroids_v3 c ON c.id = sn.actor_centroid
       LEFT JOIN event_strategic_narratives esn ON esn.narrative_id = sn.id
       WHERE sn.id = $1
       GROUP BY sn.id, mn.id, c.label, mn.name, mn.name_de`,
      [id]
    );
    return rows[0] || null;
  });
}

export async function getNarrativeWeeklyActivity(narrativeId: string): Promise<SignalWeekly[]> {
  return cached(`narrative_weekly:${narrativeId}`, 1800, () =>
    query<SignalWeekly>(
      `SELECT date_trunc('week', e.date::date)::text as week, COUNT(*)::int as count
       FROM event_strategic_narratives esn
       JOIN events_v3 e ON e.id = esn.event_id
       WHERE esn.narrative_id = $1
         AND e.date >= now() - interval '90 days'
       GROUP BY week ORDER BY week`,
      [narrativeId]
    )
  );
}

export async function getNarrativeEvents(narrativeId: string, limit: number = 50, locale?: string): Promise<(EventDetail & { confidence: number })[]> {
  return cached(`narrative_events:${narrativeId}:${limit}:${locale || 'en'}`, 900, () =>
    query<EventDetail & { confidence: number }>(
      `SELECT e.id, e.date::text as date, ${locCol('e', 'title', locale)} as title,
              LEFT(${locCol('e', 'summary', locale)}, 200) as summary,
              e.source_batch_count, e.tags,
              c.centroid_id, cv.label as centroid_label, c.track,
              esn.confidence
       FROM event_strategic_narratives esn
       JOIN events_v3 e ON e.id = esn.event_id
       JOIN ctm c ON c.id = e.ctm_id
       JOIN centroids_v3 cv ON cv.id = c.centroid_id
       WHERE esn.narrative_id = $1
         AND e.title IS NOT NULL
       ORDER BY e.date DESC
       LIMIT $2`,
      [narrativeId, limit]
    )
  );
}

export async function getNarrativesForEvent(eventId: string): Promise<EventNarrativeLink[]> {
  return cached(`event_narratives:${eventId}`, 3600, () =>
    query<EventNarrativeLink>(
      `SELECT esn.narrative_id, sn.name as narrative_name,
              sn.actor_centroid, c.label as actor_label,
              esn.confidence
       FROM event_strategic_narratives esn
       JOIN strategic_narratives sn ON sn.id = esn.narrative_id
       LEFT JOIN centroids_v3 c ON c.id = sn.actor_centroid
       WHERE esn.event_id = $1
       ORDER BY esn.confidence DESC`,
      [eventId]
    )
  );
}

export async function getNarrativesForCentroid(centroidId: string, locale?: string): Promise<StrategicNarrative[]> {
  return cached(`centroid_narratives:${centroidId}:${locale || 'en'}`, 1800, () =>
    query<StrategicNarrative>(
      `SELECT sn.id, sn.meta_narrative_id, ${locCol('mn', 'name', locale)} as meta_name,
              sn.category, sn.actor_centroid, c.label as actor_label,
              ${locCol('sn', 'name', locale)} as name,
              ${locCol('sn', 'claim', locale)} as claim,
              sn.normative_conclusion, sn.keywords, sn.action_classes, sn.domains,
              COUNT(esn.event_id)::int as event_count
       FROM strategic_narratives sn
       JOIN meta_narratives mn ON mn.id = sn.meta_narrative_id
       LEFT JOIN centroids_v3 c ON c.id = sn.actor_centroid
       LEFT JOIN event_strategic_narratives esn ON esn.narrative_id = sn.id
       WHERE sn.actor_centroid = $1 AND sn.is_active = true
       GROUP BY sn.id, mn.id, c.label, mn.name, mn.name_de
       ORDER BY event_count DESC`,
      [centroidId]
    )
  );
}

export async function getCompetingNarratives(narrativeId: string): Promise<(StrategicNarrative & { shared_events: number })[]> {
  return cached(`competing_narratives:${narrativeId}`, 1800, () =>
    query<StrategicNarrative & { shared_events: number }>(
      `SELECT sn.id, sn.name, sn.actor_centroid, c.label as actor_label,
              sn.meta_narrative_id, sn.claim,
              COUNT(*)::int as shared_events
       FROM event_strategic_narratives esn1
       JOIN event_strategic_narratives esn2 ON esn2.event_id = esn1.event_id AND esn2.narrative_id != esn1.narrative_id
       JOIN strategic_narratives sn ON sn.id = esn2.narrative_id
       LEFT JOIN centroids_v3 c ON c.id = sn.actor_centroid
       WHERE esn1.narrative_id = $1
         AND sn.actor_centroid != (SELECT actor_centroid FROM strategic_narratives WHERE id = $1)
       GROUP BY sn.id, c.label
       ORDER BY shared_events DESC
       LIMIT 10`,
      [narrativeId]
    )
  );
}

export async function getNarrativeSparklines(): Promise<Record<string, SignalWeekly[]>> {
  return cached('narrative_sparklines:all', 1800, async () => {
    const rows = await query<{ narrative_id: string; week: string; count: number }>(
      `SELECT narrative_id, week, event_count as count
       FROM narrative_weekly_activity
       WHERE week >= (now() - interval '90 days')::date::text
       ORDER BY week`
    );
    const map: Record<string, SignalWeekly[]> = {};
    for (const r of rows) {
      if (!map[r.narrative_id]) map[r.narrative_id] = [];
      map[r.narrative_id].push({ week: r.week, count: r.count });
    }
    return map;
  });
}

export async function getMetaNarrativeActivity(metaId: string): Promise<SignalWeekly[]> {
  return cached(`meta_narrative_activity:${metaId}`, 1800, () =>
    query<SignalWeekly>(
      `SELECT date_trunc('week', e.date::date)::text as week, COUNT(*)::int as count
       FROM event_strategic_narratives esn
       JOIN strategic_narratives sn ON sn.id = esn.narrative_id
       JOIN events_v3 e ON e.id = esn.event_id
       WHERE sn.meta_narrative_id = $1
         AND e.date >= now() - interval '90 days'
       GROUP BY week ORDER BY week`,
      [metaId]
    )
  );
}

// Top narrative per event (for trending cards: one badge per event, from its own centroid)
export async function getTopNarrativePerEvent(eventIds: string[]): Promise<Record<string, EventNarrativeLink>> {
  if (eventIds.length === 0) return {};
  return cached(`top_narrative_per_event:${eventIds.sort().join(',')}`, 1800, async () => {
    const rows = await query<EventNarrativeLink & { event_id: string }>(
      `SELECT DISTINCT ON (esn.event_id)
              esn.event_id::text as event_id,
              esn.narrative_id, sn.name as narrative_name,
              sn.actor_centroid, c.label as actor_label,
              esn.confidence
       FROM event_strategic_narratives esn
       JOIN strategic_narratives sn ON sn.id = esn.narrative_id
       JOIN events_v3 e ON e.id = esn.event_id
       JOIN ctm ct ON ct.id = e.ctm_id
       LEFT JOIN centroids_v3 c ON c.id = sn.actor_centroid
       WHERE esn.event_id = ANY($1::uuid[])
         AND sn.actor_centroid = ct.centroid_id
       ORDER BY esn.event_id, esn.confidence DESC`,
      [eventIds]
    );
    const map: Record<string, EventNarrativeLink> = {};
    for (const r of rows) {
      map[r.event_id] = r;
    }
    return map;
  });
}

// Narratives for an epic's events, grouped by centroid
export async function getNarrativesForEpic(epicId: string, locale?: string): Promise<{
  centroid_id: string;
  centroid_label: string;
  narratives: { id: string; name: string; event_count: number }[];
}[]> {
  return cached(`epic_narratives:${epicId}:${locale || 'en'}`, 1800, async () => {
    const rows = await query<{
      centroid_id: string;
      centroid_label: string;
      narrative_id: string;
      narrative_name: string;
      event_count: number;
    }>(
      `SELECT sn.actor_centroid as centroid_id, cv.label as centroid_label,
              sn.id as narrative_id, ${locCol('sn', 'name', locale)} as narrative_name,
              COUNT(DISTINCT esn.event_id)::int as event_count
       FROM epic_events ee
       JOIN event_strategic_narratives esn ON esn.event_id = ee.event_id
       JOIN strategic_narratives sn ON sn.id = esn.narrative_id
       LEFT JOIN centroids_v3 cv ON cv.id = sn.actor_centroid
       WHERE ee.epic_id = $1
         AND sn.actor_centroid IS NOT NULL
       GROUP BY sn.actor_centroid, cv.label, sn.id, sn.name, sn.name_de
       HAVING COUNT(DISTINCT esn.event_id) >= 2
       ORDER BY cv.label, event_count DESC`,
      [epicId]
    );
    // Group by centroid
    const map = new Map<string, { centroid_id: string; centroid_label: string; narratives: { id: string; name: string; event_count: number }[] }>();
    for (const r of rows) {
      if (!map.has(r.centroid_id)) {
        map.set(r.centroid_id, { centroid_id: r.centroid_id, centroid_label: r.centroid_label, narratives: [] });
      }
      map.get(r.centroid_id)!.narratives.push({
        id: r.narrative_id,
        name: r.narrative_name,
        event_count: r.event_count,
      });
    }
    return Array.from(map.values());
  });
}

// ── Narrative Map ────────────────────────────────────────────────

export async function getNarrativeMapData(locale?: string): Promise<NarrativeMapEntry[]> {
  return cached(`narrative_map:all:${locale || 'en'}`, 1800, () =>
    query<NarrativeMapEntry>(
      `SELECT sn.id, sn.meta_narrative_id, ${locCol('mn', 'name', locale)} as meta_name,
              sn.actor_centroid, c.label as actor_label, c.iso_codes as actor_iso_codes,
              ${locCol('sn', 'name', locale)} as name,
              ${locCol('sn', 'claim', locale)} as claim,
              sn.actor_prefixes, sn.related_centroids, sn.tier,
              COUNT(esn.event_id)::int as event_count
       FROM strategic_narratives sn
       JOIN meta_narratives mn ON mn.id = sn.meta_narrative_id
       LEFT JOIN centroids_v3 c ON c.id = sn.actor_centroid
       LEFT JOIN event_strategic_narratives esn ON esn.narrative_id = sn.id
       WHERE sn.is_active = true
       GROUP BY sn.id, mn.id, mn.name, mn.name_de, c.id
       ORDER BY COUNT(esn.event_id) DESC`
    )
  );
}

export async function getCentroidIsoMap(): Promise<{ id: string; iso_codes: string[] }[]> {
  return cached('centroid_iso_map', 3600, () =>
    query<{ id: string; iso_codes: string[] }>(
      `SELECT id, iso_codes FROM centroids_v3 WHERE is_active = true AND iso_codes IS NOT NULL`
    )
  );
}

// ============================================================================
// CALENDAR-DAY FRONTEND (Workstream A)
// See docs/FRONTEND_CALENDAR_REDESIGN.md
// ============================================================================

interface CalendarClusterRow {
  id: string;
  first_date: string;
  last_date: string;
  title: string | null;
  source_batch_count: number;
  event_type: string | null;
  bucket_key: string | null;
  is_substrate: boolean;
  has_narratives: boolean;
}

/**
 * Load a full calendar-day view for a CTM-month in a single call.
 *
 * Returns:
 * - the CTM metadata
 * - days[] grouped by events_v3.date (only days with >= 1 promoted cluster)
 * - activity_stripe[] covering every day of the month, with top-5 stack segments
 * - scope stats (total sources analyzed, outlet count, active days)
 *
 * Only is_promoted events are returned (top 20/day, set by phase 4.5a).
 * daily_brief is pulled from the daily_briefs table (phase 4.5-day).
 */

export async function getCalendarMonthView(
  centroidId: string,
  track: string,
  month: string, // YYYY-MM
  locale?: string
): Promise<CalendarMonthView | null> {
  return cached(`calendar:${centroidId}:${track}:${month}:${locale || 'en'}`, 900, async () => {
    // 1. Resolve CTM
    const ctm = await getCTM(centroidId, track, month, locale);
    if (!ctm) return null;

    // 2. Fetch promoted events (top 20/day). Promotion is instant (Slot 3),
    //    so new days are visible immediately after clustering.
    const clusterRows = await query<CalendarClusterRow>(
      `SELECT
         e.id::text AS id,
         e.date::text AS first_date,
         COALESCE(e.last_active::text, e.date::text) AS last_date,
         COALESCE(
           ${locale === 'de' ? 'e.title_de, ' : ''}
           e.title,
           (SELECT t2.title_display FROM event_v3_titles evt2
            JOIN titles_v3 t2 ON t2.id = evt2.title_id
            WHERE evt2.event_id = e.id
            ORDER BY t2.pubdate_utc ASC LIMIT 1)
         ) AS title,
         e.source_batch_count,
         e.event_type,
         e.bucket_key,
         false AS is_substrate,
         EXISTS(
           SELECT 1 FROM narratives n
           WHERE n.entity_type = 'event' AND n.entity_id = e.id
         ) AS has_narratives
       FROM events_v3 e
       WHERE e.ctm_id = $1
         AND e.is_promoted = true
         AND e.is_catchall = false
         AND e.merged_into IS NULL
       ORDER BY e.date ASC, e.source_batch_count DESC`,
      [ctm.id]
    );

    // 3. Group by date; cluster order within day preserved (source_count DESC)
    const daysMap = new Map<string, CalendarDayView>();
    for (const row of clusterRows) {
      const dateKey = row.first_date;
      let day = daysMap.get(dateKey);
      if (!day) {
        day = {
          date: dateKey,
          total_sources: 0,
          cluster_count: 0,
          daily_brief: null,
          clusters: [],
        };
        daysMap.set(dateKey, day);
      }
      const card: CalendarClusterCard = {
        id: row.id,
        title: row.title,
        source_count: row.source_batch_count,
        first_date: row.first_date,
        last_date: row.last_date,
        event_type: row.event_type as CalendarClusterCard['event_type'],
        bucket_key: row.bucket_key,
        has_event_page: row.source_batch_count >= CALENDAR_EVENT_PAGE_MIN_SOURCES,
        is_substrate: row.is_substrate,
        has_narratives: row.has_narratives,
      };
      day.clusters.push(card);
      day.total_sources += row.source_batch_count;
      day.cluster_count += 1;
    }

    // 3b. Load source titles for SMALL clusters (source_count < 5 = no event page).
    //     Users still need to click through to the original articles.
    const smallClusterIds: string[] = [];
    for (const day of daysMap.values()) {
      for (const c of day.clusters) {
        if (!c.has_event_page) smallClusterIds.push(c.id);
      }
    }
    if (smallClusterIds.length > 0) {
      const sourceRows = await query<{
        event_id: string;
        id: string;
        title_display: string;
        url_gnews: string | null;
        publisher_name: string | null;
        publisher_domain: string | null;
        detected_language: string | null;
      }>(
        `SELECT et.event_id::text AS event_id,
                t.id::text        AS id,
                t.title_display,
                t.url_gnews,
                t.publisher_name,
                f.source_domain   AS publisher_domain,
                t.detected_language
           FROM event_v3_titles et
           JOIN titles_v3 t  ON t.id = et.title_id
           LEFT JOIN feeds f ON f.id = t.feed_id
          WHERE et.event_id = ANY($1::uuid[])
          ORDER BY t.pubdate_utc ASC`,
        [smallClusterIds]
      );
      const sourcesByEvent = new Map<string, CalendarClusterSource[]>();
      for (const row of sourceRows) {
        let list = sourcesByEvent.get(row.event_id);
        if (!list) {
          list = [];
          sourcesByEvent.set(row.event_id, list);
        }
        list.push({
          id: row.id,
          title_display: row.title_display,
          url: row.url_gnews,
          publisher_name: row.publisher_name,
          publisher_domain: row.publisher_domain,
          detected_language: row.detected_language,
        });
      }
      for (const day of daysMap.values()) {
        for (const c of day.clusters) {
          if (!c.has_event_page) {
            c.sources = sourcesByEvent.get(c.id) || [];
          }
        }
      }
    }

    // 4a. Brief text (prose) — only exists for days that crossed the promotion
    //     threshold and got an LLM-generated daily brief.
    const briefRows = await query<{
      date: string;
      brief_en: string;
      brief_de: string | null;
    }>(
      `SELECT date::text AS date, brief_en, brief_de
         FROM daily_briefs WHERE ctm_id = $1`,
      [ctm.id]
    );
    for (const br of briefRows) {
      const day = daysMap.get(br.date);
      if (day) {
        day.daily_brief = (locale === 'de' && br.brief_de) ? br.brief_de : br.brief_en;
      }
    }

    // 4b. Day themes — mechanical aggregation of title_labels (sector, subject)
    //     over promoted events per date. Mirrors compute_themes() in the brief
    //     generator; produced for every covered day, not only brief-qualified ones.
    const themeRows = await query<{
      date: string;
      sector: string;
      subject: string;
      weight: number;
    }>(
      `WITH day_labels AS (
         SELECT e.date::text AS date, tl.sector, tl.subject, COUNT(*) AS cnt
           FROM events_v3 e
           JOIN event_v3_titles evt ON evt.event_id = e.id
           JOIN title_labels tl ON tl.title_id = evt.title_id
          WHERE e.ctm_id = $1 AND e.is_promoted = true
            AND tl.sector IS NOT NULL AND tl.sector <> 'NON_STRATEGIC'
          GROUP BY e.date, tl.sector, tl.subject
       ),
       totals AS (
         SELECT date, SUM(cnt) AS day_total FROM day_labels GROUP BY date
       )
       SELECT dl.date, dl.sector, dl.subject,
              (dl.cnt::float / t.day_total)::float AS weight
         FROM day_labels dl
         JOIN totals t ON t.date = dl.date
        ORDER BY dl.date, dl.cnt DESC, dl.sector, dl.subject`,
      [ctm.id]
    );
    const themesByDate = new Map<string, CalendarThemeSegment[]>();
    for (const r of themeRows) {
      let list = themesByDate.get(r.date);
      if (!list) {
        list = [];
        themesByDate.set(r.date, list);
      }
      list.push({ sector: r.sector, subject: r.subject, weight: Number(r.weight) });
    }

    const days: CalendarDayView[] = Array.from(daysMap.values());

    // 5. Activity stripe: every day of the month with theme segments from daily_briefs
    const [year, mm] = month.split('-').map(Number);
    const daysInMonth = new Date(year, mm, 0).getDate();
    const stripe: CalendarStripeEntry[] = [];
    for (let d = 1; d <= daysInMonth; d++) {
      const dateStr = `${year}-${String(mm).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
      const dayEntry = daysMap.get(dateStr);
      stripe.push({
        date: dateStr,
        total_sources: dayEntry ? dayEntry.total_sources : 0,
        themes: themesByDate.get(dateStr) || [],
      });
    }

    // 6. Analysis scope stats (total sources + distinct outlets for the CTM)
    const scopeRows = await query<{ total_sources: number; outlet_count: number }>(
      `SELECT
         COUNT(DISTINCT ta.title_id)::int AS total_sources,
         COUNT(DISTINCT t.feed_id)::int   AS outlet_count
       FROM title_assignments ta
       JOIN titles_v3 t ON t.id = ta.title_id
       WHERE ta.ctm_id = $1`,
      [ctm.id]
    );
    const scopeRow = scopeRows[0] || { total_sources: 0, outlet_count: 0 };
    const scope: CalendarAnalysisScope = {
      total_sources: scopeRow.total_sources,
      outlet_count: scopeRow.outlet_count,
      active_days: days.length,
    };

    const theme_chips = await getCtmThemeChips(ctm.id, 3);

    return {
      ctm,
      days,
      activity_stripe: stripe,
      scope,
      theme_chips,
    };
  });
}

// Top strategic narratives active in a centroid+month (by event count).
// Surfaces the 260-narrative curated layer into the centroid sidebar.
export async function getActiveNarrativesForCentroid(
  centroidId: string,
  month: string,
  locale?: string,
  limit = 5
): Promise<Array<{ id: string; name: string; actor_centroid: string | null; meta_narrative_id: string | null; event_count: number }>> {
  const monthStart = month.length === 7 ? `${month}-01` : month;
  return cached(
    `centroid_narratives:${centroidId}:${monthStart}:${locale || 'en'}`,
    900,
    async () => {
      const rows = await query<{
        id: string;
        name: string;
        name_de: string | null;
        actor_centroid: string | null;
        meta_narrative_id: string | null;
        event_count: number;
      }>(
        `SELECT sn.id, sn.name, sn.name_de, sn.actor_centroid, sn.meta_narrative_id,
                COUNT(DISTINCT e.id)::int AS event_count
           FROM event_strategic_narratives esn
           JOIN events_v3 e ON e.id = esn.event_id
           JOIN ctm c ON c.id = e.ctm_id
           JOIN strategic_narratives sn ON sn.id = esn.narrative_id
          WHERE c.centroid_id = $1 AND c.month = $2
            AND e.merged_into IS NULL
          GROUP BY sn.id, sn.name, sn.name_de, sn.actor_centroid, sn.meta_narrative_id
          ORDER BY event_count DESC, sn.name
          LIMIT $3`,
        [centroidId, monthStart, limit]
      );
      return rows.map(r => ({
        id: r.id,
        name: locale === 'de' && r.name_de ? r.name_de : r.name,
        actor_centroid: r.actor_centroid,
        meta_narrative_id: r.meta_narrative_id,
        event_count: r.event_count,
      }));
    }
  );
}

// Returns true if the centroid+month has any promoted events across any track.
// Used to gate the new centroid hero view vs the legacy cards.
export async function centroidHasPromotedForMonth(
  centroidId: string,
  month: string // YYYY-MM or YYYY-MM-DD
): Promise<boolean> {
  const monthStart = month.length === 7 ? `${month}-01` : month;
  const rows = await query<{ ok: boolean }>(
    `SELECT EXISTS (
       SELECT 1 FROM events_v3 e
       JOIN ctm c ON c.id = e.ctm_id
       WHERE c.centroid_id = $1 AND c.month = $2
         AND e.is_promoted = true AND e.merged_into IS NULL
     ) AS ok`,
    [centroidId, monthStart]
  );
  return !!rows[0]?.ok;
}

// Top-N dominant themes for a CTM (across all promoted events). Used for the
// header chips on CTM calendar + centroid track cards.
async function getCtmThemeChips(ctmId: string, limit = 3): Promise<CtmThemeChip[]> {
  const rows = await query<{ sector: string; subject: string; weight: number }>(
    `WITH labels AS (
       SELECT tl.sector, tl.subject, COUNT(*) AS cnt
         FROM events_v3 e
         JOIN event_v3_titles evt ON evt.event_id = e.id
         JOIN title_labels tl ON tl.title_id = evt.title_id
        WHERE e.ctm_id = $1 AND e.is_promoted = true
          AND tl.sector IS NOT NULL AND tl.sector <> 'NON_STRATEGIC'
        GROUP BY tl.sector, tl.subject
     )
     SELECT sector, subject, (cnt::float / SUM(cnt) OVER ())::float AS weight
       FROM labels
      ORDER BY cnt DESC, sector, subject
      LIMIT $2`,
    [ctmId, limit]
  );
  return rows.map(r => ({
    sector: r.sector,
    subject: r.subject,
    weight: Number(r.weight),
  }));
}

// Stopwords + tokenizer + Dice — ported from pipeline/phase_4/merge_same_day_events.py
// Used for display-layer de-dup of cross-day fragments in track card top events.
const CARD_STOP_WORDS = new Set(
  ('the a an and or of to in on at for with by from as is was are be has have had not but '
    + 'this it its be has have had not but after over says said could new us s t '
    + 'will during about between into than more out up no may').split(/\s+/)
);

// Ultra-common entities that appear in too many titles to be distinctive.
// Removing them lets truly distinctive names (Pope, Leo, Vance, Hormuz...)
// drive the similarity score.
const CARD_UBIQUITOUS = new Set(
  ('trump biden vance us usa american america iran iranian china chinese russia '
    + 'russian putin netanyahu khamenei xi nato eu un').split(/\s+/)
);

function titleWords(text: string | null | undefined): Set<string> {
  const words = new Set<string>();
  if (!text) return words;
  const tokens = text.toLowerCase().match(/[a-z0-9]+/g) || [];
  for (const w of tokens) {
    if (w.length > 1 && !CARD_STOP_WORDS.has(w) && !CARD_UBIQUITOUS.has(w)) {
      words.add(w);
    }
  }
  return words;
}

function dice(a: Set<string>, b: Set<string>): number {
  if (!a.size || !b.size) return 0;
  let inter = 0;
  for (const w of a) if (b.has(w)) inter++;
  return (2 * inter) / (a.size + b.size);
}

// Cross-track monthly view for the centroid page hero.
// Returns per-day stacked activity (colored by track) + per-track summaries
// with top-5 promoted events.
export async function getCentroidMonthView(
  centroidId: string,
  month: string, // YYYY-MM or YYYY-MM-DD
  locale?: string
): Promise<CentroidMonthView | null> {
  const monthStart = month.length === 7 ? `${month}-01` : month;
  return cached(`centroid_cal:${centroidId}:${monthStart}:${locale || 'en'}`, 900, async () => {
    // 1. Per-day, per-track source totals — drives the activity stripe
    const stripeRows = await query<{
      date: string;
      track: string;
      src: number;
    }>(
      `SELECT e.date::text AS date, c.track, SUM(e.source_batch_count)::int AS src
         FROM events_v3 e
         JOIN ctm c ON c.id = e.ctm_id
        WHERE c.centroid_id = $1 AND c.month = $2
          AND e.is_promoted = true AND e.merged_into IS NULL
        GROUP BY e.date, c.track`,
      [centroidId, monthStart]
    );

    // 2. Top-5 promoted events per track (for the track cards)
    const topRows = await query<{
      track: string;
      event_id: string;
      date: string;
      title: string | null;
      source_batch_count: number;
    }>(
      `WITH ranked AS (
         SELECT c.track,
                e.id::text AS event_id,
                e.date::text AS date,
                COALESCE(
                  ${locale === 'de' ? 'e.title_de, ' : ''}
                  e.title,
                  (SELECT t2.title_display FROM event_v3_titles evt2
                   JOIN titles_v3 t2 ON t2.id = evt2.title_id
                   WHERE evt2.event_id = e.id
                   ORDER BY t2.pubdate_utc ASC LIMIT 1)
                ) AS title,
                e.source_batch_count,
                ROW_NUMBER() OVER (
                  PARTITION BY c.track
                  ORDER BY e.source_batch_count DESC, e.date DESC, e.id
                ) AS rnk
           FROM events_v3 e
           JOIN ctm c ON c.id = e.ctm_id
          WHERE c.centroid_id = $1 AND c.month = $2
            AND e.is_promoted = true AND e.merged_into IS NULL
            AND e.is_catchall = false
       )
       SELECT track, event_id, date, title, source_batch_count
         FROM ranked WHERE rnk <= 10
        ORDER BY track, rnk`,
      [centroidId, monthStart]
    );

    // 3. Per-track CTM metadata (title_count, summary_text)
    const ctmRows = await query<{
      track: string;
      title_count: number;
      summary_text: string | null;
      summary_text_de: string | null;
      last_active: string | null;
    }>(
      `SELECT c.track,
              c.title_count::int AS title_count,
              c.summary_text,
              c.summary_text_de,
              (SELECT MAX(e.date)::text FROM events_v3 e WHERE e.ctm_id = c.id) AS last_active
         FROM ctm c
        WHERE c.centroid_id = $1 AND c.month = $2`,
      [centroidId, monthStart]
    );

    // 4. Prev / next month with coverage
    const navRows = await query<{ month: string; is_prev: boolean }>(
      `(SELECT month::text AS month, true AS is_prev
          FROM ctm WHERE centroid_id = $1 AND month < $2
          ORDER BY month DESC LIMIT 1)
       UNION ALL
       (SELECT month::text AS month, false AS is_prev
          FROM ctm WHERE centroid_id = $1 AND month > $2
          ORDER BY month ASC LIMIT 1)`,
      [centroidId, monthStart]
    );
    const prevMonth =
      navRows.find(r => r.is_prev)?.month.slice(0, 7) || null;
    const nextMonth =
      navRows.find(r => !r.is_prev)?.month.slice(0, 7) || null;

    // 5. Build activity stripe: every day of month, track weights sum to 1
    const byDate = new Map<string, Map<string, number>>();
    const totalByDate = new Map<string, number>();
    for (const r of stripeRows) {
      let m = byDate.get(r.date);
      if (!m) {
        m = new Map();
        byDate.set(r.date, m);
      }
      m.set(r.track, (m.get(r.track) || 0) + r.src);
      totalByDate.set(r.date, (totalByDate.get(r.date) || 0) + r.src);
    }
    const [yearStr, mmStr] = monthStart.split('-');
    const year = parseInt(yearStr);
    const mm = parseInt(mmStr);
    const daysInMonth = new Date(year, mm, 0).getDate();
    const activity_stripe: CentroidStripeEntry[] = [];
    for (let d = 1; d <= daysInMonth; d++) {
      const dateStr = `${year}-${String(mm).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
      const trackMap = byDate.get(dateStr);
      const total = totalByDate.get(dateStr) || 0;
      const tracks: CentroidStripeEntry['tracks'] = [];
      if (trackMap && total > 0) {
        for (const [tr, src] of trackMap.entries()) {
          tracks.push({ track: tr, weight: src / total });
        }
        tracks.sort((a, b) => b.weight - a.weight);
      }
      activity_stripe.push({ date: dateStr, total_sources: total, tracks });
    }

    // 6. Build track summaries with title-Dice de-dup for cross-day fragments.
    //    Same story often promoted as separate events on consecutive days
    //    (e.g. Trump+Pope criticism on Apr 13/14/15). We collapse fragments
    //    with title Dice >= 0.4 into the biggest representative, display-only.
    const CARD_DICE_THRESHOLD = 0.3;
    const CARD_TOP_N = 5;
    const topByTrack = new Map<string, CentroidTrackSummary['top_events']>();
    const candidatesByTrack = new Map<
      string,
      Array<{ event: CentroidTrackSummary['top_events'][number]; words: Set<string> }>
    >();
    for (const r of topRows) {
      let list = candidatesByTrack.get(r.track);
      if (!list) {
        list = [];
        candidatesByTrack.set(r.track, list);
      }
      list.push({
        event: {
          id: r.event_id,
          title: r.title || '',
          date: r.date,
          source_count: r.source_batch_count,
          has_event_page: r.source_batch_count >= CALENDAR_EVENT_PAGE_MIN_SOURCES,
        },
        words: titleWords(r.title),
      });
    }
    for (const [track, candidates] of candidatesByTrack.entries()) {
      // Candidates come in source_count DESC order (SQL ORDER BY), so the
      // first kept representative is always the biggest of its cluster.
      const kept: Array<{ event: CentroidTrackSummary['top_events'][number]; words: Set<string> }> = [];
      for (const c of candidates) {
        const isDup = kept.some(k => dice(k.words, c.words) >= CARD_DICE_THRESHOLD);
        if (!isDup) kept.push(c);
        if (kept.length >= CARD_TOP_N) break;
      }
      topByTrack.set(track, kept.map(k => k.event));
    }
    // Fetch theme chips per-track in parallel
    const ctmIdByTrack = new Map<string, string>();
    const ctmIdRows = await query<{ id: string; track: string }>(
      `SELECT id::text, track FROM ctm WHERE centroid_id = $1 AND month = $2`,
      [centroidId, monthStart]
    );
    for (const r of ctmIdRows) ctmIdByTrack.set(r.track, r.id);
    const chipResults = await Promise.all(
      ctmRows.map(c => {
        const id = ctmIdByTrack.get(c.track);
        return id ? getCtmThemeChips(id, 3) : Promise.resolve([]);
      })
    );

    const tracks: CentroidTrackSummary[] = ctmRows.map((c, idx) => ({
      track: c.track,
      title_count: c.title_count,
      summary_text:
        locale === 'de' && c.summary_text_de ? c.summary_text_de : c.summary_text,
      last_active: c.last_active,
      theme_chips: chipResults[idx],
      top_events: topByTrack.get(c.track) || [],
    }));

    return {
      centroid_id: centroidId,
      month: monthStart,
      activity_stripe,
      tracks,
      prev_month: prevMonth,
      next_month: nextMonth,
    };
  });
}
