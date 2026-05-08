from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from .llm_client import LLMClient
from .schemas import ExpertReview, HumanConfirmation, PRDraftPackage, PRInsight, TaskMetadata


def _contains_any(text: str, terms: List[str]) -> List[str]:
    lower = text.lower()
    return [term for term in terms if term.lower() in lower]


def content_review(draft: PRDraftPackage, insight: PRInsight, metadata: TaskMetadata) -> ExpertReview:
    text = draft.press_release
    issues: List[str] = []
    suggestions: List[str] = []
    if "About AITO" not in text and "About" not in text:
        issues.append("Missing a clear boilerplate / About section.")
        suggestions.append("Add a concise About AITO section with SERES Group and HIMA relationship wording.")
    if "[Date]" in text:
        suggestions.append("Replace [Date] with the intended release date before submission to media.")
    if "quote" not in text.lower() and "said" not in text.lower():
        issues.append("The draft may need a stronger spokesperson quote.")
    score = 88 - len(issues) * 6
    return ExpertReview(
        reviewer="Content Review Agent",
        role="Checks PR structure, clarity, newsworthiness, and completeness.",
        score=max(score, 70),
        strengths=[
            "The draft is organized around a clear market-entry story.",
            "The message connects brand, market, user value, and local readiness.",
        ],
        issues=issues or ["No blocking content-structure issue found in internal review."],
        suggestions=suggestions or ["Keep one lead angle and avoid diluting the release with too many product claims."],
        risk_level="low" if not issues else "medium",
    )


def brand_consistency_review(draft: PRDraftPackage, confirmation: HumanConfirmation) -> ExpertReview:
    text = draft.press_release
    risky = _contains_any(text, ["Huawei-owned", "Huawei owned", "Huawei's car brand", "self-driving", "autonomous driving"])
    issues = []
    suggestions = []
    if risky:
        issues.append(f"Risky brand or ADAS wording detected: {', '.join(risky)}")
        suggestions.append("Use: AITO is the premium intelligent vehicle brand under SERES Group; in China, AITO products are part of the HIMA ecosystem.")
    if "SERES" not in text and "Seres" not in text:
        issues.append("SERES Group relationship is not visible enough.")
        suggestions.append("Add SERES Group relationship in boilerplate or the second paragraph.")
    score = 92 - len(issues) * 10
    return ExpertReview(
        reviewer="Brand Consistency Agent",
        role="Checks whether wording matches the verified brand relationship, tone, and positioning.",
        score=max(score, 60),
        strengths=[
            f"The draft follows a {confirmation.brand_tone} tone direction.",
            "The core angle emphasizes intelligent new luxury rather than price competition.",
        ],
        issues=issues or ["No blocking brand-consistency issue found in internal review."],
        suggestions=suggestions or ["Keep all China-market proof points explicitly qualified by geography and segment."],
        risk_level="high" if risky else ("medium" if issues else "low"),
    )


def creative_insight_review(draft: PRDraftPackage, insight: PRInsight) -> ExpertReview:
    issues: List[str] = []
    suggestions = [
        "Lead with a Gulf use case: family comfort, executive travel, long-distance confidence, and local service trust.",
        "Use one memorable phrase consistently, such as 'From China proof to Gulf trust'.",
    ]
    if len(draft.title_options) < 3:
        issues.append("More headline alternatives would help business teams compare angles.")
    return ExpertReview(
        reviewer="Creative Insight Agent",
        role="Evaluates whether the story is distinctive, locally relevant, and media-pitchable.",
        score=90 if not issues else 82,
        strengths=[
            "The PR angle is more specific than a generic EV launch story.",
            "It turns technical intelligence into a local lifestyle and service-readiness narrative.",
        ],
        issues=issues or ["No blocking creative issue found in internal review."],
        suggestions=suggestions,
        risk_level="low",
    )


