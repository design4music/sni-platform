"""
Base classes for narrative generation pipeline
"""

import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import structlog
from jinja2 import Environment, FileSystemLoader, Template

logger = structlog.get_logger(__name__)


class GenerationStage(str, Enum):
    GEN_1_NARRATIVE_BUILDER = "gen_1_narrative_builder"
    GEN_2_UPDATES = "gen_2_updates"
    GEN_3_CONTRADICTION_DETECTION = "gen_3_contradiction_detection"


class LLMProvider(str, Enum):
    DEEPSEEK = "deepseek"
    CLAUDE = "claude"
    OPENAI = "openai"


@dataclass
class GenerationResult:
    """Result of a generation operation"""

    stage: GenerationStage
    narratives: List["GeneratedNarrative"]
    processing_time_seconds: float
    items_processed: int
    items_generated: int
    items_failed: int
    metadata: Dict[str, Any]


@dataclass
class GeneratedNarrative:
    """A generated narrative"""

    narrative_id: str
    cluster_id: str
    stage: GenerationStage
    title: str
    content: str
    summary: Optional[str]
    key_points: List[str]
    narrative_type: str  # main, update, contradiction
    confidence_score: float
    model_used: str
    generation_params: Dict[str, Any]
    contradictions_detected: List[Dict[str, Any]]
    update_reason: Optional[str]
    version: int
    parent_narrative_id: Optional[str]
    metadata: Dict[str, Any]


class BaseLLMClient(ABC):
    """Base class for LLM clients"""

    def __init__(self, provider: LLMProvider, config: Dict[str, Any]):
        self.provider = provider
        self.config = config
        self.logger = structlog.get_logger(__name__).bind(provider=provider.value)

    @abstractmethod
    async def generate_text(
        self, prompt: str, max_tokens: int = 1000, temperature: float = 0.3, **kwargs
    ) -> Dict[str, Any]:
        """Generate text using the LLM"""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the LLM is available"""
        pass


class DeepSeekClient(BaseLLMClient):
    """DeepSeek API client"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(LLMProvider.DEEPSEEK, config)
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://api.deepseek.com/v1")
        self.model = config.get("model", "deepseek-chat")

        if not self.api_key:
            raise ValueError("DeepSeek API key is required")

    async def generate_text(
        self, prompt: str, max_tokens: int = 1000, temperature: float = 0.3, **kwargs
    ) -> Dict[str, Any]:
        """Generate text using DeepSeek API"""
        import httpx

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
                **kwargs,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60.0,
                )

                if response.status_code != 200:
                    raise Exception(f"DeepSeek API error: {response.status_code}")

                data = response.json()

                return {
                    "text": data["choices"][0]["message"]["content"],
                    "usage": data.get("usage", {}),
                    "model": data.get("model", self.model),
                    "provider": self.provider.value,
                }

        except Exception as e:
            self.logger.error("DeepSeek generation failed", error=str(e))
            raise

    async def is_available(self) -> bool:
        """Check DeepSeek availability"""
        try:
            await self.generate_text("Test", max_tokens=1)
            return True
        except:
            return False


class ClaudeClient(BaseLLMClient):
    """Anthropic Claude API client"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(LLMProvider.CLAUDE, config)
        self.api_key = config.get("api_key")
        self.model = config.get("model", "claude-3-haiku-20240307")

        if not self.api_key:
            raise ValueError("Claude API key is required")

    async def generate_text(
        self, prompt: str, max_tokens: int = 1000, temperature: float = 0.3, **kwargs
    ) -> Dict[str, Any]:
        """Generate text using Claude API"""
        import anthropic

        try:
            client = anthropic.AsyncAnthropic(api_key=self.api_key)

            response = await client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            return {
                "text": response.content[0].text,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens
                    + response.usage.output_tokens,
                },
                "model": response.model,
                "provider": self.provider.value,
            }

        except Exception as e:
            self.logger.error("Claude generation failed", error=str(e))
            raise

    async def is_available(self) -> bool:
        """Check Claude availability"""
        try:
            await self.generate_text("Test", max_tokens=1)
            return True
        except:
            return False


class OpenAIClient(BaseLLMClient):
    """OpenAI API client"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(LLMProvider.OPENAI, config)
        self.api_key = config.get("api_key")
        self.model = config.get("model", "gpt-3.5-turbo")

        if not self.api_key:
            raise ValueError("OpenAI API key is required")

    async def generate_text(
        self, prompt: str, max_tokens: int = 1000, temperature: float = 0.3, **kwargs
    ) -> Dict[str, Any]:
        """Generate text using OpenAI API"""
        import openai

        try:
            client = openai.AsyncOpenAI(api_key=self.api_key)

            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs,
            )

            return {
                "text": response.choices[0].message.content,
                "usage": response.usage.dict(),
                "model": response.model,
                "provider": self.provider.value,
            }

        except Exception as e:
            self.logger.error("OpenAI generation failed", error=str(e))
            raise

    async def is_available(self) -> bool:
        """Check OpenAI availability"""
        try:
            await self.generate_text("Test", max_tokens=1)
            return True
        except:
            return False


