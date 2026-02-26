"""Review & Validator Agent - checks grammar, tone alignment, coherence."""

from typing import Any

from pydantic import BaseModel, Field

from email_assistant.src.integrations.llm_factory import get_llm
from email_assistant.src.models.schemas import DraftResult, ReviewResult


class _ReviewOutput(BaseModel):
    """LLM structured output for review."""

    passed: bool = Field(..., description="Whether the draft passes validation")
    suggestions: list[str] = Field(default_factory=list, description="Suggested edits")
    issues: list[str] = Field(default_factory=list, description="Detected issues")


class ReviewAgent:
    """Reviews draft for grammar, tone alignment, and coherence."""

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        draft = state.get("personalized_draft") or state.get("draft")
        tone_context = state.get("tone_context", "")

        if not draft:
            return {"review_result": ReviewResult(passed=False, issues=["No draft to review"])}

        if not isinstance(draft, DraftResult):
            return {"review_result": ReviewResult(passed=True)}

        llm = get_llm(temperature=0).with_structured_output(_ReviewOutput)
        prompt = f"""Review this email draft for:
1. Grammar and spelling
2. Tone alignment (expected: {tone_context[:200] if tone_context else "professional"})
3. Contextual coherence and clarity

Subject: {draft.subject}

Body:
{draft.body}

Return: passed (bool), suggestions (list of strings), issues (list of strings).
Be lenient - only fail for clear grammar errors or major tone mismatch."""

        try:
            out = llm.invoke(prompt)
            return {
                "review_result": ReviewResult(
                    passed=out.passed,
                    suggestions=out.suggestions or [],
                    issues=out.issues or [],
                ),
            }
        except Exception:
            return {"review_result": ReviewResult(passed=True)}
