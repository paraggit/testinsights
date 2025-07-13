"""LLM integration module for natural language querying."""

from test_insights.llm.providers.base import BaseLLMProvider, LLMResponse, Message
from test_insights.llm.query_processor import QueryProcessor

# Import providers with error handling for optional dependencies
try:
    from test_insights.llm.providers.openai_provider import OpenAIProvider
except ImportError:
    OpenAIProvider = None

try:
    from test_insights.llm.providers.anthropic_provider import AnthropicProvider
except ImportError:
    AnthropicProvider = None

try:
    from test_insights.llm.providers.ollama_provider import OllamaProvider
except ImportError:
    OllamaProvider = None

__all__ = [
    "BaseLLMProvider",
    "Message",
    "LLMResponse",
    "QueryProcessor",
]

# Add providers to __all__ if they're available
if OpenAIProvider:
    __all__.append("OpenAIProvider")
if AnthropicProvider:
    __all__.append("AnthropicProvider")
if OllamaProvider:
    __all__.append("OllamaProvider")
