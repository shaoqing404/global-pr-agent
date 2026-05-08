from __future__ import annotations

import json
from typing import Any, Dict, List

from .llm_client import LLMClient
from .reviewers import run_all_reviews
from .schemas import HumanConfirmation, PRDraftPackage, PRInsight, TaskMetadata, WorkflowResult


def _list_text(items: Any, limit: int = 5) -> str:
    if isinstance(items, list):
        clean = [str(item) for item in items if item]
    elif isinstance(items, str) and items.strip():
        clean = [items.strip()]
    else:
        clean = []
    return "\n".join(f"- {item}" for item in clean[:limit]) or "- N/A"


def _field(obj: Dict[str, Any], key: str, default: str = "") -> str:
    value = obj.get(key, default)
    if isinstance(value, list):
        return "; ".join(str(v) for v in value[:5])
    if value is None:
        return default
    return str(value)


def _safe_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def run_task_planning(
    metadata: TaskMetadata,
    report: Dict[str, Any] | None = None,
    llm_client: LLMClient | None = None,
    force_fallback: bool = False,
) -> Dict[str, Any]:
    """Generate clarification questions and a task plan.

    When an LLM is available, questions are generated dynamically based on the
    user's actual task input.  Falls back to curated static questions otherwise.
    """
    report = report or {}
    summary = report.get("pr_angle_recommendation", {})

    # ── LLM-powered clarification questions ───────────────────────────────────
    questions = None
    client = llm_client or LLMClient()
    if client.available and not force_fallback:
        system = (
            "You are a senior global PR strategist. The user wants to create a "
            "localized overseas PR draft. Based on the task metadata and any "
            "available research report, generate 5-7 sharp clarification "
            "questions that a PR director would ask before starting work.\n"
            "Return ONLY a JSON array of strings (the questions). No markdown, "
            "no explanation, just the JSON array. 请务必使用中文输出这些问题。"
        )
        user_msg = (
            f"Task metadata:\n{_safe_json(metadata.to_dict())}\n\n"
            f"Research report summary (may be empty):\n"
            f"{_safe_json({k: report.get(k) for k in ('metadata', 'brand_snapshot', 'target_market_context', 'pr_angle_recommendation') if report.get(k)})}"
        )
        resp = client.chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user_msg}],
            temperature=0.4,
        )
        if resp and not resp.startswith("[LLM_CALL_FAILED]"):
            try:
                cleaned = resp.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
                questions = json.loads(cleaned)
            except Exception:
                questions = None

    # ── Fallback static questions ─────────────────────────────────────────────
    if not questions:
        questions = [
            "本次 PR 是品牌进入市场、产品发布、渠道合作，还是媒体试驾前置稿？",
            "是否以 AITO 9 作为主角，AITO 7 / 5 作为产品矩阵补充？",
            "是否允许引用中国市场成绩？如果允许，必须加中国市场与细分市场限定。",
            "是否有 UAE 本地价格、交付时间、体验中心开业时间等可公开信息？",
            "英文稿是否需要同步准备阿拉伯语短标题或社媒素材？",
        ]

    plan = [
        {"step": 0, "name": "Task Start", "status": "done", "output": "Task metadata and clarification questions"},
        {"step": 1, "name": "Information Search Agent Report", "status": "done", "output": "DeepResearch report loaded as upstream intelligence"},
        {"step": 2, "name": "Human Confirmation", "status": "pending", "output": "Brand tone, PR angle, risk constraints"},
        {"step": 3, "name": "PR Director Insight", "status": "pending", "output": "Narrative direction and localization advice"},
        {"step": 4, "name": "PR Draft Generation", "status": "pending", "output": "Press release, headlines, captions, pitch email"},
        {"step": 4.1, "name": "Specialist Review", "status": "pending", "output": "Content, brand, creative, legal-risk feedback"},
        {"step": 4.2, "name": "Human Feedback Revision", "status": "pending", "output": "Revised draft"},
        {"step": 5, "name": "Compliance Gate", "status": "demo_pass", "output": "Lightweight demo notice; real legal review reserved"},
    ]
    return {
        "clarification_questions": questions,
        "task_plan": plan,
        "initial_strategy_hint": summary.get("recommended_main_angle", "Use DeepResearch report to define a localized PR angle before drafting."),
    }


