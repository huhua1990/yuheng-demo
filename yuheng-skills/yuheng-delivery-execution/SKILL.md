---
name: yuheng-delivery-execution
description: Use when a Yuheng plan is approved and the task requires implementation, regression fixes, integration checks or delivery evidence.
metadata:
  version: 0.2.0
  entry: public
---

# yuheng-delivery-execution

按 [SDD 契约](../yuheng-workflow-router/references/sdd-contract.md) 读取规格、计划、确认依据和已有工作区修改。输出 `PHASE_GATE`，必需证据缺失时先补齐，不能自行乐观填 `implementationAllowed: true`。

## 执行链路

先 [知识路由](../yuheng-knowledge-routing/SKILL.md)，再按计划执行：

- 后端：[后端交付](../yuheng-backend-delivery/SKILL.md) → [TDD](../test-driven-development/SKILL.md) → [API 验证](../yuheng-api-verification/SKILL.md)。
- 前端：[页面交付](../yuheng-page-delivery/SKILL.md) → 行为测试/视觉检查 → [UI 验证](../yuheng-ui-verification/SKILL.md)。
- 菜单、角色或按钮权限：额外执行 [菜单交付](../yuheng-menu-delivery/SKILL.md)。
- 混合任务先按依赖实现契约与后端，再接前端；能独立验证的任务可以分开推进。
- 治理/文档任务：执行相关结构、资源引用、同步或情景验证；无需创建业务 CRUD 文件来凑数量。

每个任务更新计划状态，记录红灯原因、最小实现、绿灯与适用联调结果。发现业务/契约偏离先更新受影响规格与计划并获取该差异的决策；范围内的技术调整记录后继续。

## 交付出口

使用 [证据模板](assets/verification.md) 写入 `docs/verification/<workId>/verification.md`。完成 [自检](../yuheng-self-review/SKILL.md) 与 [完成前验证](../verification-before-completion/SKILL.md)，逐个核对 AC 的实际证据。专项技能按需读取已有结果；不要循环调用已完成的验证技能或重复生成同一证据。

输出实现行为、变更范围、实际验证结果、证据路径和剩余限制。必需服务不可用或测试未执行，记录 `BLOCKED` 及补验步骤，不宣称全部完成；不得为了绿灯降低验收标准或删除失败测试。
