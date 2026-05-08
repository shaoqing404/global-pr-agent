# CODEX_TASKS.md · 查漏补缺任务清单

## 0. Hard Constraints

- Do not rewrite from scratch.
- Do not add real web search.
- Do not add real legal compliance.
- Do not hard-code real API keys.
- Prioritize runnable demo and documentation clarity.

## 1. Smoke Tests

Run:

```bash
python -m compileall .
python cli.py --sample --out demo/generated --force-fallback
```

Expected files:

```text
demo/generated/global_pr_agent_output.md
demo/generated/global_pr_agent_output.json
demo/generated/global_pr_agent_output.docx
```

## 2. Streamlit QA

Run:

```bash
streamlit run app.py
```

Check tabs:

- Step 0: task plan renders.
- Step 1: sample report loads and summary renders.
- Step 2: human confirmation saves.
- Step 3: PR Director Insight generates.
- Step 4: PR draft generates.
- Step 4.1: four reviewer cards render.
- Step 4.2: feedback revision and export buttons render.

## 3. FastAPI QA

Run:

```bash
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

Test:

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/api/generate-pr -H "Content-Type: application/json" -d '{"force_fallback": true}'
```

## 4. Documentation QA

Check that README includes:

- topic selection
- implemented scope
- non-goals
- run commands
- demo flow
- input contract
- Dify / Coze / n8n migration summary

Check that docs include:

- 00_speckit.md
- 01_requirement.md
- 02_technical_design.md
- 03_usage_guide.md
- 04_platform_migration.md
- 05_known_limits.md
- 06_submission_checklist.md

## 5. If Time Remains

- Add screenshots after manually running Streamlit.
- Improve UI labels and Chinese copy.
- Add one minimal pytest for `run_full_workflow`.
- Add `demo_inputs/sample_api_request.json` for API reviewers.
