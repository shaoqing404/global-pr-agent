from __future__ import annotations

import json
from typing import Any, Dict, List

from .llm_client import LLMClient
from .market import get_market_profile
from .models import BrandProfile, CampaignBrief, PRDraftResult
from .quality import check_quality


def _bullet(items: List[str]) -> str:
    return "\n".join(f"- {item}" for item in items if item)


def _safe_list(items: List[str], fallback: str) -> List[str]:
    clean = [item.strip() for item in items if item and item.strip()]
    return clean or [fallback]


def build_prompt(brand: BrandProfile, brief: CampaignBrief, market: Dict[str, Any]) -> List[Dict[str, str]]:
    system = """
You are a senior global PR strategist and AI content workflow designer.
Generate localized PR materials for overseas brand campaigns.
Be factual, media-friendly, and culturally aware. Avoid unsupported claims.
Return a complete draft in Markdown with clear sections.
""".strip()
    user = f"""
# Brand profile
{json.dumps(brand.to_dict(), ensure_ascii=False, indent=2)}

# Campaign brief
{json.dumps(brief.to_dict(), ensure_ascii=False, indent=2)}

# Target market playbook
{json.dumps(market, ensure_ascii=False, indent=2)}

# Required output
Use {brief.target_language} as the main output language unless the brief asks otherwise.
Generate:
1. Localization strategy
2. 5 title options
3. 3-5 key messages
4. Full press release with headline, dateline, lead, body, quote, availability, boilerplate, media contact placeholder
5. Social media caption
6. Short media pitch email
7. Translation and localization notes
8. Channel recommendations

Keep the tone: {brand.tone_of_voice}.
Must include: {brief.must_include}.
Must avoid: {brief.must_avoid + brand.forbidden_words}.
""".strip()
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def fallback_generate(brand: BrandProfile, brief: CampaignBrief, market: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic fallback used when no LLM API key is configured."""
    selling_points = _safe_list(brand.key_selling_points, "clear customer value")
    proof_points = _safe_list(brand.proof_points, "early customer feedback and product milestones")
    channels = market.get("channels", ["LinkedIn", "industry media"])
    style = market.get("media_style", "clear and benefit-led")
    cultural_notes = market.get("cultural_notes", [])
    risk_notes = market.get("risk_notes", [])

    title_options = [
        f"{brand.brand_name} Introduces {brand.product_name} to Help {brief.audience_segment} {brief.pr_goal}",
        f"{brand.brand_name} Expands into {brief.target_market} with {brand.product_name}",
        f"{brand.product_name} Brings {selling_points[0]} to {brief.target_market}",
        f"{brand.brand_name} Launches Localized Solution for {brief.audience_segment}",
        f"{brand.brand_name} Announces {brief.announcement_type} for {brief.target_market}",
    ]

    key_messages = [
        f"{brand.product_name} is positioned as {brand.positioning} for {brief.audience_segment}.",
        f"The campaign focuses on {brief.key_message}.",
        f"The local communication style should be {style}.",
        f"Proof should come from {proof_points[0]}.",
    ]

    localization_strategy = (
        f"For {brief.target_market}, the PR angle should connect {brand.product_name} with local customer needs. "
        f"Use a {style} tone. Cultural notes: {'; '.join(cultural_notes) or 'no special notes'}. "
        f"Risk notes: {'; '.join(risk_notes) or 'standard brand and legal review required'}."
    )

    press_release = f"""
# {title_options[0]}

**{brief.target_market}, {brand.industry} sector - [Date]** - {brand.brand_name}, {brand.positioning}, today announced {brief.announcement_type.lower()} for **{brand.product_name}**, a solution designed to help {brief.audience_segment} {brief.pr_goal}.

The announcement responds to a growing need in {brief.target_market} for solutions that are practical, localized and easy to adopt. {brand.product_name} helps customers address this need by focusing on {', '.join(selling_points[:3])}.

"{brand.product_name} was built to make {brief.key_message} more accessible for our customers," said [Spokesperson Name], [Title] at {brand.brand_name}. "As we expand in {brief.target_market}, we want to combine global product capability with local market understanding."

Key highlights include:
{_bullet(selling_points[:5])}

Supporting evidence:
{_bullet(proof_points[:5])}

The launch is designed for {brief.audience_segment}. The communication strategy should emphasize local relevance, credible proof points and clear user benefits. Recommended channels include {', '.join(channels[:4])}.

{brief.call_to_action}

## About {brand.brand_name}
{brand.brand_name} is {brand.positioning}. The company focuses on {brand.product_description}. Learn more at {brand.website or '[official website]'}.

## For media inquiries
[Media Contact Name]  
[Email]  
[Phone]
""".strip()

    social_caption = (
        f"{brand.brand_name} announces {brand.product_name} for {brief.target_market}. "
        f"Built for {brief.audience_segment}, the solution focuses on {selling_points[0]}. {brief.call_to_action}"
    )
    media_pitch_email = f"""
Subject: Story idea - {brand.brand_name} brings {brand.product_name} to {brief.target_market}

Hi [Journalist Name],

I am reaching out with a story idea about {brand.brand_name}'s {brief.announcement_type.lower()} for {brand.product_name}. The announcement may be relevant to your coverage of {brand.industry}, especially around {brief.key_message}.

The key angle is how {brand.product_name} helps {brief.audience_segment} {brief.pr_goal}, with proof points including {proof_points[0]}.

Would you be open to receiving more details or speaking with a company spokesperson?

Best,
[Your Name]
""".strip()

    translation_notes = (
        f"Primary language requested: {brief.target_language}. If publishing in local media, ask a native reviewer to verify nuance, claims, product terms and cultural references."
    )

    return {
        "localization_strategy": localization_strategy,
        "title_options": title_options,
        "key_messages": key_messages,
        "press_release": press_release,
        "social_caption": social_caption,
        "media_pitch_email": media_pitch_email,
        "translation_notes": translation_notes,
        "channel_recommendations": channels,
    }


def generate_pr_draft(
    brand: BrandProfile,
    brief: CampaignBrief,
    llm_client: LLMClient | None = None,
    force_fallback: bool = False,
) -> PRDraftResult:
    market = get_market_profile(brief.target_market)
    client = llm_client or LLMClient()

    llm_output = None
    fallback_mode = True
    model_used = "local-template-fallback"

    if not force_fallback and client.available:
        llm_output = client.chat(build_prompt(brand, brief, market), temperature=0.35)
        if llm_output and not llm_output.startswith("[LLM_CALL_FAILED]"):
            fallback_mode = False
            model_used = client.config.model

    if llm_output and not fallback_mode:
        result_payload = fallback_generate(brand, brief, market)
        # Keep platform-independent deterministic sections while using LLM as the final article body.
        result_payload["press_release"] = llm_output.strip()
        result_payload["social_caption"] = _make_social_caption_from_llm(brand, brief)
        result_payload["media_pitch_email"] = _make_pitch_email(brand, brief)
    else:
        result_payload = fallback_generate(brand, brief, market)

    issues = check_quality(brand, brief, result_payload["press_release"])

    return PRDraftResult.now(
        brand=brand,
        brief=brief,
        localization_strategy=result_payload["localization_strategy"],
        title_options=result_payload["title_options"],
        key_messages=result_payload["key_messages"],
        press_release=result_payload["press_release"],
        social_caption=result_payload["social_caption"],
        media_pitch_email=result_payload["media_pitch_email"],
        translation_notes=result_payload["translation_notes"],
        channel_recommendations=result_payload["channel_recommendations"],
        quality_issues=issues,
        model_used=model_used,
        fallback_mode=fallback_mode,
        metadata={"market_profile": market},
    )


def _make_social_caption_from_llm(brand: BrandProfile, brief: CampaignBrief) -> str:
    return (
        f"{brand.brand_name} shares new updates for {brief.target_market}: {brief.key_message}. "
        f"Designed for {brief.audience_segment}. {brief.call_to_action}"
    )


def _make_pitch_email(brand: BrandProfile, brief: CampaignBrief) -> str:
    return f"""
Subject: Local story idea - {brand.brand_name} and {brief.key_message}

Hi [Journalist Name],

I am reaching out with a localized story idea from {brand.brand_name}. The announcement focuses on {brief.key_message} for {brief.audience_segment} in {brief.target_market}.

Would you be open to reviewing the press release or speaking with a spokesperson?

Best,
[Your Name]
""".strip()
