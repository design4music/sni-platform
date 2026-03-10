"""Materialize publisher analytics into mv_publisher_stats table.

Computes per-feed: track distribution, geographic focus (HHI),
top actors, narrative diversity, coverage concentration (Gini),
temporal patterns, and signal richness. All SQL -- no LLM calls.
"""

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config


def _load_publisher_map(cur):
    """Load feed_name -> [variant publisher_names] from DB.

    Uses the same publisher_map CTE pattern as the frontend:
    each feed's own name is always included, plus any known aliases
    stored in the publisher_aliases table (if it exists), or hardcoded
    from the canonical PUBLISHER_MAP_VALUES.
    """
    # The canonical map -- mirrors PUBLISHER_MAP_VALUES in queries.ts
    PUBLISHER_MAP = {}
    _PAIRS = [
        ("ABC News", "Australian Broadcasting Corporation"),
        ("ABC News", "ABC iview"),
        ("AFP", "AFP Fact Check"),
        ("AFP", "afp.com"),
        ("Al-Ahram", "Ahram Online"),
        ("Al Arabiya", "Al Arabiya English"),
        ("Al Arabiya", "alarabiya.net"),
        ("Al Jazeera", None),
        ("Anadolu Agency", "AA.com.tr"),
        ("Antara News", "ANTARA News"),
        ("Associated Press", "AP News"),
        ("Associated Press", "Associated Press News"),
        ("Bangkok Post", "bangkokpost.com"),
        ("BBC World", "BBC"),
        ("BelTA", None),
        ("Bloomberg", "Bloomberg.com"),
        ("BRICS Info", "infobrics.org"),
        ("CBC", "CBC Gem"),
        ("CGTN", "news.cgtn.com"),
        ("CGTN", "newsaf.cgtn.com"),
        ("CGTN", "newsus.cgtn.com"),
        ("Channel NewsAsia", "CNA"),
        ("Channel NewsAsia", "CNA Lifestyle"),
        ("China Daily", "China Daily - Global Edition"),
        ("CNN", "cnn.com"),
        ("Corriere della Sera", "corriere.it"),
        ("Corriere della Sera", "Corriere Milano"),
        ("Corriere della Sera", "Corriere Tv"),
        ("Corriere della Sera", "Corriere Roma"),
        ("CTV News", "CTV"),
        ("CTV News", "CTV More"),
        ("Daily Mirror", "Daily Mirror - Sri Lanka"),
        ("Daily Nation", "nation.africa"),
        ("Daily Sabah", "dailysabah.com"),
        ("Daily Star", "The Daily Star"),
        ("Der Spiegel", "Spiegel"),
        ("Deutsche Welle", "dw.com"),
        ("Deutsche Welle", "DW.com"),
        ("Deutsche Welle", "DW"),
        ("Dhaka Tribune", "dhakatribune.com"),
        ("El Pais", "EL PAIS"),
        ("El Pais", "EL PAIS English"),
        ("El Pais", "elpais.com"),
        ("ERR News", "ERR"),
        ("EurActiv", "Euractiv"),
        ("Euronews", "Euronews.com"),
        ("Express Tribune", "The Express Tribune"),
        ("Fox News", "foxnews.com"),
        ("Frankfurter Allgemeine", "FAZ"),
        ("Globe and Mail", "The Globe and Mail"),
        ("Gulf News", "gulfnews.com"),
        ("Gulf Times", "gulf-times.com"),
        ("i24NEWS", "i24news.tv"),
        ("Indian Express", "The Indian Express"),
        ("IRNA", "IRNA English"),
        ("Jakarta Post", "The Jakarta Post"),
        ("Japan Times", "The Japan Times"),
        ("Jerusalem Post", "The Jerusalem Post"),
        ("Jerusalem Post", "jpost.com"),
        ("Khaleej Times", "khaleejtimes.com"),
        ("Kommersant", "kommersant.ru"),
        ("Korea Herald", "The Korea Herald"),
        ("Korea Herald", "koreaherald.com"),
        ("Kyiv Post", "kyivpost.com"),
        ("La Repubblica", "la Repubblica"),
        ("La Repubblica", "repubblica.it"),
        ("Le Monde", "Le Monde.fr"),
        ("Lenta.ru", "lenta.ru"),
        ("LRT English", "LRT"),
        ("N1 Serbia", "N1"),
        ("NDTV", "NDTV Sports"),
        ("New Straits Times", "NST Online"),
        ("New York Times", "The New York Times"),
        ("New York Times", "nytimes.com"),
        ("NHK World", "nhk.or.jp"),
        ("Novinite", "Novinite.com"),
        ("People's Daily", "People's Daily Online"),
        ("Philippine Daily Inquirer", "Inquirer.net"),
        ("Press TV", "PressTV"),
        ("Punch", "Punch Newspapers"),
        ("Republic TV", "republic.tv"),
        ("RIA Novosti", "ria.ru"),
        ("Sputnik", "sputniknews.com"),
        ("Sydney Morning Herald", "The Sydney Morning Herald"),
        ("Tagesschau", "tagesschau.de"),
        ("TASS", "tass.com"),
        ("TASS Russian", "tass.ru"),
        ("The Hindu", "thehindu.com"),
        ("The National", "thenationalnews.com"),
        ("The News", "The News International"),
        ("Times of India", "The Times of India"),
        ("Times of Israel", "The Times of Israel"),
        ("Times of Israel", "timesofisrael.com"),
        ("UN News", "news.un.org"),
        ("Vanguard", "Vanguard News"),
        ("Voice of America", "VOA - Voice of America English News"),
        ("Wall Street Journal", "The Wall Street Journal"),
        ("Wall Street Journal", "WSJ"),
        ("Washington Post", "The Washington Post"),
        ("Washington Post", "washingtonpost.com"),
        ("Wired", "WIRED"),
        ("Xinhua", "Xinhuanet Deutsch"),
        ("YLE News", "Yle"),
        ("YLE News", "yle.fi"),
        ("Yonhap", "Yonhap News Agency"),
    ]
    for feed_name, variant in _PAIRS:
        if feed_name not in PUBLISHER_MAP:
            PUBLISHER_MAP[feed_name] = []
        if variant:
            PUBLISHER_MAP[feed_name].append(variant)

    return PUBLISHER_MAP


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def _herfindahl(counter):
    total = sum(counter.values())
    if total == 0:
        return 0.0
    return round(sum((c / total) ** 2 for c in counter.values()), 4)