class LLMManager:
    """Manages multiple LLM providers with fallback"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = structlog.get_logger(__name__)

        # Initialize clients
        self.clients = {}

        # DeepSeek (primary)
        if config.get("deepseek_api_key"):
            self.clients[LLMProvider.DEEPSEEK] = DeepSeekClient(
                {
                    "api_key": config.get("deepseek_api_key"),
                    "model": config.get("deepseek_model", "deepseek-chat"),
                }
            )

        # Claude (fallback)
        if config.get("claude_api_key"):
            self.clients[LLMProvider.CLAUDE] = ClaudeClient(
                {
                    "api_key": config.get("claude_api_key"),
                    "model": config.get("claude_model", "claude-3-haiku-20240307"),
                }
            )

        # OpenAI (fallback)
        if config.get("openai_api_key"):
            self.clients[LLMProvider.OPENAI] = OpenAIClient(
                {
                    "api_key": config.get("openai_api_key"),
                    "model": config.get("openai_model", "gpt-3.5-turbo"),
                }
            )

        # Set provider priority
        self.primary_provider = LLMProvider(
            config.get("primary_llm_provider", "deepseek")
        )
        self.fallback_providers = [
            LLMProvider(p)
            for p in config.get("fallback_llm_providers", ["claude", "openai"])
        ]

    async def generate_text(
        self, prompt: str, max_tokens: int = 1000, temperature: float = 0.3, **kwargs
    ) -> Dict[str, Any]:
        """Generate text with fallback to secondary providers"""

        providers_to_try = [self.primary_provider] + self.fallback_providers

        for provider in providers_to_try:
            if provider not in self.clients:
                continue

            client = self.clients[provider]

            try:
                self.logger.debug("Attempting generation", provider=provider.value)

                if not await client.is_available():
                    self.logger.warning("Provider unavailable", provider=provider.value)
                    continue

                result = await client.generate_text(
                    prompt, max_tokens, temperature, **kwargs
                )

                self.logger.info("Generation successful", provider=provider.value)
                return result

            except Exception as e:
                self.logger.error(
                    "Generation failed, trying next provider",
                    provider=provider.value,
                    error=str(e),
                )
                continue

        raise Exception("All LLM providers failed")


class BaseGenerationStage(ABC):
    """Base class for generation stages"""

    def __init__(self, stage: GenerationStage, config: Dict[str, Any]):
        self.stage = stage
        self.config = config
        self.logger = structlog.get_logger(__name__).bind(stage=stage.value)

        # Initialize LLM manager
        self.llm_manager = LLMManager(config)

        # Initialize template environment
        template_dir = config.get("template_dir", "templates")
        self.template_env = Environment(
            loader=FileSystemLoader(template_dir), autoescape=False
        )

        # Stage-specific configuration
        self.model_config = config.get("model_config", {})
        self.prompt_template_name = config.get("prompt_template")
        self.output_format = config.get("output_format", "text")

    @abstractmethod
    async def generate_narratives(
        self,
        clusters: List[Dict[str, Any]],
        existing_narratives: Optional[List[GeneratedNarrative]] = None,
    ) -> GenerationResult:
        """Main generation method to implement"""
        pass

    async def generate_from_template(
        self, template_name: str, context: Dict[str, Any], **llm_kwargs
    ) -> Dict[str, Any]:
        """Generate text using a template"""

        try:
            # Load and render template
            template = self.template_env.get_template(template_name)
            prompt = template.render(**context)

            self.logger.debug(
                "Generated prompt", template=template_name, prompt_length=len(prompt)
            )

            # Generate with LLM
            result = await self.llm_manager.generate_text(
                prompt=prompt, **{**self.model_config, **llm_kwargs}
            )

            return result

        except Exception as e:
            self.logger.error(
                "Template generation failed", template=template_name, error=str(e)
            )
            raise

    def extract_key_points(self, content: str) -> List[str]:
        """Extract key points from generated content"""

        # Simple extraction based on bullet points or numbered lists
        key_points = []
        lines = content.split("\n")

        for line in lines:
            line = line.strip()
            # Look for bullet points or numbered lists
            if (
                line.startswith("*")
                or line.startswith("-")
                or line.startswith("*")
                or line.startswith("1.")
                or line.startswith("2.")
                or line.startswith("3.")
            ):

                # Clean up the point
                point = line.lstrip("-*123456789. ").strip()
                if point and len(point) > 10:
                    key_points.append(point)

        # If no bullet points found, try to extract sentences
        if not key_points:
            sentences = content.split(".")
            for sentence in sentences[:5]:  # Take first 5 sentences
                sentence = sentence.strip()
                if len(sentence) > 20:
                    key_points.append(sentence + ".")

        return key_points[:10]  # Limit to 10 key points

    def calculate_confidence_score(
        self, cluster: Dict[str, Any], generated_content: str
    ) -> float:
        """Calculate confidence score for generated narrative"""

        score = 0.0

        # Content length factor (0.2)
        content_length = len(generated_content)
        if content_length > 100:
            score += 0.2
        elif content_length > 50:
            score += 0.1

        # Cluster coherence factor (0.3)
        coherence_score = cluster.get("coherence_score", 0.0)
        score += coherence_score * 0.3

        # Article count factor (0.2)
        article_count = len(cluster.get("articles", []))
        if article_count >= 5:
            score += 0.2
        elif article_count >= 3:
            score += 0.1
        elif article_count >= 1:
            score += 0.05

        # Entity richness factor (0.1)
        key_entities = cluster.get("key_entities", {})
        entity_count = sum(len(entities) for entities in key_entities.values())
        if entity_count >= 5:
            score += 0.1
        elif entity_count >= 2:
            score += 0.05

        # Topic coherence factor (0.1)
        dominant_topics = cluster.get("dominant_topics", [])
        if len(dominant_topics) >= 3:
            score += 0.1
        elif len(dominant_topics) >= 1:
            score += 0.05

        # Language quality factor (0.1)
        # Simple heuristic: presence of common narrative words
        narrative_words = [
            "because",
            "therefore",
            "however",
            "meanwhile",
            "consequently",
            "furthermore",
            "moreover",
            "nevertheless",
            "additionally",
        ]

        content_lower = generated_content.lower()
        narrative_word_count = sum(
            1 for word in narrative_words if word in content_lower
        )

        if narrative_word_count >= 3:
            score += 0.1
        elif narrative_word_count >= 1:
            score += 0.05

        return min(score, 1.0)  # Cap at 1.0


class GenerationPipeline:
    """Main generation pipeline coordinator"""

    def __init__(self, stages: List[BaseGenerationStage]):
        self.stages = stages
        self.logger = structlog.get_logger(__name__)

    async def run_generation_pipeline(
        self, clusters: List[Dict[str, Any]]
    ) -> List[GenerationResult]:
        """Run the complete generation pipeline"""

        results = []
        current_narratives = []

        self.logger.info(
            "Starting generation pipeline",
            stages=len(self.stages),
            clusters=len(clusters),
        )

        for stage in self.stages:
            try:
                self.logger.info(
                    "Starting generation stage",
                    stage=stage.stage.value,
                    clusters=len(clusters),
                )

                result = await stage.generate_narratives(
                    clusters=clusters, existing_narratives=current_narratives
                )

                results.append(result)
                current_narratives.extend(result.narratives)

                self.logger.info(
                    "Generation stage completed",
                    stage=stage.stage.value,
                    narratives_generated=len(result.narratives),
                    processing_time=result.processing_time_seconds,
                )

            except Exception as e:
                self.logger.error(
                    "Generation stage failed", stage=stage.stage.value, error=str(e)
                )
                # Continue with next stage
                continue

        self.logger.info(
            "Generation pipeline completed",
            total_stages=len(results),
            total_narratives=len(current_narratives),
        )

        return results
