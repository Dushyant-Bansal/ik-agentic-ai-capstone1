"""LLM-as-a-Judge evaluation: verify generated emails match the requested tone.

These tests call the real LLM API and cost a small amount per run.
Mark with `pytest -m eval` to run selectively.
Requires OPENAI_API_KEY in the environment.
"""

import os
import sys
from pathlib import Path

import pytest
from pydantic import BaseModel, Field

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from dotenv import load_dotenv

load_dotenv(_REPO_ROOT / ".env")

from email_assistant.src.integrations.llm_factory import get_llm
from email_assistant.src.models.schemas import ToneType
from email_assistant.src.workflow.langgraph_flow import invoke

pytestmark = pytest.mark.eval

_SKIP_REASON = "OPENAI_API_KEY not set; skipping LLM eval tests"


class ToneJudgment(BaseModel):
    """Structured response from the LLM judge."""

    matches_requested_tone: bool = Field(
        ..., description="True if the email body matches the requested tone"
    )
    detected_tone: str = Field(
        ..., description="The tone the judge detects in the email"
    )
    confidence: float = Field(
        ..., description="Confidence score 0.0-1.0"
    )
    reasoning: str = Field(
        ..., description="Brief explanation for the judgment"
    )


def _judge_tone(body: str, requested_tone: str) -> ToneJudgment:
    """Use a separate LLM call to evaluate whether body matches tone."""
    llm = get_llm(temperature=0).with_structured_output(ToneJudgment)
    prompt = f"""You are an expert email tone evaluator. Analyze the email below and determine
whether it matches the requested tone.

Requested tone: {requested_tone}

Email:
{body}

Evaluate on these criteria:
- formal: No contractions, proper salutations, respectful language
- casual: Contractions okay, conversational, informal
- assertive: Direct, confident, no hedging, action-oriented
- friendly: Warm, personable, approachable
- professional: Balanced, polite but efficient

Return your judgment with matches_requested_tone (bool), detected_tone, confidence (0-1), and reasoning."""
    return llm.invoke(prompt)


_EVAL_CASES = [
    (
        "Write an email to the engineering team announcing a code freeze before the release",
        ToneType.FORMAL,
    ),
    (
        "Ping the team about grabbing lunch together on Friday",
        ToneType.CASUAL,
    ),
    (
        "Demand an update on the overdue deliverables from the vendor",
        ToneType.ASSERTIVE,
    ),
    (
        "Thank a colleague for helping with the presentation and invite them for coffee",
        ToneType.FRIENDLY,
    ),
    (
        "Request a meeting with the client to discuss the quarterly results",
        ToneType.PROFESSIONAL,
    ),
]


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason=_SKIP_REASON)
@pytest.mark.parametrize("prompt_text,tone", _EVAL_CASES, ids=[t.value for _, t in _EVAL_CASES])
def test_generated_email_matches_tone(prompt_text: str, tone: ToneType, tmp_profiles_json):
    """Generate an email with the pipeline and have an LLM judge verify the tone."""
    result = invoke(
        raw_prompt=prompt_text,
        user_tone=tone.value,
        user_id="eval_test_user",
    )

    draft = result.get("personalized_draft") or result.get("draft")
    assert draft is not None, "Pipeline produced no draft"

    body = draft.body if hasattr(draft, "body") else draft.get("body", "")
    assert body, "Draft body is empty"

    judgment = _judge_tone(body, tone.value)

    assert judgment.matches_requested_tone, (
        f"Tone mismatch for '{tone.value}': "
        f"detected '{judgment.detected_tone}' (confidence={judgment.confidence:.2f}). "
        f"Reasoning: {judgment.reasoning}"
    )
    assert judgment.confidence >= 0.5, (
        f"Low confidence ({judgment.confidence:.2f}) for tone '{tone.value}': {judgment.reasoning}"
    )


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason=_SKIP_REASON)
def test_tone_consistency_across_retone(tmp_profiles_json):
    """Generate the same prompt with two different tones and verify they differ."""
    prompt_text = "Write an email to the team about the upcoming deadline"

    result_formal = invoke(
        raw_prompt=prompt_text,
        user_tone="formal",
        user_id="eval_consistency_user",
    )
    result_casual = invoke(
        raw_prompt=prompt_text,
        user_tone="casual",
        user_id="eval_consistency_user",
    )

    draft_formal = result_formal.get("personalized_draft") or result_formal.get("draft")
    draft_casual = result_casual.get("personalized_draft") or result_casual.get("draft")

    body_formal = draft_formal.body if hasattr(draft_formal, "body") else draft_formal.get("body", "")
    body_casual = draft_casual.body if hasattr(draft_casual, "body") else draft_casual.get("body", "")

    judgment_formal = _judge_tone(body_formal, "formal")
    judgment_casual = _judge_tone(body_casual, "casual")

    assert judgment_formal.matches_requested_tone, (
        f"Formal draft failed tone check: {judgment_formal.reasoning}"
    )
    assert judgment_casual.matches_requested_tone, (
        f"Casual draft failed tone check: {judgment_casual.reasoning}"
    )
    assert judgment_formal.detected_tone != judgment_casual.detected_tone, (
        "Both drafts detected as the same tone despite different requested tones"
    )
