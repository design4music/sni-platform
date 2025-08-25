# Manual Parent Narrative Curation Workflow Design
**Strategic Narrative Intelligence Platform**
**Date: August 18, 2025**

## Executive Summary

This document outlines a comprehensive manual curation workflow designed to address the strategic narrative granularity issues identified in SNI analytics:

**Current State**: 5 parents for 17 final clusters (0.29 ratio) - insufficient strategic consolidation
**Target State**: Efficient creation of strategic parent narratives that consolidate thematic clusters
**Solution**: Multi-stage workflow integrating automated triggers with human editorial oversight

---

## 1. CURATION TRIGGER WORKFLOW

### 1.1 Automated Trigger System

**Trigger Conditions:**
- **Thematic Density**: ≥3 clusters sharing 2+ core keywords within 7 days
- **Temporal Clustering**: ≥5 clusters in same theme within 48-hour window
- **Source Diversity**: Single theme appearing across ≥4 different news sources
- **Strategic Keywords**: Clusters containing high-priority terms (russia, china, ukraine, etc.)
- **Volume Threshold**: Theme generating >20 articles across multiple clusters

**Implementation Pattern:**
```python
# Daily trigger analysis after CLUST-1 completion
def analyze_curation_triggers():
    triggers = []
    
    # Thematic density analysis
    thematic_groups = identify_keyword_overlaps(min_clusters=3, min_shared_keywords=2)
    for group in thematic_groups:
        if group['strategic_score'] > 0.7:
            triggers.append(create_trigger('thematic_density', group))
    
    # Temporal clustering analysis  
    temporal_groups = identify_temporal_clusters(window_hours=48, min_clusters=5)
    for group in temporal_groups:
        if group['source_diversity'] >= 4:
            triggers.append(create_trigger('temporal_clustering', group))
    
    return prioritize_triggers(triggers)
```

### 1.2 Manual Identification Process

**Curator Dashboard Features:**
- **Theme Explorer**: Visual clustering of related narratives by keyword overlap
- **Temporal Timeline**: Chronological view of narrative emergence patterns
- **Strategic Radar**: High-priority themes requiring consolidation
- **Orphan Monitor**: Parent-worthy narratives without strategic grouping

**Daily Workflow:**
1. **Morning Briefing** (15 min): Review overnight trigger suggestions
2. **Theme Analysis** (30 min): Evaluate thematic grouping opportunities  
3. **Strategic Assessment** (20 min): Identify high-impact consolidation candidates
4. **Creation Queue** (10 min): Prioritize manual parent narrative creation

---

## 2. STRATEGIC PARENT CREATION PROCESS

### 2.1 Creation Workflow Stages

**Stage 1: Strategic Assessment**
- **Scope Definition**: Identify theme boundaries and temporal span
- **Impact Analysis**: Assess geopolitical significance and audience relevance
- **Consolidation Value**: Evaluate narrative coherence gains from grouping
- **Resource Estimation**: Determine curation effort required

**Stage 2: Content Assembly**
- **Cluster Selection**: Choose 3-8 related CLUST-1/CLUST-2 clusters
- **Narrative Synthesis**: Create cohesive strategic storyline from fragments
- **Framing Analysis**: Ensure strategic (not tactical/operational) focus
- **Quality Validation**: Verify narrative meets strategic criteria

**Stage 3: Editorial Refinement**
- **Title Optimization**: Strategic arc framing (not journalistic headline)
- **Summary Crafting**: 2-3 neutral sentences outlining scope and significance
- **Metadata Assignment**: Priority level, review deadline, keyword tags
- **Integration Planning**: Identify child narratives for assignment

### 2.2 Quality Gates

**Strategic Validation Checklist:**
- [ ] Addresses geopolitical, policy, or security themes
- [ ] Spans multiple events/actors beyond single incident
- [ ] Provides strategic context missing from individual clusters
- [ ] Appeals to policy/intelligence audience (not news consumers)
- [ ] Maintains temporal coherence (events logically connected)
- [ ] Demonstrates cross-source validation

**Technical Validation:**
- [ ] Parent narrative UUID generated correctly
- [ ] Curation status set to 'manual_draft'
- [ ] Curator assignment recorded
- [ ] Manual cluster IDs populated
- [ ] Audit trail entry created