def build_insight_prompt(metadata: TaskMetadata, report: Dict[str, Any], confirmation: HumanConfirmation) -> List[Dict[str, str]]:
    system = """
You are a senior PR Director for overseas brand launches. Convert research and human confirmation into strategic PR insight. Be factual, restrained, and suitable for a premium overseas automotive brand. Return Markdown only.
""".strip()
    user = f"""
# Task metadata
{_safe_json(metadata.to_dict())}

# Information Search Agent Report
{_safe_json(report)}

# Human confirmation
{_safe_json(confirmation.to_dict())}

Generate:
1. Brand insight
2. Market insight
3. PR narrative recommendation
4. Localization advice
5. Risk notes
6. Headline directions
""".strip()
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def run_pr_director_insight(
    metadata: TaskMetadata,
    report: Dict[str, Any],
    confirmation: HumanConfirmation,
    llm_client: LLMClient | None = None,
    force_fallback: bool = False,
) -> PRInsight:
    client = llm_client or LLMClient()
    if client.available and not force_fallback:
        system = (
            "You are a PR Director. Provide strategic insights based on the user's PR brief.\n"
            "Return ONLY a JSON object with these keys:\n"
            "- brand_insight (String)\n"
            "- market_insight (String)\n"
            "- pr_narrative (String)\n"
            "- localization_advice (String)\n"
            "- risk_notes (Array of Strings)\n"
            "- headline_directions (Array of Strings)\n"
            "IMPORTANT: Always output values entirely in Chinese. (请务必使用全中文输出)"
        )
        user = f"Metadata: {metadata.to_dict()}\nReport: {report}\nConfirmation: {confirmation.to_dict()}"
        output = client.chat([{"role": "system", "content": system}, {"role": "user", "content": user}], temperature=0.25)
        if output and not output.startswith("[LLM_CALL_FAILED]"):
            try:
                cleaned = output.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
                data = json.loads(cleaned)
                return PRInsight(
                    brand_insight=data.get("brand_insight", ""),
                    market_insight=data.get("market_insight", ""),
                    pr_narrative=data.get("pr_narrative", ""),
                    localization_advice=data.get("localization_advice", ""),
                    risk_notes=data.get("risk_notes", confirmation.risk_constraints),
                    headline_directions=data.get("headline_directions", []),
                )
            except Exception:
                pass

    # Fallback
    brand = report.get("brand_snapshot", {})
    market = report.get("target_market_context", {})
    angle = report.get("pr_angle_recommendation", {})
    local = report.get("localization_strategy", {})
    return PRInsight(
        brand_insight=(
            "AITO should not be positioned as a generic Chinese EV exporter. The stronger narrative is a premium intelligent vehicle brand "
            "under SERES Group, connected with the HIMA ecosystem in China, translating China-market product proof into Gulf-market trust. "
        ),
        market_insight=(
            "UAE is the strongest demo market because the report shows verified market-entry signals, local partner readiness, premium SUV demand, "
            "and a media environment that is open to Chinese intelligent vehicles but cautious about resale value, service stability, and over-claims. "
        ),
        pr_narrative=angle.get("recommended_main_angle", confirmation.core_pr_angle),
        localization_advice=confirmation.localization_strategy,
        risk_notes=confirmation.risk_constraints,
        headline_directions=angle.get("suggested_headline_directions", ["Gulf-ready intelligent luxury for UAE families"]),
    )




