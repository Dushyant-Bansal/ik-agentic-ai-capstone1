"""Pydantic models for the AI Email Assistant."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class IntentType(str, Enum):
    """Classified intent for the email."""

    OUTREACH = "outreach"
    FOLLOW_UP = "follow_up"
    APOLOGY = "apology"
    INFO_REQUEST = "info_request"
    INTERNAL_UPDATE = "internal_update"
    OTHER = "other"


class ToneType(str, Enum):
    """Tone/style for the email."""

    FORMAL = "formal"
    CASUAL = "casual"
    ASSERTIVE = "assertive"
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"


class Constraints(BaseModel):
    """Constraints for email generation."""

    max_length: Optional[int] = Field(None, description="Maximum word or character length")
    language: str = Field(default="en", description="Language for the email")


class EmailContext(BaseModel):
    """User-provided context for email generation."""

    prompt: str = Field(..., description="Raw user prompt describing the email")
    recipient: Optional[str] = Field(None, description="Recipient name or email")
    tone: ToneType = Field(default=ToneType.PROFESSIONAL, description="Desired tone")
    intent: Optional[IntentType] = Field(None, description="Optional intent override")
    constraints: Constraints = Field(default_factory=Constraints)


class ParsedInput(BaseModel):
    """Validated and structured output from Input Parser."""

    prompt: str = Field(..., description="Validated/normalized prompt")
    recipient: Optional[str] = Field(None, description="Extracted recipient")
    tone: ToneType = Field(..., description="Extracted or inferred tone")
    constraints: Constraints = Field(default_factory=Constraints)
    intent_hint: Optional[IntentType] = Field(None, description="Initial intent hint from prompt")


class DraftResult(BaseModel):
    """Subject and body for UI display."""

    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email body text")
    intent: Optional[IntentType] = Field(None, description="Detected intent")
    tone: Optional[ToneType] = Field(None, description="Applied tone")


class StylePreferences(BaseModel):
    """User style preferences."""

    preferred_tone: Optional[ToneType] = None
    signature: Optional[str] = None
    avoid_phrases: list[str] = Field(default_factory=list)
    preferred_phrases: list[str] = Field(default_factory=list)


class PriorDraftSummary(BaseModel):
    """Summary of a prior draft for memory."""

    subject: str = Field(...)
    intent: str = Field(...)
    tone: str = Field(...)


class UserProfile(BaseModel):
    """User profile for personalization."""

    id: str = Field(..., description="Unique user identifier")
    name: Optional[str] = Field(None, description="User name")
    company: Optional[str] = Field(None, description="Company name")
    style_preferences: StylePreferences = Field(default_factory=StylePreferences)
    prior_drafts: list[PriorDraftSummary] = Field(default_factory=list)


class ReviewResult(BaseModel):
    """Output from Review & Validator Agent."""

    passed: bool = Field(..., description="Whether validation passed")
    suggestions: list[str] = Field(default_factory=list, description="Suggested edits")
    issues: list[str] = Field(default_factory=list, description="Detected issues")
