# src/test_insights/llm/providers/ollama_provider.py
"""Ollama local LLM provider implementation."""

from typing import List, Optional, AsyncIterator
import json

import httpx
import structlog

from test_insights.llm.providers.base import BaseLLMProvider, Message, LLMResponse
from test_insights.core.exceptions import ConfigurationError

logger = structlog.get_logger(__name__)


class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM provider."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama2",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ):
        super().__init__(model, temperature, max_tokens)
        self.base_url = base_url
        self._client = httpx.AsyncClient(base_url=base_url, timeout=60.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.aclose()
    
    def _format_messages(self, messages: List[Message]) -> str:
        """Format messages into a single prompt for Ollama."""
        prompt_parts = []
        
        for msg in messages:
            if msg.role == "system":
                prompt_parts.append(f"System: {msg.content}")
            elif msg.role == "user":
                prompt_parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                prompt_parts.append(f"Assistant: {msg.content}")
        
        prompt_parts.append("Assistant:")  # Prompt for response
        return "\n\n".join(prompt_parts)
    
    async def generate(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> LLMResponse:
        """Generate a response using Ollama API."""
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
            prompt = self._format_messages(messages)
            
            response = await self._client.post(
                "/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature or self.temperature,
                        "num_predict": max_tokens or self.max_tokens,
                    },
                },
            )
            response.raise_for_status()
            
            data = response.json()
            
            return LLMResponse(
                content=data["response"],
                model=self.model,
                usage={
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                    "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                },
                metadata={
                    "eval_duration": data.get("eval_duration"),
                    "total_duration": data.get("total_duration"),
                },
            )
            
        except httpx.HTTPError as e:
            logger.error("Ollama API error", error=str(e))
            raise ConfigurationError(
                f"Failed to connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running (ollama serve)."
            )
        except Exception as e:
            logger.error("Ollama error", error=str(e))
            raise
    
    async def generate_stream(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Generate a streaming response using Ollama API."""
        try:
            prompt = self._format_messages(messages)
            
            async with self._client.stream(
                "POST",
                "/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": True,
                    "options": {
                        "temperature": temperature or self.temperature,
                        "num_predict": max_tokens or self.max_tokens,
                    },
                },
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if data.get("response"):
                                yield data["response"]
                        except json.JSONDecodeError:
                            continue
                            
        except httpx.HTTPError as e:
            logger.error("Ollama streaming error", error=str(e))
            raise ConfigurationError(
                f"Failed to connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running (ollama serve)."
            )
        except Exception as e:
            logger.error("Ollama streaming error", error=str(e))
            raise