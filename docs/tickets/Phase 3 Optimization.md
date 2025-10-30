 # Phase 3 Event Generation Optimization Plan
         2 +
         3 +  ## Current Architecture Analysis
         4 +
         5 +  ### Phase 3 Pipeline Flow
         6 +  ```
         7 +  1. MAP Phase: LLM incident clustering (100 titles/batch)
         8 +     ├─> Process batches in parallel (8 concurrent)
         9 +     ├─> LLM groups titles into incident clusters
        10 +     └─> Returns incident clusters
        11 +
        12 +  2. REDUCE Phase: LLM incident analysis
        13 +     ├─> For each incident cluster
        14 +     ├─> LLM analyzes to create Event
        15 +     └─> Assigns event_type, theater, strategic_purpose
        16 +
        17 +  3. Orphan Handling
        18 +     └─> Unclustered titles → single-title Events
        19 +
        20 +  4. P3.5a: Seed Validation
        21 +     ├─> For each Event's titles
        22 +     └─> LLM validates each title belongs (YES/NO micro-prompts)
        23 +
        24 +  5. Database Upsert
        25 +     └─> Save Events with ef_key for automatic merging
        26 +
        27 +  6. P3.5c: Interpretive Merging
        28 +     ├─> Find all EF pairs
        29 +     ├─> LLM compares pairs for semantic similarity
        30 +     └─> Merge duplicates
        31 +
        32 +  7. P3.5d: Splitting
        33 +     ├─> Find large Events (>threshold titles)
        34 +     ├─> LLM splits into sub-narratives
        35 +     └─> Create child Events
        36 +  ```
        37 +
        38 +  ### Current Performance Bottlenecks
        39 +
        40 +  **Problem 1: MAP Phase is Blind to Structure**
        41 +  - **Current**: LLM receives raw title text only
        42 +  - **Missing**: AAT triples, entity overlap, graph patterns
        43 +  - **Result**: LLM does expensive O(n²) semantic comparison
        44 +
        45 +  **Problem 2: P3.5c Merge is O(n²)**
        46 +  - **Current**: Checks all EF pairs (n*(n-1)/2 comparisons)
        47 +  - **Example**: 100 EFs = 4,950 pair comparisons
        48 +  - **Cost**: Each comparison is an LLM call
        49 +
        50 +  **Problem 3: No Pre-filtering Based on Mechanics**
        51 +  - **Current**: LLM looks at everything
        52 +  - **Missing**: Simple mechanical filters (entity overlap, theater match, etc.)
        53 +  - **Result**: Wasted LLM calls on obviously unrelated items
        54 +
        55 +  ---
        56 +
        57 +  ## Optimization Strategy
        58 +
        59 +  ### 🎯 Core Insight
        60 +  **Use mechanical clustering (AAT + Neo4j + entities) to reduce search space, then use LLM to validate/refine**
        61 +
        62 +  ---
        63 +
        64 +  ## Proposed Optimizations
        65 +
        66 +  ### 1. **AAT-Driven Pre-Clustering** 🚀
        67 +  **Impact**: 70-80% reduction in LLM MAP calls
        68 +
        69 +  **Current Flow:**
        70 +  ```
        71 +  100 titles → LLM → incident clusters
        72 +  ```
        73 +
        74 +  **Optimized Flow:**
        75 +  ```
        76 +  100 titles
        77 +    → AAT triple extraction (already done in P2!)
        78 +    → Mechanical clustering by (Actor, Action) patterns
        79 +    → LLM validation only for ambiguous clusters
        80 +  ```
        81 +
        82 +  **Implementation:**
        83 +  ```python
        84 +  # Phase 3 Pre-clustering
        85 +  def mechanical_cluster_by_aat(titles: List[Dict]) -> Dict[str, List[str]]:
        86 +      """
        87 +      Cluster titles by AAT pattern BEFORE LLM
        88 +
        89 +      Returns: {
        90 +          "Russia|attacks|Ukraine": [title_id1, title_id2, ...],
        91 +          "US|sanctions|China": [title_id3, title_id4, ...],
        92 +          "NO_CLEAR_ACTION": [title_id5, ...]  # Send these to LLM
        93 +      }
        94 +      """
        95 +      clusters = defaultdict(list)
        96 +
        97 +      for title in titles:
        98 +          aat = title.get('action_triple')
        99 +          if aat and aat['actor'] and aat['action']:
       100 +              # Normalize: "Russia attacks Ukraine" → "russia|attack|ukraine"
       101 +              key = f"{aat['actor'].lower()}|{aat['action'].lower()}|{aat['target'].lower() if aat['target'] else
           + 'none'}"
       102 +              clusters[key].append(title['id'])
       103 +          else:
       104 +              clusters['NO_CLEAR_ACTION'].append(title['id'])
       105 +
       106 +      return clusters
       107 +  ```
       108 +
       109 +  **Benefits:**
       110 +  - ✅ Mechanical clustering is instant (no LLM cost)
       111 +  - ✅ AAT data already extracted in Phase 2
       112 +  - ✅ Only ambiguous titles need LLM review
       113 +
       114 +  ---
       115 +
       116 +  ### 2. **Neo4j Graph-Pattern Clustering** 🕸️
       117 +  **Impact**: Find connected incident subgraphs mechanically
       118 +
       119 +  **Current**: Neo4j stores titles/entities but isn't used in MAP phase
       120 +
       121 +  **Optimized**: Use graph algorithms to find connected components
       122 +
       123 +  **Implementation:**
       124 +  ```cypher
       125 +  // Find connected subgraphs of titles sharing entities
       126 +  MATCH (t1:Title)-[:MENTIONS]->(e:Entity)<-[:MENTIONS]-(t2:Title)
       127 +  WHERE t1.gate_keep = true
       128 +    AND t2.gate_keep = true
       129 +    AND t1.event_id IS NULL
       130 +    AND t2.event_id IS NULL
       131 +    AND t1.id < t2.id  // Avoid duplicates
       132 +  WITH t1, t2, count(e) as shared_entities
       133 +  WHERE shared_entities >= 2  // Threshold: at least 2 shared entities
       134 +  RETURN t1.id as title1_id, t2.id as title2_id, shared_entities
       135 +  ```
       136 +
       137 +  **Use case:**
       138 +  1. Run graph query to find titles with shared entities
       139 +  2. Form incident clusters from connected components
       140 +  3. Only use LLM to validate/refine clusters
       141 +
       142 +  **Benefits:**
       143 +  - ✅ Graph queries are fast (milliseconds)
       144 +  - ✅ Finds structural patterns LLM might miss
       145 +  - ✅ Leverages Phase 2 entity extraction
       146 +
       147 +  ---
       148 +
       149 +  ### 3. **Entity-Based Bucketing** 🪣
       150 +  **Impact**: Reduce comparison space from O(n²) to O(k*m²) where k=buckets, m=avg titles/bucket
       151 +
       152 +  **Current Problem:**
       153 +  ```
       154 +  100 titles → LLM compares all-to-all → expensive
       155 +  ```
       156 +
       157 +  **Optimized Solution:**
       158 +  ```
       159 +  100 titles
       160 +    → Bucket by entity overlap
       161 +    → Process each bucket separately
       162 +    → Dramatically smaller comparison space
       163 +  ```
       164 +
       165 +  **Implementation:**
       166 +  ```python
       167 +  def bucket_by_entities(titles: List[Dict]) -> Dict[str, List[Dict]]:
       168 +      """
       169 +      Bucket titles by shared entities
       170 +
       171 +      Example:
       172 +      - Bucket "Russia_Ukraine": All titles mentioning both
       173 +      - Bucket "Israel_Gaza": All titles mentioning both
       174 +      - Bucket "China": All titles mentioning China only
       175 +      """
       176 +      from collections import defaultdict
       177 +
       178 +      buckets = defaultdict(list)
       179 +
       180 +      for title in titles:
       181 +          entities = title.get('entities', [])
       182 +          if not entities:
       183 +              buckets['NO_ENTITIES'].append(title)
       184 +              continue
       185 +
       186 +          # Sort entities to create consistent bucket key
       187 +          entity_key = "_".join(sorted(entities[:3]))  # Use top 3 entities
       188 +          buckets[entity_key].append(title)
       189 +
       190 +      return buckets
       191 +  ```
       192 +
       193 +  **Processing Strategy:**
       194 +  ```python
       195 +  # Instead of: MAP(100 titles) → clusters
       196 +  # Do:
       197 +  for bucket_key, bucket_titles in buckets.items():
       198 +      if len(bucket_titles) <= 5:
       199 +          # Small bucket: automatic cluster
       200 +          create_incident_cluster(bucket_titles)
       201 +      else:
       202 +          # Large bucket: use LLM to sub-cluster
       203 +          clusters = await llm_cluster_incidents(bucket_titles)
       204 +  ```
       205 +
       206 +  **Benefits:**
       207 +  - ✅ Reduces LLM input size
       208 +  - ✅ Titles in same bucket are pre-filtered for relevance
       209 +  - ✅ Can process small buckets without LLM
       210 +
       211 +  ---
       212 +
       213 +  ### 4. **P3.5c Merge Optimization: Candidate Filtering** 🎯
       214 +  **Impact**: 90%+ reduction in merge comparisons
       215 +
       216 +  **Current Problem:**
       217 +  ```
       218 +  100 Events → 4,950 pairwise LLM comparisons
       219 +  ```
       220 +
       221 +  **Optimized Solution:**
       222 +  ```
       223 +  100 Events
       224 +    → Filter to candidate pairs only (mechanical rules)
       225 +    → ~50-100 LLM comparisons
       226 +  ```
       227 +
       228 +  **Mechanical Filter Rules:**
       229 +  ```python
       230 +  def find_merge_candidates(events: List[Event]) -> List[Tuple[str, str]]:
       231 +      """
       232 +      Find Event pairs that MIGHT be duplicates
       233 +
       234 +      Only compare pairs that match ALL of:
       235 +      1. Same event_type
       236 +      2. Same primary_theater (or adjacent theaters)
       237 +      3. At least 2 shared actors
       238 +      4. Temporal overlap (events within 7 days)
       239 +      """
       240 +      candidates = []
       241 +
       242 +      for i, ef1 in enumerate(events):
       243 +          for ef2 in events[i+1:]:
       244 +              # Rule 1: Same event type
       245 +              if ef1.event_type != ef2.event_type:
       246 +                  continue
       247 +
       248 +              # Rule 2: Same/adjacent theater
       249 +              if not theaters_related(ef1.primary_theater, ef2.primary_theater):
       250 +                  continue
       251 +
       252 +              # Rule 3: Shared actors
       253 +              shared_actors = set(ef1.key_actors) & set(ef2.key_actors)
       254 +              if len(shared_actors) < 2:
       255 +                  continue
       256 +
       257 +              # Rule 4: Temporal overlap
       258 +              if not temporal_overlap(ef1.created_at, ef2.created_at, days=7):
       259 +                  continue
       260 +
       261 +              # PASSED ALL FILTERS → Candidate for LLM comparison
       262 +              candidates.append((ef1.id, ef2.id))
       263 +
       264 +      return candidates
       265 +  ```
       266 +
       267 +  **Neo4j Alternative:**
       268 +  ```cypher
       269 +  // Find Events with shared actors (graph-based)
       270 +  MATCH (ef1:Event)-[:HAS_ACTOR]->(a:Actor)<-[:HAS_ACTOR]-(ef2:Event)
       271 +  WHERE ef1.event_type = ef2.event_type
       272 +    AND ef1.primary_theater = ef2.primary_theater
       273 +    AND ef1.status IN ['seed', 'active']
       274 +    AND ef2.status IN ['seed', 'active']
       275 +    AND ef1.id < ef2.id
       276 +  WITH ef1, ef2, count(a) as shared_actors
       277 +  WHERE shared_actors >= 2
       278 +  RETURN ef1.id as ef1_id, ef2.id as ef2_id, shared_actors
       279 +  ORDER BY shared_actors DESC
       280 +  ```
       281 +
       282 +  **Benefits:**
       283 +  - ✅ From 4,950 comparisons to ~50-100
       284 +  - ✅ 98% reduction in LLM calls
       285 +  - ✅ Faster execution, lower cost
       286 +
       287 +  ---
       288 +
       289 +  ### 5. **Batch Validation Instead of Pairwise** 🚀
       290 +  **Impact**: N calls instead of N(N-1)/2 calls
       291 +
       292 +  **Current P3.5c Approach:**
       293 +  ```
       294 +  For each pair (EF1, EF2):
       295 +      LLM: "Are these the same narrative? YES/NO"
       296 +
       297 +  Example: 10 similar EFs = 45 LLM calls
       298 +  ```
       299 +
       300 +  **Optimized Approach:**
       301 +  ```
       302 +  Group similar EFs into cluster
       303 +  LLM: "Which of these EFs describe the same narrative?"
       304 +
       305 +  Example: 10 similar EFs = 1 LLM call
       306 +  ```
       307 +
       308 +  **Implementation:**
       309 +  ```python
       310 +  def batch_merge_candidates(similar_efs: List[Event]) -> List[List[str]]:
       311 +      """
       312 +      Instead of pairwise comparison, ask LLM to cluster similar EFs
       313 +
       314 +      Prompt: "Here are 10 Events about US-China tensions.
       315 +               Which ones describe the same strategic narrative?"
       316 +
       317 +      Returns: [[ef1_id, ef2_id], [ef3_id, ef4_id, ef5_id], ...]
       318 +      """
       319 +      system = """You are grouping similar Events. Events in the same group
       320 +      describe the same strategic narrative (just from different sources/angles).
       321 +
       322 +      Return JSON: [[group1_ids], [group2_ids], ...]"""
       323 +
       324 +      user = f"""Events about {similar_efs[0].event_type}:
       325 +
       326 +      {format_events_for_clustering(similar_efs)}
       327 +
       328 +      Group events that describe the SAME strategic narrative:"""
       329 +
       330 +      response = await llm_call(system, user)
       331 +      return parse_event_groups(response)
       332 +  ```
       333 +
       334 +  **Benefits:**
       335 +  - ✅ Dramatically fewer LLM calls
       336 +  - ✅ Can find multi-way merges (not just pairs)
       337 +  - ✅ Faster, cheaper, more comprehensive
       338 +
       339 +  ---
       340 +
       341 +  ## Implementation Roadmap
       342 +
       343 +  ### Phase 1: Quick Wins (Week 1)
       344 +  1. **Add entity-based bucketing to MAP phase**
       345 +     - Bucket titles by entity overlap before LLM
       346 +     - Process small buckets without LLM
       347 +     - **Impact**: 50% reduction in MAP LLM calls
       348 +
       349 +  2. **Add mechanical filters to P3.5c**
       350 +     - Filter merge candidates by event_type + theater + actors
       351 +     - Only LLM-compare filtered candidates
       352 +     - **Impact**: 90% reduction in merge LLM calls
       353 +
       354 +  ### Phase 2: AAT Integration (Week 2)
       355 +  3. **AAT-driven pre-clustering**
       356 +     - Use Phase 2 AAT triples for mechanical clustering
       357 +     - Group titles with same (Actor, Action) pattern
       358 +     - LLM only validates ambiguous clusters
       359 +     - **Impact**: 70% reduction in MAP LLM calls
       360 +
       361 +  ### Phase 3: Neo4j Graph Clustering (Week 3)
       362 +  4. **Graph-pattern incident detection**
       363 +     - Query Neo4j for connected title subgraphs
       364 +     - Form incident clusters from graph patterns
       365 +     - LLM refines/validates clusters
       366 +     - **Impact**: Better clustering quality, 30% faster
       367 +
       368 +  5. **Graph-based merge candidates**
       369 +     - Use Neo4j to find Events with shared actors
       370 +     - Replace pairwise comparison with graph query
       371 +     - **Impact**: Faster candidate discovery
       372 +
       373 +  ### Phase 4: Batch Operations (Week 4)
       374 +  6. **Batch merge validation**
       375 +     - Replace pairwise merge checks with batch clustering
       376 +     - One LLM call per similar-Event cluster
       377 +     - **Impact**: 80% reduction in merge LLM calls
       378 +
       379 +  ---
       380 +
       381 +  ## Expected Performance Gains
       382 +
       383 +  ### Current Performance (100 titles)
       384 +  - **MAP Phase**: 8-12 LLM calls (100 titles/12 ≈ 8 batches)
       385 +  - **REDUCE Phase**: ~20 LLM calls (one per incident cluster)
       386 +  - **P3.5a Validation**: ~100 LLM calls (one per title)
       387 +  - **P3.5c Merge**: ~200 LLM calls (pairwise comparisons)
       388 +  - **Total**: ~330 LLM calls
       389 +  - **Time**: 3-4 minutes
       390 +
       391 +  ### Optimized Performance (100 titles)
       392 +  - **Pre-clustering (AAT + entities)**: 0 LLM calls (mechanical)
       393 +  - **MAP Phase**: 2-3 LLM calls (only ambiguous clusters)
       394 +  - **REDUCE Phase**: ~20 LLM calls (same)
       395 +  - **P3.5a Validation**: ~100 LLM calls (same, but could optimize with batch validation)
       396 +  - **P3.5c Merge**: ~10 LLM calls (filtered candidates + batch validation)
       397 +  - **Total**: ~135 LLM calls
       398 +  - **Time**: 1-1.5 minutes
       399 +
       400 +  ### Performance Improvement
       401 +  - **LLM Calls**: 330 → 135 (60% reduction)
       402 +  - **Time**: 3-4 min → 1-1.5 min (60% faster)
       403 +  - **Cost**: 60% reduction
       404 +  - **Quality**: Same or better (more structured clustering)
       405 +
       406 +  ---
       407 +
       408 +  ## Next Steps
       409 +
       410 +  1. **Review this plan** - Validate optimization priorities
       411 +  2. **Implement Phase 1** - Entity bucketing + merge filtering (quick wins)
       412 +  3. **Test and measure** - Compare performance before/after
       413 +  4. **Iterate** - Add AAT and Neo4j optimizations incrementally
       414 +
       415 +  ---
       416 +
       417 +  ## Questions to Address
       418 +
       419 +  1. **AAT Triple Quality**: How accurate are Phase 2 AAT extractions? Need threshold?
       420 +  2. **Entity Bucketing Threshold**: How many shared entities = same bucket?
       421 +  3. **Merge Candidate Filters**: Should we loosen/tighten filter rules?
       422 +  4. **Neo4j Schema**: Do we need additional graph relationships for clustering?
       423 +  5. **Batch Size Limits**: What's optimal batch size for cluster validation?

Answers: 
1. **AAT Triple Quality** is far from perfect. For some titles it works very well, for others less so. It's a "helper", not a 100% solid solution.
2. **Entity Bucketing Threshold** - again it's hard to tell. [Trump, Russia] and [Trump, Putin, Ukraine] works. But in other cases you might want exact match. Also a lot of titles won't have clear merging markers.
3. **Merge Candidate Filters** - we rebuild the system, let's not change everything at once. We will see later.
4. **Neo4j Schema** - Do we need additional graph relationships for clustering? - a question to you. I have no idea how these graphs work. We hope to improve "mechanical logic" without LLM.
5. **Batch Size Limits** - depends on mechanism. The bigger clusters are, the better to reduce framentation and cross-batch merging. But performance!

My comments to the plan:
1. Can we combine all three mechanisms together? Use a combination of entities matching (say, 50% of entities should match), triplets match (actor|action|target) [it's hard to expect "action" to match because it's a verb - can be any...], graphs from Nep4j === we want some reasonable and realistic matching to cluster the majority of titles before we run LLM check.
