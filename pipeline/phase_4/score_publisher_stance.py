"""Score publisher stance toward centroids.

For each (feed, centroid, month) tuple with >= 20 titles, sample up to 30
headlines and ask the LLM to rate tone on a -2..+2 scale.

Usage:
    python -m pipeline.phase_4.score_publisher_stance --month 2026-02 --dry-run
    python -m pipeline.phase_4.score_publisher_stance --month 2026-02 --limit 50
    python -m pipeline.phase_4.score_publisher_stance --feed CNN --centroid US --month 2026-02
"""

import argparse
import json
import sys
import time
from pathlib import Path

import httpx
import psycopg2
from psycopg2.extras import RealDictCursor

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config
from core.llm_utils import check_rate_limit, extract_json

MIN_TITLES = 20
SAMPLE_SIZE = 30

# -- Publisher map (mirrors queries.ts PUBLISHER_MAP_VALUES) --
_PAIRS = [
    ("ABC News", "Australian Broadcasting Corporation"),
    ("AFP", "AFP Fact Check"),
    ("AFP", "afp.com"),
    ("Al Arabiya", "Al Arabiya English"),
    ("Al Arabiya", "alarabiya.net"),
    ("Al Jazeera", None),
    ("Associated Press", "AP News"),
    ("Associated Press", "Associated Press News"),
    ("BBC World", "BBC"),
    ("Bloomberg", "Bloomberg.com"),
    ("CGTN", "news.cgtn.com"),
    ("CGTN", "newsaf.cgtn.com"),
    ("CGTN", "newsus.cgtn.com"),
    ("CNN", "cnn.com"),
    ("Deutsche Welle", "dw.com"),
    ("Deutsche Welle", "DW.com"),
    ("Deutsche Welle", "DW"),
    ("Fox News", "foxnews.com"),
    ("New York Times", "The New York Times"),
    ("New York Times", "nytimes.com"),
    ("Reuters", None),
    ("RT", "rt.com"),
    ("RT", "Russia Today"),
    ("TASS (EN)", "tass.com"),
    ("TASS", "tass.ru"),
    ("Wall Street Journal", "The Wall Street Journal"),
    ("Wall Street Journal", "WSJ"),
    ("Washington Post", "The Washington Post"),
    ("Washington Post", "washingtonpost.com"),
    ("Xinhua", "Xinhuanet Deutsch"),
]

PUBLISHER_MAP = {}
for _fn, _var in _PAIRS:
    if _fn not in PUBLISHER_MAP:
        PUBLISHER_MAP[_fn] = []
    if _var:
        PUBLISHER_MAP[_fn].append(_var)

# -- Prompts --

STANCE_SYSTEM = (
    "You are a media-tone analyst. You assess the editorial tone of news "
    "headlines from a specific publisher toward a specific country or region."
)

STANCE_USER = """Publisher: {feed_name}
Country/Region: {centroid_label} ({centroid_id})
Month: {month}

Below are {sample_count} headlines from this publisher about this region.

{titles_block}

Rate the overall editorial TONE of these headlines toward {centroid_label} on this scale:
-2 = Hostile (demonizing, enemy framing, calls for punishment)
-1 = Critical (negative framing, emphasis on threats/failures)
 0 = Neutral (factual reporting, balanced framing)
+1 = Favorable (positive framing, emphasis on achievements/cooperation)
+2 = Supportive (advocacy, ally framing, promotion)

Consider: word choice, what is emphasized vs omitted, framing of actors, implied moral judgments.

Return ONLY a JSON object:
{{"score": <float from -2.0 to 2.0>, "confidence": <float 0-1>, "reasoning": "<1 sentence>"}}"""


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        dbname=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def fetch_eligible_pairs(cur, month, feed_name=None, centroid_id=None, limit=500):
    """Find (feed_name, centroid_id) pairs with >= MIN_TITLES titles in month."""
    month_date = month + "-01"
    conditions = [
        "t.pubdate_utc >= %s::date",
        "t.pubdate_utc < %s::date + interval '1 month'",
    ]
    params = [month_date, month_date]

    if feed_name:
        # Get all publisher name variants
        variants = PUBLISHER_MAP.get(feed_name, [])
        pub_names = [feed_name] + variants
        placeholders = ",".join(["%s"] * len(pub_names))
        conditions.append("t.publisher_name IN (%s)" % placeholders)
        params.extend(pub_names)

    if centroid_id:
        conditions.append("ta.centroid_id = %s")
        params.append(centroid_id)

    where = " AND ".join(conditions)

    cur.execute(
        """
        SELECT f.name as feed_name, ta.centroid_id, cv.label as centroid_label,
               COUNT(DISTINCT t.id) as title_count
        FROM titles_v3 t
        JOIN title_assignments ta ON ta.title_id = t.id
        JOIN feeds f ON f.name = t.publisher_name OR t.publisher_name = f.name
        JOIN centroids_v3 cv ON cv.id = ta.centroid_id
        WHERE %s
          AND t.publisher_name IS NOT NULL
          AND f.is_active = true
        GROUP BY f.name, ta.centroid_id, cv.label
        HAVING COUNT(DISTINCT t.id) >= %s
        ORDER BY COUNT(DISTINCT t.id) DESC
        LIMIT %s
        """
        % (where, "%s", "%s"),
        params + [MIN_TITLES, limit],
    )
    return cur.fetchall()