### 2.3 Creation Interface

**Proposed UI Components:**
```
┌─────────────────────────────────────────────────┐
│ CREATE STRATEGIC PARENT NARRATIVE               │
├─────────────────────────────────────────────────┤
│ Title: [Strategic arc framing (not headline)]   │
│ Summary: [2-3 sentences, strategic scope]      │  
│ Theme Keywords: [russia, sanctions, energy]    │
│ Priority: [High ▼] Deadline: [Aug 25 ▼]       │
│                                                 │
│ CLUSTER SELECTION (3 selected)                 │
│ ☑ Russia Energy Weaponization (12 articles)   │
│ ☑ European Gas Crisis Response (8 articles)    │
│ ☑ Alternative Supply Chain Development (5 art.) │
│ ☐ Sanctions Enforcement Mechanisms (15 art.)   │
│                                                 │
│ Strategic Significance:                         │
│ [Demonstrates Russia's systematic use of...]    │
│                                                 │
│ [Save Draft] [Submit for Review] [Cancel]      │
└─────────────────────────────────────────────────┘
```

---

## 3. CLUSTER GROUPING WORKFLOW

### 3.1 Thematic Consolidation Process

**Phase 1: Theme Identification**
- **Keyword Analysis**: Identify shared strategic terms across clusters
- **Temporal Correlation**: Group clusters emerging within strategic timeframes
- **Actor Mapping**: Consolidate clusters involving same geopolitical actors
- **Policy Coherence**: Group clusters affecting same policy domain

**Phase 2: Consolidation Validation**
- **Strategic Coherence**: Ensure grouping creates meaningful strategic narrative
- **Temporal Logic**: Verify events form coherent chronological sequence  
- **Source Validation**: Confirm cross-source reporting supports grouping
- **Impact Assessment**: Evaluate strategic significance of consolidated narrative

**Phase 3: Implementation**
- **Parent Creation**: Generate strategic parent narrative
- **Child Assignment**: Link existing clusters as child narratives
- **Metadata Sync**: Propagate strategic tags and classifications
- **Review Queue**: Schedule editorial validation

### 3.2 Grouping Criteria Matrix

| Criteria | Weight | Threshold | Description |
|----------|---------|-----------|-------------|
| **Keyword Overlap** | 25% | ≥2 shared strategic terms | Common thematic elements |
| **Temporal Proximity** | 20% | ≤7 days between clusters | Event chronological coherence |
| **Actor Consistency** | 25% | ≥1 shared major actor | Geopolitical entity involvement |
| **Strategic Significance** | 20% | Score ≥0.7 | Policy/security relevance |
| **Source Diversity** | 10% | ≥3 different sources | Cross-validation confidence |

**Grouping Algorithm:**
```python
def evaluate_cluster_grouping(cluster_set):
    score = 0
    score += keyword_overlap_score(cluster_set) * 0.25
    score += temporal_proximity_score(cluster_set) * 0.20  
    score += actor_consistency_score(cluster_set) * 0.25
    score += strategic_significance_score(cluster_set) * 0.20
    score += source_diversity_score(cluster_set) * 0.10
    
    return score >= 0.65  # Consolidation threshold
```

### 3.3 Special Grouping Scenarios

**Russia/Putin Theme (74% of content)**
- **Approach**: Create 3-4 strategic parents instead of 11 separate clusters
- **Suggested Groupings**:
  - "Russia Strategic Energy Weaponization" (energy, sanctions clusters)
  - "Russia Military Doctrine Evolution" (military, security clusters)  
  - "Russia Diplomatic Realignment" (diplomacy, alliance clusters)

**Ukraine Conflict Theme (8% of content)**  
- **Approach**: Temporal and operational consolidation
- **Suggested Groupings**:
  - "Ukraine Defense Capabilities Development" 
  - "International Ukraine Support Evolution"

**China Relations Theme (6% of content)**
- **Approach**: Policy domain consolidation
- **Suggested Groupings**:
  - "US-China Technology Competition"
  - "China Global Infrastructure Influence"

---

## 4. EDITORIAL REVIEW PROCESS

### 4.1 Review Workflow States

