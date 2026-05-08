# 功能操作指南 · Global PR Agent

## 1. 环境配置

本项目建议使用 Python 3.10+。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**可选 LLM 配置**（在 `.env` 文件中设置）：

```bash
LLM_API_KEY="您的 API Key"
LLM_BASE_URL="https://api.deepseek.com"
LLM_MODEL="deepseek-chat"
```
*注：未配置 API Key 时，系统将自动进入本地规则模式。*

## 2. 交互式控制台操作流程

启动控制台：
```bash
streamlit run app.py
```

### Step 0: 任务初始化
填写品牌基础信息、目标市场及传播目标。点击“生成/刷新任务计划”以同步 Agent 执行状态。

### Step 1: 战略情报注入
点击“加载问界/AITO 样例报告”注入标准化情报，或手动上传符合系统的 JSON 情报文件。

### Step 2: 业务决策确认
系统将根据情报自动提取推荐配置。业务专家可在此微调品牌调性、传播主线及合规约束，并点击“确认”以锁定生成底座。

### Step 3: Director 战略洞察
触发战略洞察 Agent，系统将输出深度品牌洞察与本土化建议，这是内容生成的核心战略依据。

### Step 4: 内容生成与多端适配
触发内容生成 Agent，一站式获得 PR 稿正文、标题组、社媒文案及媒体 Pitch 邮件。

### Step 5: 专家协同审定
启动专家 Agent 节点。系统将从内容结构、品牌一致性、创意价值、合规性四个维度自动反馈评审意见。

### Step 6: 版本修订与导出
根据专家建议提交修订指令。最后通过导出模块一键获取全套文档（Markdown / JSON / DOCX）。

## 3. 自动化脚本 (CLI)

用于批量测试或自动化流水线调用：
```bash
python cli.py --sample --out demo/generated
```

## 4. 能力服务接口 (API)

启动 API 服务：
```bash
uvicorn api_server:app --host 0.0.0.0 --port 8111
```
可通过 Swagger UI (`/docs`) 查看接口详情。

## 5. 核心价值展示点

在操作本系统时，请关注以下四个关键能力点：
1. **工作流闭环**：不仅仅是文案生成，而是覆盖了情报解析到审定导出的全生命周期。
2. **战略对齐**：通过“Director 洞察”环节确保了传播内容具备真实的策略深度。
3. **人类干预**：在决策确认和反馈修订节点，人类专家的意志被精准注入 Agent 逻辑。
4. **API 化交付**：所有的 Agent 节点均可作为标准化服务，快速集成至企业现有的协同平台。
