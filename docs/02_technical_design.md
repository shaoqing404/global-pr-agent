# 技术文档

## 1. 技术架构

# 技术架构设计

## 1. 系统架构

```text
Streamlit 交互控制台
  |
  |-- 任务元数据输入与解析
  |-- 战略情报报告注入
  |-- 业务决策决策确认
  |-- 洞察 / 稿件 / 审定 / 导出 UI
  v
Agent 编排引擎 (Orchestrator)
  |
  |-- run_task_planning (任务规划)
  |-- run_pr_director_insight (战略洞察)
  |-- run_pr_generation (内容生成)
  |-- run_all_reviews (专家审定)
  |-- run_revision (反馈修订)
  v
LLM 适配层 / 本地规则引擎
  |
  |-- OpenAI-compatible API
  |-- 确定性规则 Fallback
  v
成果导出层
  |
  |-- Markdown / JSON / DOCX
  v
FastAPI 服务层 (API Server)
```

## 2. 核心模块

| 文件 | 作用 |
|---|---|
| `app.py` | 交互式业务控制台 |
| `api_server.py` | 能力服务层接口 |
| `cli.py` | 自动化脚本工具 |
| `schemas.py` | 结构化数据契约 (Pydantic) |
| `report_loader.py` | 战略情报解析与摘要提取 |
| `orchestrator.py` | Agent 工作流编排引擎 |
| `reviewers.py` | 专家 Agent 协作审核逻辑 |
| `exporter.py` | 工业级文档导出引擎 |
| `llm_client.py` | 多模型适配客户端 |

## 3. 版本演进说明 (Iteration)

本项目在开发周期内经历了两个阶段的架构演进：

### 第一阶段：单点功能探索 (Legacy)
初期侧重于验证 LLM 生成 PR 稿件的文案质量，建立了品牌资料库原型。相关模块已归档至 `src/global_pr_agent/legacy/`。

### 第二阶段：Agentic Workflow 系统化 (Current)
当前版本实现了基于工作流的架构重构，将单点生成扩展为包含情报注入、人类确认、Director 战略洞察、多维度专家审定的完整 Agent 协同系统。核心模型统一基于 `WorkflowResult` 契约。

## 4. 关键技术选型说明

- **Agent 编排**：采用轻量化 Python Orchestrator 模式，确保逻辑的可控性与易调试性。
- **数据契约**：全量使用 Pydantic 进行输入输出校验，确保护理链路的数据稳定性。
- **模型策略**：支持 OpenAI 标准协议模型接入。未配置 API Key 时，系统将自动降级至本地规则引擎，确保业务连续性。
- **安全性**：采用环境变量管理密钥，API 接口预留基于 Token 的鉴权机制。


## 4. 数据流

```text
TaskMetadata + InformationSearchReport
  -> run_task_planning
  -> HumanConfirmation
  -> run_pr_director_insight
  -> run_pr_generation
  -> run_all_reviews
  -> run_revision
  -> WorkflowResult
  -> export
```

## 4. API 设计

### POST /api/generate-pr

一站式执行完整流程。

请求体：

```json
{
  "metadata": {},
  "information_report": {},
  "human_confirmation": {},
  "human_feedback": "",
  "force_fallback": true
}
```

如果不传入任何字段，服务会使用内置问界样例报告。

### POST /api/plan

生成任务反问和计划。

### POST /api/insight

生成 PR Director Insight。

### POST /api/generate

生成 PR Draft。

### POST /api/review

运行四专家审定。

## 5. 安全设计

- 不硬编码真实 LLM API Key。
- API Key 通过环境变量传入。
- `ACCESS_TOKEN` 仅用于轻量鉴权。
- 生产环境应使用 API Gateway、SSO、Secret Manager、调用审计和权限分级。

## 6. 模型策略

- 默认模型网关：OpenAI-compatible Chat Completions。
- 默认 DeepSeek 配置：`LLM_BASE_URL=https://api.deepseek.com`、`LLM_MODEL=deepseek-chat`。
- 如果无 API Key 或模型调用失败，则使用本地 fallback。

## 7. 数据库设计

本次新主流程不依赖数据库。旧版 `database.py` 保留用于兼容品牌信息管理思路。生产环境可扩展：

- 品牌资料库
- 市场报告库
- PR 历史稿件库
- 审核记录表
- 反馈与版本表
