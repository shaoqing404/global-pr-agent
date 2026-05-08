from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from global_pr_agent.exporter import save_docx, workflow_to_markdown  # noqa: E402
from global_pr_agent.orchestrator import (  # noqa: E402
    run_full_workflow,
    run_pr_director_insight,
    run_pr_generation,
    run_revision,
    run_task_planning,
)
from global_pr_agent.report_loader import (  # noqa: E402
    defaults_from_report,
    extract_json_from_markdown,
    load_json_report,
    summarize_report,
)
from global_pr_agent.reviewers import run_all_reviews  # noqa: E402
from global_pr_agent.schemas import HumanConfirmation, InformationSearchReport, TaskMetadata, WorkflowResult  # noqa: E402


PROJECT_ROOT = Path(__file__).resolve().parent
SAMPLE_JSON_PATH = PROJECT_ROOT / "demo_inputs" / "wenjie_sample_report.json"
SAMPLE_MD_PATH = PROJECT_ROOT / "demo_inputs" / "wenjie_sample_report.md"

st.set_page_config(page_title="Global PR Agent", page_icon="🌍", layout="wide")
st.title("🌍 Global PR Agent · 出海品牌 PR 稿件生成系统")
st.caption("情报输入 → 人类确认 → 战略洞察 → 内容生成 → 专家审定 → 反馈修订 → 成果导出")

# Initialize dirty flag to track if report has changed since last confirmation
if "report_dirty" not in st.session_state:
    st.session_state["report_dirty"] = False

if "metadata" not in st.session_state:
    st.session_state["metadata"] = TaskMetadata()
if "information_report" not in st.session_state:
    st.session_state["information_report"] = load_json_report(SAMPLE_JSON_PATH) if SAMPLE_JSON_PATH.exists() else {}
if "human_confirmation" not in st.session_state:
    st.session_state["human_confirmation"] = defaults_from_report(st.session_state["information_report"])[1]
if "task_plan" not in st.session_state:
    st.session_state["task_plan"] = run_task_planning(st.session_state["metadata"], st.session_state["information_report"])


with st.sidebar:
    st.header("系统设置")
    force_fallback = st.toggle("强制本地模式", value=False)
    st.info("系统支持 OpenAI-compatible 模型接入。未配置 API Key 时将自动切换至本地规则引擎以保证运行稳定性。")
    st.markdown("### 系统能力范围")
    st.markdown("""
- **已实现**：全链路工作流、多专家协同审定、反馈修订回路、多格式导出
- **情报源**：当前版本接入标准化 DeepResearch 市场研究报告
- **预留点**：实时联网搜索接口、企业级法务合规库、多级审批流
""")
    if st.button("加载问界 / AITO 样例报告", use_container_width=True):
        st.session_state["information_report"] = load_json_report(SAMPLE_JSON_PATH)
        st.session_state["metadata"], st.session_state["human_confirmation"] = defaults_from_report(st.session_state["information_report"])
        st.session_state["task_plan"] = run_task_planning(st.session_state["metadata"], st.session_state["information_report"])
        st.success("样例报告已加载。")


