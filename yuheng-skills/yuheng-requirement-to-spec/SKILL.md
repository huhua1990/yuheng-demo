---
name: yuheng-requirement-to-spec
description: Use when Yuheng work starts from an idea, meeting notes or an incomplete requirement without an actionable specification.
metadata:
  version: 0.2.0
  entry: public
---

# yuheng-requirement-to-spec

先读 [SDD 契约](../yuheng-workflow-router/references/sdd-contract.md)，使用 [需求探索](../yuheng-brainstorming/SKILL.md) 和 [知识路由](../yuheng-knowledge-routing/SKILL.md)，核实业务归属和复用边界。

1. 查找已有需求和确认记录，提取目标用户、流程、范围与非范围。
2. 从仓库可确定的信息直接核实；只对影响业务决策的缺口提问，不能反复问已授权的实现细节。
3. 确定页面、API、数据关系、权限键、租户、异常、兼容和非功能约束；不适用项说明理由。
4. 用 [规格模板](assets/spec.md) 生成 `docs/specs/<workId>.md`，需求编号 `REQ-*`，验收编号 `AC-*`，验收写为可观测 Given/When/Then。
5. 自检需求矛盾、未决问题和源码契约差异，记录确认来源；未确认为 `READY_FOR_REVIEW`，授权范围明确且无业务缺口才可冻结。

输出规格路径、确认范围、门禁状态与剩余问题。规格完整且允许继续时进入 [规格转计划](../yuheng-spec-to-plan/SKILL.md)。只要求分析则完成规格阶段，不扩大为实现。
