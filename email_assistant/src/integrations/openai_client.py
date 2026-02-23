"""OpenAI LLM client for the email assistant."""

import os
from typing import Optional

from langchain_openai import ChatOpenAI

from email_assistant.src.integrations.config_loader import load_mcp_config


def get_openai_llm(
    model: Optional[str] = None,
    temperature: float = 0.7,
) -> ChatOpenAI:
    """Create OpenAI Chat model. Uses config or env."""
    config = load_mcp_config()
    model_name = model or config.get("primary_model", "gpt-4o-mini")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=api_key,
    )
