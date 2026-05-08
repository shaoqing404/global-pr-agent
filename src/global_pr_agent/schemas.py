from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class TaskMetadata(BaseModel):
    """Basic task metadata entered by the human requester."""

    brand: str = "问界 / AITO"
    product_or_business: str = "AITO 9 / AITO 7 / AITO 5 Gulf-ready intelligent luxury SUVs"
    target_market: str = "UAE"
    target_language: str = "English"
    pr_objective: str = "Generate a localized overseas PR draft for AITO's UAE market-entry narrative."
    announcement_type: str = "Market Entry / Brand Launch"
    deadline: str = "Urgent - fast turnaround expected"

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class HumanConfirmation(BaseModel):
    """Human-confirmed PR direction after reading the information search report."""

    brand_tone: str = "premium, restrained, engineering-led, service-backed"
    product_tone: str = "intelligent new luxury SUV for Gulf family and executive mobility"
    target_audience: str = "UAE high-income families, business owners, executives, and premium SUV buyers"
    overseas_strategy_baseline: str = "From China proof to Gulf trust: combine AITO's China-market credibility with UAE local partner and service readiness."
    core_pr_angle: str = "Gulf-ready intelligent luxury for family comfort, long-distance confidence, and local service trust."
    localization_strategy: str = "Avoid confrontational language. Emphasize local partnership, Arabic/English readiness, family comfort, long-distance use, and verified service preparation."
    risk_constraints: List[str] = Field(
        default_factory=lambda: [
            "Do not describe AITO as a Huawei-owned brand.",
            "Do not call ADS self-driving or autonomous driving.",
            "Do not claim broad global rollout beyond verified markets.",
            "Do not use China sales rankings without a China-market qualifier.",
            "Do not make legal, pricing, availability, or range claims without local confirmation.",
        ]
    )
    spokesperson_direction: str = "Highlight long-term local partnership, Gulf user needs, safety, comfort, intelligence, and service readiness."
    human_notes: str = "This demo focuses on the main PR generation chain. Real legal approval is reserved for production."

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class PRInsight(BaseModel):
    brand_insight: str
    market_insight: str
    pr_narrative: str
    localization_advice: str
    risk_notes: List[str] = Field(default_factory=list)
    headline_directions: List[str] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class PRDraftPackage(BaseModel):
    title_options: List[str]
    press_release: str
    social_captions: List[str]
    media_pitch_email: str
    chinese_strategy_summary: str
    model_used: str = "local-template-fallback"
    fallback_mode: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class ExpertReview(BaseModel):
    reviewer: str
    role: str
    score: int
    strengths: List[str] = Field(default_factory=list)
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    risk_level: str = "low"

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class InformationSearchReport(BaseModel):
    """Structured report schema based on demo_inputs/information_search_report_schema.json.

    Accepts reports from different upstream agents as long as they carry enough
    recognizable content for downstream PR generation.
    """

    version: str = "information_search_report_v1"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    brand_snapshot: Dict[str, Any] = Field(default_factory=dict)
    product_offering_summary: List[Dict[str, Any]] = Field(default_factory=list)
    target_market_context: Dict[str, Any] = Field(default_factory=dict)
    competitor_landscape: List[Dict[str, Any]] = Field(default_factory=list)
    target_audience: Dict[str, Any] = Field(default_factory=dict)
    localization_strategy: Dict[str, Any] = Field(default_factory=dict)
    pr_angle_recommendation: Dict[str, Any] = Field(default_factory=dict)
    risk_register: List[Dict[str, Any]] = Field(default_factory=list)
    source_notes: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def check_minimum_content(self) -> "InformationSearchReport":
        filled_sections = sum(
            1 for field_name in ("metadata", "brand_snapshot", "target_market_context", "pr_angle_recommendation")
            if getattr(self, field_name, None)
        )
        if filled_sections < 2:
            raise ValueError(
                "报告内容不足：至少需要 metadata / brand_snapshot / target_market_context "
                "/ pr_angle_recommendation 中的 2 个 section 非空。"
            )
        return self

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class WorkflowResult(BaseModel):
    metadata: TaskMetadata
    information_report: Dict[str, Any]
    human_confirmation: HumanConfirmation
    task_plan: Dict[str, Any]
    insight: PRInsight
    draft: PRDraftPackage
    expert_reviews: List[ExpertReview] = Field(default_factory=list)
    revised_draft: Optional[str] = None
    human_feedback: str = ""
    compliance_status: str = "Verification Pass - lightweight risk notice only"
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
