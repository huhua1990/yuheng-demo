---
id: yuheng-sdd-traceability
version: 0.2.0
scope: core-and-consumer
---

# SDD 追踪与规格漂移

- 同一任务沿用 `workId` 和三类版本；默认规格 `docs/specs/<workId>.md`、计划 `docs/plans/<workId>.md`、证据 `docs/verification/<workId>/verification.md`，用户已有指定路径优先。
- 需求编号 `REQ-*`、验收 `AC-*`、任务 `T-*`；每个 AC 对应实现任务和实际验证，不允许孤立需求、无验收任务或只写“测试通过”。
- 每份产物引用上游路径和版本/确认依据；改变规格须列出受影响 REQ、AC、任务与回归范围。
- 范围内技术细节调整更新计划和依据后继续；改变业务行为或兼容契约须获取对应差异的决策。
- 不修改验收标准以掩盖失败，不将预期输出、示例日志、别次测试结果写成本次证据。
- 模板生成后替换全部占位符；无法确定的信息列为未决问题，保留真实阶段状态。
