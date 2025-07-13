# src/reportportal_ai/llm/providers/base.py
"""Base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator
from dataclasses import dataclass


@dataclass
class Message:
    """Represents a message in a conversation."""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    """Response from an LLM."""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""
    
    def __init__(self, model: str, temperature: float = 0.7, max_tokens: int = 2000):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> LLMResponse:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Generate a streaming response from the LLM."""
        pass
    
    def format_context(self, context_documents: List[Dict[str, Any]]) -> str:
        """Format context documents for inclusion in prompts."""
        formatted_parts = []
        
        for i, doc in enumerate(context_documents, 1):
            metadata = doc.get("metadata", {})
            entity_type = metadata.get("entity_type", "unknown")
            
            # Format based on entity type
            if entity_type == "launch":
                formatted_parts.append(
                    f"[Launch #{i}]\n"
                    f"Name: {metadata.get('launch_name', 'N/A')}\n"
                    f"Status: {metadata.get('status', 'N/A')}\n"
                    f"Mode: {metadata.get('mode', 'N/A')}\n"
                    f"Content: {doc.get('document', '')}\n"
                )
            elif entity_type == "test_item":
                formatted_parts.append(
                    f"[Test Item #{i}]\n"
                    f"Name: {metadata.get('item_name', 'N/A')}\n"
                    f"Type: {metadata.get('item_type', 'N/A')}\n"
                    f"Status: {metadata.get('status', 'N/A')}\n"
                    f"Content: {doc.get('document', '')}\n"
                )
            elif entity_type == "log":
                formatted_parts.append(
                    f"[Log #{i}]\n"
                    f"Level: {metadata.get('level', 'N/A')}\n"
                    f"Content: {doc.get('document', '')}\n"
                )
            else:
                formatted_parts.append(
                    f"[{entity_type.title()} #{i}]\n"
                    f"Content: {doc.get('document', '')}\n"
                )
        
        return "\n---\n".join(formatted_parts)