def legal_risk_review(draft: PRDraftPackage, report: Dict[str, Any]) -> ExpertReview:
    text = draft.press_release
    prohibited = [
        "global no.1",
        "world's best",
        "guaranteed",
        "zero anxiety",
        "fully autonomous",
        "self-driving",
        "already on sale in europe",
    ]
    hits = _contains_any(text, prohibited)
    issues: List[str] = []
    if hits:
        issues.append(f"Potentially unsafe or over-claiming terms detected: {', '.join(hits)}")
    risk_items = []
    for item in report.get("risk_register", [])[:4]:
        if isinstance(item, dict):
            risk_items.append(f"{item.get('risk', '')}: {item.get('mitigation', '')}")
    suggestions = risk_items or ["Run real legal review before external publication."]
    score = 94 - len(hits) * 14
    return ExpertReview(
        reviewer="Legal Risk Agent",
        role="Performs a lightweight risk screen; not a legal opinion.",
        score=max(score, 55),
        strengths=[
            "The system separates lightweight risk screening from real legal approval.",
            "The draft uses cautious launch and availability language.",
        ],
        issues=issues or ["Verification pass: no obvious prohibited wording found by internal rules."],
        suggestions=suggestions,
        risk_level="high" if hits else "low",
    )


def run_all_reviews(
    draft: PRDraftPackage,
    insight: PRInsight,
    confirmation: HumanConfirmation,
    metadata: TaskMetadata,
    report: Dict[str, Any],
    llm_client: LLMClient | None = None,
    force_fallback: bool = False,
) -> List[ExpertReview]:
    client = llm_client or LLMClient()
    if client.available and not force_fallback:
        system = (
            "You are a panel of four senior PR experts: Content, Brand, Creative, and Legal. "
            "Critically review the provided PR draft based on the PR strategy and metadata.\n"
            "Return ONLY a JSON array of exactly four objects, one for each expert.\n"
            "IMPORTANT: YOU MUST WRITE ALL FEEDBACK (role, strengths, issues, suggestions) ENTIRELY IN CHINESE. (请务必使用全中文输出所有的评价、问题和建议)。\n"
            "Each object must have the following keys:\n"
            "- reviewer: String (e.g., '内容审核专家 (Content)', '品牌一致性专家 (Brand)', '创意总监 (Creative)', '法务风控专家 (Legal)')\n"
            "- role: String (description of their focus in Chinese)\n"
            "- score: Integer (0-100, be strict, deduct points for generic EV claims, missing local nuances, or risky wording)\n"
            "- strengths: Array of Strings (Chinese)\n"
            "- issues: Array of Strings (Chinese, point out specific flaws, do not leave empty if score < 95)\n"
            "- suggestions: Array of Strings (Chinese, provide actionable fixes)\n"
            "- risk_level: String ('low', 'medium', or 'high')"
        )
        user_msg = (
            f"PR Metadata: {metadata.to_dict()}\n"
            f"Human Confirmation: {confirmation.to_dict()}\n"
            f"PR Insight: {insight.to_dict()}\n"
            f"Draft:\n{draft.press_release}"
        )
        resp = client.chat([{"role": "system", "content": system}, {"role": "user", "content": user_msg}], temperature=0.3)
        if resp and not resp.startswith("[LLM_CALL_FAILED]"):
            try:
                cleaned = resp.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
                data = json.loads(cleaned)
                if isinstance(data, list) and len(data) == 4:
                    reviews = []
                    for item in data:
                        reviews.append(ExpertReview(
                            reviewer=item.get("reviewer", "Expert"),
                            role=item.get("role", ""),
                            score=item.get("score", 85),
                            strengths=item.get("strengths", []),
                            issues=item.get("issues", []),
                            suggestions=item.get("suggestions", []),
                            risk_level=item.get("risk_level", "low"),
                        ))
                    return reviews
            except Exception:
                pass

    # Fallback to static reviews
    return [
        content_review(draft, insight, metadata),
        brand_consistency_review(draft, confirmation),
        creative_insight_review(draft, insight),
        legal_risk_review(draft, report),
    ]
