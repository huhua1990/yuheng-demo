# Yuheng 消费端开发入口

本项目通过版本化 `yuheng-server` 和 `yuheng-ui` 使用 core，业务模块及其迁移由本项目维护。开始任务前确认 Git 状态，保留已有业务修改。

共享规则位于 `yuheng-rules/`，共享技能位于 `yuheng-skills/`，框架知识位于 `ai-knowledge-core/`。先读取 `yuheng-ai-operating-principles`、`yuheng-task-entry`、`yuheng-phase-gate` 和 `yuheng-sdd-traceability`，再按任务加载相关规则及技能。规则与技能快照由 core 同步工具维护，不直接修改；项目差异维护在 `consumer-overlay/`。

本项目使用 `需求 → 规格 → 计划 → 实施 → 验证` 工作流。根据阶段使用 `yuheng-requirement-to-spec`、`yuheng-spec-to-plan`、`yuheng-delivery-execution` 或 `yuheng-workflow-router`；新工程或快照刷新后运行 postcheck。用户仅要求分析或计划时止于该阶段。

消费端不得依赖 core 源码目录。数据库操作先确认实际迁移工具、配置与授权；已执行迁移不得改写。业务规则、权限、租户及前后端行为变更须有对应验证证据，失败或未执行的检查不得标记通过。

同步与检查命令见 `sync/skills/sync-specs/SKILL.md`。同步只替换托管资产，不覆盖业务代码、`consumer-overlay/` 和 `docs/` 中项目自有内容。
