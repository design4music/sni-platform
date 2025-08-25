#!/usr/bin/env python3
"""
CLUST-1 taxonomy-aware clustering with 4 stages: seed, densify, refine, persist.
Deterministic, LLM-free implementation for scalable clustering.
"""

import argparse
import hashlib
import logging
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from itertools import combinations
from pathlib import Path

import numpy as np
from psycopg2.extras import execute_batch

# Add project root to path for centralized config
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import centralized database connection
from etl_pipeline.core.config import get_db_connection

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Database connection now uses centralized system


def generate_topic_key(topic_combo):
    """Generate deterministic hash key for topic combination."""
    sorted_combo = "::".join(sorted(topic_combo))
    return hashlib.sha1(sorted_combo.encode()).hexdigest()


def pick_keys(core_tokens, countries, event_set):
    """Pick gpe_key and event_key for recall mode clustering."""
    # gpe_key: top-2 countries (sorted)
    g = sorted(list(countries))[:2]
    gpe_key = tuple(g) if g else tuple()

    # event_key: pick the first event token present, fallback to None
    ev = None
    for t in core_tokens:
        if t in event_set:
            ev = t
            break

    return gpe_key, ev


def get_event_tokens(conn, days=30):
    """Load event tokens from materialized view."""
    cur = conn.cursor()
    try:
        # Try event_tokens_30d first, fallback to 14d
        try:
            cur.execute(f"SELECT token FROM event_tokens_{days}d")
        except Exception as e:
            logger.warning(
                f"event_tokens_{days}d not found ({e}), trying event_tokens_14d"
            )
            try:
                cur.execute("SELECT token FROM event_tokens_14d")
            except Exception:
                # Fallback to predefined event tokens
                logger.warning("No event_tokens views found, using predefined list")
                return {
                    "tariffs",
                    "sanctions",
                    "ceasefire",
                    "election",
                    "referendum",
                    "missile",
                    "drone",
                    "oil",
                    "gas",
                    "war",
                    "peace",
                    "treaty",
                    "summit",
                    "meeting",
                    "talks",
                    "negotiations",
                    "conflict",
                }

        return {row[0] for row in cur.fetchall()}
    finally:
        cur.close()


def load_hub_tokens(conn):
    """Load hub tokens from keyword_hubs_30d materialized view."""
    cur = conn.cursor()
    try:
        cur.execute("SELECT tok FROM keyword_hubs_30d")
        return {row[0] for row in cur.fetchall()}
    except Exception as e:
        logger.warning(f"Failed to load hub tokens: {e}")
        return set()
    finally:
        cur.close()


def load_event_anchored_triads(conn, use_clean_events=0):
    """Load event-anchored triads from materialized view."""
    cur = conn.cursor()
    try:
        # Choose triads table based on clean events flag
        table = (
            "event_anchored_triads_clean_30d"
            if use_clean_events
            else "event_anchored_triads_30d"
        )

        cur.execute(f"SELECT hub1, hub2, event_tok, co_doc FROM {table}")
        triads = {}
        for hub1, hub2, event_tok, co_doc in cur.fetchall():
            triads[(hub1, hub2, event_tok)] = co_doc

        event_type = "clean" if use_clean_events else "original"
        logger.info(f"Loaded {len(triads)} event-anchored triads ({event_type} events)")
        return triads
    except Exception as e:
        # Fallback to original triads if clean version fails
        if use_clean_events:
            logger.warning(
                f"Failed to load clean triads ({e}), falling back to original"
            )
            return load_event_anchored_triads(conn, use_clean_events=0)
        else:
            logger.warning(f"Failed to load event-anchored triads: {e}")
            return {}
    finally:
        cur.close()


def load_event_signals(conn):
    """Load event signals (tokens + bigrams) from materialized view."""
    cur = conn.cursor()
    try:
        cur.execute("SELECT signal FROM event_signals_30d")
        signals = {row[0] for row in cur.fetchall()}
        logger.info(f"Loaded {len(signals)} event signals")
        return signals
    except Exception as e:
        logger.warning(f"Failed to load event signals: {e}")
        return set()
    finally:
        cur.close()


def has_event_signal(article_keywords, article_title, event_signals):
    """Check if article has any event signal (token or title bigram)."""
    # Check keywords for event tokens
    for keyword in article_keywords:
        if keyword in event_signals:
            return True

    # Check title for event bigrams
    if article_title:
        title_clean = article_title.lower()
        # Generate bigrams from title
        words = title_clean.split()
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}"
            if bigram in event_signals:
                return True

    return False


def load_country_tokens(conn):
    """Load country tokens from ref_countries table."""
    cur = conn.cursor()
    try:
        cur.execute("SELECT name FROM ref_countries")
        countries = {row[0].lower() for row in cur.fetchall()}
        # Add common country aliases
        country_aliases = {
            "united states": {"usa", "america", "us"},
            "united kingdom": {"uk", "britain"},
            "russia": {"russian federation"},
            "china": {"prc"},
        }
        for country, aliases in country_aliases.items():
            if country in countries:
                countries.update(aliases)
        return countries
    except Exception as e:
        logger.warning(f"Failed to load country tokens: {e}")
        # Fallback to basic set
        return {
            "united states",
            "usa",
            "china",
            "russia",
            "ukraine",
            "israel",
            "iran",
            "india",
            "germany",
            "france",
            "uk",
            "britain",
        }
    finally:
        cur.close()


def matches_event_anchored_triad(article_tokens, triads_dict, hubs_set, events_set):
    """Check if article tokens match any event-anchored triad pattern."""
    article_hubs = [token for token in article_tokens if token in hubs_set]
    article_events = [token for token in article_tokens if token in events_set]

    if len(article_hubs) >= 2 and len(article_events) >= 1:
        # Check all hub pairs with each event
        for i in range(len(article_hubs)):
            for j in range(i + 1, len(article_hubs)):
                hub1, hub2 = sorted([article_hubs[i], article_hubs[j]])
                for event in article_events:
                    if (hub1, hub2, event) in triads_dict:
                        return True, (hub1, hub2, event)
    return False, None


def get_countries_from_tokens(tokens):
    """Extract country names from token list (comprehensive GPE detection)."""
    # Expanded country and region names for better recall
    countries = {
        "united states",
        "usa",
        "america",
        "china",
        "russia",
        "ukraine",
        "israel",
        "iran",
        "india",
        "germany",
        "france",
        "united kingdom",
        "uk",
        "britain",
        "japan",
        "south korea",
        "north korea",
        "brazil",
        "turkey",
        "egypt",
        "saudi arabia",
        "australia",
        "canada",
        "mexico",
        "italy",
        "spain",
        "poland",
        "netherlands",
        "belgium",
        "sweden",
        "norway",
        "denmark",
        "syria",
        "iraq",
        "afghanistan",
        "pakistan",
        "bangladesh",
        "philippines",
        "indonesia",
        "malaysia",
        "singapore",
        "thailand",
        "vietnam",
        "taiwan",
        "hong kong",
        "lebanon",
        "jordan",
        "yemen",
        "oman",
        "qatar",
        "kuwait",
        "uae",
        "south africa",
        "nigeria",
        "kenya",
        "ethiopia",
        "ghana",
        "morocco",
        "algeria",
        "libya",
        "tunisia",
        "greece",
        "portugal",
        "czech republic",
        "hungary",
        "romania",
        "bulgaria",
        "croatia",
        "serbia",
        "bosnia",
        "albania",
        "slovenia",
        "slovakia",
        "estonia",
        "latvia",
        "lithuania",
        "finland",
        "iceland",
        "ireland",
        "scotland",
        "wales",
        "england",
        # Regions and cities that indicate geographic context
        "europe",
        "asia",
        "africa",
        "middle east",
        "eurasia",
        "balkans",
        "moscow",
        "beijing",
        "tokyo",
        "london",
        "paris",
        "berlin",
        "washington",
        "kyiv",
        "tel aviv",
        "jerusalem",
        "tehran",
        "seoul",
        "new delhi",
        "mumbai",
        "dubai",
        # Alaska as special case
        "alaska",
        "greenland",
        "siberia",
        "crimea",
        "gaza",
        "west bank",
        "golan heights",
    }

    found_countries = set()
    for token in tokens:
        token_lower = token.lower().strip()
        if token_lower in countries:
            found_countries.add(token_lower)
        # Also check if token contains country name
        elif any(country in token_lower for country in countries if len(country) > 3):
            for country in countries:
                if len(country) > 3 and country in token_lower:
                    found_countries.add(country)
                    break

    return found_countries


def get_articles_with_core_keywords(conn, hours_back=72, lang=None):
    """Get articles with their core keywords from the specified time window."""
    cur = conn.cursor()
    try:
        lang_filter = "AND a.language = %s" if lang else ""
        query_params = [datetime.now() - timedelta(hours=hours_back)]
        if lang:
            query_params.append(lang)

        query = f"""
            SELECT 
                a.id,
                a.title,
                a.published_at,
                a.source_name,
                a.language,
                array_agg(ck.token ORDER BY ck.score DESC) as core_keywords,
                array_agg(ck.score ORDER BY ck.score DESC) as scores
            FROM articles a
            JOIN article_core_keywords ck ON a.id = ck.article_id
            WHERE a.published_at >= %s
            {lang_filter}
            GROUP BY a.id, a.title, a.published_at, a.source_name, a.language
            HAVING COUNT(ck.token) >= 3
            ORDER BY a.published_at DESC
        """

        cur.execute(query, query_params)
        articles = cur.fetchall()

        logger.info(
            "Found {} articles with core keywords from last {} hours{}".format(
                len(articles), hours_back, f" (lang: {lang})" if lang else ""
            )
        )
        return articles

    finally:
        cur.close()


