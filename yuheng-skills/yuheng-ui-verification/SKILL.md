---
name: yuheng-ui-verification
description: Use when Yuheng 页面、样式、路由或权限变化需要浏览器验收，或需要核对前端行为与真实接口。
metadata:
  version: "0.2.0"
  entry: specialist
---

# Yuheng UI 验证

遵守 [SDD 契约](../yuheng-workflow-router/references/sdd-contract.md)，读取已确认规格、计划和适用设计。
沿用 `workId`、REQ/AC/T 及 `codeVersion`、`governanceVersion`、`knowledgeVersion`，不创建无关联验收报告。

## 准备

1. 用 [知识路由](../yuheng-knowledge-routing/SKILL.md) 确认实际页面入口、菜单路径、组件映射、账号权限和租户条件。
2. 从当前 `package.json` 读取可用测试、类型检查、构建与启动脚本；包工程可能没有 `dev`，不能直接假设应用入口。
3. 核实已授权的目标环境、实际地址、服务状态和数据；浏览器能力不足或必需账号缺失时记录阻塞，不声称已访问。
4. 已有设计作为验收依据；新交互缺少必要确认时回到 [流程路由](../yuheng-workflow-router/SKILL.md)，不在验证时自行定义业务。

## 按 AC 操作

- 实际从菜单打开页面，并按适用场景检查直接 URL、刷新、返回、路由恢复和登录失效。
- 逻辑变更结合行为测试，覆盖任务涉及的查询、校验、提交、取消、错误提示及结果刷新；纯样式用可重复视觉检查。
- 检查加载、空数据、异常和适用视口下的布局，截图与已确认设计对应，不用构建成功代替浏览器操作。
- 查看实际网络请求的方法、参数、响应与页面呈现；GET/PUT/DELETE 不能被全 POST 的旧说明覆盖。
- 若发现重复解包，核对 `runtime.context.request`、API 包装层与类型；普通请求已返回业务数据，不能盲目再取 `.data`。
- 权限场景同时验证可见性和直接访问，有权限与无权限分别记录；按钮隐藏不证明后端拒绝。
- 菜单或角色变化按 [菜单交付](../yuheng-menu-delivery/SKILL.md)，接口行为按 [API 验证](../yuheng-api-verification/SKILL.md) 补齐。
- 仅模拟接口时明确标记模拟范围，不能把模拟页面交互写成真实联调通过。

## 可复核证据

在 `docs/verification/<workId>/verification.md` 或既定路径记录 AC/T、浏览器/视口、地址、账号角色/租户及操作步骤。
同时保存预期与实际结果、执行时间、截图位置、控制台/网络日志；认证信息脱敏。
命令验证记录实际命令与退出码；手工浏览器操作记录实际结果，退出码写 `N/A（手工操作）`，不伪造命令日志。
失败注明复现条件与影响；计划补验和示意截图不能当作已执行证据。

## 阶段出口

环境不可用、页面未启动或测试入口失败不是行为红灯；必需浏览器或联调证据缺失为 `BLOCKED`。
可继续完成不依赖该环境的检查，明确已验证/未验证范围，不用 `WARN` 隐藏验收失败。
修复须回到已有规格和计划授权范围；业务漂移先取得差异决策，不能为了验收自动改运行时或权限。
将结果交给 [自检](../yuheng-self-review/SKILL.md) 和 [完成前验证](../verification-before-completion/SKILL.md)。
不默认提交、推送、发布或执行真实环境写操作。
