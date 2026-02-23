"""Cohere LLM client for fallback."""

import os
from typing import Optional

from langchain_cohere import ChatCohere

from email_assistant.src.integrations.config_loader import load_mcp_config


def get_cohere_llm(
    model: Optional[str] = None,
    temperature: float = 0.7,
) -> ChatCohere:
    """Create Cohere Chat model for fallback. Uses config or env."""
    config = load_mcp_config()
    model_name = model or config.get("fallback_model", "command-r-plus")
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        raise ValueError("COHERE_API_KEY environment variable is required for Cohere fallback")
    return ChatCohere(
        model=model_name,
        temperature=temperature,
        api_key=api_key,
    )
