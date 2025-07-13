"""Anthropic Claude LLM provider implementation."""

import os
import anthropic
from anthropic import AsyncAnthropic
import structlog

from test_insights.llm.providers.base import BaseLLMProvider
from test_insights.core.exceptions import ConfigurationError

logger = structlog.get_logger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API provider."""

    def __init__(
        self,
        api_key=None,
        model="claude-3-opus-20240229",
        temperature=0.7,
        max_tokens=2000,
    ):
        super().__init__(model, temperature, max_tokens)

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ConfigurationError(
                "Anthropic API key not provided. Set ANTHROPIC_API_KEY environment variable."
            )

        self.client = AsyncAnthropic(api_key=self.api_key)

    def _convert_messages(self, messages):
        """Convert messages to Anthropic format (system message separate)."""
        system_message = ""
        conversation = []

        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                conversation.append({"role": msg.role, "content": msg.content})

        return system_message, conversation

    async def generate(
        self,
        messages,
        temperature=None,
        max_tokens=None,
        stream=False,
    ):
        """Generate a response using Anthropic API."""
        if stream:
            chunks = []
            async for chunk in self.generate_stream(messages, temperature, max_tokens):
                chunks.append(chunk)
            return {
                "content": "".join(chunks),
                "model": self.model,
            }

        try:
            system_message, conversation = self._convert_messages(messages)

            response = await self.client.messages.create(
                model=self.model,
                system=system_message,
                messages=conversation,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
            )

            return {
                "content": response.content[0].text,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                },
                "metadata": {"stop_reason": response.stop_reason},
            }

        except Exception as e:
            logger.error("Anthropic API error", error=str(e))
            raise

    async def generate_stream(
        self,
        messages,
        temperature=None,
        max_tokens=None,
    ):
        """Generate a streaming response using Anthropic API."""
        try:
            system_message, conversation = self._convert_messages(messages)

            async with self.client.messages.stream(
                model=self.model,
                system=system_message,
                messages=conversation,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            logger.error("Anthropic streaming error", error=str(e))
            raise
