"""Draft Writer Agent - generates subject and body with tone-aware templates."""

from typing import Any

from pydantic import BaseModel, Field

from email_assistant.src.integrations.llm_factory import get_llm
from email_assistant.src.memory.profile_store import load_profile
from email_assistant.src.models.schemas import DraftResult, IntentType, ToneType


class _DraftOutput(BaseModel):
    """LLM structured output for draft."""

    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email body text")


class DraftWriterAgent:
    """Generates an email draft using LLM with tone and conversation context."""

    def _build_conversation_context(self, user_id: str) -> str:
        profile = load_profile(user_id)
        if not profile or not profile.conversation_history:
            return ""
        recent = profile.conversation_history[-3:]
        formatted = [
            f"- Prompt: {turn.prompt[:120]}... | Subject: {turn.subject[:80]}... | Intent: {turn.intent} | Tone: {turn.tone}"
            for turn in recent
        ]
        return (
            "Here are some of this user's recent email interactions. "
            "Keep tone and style consistent where appropriate:\n"
            + "\n".join(formatted)
            + "\n\n"
        )

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        parsed = state.get("parsed_input")
        intent = state.get("intent", IntentType.OTHER)
        tone_context = state.get("tone_context", "")
        user_id = state.get("user_id", "default")

        if not parsed:
            return {
                "draft": DraftResult(
                    subject="(No subject)",
                    body="Please provide a prompt.",
                    intent=intent,
                    tone=None,
                ),
            }

        llm = get_llm(temperature=0.7).with_structured_output(_DraftOutput)
        recipient = f" Recipient: {parsed.recipient}" if parsed.recipient else ""
        length_hint = ""
        if parsed.constraints.max_length:
            length_hint = f" Keep the email under {parsed.constraints.max_length} words."

        conversation_snippets = self._build_conversation_context(user_id)

        profile = load_profile(user_id)
        sender_info = ""
        if profile:
            name = profile.style_preferences.signature if profile.style_preferences and profile.style_preferences.signature else profile.name
            if name:
                sender_info = f"\nThe sender's name is: {name}. Use this name in the signoff -- do NOT use placeholders like [Your Name]."
            if profile.company:
                sender_info += f"\nThe sender's company is: {profile.company}. Use this instead of any [Company] placeholder."

        prompt = f"""Write a complete email based on this request.

{parsed.prompt}{recipient}

{tone_context}{length_hint}
{sender_info}

{conversation_snippets}Output a subject line and full body. Use proper email format (greeting, body, closing).
Do NOT include any placeholder text like [Your Name], [Name], [Sender Name], [Company], etc."""

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
