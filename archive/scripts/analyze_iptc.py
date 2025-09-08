#!/usr/bin/env python3
"""Quick analysis of IPTC structure."""
import json

with open("data/iptc_mediatopic.json", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total concepts: {len(data['conceptSet'])}")
print(f"Schema URI: {data['uri']}")

# Check for broader relationships
concepts_with_broader = [c for c in data["conceptSet"] if "broader" in c]
print(f"Concepts with broader: {len(concepts_with_broader)}")

if concepts_with_broader:
    example = concepts_with_broader[0]
    print(f"Example hierarchy: {example['uri']} -> {example['broader']}")
    print(f"  Label: {example['prefLabel']['en-GB']}")

# Show some top level concepts
top_concepts = [c for c in data["conceptSet"] if c["uri"] in data["hasTopConcept"][:5]]
print("\nTop 5 concepts:")
for c in top_concepts:
    code = c["uri"].split("/")[-1]
    print(f"  {code}: {c['prefLabel']['en-GB']}")

# Check available languages
if data["conceptSet"]:
    langs = list(data["conceptSet"][0]["prefLabel"].keys())
    print(f"\nAvailable languages: {langs}")
