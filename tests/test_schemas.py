"""Unit tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError

from email_assistant.src.models.schemas import (
    Constraints,
    ConversationTurn,
    DraftResult,
    EmailContext,
    IntentType,
    ParsedInput,
    PriorDraftSummary,
    ReviewResult,
    StylePreferences,
    ToneType,
    UserProfile,
)


class TestIntentType:
    def test_all_values(self):
        expected = {"outreach", "follow_up", "apology", "info_request", "internal_update", "other"}
        assert {e.value for e in IntentType} == expected

    def test_from_string(self):
        assert IntentType("outreach") == IntentType.OUTREACH


class TestToneType:
    def test_all_values(self):
        expected = {"formal", "casual", "assertive", "friendly", "professional"}
        assert {e.value for e in ToneType} == expected


class TestConstraints:
    def test_defaults(self):
        c = Constraints()
        assert c.max_length is None
        assert c.language == "en"

    def test_custom(self):
        c = Constraints(max_length=200, language="fr")
        assert c.max_length == 200
        assert c.language == "fr"


class TestEmailContext:
    def test_minimal(self):
        ctx = EmailContext(prompt="Write an email")
        assert ctx.tone == ToneType.PROFESSIONAL
        assert ctx.recipient is None

    def test_full(self):
        ctx = EmailContext(
            prompt="Outreach email",
            recipient="Jane",
            tone=ToneType.FORMAL,
            intent=IntentType.OUTREACH,
            constraints=Constraints(max_length=100),
        )
        assert ctx.intent == IntentType.OUTREACH

    def test_missing_prompt_fails(self):
        with pytest.raises(ValidationError):
            EmailContext()


class TestParsedInput:
    def test_required_fields(self):
        p = ParsedInput(prompt="Test", tone=ToneType.CASUAL)
        assert p.prompt == "Test"
        assert p.tone == ToneType.CASUAL
        assert p.recipient is None
        assert p.intent_hint is None


class TestDraftResult:
    def test_basic(self):
        d = DraftResult(subject="Hi", body="Hello there")
        assert d.subject == "Hi"
        assert d.intent is None

    def test_with_metadata(self):
        d = DraftResult(
            subject="Hi",
            body="Hello",
            intent=IntentType.OUTREACH,
            tone=ToneType.FRIENDLY,
        )
        assert d.intent == IntentType.OUTREACH


class TestUserProfile:
    def test_defaults(self):
        p = UserProfile(id="u1")
        assert p.name is None
        assert p.prior_drafts == []
        assert p.conversation_history == []

    def test_round_trip_json(self):
        p = UserProfile(id="u1", name="Bob", company="X Corp")
        data = p.model_dump(mode="json")
        p2 = UserProfile(**data)
        assert p2.name == "Bob"
        assert p2.company == "X Corp"


class TestConversationTurn:
    def test_fields(self):
        t = ConversationTurn(
            prompt="Write email",
            subject="Hello",
            body="Dear all",
            intent="outreach",
            tone="formal",
        )
        assert t.prompt == "Write email"


class TestReviewResult:
    def test_passed(self):
        r = ReviewResult(passed=True)
        assert r.suggestions == []
        assert r.issues == []

    def test_failed_with_issues(self):
        r = ReviewResult(passed=False, issues=["Tone mismatch"])
        assert not r.passed
        assert len(r.issues) == 1
