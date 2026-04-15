"""Rewrite narrative_taxonomy_v2.yaml to use ELO v3.0.1 action_class names.

Idempotent find-replace: old->new. Preserves structure. Duplicates within
action_classes lists (after substitution) are harmless because the loader
dedupes into a set.
"""

import re
from pathlib import Path

SUBSTITUTIONS = [
    ("LEGAL_RULING", "LEGAL_ACTION"),
    ("LEGAL_CONTESTATION", "LEGAL_ACTION"),
    ("POLITICAL_PRESSURE", "PRESSURE"),
    ("DIPLOMATIC_PRESSURE", "PRESSURE"),
    ("COLLECTIVE_PROTEST", "CIVIL_ACTION"),
    ("ECONOMIC_DISRUPTION", "MARKET_SHOCK"),
    ("SOCIAL_INCIDENT", "SECURITY_INCIDENT"),
]

path = Path(__file__).resolve().parents[2] / "docs" / "narrative_taxonomy_v2.yaml"
text = path.read_text(encoding="utf-8")

# Replace whole-word only (so "LEGAL_RULING_X" if it existed wouldn't match)
for old, new in SUBSTITUTIONS:
    before = text.count(old)
    text = re.sub(rf"\b{old}\b", new, text)
    after_old = text.count(old)
    after_new = text.count(new)
    print(f"  {old:22s} -> {new:15s}  replaced {before} ({after_old} remaining)")

path.write_text(text, encoding="utf-8")
print(f"\nWrote {path}")
print(f"Final size: {len(text)} chars")
