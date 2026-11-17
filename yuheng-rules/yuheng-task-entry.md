---
id: yuheng-task-entry
version: 0.2.0
scope: core-and-consumer
---

# Yuheng 任务入口

每个任务开始时先判断它属于需求、规格、计划、交付、验证、同步或故障排查。没有明确目标、范围、验收标准或验证方式时，先补齐最小规格。

任务入口必须记录：

1. `workId` 和目标；
2. 影响的后端、前端、数据库、权限和租户边界；
3. 当前代码、治理和知识版本；
4. 预期产物与验证命令；
5. 失败时的回滚或豁免方式。

紧急修复可以缩短规格，但必须在同一 `workId` 下补齐验证和复盘。

公开入口为 `yuheng-requirement-to-spec`、`yuheng-spec-to-plan`、`yuheng-delivery-execution` 和 `yuheng-workflow-router`。完整实施使用 `yuheng-full-workflow`。专项技能只作为对应阶段的执行单元，不因用户说“创建页面”或“生成 CRUD”而绕过规格与计划。

新工程/快照刷新先用 `yuheng-init-project-postcheck`；故障先执行 [日志优先](debug-log-first.md)，再用精简规格进入交付。已有产物从实际路径读取，确认授权来源，不根据文件名猜冻结状态。
