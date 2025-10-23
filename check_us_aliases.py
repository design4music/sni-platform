#!/usr/bin/env python3
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from apps.filter.vocab_loader_db import load_actor_aliases

aliases = load_actor_aliases()

with open("us_aliases.txt", "w", encoding="utf-8") as f:
    f.write(f"US aliases ({len(aliases['US'])} total):\n\n")

    # Show ALL aliases
    for i, alias in enumerate(aliases["US"], 1):
        f.write(f"  {i}. '{alias}'\n")

    f.write("\n\n" + "=" * 60 + "\n")
    f.write("Checking if U.S. variants are present:\n")
    for check in ["U.S.", "U.S.A.", "US", "USA", "u.s.", "United States"]:
        if check in aliases["US"]:
            f.write(f"  '{check}' - FOUND\n")
        else:
            f.write(f"  '{check}' - MISSING\n")

    # Check if filtering is removing these
    from apps.filter.vocab_loader_db import _is_usable_short_code

    f.write("\n" + "=" * 60 + "\n")
    f.write("Filter test results:\n")
    for check in ["US", "USA", "U.S.", "UK", "UAE", "AD", "AND", "ae"]:
        result = _is_usable_short_code(check)
        f.write(f"  '{check}' -> {result} ({'KEPT' if result else 'FILTERED'})\n")

print("Output written to us_aliases.txt")
