# 需求分析说明书 · Global PR Agent

## 1. 问题定义

出海品牌在海外市场传播时，面临本土化叙事难、合规风险高、多端内容适配复杂等痛点。真实的 PR 业务流程并非简单的文案生成，而是一个包含深度市场情报分析、品牌意志确认、战略洞察推演、多维度专家审定和人类反馈的复杂协作链路。

本项目旨在构建一个 **出海品牌 PR 稿件生成 AI Agent 系统**。通过将 PR 工作流拆解为可治理的 Agent 节点，助力业务团队高效、稳健地完成从战略情报到最终发布稿件的全过程转化。

## 2. 设计原则

- **完备性**：覆盖从情报输入到文档导出的完整端到端链路。
- **稳定性**：内置规则引擎作为 Fallback，确保在不同网络环境下均能稳定产出。
- **可移植性**：通过 FastAPI 暴露核心 Agent 能力，支持灵活接入各类第三方自动化编排平台。

## 3. 目标用户

- 出海品牌 Marketing / PR 团队
- 跨境品牌运营负责人
- 需要标准化 PR 生产能力的代理商团队

## 4. 输入定义

### 4.1 任务元数据 (Task Metadata)
定义品牌基础信息、产品/业务属性、目标市场、目标语言及传播目标。

### 4.2 战略情报报告 (Information Search Report)
基于标准化的情报契约，输入包含品牌定位、竞品格局、受众画像、本地化策略建议及风险点在内的深度研究报告。

### 4.3 业务决策确认 (Human Confirmation)
由业务专家注入品牌格调、核心传播角度及特定的风险约束条件。

## 5. 输出定义

- 任务执行计划与澄清建议
- 战略洞察报告 (Brand & Market Insights)
- PR 稿件套装（正文、标题候选、社媒文案、媒体 Pitch 邮件）
- 多维度专家评审报告（内容、品牌、创意、风险）
- 修订版本说明
- 多格式文档包 (Markdown / JSON / DOCX)

## 6. 核心流程

```text
1. 任务配置 (Task Configuration)
2. 情报注入 (Intelligence Injection)
3. 决策确认 (Strategic Confirmation)
4. 战略洞察 (Insight Generation)
5. 内容生成 (Content Generation)
6. 专家审定 (Specialist Review)
7. 反馈修订 (Revision Loop)
8. 文档导出 (Exporting)
```

## 7. 实现范围界定

当前版本聚焦于核心 Agent 协作逻辑的跑通：
- 使用预置的标准化情报报告模拟上游搜索 Agent 的输出。
- 提供基于规则与 Prompt 的专家审核逻辑作为原型演示。
- 法律风险审核节点提供框架性建议，而非最终法律意见。

## 8. 技术栈选型

- **核心语言**：Python 3.10+
- **前端交互**：Streamlit
- **服务引擎**：FastAPI
- **数据契约**：Pydantic
- **模型驱动**：OpenAI-compatible LLM (OpenRouter / DeepSeek)
- **文档引擎**：python-docx
