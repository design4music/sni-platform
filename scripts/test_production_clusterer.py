"""Run the actual production cluster_by_day_beat against the suspect CTMs
to verify Fixes #1 + #2 work end-to-end."""

import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Override DB env BEFORE any pipeline imports
os.environ["DB_HOST"] = "dpg-d5uem563jp1c739ufrsg-a.frankfurt-postgres.render.com"
os.environ["DB_USER"] = "maxgenrih55"
os.environ["DB_NAME"] = "sni_v2"
os.environ["DB_PASSWORD"] = "DGiBGNv89pGtRsaj5Ys2fCN4DFMEmCUb"
os.environ["DB_PORT"] = "5432"

from collections import Counter  # noqa: E402

from pipeline.phase_4.incremental_clustering import (  # noqa: E402
    _extract_discriminating_entities,
    _single_link_by_entity,
    get_connection,
    load_titles_chronological,
)


def main():
    targets = [
        ("8e9a06ce-524d-4e70-8429-9ed964654519", "UAE leaves OPEC", "AMERICAS-USA"),
        (
            "dd6f66aa-c362-42e9-a9dc-bc9ef9d95b35",
            "USA/Politics Charles-Merz",
            "AMERICAS-USA",
        ),
        (
            "0daae61d-4992-4773-b4be-f95f5b740b34",
            "USA/Security 5000 troops",
            "AMERICAS-USA",
        ),
        (
            "2cfa6687-cc88-4300-8461-b7139c84a9fb",
            "USA/Economy ChatGPT/Apple",
            "AMERICAS-USA",
        ),
    ]
    conn = get_connection()
    try:
        for ctm_id, label, _ in targets:
            print(f"\n=== {label} ===")
            titles = load_titles_chronological(conn, ctm_id)
            # Group by pubdate (date part) because production clusters per day
            by_date = {}
            for t in titles:
                d = (
                    t["pubdate_utc"].date().isoformat()
                    if t.get("pubdate_utc")
                    else None
                )
                by_date.setdefault(d, []).append(t)
            print(f"  {len(titles)} titles across {len(by_date)} dates")
            for date, ts in sorted(by_date.items()):
                if len(ts) < 30:
                    continue
                clusters = _single_link_by_entity(ts)
                big = [c for c in clusters if len(c["titles"]) >= 5]
                print(
                    f"\n  {date} ({len(ts)} titles → {len(clusters)} clusters, {len(big)} big):"
                )
                for c in sorted(big, key=lambda c: -len(c["titles"]))[:5]:
                    cnt = Counter()
                    for t in c["titles"]:
                        for e in _extract_discriminating_entities(t):
                            cnt[e] += 1
                    spine = cnt.most_common(1)[0][0] if cnt else "(ngram)"
                    sample = c["titles"][0]["title_display"][:80]
                    print(
                        f'    size={len(c["titles"]):3}  spine={spine:35}  e.g. {sample}'
                    )
    finally:
        conn.close()


if __name__ == "__main__":
    main()
