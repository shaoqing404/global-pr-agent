# Speckit · Global PR Agent

## 1. 问题定义

出海品牌在海外市场传播时，需要快速且稳健地生成本土化 PR 稿件。真实的业务流程并非单点文案生成，而是包含深度情报分析、品牌意志确认、战略洞察推演、稿件生成、专家协同审定和人类反馈的完整协作链路。

本项目旨在构建一个 **出海品牌 PR 稿件生成 AI Agent 系统**。系统通过将 PR 工作流拆解为可治理的 Agent 节点，助力业务团队高效产出具备本土化洞察的传播内容。

## 2. 核心架构设计

- **模块化 Agent**：将 Director 洞察、正文撰写、合规审核等环节独立为不同的 Agent 节点。
- **结构化输入契约**：定义了 `InformationSearchReport` 标准，确保 Agent 具备可靠的战略情报支撑。
- **人类协同机制**：在关键环节预留人类专家确认节点，确保 AI 输出不偏离品牌内核。
- **多格式导出支撑**：支持一键导出 Markdown、JSON 及符合排版要求的 DOCX 文件。

## 3. 目标用户

- 出海品牌 Marketing / PR 部门
- 跨境品牌运营团队
- 专业 PR 代理商
- 企业 AI 中台架构师

## 4. 输入定义

### 4.1 任务元数据 (Task Metadata)
品牌名称、产品/业务描述、目标市场、目标语言、传播目标及交付约束。

### 4.2 战略情报报告 (Information Search Report)
包含品牌快照、产品线摘要、目标市场背景、竞品分析、受众画像、本土化策略及风险提示。

### 4.3 业务确认项 (Human Confirmation)
品牌格调、产品基调、战略底座、核心传播角度及本土化执行建议。

## 5. 输出定义

- AI 澄清建议与执行计划
- 战略洞察报告 (PR Insight)
- 多方案标题候选
- 英文 PR 稿件正文
- 社媒多端文案
- 媒体 Pitch 邮件
- 中文策略摘要
- 四维度专家审定报告 (Content, Brand, Creative, Legal)
- 修订版本说明

## 6. 核心流程

```text
1. 任务启动 (Task Start)
2. 情报注入 (Information Injection)
3. 决策确认 (Decision Confirmation)
4. 战略洞察 (Insight Generation)
5. 内容生成 (Content Generation)
6. 专家审定 (Specialist Review)
7. 反馈修订 (Revision Loop)
8. 系统导出 (Export)
```

## 7. 暂不涵盖范围

当前版本聚焦于核心协作流程的跑通，以下功能计划在未来版本中迭代：
- 实时联网搜索 Agent 的接入
- 深度法律合规自动化判断
- 企业级多级审批流与权限管理
- 生产级多机部署与日志审计

## 8. 技术栈

- **逻辑层**：Python 3.10+
- **展示层**：Streamlit
- **服务层**：FastAPI
- **模型层**：OpenAI-compatible LLM Gateway
- **文档层**：python-docx
- **契约层**：Pydantic

## 9. 验收标准

- 全项目通过 `compileall` 语法静态检查。
- 命令行工具 (`cli.py`) 可根据样例情报产出完整文档包。
- Web 交互系统 (`app.py`) 可流畅运行全链路 Agent 协作流程。
- FastAPI 核心端点 (`/api/generate-pr`) 响应正常且符合数据契约。
