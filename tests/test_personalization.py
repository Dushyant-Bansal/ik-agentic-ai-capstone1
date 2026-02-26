"""Unit tests for PersonalizationAgent."""

from pathlib import Path

from email_assistant.src.agents.personalization_agent import PersonalizationAgent
from email_assistant.src.memory.profile_store import save_profile
from email_assistant.src.models.schemas import (
    DraftResult,
    IntentType,
    StylePreferences,
    ToneType,
    UserProfile,
)


class TestPersonalizationAgent:
    def setup_method(self):
        self.agent = PersonalizationAgent()

    def test_no_draft_returns_as_is(self):
        result = self.agent.run({"draft": None, "user_id": "x"})
        assert result["personalized_draft"] is None

    def test_no_profile_returns_draft_unchanged(self, tmp_profiles_json: Path):
        draft = DraftResult(subject="Hi", body="Hello there\n\nBest,", intent=IntentType.OTHER, tone=ToneType.CASUAL)
        result = self.agent.run({"draft": draft, "user_id": "nonexistent"})
        assert result["personalized_draft"].body == draft.body

    def test_appends_name(self, tmp_profiles_json: Path):
        save_profile(UserProfile(id="u1", name="Alice"))
        draft = DraftResult(subject="Hi", body="Hello there\n\nBest regards,", intent=IntentType.OTHER, tone=ToneType.FORMAL)
        result = self.agent.run({"draft": draft, "user_id": "u1"})
        assert result["personalized_draft"].body.endswith("Alice")

    def test_uses_custom_signature_over_name(self, tmp_profiles_json: Path):
        profile = UserProfile(
            id="u2",
            name="Bob",
            style_preferences=StylePreferences(signature="-- Bob from Sales"),
        )
        save_profile(profile)
        draft = DraftResult(subject="Hi", body="Hello", intent=IntentType.OTHER, tone=ToneType.CASUAL)
        result = self.agent.run({"draft": draft, "user_id": "u2"})
        assert result["personalized_draft"].body.endswith("-- Bob from Sales")

    def test_no_duplicate_signature(self, tmp_profiles_json: Path):
        save_profile(UserProfile(id="u3", name="Charlie"))
        draft = DraftResult(subject="Hi", body="Hello\n\nCharlie", intent=IntentType.OTHER, tone=ToneType.CASUAL)
        result = self.agent.run({"draft": draft, "user_id": "u3"})
        assert result["personalized_draft"].body.count("Charlie") == 1

    def test_company_replacement(self, tmp_profiles_json: Path):
        save_profile(UserProfile(id="u4", name="Dan", company="Acme"))
        draft = DraftResult(subject="Hi", body="I work at [Company].", intent=IntentType.OTHER, tone=ToneType.PROFESSIONAL)
        result = self.agent.run({"draft": draft, "user_id": "u4"})
        assert "Acme" in result["personalized_draft"].body
        assert "[Company]" not in result["personalized_draft"].body

    def test_replaces_your_name_placeholder(self, tmp_profiles_json: Path):
        save_profile(UserProfile(id="u5", name="Eve"))
        draft = DraftResult(
            subject="Hi",
            body="Best regards,\n[Your Name]",
            intent=IntentType.OTHER,
            tone=ToneType.FORMAL,
        )
        result = self.agent.run({"draft": draft, "user_id": "u5"})
        body = result["personalized_draft"].body
        assert "[Your Name]" not in body
        assert "Eve" in body

    def test_replaces_sender_name_placeholder(self, tmp_profiles_json: Path):
        save_profile(UserProfile(id="u6", name="Frank"))
        draft = DraftResult(
            subject="Hi",
            body="Kind regards,\n[Sender Name]",
            intent=IntentType.OTHER,
            tone=ToneType.PROFESSIONAL,
        )
        result = self.agent.run({"draft": draft, "user_id": "u6"})
        body = result["personalized_draft"].body
        assert "[Sender Name]" not in body
        assert "Frank" in body

    def test_replaces_name_placeholder(self, tmp_profiles_json: Path):
        save_profile(UserProfile(id="u7", name="Grace"))
        draft = DraftResult(
            subject="Hi",
            body="Thanks,\n[Name]",
            intent=IntentType.OTHER,
            tone=ToneType.CASUAL,
        )
        result = self.agent.run({"draft": draft, "user_id": "u7"})
        body = result["personalized_draft"].body
        assert "[Name]" not in body
        assert "Grace" in body
