# Global PR Agent · 出海品牌 PR 稿件生成工作流

> 出海品牌 PR 稿件生成 AI Agent
> 技术底座：Python + Streamlit + FastAPI + OpenAI-compatible LLM
>
> 本项目基于 [MIT License](./LICENSE) 开源发布。

## 1. 项目定位

Global PR Agent 是针对出海品牌传播需求设计的 **AI Agent 协作系统**。

它将复杂的出海 PR 流程拆解为标准化、可治理的 Agent 工作流：通过接入深度市场情报，结合人类专家的战略意图，产出具备本土化洞察的 PR 稿件套装，并通过多维度专家 Agent 协同审核，确保内容的品牌一致性与合规性。

## 2. 实际运行效果预览

完整使用流程截图与阶段说明见 **[使用过程.md](./使用过程.md)**，涵盖从首页输入到文档导出的全部 8 个关键节点。

## 3. 本阶段核心关注点 (Current Focus)

本系统在构建时遵循严谨的项目管理思维，但当前的**核心关注焦点**明确锁定在 **PR 生成 Agent 的质量与逻辑链路**上。

### 核心攻坚点：
- **战略推演逻辑**：如何将非结构化的战略情报转化为具备本土化洞察的 PR Narrative，而非简单的文案润色。
- **多 Agent 协同审核机制**：通过不同角色背景的 Agent 节点（品牌、法律、创意等）形成闭环反馈，解决 AI 生成内容的合规性与一致性痛点。
- **情报-决策-生成联动**：确保从 Step 1 的情报输入到 Step 2 的人类干预，能够精准驱动 Step 4 的内容产出。

### 路线图说明：
为了确保核心 Agent 能力的深度，本阶段**有意推迟**了诸如“实时联网搜索执行”、“多租户权限系统”等外围功能的开发。这些功能已在架构设计中预留接口，但目前的交付重点是 **PR 生成 Agent 的专业度与工作流的严密性**。

## 4. 阅读引导 (Reading Guide for Reviewers & LLMs)

为了完整理解本项目的设计思路与工程演进，建议按照以下顺序审阅：

1. **工程演进记录 (Spec)**: 记录了系统的迭代过程。
   - 重点关注 `spec/05_chatbot_refactoring_plan.md` 与最近的重构记录，了解系统如何从传统的表单填报（Form-based）演进为**动态会话式（Conversational）**，并加入了严格的人机交互边界（Human-in-the-loop）。
2. **技术文档 (Docs)**: 系统的静态技术全景。
   - `docs/02_technical_design.md` 说明了架构分层。
   - `docs/interactive_design.html` 提供了交互的原型概念。
3. **核心源代码 (Src)**: `src/global_pr_agent/` 与 `app_chat.py` 展示了状态机编排与大模型动态调用的具体实现。
4. **纯前端备用方案**: 本项目在 `frontend/` 目录下提供了一套基于 Vue 3 的独立备用前端，以验证系统的 API 解耦能力。

## 5. 核心工作流 (Conversational Flow)

本系统采用 **State-Machine 驱动的会话流**，将出海 PR 场景拆解为高度协作的 Agent 节点。每个节点都强制加入**人类确认（Keyword Gating）**，确保人类拥有一票否决权：

1. **任务启动 (TASK_START)**：人类输入 PR 目标，Agent 动态生成澄清问题与执行计划。
2. **情报补充 (INTELLIGENCE_INPUT)**：人类以自然语言回答问题，提供本地化约束。
3. **业务决策 (BUSINESS_CONFIRM)**：Agent 结合底层报告与人类补充，提炼【核心PR角度、本土化策略、品牌调性】。支持在此阶段无限次打回重写。
4. **战略洞察 (DIRECTOR_INSIGHT)**：资深 PR Director 生成多维度战略洞察报告。
5. **内容生成与专家审定 (DRAFT_REVIEW)**：一站式生成 PR 初稿，并立刻调用四位专家 Agent（内容、品牌、创意、法务）以全中文进行严苛批斗与打分。
6. **反馈修订 (FEEDBACK_REVISE)**：人类可继续下达修改指令，或直接「导出」最终文档包。

## 6. 快速上手

### 6.1 环境准备

确保已安装 Python 3.10+。建议使用虚拟环境：

