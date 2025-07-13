# src/test_insights/llm/providers/openai_provider.py
"""OpenAI LLM provider implementation."""

import os
from typing import List, Optional, AsyncIterator

import openai
from openai import AsyncOpenAI
import structlog

from test_insights.llm.providers.base import BaseLLMProvider, Message, LLMResponse
from test_insights.core.exceptions import ConfigurationError

logger = structlog.get_logger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ):
        super().__init__(model, temperature, max_tokens)
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ConfigurationError(
                "OpenAI API key not provided. Set OPENAI_API_KEY environment variable."
            )
        
        self.client = AsyncOpenAI(api_key=self.api_key)
    
    async def generate(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> LLMResponse:
        """Generate a response using OpenAI API."""
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
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": m.role, "content": m.content} for m in messages],
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                metadata={"finish_reason": response.choices[0].finish_reason},
            )
            
        except Exception as e:
            logger.error("OpenAI API error", error=str(e))
            raise
    
    async def generate_stream(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Generate a streaming response using OpenAI API."""
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": m.role, "content": m.content} for m in messages],
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error("OpenAI streaming error", error=str(e))
            raise