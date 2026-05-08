# 项目审阅清单

## 1. 核心链路验证

- **环境检查**：`python -m compileall .` 确认语法无误。
- **命令行工具**：`python cli.py --sample --out demo/generated` 验证全链路自动化生成能力。
- **交互系统**：`streamlit run app.py` 验证人类协同 (Human-in-the-loop) 流程。
- **接口服务**：`uvicorn api_server:app` 验证能力的 API 化沉淀。

## 2. 关键文档索引

- **系统设计**：[技术架构设计](./02_technical_design.md)
- **业务契约**：[产品需求说明](./01_requirement.md)
- **集成指南**：[平台迁移指南](./04_platform_migration.md)
- **运营约束**：[已知局限说明](./05_known_limits.md)

## 3. 设计亮点总结

1. **工作流 Agent 化**：将 PR 生产链路拆解为多个专业 Agent 节点，支持灵活编排。
2. **战略情报驱动**：基于结构化情报报告进行生成，解决 LLM “幻觉”与叙事偏离问题。
3. **闭环审定机制**：内置内容、品牌、创意、合规四个维度的专家 Agent 审核回路。
4. **工业级配套**：提供 Markdown、JSON、DOCX 多格式导出，满足业务最终交付需求。

## 4. 验证记录

详细验证日志请参考 [docs/07_internal_validation.md](./07_internal_validation.md)。
