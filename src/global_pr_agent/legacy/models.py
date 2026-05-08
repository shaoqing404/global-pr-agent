from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class BrandProfile:
    """Brand knowledge collected from business teams."""

    brand_name: str
    industry: str
    positioning: str
    product_name: str
    product_description: str
    target_audience: str
    key_selling_points: List[str] = field(default_factory=list)
    proof_points: List[str] = field(default_factory=list)
    tone_of_voice: str = "professional, clear, media-friendly"
    forbidden_words: List[str] = field(default_factory=list)
    compliance_notes: List[str] = field(default_factory=list)
    website: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CampaignBrief:
    """PR campaign request from the front business team."""

    pr_goal: str
    target_market: str
    target_language: str
    announcement_type: str
    key_message: str
    audience_segment: str
    preferred_channels: List[str] = field(default_factory=list)
    must_include: List[str] = field(default_factory=list)
    must_avoid: List[str] = field(default_factory=list)
    length: str = "standard"
    call_to_action: str = "Learn more on the official website."
    deadline: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class QualityIssue:
    severity: str
    dimension: str
    message: str
    suggestion: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PRDraftResult:
    """Final output of the PR generation workflow."""

    brand: BrandProfile
    brief: CampaignBrief
    generated_at: str
    localization_strategy: str
    title_options: List[str]
    key_messages: List[str]
    press_release: str
    social_caption: str
    media_pitch_email: str
    translation_notes: str
    channel_recommendations: List[str]
    quality_issues: List[QualityIssue]
    model_used: str
    fallback_mode: bool = False
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def now(
        cls,
        brand: BrandProfile,
        brief: CampaignBrief,
        localization_strategy: str,
        title_options: List[str],
        key_messages: List[str],
        press_release: str,
        social_caption: str,
        media_pitch_email: str,
        translation_notes: str,
        channel_recommendations: List[str],
        quality_issues: List[QualityIssue],
        model_used: str,
        fallback_mode: bool,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "PRDraftResult":
        return cls(
            brand=brand,
            brief=brief,
            generated_at=datetime.now().isoformat(timespec="seconds"),
            localization_strategy=localization_strategy,
            title_options=title_options,
            key_messages=key_messages,
            press_release=press_release,
            social_caption=social_caption,
            media_pitch_email=media_pitch_email,
            translation_notes=translation_notes,
            channel_recommendations=channel_recommendations,
            quality_issues=quality_issues,
            model_used=model_used,
            fallback_mode=fallback_mode,
            metadata=metadata or {},
        )

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["quality_issues"] = [issue.to_dict() for issue in self.quality_issues]
        return data