def fetch_eligible_pairs_simple(
    cur, month, feed_name=None, centroid_id=None, limit=500
):
    """Find pairs with >= MIN_TITLES. Uses publisher_name directly, no feed join."""
    month_date = month + "-01"

    # Build all known feed->variants for grouping
    cur.execute("SELECT name FROM feeds WHERE is_active = true")
    all_feeds = [r["name"] for r in cur.fetchall()]

    # For each feed, get variant names
    feed_variants = {}
    for fn in all_feeds:
        variants = PUBLISHER_MAP.get(fn, [])
        feed_variants[fn] = [fn] + variants

    # Build reverse map: publisher_name -> feed_name
    pub_to_feed = {}
    for fn, variants in feed_variants.items():
        for v in variants:
            pub_to_feed[v] = fn

    # Fetch raw counts grouped by publisher_name + centroid
    conds = [
        "t.pubdate_utc >= %s::date",
        "t.pubdate_utc < %s::date + interval '1 month'",
        "t.publisher_name IS NOT NULL",
    ]
    params = [month_date, month_date]

    if centroid_id:
        conds.append("ta.centroid_id = %s")
        params.append(centroid_id)

    cur.execute(
        """
        SELECT t.publisher_name, ta.centroid_id, cv.label as centroid_label,
               COUNT(DISTINCT t.id) as cnt
        FROM titles_v3 t
        JOIN title_assignments ta ON ta.title_id = t.id
        JOIN centroids_v3 cv ON cv.id = ta.centroid_id
        WHERE %s
        GROUP BY t.publisher_name, ta.centroid_id, cv.label
        """
        % " AND ".join(conds),
        params,
    )
    raw = cur.fetchall()

    # Aggregate by canonical feed_name
    agg = {}
    for r in raw:
        fn = pub_to_feed.get(r["publisher_name"], r["publisher_name"])
        # Check if fn is actually a known feed
        if fn not in feed_variants:
            continue
        key = (fn, r["centroid_id"])
        if key not in agg:
            agg[key] = {
                "feed_name": fn,
                "centroid_id": r["centroid_id"],
                "centroid_label": r["centroid_label"],
                "title_count": 0,
            }
        agg[key]["title_count"] += r["cnt"]

    # Filter by min titles and optional feed_name
    results = []
    for pair in agg.values():
        if pair["title_count"] < MIN_TITLES:
            continue
        if feed_name and pair["feed_name"] != feed_name:
            continue
        results.append(pair)

    results.sort(key=lambda x: x["title_count"], reverse=True)
    return results[:limit]


def sample_titles(cur, feed_name, centroid_id, month, n=SAMPLE_SIZE):
    """Sample titles for a (feed, centroid, month) pair."""
    variants = PUBLISHER_MAP.get(feed_name, [])
    pub_names = [feed_name] + variants
    placeholders = ",".join(["%s"] * len(pub_names))
    month_date = month + "-01"

    cur.execute(
        """
        SELECT t.title_display, t.publisher_name
        FROM titles_v3 t
        JOIN title_assignments ta ON ta.title_id = t.id
        WHERE t.publisher_name IN (%s)
          AND ta.centroid_id = %%s
          AND t.pubdate_utc >= %%s::date
          AND t.pubdate_utc < %%s::date + interval '1 month'
        ORDER BY random()
        LIMIT %%s
        """
        % placeholders,
        pub_names + [centroid_id, month_date, month_date, n],
    )
    return cur.fetchall()


def build_titles_block(titles):
    lines = []
    for i, t in enumerate(titles, 1):
        lines.append("%d. %s" % (i, t["title_display"]))
    return "\n".join(lines)