def build_generation_prompt(metadata: TaskMetadata, report: Dict[str, Any], confirmation: HumanConfirmation, insight: PRInsight) -> List[Dict[str, str]]:
    system = """
You are a global PR writer. Generate a localized English press release for a premium intelligent vehicle brand entering the UAE. Avoid unsupported claims, absolute terms, autonomous-driving wording, and incorrect Huawei ownership wording.
""".strip()
    user = f"""
# Metadata
{_safe_json(metadata.to_dict())}

# Report
{_safe_json(report)}

# Human confirmation
{_safe_json(confirmation.to_dict())}

# PR Director Insight
{_safe_json(insight.to_dict())}

Output:
- 5 headline options
- Full English press release with dateline, lead, body, quote, local service paragraph, about section, media contact placeholder
- 3 social captions
- Media pitch email
- Chinese strategy summary
""".strip()
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _fallback_press_release(metadata: TaskMetadata, report: Dict[str, Any], confirmation: HumanConfirmation, insight: PRInsight) -> str:
    brand = report.get("brand_snapshot", {})
    market = report.get("target_market_context", {})
    products = report.get("product_offering_summary", [])
    product_names = ", ".join(item.get("product_name", "") for item in products[:3] if isinstance(item, dict)) or "AITO 9, AITO 7 and AITO 5"
    service_signal = "UAE local partner, delivery, after-sales, central warehouse and supply-chain readiness"
    return f"""
# AITO Brings Gulf-Ready Intelligent Luxury SUV Experience to the UAE

**Dubai, UAE - [Date]** - AITO, the premium intelligent vehicle brand under SERES Group, is preparing to bring its intelligent luxury SUV experience to the UAE, with a localized market approach built around family comfort, executive mobility, advanced driver assistance, and local service readiness.

The UAE launch narrative centers on {product_names}, a product family designed to combine spacious SUV comfort, intelligent cabin experiences, safety-focused driver assistance, and long-distance confidence for Gulf users. Rather than introducing a vehicle as a simple export product, AITO's UAE story is about adapting intelligent new luxury to local expectations around family travel, high-temperature environments, premium service, and trusted ownership support.

"The UAE is one of the most important markets for intelligent luxury mobility in the Gulf," said [Spokesperson Name], [Title]. "Our priority is not only to introduce advanced products, but also to work with local partners to build a long-term ownership experience around safety, comfort, intelligent features, and service confidence."

According to the prepared market intelligence, UAE premium SUV buyers are increasingly open to new intelligent vehicle choices, while still placing strong emphasis on after-sales service, parts availability, resale confidence, and real-world usability. AITO's communication strategy should therefore connect China-market product proof with local trust-building, including partner support, Gulf-ready localization, and a restrained premium tone.

The localized PR direction emphasizes three messages:

1. **Intelligent new luxury for Gulf families and executives** - AITO should be presented as a premium SUV experience that brings together comfort, safety, digital cabin features, and advanced driver assistance.
2. **From China proof to Gulf trust** - China-market recognition may be used as credibility, but every ranking or delivery proof point should be clearly qualified by market and segment.
3. **Local readiness matters** - The UAE story should highlight verified local cooperation, customer touchpoints, and service preparation instead of relying only on technology claims.

AITO should avoid describing its advanced driver assistance capabilities as autonomous driving. All local feature availability, range, configuration, delivery timing, and pricing should be subject to official local confirmation and applicable regulations.

The first phase of communication is recommended for automotive, business, technology, and premium lifestyle media, supported by dealer-led test-drive experiences and localized digital content for English and Arabic-speaking audiences.

## About AITO
AITO is the premium intelligent vehicle brand under SERES Group. In China, AITO products are part of the HIMA ecosystem. The brand focuses on combining vehicle engineering, intelligent cabin experiences, advanced driver assistance, safety, and premium comfort for next-generation mobility users.

## Media Contact
[Media Contact Name]\n[Email]\n[Phone]
""".strip()


def run_pr_generation(
    metadata: TaskMetadata,
    report: Dict[str, Any],
    confirmation: HumanConfirmation,
    insight: PRInsight,
    llm_client: LLMClient | None = None,
    force_fallback: bool = False,
) -> PRDraftPackage:
    client = llm_client or LLMClient()
    
    if client.available and not force_fallback:
        system = (
            "You are a global PR writer. Generate a localized English press release package.\n"
            "Return ONLY a JSON object with the following keys:\n"
            "- title_options (Array of Strings: 5 headline options)\n"
            "- press_release (String: the full body of the release)\n"
            "- social_captions (Array of Strings: 3 social media captions)\n"
            "- media_pitch_email (String: the pitch email to journalists)\n"
            "- chinese_strategy_summary (String: a summary of the strategy in Chinese)"
        )
        user = f"Metadata: {metadata.to_dict()}\nReport: {report}\nConfirmation: {confirmation.to_dict()}\nInsight: {insight.to_dict()}"
        
        output = client.chat([{"role": "system", "content": system}, {"role": "user", "content": user}], temperature=0.3)
        if output and not output.startswith("[LLM_CALL_FAILED]"):
            try:
                cleaned = output.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
                data = json.loads(cleaned)
                return PRDraftPackage(
                    title_options=data.get("title_options", ["Draft Title"]),
                    press_release=data.get("press_release", ""),
                    social_captions=data.get("social_captions", []),
                    media_pitch_email=data.get("media_pitch_email", ""),
                    chinese_strategy_summary=data.get("chinese_strategy_summary", ""),
                    model_used=client.config.model,
                    fallback_mode=False
                )
            except Exception:
                pass

    # Fallback to static text
    press_release = _fallback_press_release(metadata, report, confirmation, insight)
    headline_base = insight.headline_directions or []
    title_options = [
        "AITO Brings Gulf-Ready Intelligent Luxury SUV Experience to the UAE",
        "From China Proof to Gulf Trust: AITO Prepares a Localized UAE Luxury SUV Story",
        "AITO Introduces a New Intelligent Luxury Narrative for UAE Families and Executives",
        "Gulf-Ready by Design: AITO Focuses on Comfort, Intelligence, and Local Service Confidence",
        "AITO Sets Out a Premium, Service-Backed Approach for the UAE Intelligent SUV Market",
    ]
    for item in headline_base:
        text = str(item).strip()
        if text and text not in title_options:
            title_options.append(text)
    title_options = title_options[:5]
    
    captions = [
        "AITO's UAE story is not only about intelligent vehicles. It is about building Gulf-ready luxury around family comfort, advanced assistance, and local service trust.",
        "From China proof to Gulf trust: AITO is preparing a localized intelligent luxury SUV narrative for UAE premium mobility users.",
        "For UAE families and executives, intelligent luxury must feel comfortable, useful, and locally supported. That is the PR direction behind AITO's Gulf-ready story.",
    ]
    email = (
        "Hi [Name],\n\n"
        "AITO is bringing its intelligent premium SUV experience to the UAE. "
        "Unlike generic EV narratives, our story connects China-market product proof with Gulf-ready family comfort, "
        "advanced assistance, and local service trust.\n\n"
        "Would you be interested in learning more about how AITO is translating technical intelligence into a premium ownership experience?"
    )
    summary = "本次 PR 核心策略：通过突出智能化、家庭舒适与本地服务落地，将中国市场背书转化为海湾市场的信任。弱化价格战，强调长期拥有价值与产品可靠性。"
    return PRDraftPackage(
        title_options=title_options,
        press_release=press_release,
        social_captions=captions,
        media_pitch_email=email,
        chinese_strategy_summary=summary,
        model_used="local-template-fallback",
        fallback_mode=not client.available or force_fallback,
    )


