# Vue 3 前端重构架构说明 (Vue Frontend Pivot)

## 1. 架构升级动机
为了满足真正“生产级 (Production-ready)”交付标准，同时彻底实现前后端能力解耦，我们将前端从强依赖 Python 的 Streamlit 框架，重构为基于 **Vue 3 + Vite + TailwindCSS** 的现代单页应用 (SPA)。

这种架构带来的核心优势：
- **纯粹的 API-First**：前端完全通过 FastAPI 接口与后端交互，完美证明了系统可无缝迁移至任何企业内部前端、Dify 或 n8n 等平台。
- **状态管理更健壮**：摆脱了 Streamlit 诡异的重绘机制，可以在前端精确控制大模型调用的 loading 状态和用户聊天上下文。
- **定制化 UI 支持**：轻松实现分流落地页 (Demo vs. Prod)、更精细的对话气泡样式以及炫酷的交互式数据流图。

## 2. 前端目录结构 (`frontend/`)
```text
frontend/
├── package.json               # 依赖配置 (Vue, Vite, Tailwind, Axios)
├── vite.config.js             # 构建配置与后端 Proxy 设置
├── tailwind.config.js         # CSS 样式配置
├── src/
│   ├── main.js                # Vue 入口
│   ├── style.css              # 全局样式
│   ├── App.vue                # 根组件：管理全局状态与页面路由
│   └── components/
│       ├── WelcomeScreen.vue  # 初始化落地页 (区分演示/生产模式)
│       └── ChatInterface.vue  # ChatBot 主交互界面与状态机
```

## 3. 核心机制设计

### 3.1 双轨启动模式 (Welcome Screen)
借鉴 OpenAI 的设计，用户在进入系统时被要求选择模式：
- **演示模式 (Demo Fallback)**：无需配置 API Key。后端强制使用内置模板和问界样例，确保在面试环境下 100% 不翻车。
- **生产模式 (Production)**：要求用户输入 `ACCESS_TOKEN`，系统全面激活大模型生成与长文本智能抽取功能。

### 3.2 ChatBot 状态机 (Chat State Machine)
在 `ChatInterface.vue` 中，用 JavaScript 完整复现了之前设计的 6 个状态枚举：
- `0: TASK_START`
- `1: INTELLIGENCE_INPUT` (集成大模型智能文件抽取逻辑)
- `2: BUSINESS_CONFIRM`
- `3: DIRECTOR_INSIGHT`
- `4: CONTENT_GENERATE` (将生成与 4 专家审定打包调用)
- `5: FEEDBACK_REVISE` (多轮对话、多语言翻译循环)

### 3.3 异步交互与非结构化上传
前端使用 `FileReader` 读取用户上传的 TXT/MD 文档，将其作为纯文本通过 `/api/extract` 发送给 FastAPI 服务。后端通过 Prompt 将其映射为标准的 JSON Schema 后返回，前端将其挂载至上下文，实现“非结构化到结构化”的平滑过渡。

## 4. 后端接口适配 (api_server.py)
为支撑 Vue 前端的独立运行，后端增加了以下关键改造：
- **CORS 跨域支持**：挂载了 `CORSMiddleware`，允许来自 Vite dev server (5173) 的跨域请求。
- **Extraction Endpoint**：新增了 `POST /api/extract` 路由，专职处理前端长文本智能解析请求。
