# 界面与交互重构计划 (ChatBot UX Pivot)

## 1. 业务目标重对齐
根据业务专家的最新评估要求，系统交互方式需从“表单步进式 (Form-step)”全面升级为“对话交互式 (ChatBot)”，核心变化及应对策略如下：

- **对话驱动状态流转**：摒弃前端 UI 强绑定的 Tab 切换，采用 Streamlit 原生的 `st.chat_message` 构建全局聊天流。所有的状态推进（如“确认”）必须由用户的显式意图驱动，而不是大模型自动黑盒判断，确保系统的可控性。
- **非结构化文档提取**：用户上传 TXT/Word/Markdown 后，系统需要通过大模型显式地进行 `Extraction`，将其映射为标准的 `InformationSearchReport`。
- **显式的多语言本土化**：在最终的内容定稿后，不能将其仅仅视为一个隐藏属性，必须提供一个明确的对话节点或指令，让大模型执行目标语言翻译和本土化润色，并一并打包导出。

## 2. 后端架构策略：“换壳不换心”
**绝对不引入重量级的 OpenAI Agent SDK (如 Assistants API / Swarm)**。
- *理由*：一旦引入，系统将强依赖模型的 Function Calling 能力。这会彻底破坏我们现有的“本地无 Key 规则 Fallback”机制。
- *执行方案*：底层 `orchestrator.py`, `reviewers.py`, `exporter.py` 保持完全不变。只在前端包裹一层自定义的**有限状态机 (State Machine)** 来调度这些能力组件。

## 3. 状态机定义 (State Machine Schema)
在新的前端入口 `app_chat.py` 中，定义如下 6 个明确的状态流转：

```python
class AgentState(Enum):
    TASK_START = 0          # 任务启动，收集基础 Metadata
    INTELLIGENCE_INPUT = 1  # 战略情报输入与非结构化提取
    BUSINESS_CONFIRM = 2    # 业务决策确认（人类确认信息并下发策略指令）
    DIRECTOR_INSIGHT = 3    # 输出 PR Director 洞察并询问是否调整
    CONTENT_GENERATE = 4    # 组合执行 生成(Generate)+审定(Review)，输出初稿与评审意见
    FEEDBACK_REVISE = 5     # 多轮对话修改循环，并包含【翻译与多语言本土化】逻辑，最后触发导出
```

## 4. 关键节点的 LLM 增强与设计

### 4.1 非结构化文档提取 (`extract_from_document`)
在 `report_loader.py` 中新增 `extract_from_document_via_llm` 函数。
- **机制**：将用户上传的长文本发送给 LLM，配以结构化 JSON Prompt，强行映射至 `InformationSearchReport` Schema。
- **失败与降级**：如果提取失败（如 Token 超限或 JSON 格式错误），系统将触发 Fallback 机制，返回默认的“问界样例”数据兜底，同时在对话框向用户提示：“提取失败，已加载预置的结构化情报底座以供演示”。

### 4.2 生成与审定的合并调度
在 `CONTENT_GENERATE` 状态下，系统将在后台同步执行 `run_pr_generation` 和 `run_all_reviews`。
AI 在聊天框的回应形如：
> “我已经完成了初稿的撰写（附链接/预览）。同时，系统内的四位虚拟专家给出了如下意见：合规专家提示词汇风险... 品牌专家认为调性一致...。您希望如何修改？或者，确认定稿后，我们可以进行多语言翻译。”

### 4.3 显式的本土化翻译步骤
在 `FEEDBACK_REVISE` 状态下，除了接收常规的修改指令（如“写短一点”），系统还会显式侦听用户的多语言需求。
- 当用户要求“翻译成阿拉伯语”或确认定稿进入导出前，AI 必须触发一个独立的翻译 Prompt。
- 最终导出的 DOCX 和 JSON 中，将显式包含 Translation/Localized 版本的记录。