def get_articles_with_topics(conn, hours_back=72, lang=None):
    """Get articles with their top topics from the specified time window (DEPRECATED - use core keywords)."""
    cur = conn.cursor()
    try:
        lang_filter = "AND a.language = %s" if lang else ""
        query_params = [datetime.now() - timedelta(hours=hours_back)]
        if lang:
            query_params.append(lang)

        query = f"""
            SELECT 
                a.id,
                a.title,
                a.published_at,
                a.source_name,
                a.language,
                array_agg(at.topic_id ORDER BY at.score DESC) as topics,
                array_agg(at.score ORDER BY at.score DESC) as scores
            FROM articles a
            JOIN article_topics at ON a.id = at.article_id
            WHERE a.published_at >= %s
            {lang_filter}
            GROUP BY a.id, a.title, a.published_at, a.source_name, a.language
            HAVING COUNT(at.topic_id) >= 1
            ORDER BY a.published_at DESC
        """

        cur.execute(query, query_params)
        articles = cur.fetchall()

        logger.info(
            "Found {} articles with topics from last {} hours{}".format(
                len(articles), hours_back, f" (lang: {lang})" if lang else ""
            )
        )
        return articles

    finally:
        cur.close()


def load_triad_pairs(conn, hub_tokens):
    """Preload triad pairs once at seed init - drop-in enhancement for better seed detection."""
    cur = conn.cursor()
    try:
        # Check if anchor_triads_30d materialized view exists
        cur.execute(
            """
            SELECT EXISTS (
                SELECT 1 FROM pg_matviews 
                WHERE matviewname = 'anchor_triads_30d'
            )
        """
        )
        if not cur.fetchone()[0]:
            logger.warning(
                "anchor_triads_30d table not found, skipping triad enhancement"
            )
            return set()

        cur.execute("SELECT t1, t2, t3 FROM anchor_triads_30d")
        triad_pairs = set()

        for row in cur.fetchall():
            t1, t2, t3 = row[0], row[1], row[2]
            # Generate all pairs from each triad, excluding hubs
            for a, b in ((t1, t2), (t1, t3), (t2, t3)):
                if a not in hub_tokens and b not in hub_tokens:
                    triad_pairs.add(tuple(sorted((a, b))))

        return triad_pairs
    finally:
        cur.close()


def triad_seed_ok(article_tokens, hub_tokens, triad_pairs):
    """Tiny helper: check if any 2-of-3 triad pattern is present in article tokens."""
    if not triad_pairs:
        return False

    # Exclude hub tokens for cleaner matching
    toks = [t for t in article_tokens if t not in hub_tokens]

    # Check all pairs of non-hub tokens against triad pairs
    for i in range(len(toks)):
        for j in range(i + 1, len(toks)):
            if tuple(sorted((toks[i], toks[j]))) in triad_pairs:
                return True
    return False


def stage_seed(
    conn,
    hours_back=72,
    lang=None,
    profile="strict",
    use_triads=0,
    use_hub_assist=0,
    **kwargs,
):
    """Stage 1: Create seed clusters based on core keyword combinations."""
    logger.info(
        "Starting seed stage (window: {}h, lang: {}, profile: {}, hub_assist: {}) - USING CORE KEYWORDS".format(
            hours_back, lang, profile, use_hub_assist
        )
    )

    if profile == "recall":
        return stage_seed_recall(conn, hours_back, lang)

    # Continue with strict mode below

    articles = get_articles_with_core_keywords(conn, hours_back, lang)
    if not articles:
        logger.warning("No articles with core keywords found")
        return {}

    # Build keyword combinations for each article (top 3 keywords with concept clustering)
    keyword_combos = defaultdict(list)

    # Load normalizer for concept clustering
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
    from etl_pipeline.extraction.keyword_normalizer import get_normalizer

    normalizer = get_normalizer()

    # Load hub and specificity data for filtering
    cur = conn.cursor()
    try:
        hubs_query = """
            SELECT tok FROM keyword_hubs_30d
        """
        cur.execute(hubs_query)
        hub_tokens = set(row[0] for row in cur.fetchall())

        specificity_query = """
            SELECT tok, spec FROM keyword_specificity_30d
        """
        cur.execute(specificity_query)
        token_specificity = dict(cur.fetchall())

        # Load anchored-rare pairs for special seeding
        anchored_pairs_query = """
            SELECT t1, t2, co_doc FROM anchor_pairs_30d
            WHERE co_doc >= 4
        """
        cur.execute(anchored_pairs_query)
        anchored_pairs = {}
        for tok_a, tok_b, co_doc in cur.fetchall():
            anchored_pairs[(tok_a, tok_b)] = co_doc
            anchored_pairs[(tok_b, tok_a)] = co_doc  # Both directions

        logger.info(
            f"Loaded {len(hub_tokens)} hub tokens, {len(token_specificity)} specificity scores, and {len(anchored_pairs)//2} anchored pairs"
        )
    finally:
        cur.close()

    # Preload triad pairs for enhanced seed detection (drop-in enhancement)
    if use_triads:
        triad_pairs = load_triad_pairs(conn, hub_tokens)
        logger.info(
            f"Loaded {len(triad_pairs)} triad pairs for enhanced seed detection"
        )
    else:
        triad_pairs = {}
        logger.info("Triad seeding disabled (--use_triads 0)")

    for (
        article_id,
        title,
        published_at,
        source_name,
        language,
        core_keywords,
        scores,
    ) in articles:
        # Take top 3 keywords with score > 0, apply concept clustering
        valid_keywords = []
        for i in range(min(3, len(core_keywords))):
            if scores[i] > 0:
                keyword = core_keywords[i]
                # Get concept cluster for overlap counting
                cluster = normalizer.get_concept_cluster(keyword)
                valid_keywords.append(cluster)

        if len(valid_keywords) >= 2:
            # Generate 2-3 keyword combinations with hub-suppression and specificity gate
            for combo_size in range(2, min(4, len(valid_keywords) + 1)):
                if combo_size <= len(valid_keywords):
                    for combo in combinations(valid_keywords, combo_size):
                        # Apply hub-suppression: reject if both tokens are hubs
                        combo_hubs = [tok for tok in combo if tok in hub_tokens]

                        # Event+geo exception: allow event + geo/person even if geo/person is hub
                        event_tokens = {
                            "tariffs",
                            "sanctions",
                            "ceasefire",
                            "election",
                            "referendum",
                            "missile",
                            "drone",
                            "oil",
                            "gas",
                        }

                        has_event = any(tok in event_tokens for tok in combo)
                        if has_event and len(combo_hubs) <= 1:
                            pass  # Allow event + hub combination
                        elif len(combo_hubs) >= 2:
                            continue  # Skip if 2+ hubs in combination (no event exception)

                        # Apply specificity gate: require spec(a) + spec(b) >= 0.80
                        total_specificity = sum(
                            token_specificity.get(tok, 0.0) for tok in combo
                        )

                        # Anchored-rare exception: allow if (lib token, rare token) has co_doc >= 5
                        is_anchored_rare = False
                        if len(combo) == 2 and total_specificity < 0.80:
                            tok_a, tok_b = sorted(combo)
                            if (tok_a, tok_b) in anchored_pairs and anchored_pairs[
                                (tok_a, tok_b)
                            ] >= 5:
                                is_anchored_rare = True

                        if not is_anchored_rare and total_specificity < 0.80:
                            continue  # Skip low-specificity combinations unless anchored-rare

                        topic_key = generate_topic_key(combo)
                        keyword_combos[topic_key].append(
                            {
                                "article_id": article_id,
                                "title": title,
                                "published_at": published_at,
                                "source_name": source_name,
                                "language": language,
                                "keywords": list(combo),
                                "combo_size": combo_size,
                            }
                        )

    # Filter seeds: size >= 3 and >= 2 unique sources (base rule)
    seeds = {}
    for topic_key, members in keyword_combos.items():
        if len(members) >= 3:
            unique_sources = set(m["source_name"] for m in members)
            if len(unique_sources) >= 2:
                seeds[topic_key] = {
                    "members": members,
                    "size": len(members),
                    "sources": unique_sources,
                    "keywords": members[0][
                        "keywords"
                    ],  # All members have same keyword clusters
                    "lang": lang,
                }

    base_seeds = len(seeds)

    # Enhanced triad seeding: create single-article seeds for strong triad patterns
    if triad_pairs:
        processed_articles = set()
        # Get all articles already in seeds
        for seed_data in seeds.values():
            for member in seed_data["members"]:
                processed_articles.add(member["article_id"])

        # Check remaining articles for triad patterns
        triad_seeds_added = 0
        for (
            article_id,
            title,
            published_at,
            source_name,
            language,
            core_keywords,
            scores,
        ) in articles:
            if article_id in processed_articles:
                continue  # Already in a seed cluster

            # Extract top keywords for triad check
            valid_keywords = []
            for i in range(min(3, len(core_keywords))):
                if scores[i] > 0:
                    keyword = core_keywords[i]
                    cluster = normalizer.get_concept_cluster(keyword)
                    valid_keywords.append(cluster)

            # Check if article has triad pattern
            if triad_seed_ok(valid_keywords, hub_tokens, triad_pairs):
                # Create single-article seed with triad pattern
                topic_key = f"triad_{article_id}"
                seeds[topic_key] = {
                    "members": [
                        {
                            "article_id": article_id,
                            "title": title,
                            "published_at": published_at,
                            "source_name": source_name,
                            "language": language,
                            "keywords": valid_keywords[:3],  # Top 3 keywords
                            "combo_size": len(valid_keywords),
                        }
                    ],
                    "size": 1,
                    "sources": {source_name},
                    "keywords": valid_keywords[:3],
                    "lang": lang,
                    "triad_seed": True,  # Mark as triad-based seed
                }
                triad_seeds_added += 1

        if triad_seeds_added > 0:
            logger.info(
                f"Added {triad_seeds_added} triad-pattern seeds to {base_seeds} base seeds"
            )

    # Phase A: Hub-assisted seeding (event-anchored triads)
    hub_assist_seeds_added = 0
    if use_hub_assist:
        # Load Phase A data with event signals
        hub_tokens_set = load_hub_tokens(conn)
        event_tokens_set = get_event_tokens(conn, 30)
        event_triads = load_event_anchored_triads(
            conn, kwargs.get("use_clean_events", 0)
        )
        event_signals = load_event_signals(conn)

        logger.info(
            f"Phase A: Loaded {len(hub_tokens_set)} hubs, {len(event_tokens_set)} events, {len(event_triads)} triads, {len(event_signals)} signals"
        )

        # Get articles already processed
        processed_articles = set()
        for seed_data in seeds.values():
            for member in seed_data["members"]:
                processed_articles.add(member["article_id"])

        # Check remaining articles for event-anchored triad patterns
        for (
            article_id,
            title,
            published_at,
            source_name,
            language,
            core_keywords,
            scores,
        ) in articles:
            if article_id in processed_articles:
                continue

            # Extract valid keywords
            valid_keywords = []
            for i in range(
                min(8, len(core_keywords))
            ):  # Look at top 8 for more coverage
                if scores[i] > 0:
                    keyword = core_keywords[i]
                    cluster = normalizer.get_concept_cluster(keyword)
                    valid_keywords.append(cluster)

            # Gate by event signal presence - require article to have event signal
            has_signal = has_event_signal(valid_keywords, title, event_signals)

            if not has_signal:
                continue  # Skip articles without event signals for hub-assist

            # Check for event-anchored triad match
            matches_triad, triad_info = matches_event_anchored_triad(
                valid_keywords, event_triads, hub_tokens_set, event_tokens_set
            )

            if matches_triad:
                # Create seed cluster for this triad pattern
                hub1, hub2, event = triad_info
                topic_key = f"triad_{hub1}_{hub2}_{event}_{article_id}"

                seeds[topic_key] = {
                    "members": [
                        {
                            "article_id": article_id,
                            "title": title,
                            "published_at": published_at,
                            "source_name": source_name,
                            "language": language,
                            "keywords": valid_keywords,
                            "seed_type": "event_triad",
                        }
                    ],
                    "size": 1,
                    "sources": {source_name},
                    "keywords": [hub1, hub2, event],
                    "lang": lang,
                    "triad_pattern": (hub1, hub2, event),
                }
                processed_articles.add(article_id)
                hub_assist_seeds_added += 1

        if hub_assist_seeds_added > 0:
            logger.info(
                f"Phase A: Added {hub_assist_seeds_added} event-anchored triad seeds"
            )

    # Phase A: Enhanced logging with detailed counters
    triad_seeds = len(seeds) - base_seeds - hub_assist_seeds_added
    logger.info("=== PHASE A SEED STAGE SUMMARY ===")
    logger.info(f"Total seeds created: {len(seeds)}")
    logger.info(f"  Base (strict) seeds: {base_seeds}")
    logger.info(f"  Legacy triad seeds: {triad_seeds}")
    logger.info(f"  Hub-assist triad seeds: {hub_assist_seeds_added}")

    if use_hub_assist:
        logger.info(f"Hub-assist mode: ENABLED (+{hub_assist_seeds_added} seeds)")
    else:
        logger.info("Hub-assist mode: DISABLED (production default)")

    logger.info(
        "Created {} seed clusters ({} base + {} triad + {} hub-assist)".format(
            len(seeds), base_seeds, triad_seeds, hub_assist_seeds_added
        )
    )

    # Store seeds temporarily (in-memory for this MVP)
    return seeds


