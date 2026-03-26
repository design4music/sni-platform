"""
Post-extraction signal normalization via word-containment.

Places and persons: if a shorter form's words are a subset of a longer form,
normalize to the shorter form. E.g. "Strait of Hormuz" -> "Hormuz".

Orgs and named_events: no normalization (org names contain country/city names).

Learned aliases persist in signal_aliases table for cross-batch consistency.
"""

# Words to ignore when checking containment (geographic/title qualifiers, prepositions)
_STOP_WORDS = frozenset(
    {
        "of",
        "the",
        "de",
        "del",
        "di",
        "la",
        "le",
        "les",
        "das",
        "der",
        "die",
        "el",
        "al",
        "in",
        "du",
        "des",
        "van",
        "von",
        "do",
        "da",
    }
)


def _content_words(label):
    """Extract meaningful words from a label, lowercased."""
    return {w.lower() for w in label.split() if w.lower() not in _STOP_WORDS}


def _word_containment_aliases(values):
    """Find aliases via word containment: shorter form subsumes longer form.

    If words("Hormuz") is a subset of words("Strait of Hormuz"),
    map "Strait of Hormuz" -> "Hormuz".

    Returns: {original: canonical} where canonical is the shorter form.
    """
    if len(values) < 2:
        return {}

    unique = list(set(values))
    # Pre-compute content words for each value
    words_map = {v: _content_words(v) for v in unique}

    # Sort by number of content words (fewer words = more canonical)
    unique.sort(key=lambda v: (len(words_map[v]), len(v)))

    aliases = {}
    for i, shorter in enumerate(unique):
        sw = words_map[shorter]
        if not sw:
            continue
        for j in range(i + 1, len(unique)):
            longer = unique[j]
            if longer in aliases:
                continue
            lw = words_map[longer]
            # Shorter's words must be a non-empty subset of longer's words
            if sw < lw:  # strict subset
                aliases[longer] = shorter

    return aliases


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


def normalize_batch_signals(results, conn):
    """Normalize places and persons across a batch of parsed LLM results.

    1. Load known aliases from DB
    2. Apply them
    3. Discover new aliases via word-containment (batch + known canonicals)
    4. Save new aliases
    5. Apply new aliases

    Modifies results in-place. Only processes places and persons.
    """
    for sig_type in ("places", "persons"):
        # Step 1: Load existing aliases
        existing = load_aliases(conn, sig_type)

        # Step 2: Collect all unique values from batch
        batch_values = set()
        for r in results:
            for v in r.get(sig_type, []):
                batch_values.add(v)

        if not batch_values:
            continue

        # Step 3: Apply existing aliases, track unmatched
        unmatched = set()
        for v in batch_values:
            if v not in existing:
                unmatched.add(v)

        # Step 4: Discover new aliases among unmatched + existing canonicals
        existing_canonicals = set(existing.values())
        discover_pool = unmatched | existing_canonicals
        new_aliases = {}
        if len(discover_pool) >= 2:
            discovered = _word_containment_aliases(list(discover_pool))
            for orig, canon in discovered.items():
                if orig in unmatched and orig != canon:
                    new_aliases[orig] = canon

        # Step 5: Save new aliases
        if new_aliases:
            save_aliases(conn, sig_type, new_aliases)

        # Step 6: Merge and apply
        combined = {**existing, **new_aliases}
        if not combined:
            continue

        for r in results:
            vals = r.get(sig_type, [])
            if not vals:
                continue
            new_vals = []
            seen = set()
            for v in vals:
                canonical = combined.get(v, v)
                key = canonical.lower()
                if key not in seen:
                    seen.add(key)
                    new_vals.append(canonical)
            r[sig_type] = new_vals