**Status Progression:**
```
manual_draft → pending_review → reviewed → approved → published
     ↑              ↓             ↓          ↓          ↓
     └─────── needs_revision ←────┴─────────┴──────────┘
```

**Review Criteria:**
- **Strategic Focus**: Validates geopolitical/policy significance
- **Narrative Coherence**: Ensures logical thematic flow
- **Factual Accuracy**: Verifies claims against source material
- **Editorial Standards**: Confirms title/summary quality
- **Integration Quality**: Reviews child narrative assignments

### 4.2 Review Assignment Logic

**Automatic Assignment Rules:**
- **High Priority** (1-2): Senior Editor + Subject Matter Expert
- **Medium Priority** (3): Senior Editor OR Subject Matter Expert  
- **Low Priority** (4-5): Junior Editor with Senior oversight

**Workload Balancing:**
- Maximum 5 pending reviews per reviewer
- Deadline-based prioritization (overdue items first)
- Expertise matching (Russia expert for Russia themes)

### 4.3 Review Interface

**Reviewer Dashboard:**
```
┌─────────────────────────────────────────────────┐
│ EDITORIAL REVIEW QUEUE                          │
├─────────────────────────────────────────────────┤
│ 🔴 Russia Energy Strategy (OVERDUE - 2 days)   │ 
│ 🟡 China Tech Competition (Due Today)          │
│ 🟢 Ukraine Support Evolution (3 days remain)   │
│                                                 │ 
│ NARRATIVE: Russia Energy Strategy               │
│ Title: [Russia leverages energy exports for... ] │
│ Summary: [Putin administration systematically...] │
│ Clusters: 4 selected | Articles: 28 total      │
│                                                 │
│ REVIEW CHECKLIST                                │
│ ☑ Strategic significance validated              │
│ ☑ Narrative coherence confirmed                │
│ ☐ Factual accuracy verified                    │
│ ☐ Editorial standards met                      │
│                                                 │
│ Review Notes: [Title needs refinement for...]  │
│                                                 │
│ [Approve] [Request Revision] [Reject]          │
└─────────────────────────────────────────────────┘
```

---

## 5. INTEGRATION OPTIMIZATION

### 5.1 Pipeline Integration Points

**CLUST-1 Integration:**
- **Output Monitoring**: Analyze cluster formation for grouping opportunities
- **Metadata Inheritance**: Transfer strategic keywords and confidence scores
- **Quality Signals**: Use CLUST-1 coherence metrics for grouping decisions

**CLUST-2 Integration:**
- **Narrative Harvesting**: Identify auto-generated narratives for consolidation
- **Parent-Child Mapping**: Preserve existing narrative relationships
- **Confidence Propagation**: Maintain LLM-generated quality assessments

**API Integration:**
- **Real-time Updates**: Push new parent narratives to API immediately
- **Dashboard Sync**: Update curation dashboard with status changes
- **Search Integration**: Index manual narratives for discovery

### 5.2 Performance Optimization

**Database Optimization:**
- **Index Strategy**: Leverage existing curation workflow indexes
- **Query Optimization**: Use materialized views for dashboard queries
- **Batch Operations**: Group related database updates for efficiency

**Workflow Optimization:**
- **Parallel Processing**: Allow multiple curators simultaneous work
- **Smart Caching**: Cache cluster analysis results for grouping decisions
- **Incremental Updates**: Only reprocess changed clusters

### 5.3 Error Handling

**Graceful Degradation:**
- **Trigger Failures**: Continue manual identification if automation fails
- **Database Issues**: Maintain local draft state during connectivity issues  
- **Review Bottlenecks**: Auto-escalate overdue items to senior staff

**Recovery Procedures:**
- **Audit Trail**: Full rollback capability using curation log
- **Status Recovery**: Automatic status correction for workflow violations
- **Data Integrity**: Validation functions prevent orphaned narratives

---

## 6. WORKFLOW PERFORMANCE METRICS

### 6.1 Efficiency Metrics

**Throughput Indicators:**
- **Creation Rate**: Parent narratives created per curator-day
- **Consolidation Ratio**: Clusters grouped per parent narrative
- **Time-to-Publication**: Hours from draft to published status
- **Review Throughput**: Reviews completed per reviewer-day

