"""LLM provider implementations."""

# from test_insights.llm.providers.base import BaseLLMProvider, LLMResponse, Message

# Import providers with error handling
_providers = {}

try:
    from test_insights.llm.providers.openai_provider import OpenAIProvider

    _providers["OpenAIProvider"] = OpenAIProvider
except ImportError:
    pass

try:
    from test_insights.llm.providers.anthropic_provider import AnthropicProvider

    _providers["AnthropicProvider"] = AnthropicProvider
except ImportError:
    pass

try:
    from test_insights.llm.providers.ollama_provider import OllamaProvider

    _providers["OllamaProvider"] = OllamaProvider
except ImportError:
    pass

# Add available providers to module namespace
for name, provider_class in _providers.items():
    globals()[name] = provider_class

__all__ = [
    "BaseLLMProvider",
    "Message",
    "LLMResponse",
] + list(_providers.keys())
