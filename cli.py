from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from global_pr_agent.exporter import save_docx, save_json, save_markdown  # noqa: E402
from global_pr_agent.orchestrator import run_full_workflow  # noqa: E402
from global_pr_agent.report_loader import defaults_from_report, load_json_report  # noqa: E402
from global_pr_agent.schemas import HumanConfirmation, TaskMetadata  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent
SAMPLE_JSON_PATH = PROJECT_ROOT / "demo_inputs" / "wenjie_sample_report.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Global PR Agent workflow demo.")
    parser.add_argument("--sample", action="store_true", help="Run with the built-in AITO / UAE sample report.")
    parser.add_argument("--report", type=Path, help="Information Search Agent JSON report.")
    parser.add_argument("--metadata", type=Path, help="Optional TaskMetadata JSON file.")
    parser.add_argument("--human-confirmation", type=Path, help="Optional HumanConfirmation JSON file.")
    parser.add_argument("--feedback", type=str, default="", help="Optional human feedback for revision step.")
    parser.add_argument("--out", type=Path, default=Path("demo/generated"), help="Output directory.")
    parser.add_argument("--force-fallback", action="store_true", help="Disable LLM API even if an API key is configured.")
    args = parser.parse_args()

    if args.report:
        report = load_json_report(args.report)
    elif args.sample:
        report = load_json_report(SAMPLE_JSON_PATH)
    else:
        raise SystemExit("Use --sample or --report report.json")

    default_meta, default_human = defaults_from_report(report)
    if args.metadata:
        metadata = TaskMetadata(**json.loads(args.metadata.read_text(encoding="utf-8")))
    else:
        metadata = default_meta
    if args.human_confirmation:
        human = HumanConfirmation(**json.loads(args.human_confirmation.read_text(encoding="utf-8")))
    else:
        human = default_human

    result = run_full_workflow(metadata, report, human, human_feedback=args.feedback, force_fallback=args.force_fallback)
    args.out.mkdir(parents=True, exist_ok=True)
    md_path = save_markdown(result, args.out / "global_pr_agent_output.md")
    json_path = save_json(result, args.out / "global_pr_agent_output.json")
    try:
        docx_path = save_docx(result, args.out / "global_pr_agent_output.docx")
    except RuntimeError:
        docx_path = None

    print(f"Markdown saved to: {md_path}")
    print(f"JSON saved to: {json_path}")
    if docx_path:
        print(f"DOCX saved to: {docx_path}")
    print("\nPreview:\n")
    print(md_path.read_text(encoding="utf-8")[:2200])


if __name__ == "__main__":
    main()
