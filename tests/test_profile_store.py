"""Unit tests for profile_store memory layer."""

from pathlib import Path

from email_assistant.src.memory.profile_store import (
    append_conversation,
    append_draft,
    clear_history,
    load_profile,
    save_profile,
)
from email_assistant.src.models.schemas import UserProfile


class TestLoadSaveProfile:
    def test_load_nonexistent_returns_none(self, tmp_profiles_json: Path):
        assert load_profile("nonexistent") is None

    def test_save_and_load(self, tmp_profiles_json: Path):
        p = UserProfile(id="u1", name="Alice", company="Acme")
        save_profile(p)
        loaded = load_profile("u1")
        assert loaded is not None
        assert loaded.name == "Alice"
        assert loaded.company == "Acme"

    def test_update_existing_profile(self, tmp_profiles_json: Path):
        p = UserProfile(id="u1", name="Alice")
        save_profile(p)
        p.name = "Alice Updated"
        save_profile(p)
        loaded = load_profile("u1")
        assert loaded.name == "Alice Updated"


class TestAppendDraft:
    def test_creates_profile_if_missing(self, tmp_profiles_json: Path):
        append_draft("new_user", "Subject", "outreach", "formal")
        profile = load_profile("new_user")
        assert profile is not None
        assert len(profile.prior_drafts) == 1
        assert profile.prior_drafts[0].subject == "Subject"

    def test_keeps_max_20(self, tmp_profiles_json: Path):
        for i in range(25):
            append_draft("u1", f"Draft {i}", "other", "casual")
        profile = load_profile("u1")
        assert len(profile.prior_drafts) == 20


class TestAppendConversation:
    def test_appends_turn(self, tmp_profiles_json: Path):
        append_conversation("u1", "Write email", "Hello", "Body", "outreach", "formal")
        profile = load_profile("u1")
        assert len(profile.conversation_history) == 1
        assert profile.conversation_history[0].prompt == "Write email"

    def test_keeps_max_10(self, tmp_profiles_json: Path):
        for i in range(15):
            append_conversation("u1", f"prompt {i}", f"subj {i}", f"body {i}", "other", "casual")
        profile = load_profile("u1")
        assert len(profile.conversation_history) == 10


class TestClearHistory:
    def test_clears_all(self, tmp_profiles_json: Path):
        append_draft("u1", "Draft", "outreach", "formal")
        append_conversation("u1", "prompt", "subj", "body", "outreach", "formal")
        clear_history("u1")
        profile = load_profile("u1")
        assert profile.prior_drafts == []
        assert profile.conversation_history == []

    def test_noop_for_missing_user(self, tmp_profiles_json: Path):
        clear_history("nonexistent")  # should not raise