def stage_seed_recall(conn, hours_back=72, lang=None):
    """Recall mode seeding with gpe_key + event_key binning."""
    logger.info(f"Starting recall mode seeding (window: {hours_back}h, lang: {lang})")

    articles = get_articles_with_core_keywords(conn, hours_back, lang)
    if not articles:
        logger.warning("No articles with core keywords found")
        return {}

    # Load event tokens and countries
    event_set = get_event_tokens(conn, 30)
    logger.info(f"Loaded {len(event_set)} event tokens")

    # Load anchor pairs for alternative seeding
    cur = conn.cursor()
    try:
        cur.execute("SELECT t1, t2, co_doc FROM anchor_pairs_30d WHERE co_doc >= 4")
        anchored_pairs = {}
        for tok_a, tok_b, co_doc in cur.fetchall():
            anchored_pairs[(tok_a, tok_b)] = co_doc
            anchored_pairs[(tok_b, tok_a)] = co_doc
    finally:
        cur.close()

    # Build bins based on gpe_key + event_key
    bins = defaultdict(list)

    for (
        article_id,
        title,
        published_at,
        source_name,
        language,
        core_keywords,
        scores,
    ) in articles:
        # Extract core tokens and countries
        core_tokens = set(core_keywords[:5])  # Top 5 keywords
        countries = get_countries_from_tokens(core_tokens)

        # Pick keys for this article
        gpe_key, event_key = pick_keys(core_tokens, countries, event_set)

        # Create bin identifier
        bin_id = (gpe_key, event_key)

        # Alternative seeding: anchor_pair + (>=1 country or >=1 org)
        has_anchor_pair = False
        for tok_a in core_tokens:
            for tok_b in core_tokens:
                if tok_a < tok_b and (tok_a, tok_b) in anchored_pairs:
                    has_anchor_pair = True
                    break
            if has_anchor_pair:
                break

        # Much more permissive seeding for recall mode:
        # 1. Any geographic context (country/region)
        # 2. Any event context
        # 3. Anchor pair + any entity
        # 4. Fallback: top 2 keywords if no other context
        should_seed = False

        if gpe_key:  # Any geographic context
            should_seed = True
        elif event_key:  # Any event context
            should_seed = True
        elif has_anchor_pair:  # Any anchor pair
            should_seed = True
            bin_id = f"anchor_{article_id}"
        else:
            # Fallback: create bin from top 2 keywords for broader coverage
            if len(core_tokens) >= 2:
                top_2_keywords = sorted(list(core_tokens))[:2]
                bin_id = f"keywords_{'_'.join(top_2_keywords)}"
                should_seed = True

        if should_seed:
            bins[bin_id].append(
                {
                    "article_id": article_id,
                    "title": title,
                    "published_at": published_at,
                    "source_name": source_name,
                    "language": language,
                    "keywords": list(core_tokens),
                    "gpe_key": gpe_key,
                    "event_key": event_key,
                    "countries": countries,
                }
            )

    # Convert bins to seeds (recall mode: meaningful clusters only)
    seeds = {}
    for bin_id, members in bins.items():
        if (
            len(members) >= 2
        ):  # Recall mode: still need meaningful clusters (min 2 articles)
            unique_sources = set(m["source_name"] for m in members)
            # Recall mode: min sources 1 (but mark single-source clusters)

            seeds[str(bin_id)] = {
                "members": members,
                "size": len(members),
                "sources": unique_sources,
                "keywords": members[0]["keywords"],
                "lang": lang,
                "gpe_key": members[0]["gpe_key"],
                "event_key": members[0]["event_key"],
                "source_diversity": len(unique_sources),  # Mark for CLUST-2
                "recall_seed": True,
            }

    logger.info(f"Created {len(seeds)} recall mode seed clusters")
    return seeds


def get_cosine_similarity(conn, article_id1, article_id2):
    """Get cosine similarity between two articles using title embeddings."""
    cur = conn.cursor()
    try:
        query = """
            SELECT 
                ae1.title_embedding <=> ae2.title_embedding as distance
            FROM article_embeddings ae1, article_embeddings ae2
            WHERE ae1.article_id = %s AND ae2.article_id = %s
            AND ae1.title_embedding IS NOT NULL 
            AND ae2.title_embedding IS NOT NULL
        """
        cur.execute(query, (article_id1, article_id2))
        result = cur.fetchone()

        if result:
            # Convert cosine distance to similarity
            return 1.0 - result[0]
        return 0.0

    except Exception as e:
        logger.debug("Error getting cosine similarity: {}".format(e))
        return 0.0
    finally:
        cur.close()


