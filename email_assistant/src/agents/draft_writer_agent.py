"""Draft Writer Agent - generates subject and body with tone-aware templates."""

from typing import Any

from pydantic import BaseModel, Field

from email_assistant.src.integrations.llm_factory import get_llm
from email_assistant.src.models.schemas import DraftResult, IntentType, ToneType


class _DraftOutput(BaseModel):
    """LLM structured output for draft."""

    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email body text")


def run(state: dict[str, Any]) -> dict[str, Any]:
    """Generate email draft. Returns draft."""
    parsed = state.get("parsed_input")
    intent = state.get("intent", IntentType.OTHER)
    tone_context = state.get("tone_context", "")

    if not parsed:
        return {
            "draft": DraftResult(subject="(No subject)", body="Please provide a prompt.", intent=intent, tone=parsed.tone if parsed else None),
        }

    llm = get_llm(temperature=0.7).with_structured_output(_DraftOutput)
    recipient = f" Recipient: {parsed.recipient}" if parsed.recipient else ""
    length_hint = ""
    if parsed.constraints.max_length:
        length_hint = f" Keep the email under {parsed.constraints.max_length} words."

    prompt = f"""Write a complete email based on this request.

{parsed.prompt}{recipient}

{tone_context}{length_hint}

Output a subject line and full body. Use proper email format (greeting, body, closing)."""

    try:
        out = llm.invoke(prompt)
        draft = DraftResult(
            subject=out.subject,
            body=out.body,
            intent=intent,
            tone=parsed.tone,
        )
        return {"draft": draft}
    except Exception as e:
        return {
            "draft": DraftResult(
                subject="(Error)",
                body=f"Failed to generate draft: {e}",
                intent=intent,
                tone=parsed.tone,
            ),
            "errors": (state.get("errors") or []) + [str(e)],
        }
