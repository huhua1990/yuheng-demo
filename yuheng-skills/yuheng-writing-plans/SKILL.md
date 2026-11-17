---
name: yuheng-writing-plans
description: Use when Yuheng implementation tasks need precise files, dependency ordering, behavior tests and reproducible verification commands.
metadata:
  version: 0.2.0
  entry: specialist
---

# Yuheng 编写计划

读取 [SDD 契约](../yuheng-workflow-router/references/sdd-contract.md) 与冻结规格。沿用 Athena 的细粒度任务和测试先行原则，使用 [计划模板](../yuheng-spec-to-plan/assets/plan.md)。

- 先定位真实模块、相似实现和测试入口；不凭空写目录、接口或脚本名。
- 按可独立验证的结果拆任务并编号 `T-*`；声明前置依赖，关联 `REQ-*`、`AC-*`。
- 每个任务给出创建/修改/测试文件、输入输出、变更点、用例与关键断言、工作目录、红灯/绿灯命令和预期结果。
- 后端行为测试覆盖正常、非法输入、权限/租户相关边界；红灯必须来自行为断言。必要的测试装配先独立验证。
- 页面逻辑列出行为测试与浏览器操作；纯样式列视觉检查。迁移列 changelog、前置数据、验证、回滚和授权范围。
- 不使用“类似上个任务”“补适当测试”等省略，不要求未验证的大段生产实现提前写入计划。需要示例时使用已核实符号和最小可执行测试。
- 提交/推送/发布只在用户授权时列作执行动作，不把每个小步骤的提交当作默认要求。

输出可交由另一个 AI 独立执行的计划；逐条核对 AC 覆盖，记录确认依据与阶段门禁，再交回 [规格转计划](../yuheng-spec-to-plan/SKILL.md)。
