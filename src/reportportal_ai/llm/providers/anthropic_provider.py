# src/reportportal_ai/llm/providers/anthropic_provider.py
"""Anthropic Claude LLM provider implementation."""

import os
from typing import List, Optional, AsyncIterator

import anthropic
from anthropic import AsyncAnthropic
import structlog

from src.reportportal_ai.llm.providers.base import BaseLLMProvider, Message, LLMResponse
from src.reportportal_ai.core.exceptions import ConfigurationError

logger = structlog.get_logger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API provider."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-opus-20240229",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ):
        super().__init__(model, temperature, max_tokens)
        
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ConfigurationError(
                "Anthropic API key not provided. Set ANTHROPIC_API_KEY environment variable."
            )
        
        self.client = AsyncAnthropic(api_key=self.api_key)
    
    def _convert_messages(self, messages: List[Message]) -> tuple[str, List[dict]]:
        """Convert messages to Anthropic format (system message separate)."""
        system_message = ""
        conversation = []
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                conversation.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        return system_message, conversation
    
    async def generate(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> LLMResponse:
        """Generate a response using Anthropic API."""
        if stream:
            # For streaming, collect all chunks and return as single response
            chunks = []
            async for chunk in self.generate_stream(messages, temperature, max_tokens):
                chunks.append(chunk)
            return LLMResponse(
                content="".join(chunks),
                model=self.model,
            )
        
        try:
            system_message, conversation = self._convert_messages(messages)
            
            response = await self.client.messages.create(
                model=self.model,
                system=system_message,
                messages=conversation,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
            )
            
            return LLMResponse(
                content=response.content[0].text,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                },
                metadata={"stop_reason": response.stop_reason},
            )
            
        except Exception as e:
            logger.error("Anthropic API error", error=str(e))
            raise
    
    async def generate_stream(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
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