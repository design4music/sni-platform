# Entity Naming Inconsistency Report

**Date**: 2025-10-21
**Issue**: titles.entities contains mix of entity_ids (IL, PS, US, IN, AG) and name_en values (Israel, State of Palestine, United States, India)

## Problem Summary

The `titles.entities` JSONB field contains inconsistent naming:
- **Entity_ids (short codes)**: IL, PS, US, IN, AG, etc.
- **Full names (name_en)**: Israel, State of Palestine, United States, India, etc.

### Usage Statistics

From database analysis:
- **IL** (entity_id): 7 titles
- **Israel** (name_en): 29 titles ✓ Correct
- **PS** (entity_id): 6 titles
- **State of Palestine** (name_en): 47 titles ✓ Correct
- **US** (entity_id): 9 titles
- **United States** (name_en): 23 titles ✓ Correct
- **IN** (entity_id): 3 titles
- **India** (name_en): 7 titles ✓ Correct
- **AG** (entity_id): 1 title
- **UN** (NOT in data_entities): 23 titles ✗ Should be "United Nations"

**Total entity_ids being used incorrectly: 27 out of 158 unique entity names**

## Root Cause Analysis

### Two Sources of Entity Names

1. **taxonomy_extractor.py** (apps/filter/taxonomy_extractor.py:205-206, 252-254)
   - Returns `name_en` values (display names) ✓ CORRECT
   - Example: "United States", "Israel", "State of Palestine"

2. **entity_enrichment.py** (apps/filter/entity_enrichment.py:389-393)
   - `_match_llm_entities()` returns `entity_id` values ✗ WRONG
   - Example: "US", "IL", "PS", "IN", "AG"

```python
# apps/filter/entity_enrichment.py:389-393
# Current (WRONG) - returns entity_id
if entity_lower in self._entity_lookup:
    entity_id = self._entity_lookup[entity_lower]
    if entity_id not in matched_entity_ids:
        matched_entity_ids.append(entity_id)  # ← returns entity_id not name_en
```

The inconsistency occurs when:
- **Static taxonomy matches** → taxonomy_extractor returns name_en → stored correctly
- **LLM-extracted entities** → entity_enrichment returns entity_id → stored incorrectly

### Why UN Appears But Doesn't Exist

"UN" is NOT in `data_entities` table. The correct entity is:
- entity_id: `UNITED_NATIONS`
- name_en: `United Nations`

But "UN" appears in 23 titles, likely from:
1. LLM extracting "UN" from title text
2. Entity matching failing to find "UN" → no match
3. Raw LLM string "UN" being stored without validation

## Recommended Fix

### Option 1: Store name_en (Recommended)

**Pros:**
- Human-readable entity names
- Better for UI display and debugging
- Consistent with taxonomy_extractor behavior

**Cons:**
- Longer strings (more storage)
- Need lookup to get entity_id for queries

**Fix location:** apps/filter/entity_enrichment.py:389-393

```python
# Change _match_llm_entities to return name_en instead of entity_id
if entity_lower in self._entity_lookup:
    entity_id = self._entity_lookup[entity_lower]
    if entity_id not in matched_entity_ids:
        # Look up the canonical name_en for this entity_id
        name_en = self._entity_vocab[entity_id][0]  # First alias is name_en
        matched_entity_ids.append(name_en)  # ← return name_en not entity_id
```

### Option 2: Store entity_id (Alternative)

**Pros:**
- Shorter codes (less storage)
- Direct queries without lookup

**Cons:**
- Less human-readable
- Need to change taxonomy_extractor too
- More breaking changes

**Fix locations:**
- apps/filter/taxonomy_extractor.py:205-206, 252-254
- apps/filter/entity_enrichment.py:389-393

## Additional Fixes Needed

1. **Handle "UN" properly** - Add "UN" as alias for UNITED_NATIONS entity
2. **Backfill existing titles** - Update 27 titles with entity_ids to use name_en
3. **Data validation** - Ensure all stored entities exist in data_entities table

## Migration Script (if using Option 1)

```sql
-- Example: Convert entity_ids to name_en in titles.entities
UPDATE titles
SET entities = (
    SELECT jsonb_agg(
        COALESCE(
            (SELECT name_en FROM data_entities WHERE entity_id = elem::text),
            elem::text
        )
    )
    FROM jsonb_array_elements(entities) elem
)
WHERE entities IS NOT NULL AND entities != '[]';
```

## Recommendation

**Use Option 1 (store name_en)**:
1. More consistent with existing taxonomy_extractor behavior (minimal code changes)
2. Better for debugging and UI display
3. Aligns with how ~85% of entities are already stored

**Priority: HIGH** - This affects Phase 3 EF generation which relies on consistent entity naming for actor-based theater inference and ef_key generation.
