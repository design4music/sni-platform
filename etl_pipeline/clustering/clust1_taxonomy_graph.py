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

import psycopg2
from psycopg2.extras import execute_batch

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_db_connection():
    """Get database connection using environment variables."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "narrative_intelligence"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )


def generate_topic_key(topic_combo):
    """Generate deterministic hash key for topic combination."""
    sorted_combo = "::".join(sorted(topic_combo))
    return hashlib.sha1(sorted_combo.encode()).hexdigest()


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


def stage_seed(conn, hours_back=72, lang=None):
    """Stage 1: Create seed clusters based on core keyword combinations."""
    logger.info(
        "Starting seed stage (window: {}h, lang: {}) - USING CORE KEYWORDS".format(
            hours_back, lang
        )
    )

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
            SELECT tok_a, tok_b, co_doc FROM pairs30
            WHERE co_doc >= 5
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

    # Filter seeds: size >= 3 and >= 2 unique sources
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

    logger.info("Created {} seed clusters".format(len(seeds)))

    # Store seeds temporarily (in-memory for this MVP)
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


def stage_densify(conn, seeds, hours_back=72, lang=None, cos_threshold=0.82):
    """Stage 2: Densify clusters by adding similar articles with hub-suppression."""
    logger.info("Starting densify stage (cos_threshold: {})".format(cos_threshold))

    if not seeds:
        logger.warning("No seeds to densify")
        return seeds

    # Load hub tokens for densify logic
    cur = conn.cursor()
    try:
        cur.execute("SELECT tok FROM keyword_hubs_30d")
        hub_tokens = set(row[0] for row in cur.fetchall())
        logger.info(f"Loaded {len(hub_tokens)} hub tokens for densify stage")
    finally:
        cur.close()

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

                        if max_similarity >= 0.88:  # Gentler threshold for recall
                            break

                    if max_similarity >= 0.88:
                        should_add = True
                        reason = f"shared_nonhub_1+cos_{max_similarity:.3f}"

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
    logger.info(
        "Densify complete. Added {} articles across {} seeds".format(
            total_added, len(densified_seeds)
        )
    )

    return densified_seeds


def stage_consolidate(conn, seeds):
    """Stage 2.5: Consolidate overlapping clusters using connected components."""
    logger.info("Starting consolidate stage with connected components")

    if not seeds or len(seeds) < 2:
        logger.info("Insufficient clusters for consolidation")
        return seeds

    # First persist temp clusters to compute overlaps
    temp_cluster_data = []
    temp_member_data = []
    cluster_id_map = {}

    for i, (topic_key, seed_data) in enumerate(seeds.items()):
        temp_cluster_id = f"temp_{i}"
        cluster_id_map[topic_key] = temp_cluster_id

        temp_cluster_data.append(
            (temp_cluster_id, seed_data["keywords"], seed_data["size"])
        )

        for member in seed_data["members"]:
            temp_member_data.append((temp_cluster_id, member["article_id"]))

    cur = conn.cursor()
    try:
        # Create temp tables
        cur.execute("DROP TABLE IF EXISTS temp_clusters")
        cur.execute("DROP TABLE IF EXISTS temp_cluster_members")

        cur.execute(
            """
            CREATE TEMP TABLE temp_clusters (
                cluster_id VARCHAR PRIMARY KEY,
                keywords TEXT[],
                size INTEGER
            )
        """
        )

        cur.execute(
            """
            CREATE TEMP TABLE temp_cluster_members (
                cluster_id VARCHAR,
                article_id VARCHAR
            )
        """
        )

        # Insert temp data
        from psycopg2.extras import execute_batch

        execute_batch(
            cur, "INSERT INTO temp_clusters VALUES (%s, %s, %s)", temp_cluster_data
        )
        execute_batch(
            cur, "INSERT INTO temp_cluster_members VALUES (%s, %s)", temp_member_data
        )

        # Compute overlaps using the provided SQL
        overlap_query = """
            CREATE TEMP TABLE cl_overlap AS
            SELECT a.cluster_id AS c1, b.cluster_id AS c2,
                   COUNT(*)::int AS inter,
                   ca.size AS size1, cb.size AS size2
            FROM temp_cluster_members a
            JOIN temp_cluster_members b
              ON a.article_id=b.article_id AND a.cluster_id < b.cluster_id
            JOIN temp_clusters ca ON ca.cluster_id=a.cluster_id
            JOIN temp_clusters cb ON cb.cluster_id=b.cluster_id
            GROUP BY a.cluster_id, b.cluster_id, ca.size, cb.size
        """
        cur.execute(overlap_query)

        # Get pairs to merge
        merge_query = """
            SELECT c1, c2
            FROM (
              SELECT c1, c2,
                     inter::float / (size1 + size2 - inter) AS jaccard,
                     (inter = size1) AS a_subset_b,
                     (inter = size2) AS b_subset_a
              FROM cl_overlap
            ) x
            WHERE jaccard >= 0.60 OR a_subset_b OR b_subset_a
        """
        cur.execute(merge_query)
        merge_pairs = cur.fetchall()

        logger.info(f"Found {len(merge_pairs)} cluster pairs to merge")

        # Apply union-find to get connected components
        consolidated_seeds = apply_union_find(conn, seeds, merge_pairs, cluster_id_map)

        logger.info(
            f"Consolidated {len(seeds)} clusters into {len(consolidated_seeds)} components"
        )
        return consolidated_seeds

    finally:
        cur.close()


def apply_union_find(conn, seeds, merge_pairs, cluster_id_map):
    """Apply union-find algorithm to merge connected cluster components."""
    # Reverse mapping from temp_id to topic_key
    id_to_key = {v: k for k, v in cluster_id_map.items()}

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

    # Union overlapping clusters
    for temp_c1, temp_c2 in merge_pairs:
        if temp_c1 in id_to_key and temp_c2 in id_to_key:
            key1, key2 = id_to_key[temp_c1], id_to_key[temp_c2]
            union(key1, key2)

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
            merged_key = f"merged_{root}"
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
                        merged_sources.add(member["source_name"])

                # Combine keywords
                if "keywords" in seeds[key]:
                    merged_keywords.update(seeds[key]["keywords"])

            # Generate TF-IDF label for merged cluster
            try:
                label = generate_tfidf_label(conn, merged_members, merged_keywords)
            except Exception as e:
                logger.error(f"Error generating label for merged cluster: {e}")
                label = f"merged_{merged_key[:8]}"

            consolidated[merged_key] = {
                "members": merged_members,
                "size": len(merged_members),
                "sources": merged_sources,
                "keywords": list(merged_keywords),
                "label": label,
                "lang": seeds[cluster_keys[0]].get("lang"),
                "merged_from": cluster_keys,
            }

            logger.info(
                f"Merged clusters {cluster_keys} into {merged_key} with {len(merged_members)} articles"
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


def stage_persist(conn, seeds):
    """Stage 4: Persist clusters to database."""
    logger.info("Starting persist stage")

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
            INSERT INTO article_clusters (topic_key, top_topics, label, lang, time_window, size, cohesion)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
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
        "--lang", type=str, default="en", help="Language filter (default: en for MVP)"
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
                seeds = stage_seed(conn, args.window, args.lang)
                logger.info("Seed stage completed with {} seeds".format(len(seeds)))
                # Store seeds in a simple way for MVP (could use Redis/file for production)

            elif args.stage == "densify":
                # For MVP, re-run seed stage then densify
                seeds = stage_seed(conn, args.window, args.lang)
                if seeds:
                    seeds = stage_densify(conn, seeds, args.window, args.lang, args.cos)
                logger.info("Densify stage completed")

            elif args.stage == "consolidate":
                seeds = stage_seed(conn, args.window, args.lang)
                if seeds:
                    seeds = stage_densify(conn, seeds, args.window, args.lang, args.cos)
                    seeds = stage_consolidate(conn, seeds)
                logger.info("Consolidate stage completed")

            elif args.stage == "refine":
                seeds = stage_seed(conn, args.window, args.lang)
                if seeds:
                    seeds = stage_densify(conn, seeds, args.window, args.lang, args.cos)
                    seeds = stage_consolidate(conn, seeds)
                    seeds = stage_refine(conn, seeds, args.min_size)
                logger.info("Refine stage completed")

            elif args.stage == "persist":
                seeds = stage_seed(conn, args.window, args.lang)
                if seeds:
                    seeds = stage_densify(conn, seeds, args.window, args.lang, args.cos)
                    seeds = stage_consolidate(conn, seeds)
                    seeds = stage_refine(conn, seeds, args.min_size)
                    stage_persist(conn, seeds)
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