def find_similar_articles(
    conn, seed_member_ids, hours_back=72, lang=None, cos_threshold=0.82
):
    """Find articles similar to seed members using embeddings."""
    if not seed_member_ids:
        return []

    cur = conn.cursor()
    try:
        lang_filter = "AND a.language = %s" if lang else ""
        query_params = [datetime.now() - timedelta(hours=hours_back)]
        if lang:
            query_params.append(lang)

        # Find articles with embeddings in the time window
        query = f"""
            SELECT DISTINCT a.id, a.title, a.published_at, a.source_name, a.language
            FROM articles a
            JOIN article_embeddings ae ON a.id = ae.article_id
            WHERE a.published_at >= %s
            {lang_filter}
            AND ae.title_embedding IS NOT NULL
            AND a.id NOT IN %s
            ORDER BY a.published_at DESC
            LIMIT 1000
        """

        cur.execute(query, query_params + [tuple(seed_member_ids)])
        candidate_articles = cur.fetchall()

        similar_articles = []

        # Check cosine similarity against seed members (limit to k=20 per seed member)
        for (
            candidate_id,
            title,
            published_at,
            source_name,
            language,
        ) in candidate_articles:
            max_similarity = 0.0

            # Check against up to 5 seed members for efficiency
            for seed_member_id in seed_member_ids[:5]:
                similarity = get_cosine_similarity(conn, candidate_id, seed_member_id)
                max_similarity = max(max_similarity, similarity)

                if max_similarity >= cos_threshold:
                    break

            if max_similarity >= cos_threshold:
                similar_articles.append(
                    {
                        "article_id": candidate_id,
                        "title": title,
                        "published_at": published_at,
                        "source_name": source_name,
                        "language": language,
                        "similarity": max_similarity,
                    }
                )

        return similar_articles[:20]  # Limit to top 20 similar articles per seed

    finally:
        cur.close()


def stage_densify(
    conn,
    seeds,
    hours_back=72,
    lang=None,
    cos_threshold=0.82,
    profile="strict",
    use_hub_assist=0,
    hub_pair_cos=0.90,
    **kwargs,
):
    """Stage 2: Densify clusters by adding similar articles with hub-suppression."""
    logger.info(
        "Starting densify stage (cos_threshold: {}, profile: {}, hub_assist: {})".format(
            cos_threshold, profile, use_hub_assist
        )
    )

    if not seeds:
        logger.warning("No seeds to densify")
        return seeds

    # Load hub tokens and event signals for densify logic
    cur = conn.cursor()
    try:
        cur.execute("SELECT tok FROM keyword_hubs_30d")
        hub_tokens = set(row[0] for row in cur.fetchall())
        logger.info(f"Loaded {len(hub_tokens)} hub tokens for densify stage")
    finally:
        cur.close()

    # Load event signals for hub-assist gating
    event_signals = set()
    if use_hub_assist:
        event_signals = load_event_signals(conn)

    if profile == "recall":
        return stage_densify_recall(conn, seeds, hours_back, lang, hub_tokens)

    densified_seeds = {}

    for topic_key, seed_data in seeds.items():
        logger.debug(
            "Densifying seed {} (size: {})".format(topic_key, seed_data["size"])
        )

        # Get articles with shared keywords
        seed_member_ids = [m["article_id"] for m in seed_data["members"]]
        seed_keywords = set(seed_data["keywords"])

        # Find articles that share >= 2 keywords OR share >= 1 keyword + high cosine similarity
        cur = conn.cursor()
        try:
            lang_filter = "AND a.language = %s" if lang else ""
            query_params = [
                datetime.now() - timedelta(hours=hours_back),
                tuple(seed_member_ids),
            ]
            if lang:
                query_params.append(lang)

            # Find articles with keyword overlap
            query = f"""
                SELECT 
                    a.id, a.title, a.published_at, a.source_name, a.language,
                    array_agg(ck.token) as keywords,
                    array_agg(ck.score) as scores
                FROM articles a
                JOIN article_core_keywords ck ON a.id = ck.article_id
                WHERE a.published_at >= %s
                AND a.id NOT IN %s
                {lang_filter}
                GROUP BY a.id, a.title, a.published_at, a.source_name, a.language
                HAVING array_agg(ck.token) && %s
            """

            cur.execute(query, query_params + [list(seed_keywords)])
            candidates = cur.fetchall()

            added_members = []

            for (
                candidate_id,
                title,
                published_at,
                source_name,
                language,
                keywords,
                scores,
            ) in candidates:
                candidate_keywords = set(keywords)

                # Compute shared_nonhub: shared tokens excluding hubs
                shared_tokens = seed_keywords.intersection(candidate_keywords)
                shared_nonhub = len(
                    [tok for tok in shared_tokens if tok not in hub_tokens]
                )

                should_add = False

                # Rule 1: shared_nonhub >= 2
                if shared_nonhub >= 2:
                    should_add = True
                    reason = f"shared_nonhub_{shared_nonhub}"

                # Rule 2: shared_nonhub >= 1 AND high cosine similarity >= 0.90
                elif shared_nonhub >= 1:
                    # Check cosine similarity with seed members
                    max_similarity = 0.0
                    for seed_member_id in seed_member_ids[
                        :3
                    ]:  # Check against top 3 seed members
                        similarity = get_cosine_similarity(
                            conn, candidate_id, seed_member_id
                        )
                        max_similarity = max(max_similarity, similarity)

                        if (
                            max_similarity >= 0.86
                        ):  # Even gentler threshold for recall boost
                            break

                    if max_similarity >= 0.86:
                        should_add = True
                        reason = f"shared_nonhub_1+cos_{max_similarity:.3f}"

                # Phase A: Hub-pair admission rule (when hub assist enabled)
                if not should_add and use_hub_assist:
                    # Gate by event signal presence - require candidate to have event signal
                    candidate_has_signal = has_event_signal(
                        candidate_keywords, title, event_signals
                    )

                    if not candidate_has_signal:
                        continue  # Skip candidates without event signals for hub-assist

                    # Check if candidate shares 2+ hubs with seed
                    candidate_hubs = [
                        tok for tok in candidate_keywords if tok in hub_tokens
                    ]
                    seed_hubs = [tok for tok in seed_keywords if tok in hub_tokens]
                    shared_hubs = set(candidate_hubs).intersection(set(seed_hubs))

                    if len(shared_hubs) >= 2:
                        # Check if same country set (1-2 countries)
                        candidate_countries = get_countries_from_tokens(
                            candidate_keywords
                        )
                        seed_countries = get_countries_from_tokens(seed_keywords)

                        if (
                            candidate_countries == seed_countries
                            and len(candidate_countries) <= 2
                        ):
                            # Check cosine similarity with hub_pair_cos threshold
                            max_similarity = 0.0
                            for seed_member_id in seed_member_ids[:3]:
                                similarity = get_cosine_similarity(
                                    conn, candidate_id, seed_member_id
                                )
                                max_similarity = max(max_similarity, similarity)
                                if max_similarity >= hub_pair_cos:
                                    break

                            if max_similarity >= hub_pair_cos:
                                should_add = True
                                reason = f"hub_pair_{len(shared_hubs)}+cos_{max_similarity:.3f}"

                if should_add:
                    added_members.append(
                        {
                            "article_id": candidate_id,
                            "title": title,
                            "published_at": published_at,
                            "source_name": source_name,
                            "language": language,
                            "keywords": keywords,
                            "reason": reason,
                        }
                    )

            # Update seed with new members
            all_members = seed_data["members"] + added_members
            densified_seeds[topic_key] = {
                **seed_data,
                "members": all_members,
                "size": len(all_members),
                "added_count": len(added_members),
            }

            if added_members:
                logger.debug(
                    "Added {} members to seed {}".format(len(added_members), topic_key)
                )

        finally:
            cur.close()

    total_added = sum(s.get("added_count", 0) for s in densified_seeds.values())

    # Phase A: Enhanced logging with admission type breakdown
    strict_admits = 0
    hub_pair_admits = 0

    for seed_data in densified_seeds.values():
        for member in seed_data.get("members", []):
            if "reason" in member:
                if member["reason"].startswith("hub_pair_"):
                    hub_pair_admits += 1
                else:
                    strict_admits += 1

    logger.info("=== PHASE A DENSIFY STAGE SUMMARY ===")
    logger.info(f"Total articles added: {total_added}")
    logger.info(f"  Strict admissions: {strict_admits}")
    logger.info(f"  Hub-pair admissions: {hub_pair_admits}")

    if use_hub_assist:
        if hub_pair_admits > 0:
            logger.info(
                f"Hub-assist admissions: {hub_pair_admits} (+{hub_pair_admits/max(1,total_added)*100:.1f}% boost)"
            )
        else:
            logger.info("Hub-assist: No additional admissions found")
    else:
        logger.info("Hub-assist mode: DISABLED")

    logger.info(
        "Densify complete. Added {} articles across {} seeds".format(
            total_added, len(densified_seeds)
        )
    )

    return densified_seeds


