# FILTERS AND THRESHOLDS
**Strategic Narrative Intelligence - Production Parameters**

**Scope**: CLUST-1 & CLUST-2 + Feed Ingestion (current MVP phase)  
**Last Updated**: 2025-08-04  
**Status**: Production Ready (post comprehensive testing)

---

## 0. RSS Ingestion / Feed Handling

### Feeds Used (Production)
- **Count**: 18+ geopolitical news RSS feeds  
- **Sources**: Western + Russian + Chinese + Middle Eastern  
- **Examples**: BBC, Reuters, TASS, Kremlin, Al Jazeera, Xinhua, etc.
- **Configuration**: `news_feeds_config.json` + database `news_feeds` table
- **Geographic Restrictions**: RT, RIA Novosti, Sputnik blocked in Germany

### Batch Limits
- **Current Production**: `25 articles/feed/run` 
- **Rationale**: Balanced ingestion without overwhelming DeepSeek API limits
- **Override**: `--limit` parameter available for testing/catchup runs

### Filtering at Ingestion
- **Thematic Filtering**: ❌ None (sports, entertainment still ingested)
- **Rationale**: Preserve semantic clustering purity; filter later in CLUST-2
- **Deduplication**: ✅ Enabled (URL + content hash check)
- **Quality Filters**: Min 5 words, max 10,000 words

---

## 1. CLUST-1 Semantic Clustering
**Purpose**: Group articles into broad thematic clusters without interpretive bias

### Algorithm & Model
- **Embedding Model**: `all-MiniLM-L6-v2` (HuggingFace sentence-transformers)
- **Clustering Method**: DBSCAN (density-based)
- **Vector Dimensions**: 384

### Core Parameters
```python
dbscan_eps = 0.35                 # Distance threshold (was inconsistent 0.3-0.5)
dbscan_min_samples = 3            # Min articles per cluster (was inconsistent 2-3)
min_cluster_size = 3              # Minimum meaningful cluster size
max_cluster_size = 100            # Prevent mega-clusters
```

### Batch Processing Modes
1. **Time-Window Mode** (Production Default)
   - `time_window_hours = 72`     # 3-day rolling window
   - `batch_size = 200`           # Articles per processing batch

2. **Full-Corpus Mode** (Testing/Research)
   - `time_window_hours = 168`    # 1-week window 
   - `batch_size = None`          # Process all articles together
   - **Results**: 4X better clustering rate (21.3% vs 5.2%)

### Entity Boosting
- **NER Extraction**: SpaCy English model (`en_core_web_sm`)
- **Boosted Types**: PERSON, ORG, LOC (Named entities)
- **Boost Factor**: `entity_boost_factor = 0.2`
- **Purpose**: Improve thematic grouping around key actors/locations

---

## 2. Strategic vs Non-Strategic Classification
**Purpose**: Filter clusters before expensive CLUST-2 narrative segmentation

### Implementation
- **Method**: DeepSeek LLM prompt-based classification
- **Integration**: Built into CLUST-2 (first step of processing)
- **Database Field**: `article_clusters.strategic_status` ENUM

### Classification Categories

#### STRATEGIC (Proceed to Narrative Segmentation)
- Geopolitical topics (wars, diplomacy, sanctions)
- Government actions & policy
- Security & intelligence topics  
- Major societal movements (protests, cultural wars)
- Economic/trade disputes with political implications
- Energy policy & security (oil/gas geopolitics, renewable transitions, pipeline politics, energy independence, OPEC decisions)
- Technological rivalry & strategic tech developments (AI, quantum computing, nuclear power, semiconductors, autonomous vehicles, robotics, space technology)
- **Special Case**: Weaponized sports/entertainment (Olympic boycotts, celebrity political activism)

#### NON-STRATEGIC (Skip to 'discarded' status)
- Regular sports matches/scores/results (cricket, football, tennis, etc.)
- Celebrity gossip & entertainment awards
- Lifestyle trends & local curiosities
- **Key Rule**: Sports between countries are still just sports unless explicit political/diplomatic implications

### Quality Control
- **Manual Review**: Sports misclassification identified and corrected during testing
- **Prompt Calibration**: Enhanced specificity for sports filtering (Aug 2025)

---

## 3. CLUST-2 Breadth Validation  
**Purpose**: Prevent over-segmentation; ensure meaningful narrative diversity

### Validation Thresholds
```python
min_articles_for_segmentation = 4    # Minimum cluster size for parent/child split
min_actors_for_segmentation = 2      # Unique PERSON/ORG entities required
min_source_diversity = 2             # Different source countries required
```

