from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from global_pr_agent.orchestrator import (  # noqa: E402
    run_full_workflow,
    run_pr_director_insight,
    run_pr_generation,
    run_task_planning,
)
from global_pr_agent.report_loader import load_json_report, defaults_from_report, extract_from_document_via_llm  # noqa: E402
from global_pr_agent.reviewers import run_all_reviews  # noqa: E402
from global_pr_agent.schemas import HumanConfirmation, TaskMetadata  # noqa: E402

app = FastAPI(title="Global PR Agent API", version="2.0.0")

# Add CORS middleware to allow Vue frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ROOT = Path(__file__).resolve().parent
SAMPLE_JSON_PATH = PROJECT_ROOT / "demo_inputs" / "wenjie_sample_report.json"


class WorkflowRequest(BaseModel):
    metadata: Optional[Dict[str, Any]] = None
    information_report: Optional[Dict[str, Any]] = None
    human_confirmation: Optional[Dict[str, Any]] = None
    human_feedback: str = ""
    force_fallback: bool = False


class PlanRequest(BaseModel):
    metadata: Dict[str, Any]
    information_report: Optional[Dict[str, Any]] = None


class ExtractRequest(BaseModel):
    text: str


def _check_token(authorization: Optional[str]) -> None:
    expected = os.environ.get("ACCESS_TOKEN", "")
    if not expected:
        return
    if not authorization or authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="Invalid or missing access token")


def _normalize(payload: WorkflowRequest) -> tuple[TaskMetadata, Dict[str, Any], HumanConfirmation]:
    report = payload.information_report or load_json_report(SAMPLE_JSON_PATH)
    default_meta, default_human = defaults_from_report(report)
    metadata = TaskMetadata(**payload.metadata) if payload.metadata else default_meta
    human = HumanConfirmation(**payload.human_confirmation) if payload.human_confirmation else default_human
    return metadata, report, human


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "global-pr-agent", "version": "2.0.0"}


@app.post("/api/extract")
def api_extract(payload: ExtractRequest, authorization: Optional[str] = Header(default=None)) -> JSONResponse:
    _check_token(authorization)
    extracted = extract_from_document_via_llm(payload.text)
    if not extracted:
        raise HTTPException(status_code=400, detail="Extraction failed or LLM not available")
    return JSONResponse(extracted)


@app.post("/api/plan")
def api_plan(payload: PlanRequest, authorization: Optional[str] = Header(default=None)) -> JSONResponse:
    _check_token(authorization)
    metadata = TaskMetadata(**payload.metadata)
    return JSONResponse(run_task_planning(metadata, payload.information_report or {}))


@app.post("/api/generate-pr")
def api_generate_pr(payload: WorkflowRequest, authorization: Optional[str] = Header(default=None)) -> JSONResponse:
    _check_token(authorization)
    metadata, report, human = _normalize(payload)
    result = run_full_workflow(
        metadata=metadata,
        report=report,
        confirmation=human,
        human_feedback=payload.human_feedback,
        force_fallback=payload.force_fallback,
    )
    return JSONResponse(result.to_dict())


@app.post("/api/insight")
def api_insight(payload: WorkflowRequest, authorization: Optional[str] = Header(default=None)) -> JSONResponse:
    _check_token(authorization)
    metadata, report, human = _normalize(payload)
    insight = run_pr_director_insight(metadata, report, human, force_fallback=payload.force_fallback)
    return JSONResponse(insight.to_dict())


@app.post("/api/generate")
def api_generate(payload: WorkflowRequest, authorization: Optional[str] = Header(default=None)) -> JSONResponse:
    _check_token(authorization)
    metadata, report, human = _normalize(payload)
    insight = run_pr_director_insight(metadata, report, human, force_fallback=payload.force_fallback)
    draft = run_pr_generation(metadata, report, human, insight, force_fallback=payload.force_fallback)
    return JSONResponse(draft.to_dict())


@app.post("/api/review")
def api_review(payload: WorkflowRequest, authorization: Optional[str] = Header(default=None)) -> JSONResponse:
    _check_token(authorization)
    metadata, report, human = _normalize(payload)
    insight = run_pr_director_insight(metadata, report, human, force_fallback=payload.force_fallback)
    draft = run_pr_generation(metadata, report, human, insight, force_fallback=payload.force_fallback)
    reviews = run_all_reviews(draft, insight, human, metadata, report)
    return JSONResponse({"items": [review.to_dict() for review in reviews]})
