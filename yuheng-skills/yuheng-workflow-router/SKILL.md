---
name: yuheng-workflow-router
description: Use when a Yuheng request mixes requirements, specifications, plans, coding or verification, or the next SDD stage is unclear.
metadata:
  version: 0.2.0
  entry: public
---

# yuheng-workflow-router

根据已有产物与授权选择一个入口。先读取 [SDD 契约](references/sdd-contract.md) 和当前工程 `yuheng-task-entry`、`yuheng-phase-gate` 规则。

路由顺序：

| 输入/现状 | 下一步 |
|---|---|
| 新建工程、复制模板、计划治理快照刷新 | 先用 [初始化体检](../yuheng-init-project-postcheck/SKILL.md) 的只读检查，再选入口 |
| 业务模板源码复制、接入或消费流程验证 | 结合当前阶段使用 [业务模板迁移](../yuheng-business-template-migration/SKILL.md) |
| 报错、异常、功能失效 | 先按 `debug-log-first` 采集日志/复现；精简修复规格和计划后进入交付 |
| 仅原始想法、会议纪要 | [需求转规格](../yuheng-requirement-to-spec/SKILL.md) |
| 规格已确认，尚无可执行计划 | [规格转计划](../yuheng-spec-to-plan/SKILL.md) |
| 计划已确认，要求实现或补验证 | [交付执行](../yuheng-delivery-execution/SKILL.md) |
| 代码已存在，只要求验收/状态但规格或计划位置不明 | [交付执行](../yuheng-delivery-execution/SKILL.md)：先检查现状、定位授权和验证入口；独立验证可继续，上游证据缺失保持阻塞，不补造文档或红绿证据 |
| 明确要求从需求完整实施 | [完整流程](../yuheng-full-workflow/SKILL.md) |

“生成 CRUD”或“创建页面”仍先判断规格/计划，不直接绕到专项技能。已有规格或计划先读实际内容和确认依据，不能仅看文件名判断冻结。

输出：当前工程/`workId`、前置动作、当前阶段、一个推荐入口、现有证据/缺口、下一步。只要求路由则到此；要求做事则继续执行被选技能。