```bash
uv venv
uv pip install -r requirements.txt
```

### 6.2 配置 LLM API (必需，以激活完整动态智能)

在根目录创建 `.env` 文件。系统会自动读取环境变量加载 API Key。这是激活会话流动态推理、动态生成和专家严格审核的前提：

```bash
cp .env.example .env
export LLM_API_KEY="sk-xxxx"
export LLM_BASE_URL="https://api.deepseek.com"
export LLM_MODEL="deepseek-chat"
```

### 6.3 启动动态会话 UI (Chatbot)

系统前端采用极简的暗黑模式（Dark Mode），提供专注的沉浸式交互体验。

```bash
uv run streamlit run app_chat.py
```

**推荐 Demo 体验路径：**
1. 在底部输入框输入：*“帮我调研问界 / AITO 品牌在阿联酋市场的 PR 推广机会，并设计一份面向阿拉伯地区、英文撰写的高端智能 SUV 品牌 PR 稿件”*
2. 观察 Agent 动态生成的**澄清问题**，并尝试回复你的业务见解（如：*强调高温适应性与售后保障*）。
3. 按照提示，在阶段内自由提出修改意见，待满意后，输入指令关键词（如：**确认计划**、**确认策略**、**确认生成**）放行至下一阶段。
4. 欣赏生成的 PR 初稿，并查看四位专家给出的**严苛全中文点评**。

### 6.4 命令行工具

```bash
uv run python cli.py --sample --out demo/generated
```

### 6.5 启动 API 服务

```bash
uvicorn api_server:app --host 0.0.0.0 --port 8111
```

---

## 7. 交付清单

📄 **规格说明 (Spec)**
- [00_需求分析](./spec/00_requirement_analysis.md)
- [01_工作计划](./spec/01_work_plan.md)
- [02_开发阶段计划](./spec/02_development_plan.md)
- [03_测试计划](./spec/03_test_plan.md)
- [04_任务清单](./spec/04_task_list.md)

📘 **技术与产品文档 (Docs)**
- [01_产品需求说明](./docs/01_requirement.md)
- [02_技术架构设计](./docs/02_technical_design.md)
- [03_功能操作指南](./docs/03_usage_guide.md)
- [04_平台迁移指南](./docs/04_platform_migration.md)
- [05_已知局限说明](./docs/05_known_limits.md)

---

## 8. 项目结构

```text
.
├── frontend/                           # 基于 Vue 3 的纯前端备用实现
├── app_chat.py                         # Web 动态会话系统主入口 (推荐)
├── app.py                              # 旧版静态表单系统入口
├── api_server.py                       # 能力服务层，供集成调用
├── cli.py                              # 命令行工具
├── demo_inputs/                        # 标准化输入契约与样例
├── src/global_pr_agent/
│   ├── schemas.py                      # Pydantic 核心数据模型
│   ├── orchestrator.py                 # 工作流编排引擎
│   ├── reviewers.py                    # 专家审定 Agent 逻辑
│   ├── report_loader.py                # 战略情报解析
│   └── exporter.py                     # 多格式文档生成器
├── docs/                               # 产品与技术文档体系
└── spec/                               # 项目规格与过程记录
```

## 9. 核心设计理念

1. **情报驱动 (Intelligence-Driven)**：PR 不再是单纯的文案创作，而是基于深度的市场搜索报告进行战略推演。
2. **人类协同 (Human-in-the-loop)**：在关键环节预留“人类确认”节点，确保 AI 产出符合品牌核心价值。
3. **专家协同 (Multi-Agent Review)**：通过多个具备专业角色的 Agent 协同审核，降低合规与品牌风险。
4. **能力解耦 (API-First)**：所有核心能力均通过 FastAPI 暴露，可自然接入 Dify、Coze, n8n 等外部编排系统。

## 10. 许可协议

本项目基于 [MIT License](./LICENSE) 开源。使用、复制、修改、合并、发布、分发、再许可及销售本软件的副本时，须保留原始版权声明与许可声明。

## 11. 免责声明

本系统旨在展示 AI Agent 在出海 PR 场景下的自动化协作流程。系统输出的法律风险提示仅供参考，不构成专业法律意见。正式发布稿件前请务必咨询当地法务与 PR 专家。
