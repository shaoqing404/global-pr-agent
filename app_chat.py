from __future__ import annotations

import json
import os
import re
import sys
import webbrowser
# State constants (plain ints – Enum classes break in Streamlit because
# each script rerun creates a new class and session_state holds old instances)
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from global_pr_agent.exporter import save_docx, workflow_to_markdown
from global_pr_agent.llm_client import LLMClient
from global_pr_agent.orchestrator import (
    run_pr_director_insight,
    run_pr_generation,
    run_revision,
    run_task_planning,
)
from global_pr_agent.report_loader import (
    defaults_from_report,
    extract_from_document_via_llm,
    load_json_report,
)
from global_pr_agent.reviewers import run_all_reviews
from global_pr_agent.schemas import (
    HumanConfirmation,
    InformationSearchReport,
    TaskMetadata,
    WorkflowResult,
)

PROJECT_ROOT = Path(__file__).resolve().parent
SAMPLE_JSON_PATH = PROJECT_ROOT / "demo_inputs" / "wenjie_sample_report.json"
DESIGN_DOC_PATH = PROJECT_ROOT / "docs" / "interactive_design.html"
EXPORT_DIR = PROJECT_ROOT / "storage" / "export"

st.set_page_config(page_title="Global PR Agent", page_icon="🌍", layout="wide")

# ── Load Environment Variables (since python-dotenv is not in requirements) ───
env_path = PROJECT_ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            key, _, val = line.partition("=")
            if key:
                os.environ[key.strip()] = val.strip()

# ── State Machine (plain int constants) ───────────────────────────────────────
# NOTE: Do NOT use Enum here. Streamlit re-executes the entire script on every
# interaction, creating a brand-new Enum class each time. session_state holds
# instances from the *previous* class, and Python Enum.__eq__ uses identity
# comparison ("is"), so old_instance == new_class.MEMBER is always False.
ST_TASK_START = 0           # 等待用户输入任务描述
ST_INTELLIGENCE_INPUT = 1   # 澄清问题阶段
ST_BUSINESS_CONFIRM = 2     # 业务决策确认
ST_DIRECTOR_INSIGHT = 3     # 战略洞察 → 生成
ST_FEEDBACK_REVISE = 4      # 多轮修订 / 翻译 / 导出


