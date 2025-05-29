"""
Resolve an LLM client based on the DB model name.

Supported prefixes:
- "openai:*"     -> OpenAIClient    (uses OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_TIMEOUT_MS)
- "anthropic:*"  -> AnthropicClient (uses ANTHROPIC_API_KEY / ANTHROPIC_BASE_URL / ANTHROPIC_VERSION / ANTHROPIC_TIMEOUT_MS)
- "ollama:*"     -> OllamaClient    (uses OLLAMA_BASE_URL / OLLAMA_TIMEOUT_MS [/ OLLAMA_API_KEY])
- anything else  -> MockLLMClient

Notes:
- We set `client.model` from the suffix after the first ":" in the provided model name.
  e.g., "openai:gpt-4o-mini" -> client.model = "gpt-4o-mini"
- If required env vars are missing (e.g., API key, base URL), we gracefully fall back to the Mock client
  so the app remains runnable without secrets.
"""

import os
from .client import BaseLLMClient, MockLLMClient
from .providers.openai_client import OpenAIClient
from .providers.anthropic_client import AnthropicClient
from .providers.ollama_client import OllamaClient


def _suffix(model_name: str) -> str:
    """Return the part after the first colon; if absent, return the original string."""
    if not model_name:
        return ""
    parts = model_name.split(":", 1)
    return parts[1] if len(parts) == 2 else model_name


def get_client_for_model(model_name: str) -> BaseLLMClient:
    name = (model_name or "").strip()
    lname = name.lower()

    # OPENAI
    if lname.startswith("openai:"):
        api_key = os.getenv("OPENAI_API_KEY", "")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        timeout = int(os.getenv("OPENAI_TIMEOUT_MS", "12000"))
        if not api_key:
            # Missing key → fall back to mock
            return MockLLMClient()
        client = OpenAIClient(api_key=api_key, base_url=base_url, timeout_ms=timeout)
        client.model = _suffix(name) or "gpt-4o-mini"
        return client

    # ANTHROPIC
    if lname.startswith("anthropic:"):
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
        version = os.getenv("ANTHROPIC_VERSION", "2023-06-01")
        timeout = int(os.getenv("ANTHROPIC_TIMEOUT_MS", "12000"))
        if not api_key:
            return MockLLMClient()
        client = AnthropicClient(api_key=api_key, base_url=base_url, api_version=version, timeout_ms=timeout)
        client.model = _suffix(name) or "claude-3-haiku"
        return client

    # OLLAMA
    if lname.startswith("ollama:"):
        base_url = os.getenv("OLLAMA_BASE_URL", "")
        timeout = int(os.getenv("OLLAMA_TIMEOUT_MS", "12000"))
        api_key = os.getenv("OLLAMA_API_KEY", None)  # usually not needed
        if not base_url:
            return MockLLMClient()
        client = OllamaClient(base_url=base_url, timeout_ms=timeout, api_key=api_key)
        client.model = _suffix(name) or "llama3:8b-instruct"
        return client

    # DEFAULT → MOCK
    return MockLLMClient()
