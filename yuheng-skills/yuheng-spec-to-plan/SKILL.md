---
name: yuheng-spec-to-plan
description: Use when an approved Yuheng specification exists and development needs task boundaries, dependencies and executable acceptance checks.
metadata:
  version: 0.2.0
  entry: public
---

# yuheng-spec-to-plan

读取 [SDD 契约](../yuheng-workflow-router/references/sdd-contract.md)、实际规格与确认来源。规格未冻结或存在影响实现的业务缺口时，补规格，不制造一份看似可执行的计划。

1. 执行 [任务拆解](../yuheng-task-decomposition/SKILL.md)，核实前后端和数据库边界、现有能力及消费端影响。
2. 页面需要设计但未确认时先补最小原型/交互说明；已有批准设计或局部改造记录来源和不另做原型的理由。
3. 执行 [编写计划](../yuheng-writing-plans/SKILL.md)，使用 [计划模板](assets/plan.md)，保存 `docs/plans/<workId>.md`。
4. 每个任务提供 REQ/AC、输入输出、真实文件、依赖、行为测试、红灯/绿灯命令、API/UI/迁移验证和回滚方式。
5. 核对每个 AC 均有任务和验证入口；记录授权来源，依契约冻结或提交待审。

计划只列预期验证，禁止写成已通过。输出路径、覆盖关系、门禁与风险；已授权实施且门禁通过，进入 [交付执行](../yuheng-delivery-execution/SKILL.md)。