# ── Minimal CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"], .main { background: #0a0a0a !important; }
[data-testid="stSidebar"] { background: #0f0f0f !important; }
[data-testid="stSidebar"] * { color: #c9d1d9 !important; }
</style>
""", unsafe_allow_html=True)


# ── Welcome message (shown on first load) ─────────────────────────────────────
WELCOME_MESSAGE = """\
👋 你好！我是 **Global PR Agent**，出海品牌 PR 稿件生成 AI 助手。

我可以帮你完成：
- 📊 品牌战略洞察分析
- 📝 英文 PR 稿件撰写
- 🔍 四位专家协同审定（内容 / 品牌一致性 / 创意 / 法律风险）
- 🌍 多语言本土化翻译
- 📦 文档导出（DOCX / JSON / Markdown）

---

**请告诉我您的 PR 任务目标**，例如：

> 帮我调研问界 / AITO 品牌在阿联酋市场的 PR 推广机会，并设计一份面向阿拉伯地区、英文撰写的高端智能 SUV 品牌 PR 稿件

您也可以在左侧边栏 **上传品牌信息文档**（txt / md），我会自动提取结构化品牌情报。

直接在下方输入框开始吧 👇"""


# ── Session state init ────────────────────────────────────────────────────────
_defaults = {
    "state": ST_TASK_START,
    "chat_history": [{"role": "assistant", "content": WELCOME_MESSAGE}],
    "metadata": TaskMetadata(),
    "report": {},
    "confirmation": HumanConfirmation(),
    "insight": None,
    "draft": None,
    "reviews": [],
    "workflow_result": None,
    "source_mode": None,  # "sample" | "upload"
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🌍 Global PR Agent")
    st.caption("出海品牌 PR 稿件生成系统")

    # ── Progress tracker ──
    st.markdown("### 进度")
    labels = ["任务启动", "战略情报", "业务决策", "战略洞察", "生成审定 & 反馈"]
    cur = st.session_state.state
    for i, s in enumerate(labels):
        if i == cur:
            st.markdown(f"**👉 {i+1}. {s}**")
        elif i < cur:
            st.markdown(f"✅ {i+1}. {s}")
        else:
            st.markdown(f"⏳ {i+1}. {s}")

    st.markdown("---")

    # ── Data source badge ──
    badge = {"sample": "🎯 问界 / AITO 样例", "upload": "📄 上传文档"}.get(
        st.session_state.source_mode, ""
    )
    if badge:
        st.info(badge)

    # ── Document upload ──
    st.markdown("### 📄 品牌文档上传")
    st.caption("上传 txt / md 格式的品牌信息文档，AI 自动提取情报")
    uploaded = st.file_uploader(
        "上传品牌文档", type=["txt", "md"], label_visibility="collapsed"
    )
    if uploaded:
        with st.spinner("AI 正在提取结构化品牌情报..."):
            text = uploaded.read().decode("utf-8")
            extracted = extract_from_document_via_llm(text)
            if extracted:
                try:
                    InformationSearchReport(**extracted)
                    st.session_state.report = extracted
                    st.success("✅ 品牌情报提取成功！")
                except Exception:
                    st.session_state.report = load_json_report(SAMPLE_JSON_PATH)
                    st.warning("结构校验失败，已回退至问界样例底座。")
            else:
                st.session_state.report = load_json_report(SAMPLE_JSON_PATH)
                st.warning("提取失败（未配置 LLM_API_KEY），已加载问界样例底座。")
            st.session_state.metadata, st.session_state.confirmation = defaults_from_report(
                st.session_state.report
            )
            st.session_state.source_mode = "upload"

    st.markdown("---")

    # ── Design doc link ──
    if DESIGN_DOC_PATH.exists():
        if st.button("📊 项目设计文档", use_container_width=True,
                     help="在浏览器新窗口中打开交互式设计文档"):
            webbrowser.open(DESIGN_DOC_PATH.resolve().as_uri())


# ══════════════════════════════════════════════════════════════════════════════
# CHAT RENDERING
# ══════════════════════════════════════════════════════════════════════════════
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


def _assistant(text: str):
    """Append an assistant message and render it immediately."""
    st.session_state.chat_history.append({"role": "assistant", "content": text})
    with st.chat_message("assistant"):
        st.markdown(text)


# ══════════════════════════════════════════════════════════════════════════════
# CHAT INPUT HANDLING
# ══════════════════════════════════════════════════════════════════════════════
if prompt := st.chat_input("输入您的回复或指令..."):
    # Render user message
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    state = st.session_state.state

    try:
        # ── TASK_START ────────────────────────────────────────────────────────
        if state == ST_TASK_START:
            # Load report if not already loaded (default to sample)
            if not st.session_state.report:
                st.session_state.report = load_json_report(SAMPLE_JSON_PATH)
                st.session_state.metadata, st.session_state.confirmation = defaults_from_report(
                    st.session_state.report
                )
                st.session_state.source_mode = "sample"

            # Try LLM extraction of task metadata
            client = LLMClient()
            if client.available:
                meta_resp = client.chat([
                    {"role": "system", "content": (
                        "Extract PR task metadata from the user message. "
                        "Return JSON only with keys: brand, product_or_business, "
                        "target_market, target_language, pr_objective. "
                        "If not mentioned, keep existing defaults."
                    )},
                    {"role": "user", "content": prompt},
                ], temperature=0.1)
                if meta_resp and not meta_resp.startswith("[LLM_CALL_FAILED]"):
                    try:
                        meta_data = json.loads(re.sub(r"```json|```", "", meta_resp).strip())
                        m = st.session_state.metadata
                        st.session_state.metadata = TaskMetadata(
                            brand=meta_data.get("brand", m.brand),
                            product_or_business=meta_data.get("product_or_business", m.product_or_business),
                            target_market=meta_data.get("target_market", m.target_market),
                            target_language=meta_data.get("target_language", m.target_language),
                            pr_objective=meta_data.get("pr_objective", prompt),
                        )
                    except Exception:
                        st.session_state.metadata.pr_objective = prompt
            else:
                st.session_state.metadata.pr_objective = prompt

            # Run task planning
            with st.spinner("思考澄清问题中..."):
                plan = run_task_planning(st.session_state.metadata, st.session_state.report)
            qs = "\n".join(f"- {q}" for q in plan.get("clarification_questions", []))
            plan_md = "\n".join(f"- Step {item.get('step')}: **{item.get('name')}**" for item in plan.get("task_plan", []))
            
            _assistant(
                f"收到！已记录任务目标：**{st.session_state.metadata.pr_objective[:80]}**\n\n"
                f"这是我为您制定的 Agent 执行计划：\n{plan_md}\n\n"
                f"---\n"
                f"在正式进入【业务决策阶段】前，有几个细节需要向您确认：\n\n{qs}\n\n"
                "您可以逐一回答，也可以直接输入「**确认计划**」进入下一步。"
            )
            st.session_state.state = ST_INTELLIGENCE_INPUT

        # ── INTELLIGENCE_INPUT ────────────────────────────────────────────────
        elif state == ST_INTELLIGENCE_INPUT:
            keywords = ("确认", "跳过", "ok", "开始", "continue", "next", "计划")
            if any(kw in prompt.lower() for kw in keywords):
                if not st.session_state.report:
                    st.session_state.report = load_json_report(SAMPLE_JSON_PATH)
                    st.session_state.metadata, st.session_state.confirmation = defaults_from_report(
                        st.session_state.report
                    )
                
                with st.spinner("正在综合您的反馈与情报底座提炼业务策略..."):
                    client = LLMClient()
                    if client.available and st.session_state.confirmation.human_notes:
                        sys_prompt = (
                            "You are a PR strategist. Extract the business strategy based on the user's feedback. "
                            "Return ONLY JSON with keys: core_pr_angle, localization_strategy, brand_tone. "
                            "Always use Chinese for the values."
                        )
                        user_msg = f"User feedback: {st.session_state.confirmation.human_notes}\nBase defaults: {st.session_state.confirmation.to_dict()}"
                        resp = client.chat([{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_msg}], temperature=0.2)
                        if resp and not resp.startswith("[LLM_CALL_FAILED]"):
                            try:
                                cleaned = resp.strip()
                                if cleaned.startswith("```"):
                                    cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
                                data = json.loads(cleaned)
                                c = st.session_state.confirmation
                                c.core_pr_angle = data.get("core_pr_angle", c.core_pr_angle)
                                c.localization_strategy = data.get("localization_strategy", c.localization_strategy)
                                c.brand_tone = data.get("brand_tone", c.brand_tone)
                            except Exception:
                                pass

                c = st.session_state.confirmation
                _assistant(
                    "✅ **计划已确认，进入业务决策阶段。**\n\n根据 DeepResearch Agent 和 知识库Agent 的情报反馈，以及您补充的专业信息，我提炼了以下推荐策略：\n\n"
                    f"- **核心 PR 角度**: {c.core_pr_angle}\n"
                    f"- **本土化策略**: {c.localization_strategy}\n"
                    f"- **品牌调性**: {c.brand_tone}\n\n"
                    "请核实以上方向。如需调整请直接告诉我，或输入「**确认策略**」进入 Director 洞察阶段。"
                )
                st.session_state.state = ST_BUSINESS_CONFIRM
            else:
                st.session_state.confirmation.human_notes += f" | {prompt}"
                _assistant("已收到您的解答并记录入情报库中。如果您还有其他补充可以直接告诉我，或者输入「**确认计划**」进入下一步的业务策略提炼。")

        # ── BUSINESS_CONFIRM ─────────────────────────────────────────────────
        elif state == ST_BUSINESS_CONFIRM:
            keywords = ("确认", "ok", "好的", "同意", "continue", "策略")
            if any(kw in prompt.lower() for kw in keywords):
                with st.spinner("PR Director Agent 正在生成战略洞察..."):
                    st.session_state.insight = run_pr_director_insight(
                        st.session_state.metadata,
                        st.session_state.report,
                        st.session_state.confirmation,
                        force_fallback=not LLMClient().available,
                    )
                ins = st.session_state.insight
                _assistant(
                    "✅ **业务策略已锁定。以下是战略洞察：**\n\n"
                    f"**品牌洞察**：{ins.brand_insight}\n\n"
                    f"**市场分析**：{ins.market_insight}\n\n"
                    f"**PR叙事推荐**：{ins.pr_narrative}\n\n"
                    f"**本土化建议**：{ins.localization_advice}\n\n"
                    f"**风险提示**：{', '.join(ins.risk_notes)}\n\n"
                    "您可以提出修改意见，或输入「**确认生成**」，我将立即撰写 PR 初稿并调用四位专家协同审定。"
                )
                st.session_state.state = ST_DIRECTOR_INSIGHT
            else:
                st.session_state.confirmation.human_notes += f" | {prompt}"
                with st.spinner("正在基于您的调整意见重新规划策略..."):
                    client = LLMClient()
                    if client.available:
                        sys_prompt = (
                            "You are a PR strategist. Extract the updated business strategy based on the user's adjustment feedback. "
                            "Return ONLY JSON with keys: core_pr_angle, localization_strategy, brand_tone. "
                            "Always use Chinese for the values."
                        )
                        user_msg = f"User feedback: {prompt}\nCurrent strategy: {st.session_state.confirmation.to_dict()}"
                        resp = client.chat([{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_msg}], temperature=0.2)
                        if resp and not resp.startswith("[LLM_CALL_FAILED]"):
                            try:
                                cleaned = resp.strip()
                                if cleaned.startswith("```"):
                                    cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
                                data = json.loads(cleaned)
                                c = st.session_state.confirmation
                                c.core_pr_angle = data.get("core_pr_angle", c.core_pr_angle)
                                c.localization_strategy = data.get("localization_strategy", c.localization_strategy)
                                c.brand_tone = data.get("brand_tone", c.brand_tone)
                            except Exception:
                                pass
                c = st.session_state.confirmation
                _assistant(
                    "已根据您的意见动态调整业务策略，更新后如下：\n\n"
                    f"- **核心 PR 角度**: {c.core_pr_angle}\n"
                    f"- **本土化策略**: {c.localization_strategy}\n"
                    f"- **品牌调性**: {c.brand_tone}\n\n"
                    "如果确认无误，请输入「**确认策略**」进入 Director 洞察阶段。"
                )

        # ── DIRECTOR_INSIGHT ─────────────────────────────────────────────────
        elif state == ST_DIRECTOR_INSIGHT:
            keywords = ("生成", "确认", "ok", "continue", "generate")
            if any(kw in prompt.lower() for kw in keywords):
                with st.spinner("正在生成 PR 初稿并调用四位专家审定..."):
                    st.session_state.draft = run_pr_generation(
                        st.session_state.metadata,
                        st.session_state.report,
                        st.session_state.confirmation,
                        st.session_state.insight,
                        force_fallback=not LLMClient().available,
                    )
                    st.session_state.reviews = run_all_reviews(
                        st.session_state.draft,
                        st.session_state.insight,
                        st.session_state.confirmation,
                        st.session_state.metadata,
                        st.session_state.report,
                    )
                review_lines = ""
                for r in st.session_state.reviews:
                    review_lines += f"### {r.reviewer} (分数 {r.score}/100)\n"
                    review_lines += f"- **优势**: {' / '.join(r.strengths) if r.strengths else '无'}\n"
                    review_lines += f"- **问题**: {' / '.join(r.issues) if r.issues else '无'}\n"
                    review_lines += f"- **建议**: {' / '.join(r.suggestions) if r.suggestions else '无'}\n\n"

                _assistant(
                    "🎉 **PR 初稿已生成！** 以下是为您撰写的初稿：\n\n"
                    "---\n"
                    f"{st.session_state.draft.press_release}\n"
                    "---\n\n"
                    "**四位专家审定意见如下：**\n\n"
                    f"{review_lines}\n"
                    "**请问您希望如何修改？**\n"
                    "- 输入修改意见（如「缩短正文」「更强调家庭场景」）\n"
                    "- 输入「**翻译成阿拉伯语**」进行多语言本土化\n"
                    "- 输入「**导出**」直接生成最终文档包"
                )
                st.session_state.state = ST_FEEDBACK_REVISE
            else:
                st.session_state.confirmation.human_notes += f" | {prompt}"
                with st.spinner("正在基于您的建议重塑战略洞察..."):
                    client = LLMClient()
                    if client.available:
                        sys_prompt = (
                            "You are a PR Director. Modify the current strategic PR insight based on the user's feedback.\n"
                            "Return ONLY a JSON object with these keys:\n"
                            "- brand_insight (String)\n"
                            "- market_insight (String)\n"
                            "- pr_narrative (String)\n"
                            "- localization_advice (String)\n"
                            "- risk_notes (Array of Strings)\n"
                            "Always use Chinese for the values."
                        )
                        user_msg = f"User feedback: {prompt}\nCurrent Insight: {st.session_state.insight.to_dict()}"
                        resp = client.chat([{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_msg}], temperature=0.2)
                        if resp and not resp.startswith("[LLM_CALL_FAILED]"):
                            try:
                                cleaned = resp.strip()
                                if cleaned.startswith("```"):
                                    cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
                                data = json.loads(cleaned)
                                ins = st.session_state.insight
                                ins.brand_insight = data.get("brand_insight", ins.brand_insight)
                                ins.market_insight = data.get("market_insight", ins.market_insight)
                                ins.pr_narrative = data.get("pr_narrative", ins.pr_narrative)
                                ins.localization_advice = data.get("localization_advice", ins.localization_advice)
                                ins.risk_notes = data.get("risk_notes", ins.risk_notes)
                            except Exception:
                                pass
                
                ins = st.session_state.insight
                _assistant(
                    "已根据您的意见动态调整战略洞察，更新后如下：\n\n"
                    f"**品牌洞察**：{ins.brand_insight}\n\n"
                    f"**市场分析**：{ins.market_insight}\n\n"
                    f"**PR叙事推荐**：{ins.pr_narrative}\n\n"
                    f"**本土化建议**：{ins.localization_advice}\n\n"
                    f"**风险提示**：{', '.join(ins.risk_notes)}\n\n"
                    "如果确认无误，请输入「**确认生成**」启动稿件撰写与专家审定。"
                )

        # ── FEEDBACK_REVISE ───────────────────────────────────────────────────
        elif state == ST_FEEDBACK_REVISE:
            export_kws = ("导出", "export", "结束", "完成", "done", "finish")
            if any(kw in prompt.lower() for kw in export_kws):
                # Build workflow result and export
                EXPORT_DIR.mkdir(parents=True, exist_ok=True)
                out_path = EXPORT_DIR / "global_pr_agent_output.docx"
                st.session_state.workflow_result = WorkflowResult(
                    metadata=st.session_state.metadata,
                    information_report=st.session_state.report,
                    human_confirmation=st.session_state.confirmation,
                    task_plan={"status": "completed via chat"},
                    insight=st.session_state.insight,
                    draft=st.session_state.draft,
                    expert_reviews=st.session_state.reviews,
                    revised_draft=st.session_state.draft.press_release,
                    human_feedback="Finalized via chat.",
                )
                save_docx(st.session_state.workflow_result, out_path)
                _assistant("✅ **全套 PR 物料已准备完毕！** 请在下方下载您的成果文档包。")
                # Rerun only here so download buttons render immediately
                st.rerun()
            else:
                with st.spinner("正在根据您的反馈进行修订..."):
                    revised = run_revision(st.session_state.draft, prompt)
                    st.session_state.draft.press_release = revised
                _assistant(
                    "已完成修订（含翻译/本土化优化）。以下是最新版本：\n\n"
                    "---\n"
                    f"{revised}\n"
                    "---\n\n"
                    "还有其他调整吗？确认无误请输入「**导出**」。"
                )

    except Exception as exc:
        st.error(f"⚠️ 处理过程中出现异常：{exc}")
        import traceback
        st.code(traceback.format_exc(), language="python")


# ── Download buttons ──────────────────────────────────────────────────────────
if st.session_state.workflow_result:
    st.markdown("---")
    wf = st.session_state.workflow_result
    out_path = EXPORT_DIR / "global_pr_agent_output.docx"
    c1, c2, c3 = st.columns(3)
    with c1:
        if out_path.exists():
            st.download_button(
                "📥 下载 DOCX", data=out_path.read_bytes(),
                file_name="global_pr_agent_output.docx",
            )
    with c2:
        st.download_button(
            "📥 下载 JSON",
            data=json.dumps(wf.to_dict(), ensure_ascii=False, indent=2).encode(),
            file_name="output.json", mime="application/json",
        )
    with c3:
        st.download_button(
            "📥 下载 Markdown",
            data=workflow_to_markdown(wf).encode(),
            file_name="output.md", mime="text/markdown",
        )