def run_revision(
    draft: PRDraftPackage,
    human_feedback: str,
    llm_client: LLMClient | None = None,
    force_fallback: bool = False,
) -> str:
    """Revise or translate the PR draft based on human feedback.

    If an LLM is available, the full draft and feedback are sent to the model so
    it can rewrite, shorten, translate, or localize the content as instructed.
    Falls back to a deterministic template-append when no API key is configured.
    """
    feedback = human_feedback.strip()
    if not feedback:
        return draft.press_release

    client = llm_client or LLMClient()
    if client.available and not force_fallback:
        # Detect translation intent for a more targeted system prompt
        translation_keywords = [
            "翻译", "translate", "arabic", "阿拉伯", "french", "法语",
            "german", "德语", "japanese", "日语", "korean", "韩语",
            "spanish", "西班牙", "localize", "本土化",
        ]
        is_translation = any(kw in feedback.lower() for kw in translation_keywords)
        if is_translation:
            system_msg = (
                "You are a professional PR localization specialist. "
                "Translate and culturally adapt the provided press release according to the user's instruction. "
                "Preserve the structure, factual accuracy, and brand tone. "
                "Output the translated/localized version only, in Markdown."
            )
        else:
            system_msg = (
                "You are a senior PR editor. Revise the provided press release based on the user's feedback. "
                "Maintain brand tone, factual accuracy, and professional quality. "
                "Output the revised press release only, in Markdown."
            )
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": f"Original press release:\n\n{draft.press_release}\n\nFeedback / Instruction:\n{feedback}"},
        ]
        result = client.chat(messages, temperature=0.3)
        if result and not result.startswith("[LLM_CALL_FAILED]"):
            return result.strip()

    # ── Deterministic fallback ────────────────────────────────────────────────
    header = "## REVISED DRAFT (Based on Human Feedback)\n\n"
    note = (
        f"> **Applied Feedback:** {feedback}\n>"
        "\n> *Note: Configure LLM_API_KEY to enable AI-powered revision and translation.*\n\n"
    )
    return header + note + draft.press_release.strip()


def _completed_task_plan(metadata: TaskMetadata, report: Dict[str, Any], has_feedback: bool) -> Dict[str, Any]:
    plan = run_task_planning(metadata, report)
    for item in plan.get("task_plan", []):
        step = item.get("step")
        if step == 5:
            item["status"] = "demo_pass"
        elif step == 4.2 and not has_feedback:
            item["status"] = "ready"
        else:
            item["status"] = "done"
    return plan


def run_full_workflow(
    metadata: TaskMetadata,
    report: Dict[str, Any],
    confirmation: HumanConfirmation,
    human_feedback: str = "",
    force_fallback: bool = False,
) -> WorkflowResult:
    insight = run_pr_director_insight(metadata, report, confirmation, force_fallback=force_fallback)
    draft = run_pr_generation(metadata, report, confirmation, insight, force_fallback=force_fallback)
    reviews = run_all_reviews(draft, insight, confirmation, metadata, report)
    revised = run_revision(draft, human_feedback) if human_feedback else None
    task_plan = _completed_task_plan(metadata, report, bool(human_feedback))
    return WorkflowResult(
        metadata=metadata,
        information_report=report,
        human_confirmation=confirmation,
        task_plan=task_plan,
        insight=insight,
        draft=draft,
        expert_reviews=reviews,
        revised_draft=revised,
        human_feedback=human_feedback,
    )
