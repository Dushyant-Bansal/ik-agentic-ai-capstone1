"""Streamlit UI for the AI Email Assistant."""

import sys
from pathlib import Path

# Add repo root to path for imports
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import streamlit as st
from dotenv import load_dotenv

load_dotenv(_REPO_ROOT / ".env")

from email_assistant.src.memory.profile_store import clear_history, load_profile, save_profile
from email_assistant.src.models.schemas import DraftResult, IntentType, ToneType, UserProfile
from email_assistant.src.workflow.langgraph_flow import invoke


def main() -> None:
    st.set_page_config(
        page_title="AI Email Assistant",
        page_icon="✉️",
        layout="wide",
    )
    st.title("AI-Powered Email Assistant")
    st.caption("Generate, personalize, and validate email drafts in seconds.")

    # Session state
    if "draft_subject" not in st.session_state:
        st.session_state.draft_subject = ""
    if "draft_body" not in st.session_state:
        st.session_state.draft_body = ""
    if "profile_id" not in st.session_state:
        st.session_state.profile_id = "default"

    # Sidebar
    with st.sidebar:
        st.header("Settings")
        tone = st.selectbox(
            "Tone",
            options=[t.value for t in ToneType],
            index=[t.value for t in ToneType].index("professional"),
            help="Select the desired tone for the email.",
        )
        intent_override = st.selectbox(
            "Intent override (optional)",
            options=[""] + [t.value for t in IntentType],
            help="Override automatic intent detection.",
        )
        recipient = st.text_input(
            "Recipient (optional)",
            placeholder="e.g., John Smith, john@example.com",
            help="Recipient name or email.",
        )
        user_id = st.text_input(
            "User ID",
            value=st.session_state.profile_id,
            help="For personalization and draft history.",
        )
        st.session_state.profile_id = user_id or "default"

        with st.expander("Profile & Memory"):
            profile = load_profile(st.session_state.profile_id)
            p_name = st.text_input("Your name", value=profile.name if profile else "", key="profile_name")
            p_company = st.text_input("Company", value=profile.company if profile else "", key="profile_company")
            if st.button("Save profile", key="save_profile"):
                p = profile or UserProfile(id=st.session_state.profile_id)
                p.name = p_name or None
                p.company = p_company or None
                save_profile(p)
                st.success("Profile saved.")

            if st.button("Clear conversation history", key="clear_history_btn"):
                clear_history(st.session_state.profile_id)
                st.success("Conversation history cleared for this User ID.")

    # Main content
    prompt = st.text_area(
        "What would you like to write?",
        placeholder="e.g., Follow up on our meeting from yesterday and request the updated proposal by Friday.",
        height=120,
    )

    generate_clicked = st.button("Generate Email", type="primary")

    if generate_clicked and prompt.strip():
        with st.spinner("Generating email..."):
            try:
                result = invoke(
                    raw_prompt=prompt.strip(),
                    user_tone=tone,
                    user_recipient=recipient or None,
                    user_intent_override=intent_override or None,
                    user_id=st.session_state.profile_id,
                )
                draft = result.get("personalized_draft") or result.get("draft")
                if isinstance(draft, DraftResult):
                    st.session_state.draft_subject = draft.subject
                    st.session_state.draft_body = draft.body
                elif isinstance(draft, dict):
                    st.session_state.draft_subject = draft.get("subject", "")
                    st.session_state.draft_body = draft.get("body", "")
                else:
                    st.session_state.draft_subject = "(No subject)"
                    st.session_state.draft_body = str(draft) if draft else "No draft generated."
                errors = result.get("errors", [])
                if errors:
                    for err in errors:
                        st.warning(err)
            except Exception as e:
                st.error(f"Error: {e}")
                st.session_state.draft_subject = ""
                st.session_state.draft_body = ""

    st.divider()
    st.subheader("Email Preview")

    st.text_input(
        "Subject",
        key="draft_subject",
        placeholder="Email subject",
    )
    st.text_area(
        "Body",
        key="draft_body",
        height=300,
        placeholder="Email body will appear here after generation.",
    )

    # Export
    st.divider()
    content = f"Subject: {st.session_state.draft_subject}\n\n{st.session_state.draft_body}"
    st.download_button(
        "Export as TXT",
        data=content,
        file_name="email_draft.txt",
        mime="text/plain",
        key="dl_txt",
    )


if __name__ == "__main__":
    main()