### Tension Detection
- **Keywords**: `['critics', 'supporters', 'controversy', 'debate', 'dispute', 'accuse', 'allegedly', 'blame', 'praise', 'condemn', 'defend']`
- **Requirement**: ≥1 tension indicator for parent/child segmentation
- **Fallback**: Create single narrative if validation fails

### Child Narrative Requirements
```python
min_article_percentage = 0.05        # Each child must represent ≥5% of articles
min_source_count = 2                 # Each child must have ≥2 source countries
max_child_narratives = 4             # Maximum competing narratives
min_child_narratives = 2             # Minimum for parent/child structure
```

---

## 4. CLUST-2 Narrative Segmentation
**Purpose**: Create parent/child narrative hierarchies with competing interpretations

### DeepSeek LLM Configuration
```python
model_name = 'deepseek-chat'         # DeepSeek's flagship model
max_tokens = 2000                    # Response length limit
temperature = 0.3                    # Lower = more consistent/focused
```

### Narrative Structure
- **Parent Narrative**: Broad thematic frame (e.g., "Energy Independence as Security")
- **Child Narratives**: 2-4 competing interpretations (e.g., "Green Autonomy," "Fossil Pragmatism")

### Divergence Categories
1. **Causal** - Different explanations of events
2. **Moral** - Different ethical evaluations  
3. **Strategic** - Different goal framings
4. **Identity** - Different group identity framings
5. **Tone** - Different emotional/evaluative tones

### Tone Classification
- **Vocabulary**: `['propagandistic', 'skeptical', 'celebratory', 'alarmist', 'neutral', 'condemnatory']`
- **Assignment**: DeepSeek LLM selects most appropriate tone per narrative

### Database Integration
- **Parent ID**: Canonical UUID-based parent_id for hierarchical structure
- **NSF-1 Compliance**: All narratives follow NSF-1 specification format
- **Metrics Tracking**: Start/end dates, confidence scores, article associations

---

## 5. System Performance Benchmarks

### CLUST-1 Clustering Effectiveness
- **Batch Processing**: 5.2% clustering rate (baseline)
- **Full-Corpus Processing**: 21.3% clustering rate (**4X improvement**)
- **Noise Articles**: ~78.7% classified as noise (expected for news diversity)

### CLUST-2 Strategic Classification  
- **Strategic Rate**: ~12.8% of clusters deemed strategic
- **Processing Success**: >95% of strategic clusters successfully segmented
- **Quality Control**: Sports misclassification <5% (post-calibration)

### API & Resource Limits
- **DeepSeek API**: ~45-60 seconds per cluster (strategic ones)
- **Concurrency**: Single-threaded for API stability
- **Memory**: ~2GB peak for 1,300+ article corpus processing

---

## 6. Configuration Files & Override Points

### Primary Configuration
- **CLUST-1**: `production_clust1.py` config dict
- **CLUST-2**: `test_clust2.py` config dict  
- **RSS Ingestion**: `rss_ingestion.py` + `news_feeds_config.json`

### Runtime Overrides
```bash
# RSS Ingestion
python rss_ingestion.py --limit 50 --verbose

# CLUST-1 Processing  
python production_clust1.py --limit 500 --config custom_config.json

# CLUST-2 Processing
python test_clust2.py  # Processes all pending clusters
```

### Environment Variables
```bash
DEEPSEEK_API_KEY=sk-xxx                    # Required for CLUST-2
DB_HOST=localhost                          # Database connection
DB_NAME=narrative_intelligence             # Database name
PYTHONIOENCODING=utf-8                     # Windows Unicode fix
```

---

## 7. Quality Assurance & Testing

### Validation Completed (Aug 2025)
- ✅ **End-to-End Pipeline**: 1,300+ articles processed successfully
- ✅ **Cross-Batch Clustering**: Proven 4X improvement over time-window approach  
- ✅ **Strategic Classification**: Sports filtering calibrated and validated
- ✅ **Narrative Quality**: Parent/child hierarchies generating meaningful competing perspectives
- ✅ **Database Integration**: Full CRUD operations with proper foreign key relationships

### Known Issues & Mitigations
- **Geographic Blocking**: Russian sources (RT, RIA) blocked in Germany - use VPN/proxy for full coverage
- **Unicode Encoding**: Windows console issues - `PYTHONIOENCODING=utf-8` env var required
- **API Rate Limits**: DeepSeek processing time ~1 minute per cluster - scale horizontally if needed

---

**System Status**: Production Ready  
**Next Phase**: Operational deployment & monitoring setup