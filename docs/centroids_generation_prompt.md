# Geopolitical Centroids Generation Prompt

## Prompt for LLM Testing

```
You are a strategic intelligence analyst tasked with identifying the core "centroids" - the fundamental geopolitical entities, themes, and forces that shape current global events and narratives.

Your task is to generate 25-30 centroids that would help categorize and connect news events in a global monitoring system. Each centroid should be:

1. **Persistent** - Relevant across months/years, not just current events
2. **Connective** - Capable of linking multiple disparate news stories
3. **Analytically Valuable** - Provides insight beyond simple keyword matching

For each centroid, provide:
- **Name**: Clear, concise identifier
- **Category**: One of: ACTOR, THEME, THEATER, SYSTEM
- **Description**: 1-2 sentences explaining its significance
- **Keywords**: 8-12 terms/phrases for matching news content
- **Relationships**: 2-3 other centroids it commonly intersects with

## Categories Defined:
- **ACTOR**: Geopolitical entities (nations, blocs, organizations)
- **THEME**: Cross-cutting issues (technology, environment, economics)  
- **THEATER**: Geographic regions of persistent strategic importance
- **SYSTEM**: Structural forces shaping global order

## Output Format:
```json
{
  "centroids": [
    {
      "name": "US-China Strategic Competition",
      "category": "ACTOR",
      "description": "The defining great power rivalry of the 21st century, encompassing trade, technology, military, and ideological dimensions.",
      "keywords": ["US-China relations", "strategic competition", "trade war", "tech rivalry", "Taiwan", "South China Sea", "decoupling", "supply chain", "semiconductors", "military buildup", "Belt and Road", "democracy vs authoritarianism"],
      "relationships": ["Indo-Pacific Theater", "Semiconductor Competition", "Global Supply Chains"]
    }
  ]
}
```

Generate centroids that would help identify connections between headlines like:
- "China announces new semiconductor investment fund"
- "US strengthens ties with Philippines amid South China Sea tensions" 
- "Taiwan reports increased Chinese military flights"
- "European companies reassess China supply chains"

Focus on entities/themes that appear repeatedly in international news and help explain the deeper patterns behind surface events.
```

## Testing Instructions

Test this prompt with:
1. **Claude 3.5 Sonnet** - Should provide sophisticated geopolitical analysis
2. **GPT-4** - Good at structured output and comprehensive coverage
3. **DeepSeek** - May offer different perspective, especially on Asian affairs

Compare results on:
- **Coverage breadth** - Do they capture major global forces?
- **Analytical depth** - Are descriptions insightful vs generic?
- **Keyword quality** - Would these actually match news content?
- **Relationship mapping** - Do the connections make strategic sense?

## Evaluation Criteria

**High Quality Centroids:**
- Connect 3+ disparate news stories under coherent theme
- Provide analytical insight beyond obvious connections
- Have rich, varied keyword sets for robust matching
- Show clear relationships with other centroids

**Low Quality Centroids:**
- Too narrow (only match 1 type of story)
- Too broad (match everything, explain nothing)
- Generic keywords that don't differentiate
- Unclear strategic significance

## Next Steps

Based on results:
1. **If high quality**: Use as foundation for manual curation
2. **If mixed quality**: Iterate prompt design with specific examples
3. **If low quality**: Consider more structured/guided generation approach

This will inform whether to start with 20-30 centroids or go broader initially.