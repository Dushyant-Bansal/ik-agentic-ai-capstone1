"""Unit tests for ToneStylistAgent."""

from email_assistant.src.agents.tone_stylist_agent import ToneStylistAgent
from email_assistant.src.models.schemas import IntentType, ParsedInput, ToneType, Constraints


class TestToneStylistAgent:
    def setup_method(self):
        self.agent = ToneStylistAgent()

    def test_returns_empty_when_no_parsed_input(self):
        result = self.agent.run({})
        assert result["tone_context"] == ""

    def test_formal_tone_contains_formal_instructions(self):
        parsed = ParsedInput(prompt="Write email", tone=ToneType.FORMAL, constraints=Constraints())
        state = {"parsed_input": parsed, "intent": IntentType.OUTREACH}
        result = self.agent.run(state)
        ctx = result["tone_context"]
        assert "formal" in ctx.lower()
        assert "contractions" in ctx.lower()

    def test_casual_tone_contains_casual_instructions(self):
        parsed = ParsedInput(prompt="Write email", tone=ToneType.CASUAL, constraints=Constraints())
        state = {"parsed_input": parsed, "intent": IntentType.OTHER}
        result = self.agent.run(state)
        ctx = result["tone_context"]
        assert "casual" in ctx.lower()

    def test_assertive_tone_contains_assertive_instructions(self):
        parsed = ParsedInput(prompt="Write email", tone=ToneType.ASSERTIVE, constraints=Constraints())
        state = {"parsed_input": parsed, "intent": IntentType.OTHER}
        result = self.agent.run(state)
        ctx = result["tone_context"]
        assert "assertive" in ctx.lower()
        assert "direct" in ctx.lower()

    def test_intent_included_in_context(self):
        parsed = ParsedInput(prompt="Write email", tone=ToneType.PROFESSIONAL, constraints=Constraints())
        state = {"parsed_input": parsed, "intent": IntentType.FOLLOW_UP}
        result = self.agent.run(state)
        assert "follow_up" in result["tone_context"]

    def test_all_tones_produce_nonempty_context(self):
        for tone in ToneType:
            parsed = ParsedInput(prompt="Test", tone=tone, constraints=Constraints())
            result = self.agent.run({"parsed_input": parsed, "intent": IntentType.OTHER})
            assert result["tone_context"] != ""
