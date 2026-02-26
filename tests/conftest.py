"""Shared fixtures for tests."""

import json
import sys
from pathlib import Path
from typing import Any

import pytest

# Ensure the repo root is on the path
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from email_assistant.src.models.schemas import (
    Constraints,
    DraftResult,
    IntentType,
    ParsedInput,
    ToneType,
    UserProfile,
)


@pytest.fixture
def sample_parsed_input() -> ParsedInput:
    return ParsedInput(
        prompt="Follow up on our meeting and request the proposal by Friday.",
        recipient="John Smith",
        tone=ToneType.PROFESSIONAL,
        constraints=Constraints(),
    )


@pytest.fixture
def sample_draft() -> DraftResult:
    return DraftResult(
        subject="Follow-Up: Meeting Discussion",
        body="Dear John,\n\nThank you for our meeting yesterday. Could you please send the updated proposal by Friday?\n\nBest regards,",
        intent=IntentType.FOLLOW_UP,
        tone=ToneType.PROFESSIONAL,
    )


@pytest.fixture
def sample_profile(tmp_path: Path) -> UserProfile:
    return UserProfile(
        id="test_user",
        name="Alice Johnson",
        company="Acme Corp",
    )


@pytest.fixture
def tmp_profiles_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect profile_store to a temp JSON file so tests don't touch real data."""
    profiles_file = tmp_path / "user_profiles.json"
    profiles_file.write_text(json.dumps({"profiles": []}), encoding="utf-8")
    import email_assistant.src.memory.profile_store as ps
    monkeypatch.setattr(ps, "_profiles_path", lambda: profiles_file)
    return profiles_file
