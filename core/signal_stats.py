"""
Tier 1 Signal Stats: compute hard coverage statistics for an event.

No LLM calls -- pure SQL + Python aggregation.
"""

import json
from collections import Counter

from psycopg2.extras import RealDictCursor


def herfindahl(counter):
    """Herfindahl-Hirschman Index: 0 = perfectly diverse, 1 = monopoly."""
    total = sum(counter.values())
    if total == 0:
        return 0.0
    return round(sum((c / total) ** 2 for c in counter.values()), 4)


def _top_n(counter, n=5):
    """Return top-N items with count and share."""
    total = sum(counter.values())
    if total == 0:
        return []
    return [
        {"name": name, "count": count, "share": round(count / total, 3)}
        for name, count in counter.most_common(n)
    ]


def compute_event_stats(conn, event_id):
    """Compute coverage statistics for a single event.

    Returns a dict ready to store as narratives.signal_stats JSONB.
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT t.publisher_name,
                   t.detected_language,
                   t.pubdate_utc,
                   tl.actor,
                   tl.action_class,
                   tl.domain,
                   tl.target,
                   tl.persons,
                   tl.orgs,
                   tl.entity_countries
            FROM event_v3_titles et
            JOIN titles_v3 t ON t.id = et.title_id
            LEFT JOIN title_labels tl ON tl.title_id = et.title_id
            WHERE et.event_id = %s
            """,
            (str(event_id),),
        )
        rows = cur.fetchall()

    if not rows:
        return {}

    title_count = len(rows)
    labeled_count = sum(1 for r in rows if r["actor"] is not None)

    # Publishers
    pub_counter = Counter(r["publisher_name"] for r in rows if r["publisher_name"])

    # Languages
    lang_counter = Counter(
        r["detected_language"] for r in rows if r["detected_language"]
    )

    # Domains, action classes, actors
    domain_counter = Counter(r["domain"] for r in rows if r["domain"])
    action_counter = Counter(r["action_class"] for r in rows if r["action_class"])
    actor_counter = Counter(r["actor"] for r in rows if r["actor"])

    # Persons and orgs (array columns)
    person_counter = Counter()
    org_counter = Counter()
    for r in rows:
        for p in r["persons"] or []:
            person_counter[p] += 1
        for o in r["orgs"] or []:
            org_counter[o] += 1

    # Entity countries (JSONB: {entity: code, ...})
    country_counter = Counter()
    for r in rows:
        ec = r["entity_countries"]
        if isinstance(ec, str):
            ec = json.loads(ec) if ec else {}
        if isinstance(ec, dict):
            for code in ec.values():
                if code:
                    country_counter[code] += 1

    # Date range
    dates = [r["pubdate_utc"] for r in rows if r["pubdate_utc"]]
    if len(dates) >= 2:
        date_range_days = (max(dates) - min(dates)).days
    else:
        date_range_days = 0

    # Narrative frame count (how many narratives exist for this event)
    with conn.cursor() as cur2:
        cur2.execute(
            "SELECT COUNT(*) FROM narratives WHERE entity_type = 'event' AND entity_id = %s",
            (str(event_id),),
        )
        narrative_frame_count = cur2.fetchone()[0]

    return {
        "title_count": title_count,
        "publisher_count": len(pub_counter),
        "publisher_hhi": herfindahl(pub_counter),
        "top_publishers": _top_n(pub_counter, 5),
        "language_count": len(lang_counter),
        "language_distribution": dict(lang_counter.most_common(10)),
        "entity_country_distribution": dict(country_counter.most_common(15)),
        "domain_distribution": dict(domain_counter),
        "action_class_distribution": dict(action_counter),
        "actor_count": len(actor_counter),
        "top_actors": _top_n(actor_counter, 5),
        "person_count": len(person_counter),
        "top_persons": _top_n(person_counter, 5),
        "top_orgs": _top_n(org_counter, 5),
        "narrative_frame_count": narrative_frame_count,
        "date_range_days": date_range_days,
        "label_coverage": round(labeled_count / title_count, 2) if title_count else 0,
    }


if __name__ == "__main__":
    import argparse

    import psycopg2

    from core.config import get_config

    parser = argparse.ArgumentParser(description="Print signal stats for an event")
    parser.add_argument("--event-id", required=True, help="Event UUID")
    args = parser.parse_args()

    cfg = get_config()
    conn = psycopg2.connect(
        host=cfg.db_host,
        port=cfg.db_port,
        dbname=cfg.db_name,
        user=cfg.db_user,
        password=cfg.db_password,
    )
    stats = compute_event_stats(conn, args.event_id)
    conn.close()

    print(json.dumps(stats, indent=2, default=str))
