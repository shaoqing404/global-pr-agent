from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from .llm_client import LLMClient
from .schemas import HumanConfirmation, TaskMetadata


def strip_research_citations(value: Any) -> Any:
    """Remove DeepResearch / ChatGPT citation markers from runtime text.

    The original Markdown report keeps its source markers for human reading, but
    generated PR drafts and DOCX outputs should not leak internal citation glyphs.
    """
    if isinstance(value, str):
        value = re.sub(r"cite.*?", "", value)
        value = re.sub(r"\s+([。；，,.!?])", r"\1", value)
        return re.sub(r"[ \t]{2,}", " ", value).strip()
    if isinstance(value, list):
        return [strip_research_citations(item) for item in value]
    if isinstance(value, dict):
        return {key: strip_research_citations(item) for key, item in value.items()}
    return value


def load_json_report(path: str | Path) -> Dict[str, Any]:
    return strip_research_citations(json.loads(Path(path).read_text(encoding="utf-8")))


def load_markdown_report(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def extract_json_from_markdown(markdown: str) -> Dict[str, Any] | None:
    marker = "## JSON Structured Report"
    idx = markdown.find(marker)
    if idx < 0:
        return None
    raw = markdown[idx:].split("\n", 1)[1].strip()
    try:
        return strip_research_citations(json.loads(raw))
    except json.JSONDecodeError:
        return None


def _first(value: Any, default: str = "") -> str:
    if isinstance(value, list):
        return str(value[0]) if value else default
    if value is None:
        return default
    return str(value)


def _clean_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def summarize_report(report: Dict[str, Any]) -> Dict[str, Any]:
    metadata = report.get("metadata", {})
    brand = report.get("brand_snapshot", {})
    market = report.get("target_market_context", {})
    pr_angle = report.get("pr_angle_recommendation", {})
    audience = report.get("target_audience", {})
    local = report.get("localization_strategy", {})
    risks = report.get("risk_register", [])
    return {
        "brand": metadata.get("brand", "问界 / AITO"),
        "target_market": market.get("market_selected", metadata.get("target_market", "UAE")),
        "positioning": brand.get("brand_positioning", ""),
        "main_angle": pr_angle.get("recommended_main_angle", ""),
        "primary_audience": audience.get("primary_audience", ""),
        "recommended_tone": local.get("recommended_tone", ""),
        "top_risks": [risk.get("risk", "") for risk in risks[:5] if isinstance(risk, dict)],
    }


def defaults_from_report(report: Dict[str, Any]) -> tuple[TaskMetadata, HumanConfirmation]:
    metadata = report.get("metadata", {})
    market = report.get("target_market_context", {})
    audience = report.get("target_audience", {})
    local = report.get("localization_strategy", {})
    pr_angle = report.get("pr_angle_recommendation", {})
    risks = report.get("risk_register", [])
    risk_constraints = []
    for risk in risks[:6]:
        if isinstance(risk, dict):
            risk_constraints.append(f"{risk.get('risk', '')}: {risk.get('mitigation', '')}".strip(": "))
    task = TaskMetadata(
        brand="问界 / AITO",
        product_or_business="AITO 9 / AITO 7 / AITO 5 Gulf-ready intelligent luxury SUVs",
        target_market=market.get("market_selected", "UAE"),
        target_language="English",
        pr_objective="Generate a localized overseas PR draft for AITO's UAE market-entry narrative.",
        announcement_type="Market Entry / Brand Launch",
        deadline="Urgent - fast turnaround expected",
    )
    human = HumanConfirmation(
        brand_tone=local.get("recommended_tone", "premium, restrained, engineering-led, service-backed"),
        product_tone="intelligent new luxury SUV for Gulf family and executive mobility",
        target_audience=audience.get("primary_audience", "UAE premium SUV buyers"),
        overseas_strategy_baseline="From China proof to Gulf trust: combine China-market credibility with UAE local partner and service readiness.",
        core_pr_angle=pr_angle.get("recommended_main_angle", "Gulf-ready intelligent luxury for UAE families and executives."),
        localization_strategy="; ".join(_clean_list(local.get("cultural_considerations"))) or "Emphasize local partnership and avoid over-claiming.",
        risk_constraints=risk_constraints or HumanConfirmation().risk_constraints,
        spokesperson_direction=pr_angle.get("suggested_spokesperson_quote_direction", HumanConfirmation().spokesperson_direction),
        human_notes="Auto-filled from the information search report. Human can edit before generation.",
    )
    return task, human


def extract_from_document_via_llm(text: str, llm_client: LLMClient | None = None) -> Dict[str, Any] | None:
    """Uses LLM to extract unstructured text into the InformationSearchReport JSON schema.
    Returns None if extraction fails or falls back to template if no LLM is available.
    """
    client = llm_client or LLMClient()
    if not client.available:
        return None

    # Truncate text to avoid token limits
    truncated_text = text[:15000]

    system_prompt = """
You are an expert strategic PR intelligence extractor. Your task is to analyze the provided unstructured document 
and extract key information into a strict JSON format matching the `InformationSearchReport` schema.

Ensure the output is ONLY valid JSON. Do not include markdown code blocks like ```json or any other text.
The JSON must have the following keys at the root level:
- "metadata" (dict)
- "brand_snapshot" (dict)
- "product_offering_summary" (list of dicts)
- "target_market_context" (dict)
- "competitor_landscape" (list of dicts)
- "target_audience" (dict)
- "localization_strategy" (dict)
- "pr_angle_recommendation" (dict)
- "risk_register" (list of dicts)

If certain information is not present in the text, use empty strings, empty lists, or generic placeholders.
""".strip()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Document Text:\n\n{truncated_text}"}
    ]

    try:
        response = client.chat(messages, temperature=0.1)
        if response and not response.startswith("[LLM_CALL_FAILED]"):
            # Strip markdown formatting if the LLM hallucinated it
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            
            parsed_json = json.loads(cleaned_response.strip())
            return parsed_json
    except Exception as e:
        print(f"Failed to extract document via LLM: {e}")
    
    return None
