# SNI v3 Pipeline

This directory contains the SNI v3 pipeline implementation, which uses centroid-based architecture and CTM (Centroid-Track-Month) aggregation units.

## Architecture

SNI v3 replaces the vocabulary-based gating system with mechanical centroid matching:

- **Phase 1**: Title ingestion and cleaning (reuses v2 implementation)
- **Phase 2**: 3-pass centroid matching (geographic -> systemic -> superpower)
- **Phase 3**: Track classification and CTM building

## Directory Structure

- `phase_1/` - Title ingestion and cleaning
- `phase_2/` - Centroid matching logic
- `phase_3/` - Track classification and CTM building
- `shared/` - Common utilities and helpers

## Database Tables

- `centroids_v3` - Stable narrative anchors
- `taxonomy_v3` - Unified lookup table for entities, keywords, institutions
- `ctm` - Centroid-Track-Month aggregation units
- `titles_v3` - Simplified title table with centroid/track/CTM linkage

## Documentation

See `/docs/tickets/SNI_v3_Design.md` for complete architectural specification.
