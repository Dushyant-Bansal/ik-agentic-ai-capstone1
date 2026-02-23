"""User profile store - load/save profiles and append drafts."""

import json
from pathlib import Path
from typing import Optional

from email_assistant.src.models.schemas import (
    PriorDraftSummary,
    UserProfile,
)


def _profiles_path() -> Path:
    return Path(__file__).resolve().parent / "user_profiles.json"


def _load_data() -> dict:
    path = _profiles_path()
    if not path.exists():
        return {"profiles": []}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save_data(data: dict) -> None:
    with open(_profiles_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_profile(user_id: str) -> Optional[UserProfile]:
    """Load user profile by ID. Returns None if not found."""
    data = _load_data()
    for p in data.get("profiles", []):
        if p.get("id") == user_id:
            return UserProfile(**p)
    return None


def save_profile(profile: UserProfile) -> None:
    """Save or update user profile."""
    data = _load_data()
    profiles = data.get("profiles", [])
    updated = False
    for i, p in enumerate(profiles):
        if p.get("id") == profile.id:
            profiles[i] = profile.model_dump(mode="json")
            updated = True
            break
    if not updated:
        profiles.append(profile.model_dump(mode="json"))
    data["profiles"] = profiles
    _save_data(data)


def append_draft(user_id: str, subject: str, intent: str, tone: str) -> None:
    """Append a draft summary to the user's prior_drafts. Creates profile if needed."""
    profile = load_profile(user_id)
    if not profile:
        profile = UserProfile(id=user_id)
    summary = PriorDraftSummary(subject=subject, intent=intent, tone=tone)
    profile.prior_drafts = (profile.prior_drafts or [])[-19:] + [summary]  # Keep last 20
    save_profile(profile)
