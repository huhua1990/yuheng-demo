---
name: yuheng-backend-delivery
description: Use when Yuheng 已确认任务涉及后端接口、Service、Mapper、数据契约或后端行为修复。
metadata:
  version: "0.2.0"
  entry: specialist
---

# Yuheng 后端交付

遵守 [SDD 契约](../yuheng-workflow-router/references/sdd-contract.md)，先读规格、计划、确认来源和已有修改。
沿用 `workId`、REQ/AC/T 及 `codeVersion`、`governanceVersion`、`knowledgeVersion`，不另起脱离任务的完成报告。

## 实现前

1. 确认规格、计划已冻结，相关兼容评估齐全，`PHASE_GATE.implementationAllowed: true` 有证据支撑。
2. 缺规格或计划时回到 [流程路由](../yuheng-workflow-router/SKILL.md)；已有完整实施授权的范围内细节由 AI 补录后继续。
3. 用 [知识路由](../yuheng-knowledge-routing/SKILL.md) 定位后端规则、能力索引、同模块实现及测试入口。
4. 划清 core 框架能力与消费端业务定制；按计划确认允许修改与禁止修改的文件范围。

## 按既有契约实现

- 先找同一能力的 Controller、VO、Service/Impl、Mapper 和 DO，只新增验收所需文件，不固定生成八类 CRUD 产物。
- 核对真实方法签名与依赖；现有 Service 接口加 Impl 并不普遍继承 `ServiceImpl`，不得批量改造继承关系。
- 保留实际 HTTP 方法、路径、参数位置和响应语义；查询可为 GET，修改可为 PUT，删除可为 DELETE，不能统一改 POST。
- 复用已存在的 `CommonResult`、`PageResult`、校验、异常与上下文能力；以当前模块用法确认类型和边界。
- 按 AC 核对权限标识、租户条件、数据权限、事务、唯一性及关联约束，避免仅验证正常保存。
- 先按 [TDD](../test-driven-development/SKILL.md) 运行行为断言红灯，再写最小实现，重跑同一测试转绿并做相关回归。
- 新接口先使最小声明/测试入口可编译；`method not found`、依赖失败或启动失败均不能充当行为红灯。

## 涉及数据库时

先定位当前工程真实迁移目录、历史脚本、构建依赖、运行配置和可执行入口；测试建表 SQL 不能冒充生产迁移体系。
未发现 Liquibase 配置或脚本时，记录缺口，不编造 `liquibase:update` 等命令或新建未经确认的迁移机制。
新增迁移遵守实际命名、顺序及数据库保护规则；已执行脚本不得重写，基础表或破坏性变更须有对应明确决策。
只在授权环境执行已确认命令，记录影响与回滚方式；无数据变更则写 `N/A` 及理由。

## 交付与证据

更新计划中 T 的状态；技术细节调整记录后继续，业务行为或契约漂移须先更新受影响 REQ/AC 并取得差异决策。
执行适用的 [API 验证](../yuheng-api-verification/SKILL.md)，需要页面联动时接入页面和菜单的既有任务。
在 `docs/verification/<workId>/verification.md` 或用户指定证据路径记录 AC/T、实际命令、时间、退出码、日志及未验证项。
环境问题不算红灯；必需测试、联调或迁移证据缺失为 `BLOCKED`，不能用编译通过或代码已写代替验收。
交付前执行 [自检](../yuheng-self-review/SKILL.md) 与 [完成前验证](../verification-before-completion/SKILL.md)，说明实际结果和局限。
不默认提交、推送、发布或操作真实环境；既有授权仅覆盖其明确范围。
