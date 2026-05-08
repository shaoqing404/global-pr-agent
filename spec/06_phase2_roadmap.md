# Phase 2 规划：网页链接解析 & 知识库

## 背景

在当前 Demo（Phase 1）中，系统支持两种品牌信息输入方式：
1. **问界 / AITO 样例报告**：内置的标准化 DeepResearch 情报底座
2. **文档上传**：用户上传 txt/md 文件，LLM 自动提取结构化情报

以下两个入口在 WELCOME 界面以灰色禁用卡片显示，并注明"即将推出"，
属于 Phase 2 功能，已在架构层预留接入点。

---

## Phase 2 · Feature A：网页链接解析

### 目标
用户粘贴品牌官网、新闻稿链接或竞品页面 URL，系统自动抓取正文并提取结构化品牌情报。

### 技术方案

```python
# report_loader.py 新增函数（预留接口）
def load_from_url(url: str, llm_client: LLMClient | None = None) -> Dict[str, Any]:
    """
    1. requests.get(url, timeout=15) 抓取 HTML
    2. BeautifulSoup 提取 <body> 文本，清理广告/导航噪声
    3. 截断至 12000 字符，调用 extract_from_document_via_llm()
    4. 失败时 Fallback 至样例报告
    """
    ...
```

### 依赖
```
beautifulsoup4>=4.12.0
lxml>=4.9.0
```

### UI 变更
- WELCOME 界面"网页链接解析"卡片启用
- 点击后主区域显示 URL 输入框 + "解析"按钮
- 解析成功后与文档上传流程合并，进入 TASK_START

### 风险
- 部分网站有反爬虫机制，需添加 User-Agent 和 robots.txt 检查
- 长页面 token 超限问题与文档上传一致，用同一截断策略处理

---

## Phase 2 · Feature B：品牌知识库

### 目标
持久化存储历史品牌信息、PR 稿件和审定记录，支持跨任务检索复用。

### 技术方案

| 组件 | 选型 | 说明 |
|------|------|------|
| 向量存储 | ChromaDB / Qdrant | 本地部署，无需云服务 |
| Embedding | text-embedding-3-small | OpenAI-compatible |
| 检索接口 | LangChain Retriever | 或直接调用 Chroma Python SDK |

### 数据库表设计（SQLite 扩展）

```sql
-- 品牌资料库
CREATE TABLE brand_assets (
    id INTEGER PRIMARY KEY,
    brand_name TEXT NOT NULL,
    asset_type TEXT,        -- 'report' | 'draft' | 'review'
    content TEXT,
    embedding_id TEXT,
    created_at TEXT
);

-- PR 历史稿件
CREATE TABLE pr_history (
    id INTEGER PRIMARY KEY,
    brand_name TEXT,
    target_market TEXT,
    press_release TEXT,
    score INTEGER,
    created_at TEXT
);
```

### UI 变更
- WELCOME 界面"知识库"卡片启用
- 侧边栏增加"品牌资产管理"面板
- Step 1（情报输入）增加"从知识库检索"选项

---

## 实施优先级

| 功能 | 优先级 | 预计工时 |
|------|--------|---------|
| 网页链接解析 | P1 | 1.5 天 |
| 品牌知识库（存储+检索） | P2 | 3 天 |
| 知识库 UI 集成 | P3 | 1 天 |
