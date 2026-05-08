# boot.md · 给 Codex / 下一轮 AI 的项目启动说明

## 项目背景

这是蓝色光标 FDE 笔试题目二“出海品牌 PR 稿件生成 AI Agent”的代码实现。当前版本已经完成一次从旧版 PR 生成器到“中台型 Agent 工作流 Demo”的重构。

候选人的核心表达目标：

> 完成比完整更重要，清晰比准确更重要。代码必须能跑，README 必须让 AI 评审快速判断完成度，架构必须自然迁移到 Dify / Coze / n8n。

## 当前主链路

1. 任务启动与 AI 反问
2. 读取 Information Search Agent 报告
3. 人类确认 PR 关键元数据
4. PR Director 生成洞察
5. PR Writer 生成稿件
6. 四专家审定
7. 人类反馈修订
8. 导出 Markdown / JSON / DOCX

## 当前样例

品牌：问界 / AITO  
目标市场：UAE  
目标语言：English  
上游输入：`demo_inputs/wenjie_sample_report.md/json`

## 运行命令

```bash
pip install -r requirements.txt
python cli.py --sample --out demo/generated --force-fallback
streamlit run app.py
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

## Codex 后续任务优先级

1. 先保证 `python -m compileall .` 无错误。
2. 再保证 `python cli.py --sample --out demo/generated --force-fallback` 可生成三类文件。
3. 再检查 Streamlit 是否能启动，按钮流程是否不会因 session_state 报错。
4. 再检查 FastAPI `/health` 与 `/api/generate-pr` 是否可调用。
5. 最后做 UI 文案小修和 README 命令核对。

不要重写项目，不要引入复杂数据库，不要真实联网搜索，不要实现真实法律合规。当前版本的目标是一个 48 小时可交付 Demo。
