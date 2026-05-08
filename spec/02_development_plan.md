# 开发阶段计划 · Global PR Agent

## 阶段 1: 基础设施 (Hour 1-8)
- [x] 初始化项目结构。
- [x] 定义 `schemas.py` 核心数据模型。
- [x] 实现 `llm_client.py` 适配 OpenAI 标准接口。
- [x] 准备 `demo_inputs` 中的 DeepResearch 样例报告。

## 阶段 2: Agent 核心逻辑 (Hour 9-24)
- [x] **Orchestrator:** 实现 PR Director Insight 和 Draft 生成逻辑。
- [x] **Report Loader:** 实现 JSON/Markdown 提取与清洗。
- [x] **Reviewers:** 实现四专家审定（Content, Brand, Creative, Legal）。
- [x] **Fallback:** 实现无 API Key 的确定性模板输出。

## 阶段 3: 界面与接口 (Hour 25-40)
- [x] **Streamlit:** 开发 7 步骤交互流程。
- [x] **FastAPI:** 暴露 `/api/generate-pr` 等核心端点。
- [x] **Exporter:** 实现多格式导出，补全 DOCX 字段。

## 阶段 4: 质量与交付 (Hour 41-48)
- [x] 清理旧版冗余文件。
- [x] 补齐 `spec/` 规格说明文件夹。
- [x] 运行全链路回归测试。
- [x] 编写 `04_platform_migration.md` 迁移指南。
