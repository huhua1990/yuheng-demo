---
name: yuheng-page-delivery
description: Use when Yuheng 任务涉及新增页面、页面交互、API 接线或既有前端页面行为调整。
metadata:
  version: "0.2.0"
  entry: specialist
---

# Yuheng 页面交付

先读 [SDD 契约](../yuheng-workflow-router/references/sdd-contract.md) 及任务规格、计划，不能从“做个页面”直接跳到运行时代码。
沿用 `workId`、REQ/AC/T 和三项版本 `codeVersion`、`governanceVersion`、`knowledgeVersion`。

## 进入条件

1. 核实规格/计划冻结和确认来源、修改范围、兼容影响及 `PHASE_GATE.implementationAllowed`，缺必需输入则 `BLOCKED`。
2. 无规格或计划时回到 [流程路由](../yuheng-workflow-router/SKILL.md)；已有实施授权不重复审批范围内技术细节。
3. 新页面、主要布局或核心交互缺少确认设计时先补设计；已认可页面可作原型依据，局部接线可记录 `NOT_REQUIRED` 和理由。
4. 用 [知识路由](../yuheng-knowledge-routing/SKILL.md) 核对真实组件、页面目录、路由入口和消费端/框架边界。

## 实现约束

- 在当前工程既有页面结构中改动，优先复用组件、布局和状态；消费端业务不进入 core，不强套旧目录或其他框架组件。
- 核对 `yuheng-ui` 的 `package.json` 导出、类型与源码；实际入口包括 `installYuhengUi` 和 `createYuhengRequest`。
- 复用已有 runtime 的 `runtime.context.request`，实例创建留在应用装配处；不从包导入静态 `request`，不另建页面级 axios。
- 共享状态使用真实的 `useUserStore`、`usePermissionStore`、`useDictStore` 及已核实成员，不引用未导出的 `useMenuStore`。
- 核对实际请求实例、API 包装层和类型；普通请求解包 `{code,data}` 后返回业务数据，不再机械读取 `.data`。
- `postOriginal`、下载及自定义注入请求需分别核对契约；不把内部 `systemRequest` 的配置对象签名套到 runtime 请求上。
- 按 Controller 和实际 API 保留 GET/POST/PUT/DELETE、查询参数和 body 位置，不因旧示例改成全 POST。
- 只实现 AC 要求的字段和交互，覆盖适用的加载、空数据、错误、校验、提交结果与列表刷新，不生成无关 CRUD。

## 验证与联动

前端逻辑变更按 [TDD](../test-driven-development/SKILL.md) 补行为测试，再结合 [UI 验证](../yuheng-ui-verification/SKILL.md) 检查实际页面。
纯样式改动使用可重复的视觉检查；测试和构建命令从当前 `package.json` 获取，不能假定存在 `dev` 等脚本。
涉及菜单、路由或按钮权限时使用 [菜单交付](../yuheng-menu-delivery/SKILL.md)，同时检查直接 URL 访问与后端权限。
后端未具备时可记录契约和明确标识的模拟验证；模拟结果不等于真实 API 联调通过。
业务或交互含义发生变化时更新对应 REQ/AC 并取得差异决策，不事后降低验收标准。

## 交付出口

沿用 `docs/verification/<workId>/verification.md` 或用户指定路径，记录 AC/T、命令、时间、退出码、截图/日志与未验证项。
构建成功不能代替浏览器验收；环境不可用不是行为红灯，必需 UI 或联调证据缺失为 `BLOCKED`。
执行 [自检](../yuheng-self-review/SKILL.md) 与 [完成前验证](../verification-before-completion/SKILL.md)，报告变更和实际证据。
不默认提交、推送、发布，不擅自替换运行时或升级依赖。
