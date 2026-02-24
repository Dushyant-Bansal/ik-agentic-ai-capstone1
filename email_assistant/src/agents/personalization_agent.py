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
    # Prefer explicit signature over just name if available
    signature = profile.style_preferences.signature if profile.style_preferences and profile.style_preferences.signature else profile.name

    if profile.company and "[Company]" in body:
        body = body.replace("[Company]", profile.company)

    # Always ensure a closing with signature/name when available
    if signature:
        stripped = body.rstrip()
        # Avoid duplicating signature if already present at end
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
