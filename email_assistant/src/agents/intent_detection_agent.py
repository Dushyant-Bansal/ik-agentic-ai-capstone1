"""Intent Detection Agent - classifies intent (outreach, follow-up, apology, etc.)."""

from typing import Any

from pydantic import BaseModel, Field

from email_assistant.src.integrations.llm_factory import get_llm
from email_assistant.src.models.schemas import IntentType


_INTENTS = [e.value for e in IntentType]


class _IntentOutput(BaseModel):
    """LLM structured output for intent."""

    intent: str = Field(..., description="One of: " + ", ".join(_INTENTS))


def run(state: dict[str, Any]) -> dict[str, Any]:
    """Classify email intent. Returns intent."""
    parsed = state.get("parsed_input")
    user_intent_override = state.get("user_intent_override")

    if user_intent_override and user_intent_override in _INTENTS:
        return {"intent": IntentType(user_intent_override)}

    if not parsed:
        return {"intent": IntentType.OTHER}

    llm = get_llm(temperature=0).with_structured_output(_IntentOutput)
    prompt = f"""Classify the intent of this email request into exactly one of: {", ".join(_INTENTS)}.

Request: {parsed.prompt}

Respond with the intent value only."""

    try:
        out = llm.invoke(prompt)
        intent_val = out.intent.lower().replace("-", "_").replace(" ", "_")
        return {"intent": IntentType(intent_val) if intent_val in _INTENTS else IntentType.OTHER}
    except Exception:
        return {"intent": IntentType.OTHER}