def stage_densify_recall(conn, seeds, hours_back=72, lang=None, hub_tokens=None):
    """Recall mode densify with looser similarity thresholds."""
    logger.info("Starting recall mode densify")

    if not seeds:
        return seeds

    densified_seeds = {}

    for topic_key, seed_data in seeds.items():
        logger.debug(f"Densifying recall seed {topic_key} (size: {seed_data['size']})")

        seed_member_ids = [m["article_id"] for m in seed_data["members"]]
        seed_gpe_key = seed_data.get("gpe_key", tuple())
        seed_event_key = seed_data.get("event_key")
        seed_keywords = set(seed_data["keywords"])

        # Find candidate articles for densification
        cur = conn.cursor()
        try:
            lang_filter = "AND a.language = %s" if lang else ""
            query_params = [
                datetime.now() - timedelta(hours=hours_back),
                tuple(seed_member_ids),
            ]
            if lang:
                query_params.append(lang)

            query = f"""
                SELECT 
                    a.id, a.title, a.published_at, a.source_name, a.language,
                    array_agg(ck.token ORDER BY ck.score DESC) as keywords,
                    array_agg(ck.score ORDER BY ck.score DESC) as scores
                FROM articles a
                JOIN article_core_keywords ck ON a.id = ck.article_id
                WHERE a.published_at >= %s
                AND a.id NOT IN %s
                {lang_filter}
                GROUP BY a.id, a.title, a.published_at, a.source_name, a.language
                HAVING COUNT(ck.token) >= 3
            """

            cur.execute(query, query_params)
            candidates = cur.fetchall()

            added_members = []
            event_set = get_event_tokens(conn, 30)

            for (
                candidate_id,
                title,
                published_at,
                source_name,
                language,
                keywords,
                scores,
            ) in candidates:
                candidate_keywords = set(keywords[:5])  # Top 5 keywords
                candidate_countries = get_countries_from_tokens(candidate_keywords)
                candidate_gpe_key, candidate_event_key = pick_keys(
                    candidate_keywords, candidate_countries, event_set
                )

                should_add = False
                reason = ""

                # Recall rule 1: same gpe_key and same event_key
                if (
                    seed_gpe_key
                    and candidate_gpe_key == seed_gpe_key
                    and seed_event_key
                    and candidate_event_key == seed_event_key
                ):
                    should_add = True
                    reason = "same_gpe_event"

                # Recall rule 2: same gpe_key and title cosine >= 0.65 (much lower for recall)
                elif seed_gpe_key and candidate_gpe_key == seed_gpe_key:
                    # Check title cosine similarity
                    max_title_similarity = 0.0
                    for seed_member_id in seed_member_ids[:3]:
                        similarity = get_cosine_similarity(
                            conn, candidate_id, seed_member_id
                        )
                        max_title_similarity = max(max_title_similarity, similarity)
                        if max_title_similarity >= 0.65:
                            break

                    if max_title_similarity >= 0.65:
                        should_add = True
                        reason = f"same_gpe_title_cos_{max_title_similarity:.3f}"

                # Recall rule 3: shares >=1 non-hub token with anchor set and cosine >= 0.60 (very low for recall)
                if not should_add:
                    shared_tokens = seed_keywords.intersection(candidate_keywords)
                    shared_nonhub = len(
                        [
                            tok
                            for tok in shared_tokens
                            if tok not in (hub_tokens or set())
                        ]
                    )

                    if shared_nonhub >= 1:
                        max_similarity = 0.0
                        for seed_member_id in seed_member_ids[:3]:
                            similarity = get_cosine_similarity(
                                conn, candidate_id, seed_member_id
                            )
                            max_similarity = max(max_similarity, similarity)
                            if max_similarity >= 0.60:
                                break

                        if max_similarity >= 0.60:
                            should_add = True
                            reason = f"shared_nonhub_{shared_nonhub}_cos_{max_similarity:.3f}"

                if should_add:
                    added_members.append(
                        {
                            "article_id": candidate_id,
                            "title": title,
                            "published_at": published_at,
                            "source_name": source_name,
                            "language": language,
                            "keywords": keywords,
                            "reason": reason,
                            "gpe_key": candidate_gpe_key,
                            "event_key": candidate_event_key,
                        }
                    )

            # Update seed with new members
            all_members = seed_data["members"] + added_members
            densified_seeds[topic_key] = {
                **seed_data,
                "members": all_members,
                "size": len(all_members),
                "added_count": len(added_members),
            }

            if added_members:
                logger.debug(
                    f"Added {len(added_members)} members to recall seed {topic_key}"
                )

        finally:
            cur.close()

    total_added = sum(s.get("added_count", 0) for s in densified_seeds.values())
    logger.info(
        f"Recall densify complete. Added {total_added} articles across {len(densified_seeds)} seeds"
    )

    return densified_seeds


def compute_cluster_features(conn, seed_data):
    """Compute advanced features for cluster merge comparison."""
    try:
        # Extract basic info
        members = seed_data["members"]

        logger.debug(f"Computing features for {len(members)} members")

        # Compute centroid from article keywords
        centroid = compute_cluster_centroid(conn, members)
        logger.debug(f"Computed centroid with {len(centroid)} keywords")

        # Extract non-hub anchors (top strategic keywords excluding hubs)
        anchors_nonhub = get_cluster_anchors_nonhub(conn, members)
        logger.debug(f"Computed {len(anchors_nonhub)} anchor keywords")

        # Extract countries mentioned
        country_set = get_cluster_countries(conn, members)
        logger.debug(f"Found {len(country_set)} countries")

        # Compute time span (earliest to latest article)
        time_span = compute_cluster_time_span(members)
        logger.debug(f"Computed time span: {time_span}")

        return {
            "centroid": centroid,
            "anchors_nonhub": anchors_nonhub,
            "country_set": country_set,
            "time_span": time_span,
            "size": len(members),
        }
    except Exception as e:
        logger.error(f"Error in compute_cluster_features: {e}")
        logger.error(f"Seed data keys: {list(seed_data.keys())}")
        logger.error(f"Members type: {type(seed_data.get('members', 'missing'))}")
        if "members" in seed_data and seed_data["members"]:
            logger.error(f"First member keys: {list(seed_data['members'][0].keys())}")
        raise


def compute_cluster_centroid(conn, members):
    """Compute centroid vector from article keyword embeddings."""

    if not members:
        return {}  # Empty centroid

    article_ids = [member["article_id"] for member in members]

    cur = conn.cursor()
    try:
        # Get keyword vectors for articles (simplified - use keyword text frequency)
        format_strings = ",".join(["%s"] * len(article_ids))
        cur.execute(
            f"""
            SELECT k.keyword, COUNT(*) as freq, AVG(ak.strategic_score) as avg_score
            FROM article_keywords ak
            JOIN keywords k ON ak.keyword_id = k.id
            WHERE ak.article_id IN ({format_strings})
            GROUP BY k.keyword
            ORDER BY avg_score DESC, freq DESC
            LIMIT 50
        """,
            article_ids,
        )

        keyword_data = cur.fetchall()

        # Create simple centroid from top keywords (bag of words approach)
        centroid = {}
        for keyword, freq, score in keyword_data:
            centroid[keyword] = float(freq) * float(score)

        return centroid

    finally:
        cur.close()


