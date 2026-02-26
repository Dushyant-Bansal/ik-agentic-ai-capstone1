"""Personalization Agent - injects user profile data into draft."""

from typing import Any

from email_assistant.src.memory.profile_store import load_profile
from email_assistant.src.models.schemas import DraftResult


class PersonalizationAgent:
    """Applies user profile data (name, company, signature) to the draft."""

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        draft = state.get("draft")
        user_id = state.get("user_id", "default")

        if not draft or not isinstance(draft, DraftResult):
            return {"personalized_draft": draft}

        profile = load_profile(user_id)
        if not profile or (not profile.name and not profile.company and not profile.style_preferences):
            return {"personalized_draft": draft}

        body = draft.body
        signature = (
            profile.style_preferences.signature
            if profile.style_preferences and profile.style_preferences.signature
            else profile.name
        )

        if profile.company and "[Company]" in body:
            body = body.replace("[Company]", profile.company)

        # Strip common LLM placeholder tokens
        _PLACEHOLDERS = [
            "[Your Name]", "[Name]", "[Sender Name]", "[Sender]",
            "[Your Full Name]", "[Full Name]", "[Insert Name]",
        ]
        for ph in _PLACEHOLDERS:
            if ph in body:
                body = body.replace(ph, signature or "")

        if signature:
            stripped = body.rstrip()
            if not stripped.endswith(signature):
                body = f"{stripped}\n\n{signature}"
            else:
                body = stripped

        personalized = DraftResult(
            subject=draft.subject,
            body=body,
            intent=draft.intent,
            tone=draft.tone,
        )
        return {"personalized_draft": personalized}
