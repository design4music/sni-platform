# Performance Optimization Plan
*Based on full corpus processing analysis*

## Critical Performance Issues

### 1. API Reliability (Priority: Critical)
**Current State**: 50% batch failure rate due to LLM API issues
**Impact**: Processing efficiency severely limited

**Immediate Actions:**
- Implement exponential backoff retry logic for failed LLM calls
- Add circuit breaker pattern for API health monitoring
- Create fallback to smaller batch sizes on repeated failures
- Add comprehensive error logging for API failure analysis

**Code Changes Needed:**
```python
# apps/gen1/llm_client.py
async def _call_llm_with_retry(self, messages, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await self._call_llm(messages)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### 2. Processing Efficiency (Priority: High)
**Current State**: 2.2% of strategic titles assigned to Event Families
**Target**: >15% assignment rate for meaningful processing

**Scope Calibration Adjustments:**
- Lower coherence thresholds in LLM prompts from 0.9+ to 0.7+
- Reduce minimum title requirements for EF creation from 5+ to 3+
- Allow more diverse actor sets within Event Families
- Implement graduated processing (strict → relaxed thresholds)

**Batch Size Optimization:**
- Reduce from 1000 to 500 titles per batch for better LLM handling
- Implement adaptive batch sizing based on success rates
- Add small batch fallback (50-100 titles) for failed large batches

### 3. Theater Classification Accuracy (Priority: Medium)
**Current Issue**: Indonesia classified as LATAM_REGIONAL

**Fixes Needed:**
- Update theater classification logic in `apps/gen1/llm_client.py`
- Add validation rules for geographic consistency
- Create theater-specific actor validation

## Performance Benchmarks & Targets

### Current Metrics (Baseline)
- **Batch Success Rate**: 37.5%
- **Title Assignment Rate**: 2.2%
- **Processing Time**: ~25 minutes for 7,483 titles
- **EF Creation Rate**: 17 EFs from 7,483 titles (0.2%)
- **Merge Success Rate**: 6 merges from 29 total EFs (20.7%)

### Target Metrics (3-Month Goal)
- **Batch Success Rate**: >90%
- **Title Assignment Rate**: >15%
- **Processing Time**: <15 minutes for 7,500 titles
- **EF Creation Rate**: >1.5% (100+ EFs from 7,500 titles)
- **Merge Success Rate**: >30%

## Implementation Roadmap

### Phase 1: Reliability (Week 1-2)
1. **API Resilience**
   - Implement retry logic with exponential backoff
   - Add circuit breaker for API health monitoring
   - Create comprehensive error logging

2. **Batch Processing Improvements**
   - Reduce batch sizes to 500 titles
   - Add fallback to smaller batches on failures
   - Implement batch progress tracking

### Phase 2: Efficiency (Week 3-4)
1. **Scope Calibration**
   - Lower LLM coherence thresholds
   - Reduce minimum title requirements for EF creation
   - Test graduated processing approach

2. **Performance Monitoring**
   - Add real-time metrics dashboard
   - Implement automated performance alerts
   - Create daily processing reports

### Phase 3: Optimization (Week 5-8)
1. **Advanced Features**
   - Implement parallel batch processing
   - Add intelligent batch composition
   - Create predictive EF formation

2. **Quality Improvements**
   - Enhanced theater classification validation
   - Improved actor normalization
   - Better merging decision algorithms

## Monitoring and Alerting

### Key Performance Indicators (KPIs)
1. **Reliability Metrics**
   - API success rate (target: >95%)
   - Batch completion rate (target: >90%)
   - Error rate by error type

2. **Efficiency Metrics**
   - Title assignment rate (target: >15%)
   - EF creation rate (target: >1.5%)
   - Processing throughput (titles/minute)

3. **Quality Metrics**
   - Theater classification accuracy (target: >95%)
   - Merge decision accuracy (manual review sample)
   - EF coherence scores (LLM-generated)

### Automated Alerts
- Batch failure rate >20% (immediate alert)
- Assignment rate <5% for daily runs (warning)
- Processing time >30 minutes for full corpus (warning)
- API error rate >10% (immediate alert)

## Risk Mitigation

### API Dependency Risks
- **Backup LLM Provider**: Prepare integration with secondary API (e.g., OpenAI)
- **Graceful Degradation**: Continue processing with reduced functionality
- **Local Fallback**: Basic rule-based EF creation for critical operations

### Data Quality Risks
- **Validation Pipelines**: Automated data quality checks
- **Manual Review Samples**: Regular quality audits
- **Rollback Procedures**: Ability to revert problematic processing runs

### Performance Risks
- **Load Testing**: Regular stress testing with full corpus
- **Capacity Planning**: Monitor resource usage trends
- **Scaling Strategy**: Horizontal scaling approach for high-volume periods

## Success Criteria

### Technical Success
- Achieve >90% batch success rate consistently
- Process full corpus (7,500+ titles) in <15 minutes
- Maintain >15% title assignment rate
- Zero critical data integrity issues

### Business Success
- Enable daily automated processing without manual intervention
- Provide reliable metrics for strategic content analysis
- Support real-time Event Family monitoring and alerts
- Demonstrate clear ROI through improved content organization

## Next Steps

1. **Immediate (This Week)**
   - Implement basic retry logic for API calls
   - Reduce batch sizes to 500 titles
   - Fix Indonesia theater classification

2. **Short-term (Next 2 Weeks)**
   - Deploy comprehensive error handling
   - Implement batch fallback strategies
   - Add performance monitoring dashboard

3. **Medium-term (Next Month)**
   - Complete scope calibration adjustments
   - Deploy parallel processing capabilities
   - Implement automated quality validation

This optimization plan provides a clear path to transform the current 2.2% processing efficiency into a robust, reliable system capable of handling the full strategic content corpus with high reliability and quality.