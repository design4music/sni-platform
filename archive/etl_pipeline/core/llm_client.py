"""
LLM Client - Single connection point for LLM services
Strategic Narrative Intelligence ETL Pipeline

Simple abstraction that hides provider details from pipeline code.
Currently uses DeepSeek but can be easily swapped without changing pipeline code.
"""

import json
import os
from typing import Any, Dict, List, Optional

import httpx
import structlog

from core.config import get_config

logger = structlog.get_logger(__name__)


class LLMClient:
    """
    Single LLM client abstraction

    Pipeline code calls this class without knowing the underlying provider.
    Configuration determines which LLM service to use.
    """

    def __init__(self):
        """Initialize LLM client with configuration from environment"""
        
        config = get_config()
        
        # Load configuration from config system
        self.api_key = (
            config.deepseek_api_key or "sk-7f684036607a4647bfb08df006b54ea1"
        )
        self.base_url = config.deepseek_api_url
        self.model = config.llm_model

        if not self.api_key:
            raise ValueError("LLM API key not configured")

        self.timeout = config.llm_timeout_seconds
        self.max_retries = 2

        logger.info("LLM client initialized", model=self.model)

    async def generate_text(
        self, prompt: str, max_tokens: int = 2000, temperature: float = 0.3, **kwargs
    ) -> str:
        """
        Generate text using LLM

        Args:
            prompt: Text prompt for generation
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature (0.0-1.0)

        Returns:
            Generated text string
        """

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

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions", headers=headers, json=payload
                )

                if response.status_code != 200:
                    raise Exception(
                        f"LLM API error: {response.status_code} - {response.text}"
                    )

                data = response.json()
                generated_text = data["choices"][0]["message"]["content"]

                logger.debug(
                    "LLM generation successful",
                    prompt_length=len(prompt),
                    response_length=len(generated_text),
                    tokens_used=data.get("usage", {}).get("total_tokens", 0),
                )

                return generated_text.strip()

        except Exception as e:
            logger.error(
                "LLM generation failed", error=str(e), prompt_length=len(prompt)
            )
            raise

    async def generate_json(
        self, prompt: str, max_tokens: int = 2000, temperature: float = 0.3, **kwargs
    ) -> Dict[str, Any]:
        """
        Generate JSON response using LLM

        Args:
            prompt: Text prompt for generation
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature (0.0-1.0)

        Returns:
            Parsed JSON response as dictionary
        """

        # Add JSON instruction to prompt if not present
        if "json" not in prompt.lower():
            prompt += "\n\nReturn your response as valid JSON only."

        text_response = await self.generate_text(
            prompt, max_tokens, temperature, **kwargs
        )

        try:
            # Try to parse JSON response
            return json.loads(text_response)
        except json.JSONDecodeError:
            # If direct parsing fails, try to extract JSON from text
            import re

            json_match = re.search(r"\{.*\}", text_response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            raise ValueError(f"LLM did not return valid JSON: {text_response[:200]}")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 2000,
        temperature: float = 0.3,
        **kwargs,
    ) -> str:
        """
        Generate response using chat completion format

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature (0.0-1.0)

        Returns:
            Generated response text
        """

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                **kwargs,
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions", headers=headers, json=payload
                )

                if response.status_code != 200:
                    raise Exception(
                        f"LLM API error: {response.status_code} - {response.text}"
                    )

                data = response.json()
                generated_text = data["choices"][0]["message"]["content"]

                return generated_text.strip()

        except Exception as e:
            logger.error("LLM chat completion failed", error=str(e))
            raise

    async def is_available(self) -> bool:
        """
        Check if LLM service is available

        Returns:
            True if service is responding, False otherwise
        """
        try:
            test_response = await self.generate_text("Test", max_tokens=1)
            return bool(test_response)
        except:
            return False


# Global LLM client instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get global LLM client instance"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
