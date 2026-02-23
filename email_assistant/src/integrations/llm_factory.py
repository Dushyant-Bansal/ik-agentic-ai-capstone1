"""LLM factory for primary and fallback models."""

import os
from typing import Optional, Type

from langchain_core.language_models import BaseChatModel

from email_assistant.src.integrations.config_loader import load_mcp_config
from email_assistant.src.integrations.openai_client import get_openai_llm


def get_llm(temperature: float = 0.7) -> BaseChatModel:
    """Return primary LLM based on config."""
    config = load_mcp_config()
    provider = config.get("primary_provider", "openai")
    model = config.get("primary_model", "gpt-4o-mini")

    if provider == "openai":
        return get_openai_llm(model=model, temperature=temperature)
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY required when primary_provider is anthropic")
        return ChatAnthropic(model=model, temperature=temperature, api_key=api_key)
    if provider == "cohere":
        from email_assistant.src.integrations.cohere_client import get_cohere_llm

        return get_cohere_llm(model=model, temperature=temperature)

    return get_openai_llm(model=model, temperature=temperature)


def get_fallback_llm(temperature: float = 0.7) -> Optional[BaseChatModel]:
    """Return fallback LLM if configured and API key is available."""
    config = load_mcp_config()
    provider = config.get("fallback_provider")
    model = config.get("fallback_model")
    if not provider or not model:
        return None
    try:
        if provider == "openai":
            return get_openai_llm(model=model, temperature=temperature)
        if provider == "anthropic":
            from langchain_anthropic import ChatAnthropic

            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                return None
            return ChatAnthropic(model=model, temperature=temperature, api_key=api_key)
        if provider == "cohere":
            from email_assistant.src.integrations.cohere_client import get_cohere_llm

            return get_cohere_llm(model=model, temperature=temperature)
    except (ValueError, ImportError):
        pass
    return None