def _gini(values):
    """Gini coefficient: 0 = perfectly equal, 1 = maximally concentrated."""
    if not values or sum(values) == 0:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    total = sum(sorted_vals)
    cumulative = 0.0
    weighted_sum = 0.0
    for i, v in enumerate(sorted_vals):
        cumulative += v
        weighted_sum += (2 * (i + 1) - n - 1) * v
    return round(weighted_sum / (n * total), 4)


def _top_n(counter, n=10):
    total = sum(counter.values())
    if total == 0:
        return []
    return [
        {"name": name, "count": count, "share": round(count / total, 3)}
        for name, count in counter.most_common(n)
    ]


def _compute_feed_stats(cur, feed_name, publisher_map):
    """Compute all analytics for a single feed. Returns stats dict or None."""
    # Build publisher name list for this feed
    variants = publisher_map.get(feed_name, [])
    pub_names = [feed_name] + variants

    placeholders = ",".join(["%s"] * len(pub_names))

    # Fetch all assigned titles with labels for this publisher
    cur.execute(
        f"""
        SELECT t.publisher_name, t.detected_language, t.pubdate_utc,
               ta.centroid_id, ta.track,
               tl.actor, tl.action_class, tl.domain,
               tl.persons, tl.orgs, tl.places
        FROM titles_v3 t
        JOIN title_assignments ta ON ta.title_id = t.id
        LEFT JOIN title_labels tl ON tl.title_id = t.id
        WHERE t.publisher_name IN ({placeholders})
        """,
        pub_names,
    )
    rows = cur.fetchall()

    if not rows or len(rows) < 10:
        return None

    title_count = len(rows)

    # Track distribution
    track_counter = Counter(r["track"] for r in rows if r["track"])
    track_total = sum(track_counter.values())
    track_distribution = (
        {t: round(c / track_total, 3) for t, c in track_counter.most_common()}
        if track_total
        else {}
    )

    # Geographic focus
    centroid_counter = Counter(r["centroid_id"] for r in rows if r["centroid_id"])
    geo_hhi = _herfindahl(centroid_counter)
    geo_gini = _gini(list(centroid_counter.values()))
    top_centroids = _top_n(centroid_counter, 10)

    # Actors
    actor_counter = Counter(r["actor"] for r in rows if r["actor"])
    top_actors = _top_n(actor_counter, 10)

    # Action class distribution
    action_counter = Counter(r["action_class"] for r in rows if r["action_class"])
    action_total = sum(action_counter.values())
    action_distribution = (
        {a: round(c / action_total, 3) for a, c in action_counter.most_common()}
        if action_total
        else {}
    )

    # Domain distribution
    domain_counter = Counter(r["domain"] for r in rows if r["domain"])
    domain_total = sum(domain_counter.values())
    domain_distribution = (
        {d: round(c / domain_total, 3) for d, c in domain_counter.most_common()}
        if domain_total
        else {}
    )

    # Language distribution
    lang_counter = Counter(
        r["detected_language"] for r in rows if r["detected_language"]
    )
    lang_total = sum(lang_counter.values())
    language_distribution = (
        {la: round(c / lang_total, 3) for la, c in lang_counter.most_common(5)}
        if lang_total
        else {}
    )

    # Signal richness: avg persons/orgs/places per title
    person_counts = [len(r["persons"] or []) for r in rows]
    org_counts = [len(r["orgs"] or []) for r in rows]
    place_counts = [len(r["places"] or []) for r in rows]
    signal_richness = round(
        (sum(person_counts) + sum(org_counts) + sum(place_counts)) / title_count, 2
    )

    # Temporal: day-of-week distribution (0=Mon, 6=Sun)
    dow_counter = Counter()
    hour_counter = Counter()
    for r in rows:
        if r["pubdate_utc"]:
            dow_counter[r["pubdate_utc"].weekday()] += 1
            hour_counter[r["pubdate_utc"].hour] += 1

    dow_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    dow_dist = {}
    dow_total = sum(dow_counter.values())
    if dow_total:
        for i in range(7):
            dow_dist[dow_names[i]] = round(dow_counter.get(i, 0) / dow_total, 3)

    # Peak hour
    peak_hour = hour_counter.most_common(1)[0][0] if hour_counter else None

    # Narrative diversity: count distinct narrative frames this publisher appears in
    cur.execute(
        f"""
        SELECT COUNT(*) FROM narratives
        WHERE EXISTS (
            SELECT 1 FROM unnest(top_sources) AS src
            WHERE src IN ({placeholders})
        )
        """,
        pub_names,
    )
    narrative_frame_count = cur.fetchone()["count"]

    return {
        "title_count": title_count,
        "centroid_count": len(centroid_counter),
        "track_distribution": track_distribution,
        "geo_hhi": geo_hhi,
        "geo_gini": geo_gini,
        "top_centroids": top_centroids,
        "top_actors": top_actors,
        "action_distribution": action_distribution,
        "domain_distribution": domain_distribution,
        "language_distribution": language_distribution,
        "signal_richness": signal_richness,
        "dow_distribution": dow_dist,
        "peak_hour": peak_hour,
        "narrative_frame_count": narrative_frame_count,
    }


