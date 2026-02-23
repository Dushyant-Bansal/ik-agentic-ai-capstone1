"""Tone Stylist Agent - adjusts tone using tokenized prompts and samples."""

from pathlib import Path
from typing import Any

from email_assistant.src.models.schemas import IntentType, ToneType


def _load_tone_sample(tone: ToneType) -> str:
    """Load tone sample text if available."""
    base = Path(__file__).resolve().parent.parent.parent.parent
    sample_path = base / "email_assistant" / "data" / "tone_samples" / f"{tone.value}.txt"
    if sample_path.exists():
        return sample_path.read_text(encoding="utf-8").strip()
    return ""


_TONE_PROMPTS = {
    ToneType.FORMAL: "Use a formal, respectful tone. Avoid contractions. Use complete sentences and proper salutations.",
    ToneType.CASUAL: "Use a casual, conversational tone. Contractions and informal phrases are fine.",
    ToneType.ASSERTIVE: "Use an assertive, confident tone. Be direct and clear. Avoid hedging language.",
    ToneType.FRIENDLY: "Use a warm, friendly tone. Be approachable and personable.",
    ToneType.PROFESSIONAL: "Use a professional, balanced tone. Polite but efficient.",
}


def run(state: dict[str, Any]) -> dict[str, Any]:
    """Build tone context for the draft writer. Returns tone_context."""
    parsed = state.get("parsed_input")
    intent = state.get("intent", IntentType.OTHER)
    if not parsed:
        return {"tone_context": ""}

    tone = parsed.tone
    base_prompt = _TONE_PROMPTS.get(tone, _TONE_PROMPTS[ToneType.PROFESSIONAL])
    sample = _load_tone_sample(tone)
    if sample:
        base_prompt += f"\n\nExample of this tone:\n{sample[:500]}"
    context = f"Tone: {base_prompt}\nIntent: {intent.value}"
    return {"tone_context": context}
