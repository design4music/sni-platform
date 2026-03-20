"""
Dynamic signal normalization with persistent aliases.

1. Load existing aliases from signal_aliases table
2. Apply them to current batch
3. Run cosine similarity on remaining unmatched unique values
4. Discover new aliases, save to DB
5. Apply new aliases

Works for: places, persons, orgs, named_events.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def load_aliases(conn, signal_type):
    """Load existing aliases from DB."""
    cur = conn.cursor()
    cur.execute(
        "SELECT original, canonical FROM signal_aliases WHERE signal_type = %s",
        (signal_type,),
    )
    return {r[0]: r[1] for r in cur.fetchall()}


def save_aliases(conn, signal_type, new_aliases):
    """Save new aliases to DB."""
    if not new_aliases:
        return
    cur = conn.cursor()
    for original, canonical in new_aliases.items():
        cur.execute(
            "INSERT INTO signal_aliases (signal_type, original, canonical) "
            "VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
            (signal_type, original, canonical),
        )
    conn.commit()


def discover_aliases(values, threshold=0.6):
    """Find similar value pairs via character n-gram cosine similarity.

    Returns: {original: canonical} where canonical is the shorter form.
    """
    if len(values) < 2:
        return {}

    unique = sorted(values)
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), lowercase=True)
    tfidf = vec.fit_transform(unique)
    sim = cosine_similarity(tfidf)

    # Union-find
    parent = list(range(len(unique)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            if len(unique[ra]) <= len(unique[rb]):
                parent[rb] = ra
            else:
                parent[ra] = rb

    for i in range(len(unique)):
        for j in range(i + 1, len(unique)):
            if sim[i, j] > threshold:
                union(i, j)

    aliases = {}
    for i, val in enumerate(unique):
        root = find(i)
        canonical = unique[root]
        if canonical != val:
            aliases[val] = canonical

    return aliases


def normalize_title_signals(
    titles,
    conn,
    signal_types=None,
    threshold=0.6,
):
    """Normalize signals across a batch of titles in-place.

    Loads persistent aliases, discovers new ones, saves them, applies all.

    Args:
        titles: list of title dicts with signal fields
        conn: DB connection for alias persistence
        signal_types: which fields to normalize (default: places, persons, orgs, named_events)
        threshold: cosine similarity threshold

    Returns:
        dict of {signal_type: alias_map} showing all aliases applied (existing + new)
    """
    if signal_types is None:
        signal_types = ["places", "persons", "orgs", "named_events"]

    all_aliases = {}

    for sig_type in signal_types:
        # Step 1: Load existing aliases
        existing = load_aliases(conn, sig_type)

        # Step 2: Collect unique values from batch
        batch_values = set()
        for t in titles:
            for v in t.get(sig_type, []):
                batch_values.add(v)

        # Step 3: Apply existing aliases and find remaining unmatched
        unmatched = set()
        for v in batch_values:
            if v not in existing:
                unmatched.add(v)

        # Step 4: Discover new aliases among unmatched values
        # Also include existing canonicals so new values can match them
        existing_canonicals = set(existing.values())
        discover_pool = unmatched | existing_canonicals
        new_aliases = {}
        if len(discover_pool) >= 2:
            discovered = discover_aliases(list(discover_pool), threshold)
            # Only keep aliases for genuinely new values (not existing canonicals)
            for orig, canon in discovered.items():
                if orig in unmatched and orig != canon:
                    new_aliases[orig] = canon

        # Step 5: Save new aliases
        if new_aliases:
            save_aliases(conn, sig_type, new_aliases)

        # Step 6: Merge all aliases
        combined = {**existing, **new_aliases}

        if not combined:
            continue

        all_aliases[sig_type] = combined

        # Step 7: Apply to titles
        for t in titles:
            vals = t.get(sig_type, [])
            if not vals:
                continue
            new_vals = []
            seen = set()
            for v in vals:
                canonical = combined.get(v, v)
                if canonical not in seen:
                    seen.add(canonical)
                    new_vals.append(canonical)
            t[sig_type] = new_vals

    return all_aliases
