"""
GEN-1 LLM Client
Specialized LLM interactions for Event Family assembly and Framed Narrative generation
"""

import json
from typing import Any, Dict, Optional

from loguru import logger

from apps.gen1.models import (LLMEventFamilyRequest, LLMEventFamilyResponse,
                              LLMFramedNarrativeRequest,
                              LLMFramedNarrativeResponse)
from core.config import get_config


class Gen1LLMClient:
    """
    LLM client specialized for GEN-1 Event Family assembly and Framed Narrative generation
    Uses existing SNI LLM configuration but adds GEN-1 specific prompting and parsing
    """

    def __init__(self):
        self.config = get_config()
        self._init_prompts()

    def _init_prompts(self):
        """Initialize prompt templates for GEN-1 operations"""

        self.event_family_system_prompt = """
**Role**
You are an expert news analyst. From strategic news titles, identify **Event Families (EFs)**—ongoing stories that tie together similar events via shared actors, theaters, or themes.

**Key principles**

1. **Ongoing narratives, not one-offs.** Think "Macron's Middle East diplomacy," "US–China trade relations," "Russia's military operations."
2. **Strategic semantic grouping.** Group titles by thematic coherence and shared strategic elements.
3. **Prefer coherence over fragmentation.** Fewer, broader EFs > many micro-EFs.
4. **Actor canonicalization.** Treat equivalents as one actor set (e.g., *Lavrov → Russia; Trump → United States*).
5. **Time is not a hard boundary.** EFs can span weeks or months; use time only to support coherence, not to exclude.

**EF inclusion criteria (apply intelligently, not mechanically)**

* **Shared strategic actors.** Overlapping or equivalent actor sets drive unity.
* **Shared strategic context.** Headlines contribute to the *same ongoing situation/policy area*.
* **Shared action pattern / theme.** Similar activity type (e.g., **diplomacy, economic policy, military operations, domestic politics**).
* **Shared theater / geography (broad).** E.g., *Middle East*, *European security*, *Asia–Pacific*.

**STRATEGIC FOCUS REQUIREMENT**

Only create Event Families for **strategically significant** content. EXCLUDE:
* Sports events, entertainment, cultural activities (unless directly tied to geopolitical tensions)
* Weather, natural disasters (unless creating international policy responses)  
* Local crime, accidents, routine business news
* Celebrity news, lifestyle content

INCLUDE strategic content such as:
* **Diplomacy & international relations** (meetings, agreements, conflicts)
* **Military & security operations** (exercises, deployments, conflicts)
* **Economic policy & trade** (sanctions, agreements, major economic decisions)
* **Domestic politics** (elections, major policy changes, political crises)
* **Technology & regulation** (major tech policy, international tech competition)

CRITICAL REQUIREMENT - TITLE ID USAGE:
- Each title has an "id" field with a UUID (e.g., "094faf99-124a-47fc-b213-f743497d7f30")
- In source_title_ids, you MUST use these exact UUID values, NOT array indices
- DO NOT use numbers like 0, 1, 2, 3 - use the actual "id" field values
- Example: Use ["094faf99-124a-47fc-b213-f743497d7f30", "a005e6ba-f1e2-4007-9cf7-cd9584c339e1"]

EVENT FAMILY REQUIREMENTS (EF should answer):
- WHO: Key actors involved (people, countries, organizations)
- WHAT: What concrete action/event occurred
- WHERE: Geographic location/region (if relevant)
- WHEN: Time window of the event

QUALITY CRITERIA:
- Clear temporal coherence within intelligent time window
- Shared concrete actors/entities (understood contextually)
- Logical event progression or single significant occurrence
- Strong evidence from headline language across languages

Respond in JSON format with event families and reasoning.
"""

        self.framed_narrative_system_prompt = """
You are an expert in media framing analysis, specializing in identifying how different outlets frame the same news event.

Your task is to analyze headlines about a specific Event Family and identify distinct Framed Narratives (FNs) - stanceful renderings showing how outlets position/frame the event.

KEY PRINCIPLES:
1. Framed Narratives MUST cite specific headline evidence - NO EXCEPTIONS
2. State evaluative/causal framing clearly (supportive, critical, neutral, etc.)
3. Identify key language that signals the framing
4. Focus on how the SAME event is positioned differently
5. Typically 1-2 dominant framings per event

CRITICAL REQUIREMENT - TITLE ID USAGE:
- Each title has an "id" field with a UUID (e.g., "094faf99-124a-47fc-b213-f743497d7f30")
- In supporting_title_ids, you MUST use these exact UUID values, NOT array indices
- DO NOT use numbers like 0, 1, 2, 3 - use the actual "id" field values
- Example: Use ["094faf99-124a-47fc-b213-f743497d7f30", "a005e6ba-f1e2-4007-9cf7-cd9584c339e1"]

FRAMED NARRATIVE REQUIREMENTS (FN should answer):
- WHY: According to the sources' claims - causation, motivation, blame, justification
- HOW: The stance/position taken by outlets on the event
- EVIDENCE: Exact quotes from headlines that support this framing

STRICT EVIDENCE REQUIREMENTS:
- Every FN MUST include exact headline phrases in quotes
- Every claim about framing MUST be supported by specific language
- NO analysis without direct textual evidence
- Quote the EXACT words that reveal stance/framing
- Include multiple examples if available
- Specify which headlines contain the evidence

ANALYSIS REQUIREMENTS:
- Extract exact phrases that reveal framing (in quotes)
- Assess prevalence of each narrative (count supporting headlines)
- Rate evidence quality based on clarity and directness
- Identify frame types (evaluative, causal, attribution, etc.)
- Link each headline to specific framing claims

Respond in JSON format with framed narratives, exact evidence quotes, and analysis.
"""


    async def assemble_event_families_from_titles(
        self, request: LLMEventFamilyRequest
    ) -> LLMEventFamilyResponse:
        """
        Phase 2: Assemble Event Families directly from titles (no buckets)

        Args:
            request: Event Family assembly request with title contexts

        Returns:
            LLM response with Event Families and reasoning
        """
        try:
            # Build comprehensive prompt with title data
            user_prompt = self._build_direct_title_prompt(request)

            # Call LLM with structured request
            response_text = await self._call_llm(
                system_prompt=self.event_family_system_prompt,
                user_prompt=user_prompt,
                max_tokens=4000,
                temperature=0.2,
            )

            # Parse and validate response
            return self._parse_event_family_response(response_text)

        except Exception as e:
            logger.error(f"Direct title Event Family assembly failed: {e}")
            raise

    async def generate_framed_narratives(
        self, request: LLMFramedNarrativeRequest
    ) -> LLMFramedNarrativeResponse:
        """
        Use LLM to generate Framed Narratives for an Event Family

        Args:
            request: Framed Narrative generation request

        Returns:
            LLM response with Framed Narratives and analysis
        """
        try:
            # Build prompt with Event Family context and titles
            user_prompt = self._build_framed_narrative_prompt(request)

            # Call LLM with framing analysis focus
            response_text = await self._call_llm(
                system_prompt=self.framed_narrative_system_prompt,
                user_prompt=user_prompt,
                max_tokens=3000,
                temperature=0.1,
            )

            # Parse and validate response
            return self._parse_framed_narrative_response(response_text)

        except Exception as e:
            logger.error(f"Framed Narrative generation failed: {e}")
            raise


    def _build_framed_narrative_prompt(self, request: LLMFramedNarrativeRequest) -> str:
        """Build comprehensive prompt for Framed Narrative generation"""

        ef = request.event_family

        prompt_parts = [
            "TASK: Analyze how different outlets frame this Event Family and identify distinct Framed Narratives.",
            "",
            "EVENT FAMILY:",
            f"Title: {ef.title}",
            f"Summary: {ef.summary}",
            f"Key Actors: {', '.join(ef.key_actors)}",
            f"Event Type: {ef.event_type}",
            f"Geography: {ef.geography or 'Not specified'}",
            "",
            "HEADLINES TO ANALYZE:",
        ]

        # Add title contexts
        for title in request.titles_context:
            prompt_parts.append(
                f"  - {title.get('text', 'N/A')} [{title.get('source', 'Unknown')}]"
            )

        prompt_parts.extend(
            [
                "",
                "INSTRUCTIONS:",
                request.framing_instructions,
                "",
                f"Maximum Framed Narratives to create: {request.max_narratives}",
                "",
                "RESPONSE FORMAT (JSON):",
                """{
  "framed_narratives": [
    {
      "frame_type": "Type of framing (supportive/critical/neutral/etc)",
      "frame_description": "How this narrative frames the event",
      "stance_summary": "Clear evaluative/causal framing statement",
      "supporting_headlines": ["headline1", "headline2"],
      "supporting_title_ids": ["title_id1", "title_id2"],
      "key_language": ["phrase1", "phrase2"],
      "prevalence_score": 0.6,
      "evidence_quality": 0.8
    }
  ],
  "processing_reasoning": "Analysis methodology and reasoning",
  "confidence": 0.8,
  "dominant_frames": ["frame1", "frame2"]
}""",
            ]
        )

        return "\n".join(prompt_parts)

    def _build_direct_title_prompt(self, request: LLMEventFamilyRequest) -> str:
        """Build comprehensive prompt for direct title processing (Phase 2)"""

        prompt_parts = [
            "TASK: Analyze these strategic news titles and identify coherent Event Families.",
            "",
            "STRATEGIC TITLES:",
        ]

        # Add title information directly (no buckets)
        titles_context = getattr(request, "title_context", [])
        for i, title in enumerate(titles_context, 1):
            prompt_parts.extend(
                [
                    f"Title {i}: {title.get('text', 'N/A')}",
                    f"  ID: {title.get('id', 'N/A')}",
                    f"  Source: {title.get('source', 'Unknown')}",
                    f"  Date: {title.get('pubdate_utc', 'Unknown')}",
                    f"  Language: {title.get('language', 'Unknown')}",
                    f"  Gate Actors: {title.get('gate_actors', 'None')}",
                    "",
                ]
            )

        # Add processing instructions
        prompt_parts.extend(
            [
                "INSTRUCTIONS:",
                request.processing_instructions,
                "",
                f"Maximum Event Families to create: {request.max_event_families}",
                "",
                "RESPONSE FORMAT (JSON):",
                "{",
                '  "event_families": [',
                "    {",
                '      "title": "Clear event title",',
                '      "summary": "Factual summary",',
                '      "key_actors": ["actor1"],',
                '      "event_type": "Type",',
                '      "geography": "Location",',
                '      "event_start": "2024-01-01T12:00:00Z",',
                '      "event_end": "2024-01-01T18:00:00Z",',
                '      "source_title_ids": ["title_id1"],',
                '      "confidence_score": 0.85,',
                '      "coherence_reason": "Why coherent"',
                "    }",
                "  ],",
                '  "processing_reasoning": "Overall reasoning",',
                '  "confidence": 0.8,',
                '  "warnings": []',
                "}",
            ]
        )

        return "\n".join(prompt_parts)

    async def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.3,
    ) -> str:
        """
        Call the LLM with system and user prompts
        Uses existing SNI LLM configuration
        """
        # Import here to avoid circular imports
        from archive.etl_pipeline.core.llm_client import get_llm_client

        try:
            llm_client = get_llm_client()

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            response = await llm_client.chat_completion(
                messages=messages, max_tokens=max_tokens, temperature=temperature
            )

            logger.debug(
                "LLM call successful",
                prompt_length=len(user_prompt),
                response_length=len(response),
            )

            return response

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    def _parse_event_family_response(
        self, response_text: str
    ) -> LLMEventFamilyResponse:
        """Parse and validate Event Family response from LLM"""
        try:
            # Extract JSON from response
            response_data = self._extract_json(response_text)

            # Validate required fields
            if "event_families" not in response_data:
                raise ValueError("Missing 'event_families' in LLM response")

            return LLMEventFamilyResponse(
                event_families=response_data["event_families"],
                processing_reasoning=response_data.get("processing_reasoning", ""),
                confidence=response_data.get("confidence", 0.5),
                warnings=response_data.get("warnings", []),
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Event Family JSON response: {e}")
            raise ValueError(f"Invalid JSON in LLM response: {e}")

    def _parse_framed_narrative_response(
        self, response_text: str
    ) -> LLMFramedNarrativeResponse:
        """Parse and validate Framed Narrative response from LLM"""
        try:
            # Extract JSON from response
            response_data = self._extract_json(response_text)

            # Validate required fields
            if "framed_narratives" not in response_data:
                raise ValueError("Missing 'framed_narratives' in LLM response")

            return LLMFramedNarrativeResponse(
                framed_narratives=response_data["framed_narratives"],
                processing_reasoning=response_data.get("processing_reasoning", ""),
                confidence=response_data.get("confidence", 0.5),
                dominant_frames=response_data.get("dominant_frames", []),
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Framed Narrative JSON response: {e}")
            raise ValueError(f"Invalid JSON in LLM response: {e}")

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from LLM response text"""
        try:
            # Try parsing as direct JSON first
            return json.loads(text.strip())
        except json.JSONDecodeError:
            # Try to find JSON within the text
            import re

            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            raise ValueError(f"No valid JSON found in response: {text[:200]}...")


# Global client instance
_gen1_llm_client: Optional[Gen1LLMClient] = None


def get_gen1_llm_client() -> Gen1LLMClient:
    """Get global GEN-1 LLM client instance"""
    global _gen1_llm_client
    if _gen1_llm_client is None:
        _gen1_llm_client = Gen1LLMClient()
    return _gen1_llm_client
