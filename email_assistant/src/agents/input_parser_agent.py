"""Input Parsing Agent - validates prompt, extracts intent, recipient, tone, constraints."""

from typing import Any

from pydantic import BaseModel, Field

from email_assistant.src.integrations.llm_factory import get_llm
from email_assistant.src.models.schemas import Constraints, ParsedInput, ToneType


class _ParsedOutput(BaseModel):
    """LLM structured output schema."""

    prompt: str = Field(..., description="Validated/normalized prompt")
    recipient: str | None = Field(None, description="Extracted recipient if mentioned")
    tone: str = Field(..., description="Extracted tone: formal, casual, assertive, friendly, professional")
    max_length: int | None = Field(None, description="Max length hint if mentioned")
    language: str = Field(default="en", description="Language")


def run(state: dict[str, Any]) -> dict[str, Any]:
    """Parse and validate user input. Returns parsed_input and any errors."""
    raw_prompt = state.get("raw_prompt", "")
    user_tone = state.get("user_tone", "professional")
    user_recipient = state.get("user_recipient")

    if not raw_prompt or not raw_prompt.strip():
        return {
            "parsed_input": None,
            "errors": (state.get("errors") or []) + ["Prompt cannot be empty"],
        }

    llm = get_llm(temperature=0.1).with_structured_output(_ParsedOutput)
    prompt = f"""Parse and normalize this email request. Extract recipient (if mentioned), tone, and any constraints (length, language).

User's stated tone preference: {user_tone}
User's stated recipient (if any): {user_recipient or "not provided"}

Raw prompt:
{raw_prompt}

Return structured data. For tone, use one of: formal, casual, assertive, friendly, professional.
Use the user's stated tone if they provided one and the prompt doesn't override it."""

    try:
        out = llm.invoke(prompt)
        tone_map = {
            "formal": ToneType.FORMAL,
            "casual": ToneType.CASUAL,
            "assertive": ToneType.ASSERTIVE,
            "friendly": ToneType.FRIENDLY,
            "professional": ToneType.PROFESSIONAL,
        }
        tone = tone_map.get(out.tone.lower(), ToneType.PROFESSIONAL)
        parsed = ParsedInput(
            prompt=out.prompt,
            recipient=out.recipient or user_recipient,
            tone=tone,
            constraints=Constraints(max_length=out.max_length, language=out.language),
        )
        return {"parsed_input": parsed, "errors": []}
    except Exception as e:
        # Fallback: use user inputs directly
        tone_map = {
            "formal": ToneType.FORMAL,
            "casual": ToneType.CASUAL,
            "assertive": ToneType.ASSERTIVE,
            "friendly": ToneType.FRIENDLY,
            "professional": ToneType.PROFESSIONAL,
        }
        parsed = ParsedInput(
            prompt=raw_prompt.strip(),
            recipient=user_recipient,
            tone=tone_map.get(str(user_tone).lower(), ToneType.PROFESSIONAL),
            constraints=Constraints(),
        )
        return {
            "parsed_input": parsed,
            "errors": (state.get("errors") or []) + [f"Parse fallback used: {e}"],
        }
