"""
GEN-1 LLM Client
Specialized LLM interactions for Event Family assembly and Framed Narrative generation
"""

import asyncio
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from apps.generate.models import (LLMEventFamilyRequest,
                                  LLMEventFamilyResponse,
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

    def _load_taxonomies(self) -> None:
        """Load event type and theater taxonomies from CSV files"""
        data_path = Path(__file__).parent.parent.parent / "data"

        # Load event types
        self.event_types: List[Dict[str, str]] = []
        event_types_path = data_path / "event_types.csv"
        if event_types_path.exists():
            with open(event_types_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self.event_types = list(reader)

        # Load theaters
        self.theaters: List[Dict[str, str]] = []
        theaters_path = data_path / "theaters.csv"
        if theaters_path.exists():
            with open(theaters_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self.theaters = list(reader)

    def _init_prompts(self):
        """Initialize prompt templates for GEN-1 operations"""

        # Load standardized taxonomies
        self._load_taxonomies()

        self.event_family_system_prompt = """
**Role**
You are an expert news analyst. From strategic news titles, assemble long-lived **Event Families (Sagas)** by grouping incidents that share (key_actors + geography + event_type). Do not create families for single incidents; absorb repeated incidents into one family.

**Key principles**

1. **Create Sagas, not single incidents.** Think "Ukraine Conflict Saga," "Gaza Military Operations Saga," "Iran Nuclear Diplomacy Saga."
2. **Triple key matching: actors + geography + event_type.** Events with same strategic actors, same theater, and same activity type = one Saga.
3. **Absorb incidents into existing patterns.** If similar actors are doing similar things in the same theater, it's the same ongoing Saga.
4. **Actor canonicalization.** Treat equivalents as one actor set (e.g., *Lavrov → Russia; Trump → United States*).
5. **Time spans are expected.** Sagas naturally span weeks or months; temporal gaps don't break the pattern.

**Saga Assembly Criteria (Triple Key Matching)**

* **ACTORS**: Same strategic actors or actor sets (canonicalized equivalents)
* **GEOGRAPHY**: Same strategic theater (use specific theater codes)  
* **EVENT_TYPE**: Same category of strategic activity
* **PATTERN**: Repeated or ongoing incidents, not isolated events

**Anti-fragmentation Rule**: If you can group incidents by (actors + geography + event_type), you MUST create one Saga, not multiple families.

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

**MULTILINGUAL PROCESSING**

This system processes content in multiple languages including English, Spanish, French, German, Italian, Portuguese, Indonesian, and others. You MUST:

1. **Cross-language consolidation**: Group titles about the same strategic event regardless of language
   - Example: English "Putin visits China", Spanish "Putin visita China", French "Poutine visite la Chine" = same EF
2. **Actor canonicalization across languages**: Standardize actor names to English canonical forms
   - "Emmanuel Macron" = "Macron" = "Francia" → "France" 
   - "Xi Jinping" = "习近平" = "Cina" → "China"
   - "Donald Trump" = "Trump" = "Estados Unidos" → "United States"
3. **Theater/event_type consistency**: Use English taxonomy values regardless of source language
4. **Summary language**: Always write summaries and titles in English for system consistency
5. **Language diversity strength**: Multilingual coverage provides richer perspective on global events

CRITICAL REQUIREMENT - TITLE ID USAGE:
- Each title has an "id" field with a UUID (e.g., "094faf99-124a-47fc-b213-f743497d7f30")
- In source_title_ids, you MUST use these exact UUID values, NOT array indices
- DO NOT use numbers like 0, 1, 2, 3 - use the actual "id" field values
- Example: Use ["094faf99-124a-47fc-b213-f743497d7f30", "a005e6ba-f1e2-4007-9cf7-cd9584c339e1"]

**STANDARDIZED TAXONOMIES - MANDATORY COMPLIANCE**

EVENT_TYPE must be one of these exact values:
- Strategy/Tactics: Military strategy and tactical operations
- Humanitarian: Humanitarian crises and aid operations  
- Alliances/Geopolitics: Alliance formation and geopolitical realignments
- Diplomacy/Negotiations: Diplomatic meetings and negotiation processes
- Sanctions/Economy: Economic sanctions and financial measures
- Domestic Politics: Internal political developments and governance
- Procurement/Force-gen: Military procurement and force generation
- Tech/Cyber/OSINT: Technology warfare and intelligence operations
- Legal/ICC: Legal proceedings and international court actions
- Information/Media/Platforms: Information warfare and media operations
- Energy/Infrastructure: Energy security and critical infrastructure

GEOGRAPHY must be one of these specific theater codes (choose the most relevant):
- UKRAINE: Ukraine Conflict Theater (Russia-Ukraine war, border incidents)
- GAZA: Gaza/Palestine Theater (Israel-Palestine conflict zone)
- TAIWAN_STRAIT: Taiwan Strait Theater (China-Taiwan tensions, South China Sea)
- IRAN_NUCLEAR: Iran Nuclear Theater (Nuclear program, sanctions, IAEA)
- EUROPE_SECURITY: European Security Theater (NATO, EU defense matters)
- US_DOMESTIC: US Domestic Theater (US internal politics, domestic policy)
- CHINA_TRADE: China Trade Theater (US-China economic competition)
- MEAST_REGIONAL: Middle East Regional Theater (Syria, Iraq, Yemen, Gulf states)
- CYBER_GLOBAL: Global Cyber Theater (State cyber operations, digital warfare)
- CLIMATE_GLOBAL: Climate/Energy Theater (Energy security, resource conflicts)
- AFRICA_SECURITY: Africa Security Theater (African conflicts, peacekeeping)
- KOREA_PENINSULA: Korean Peninsula Theater (North Korea, regional tensions)
- LATAM_REGIONAL: Latin America Regional Theater (US-Venezuela, US-Mexico border, regional conflicts)
- ARCTIC: Arctic Theater (Arctic sovereignty, resource competition)
- GLOBAL_SUMMIT: Global Diplomatic Theater (International summits, multilateral diplomacy)

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

**HARD RULES - NON-NEGOTIABLE:**
1. **MUST cite 2-6 specific headline UUIDs per frame** with short quotes from those headlines
2. **Maximum 1-3 frames total** - drop weak frames, keep only the strongest
3. **Each frame needs concrete textual evidence** - quote the actual headline language that signals the framing
4. **No frame without citations** - if you can't cite specific headlines, don't create the frame

**KEY PRINCIPLES:**
- State evaluative/causal framing clearly (supportive, critical, neutral, etc.)
- Focus on how the SAME event is positioned differently by different outlets
- Quality over quantity - fewer, well-evidenced frames are better than many weak ones

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
                max_tokens=self.config.llm_max_tokens_ef,
                temperature=self.config.llm_temperature,
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
                max_tokens=self.config.llm_max_tokens_fn,
                temperature=self.config.llm_temperature,
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
                '      "event_type": "Strategy/Tactics",',
                '      "primary_theater": "THEATER_CODE",',
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
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Call the LLM with system and user prompts
        Uses existing SNI LLM configuration
        """
        # Use unified configuration
        import httpx

        # Apply defaults if not specified
        if temperature is None:
            temperature = self.config.llm_temperature

        # Implement retry logic with exponential backoff
        for attempt in range(self.config.llm_retry_attempts):
            try:
                headers = {
                    "Authorization": f"Bearer {self.config.deepseek_api_key}",
                    "Content-Type": "application/json",
                }

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]

                payload = {
                    "model": self.config.llm_model,
                    "messages": messages,
                    "temperature": temperature,
                }

                # Only add max_tokens if explicitly specified
                if max_tokens is not None:
                    payload["max_tokens"] = max_tokens

                async with httpx.AsyncClient(
                    timeout=self.config.llm_timeout_seconds
                ) as client:
                    response_data = await client.post(
                        f"{self.config.deepseek_api_url}/chat/completions",
                        headers=headers,
                        json=payload,
                    )

                    if response_data.status_code != 200:
                        raise Exception(
                            f"LLM API error: {response_data.status_code} - {response_data.text}"
                        )

                    data = response_data.json()
                    response = data["choices"][0]["message"]["content"].strip()

                logger.debug(
                    "LLM call successful",
                    attempt=attempt + 1,
                    prompt_length=len(user_prompt),
                    response_length=len(response),
                )

                return response

            except Exception as e:
                is_last_attempt = attempt == self.config.llm_retry_attempts - 1
                if is_last_attempt:
                    logger.error(
                        f"LLM call failed after {self.config.llm_retry_attempts} attempts: {e}"
                    )
                    raise
                else:
                    # Exponential backoff with jitter
                    delay = (self.config.llm_retry_backoff**attempt) + (0.1 * attempt)
                    logger.warning(
                        f"LLM call attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s"
                    )
                    await asyncio.sleep(delay)

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
            # Try to find JSON within markdown code blocks
            import re

            # First, try to extract from markdown code blocks (multiple patterns)
            patterns = [
                r"```json\s*(.*?)\s*```",  # Standard: ```json ... ```
                r"```\s*(.*?)\s*```",  # Generic: ``` ... ```
                r"`json\s*(.*?)\s*`",  # Single backtick: `json ... `
            ]

            for pattern in patterns:
                markdown_match = re.search(pattern, text, re.DOTALL)
                if markdown_match:
                    try:
                        json_content = markdown_match.group(1).strip()
                        # Only try if it looks like JSON (starts with {)
                        if json_content.startswith("{"):
                            return json.loads(json_content)
                    except json.JSONDecodeError:
                        continue

            # Fallback: try to find any JSON object in the text
            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            raise ValueError(f"No valid JSON found in response: {text}")


# Global client instance
_gen1_llm_client: Optional[Gen1LLMClient] = None


def get_gen1_llm_client() -> Gen1LLMClient:
    """Get global GEN-1 LLM client instance"""
    global _gen1_llm_client
    if _gen1_llm_client is None:
        _gen1_llm_client = Gen1LLMClient()
    return _gen1_llm_client
