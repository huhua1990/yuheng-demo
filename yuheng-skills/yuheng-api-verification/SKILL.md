---
name: yuheng-api-verification
description: Use when Yuheng 接口变更需要验收、前后端需要联调，或需要确认方法、响应、权限及租户行为。
metadata:
  version: "0.2.0"
  entry: specialist
---

# Yuheng API 验证

先读 [SDD 契约](../yuheng-workflow-router/references/sdd-contract.md) 与已确认规格、计划、接口契约。
沿用 `workId`、REQ/AC/T、证据路径和 `codeVersion`、`governanceVersion`、`knowledgeVersion`。
验证任务不额外授予实现、数据修改或真实环境写操作权限；已有授权范围内继续执行，不重复形式审批。

## 确认对象

1. 通过 [知识路由](../yuheng-knowledge-routing/SKILL.md) 定位 Controller、请求/响应类型、调用方、现有测试及启动配置。
2. 建立本次所需的接口清单：AC/T、HTTP 方法、实际路径、参数位置、认证/权限/租户条件、预期响应和副作用。
3. 按源码保留 GET/POST/PUT/DELETE；查询参数、body、文件和路径参数不能由旧示例或“全部 POST”约定替代。
4. 核实服务地址、上下文前缀、测试账号与数据来源，只对本次授权环境执行；不能凭记忆拼接地址或凭据。

## 执行与判定

- 从实际构建配置和已有测试选取命令，先验证相关行为测试；API 联调补充 [TDD](../test-driven-development/SKILL.md)，不能替代实现前红灯。
- 按 AC 覆盖成功、参数边界、业务错误、无权限和适用的租户隔离；只执行任务需要的场景。
- 同时核对 HTTP 状态、业务码、数据结构和实际副作用；HTTP 200 不等于业务成功。
- 区分原始响应与前端返回值：普通 `runtime.context.request` 会解包 `{code,data}`，不能拿二次 `.data` 读取作为契约。
- `postOriginal`、下载及注入的自定义请求另读实现/类型；记录原始响应、包装层与页面之间的差异。
- 验证持久化或状态变化时使用明确测试数据并记录恢复方法；删除、批量操作等遵守本次授权与数据库保护规则。
- 发现业务/契约漂移先记录受影响 REQ/AC 并取得差异决策，不通过放宽断言或改规格掩盖失败。

## 证据

在 `docs/verification/<workId>/verification.md` 或用户指定路径逐项记录 AC/T、实际命令、执行时间、退出码、断言和日志位置。
请求证据包含方法、脱敏后的地址/参数、角色/租户条件、响应摘要及副作用；不得把 token、密码等写入交付文档。
区分单元测试、模拟响应与真实联调，注明各自覆盖范围；未执行的补验命令必须标为待执行。
服务未启动、依赖缺失、连接失败或编译失败都是环境/入口问题，不是目标行为红灯。

## 门禁与交接

必需接口或权限证据缺失、断言失败时为 `BLOCKED`；只完成源码核对不能标记 API 验收 `PASS`。
`WARN` 仅用于不影响当前阶段的缺口；`WAIVED` 须按契约记录授权、负责人、风险、到期与后续任务，仍保留未验证事实。
页面联动按 [UI 验证](../yuheng-ui-verification/SKILL.md) 检查，最终由 [完成前验证](../verification-before-completion/SKILL.md) 汇总。
报告通过项、失败项、环境限制和补验步骤，不默认提交、推送、发布或修运行时。