def materialize(feed_name=None):
    """Compute and upsert publisher stats.

    Args:
        feed_name: specific feed name. None = all active feeds.
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            publisher_map = _load_publisher_map(cur)

            if feed_name:
                feeds = [{"name": feed_name}]
            else:
                cur.execute(
                    "SELECT name FROM feeds WHERE is_active = true ORDER BY name"
                )
                feeds = cur.fetchall()

            if not feeds:
                print("No feeds to process")
                return

            total = 0
            skipped = 0
            for f in feeds:
                name = f["name"]
                start = time.time()
                stats = _compute_feed_stats(cur, name, publisher_map)
                elapsed = time.time() - start

                if stats is None:
                    skipped += 1
                    continue

                cur.execute(
                    """INSERT INTO mv_publisher_stats (feed_name, stats, updated_at)
                       VALUES (%s, %s, NOW())
                       ON CONFLICT (feed_name) DO UPDATE
                       SET stats = EXCLUDED.stats, updated_at = NOW()""",
                    (name, json.dumps(stats)),
                )
                total += 1
                print("  %s: %d titles (%.1fs)" % (name, stats["title_count"], elapsed))

            conn.commit()
            print(
                "Done: %d feeds materialized, %d skipped (<10 titles)"
                % (total, skipped)
            )
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Materialize publisher analytics")
    parser.add_argument("--feed", help="Specific feed name")
    args = parser.parse_args()
    materialize(feed_name=args.feed)


if __name__ == "__main__":
    main()