def score_stance_llm(feed_name, centroid_id, centroid_label, month, titles):
    """Call LLM to score stance. Returns (score, confidence, reasoning)."""
    titles_block = build_titles_block(titles)

    user_prompt = STANCE_USER.format(
        feed_name=feed_name,
        centroid_id=centroid_id,
        centroid_label=centroid_label,
        month=month,
        sample_count=len(titles),
        titles_block=titles_block,
    )

    headers = {
        "Authorization": "Bearer %s" % config.deepseek_api_key,
        "Content-Type": "application/json",
    }

    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": STANCE_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 200,
    }

    for attempt in range(config.llm_retry_attempts):
        resp = httpx.post(
            "%s/chat/completions" % config.deepseek_api_url,
            headers=headers,
            json=payload,
            timeout=60,
        )
        if check_rate_limit(resp, attempt):
            continue
        if resp.status_code != 200:
            raise Exception("LLM error: %d - %s" % (resp.status_code, resp.text[:200]))
        break

    data = resp.json()
    content = data["choices"][0]["message"]["content"].strip()
    usage = data.get("usage", {})
    tok_in = usage.get("prompt_tokens", 0)
    tok_out = usage.get("completion_tokens", 0)

    result = extract_json(content)
    score = float(result["score"])
    score = max(-2.0, min(2.0, score))
    confidence = float(result.get("confidence", 0.5))
    reasoning = result.get("reasoning", "")

    return score, confidence, reasoning, tok_in, tok_out


def run(month, feed_name=None, centroid_id=None, limit=500, dry_run=False):
    conn = get_connection()
    total_tok_in = 0
    total_tok_out = 0
    scored = 0
    skipped = 0

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            print("Finding eligible pairs for %s..." % month)
            pairs = fetch_eligible_pairs_simple(
                cur, month, feed_name=feed_name, centroid_id=centroid_id, limit=limit
            )
            print("Found %d pairs with >= %d titles" % (len(pairs), MIN_TITLES))

            if dry_run:
                for p in pairs[:20]:
                    print(
                        "  %s -> %s (%s): %d titles"
                        % (
                            p["feed_name"],
                            p["centroid_id"],
                            p["centroid_label"],
                            p["title_count"],
                        )
                    )
                if len(pairs) > 20:
                    print("  ... and %d more" % (len(pairs) - 20))
                return

            # Filter out already-scored pairs
            month_date = month + "-01"
            cur.execute(
                "SELECT feed_name, centroid_id FROM publisher_stance WHERE month = %s",
                (month_date,),
            )
            existing = {(r["feed_name"], r["centroid_id"]) for r in cur.fetchall()}

            for p in pairs:
                key = (p["feed_name"], p["centroid_id"])
                if key in existing:
                    skipped += 1
                    continue

                titles = sample_titles(cur, p["feed_name"], p["centroid_id"], month)
                if len(titles) < 10:
                    skipped += 1
                    continue

                start = time.time()
                try:
                    score, confidence, reasoning, tok_in, tok_out = score_stance_llm(
                        p["feed_name"],
                        p["centroid_id"],
                        p["centroid_label"],
                        month,
                        titles,
                    )
                except Exception as e:
                    print(
                        "  ERROR %s -> %s: %s" % (p["feed_name"], p["centroid_id"], e)
                    )
                    skipped += 1
                    continue

                total_tok_in += tok_in
                total_tok_out += tok_out
                elapsed = time.time() - start

                # Store sample titles as compact JSON
                sample_json = [
                    {"title": t["title_display"][:200], "pub": t["publisher_name"]}
                    for t in titles[:10]
                ]

                cur.execute(
                    """INSERT INTO publisher_stance
                       (feed_name, centroid_id, month, score, confidence, sample_size,
                        sample_titles, computed_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                       ON CONFLICT (feed_name, centroid_id, month) DO UPDATE
                       SET score = EXCLUDED.score, confidence = EXCLUDED.confidence,
                           sample_size = EXCLUDED.sample_size,
                           sample_titles = EXCLUDED.sample_titles,
                           computed_at = NOW()""",
                    (
                        p["feed_name"],
                        p["centroid_id"],
                        month_date,
                        score,
                        confidence,
                        len(titles),
                        json.dumps(sample_json),
                    ),
                )
                conn.commit()
                scored += 1

                sign = "+" if score > 0 else ""
                print(
                    "  %s -> %s: %s%.1f (conf=%.0f%%) [%s] %.1fs"
                    % (
                        p["feed_name"],
                        p["centroid_label"],
                        sign,
                        score,
                        confidence * 100,
                        reasoning[:60],
                        elapsed,
                    )
                )

        print("\nDone: %d scored, %d skipped" % (scored, skipped))
        cost = (total_tok_in * 0.14 + total_tok_out * 0.28) / 1_000_000
        print("Tokens: %d in + %d out = ~$%.3f" % (total_tok_in, total_tok_out, cost))
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Score publisher stance toward centroids"
    )
    parser.add_argument("--month", required=True, help="Month (YYYY-MM)")
    parser.add_argument("--feed", help="Specific feed name")
    parser.add_argument("--centroid", help="Specific centroid ID")
    parser.add_argument("--limit", type=int, default=500, help="Max pairs to process")
    parser.add_argument(
        "--dry-run", action="store_true", help="List pairs without scoring"
    )
    args = parser.parse_args()
    run(
        args.month,
        feed_name=args.feed,
        centroid_id=args.centroid,
        limit=args.limit,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
