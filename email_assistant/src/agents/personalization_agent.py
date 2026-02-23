"""Personalization Agent - injects user profile data into draft."""

from typing import Any

from email_assistant.src.memory.profile_store import load_profile
from email_assistant.src.models.schemas import DraftResult, UserProfile


def run(state: dict[str, Any]) -> dict[str, Any]:
    """Personalize draft with user profile. Returns personalized_draft."""
    draft = state.get("draft")
    user_id = state.get("user_id", "default")

    if not draft or not isinstance(draft, DraftResult):
        return {"personalized_draft": draft}

    profile = load_profile(user_id)
    if not profile or (not profile.name and not profile.company and not profile.style_preferences):
        return {"personalized_draft": draft}

    body = draft.body
    changes = []

    if profile.name:
        if "Best regards" in body or "Regards," in body or "Sincerely" in body:
            body = body.rstrip()
            if not body.endswith(profile.name):
                body += f"\n\n{profile.name}"
                changes.append("added_signature")
        changes.append("name_used")

    if profile.company and "[Company]" in body:
        body = body.replace("[Company]", profile.company)
        changes.append("company_injected")

    personalized = DraftResult(
        subject=draft.subject,
        body=body,
        intent=draft.intent,
        tone=draft.tone,
    )
    return {"personalized_draft": personalized}
