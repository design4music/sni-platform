# Phase 3 v3: CTM Builder

This phase assigns strategic tracks to titles and aggregates them into CTM (Centroid-Track-Month) units.

## Track Classification

Uses LLM to classify each title into one of 7 strategic tracks:

- `military` - Armed conflict, defense operations, military movements
- `diplomacy` - Negotiations, summits, treaties, diplomatic initiatives
- `economic` - Trade, sanctions, economic policy, financial flows
- `tech_cyber` - Technology competition, cybersecurity, digital infrastructure
- `humanitarian` - Aid, refugees, disasters, human rights
- `information_media` - Information campaigns, media narratives, propaganda
- `legal_regulatory` - Laws, regulations, international legal frameworks

## CTM Aggregation

Each CTM is a unique combination of:
- **Centroid** - The narrative anchor
- **Track** - The strategic domain
- **Month** - Calendar month (YYYY-MM-01)

All titles matching this combination are aggregated into one CTM unit.

## Output

Each title gets:
- `track` - Assigned strategic track
- `track_confidence` - Classification confidence (0.0-1.0)
- `ctm_id` - UUID of the CTM it belongs to
- `ctm_month` - Month of aggregation
- `processing_status` - Updated to 'ctm_assigned'

Each CTM record contains:
- `title_count` - Number of titles in this CTM
- `first_title_date` - Earliest title timestamp
- `last_title_date` - Latest title timestamp

## Implementation

1. Query titles with `processing_status = 'centroid_assigned'`
2. For each title, call LLM to classify track
3. Find or create CTM record for (centroid_id, track, month)
4. Link title to CTM and update counts