def get_cluster_anchors_nonhub(conn, members, limit=10):
    """Get top strategic keywords excluding hub terms."""
    if not members:
        return set()

    article_ids = [member["article_id"] for member in members]

    cur = conn.cursor()
    try:
        # Get hub tokens to exclude (check if table exists first)
        cur.execute(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'keyword_hubs_30d'
            )
        """
        )
        if cur.fetchone()[0]:
            cur.execute("SELECT tok FROM keyword_hubs_30d")
            hub_tokens = set(row[0] for row in cur.fetchall())
        else:
            hub_tokens = set()

        # Get top non-hub keywords
        format_strings = ",".join(["%s"] * len(article_ids))

        if hub_tokens:
            cur.execute(
                f"""
                SELECT k.keyword, AVG(ak.strategic_score) as avg_score, COUNT(*) as freq
                FROM article_keywords ak
                JOIN keywords k ON ak.keyword_id = k.id
                WHERE ak.article_id IN ({format_strings})
                AND k.keyword NOT IN %s
                GROUP BY k.keyword
                ORDER BY avg_score DESC, freq DESC
                LIMIT %s
            """,
                article_ids + [tuple(hub_tokens), limit],
            )
        else:
            cur.execute(
                f"""
                SELECT k.keyword, AVG(ak.strategic_score) as avg_score, COUNT(*) as freq
                FROM article_keywords ak
                JOIN keywords k ON ak.keyword_id = k.id
                WHERE ak.article_id IN ({format_strings})
                GROUP BY k.keyword
                ORDER BY avg_score DESC, freq DESC
                LIMIT %s
            """,
                article_ids + [limit],
            )

        anchors = set(row[0] for row in cur.fetchall())
        return anchors

    finally:
        cur.close()


def get_cluster_countries(conn, members):
    """Extract country/geopolitical entities mentioned in cluster."""
    if not members:
        return set()

    article_ids = [member["article_id"] for member in members]
    logger.debug(f"Looking for countries in {len(article_ids)} articles")

    cur = conn.cursor()
    try:
        format_strings = ",".join(["%s"] * len(article_ids))
        cur.execute(
            f"""
            SELECT DISTINCT k.keyword
            FROM article_keywords ak
            JOIN keywords k ON ak.keyword_id = k.id
            WHERE ak.article_id IN ({format_strings})
            AND k.keyword_type IN ('entity')
            AND (
                k.keyword ILIKE '%china%' OR k.keyword ILIKE '%usa%' OR k.keyword ILIKE '%russia%' 
                OR k.keyword ILIKE '%ukraine%' OR k.keyword ILIKE '%israel%' OR k.keyword ILIKE '%iran%'
                OR k.keyword ILIKE '%india%' OR k.keyword ILIKE '%japan%' OR k.keyword ILIKE '%germany%'
                OR k.keyword ILIKE '%france%' OR k.keyword ILIKE '%britain%' OR k.keyword ILIKE '%turkey%'
            )
        """,
            article_ids,
        )

        results = cur.fetchall()
        logger.debug(f"Found {len(results)} country keywords")

        countries = set()
        for row in results:
            if row and len(row) > 0 and row[0]:  # Defensive check for None values
                try:
                    countries.add(row[0].lower())
                except (AttributeError, IndexError):
                    continue  # Skip invalid entries

        return countries

    except Exception as e:
        logger.error(f"Error in get_cluster_countries: {e}")
        return set()
    finally:
        cur.close()


def compute_cluster_time_span(members):
    """Compute time span of cluster articles."""
    if not members:
        return {"start": None, "end": None, "hours": 0}

    timestamps = []
    for member in members:
        # Members might have different field names for timestamp
        timestamp = None
        for field in ["published_at", "created_at", "timestamp"]:
            if field in member:
                timestamp = member[field]
                break

        if timestamp:
            timestamps.append(timestamp)

    if not timestamps:
        return {"start": None, "end": None, "hours": 0}

    try:
        start_time = min(timestamps)
        end_time = max(timestamps)
        hours_span = (end_time - start_time).total_seconds() / 3600

        return {"start": start_time, "end": end_time, "hours": hours_span}
    except Exception as e:
        logger.error(f"Error computing time span: {e}")
        return {"start": None, "end": None, "hours": 0}


def compute_cosine_similarity(features1, features2):
    """Compute cosine similarity between cluster centroids."""

    centroid1 = features1["centroid"]
    centroid2 = features2["centroid"]

    if not centroid1 or not centroid2:
        return 0.0

    # Convert to common keyword space
    all_keywords = set(centroid1.keys()) | set(centroid2.keys())

    if not all_keywords:
        return 0.0

    vec1 = np.array([centroid1.get(kw, 0) for kw in all_keywords])
    vec2 = np.array([centroid2.get(kw, 0) for kw in all_keywords])

    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return np.dot(vec1, vec2) / (norm1 * norm2)


def compute_weighted_jaccard(features1, features2):
    """Compute weighted Jaccard similarity between anchor keywords."""
    anchors1 = features1["anchors_nonhub"]
    anchors2 = features2["anchors_nonhub"]

    if not anchors1 or not anchors2:
        return 0.0

    intersection = len(anchors1 & anchors2)
    union = len(anchors1 | anchors2)

    if union == 0:
        return 0.0

    # Weight by cluster sizes
    size1 = features1["size"]
    size2 = features2["size"]
    weight = min(size1, size2) / max(size1, size2)

    return (intersection / union) * weight


def compute_time_overlap(features1, features2):
    """Compute time overlap between cluster time spans."""
    span1 = features1["time_span"]
    span2 = features2["time_span"]

    if not span1["start"] or not span1["end"] or not span2["start"] or not span2["end"]:
        return 0.0

    # Find overlap period
    overlap_start = max(span1["start"], span2["start"])
    overlap_end = min(span1["end"], span2["end"])

    if overlap_start >= overlap_end:
        return 0.0  # No overlap

    overlap_hours = (overlap_end - overlap_start).total_seconds() / 3600

    # Normalize by smaller span
    min_span_hours = min(span1["hours"], span2["hours"])

    if min_span_hours == 0:
        return 1.0 if overlap_hours > 0 else 0.0

    return min(overlap_hours / min_span_hours, 1.0)


def stage_consolidate(conn, seeds, merge_cos=0.90, merge_wj=0.55, merge_time=0.50):
    """Stage 2.5: Consolidate overlapping clusters using cosine similarity, weighted Jaccard, and time overlap."""
    logger.info(
        f"Starting consolidate stage with merge thresholds: cos={merge_cos}, wj={merge_wj}, time={merge_time}"
    )

    if not seeds or len(seeds) < 2:
        logger.info("Insufficient clusters for consolidation")
        return seeds

    # Compute cluster features for merge comparison
    cluster_features = {}
    for topic_key, seed_data in seeds.items():
        try:
            cluster_features[topic_key] = compute_cluster_features(conn, seed_data)
            logger.debug(f"Computed features for cluster {topic_key[:8]}...")
        except Exception as e:
            logger.error(f"Failed to compute features for cluster {topic_key}: {e}")
            raise

    # Find merge candidates using advanced similarity metrics
    merge_pairs = []
    cluster_keys = list(seeds.keys())

    for i, key1 in enumerate(cluster_keys):
        for key2 in cluster_keys[i + 1 :]:
            # Calculate similarities
            cos_sim = compute_cosine_similarity(
                cluster_features[key1], cluster_features[key2]
            )
            wj_sim = compute_weighted_jaccard(
                cluster_features[key1], cluster_features[key2]
            )
            time_overlap = compute_time_overlap(
                cluster_features[key1], cluster_features[key2]
            )

            # Apply merge rule: accept if >=2 hold
            conditions = [
                cos_sim >= merge_cos,
                wj_sim >= merge_wj,
                time_overlap >= merge_time,
            ]

            if sum(conditions) >= 2:
                merge_pairs.append(
                    (
                        key1,
                        key2,
                        {
                            "cos_sim": cos_sim,
                            "wj_sim": wj_sim,
                            "time_overlap": time_overlap,
                            "conditions_met": sum(conditions),
                        },
                    )
                )

    logger.info(
        f"Found {len(merge_pairs)} cluster pairs meeting merge criteria (>=2 conditions)"
    )

    # Apply union-find to get connected components
    consolidated_seeds = apply_advanced_union_find(conn, seeds, merge_pairs)

    logger.info(
        f"Consolidated {len(seeds)} clusters into {len(consolidated_seeds)} components"
    )
    return consolidated_seeds


def apply_advanced_union_find(conn, seeds, merge_pairs):
    """Apply union-find algorithm to merge connected cluster components with advanced similarity."""

    # Union-Find data structure
    parent = {}
    rank = {}

    def find(x):
        if x not in parent:
            parent[x] = x
            rank[x] = 0
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x, y):
        px, py = find(x), find(y)
        if px == py:
            return
        if rank[px] < rank[py]:
            px, py = py, px
        parent[py] = px
        if rank[px] == rank[py]:
            rank[px] += 1

    # Initialize all clusters
    for topic_key in seeds.keys():
        find(topic_key)

    # Union clusters based on merge pairs
    for key1, key2, similarity_metrics in merge_pairs:
        union(key1, key2)
        logger.info(
            f"Unioning clusters {key1[:8]}...{key2[:8]} - cos={similarity_metrics['cos_sim']:.3f}, wj={similarity_metrics['wj_sim']:.3f}, time={similarity_metrics['time_overlap']:.3f}"
        )

    # Group clusters by component
    components = {}
    for topic_key in seeds.keys():
        root = find(topic_key)
        if root not in components:
            components[root] = []
        components[root].append(topic_key)

    # Merge clusters within each component
    consolidated = {}
    for root, cluster_keys in components.items():
        if len(cluster_keys) == 1:
            # Single cluster - generate label and keep as is
            single_key = cluster_keys[0]
            single_data = seeds[single_key]
            try:
                label = generate_tfidf_label(
                    conn, single_data["members"], single_data.get("keywords", [])
                )
                single_data["label"] = label
            except Exception as e:
                logger.error(f"Error generating label for single cluster: {e}")
                single_data["label"] = f"cluster_{single_key[:8]}"
            consolidated[single_key] = single_data
        else:
            # Multiple clusters - merge them
            merged_key = f"consolidated_{root[:8]}"
            merged_members = []
            merged_keywords = set()
            merged_sources = set()

            # Collect all unique articles from component clusters
            seen_articles = set()
            for key in cluster_keys:
                for member in seeds[key]["members"]:
                    article_id = member["article_id"]
                    if article_id not in seen_articles:
                        merged_members.append(member)
                        seen_articles.add(article_id)
                        if "source_name" in member:
                            merged_sources.add(member["source_name"])

                # Combine keywords
                if "keywords" in seeds[key]:
                    merged_keywords.update(seeds[key]["keywords"])

            # Generate TF-IDF label for merged cluster
            try:
                label = generate_tfidf_label(
                    conn, merged_members, list(merged_keywords)
                )
            except Exception as e:
                logger.error(f"Error generating label for merged cluster: {e}")
                label = f"consolidated_{merged_key[-8:]}"

            consolidated[merged_key] = {
                "members": merged_members,
                "size": len(merged_members),
                "sources": list(merged_sources),
                "keywords": list(merged_keywords),
                "label": label,
                "lang": seeds[cluster_keys[0]].get("lang", "EN"),
                "merged_from": cluster_keys,
            }

            logger.info(
                f"Consolidated {len(cluster_keys)} clusters into {merged_key} with {len(merged_members)} articles"
            )

    return consolidated


def generate_tfidf_label(conn, members, cluster_keywords):
    """Generate TF-IDF based label: top (geo OR org) + top event + optional person (max 3)."""
    if not members:
        return "unlabeled"

    # Get article IDs
    article_ids = [member["article_id"] for member in members]

    cur = conn.cursor()
    try:
        # Load hub tokens to exclude
        cur.execute("SELECT tok FROM keyword_hubs_30d")
        hub_tokens = set(row[0] for row in cur.fetchall())

        # Get all keywords for these articles with their types
        format_strings = ",".join(["%s"] * len(article_ids))
        cur.execute(
            f"""
            SELECT k.keyword, k.keyword_type, ak.strategic_score
            FROM article_keywords ak
            JOIN keywords k ON ak.keyword_id = k.id
            WHERE ak.article_id IN ({format_strings})
            AND k.keyword NOT IN %s
            ORDER BY ak.strategic_score DESC
        """,
            article_ids + [tuple(hub_tokens)],
        )

        keyword_data = cur.fetchall()

        # Classify tokens by type
        geo_org_tokens = []
        event_tokens = []
        person_tokens = []

        for keyword, kw_type, score in keyword_data:
            keyword_lower = keyword.lower()

            # Classify based on keyword type and content
            if kw_type == "entity":
                # Check if it's a location or organization
                if any(
                    geo_indicator in keyword_lower
                    for geo_indicator in [
                        "africa",
                        "america",
                        "asia",
                        "europe",
                        "country",
                        "city",
                        "state",
                    ]
                ):
                    geo_org_tokens.append((keyword, score))
                elif any(
                    org_indicator in keyword_lower
                    for org_indicator in [
                        "government",
                        "ministry",
                        "department",
                        "agency",
                        "union",
                        "organization",
                    ]
                ):
                    geo_org_tokens.append((keyword, score))
                elif any(
                    person_indicator in keyword_lower
                    for person_indicator in [
                        "president",
                        "minister",
                        "secretary",
                        "director",
                        "chairman",
                    ]
                ):
                    person_tokens.append((keyword, score))
                else:
                    # Default entity classification
                    if len(keyword.split()) == 1 and keyword.istitle():
                        person_tokens.append((keyword, score))
                    else:
                        geo_org_tokens.append((keyword, score))
            elif kw_type == "phrase":
                # Phrases are likely events
                if any(
                    event_indicator in keyword_lower
                    for event_indicator in [
                        "crash",
                        "accident",
                        "attack",
                        "summit",
                        "meeting",
                        "conference",
                        "crisis",
                    ]
                ):
                    event_tokens.append((keyword, score))
                else:
                    geo_org_tokens.append((keyword, score))  # Default to geo/org

        # Build label: top (geo OR org) + top event + optional person (max 3)
        label_parts = []

        # Top geo/org token
        if geo_org_tokens:
            top_geo_org = max(geo_org_tokens, key=lambda x: x[1])
            label_parts.append(top_geo_org[0])

        # Top event token
        if event_tokens:
            top_event = max(event_tokens, key=lambda x: x[1])
            label_parts.append(top_event[0])

        # Optional top person (if space allows)
        if person_tokens and len(label_parts) < 3:
            top_person = max(person_tokens, key=lambda x: x[1])
            label_parts.append(top_person[0])

        # Fallback to top cluster keywords if no good classification
        if not label_parts and cluster_keywords:
            # Use top 2-3 cluster keywords
            non_hub_keywords = [kw for kw in cluster_keywords if kw not in hub_tokens]
            label_parts = non_hub_keywords[:3]

        if label_parts:
            return " • ".join(label_parts)
        else:
            return "mixed topics"

    except Exception as e:
        logger.error(f"Error generating TF-IDF label: {e}")
        return "label error"
    finally:
        cur.close()


def stage_refine(conn, seeds, min_size=80):
    """Stage 3: Split giant clusters with size > 80 and entropy > 2.4."""
    logger.info(
        "Starting refine stage with giant cluster splitting (min_size: {})".format(
            min_size
        )
    )

    # Load hub tokens for discriminator selection
    cur = conn.cursor()
    try:
        cur.execute("SELECT tok FROM keyword_hubs_30d")
        hub_tokens = set(row[0] for row in cur.fetchall())

        cur.execute("SELECT tok, spec FROM keyword_specificity_30d")
        token_specificity = dict(cur.fetchall())

        logger.info(
            f"Loaded {len(hub_tokens)} hub tokens and {len(token_specificity)} specificity scores for refine stage"
        )
    finally:
        cur.close()

    refined_seeds = {}
    split_count = 0

    for topic_key, seed_data in seeds.items():
        members = seed_data["members"]
        cluster_size = len(members)

        # Check if cluster qualifies for splitting
        if cluster_size > 80:
            # Calculate entropy
            source_counts = {}
            for member in members:
                source = member["source_name"]
                source_counts[source] = source_counts.get(source, 0) + 1

            total_articles = len(members)
            entropy = 0.0
            for count in source_counts.values():
                p = count / total_articles
                if p > 0:
                    entropy -= p * (p**0.5)  # Simplified entropy calculation

            if entropy > 2.4:
                logger.info(
                    f"Splitting giant cluster {topic_key} (size: {cluster_size}, entropy: {entropy:.2f})"
                )

                # Find top 3 non-hub discriminators
                keyword_frequencies = {}
                for member in members:
                    if "keywords" in member:
                        for keyword in member["keywords"]:
                            if keyword not in hub_tokens:  # Non-hub only
                                keyword_frequencies[keyword] = (
                                    keyword_frequencies.get(keyword, 0) + 1
                                )

                # Score discriminators: specificity × frequency
                discriminator_scores = {}
                for keyword, freq in keyword_frequencies.items():
                    spec = token_specificity.get(keyword, 0.0)
                    discriminator_scores[keyword] = spec * freq

                # Get top 3 discriminators
                top_discriminators = sorted(
                    discriminator_scores.items(), key=lambda x: x[1], reverse=True
                )[:3]

                if top_discriminators:
                    best_discriminator = top_discriminators[0][0]
                    logger.debug(
                        f"Using discriminator '{best_discriminator}' to split cluster {topic_key}"
                    )

                    # Partition articles by best discriminator
                    with_discriminator = []
                    without_discriminator = []

                    for member in members:
                        has_discriminator = False
                        if "keywords" in member:
                            has_discriminator = best_discriminator in member["keywords"]

                        if has_discriminator:
                            with_discriminator.append(member)
                        else:
                            without_discriminator.append(member)

                    # Only split if both children have size >= 8
                    if len(with_discriminator) >= 8 and len(without_discriminator) >= 8:
                        # Create child clusters
                        child1_key = f"{topic_key}_split1"
                        child2_key = f"{topic_key}_split2"

                        refined_seeds[child1_key] = {
                            **seed_data,
                            "members": with_discriminator,
                            "size": len(with_discriminator),
                            "split_from": topic_key,
                            "discriminator": best_discriminator,
                        }

                        refined_seeds[child2_key] = {
                            **seed_data,
                            "members": without_discriminator,
                            "size": len(without_discriminator),
                            "split_from": topic_key,
                            "discriminator": f"not_{best_discriminator}",
                        }

                        split_count += 1
                        logger.info(
                            f"Split cluster {topic_key} into {child1_key} ({len(with_discriminator)}) and {child2_key} ({len(without_discriminator)})"
                        )
                        continue

                # If splitting failed, keep original cluster
                logger.debug(f"Failed to split cluster {topic_key}, keeping original")

        # Keep cluster as-is (not giant or splitting failed)
        refined_seeds[topic_key] = seed_data

    if split_count > 0:
        logger.info(f"Giant cluster splitting complete: split {split_count} clusters")

    return refined_seeds


def compute_cluster_cohesion(members):
    """Compute cluster cohesion score based on multiple factors."""
    if not members:
        return 0.0

    # Factor 1: Source diversity (0-1)
    unique_sources = set(m["source_name"] for m in members)
    source_diversity = min(len(unique_sources) / 5.0, 1.0)  # Normalize to max 5 sources

    # Factor 2: Topic overlap (simplified - assume high since they're in same cluster)
    topic_overlap = 0.8  # Static for MVP since members share topics

    # Factor 3: Time span penalty
    timestamps = [m["published_at"] for m in members]
    if len(timestamps) > 1:
        time_span = (max(timestamps) - min(timestamps)).total_seconds() / 3600  # Hours
        time_penalty = -0.1 if time_span > 72 else 0.0
    else:
        time_penalty = 0.0

    # Weighted combination
    cohesion = (
        0.45 * 0.8  # avg_cos (simplified)
        + 0.35 * topic_overlap
        + 0.20 * source_diversity
        + time_penalty
    )

    return max(0.0, min(1.0, cohesion))


def stage_persist(conn, seeds, macro_enable=1):
    """Stage 4: Persist clusters to database."""
    logger.info(f"Starting persist stage (macro_enable: {macro_enable})")

    if not seeds:
        logger.warning("No seeds to persist")
        return

    cur = conn.cursor()

    try:
        # Clear existing clusters (for clean run)
        cur.execute("DELETE FROM article_cluster_members")
        cur.execute("DELETE FROM article_clusters")

        cluster_rows = []
        member_rows = []

        for topic_key, seed_data in seeds.items():
            members = seed_data["members"]
            if not members:
                continue

            # Compute time window
            timestamps = [m["published_at"] for m in members]
            time_start = min(timestamps)
            time_end = max(timestamps)
            time_window = f"[{time_start},{time_end}]"

            # Compute cohesion
            cohesion = compute_cluster_cohesion(members)

            # Phase A: Enhanced macro classification rule using event signals
            cluster_type = "final"  # Default
            if macro_enable:
                # Load event signals for classification
                cur_temp = conn.cursor()
                try:
                    cur_temp.execute("SELECT signal FROM event_signals_30d")
                    event_signals = {row[0] for row in cur_temp.fetchall()}
                finally:
                    cur_temp.close()

                # Check if any member has an event signal
                has_event_signal_member = False
                for member in members:
                    member_keywords = member.get("keywords", [])
                    member_title = member.get("title", "")

                    if has_event_signal(member_keywords, member_title, event_signals):
                        has_event_signal_member = True
                        break

                # New rule: mark as macro if NO member has an event signal
                if not has_event_signal_member:
                    cluster_type = "macro"

            # Create cluster record
            cluster_rows.append(
                (
                    topic_key,
                    seed_data["keywords"],
                    None,  # label (to be filled by labeler)
                    seed_data.get("lang"),
                    time_window,
                    len(members),
                    cohesion,
                    cluster_type,
                )
            )

            # Create member records
            for member in members:
                member_rows.append(
                    (
                        topic_key,  # Will be replaced with actual cluster_id after insert
                        member["article_id"],
                        1.0,  # weight (simplified)
                    )
                )

        # Insert clusters
        insert_cluster_sql = """
            INSERT INTO article_clusters (topic_key, top_topics, label, lang, time_window, size, cohesion, cluster_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        execute_batch(cur, insert_cluster_sql, cluster_rows)

        # Get cluster IDs for members
        cur.execute(
            """
            SELECT cluster_id, topic_key 
            FROM article_clusters 
            WHERE topic_key = ANY(%s)
        """,
            ([topic_key for topic_key, _ in seeds.items()],),
        )

        topic_key_to_cluster_id = {row[1]: row[0] for row in cur.fetchall()}

        # Update member rows with actual cluster IDs
        updated_member_rows = []
        for topic_key, article_id, weight in member_rows:
            cluster_id = topic_key_to_cluster_id.get(topic_key)
            if cluster_id:
                updated_member_rows.append((cluster_id, article_id, weight))

        # Insert members
        insert_member_sql = """
            INSERT INTO article_cluster_members (cluster_id, article_id, weight)
            VALUES (%s, %s, %s)
        """
        execute_batch(cur, insert_member_sql, updated_member_rows)

        # Phase A: Enhanced logging with cluster type breakdown
        final_clusters = sum(1 for row in cluster_rows if row[7] == "final")
        macro_clusters = sum(1 for row in cluster_rows if row[7] == "macro")

        logger.info("=== PHASE A PERSIST STAGE SUMMARY ===")
        logger.info(f"Total clusters persisted: {len(cluster_rows)}")
        logger.info(f"  Final clusters: {final_clusters}")
        logger.info(f"  Macro clusters: {macro_clusters}")

        if macro_enable:
            if macro_clusters > 0:
                macro_pct = (macro_clusters / len(cluster_rows)) * 100
                logger.info(
                    f"Macro classification: {macro_clusters} clusters ({macro_pct:.1f}%)"
                )
                if macro_pct > 20:
                    logger.warning(
                        f"High macro percentage: {macro_pct:.1f}% > 20% target"
                    )
            else:
                logger.info("Macro classification: All clusters are final type")
        else:
            logger.info("Macro classification: DISABLED")

        logger.info(
            "Persisted {} clusters with {} total members".format(
                len(cluster_rows), len(updated_member_rows)
            )
        )

    except Exception as e:
        logger.error("Failed to persist clusters: {}".format(e))
        raise
    finally:
        cur.close()


def main():
    """Main clustering function with stage selection."""
    parser = argparse.ArgumentParser(description="CLUST-1 taxonomy-aware clustering")
    parser.add_argument(
        "--stage",
        choices=["seed", "densify", "consolidate", "refine", "persist"],
        required=True,
        help="Clustering stage to run",
    )
    parser.add_argument(
        "--window", type=int, default=72, help="Time window in hours (default: 72)"
    )
    parser.add_argument(
        "--lang", type=str, default="EN", help="Language filter (default: EN for MVP)"
    )
    parser.add_argument(
        "--cos",
        type=float,
        default=0.88,
        help="Cosine similarity threshold (default: 0.88)",
    )
    parser.add_argument(
        "--min-size",
        type=int,
        default=80,
        help="Minimum size for refine stage (default: 80)",
    )
    parser.add_argument(
        "--merge-cos",
        type=float,
        default=0.90,
        help="Cosine similarity threshold for consolidate merge (default: 0.90)",
    )
    parser.add_argument(
        "--merge-wj",
        type=float,
        default=0.55,
        help="Weighted Jaccard threshold for consolidate merge (default: 0.55)",
    )
    parser.add_argument(
        "--merge-time",
        type=float,
        default=0.50,
        help="Time overlap threshold for consolidate merge (default: 0.50)",
    )
    parser.add_argument(
        "--profile",
        choices=["strict", "recall"],
        default="strict",
        help="Clustering profile: strict (default) for precision, recall for coverage",
    )
    parser.add_argument(
        "--use_triads",
        type=int,
        default=0,
        help="Enable triad-based seed enhancement (0=off, 1=on, default: 0)",
    )

    # Phase A: Hub-assisted rules and macro clustering flags
    parser.add_argument(
        "--use_hub_assist",
        type=int,
        default=0,
        help="Enable hub-assisted clustering rules (0=off, 1=on, default: 0)",
    )
    parser.add_argument(
        "--macro_enable",
        type=int,
        default=1,
        help="Enable macro cluster classification (0=off, 1=on, default: 1)",
    )
    parser.add_argument(
        "--hub_pair_cos",
        type=float,
        default=0.90,
        help="Cosine threshold for hub-pair admission (default: 0.90)",
    )
    parser.add_argument(
        "--hub_plus_one_cos",
        type=float,
        default=0.85,
        help="Cosine threshold for hub+1 admission (default: 0.85)",
    )
    parser.add_argument(
        "--hub_only_cap",
        type=float,
        default=0.25,
        help="Max proportion of hub-only admissions per cluster (default: 0.25)",
    )
    parser.add_argument(
        "--triad_codoc_min",
        type=int,
        default=3,
        help="Minimum co-occurrence for triad patterns (default: 3)",
    )
    parser.add_argument(
        "--triad_pmi_min",
        type=float,
        default=2.5,
        help="Minimum PMI score for triad patterns (default: 2.5)",
    )
    parser.add_argument(
        "--use_clean_events",
        type=int,
        default=0,
        help="Use clean filtered event tokens for A/B testing (0=original, 1=clean, default: 0)",
    )

    args = parser.parse_args()

    logger.info(
        "Starting CLUST-1 stage: {} (language: {}, MVP English-only)".format(
            args.stage, args.lang
        )
    )

    try:
        conn = get_db_connection()

        try:
            if args.stage == "seed":
                seeds = stage_seed(
                    conn,
                    args.window,
                    args.lang,
                    args.profile,
                    args.use_triads,
                    args.use_hub_assist,
                    use_clean_events=args.use_clean_events,
                )
                logger.info("Seed stage completed with {} seeds".format(len(seeds)))
                # Store seeds in a simple way for MVP (could use Redis/file for production)

            elif args.stage == "densify":
                # For MVP, re-run seed stage then densify
                seeds = stage_seed(
                    conn,
                    args.window,
                    args.lang,
                    args.profile,
                    args.use_triads,
                    args.use_hub_assist,
                    use_clean_events=args.use_clean_events,
                )
                if seeds:
                    seeds = stage_densify(
                        conn,
                        seeds,
                        args.window,
                        args.lang,
                        args.cos,
                        args.profile,
                        args.use_hub_assist,
                        args.hub_pair_cos,
                    )
                logger.info("Densify stage completed")

            elif args.stage == "consolidate":
                seeds = stage_seed(
                    conn,
                    args.window,
                    args.lang,
                    args.profile,
                    args.use_triads,
                    args.use_hub_assist,
                    use_clean_events=args.use_clean_events,
                )
                if seeds:
                    seeds = stage_densify(
                        conn,
                        seeds,
                        args.window,
                        args.lang,
                        args.cos,
                        args.profile,
                        args.use_hub_assist,
                        args.hub_pair_cos,
                    )
                    seeds = stage_consolidate(
                        conn, seeds, args.merge_cos, args.merge_wj, args.merge_time
                    )
                logger.info("Consolidate stage completed")

            elif args.stage == "refine":
                seeds = stage_seed(
                    conn,
                    args.window,
                    args.lang,
                    args.profile,
                    args.use_triads,
                    args.use_hub_assist,
                    use_clean_events=args.use_clean_events,
                )
                if seeds:
                    seeds = stage_densify(
                        conn,
                        seeds,
                        args.window,
                        args.lang,
                        args.cos,
                        args.profile,
                        args.use_hub_assist,
                        args.hub_pair_cos,
                    )
                    seeds = stage_consolidate(conn, seeds)
                    seeds = stage_refine(conn, seeds, args.min_size)
                logger.info("Refine stage completed")

            elif args.stage == "persist":
                seeds = stage_seed(
                    conn,
                    args.window,
                    args.lang,
                    args.profile,
                    args.use_triads,
                    args.use_hub_assist,
                    use_clean_events=args.use_clean_events,
                )
                if seeds:
                    seeds = stage_densify(
                        conn,
                        seeds,
                        args.window,
                        args.lang,
                        args.cos,
                        args.profile,
                        args.use_hub_assist,
                        args.hub_pair_cos,
                    )
                    seeds = stage_consolidate(conn, seeds)
                    seeds = stage_refine(conn, seeds, args.min_size)
                    stage_persist(conn, seeds, args.macro_enable)
                conn.commit()
                logger.info("Persist stage completed")

        except Exception as e:
            conn.rollback()
            logger.error("CLUST-1 stage {} failed: {}".format(args.stage, e))
            raise
        finally:
            conn.close()

    except Exception as e:
        logger.error("Failed to run CLUST-1: {}".format(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
