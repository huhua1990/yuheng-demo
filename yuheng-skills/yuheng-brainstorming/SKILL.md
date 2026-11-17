---
name: yuheng-brainstorming
description: Use when a Yuheng feature has uncertain user goals, competing designs, unclear scope or unresolved behavior before specification.
metadata:
  version: 0.2.0
  entry: specialist
---

# Yuheng 需求探索

先读 [SDD 契约](../yuheng-workflow-router/references/sdd-contract.md)。参考 Athena 的上下文探索、方案比较和设计收敛方式，按任务规模执行，不引入其他环境才有的工具或审批步骤。

1. 阅读当前工程、已有规格和最相近实现，通过 [知识路由](../yuheng-knowledge-routing/SKILL.md) 确认复用与边界。
2. 区分已确认事实、可自行核实的技术细节和真正影响业务选择的问题。仅为最后一类提问，问题聚焦，不反复询问已提供的信息。
3. 有实际取舍时给出 2–3 个方案及推荐；目标和方案已由用户指定时直接评估可行性与影响。
4. 明确业务流程、API/页面契约、权限/租户、异常和可验收结果。按复杂度给出简要设计或完整设计。
5. 用户尚未授权设计时记录 `READY_FOR_REVIEW`；已有明确实施授权时按授权范围记录依据，未决业务差异单独确认。
6. 将结论交给 [需求转规格](../yuheng-requirement-to-spec/SKILL.md) 整理为同一份规格，不另写一份重复事实来源。

输出事实、设计选择、风险、待决策问题和来源。探索本身不修改业务代码；临时探查不得污染用户已有改动。
