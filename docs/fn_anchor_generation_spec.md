# fn_anchor Bundle Generation Spec for LLM

## Purpose
Generate multilingual keyword aliases for Friction Node anchor bundles (`taxonomy_v3.aliases`). These keywords identify events in news that match a specific friction node through headline keyword matching + centroid_ids overlap.

## Critical Constraints

### 1. **False Positives Are Your Enemy**
- Keywords like "sovereignty", "warship", "military" will match HUNDREDS of unrelated events
- Example BAD: "warship" alone matches any naval story (not just this FN)
- Example GOOD: "AUKUS" + "Australia" + "China" = highly specific
- Test by asking: "Will this keyword appear in a headline about THIS specific issue?"

### 2. **Centroid Scoping**
The friction node has these centroid_ids:
```
PRIMARY: OCEANIA-AUSTRALIA, ASIA-CHINA
SECONDARY: AMERICAS-USA, ASIA-JAPAN, ASIA-SOUTHKOREA
```

Keywords should identify events where:
- **At least one** title has centroid overlap with the FN's centroids
- AND headline contains keyword(s) from the fn_anchor bundle

**False positive prevention**: Avoid pure geography keywords ("Australia", "China"). Use compound terms ("Australia-China", "Beijing-Canberra", "trade with China").

### 3. **Multilingual Requirements**
Return keywords in these 10 languages:
- **en**: English
- **ar**: Arabic (news sources: Al Jazeera, others)
- **de**: German (news sources: DW, others)
- **es**: Spanish (news sources: RT Spanish, others)
- **fr**: French (news sources: France 24, others)
- **hi**: Hindi (news sources: India Today, others)
- **it**: Italian (news sources: ANSA, others)
- **ja**: Japanese (news sources: NHK, others)
- **ru**: Russian (news sources: TASS, others)
- **zh**: Chinese (news sources: Xinhua, others)

**Translation rule**: Translate the CONCEPT, not the English word. For example:
- "AUKUS" → stays "AUKUS" in all languages (proper noun)
- "quad" (security alliance) → "Quad" (EN), "Quad" (FR), etc.
- "critical minerals" → German: "kritische Rohstoffe", Chinese: "关键矿物", etc.

### 4. **Keyword Categories** (Examples from Iran Nuclear Program)

**Location-specific** (highly specific, low false positives):
- Facility names: Natanz, Fordow, Bushehr, Arak, Isfahan
- Region/country names with context: not standalone "Iran" but "Iranian nuclear", "Tehran nuclear negotiations"

**Actor names** (highly specific):
- Key officials: Fakhrizadeh, Salehi, Khamenei (but only if central to THIS FN)
- Organization names: IAEA, AEOI, but not generic "government"

**Technical/Domain terms** (must be specific to this FN):
- Enrichment, centrifuge, uranium, plutonium, heavy water ✓
- Nuclear (alone) ✗ — too broad

**Deal/Agreement names**:
- JCPOA, SVPD (Iran Deal variants) ✓
- "negotiations" (alone) ✗ — too broad

**Process/event terms**:
- Vienna talks, snapback, snapback mechanism ✓
- "sanctions" (alone) ✗ — too broad

### 5. **What NOT to Include**

❌ Single-word adjectives: sovereign, strategic, military, defense, security
❌ Generic verbs: attack, bomb, strike, negotiate (only in compounds: "cyber attack on Australia")
❌ Broad nouns: sanctions, talks, crisis, tensions, deal
❌ Country names alone: Australia, China, USA (only in context compounds)

✓ Use compound forms: "Australia-China" "Beijing-Canberra", "US-Australia alliance"

---

## Theater Context: Australia-China Rivalry

**Theater ID**: `australia_china_theater`  
**Theater Name**: Australia-China strategic rivalry  
**Centroid IDs**: OCEANIA-AUSTRALIA, ASIA-CHINA, AMERICAS-USA, ASIA-JAPAN, ASIA-SOUTHKOREA

### Three Atomic Friction Nodes to Generate for:

#### 1. **security_alignment** (AUKUS and Indo-Pacific security partnership)
- **Concept**: Australia + US + UK military alliance in Indo-Pacific
- **Key actors**: AUKUS (Australia, US, UK), Quad (US, Japan, India, Australia), Five Eyes
- **Tech angle**: Submarines (AUKUS), hypersonics, cyber capabilities
- **Geographic**: Indo-Pacific, South China Sea, Taiwan Strait mentions with Australia role
- **Key keywords**: AUKUS, Quad, Five Eyes, ANZUS, US-Australia alliance, Indo-Pacific, submarine, Taiwan Strait (+ Australia context)

#### 2. **economic_coercion** (Economic sanctions and trade weaponization)
- **Concept**: China-Australia trade conflicts, tech export controls, critical minerals
- **Key products**: Coal, iron ore, barley, wine, lobster (China's bans), semiconductors
- **Key issues**: Export restrictions, tech decoupling, critical minerals, rare earths, supply chains
- **Key keywords**: Trade war with China, export ban, critical minerals, supply chain disruption, Australian coal ban, barley tariff, decoupling, economic coercion, rare earths

#### 3. **pacific_island_alignment** (Geopolitical competition in Pacific island states)
- **Concept**: Solomon Islands, Vanuatu, Fiji, Kiribati choosing sides (China vs Australia/US)
- **Key countries**: Solomon Islands, Vanuatu, Kiribati, Tonga, Samoa, Micronesia, Papua New Guinea
- **Key issues**: China security deals, police training, infrastructure loans, Taiwan recognition, Australia-China competition
- **Key keywords**: Solomon Islands China agreement, Beijing diplomatic push, Pacific islands, Taiwan recognition Nauru Palau, police training, security pact, infrastructure investment, Chinese presence in Pacific

---

## Output Format

Return a JSON object with this structure:

```json
{
  "en": [
    "keyword 1",
    "keyword 2",
    "keyword 3",
    ...
  ],
  "ar": [
    "كلمة مفتاحية 1",
    ...
  ],
  "de": [
    "Stichwort 1",
    ...
  ],
  ... (all 10 languages)
}
```

### Expectations
- **40-60 total keywords per FN** across all languages (roughly 4-6 per language on average)
- **Mix of English loanwords** (AUKUS, Quad, JCPOA) across all languages when appropriate
- **Proper nouns unchanged** (AUKUS stays AUKUS in German, Chinese, etc.)
- **Geopolitical specificity**: Avoid duplicates, prioritize unique identifiers

---

## Example: Iran Proxy Network (Reference)

For comparison, `iran_proxy_network` fn_anchor includes:
- English: Hezbollah, Hamas, Houthi/Houthis, IRGC, Quds Force, Iraqi PMF, Kataib Hezbollah, Axis of Resistance, Iran-backed, Iran-aligned, commander killed, commander assassinated
- Arabic: حزب الله (Hezbollah), حماس, الحرس الثوري, قوة القدس, etc.
- German: Hisbollah, Hamas, IRGC-Marine, Quds-Truppe, etc.

**Key traits**:
- Proper names (Hezbollah) translate phonetically, not semantically
- Acronyms (IRGC, PMF) stay consistent across languages
- Compound modifiers: "Iran-backed", "Iran-aligned" prevent false positives
- Technical role terms: "Quds commander", "Quds Force" (not just "commander")

---

## Your Task

Generate fn_anchor bundles for the three atomic FNs under `australia_china_theater`:
1. **security_alignment**
2. **economic_coercion**
3. **pacific_island_alignment**

For each FN:
- Follow the false-positive prevention rules above
- Ensure 40-60 keywords across all 10 languages
- Balance proper nouns, acronyms, and compound phrases
- Avoid generic terms that would match hundreds of unrelated events
- Return as valid JSON with all 10 language keys

---

## Success Criteria

✓ Keywords are specific enough that 80%+ of matched events are actually about this FN  
✓ Keywords are comprehensive enough that 70%+ of real events about this FN contain at least one keyword  
✓ No single-word false positives (all high-risk words used as compounds)  
✓ All 10 languages represented with context-appropriate translations  
✓ Proper nouns and acronyms consistent across languages
