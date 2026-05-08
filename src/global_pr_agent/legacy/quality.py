from __future__ import annotations

import re
from typing import List

from .models import BrandProfile, CampaignBrief, QualityIssue

ABSOLUTE_CLAIMS = [
    "best",
    "guaranteed",
    "number one",
    "No.1",
    "world-class",
    "全球第一",
    "最强",
    "绝对",
    "保证",
    "永久免费",
]

REQUIRED_PR_MARKERS = ["About", "Contact", "For media inquiries"]


def check_quality(brand: BrandProfile, brief: CampaignBrief, draft_text: str) -> List[QualityIssue]:
    issues: List[QualityIssue] = []
    lower = draft_text.lower()

    if brand.brand_name and brand.brand_name.lower() not in lower:
        issues.append(
            QualityIssue(
                severity="high",
                dimension="brand_consistency",
                message="PR draft does not mention the brand name clearly.",
                suggestion="Add the brand name in the headline, lead paragraph, or boilerplate.",
            )
        )

    if brand.product_name and brand.product_name.lower() not in lower:
        issues.append(
            QualityIssue(
                severity="medium",
                dimension="product_clarity",
                message="PR draft does not clearly mention the product name.",
                suggestion="Add the product name and explain what it does in one sentence.",
            )
        )

    for word in brand.forbidden_words + brief.must_avoid:
        if word and word.lower() in lower:
            issues.append(
                QualityIssue(
                    severity="high",
                    dimension="forbidden_word",
                    message=f"The draft contains forbidden or risky wording: {word}",
                    suggestion="Remove or replace the wording before external release.",
                )
            )

    for claim in ABSOLUTE_CLAIMS:
        pattern = re.escape(claim.lower())
        if re.search(pattern, lower):
            issues.append(
                QualityIssue(
                    severity="medium",
                    dimension="claim_risk",
                    message=f"Potentially absolute claim detected: {claim}",
                    suggestion="Use evidence-backed and less absolute wording.",
                )
            )

    if len(draft_text) < 800:
        issues.append(
            QualityIssue(
                severity="low",
                dimension="length",
                message="The draft may be too short for a standard press release.",
                suggestion="Add background, quote, proof points, availability, or media contact information.",
            )
        )

    if not brand.proof_points:
        issues.append(
            QualityIssue(
                severity="medium",
                dimension="evidence",
                message="No proof points were provided in the brand profile.",
                suggestion="Add data, customer examples, certifications, product specs, or launch milestones.",
            )
        )

    if brief.target_market.lower() not in lower and brief.target_market not in ["United States", "United Kingdom"]:
        issues.append(
            QualityIssue(
                severity="low",
                dimension="localization",
                message="The target market is not explicitly reflected in the draft.",
                suggestion="Add a local relevance sentence or a market-specific paragraph.",
            )
        )

    return issues


def quality_summary(issues: List[QualityIssue]) -> str:
    if not issues:
        return "No obvious quality risks detected. Manual brand/legal review is still recommended."
    lines = ["Quality review findings:"]
    for idx, issue in enumerate(issues, start=1):
        lines.append(
            f"{idx}. [{issue.severity}] {issue.dimension}: {issue.message} Suggestion: {issue.suggestion}"
        )
    return "\n".join(lines)
