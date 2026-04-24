"""Stratified 50-row sample from stance pilot v3 results for manual review.

Outputs:
    out/stance_pilot/review_50.md   — readable markdown, mark ✓/✗/? per row
    out/stance_pilot/review_50.csv  — Excel-friendly, same rows

Stratification (per language: en, de, ru, ar, ja):
    3 framed-strong (at least one target with p=±2)
    4 framed-soft   (all targets |p|=1)
    3 report
= 10 per language × 5 languages = 50 rows.

If a bucket is thin (e.g. ja strong-framed), fills remainder from framed-soft.
Seed is fixed for reproducibility.
"""

import csv
import json
import random
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")

SEED = 17
LANGS = ("en", "de", "ru", "ar", "ja")
PER_LANG_SPEC = [("strong", 3), ("soft", 4), ("report", 3)]
IN_PATH = Path("out/stance_pilot/results.csv")
MD_PATH = Path("out/stance_pilot/review_50.md")
CSV_PATH = Path("out/stance_pilot/review_50.csv")


def has_strong(targets):
    return any(t["p"] in (-2, 2) for t in targets)


def classify(row):
    if row["llm_mode"] == "report":
        return "report"
    targets = json.loads(row["llm_targets_json"])
    if not targets:
        return "report"
    return "strong" if has_strong(targets) else "soft"


def fmt_targets(targets):
    parts = []
    for t in targets:
        label = (
            "%s(%s)" % (t.get("name", "?"), t["c"])
            if t.get("t") == "person"
            else t["c"]
        )
        markers = " / ".join(t.get("m", []))
        parts.append("%s%+d [%s]" % (label, t["p"], markers))
    return " · ".join(parts) if parts else "—"


def main():
    random.seed(SEED)
    rows = list(csv.DictReader(open(IN_PATH, encoding="utf-8")))

    # Bucket by (lang, class)
    buckets = {(lang, cls): [] for lang in LANGS for cls, _ in PER_LANG_SPEC}
    for r in rows:
        lang = r["language"]
        if lang not in LANGS:
            continue
        cls = classify(r)
        buckets[(lang, cls)].append(r)

    # Sample with fallback
    selected = []
    for lang in LANGS:
        lang_picks = []
        remainder_pool = []
        for cls, n in PER_LANG_SPEC:
            pool = buckets[(lang, cls)]
            random.shuffle(pool)
            take = pool[:n]
            lang_picks.extend([(cls, r) for r in take])
            remainder_pool.extend(pool[n:])
        # Fill shortage with any remaining items from the language
        random.shuffle(remainder_pool)
        target_total = sum(n for _, n in PER_LANG_SPEC)
        while len(lang_picks) < target_total and remainder_pool:
            r = remainder_pool.pop()
            lang_picks.append((classify(r), r))
        selected.extend(lang_picks)

    # --- Write CSV (annotation-friendly) ---
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "review_call",
                "notes",
                "language",
                "classification",
                "sector",
                "title_display",
                "llm_mode",
                "targets_summary",
                "persons_labels",
                "actor",
                "publisher",
                "title_id",
            ]
        )
        for cls, r in selected:
            targets = json.loads(r["llm_targets_json"])
            w.writerow(
                [
                    "",  # review_call — user fills in ✓/✗/?
                    "",  # notes
                    r["language"],
                    cls,
                    r["sector"],
                    r["title_display"],
                    r["llm_mode"],
                    fmt_targets(targets),
                    r.get("persons_labels", ""),
                    r["actor"],
                    r["publisher"],
                    r["title_id"],
                ]
            )

    # --- Write markdown (skim-friendly) ---
    md = ["# Stance Pilot — 50-Row Manual Review\n"]
    md.append(
        "Mark each row ✓ (correct) / ✗ (miscall) / ? (borderline) in `review_50.csv` "
        "(open in Excel; fill the `review_call` column)."
    )
    md.append("")
    md.append(
        "Sample: 10 per language × 5 languages, stratified 3 strong-framed / 4 soft-framed / 3 report."
    )
    md.append("")
    # Group rows by language for readability
    by_lang = {lang: [] for lang in LANGS}
    for cls, r in selected:
        by_lang[r["language"]].append((cls, r))

    for lang in LANGS:
        md.append("## %s (%d rows)" % (lang.upper(), len(by_lang[lang])))
        md.append("")
        md.append("| # | class | sector | title | targets | persons[] |")
        md.append("|---|---|---|---|---|---|")
        for i, (cls, r) in enumerate(by_lang[lang], 1):
            targets = json.loads(r["llm_targets_json"])
            title = r["title_display"].replace("|", "¦")[:140]
            tgt = fmt_targets(targets).replace("|", "¦")
            persons = r.get("persons_labels", "")
            if persons and len(persons) > 40:
                persons = persons[:37] + "..."
            md.append(
                "| %d | %s | %s | %s | %s | %s |"
                % (i, cls, r["sector"], title, tgt, persons.replace("|", "¦"))
            )
        md.append("")

    MD_PATH.write_text("\n".join(md), encoding="utf-8")
    print("Wrote: %s" % CSV_PATH)
    print("Wrote: %s" % MD_PATH)
    print("Total rows: %d" % len(selected))


if __name__ == "__main__":
    main()
