"""LangGraph workflow for the AI Email Assistant."""

from typing import Any, Literal, TypedDict

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from email_assistant.src.agents import (
    draft_writer_agent,
    input_parser_agent,
    intent_detection_agent,
    personalization_agent,
    review_agent,
    router_agent,
    tone_stylist_agent,
)
from email_assistant.src.integrations.config_loader import load_mcp_config
from email_assistant.src.models.schemas import DraftResult, ReviewResult


class EmailAssistantState(TypedDict, total=False):
    """State for the email assistant pipeline."""

    raw_prompt: str
    user_tone: str
    user_recipient: str | None
    user_intent_override: str | None
    user_id: str
    parsed_input: Any
    intent: Any
    tone_context: str
    draft: Any
    personalized_draft: Any
    review_result: Any
    errors: list[str]
    retry_count: int
    retry_reason: str


def _input_parser_node(state: EmailAssistantState) -> dict[str, Any]:
    return input_parser_agent.run(dict(state))


def _intent_detection_node(state: EmailAssistantState) -> dict[str, Any]:
    return intent_detection_agent.run(dict(state))


def _tone_stylist_node(state: EmailAssistantState) -> dict[str, Any]:
    return tone_stylist_agent.run(dict(state))


def _draft_writer_node(state: EmailAssistantState) -> dict[str, Any]:
    return draft_writer_agent.run(dict(state))


def _personalization_node(state: EmailAssistantState) -> dict[str, Any]:
    return personalization_agent.run(dict(state))


def _review_node(state: EmailAssistantState) -> dict[str, Any]:
    return review_agent.run(dict(state))


def _router_node(state: EmailAssistantState) -> dict[str, Any]:
    return router_agent.run(dict(state))


def _route_after_review(state: EmailAssistantState) -> Literal["draft_writer", "__end__"]:
    """Conditional edge: retry draft or end."""
    config = load_mcp_config()
    max_retries = config.get("max_retries", 2)
    retry_count = state.get("retry_count", 0)
    review = state.get("review_result")

    if isinstance(review, ReviewResult) and not review.passed:
        if retry_count < max_retries:
            return "draft_writer"
    return "__end__"


def create_graph() -> StateGraph:
    """Build and compile the email assistant graph."""
    workflow = StateGraph(EmailAssistantState)

    workflow.add_node("input_parser", _input_parser_node)
    workflow.add_node("intent_detection", _intent_detection_node)
    workflow.add_node("tone_stylist", _tone_stylist_node)
    workflow.add_node("draft_writer", _draft_writer_node)
    workflow.add_node("personalization", _personalization_node)
    workflow.add_node("review", _review_node)
    workflow.add_node("router", _router_node)

    workflow.set_entry_point("input_parser")
    workflow.add_edge("input_parser", "intent_detection")
    workflow.add_edge("intent_detection", "tone_stylist")
    workflow.add_edge("tone_stylist", "draft_writer")
    workflow.add_edge("draft_writer", "personalization")
    workflow.add_edge("personalization", "review")
    workflow.add_edge("review", "router")
    workflow.add_conditional_edges("router", _route_after_review, {"draft_writer": "draft_writer", "__end__": END})

    return workflow


_compiled_graph = None


def get_graph():
    """Get compiled graph with optional checkpointer."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = create_graph().compile(checkpointer=MemorySaver())
    return _compiled_graph


def invoke(
    raw_prompt: str,
    user_tone: str = "professional",
    user_recipient: str | None = None,
    user_intent_override: str | None = None,
    user_id: str = "default",
) -> dict[str, Any]:
    """Run the email assistant pipeline and return final state."""
    initial: EmailAssistantState = {
        "raw_prompt": raw_prompt,
        "user_tone": user_tone,
        "user_recipient": user_recipient,
        "user_intent_override": user_intent_override,
        "user_id": user_id,
        "retry_count": 0,
    }
    graph = get_graph()
    config: dict[str, Any] = {"configurable": {"thread_id": "default"}}
    final_state = graph.invoke(initial, config)
    return dict(final_state)