def _lines_to_list(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def _display_plan(plan: dict) -> None:
    st.markdown("#### AI 反问")
    for q in plan.get("clarification_questions", []):
        st.markdown(f"- {q}")
    st.markdown("#### 任务进度")
    rows = []
    for item in plan.get("task_plan", []):
        rows.append({
            "Step": item.get("step"),
            "Name": item.get("name"),
            "Status": item.get("status"),
            "Output": item.get("output"),
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)


step0, step1, step2, step3, step4, step5, step6 = st.tabs([
    "0. 任务启动",
    "1. 信息搜索报告",
    "2. 人类确认",
    "3. PR 洞察",
    "4. 内容生成",
    "4.1 专家审定",
    "4.2 反馈与导出",
])

with step0:
    st.subheader("Step 0 · 任务启动与计划")
    metadata: TaskMetadata = st.session_state["metadata"]
    col1, col2 = st.columns(2)
    with col1:
        brand = st.text_input("品牌", value=metadata.brand)
        product_or_business = st.text_input("产品 / 业务", value=metadata.product_or_business)
        target_market = st.text_input("目标市场", value=metadata.target_market)
        target_language = st.text_input("目标语言", value=metadata.target_language)
    with col2:
        pr_objective = st.text_area("PR 目标", value=metadata.pr_objective)
        announcement_type = st.text_input("稿件类型", value=metadata.announcement_type)
        deadline = st.text_input("交付约束", value=metadata.deadline)
    if st.button("生成 / 刷新任务计划", type="primary"):
        st.session_state["metadata"] = TaskMetadata(
            brand=brand,
            product_or_business=product_or_business,
            target_market=target_market,
            target_language=target_language,
            pr_objective=pr_objective,
            announcement_type=announcement_type,
            deadline=deadline,
        )
        st.session_state["task_plan"] = run_task_planning(st.session_state["metadata"], st.session_state["information_report"])
        st.success("任务计划已生成。")
    _display_plan(st.session_state["task_plan"])

with step1:
    st.subheader("Step 1 · 战略情报输入")
    st.markdown("系统接入标准化市场研究报告（Information Search Report）作为 PR 战略生成的底座。")
    col1, col2 = st.columns(2)
    with col1:
        uploaded = st.file_uploader("上传 JSON 结构化报告", type=["json"])
        if uploaded:
            try:
                data = json.loads(uploaded.read().decode("utf-8"))
                # Pydantic validation
                InformationSearchReport(**data)
                st.session_state["information_report"] = data
                st.session_state["report_dirty"] = True
                st.success("✅ JSON 报告已通过 Schema 验证并加载。")
                st.warning("⚠️ 检测到报告内容更新，请前往 Step 2 重新确认业务元数据。")
            except Exception as exc:  # noqa: BLE001
                st.error(f"❌ JSON 验证失败：该文件不符合 InformationSearchReport 契约。错误详情：{exc}")
    with col2:
        st.download_button(
            "下载样例 JSON 输入",
            data=json.dumps(st.session_state["information_report"], ensure_ascii=False, indent=2).encode("utf-8"),
            file_name="wenjie_sample_report.json",
            mime="application/json",
        )
    md_default = SAMPLE_MD_PATH.read_text(encoding="utf-8")[:8000] if SAMPLE_MD_PATH.exists() else ""
    md_text = st.text_area("或粘贴 Markdown 报告（可选）", value=md_default, height=220)
    if st.button("从 Markdown 报告中提取 JSON"):
        parsed = extract_json_from_markdown(md_text)
        if parsed:
            try:
                # Pydantic validation
                InformationSearchReport(**parsed)
                st.session_state["information_report"] = parsed
                st.session_state["report_dirty"] = True
                st.success("✅ 已从 Markdown 中提取并验证 JSON 报告。")
                st.warning("⚠️ 检测到报告内容更新，请前往 Step 2 重新确认业务元数据。")
            except Exception as exc:  # noqa: BLE001
                st.error(f"❌ 提取的 JSON 验证失败：{exc}")
        else:
            st.warning("未找到可解析的 JSON Structured Report。")
    summary = summarize_report(st.session_state["information_report"])
    st.markdown("#### 报告摘要")
    st.json(summary)

with step2:
    st.subheader("Step 2 · 业务决策确认")
    if st.session_state.get("report_dirty"):
        st.warning("🔔 情报源已更新，建议点击下方按钮刷新推荐值以保证生成质量。")
    st.markdown("由业务专家对 Agent 提取的元数据进行终审，确保传播方向符合品牌意志。")
    if st.button("按报告推荐值自动填充确认项"):
        _, st.session_state["human_confirmation"] = defaults_from_report(st.session_state["information_report"])
        st.session_state["report_dirty"] = False
        st.success("已按报告推荐值填充并确认。")
    human: HumanConfirmation = st.session_state["human_confirmation"]
    col1, col2 = st.columns(2)
    with col1:
        brand_tone = st.text_input("品牌格调", value=human.brand_tone)
        product_tone = st.text_input("产品格调", value=human.product_tone)
        target_audience = st.text_area("目标客群", value=human.target_audience)
        overseas_strategy_baseline = st.text_area("出海战略基调", value=human.overseas_strategy_baseline)
    with col2:
        core_pr_angle = st.text_area("核心 PR 角度", value=human.core_pr_angle)
        localization_strategy = st.text_area("本土化策略", value=human.localization_strategy)
        spokesperson_direction = st.text_area("发言人口径", value=human.spokesperson_direction)
        human_notes = st.text_area("人类备注", value=human.human_notes)
    risk_constraints = st.text_area("风险约束，每行一条", value="\n".join(human.risk_constraints), height=140)
    if st.button("确认并进入 PR 洞察阶段", type="primary"):
        st.session_state["human_confirmation"] = HumanConfirmation(
            brand_tone=brand_tone,
            product_tone=product_tone,
            target_audience=target_audience,
            overseas_strategy_baseline=overseas_strategy_baseline,
            core_pr_angle=core_pr_angle,
            localization_strategy=localization_strategy,
            risk_constraints=_lines_to_list(risk_constraints),
            spokesperson_direction=spokesperson_direction,
            human_notes=human_notes,
        )
        st.session_state["report_dirty"] = False
        st.success("确认完成。")
    st.json(st.session_state["human_confirmation"].to_dict())

with step3:
    st.subheader("Step 3 · Director 战略洞察")
    st.markdown("系统将结合情报源与业务确认项，输出品牌洞察、市场叙事及本土化策略建议。")
    if st.button("生成战略洞察", type="primary"):
        st.session_state["insight"] = run_pr_director_insight(
            st.session_state["metadata"],
            st.session_state["information_report"],
            st.session_state["human_confirmation"],
            force_fallback=force_fallback,
        )
        st.success("战略洞察已生成。")
    st.button("深度搜索补充信息 · Coming Soon", disabled=True)
    st.caption("该功能将授权 Agent 二次检索竞品舆情、本地法规或媒体素材。")

    insight = st.session_state.get("insight")
    if insight:
        st.markdown("#### 品牌洞察")
        st.write(insight.brand_insight)
        st.markdown("#### 市场洞察")
        st.write(insight.market_insight)
        st.markdown("#### PR 叙事")
        st.write(insight.pr_narrative)
        st.markdown("#### 本土化建议")
        st.write(insight.localization_advice)
        st.markdown("#### 风险提示")
        for item in insight.risk_notes:
            st.markdown(f"- {item}")

with step4:
    st.subheader("Step 4 · 内容生成")
    if st.button("生成 PR 稿件", type="primary"):
        if "insight" not in st.session_state:
            st.session_state["insight"] = run_pr_director_insight(
                st.session_state["metadata"],
                st.session_state["information_report"],
                st.session_state["human_confirmation"],
                force_fallback=force_fallback,
            )
        st.session_state["draft"] = run_pr_generation(
            st.session_state["metadata"],
            st.session_state["information_report"],
            st.session_state["human_confirmation"],
            st.session_state["insight"],
            force_fallback=force_fallback,
        )
        st.success("PR 稿件已生成。")
    draft = st.session_state.get("draft")
    if draft:
        st.markdown("#### 标题候选")
        for title in draft.title_options:
            st.markdown(f"- {title}")
        st.markdown("#### PR 正文")
        st.markdown(draft.press_release)
        st.markdown("#### 社媒短文案")
        for caption in draft.social_captions:
            st.markdown(f"- {caption}")
        st.markdown("#### 媒体 Pitch Email")
        st.code(draft.media_pitch_email)
        st.markdown("#### 中文策略说明")
        st.write(draft.chinese_strategy_summary)

with step5:
    st.subheader("Step 4.1 · 专家 Agent 协同审定")
    st.markdown("系统调用多个具备专业角色背景的 Agent 节点，对稿件进行多维度质量与合规性审查。")
    if st.button("运行专家协同审定", type="primary"):
        if "draft" not in st.session_state:
            st.warning("请先生成 PR 稿件。")
        else:
            st.session_state["expert_reviews"] = run_all_reviews(
                st.session_state["draft"],
                st.session_state["insight"],
                st.session_state["human_confirmation"],
                st.session_state["metadata"],
                st.session_state["information_report"],
            )
            st.success("四专家审定完成。")
    reviews = st.session_state.get("expert_reviews", [])
    if reviews:
        cols = st.columns(2)
        for idx, review in enumerate(reviews):
            with cols[idx % 2]:
                st.markdown(f"### {review.reviewer}")
                st.metric("Score", f"{review.score}/100")
                st.caption(f"Risk: {review.risk_level}")
                st.write(review.role)
                st.markdown("**Strengths**")
                for item in review.strengths:
                    st.markdown(f"- {item}")
                st.markdown("**Issues**")
                for item in review.issues:
                    st.markdown(f"- {item}")
                st.markdown("**Suggestions**")
                for item in review.suggestions:
                    st.markdown(f"- {item}")

with step6:
    st.subheader("Step 4.2 · 反馈修订与成果导出")
    feedback = st.text_area("修订建议", value="请让稿件更偏商业媒体口径，并进一步弱化技术参数堆叠。", height=120)
    if st.button("提交修订建议并生成版本说明"):
        if "draft" not in st.session_state:
            st.warning("请先生成 PR 稿件。")
        else:
            st.session_state["human_feedback"] = feedback
            st.session_state["revised_draft"] = run_revision(st.session_state["draft"], feedback)
            st.success("修订说明已生成。")
    if "draft" in st.session_state:
        if "expert_reviews" not in st.session_state:
            st.session_state["expert_reviews"] = run_all_reviews(
                st.session_state["draft"],
                st.session_state.get("insight") or run_pr_director_insight(st.session_state["metadata"], st.session_state["information_report"], st.session_state["human_confirmation"], force_fallback=True),
                st.session_state["human_confirmation"],
                st.session_state["metadata"],
                st.session_state["information_report"],
            )
        result = WorkflowResult(
            metadata=st.session_state["metadata"],
            information_report=st.session_state["information_report"],
            human_confirmation=st.session_state["human_confirmation"],
            task_plan=st.session_state["task_plan"],
            insight=st.session_state.get("insight") or run_pr_director_insight(st.session_state["metadata"], st.session_state["information_report"], st.session_state["human_confirmation"], force_fallback=True),
            draft=st.session_state["draft"],
            expert_reviews=st.session_state.get("expert_reviews", []),
            revised_draft=st.session_state.get("revised_draft"),
            human_feedback=st.session_state.get("human_feedback", ""),
        )
        st.session_state["workflow_result"] = result
        md = workflow_to_markdown(result)
        st.download_button("下载 Markdown", data=md.encode("utf-8"), file_name="global_pr_agent_output.md", mime="text/markdown")
        st.download_button(
            "下载 JSON",
            data=json.dumps(result.to_dict(), ensure_ascii=False, indent=2).encode("utf-8"),
            file_name="global_pr_agent_output.json",
            mime="application/json",
        )
        tmp = PROJECT_ROOT / "storage" / "export" / "global_pr_agent_output.docx"
        save_docx(result, tmp)
        st.download_button(
            "下载 DOCX",
            data=tmp.read_bytes(),
            file_name="global_pr_agent_output.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        st.markdown("#### 合规状态")
        st.success(result.compliance_status)
        st.markdown("#### 结果预览")
        st.markdown(md[:6000])
    else:
        st.info("请先完成内容生成。")
