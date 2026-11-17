---
name: yuheng-full-workflow
description: Use when the user explicitly requests a complete Yuheng feature from requirements through implementation and verified delivery.
metadata:
  version: 0.2.0
  entry: public
---

# yuheng-full-workflow

先读取 [SDD 契约](../yuheng-workflow-router/references/sdd-contract.md)。检查现有产物，从最早缺失阶段继续，保留已确认范围，不重做用户已批准的步骤。

1. [需求转规格](../yuheng-requirement-to-spec/SKILL.md)：生成 REQ/AC、明确契约和范围。
2. 按需补原型；已有明确批准的设计可复用，局部改造记录不适用理由。
3. [规格转计划](../yuheng-spec-to-plan/SKILL.md)：补齐任务、依赖和可执行验证。
4. [交付执行](../yuheng-delivery-execution/SKILL.md)：按当前任务拆分后端和前端子任务，仅加载适用的交付技能，测试先行并验证 API/UI/迁移。
5. 验证后使用 [自检](../yuheng-self-review/SKILL.md) 与 [完成前验证](../verification-before-completion/SKILL.md)：逐 AC 核实交付证据。

每阶段执行门禁。完整实施授权允许继续完成范围内技术工作；遇到必须由业务决定的新行为才停下具体受阻步骤。`BLOCKED` 不进入依赖它的实现或发布。该技能不默认提交、推送或发布。
