"""Router & Memory Agent - fallback, retry logic, log drafts, update profile."""

from typing import Any

from email_assistant.src.integrations.config_loader import load_mcp_config
from email_assistant.src.memory.profile_store import append_conversation, append_draft
from email_assistant.src.models.schemas import DraftResult, ReviewResult


class RouterAgent:
    """Logs drafts to memory, decides whether to retry or finish."""

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        config = load_mcp_config()
        max_retries = config.get("max_retries", 2)
        retry_count = state.get("retry_count", 0)
        review = state.get("review_result")
        draft = state.get("personalized_draft") or state.get("draft")
        user_id = state.get("user_id", "default")

        if draft and isinstance(draft, DraftResult):
            intent_val = draft.intent.value if draft.intent else "other"
            tone_val = draft.tone.value if draft.tone else "professional"

            append_draft(
                user_id=user_id,
                subject=draft.subject,
                intent=intent_val,
                tone=tone_val,
            )

            raw_prompt = state.get("raw_prompt") or ""
            append_conversation(
                user_id=user_id,
                prompt=str(raw_prompt),
                subject=draft.subject,
                body=draft.body,
                intent=intent_val,
                tone=tone_val,
            )

        should_retry = False
        if isinstance(review, ReviewResult) and not review.passed:
            if retry_count < max_retries:
                should_retry = True

        updates: dict[str, Any] = {"retry_count": retry_count + (1 if should_retry else 0)}
        if should_retry:
            updates["retry_reason"] = "; ".join((review.issues or [])[:3])

        return updates