**Quality Indicators:**
- **Strategic Coherence Score**: LLM-evaluated narrative quality
- **Child Assignment Rate**: Percentage of children successfully linked
- **Revision Rate**: Percentage of drafts requiring rework
- **Publication Success**: Approved narratives reaching publication

### 6.2 Target Performance

**Daily Operation Goals:**
- **15-20 new clusters processed** → 3-5 strategic parents created
- **Review turnaround**: <24 hours for high priority items
- **Consolidation rate**: 4-6 clusters per strategic parent
- **Quality threshold**: >85% first-pass approval rate

**Scalability Targets:**
- **Curator Capacity**: 8-12 strategic parents per curator per day
- **Review Capacity**: 12-15 reviews per reviewer per day  
- **System Response**: <2 seconds for dashboard updates
- **Integration Latency**: <30 seconds from creation to API availability

---

## 7. USER INTERFACE REQUIREMENTS

### 7.1 Curator Dashboard

**Essential Features:**
- **Trigger Monitor**: Real-time display of consolidation opportunities
- **Theme Explorer**: Visual clustering interface for thematic analysis
- **Creation Wizard**: Step-by-step parent narrative creation
- **Progress Tracking**: Status overview of curated narratives
- **Performance Analytics**: Personal productivity metrics

**Advanced Features:**
- **AI Suggestions**: ML-powered grouping recommendations
- **Collaboration Tools**: Multi-curator narrative development
- **Template Library**: Pre-configured narrative structures
- **Batch Operations**: Bulk cluster assignment capabilities

### 7.2 Review Interface

**Core Components:**
- **Review Queue**: Prioritized list of pending narratives
- **Narrative Validator**: Side-by-side original vs. consolidated view
- **Quality Checklist**: Standardized review criteria
- **Collaborative Annotation**: Comments and suggestions system
- **Decision Tools**: Approve/revise/reject with detailed feedback

### 7.3 Management Dashboard

**Executive Overview:**
- **Workflow Health**: System status and bottleneck identification
- **Performance Metrics**: Team productivity and quality statistics
- **Strategic Impact**: Narrative consolidation effectiveness
- **Resource Planning**: Capacity utilization and scaling needs

---

## 8. IMPLEMENTATION ROADMAP

### Phase 1: Core Infrastructure (Week 1-2)
- [x] Database schema enhancements (completed)
- [x] ManualNarrativeManager class (completed)  
- [ ] Trigger analysis system implementation
- [ ] Basic curator dashboard development

### Phase 2: Workflow Integration (Week 3-4)
- [ ] CLUST-1/CLUST-2 pipeline integration
- [ ] Automated grouping recommendation engine
- [ ] Review workflow implementation
- [ ] API endpoint integration

### Phase 3: Advanced Features (Week 5-6)
- [ ] AI-powered consolidation suggestions
- [ ] Advanced analytics and reporting
- [ ] Performance optimization
- [ ] Load testing and scaling

### Phase 4: Production Deployment (Week 7-8)
- [ ] User training and documentation
- [ ] Production deployment
- [ ] Monitoring and alerting setup
- [ ] Continuous improvement framework

---

## 9. SUCCESS CRITERIA

**Quantitative Goals:**
- **Parent/Cluster Ratio**: Increase from 0.29 to 0.40-0.60
- **Strategic Coverage**: Maintain 95%+ strategic theme coverage
- **Processing Efficiency**: Handle 15-20 daily clusters with 3-5 strategic parents
- **Quality Metrics**: Achieve >85% first-pass review approval rate

**Qualitative Goals:**
- **Strategic Focus**: Eliminate tactical/operational narrative fragmentation
- **Editorial Quality**: Consistent strategic narrative standards
- **User Experience**: Intuitive workflow reducing curator cognitive load
- **System Integration**: Seamless pipeline integration without disruption

**Business Impact:**
- **Intelligence Value**: Higher-quality strategic narratives for policy audience
- **Operational Efficiency**: Reduced manual effort through intelligent automation
- **Scalability**: System handles growing content volume without proportional staff increases
- **Competitive Advantage**: Superior narrative consolidation vs existing intelligence platforms

---

This workflow design addresses the core challenge of strategic narrative granularity while leveraging the excellent technical foundation already built in the SNI platform. The multi-stage approach ensures quality while maintaining operational efficiency at scale.