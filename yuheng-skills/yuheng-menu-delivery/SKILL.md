---
name: yuheng-menu-delivery
description: Use when Yuheng 任务涉及菜单注册、动态路由、角色分配、按钮权限或页面可达性变化。
metadata:
  version: "0.2.0"
  entry: specialist
---

# Yuheng 菜单与权限交付

遵守 [SDD 契约](../yuheng-workflow-router/references/sdd-contract.md)，沿用 `workId`、REQ/AC/T 和现有规格、计划、证据路径。
所有产物记录 `codeVersion`、`governanceVersion`、`knowledgeVersion`；菜单可见、路由可达和接口授权分别验收。

## 前置条件

1. 核对冻结规格/计划、确认来源、`PHASE_GATE.implementationAllowed` 及角色、租户和修改范围。
2. 缺少规格或权限业务含义时回到 [流程路由](../yuheng-workflow-router/SKILL.md)，不能仅凭页面已生成就加菜单。
3. 已有授权继续有效；超出已确认角色可见范围、扩大权限或改变业务行为时仅对该差异取得决策。
4. 用 [知识路由](../yuheng-knowledge-routing/SKILL.md) 读取真实菜单模型、权限接口、路由解析和测试，不假定另一框架字段。

## 最小改动

- 查找同名菜单、路径、组件标识和权限码，复用已有节点；只新增任务需要的目录、页面或按钮节点。
- 核对实际 `parentId`、`type`、`path`、`component`、`componentName`、状态及可见字段，取值依据现有模型和样例。
- 从页面组件映射追到动态路由解析与守卫，确认父子路径、名称、布局和刷新时的注册行为。
- 使用 `yuheng-ui` 真实的 `usePermissionStore` 和已有 runtime 上下文；不引用 `useMenuStore` 或平行维护权限缓存。
- 菜单与权限 API 复用 `runtime.context.request` 或已有已配置包装层；方法以源码为准，更新为 PUT、删除为 DELETE 等不能统一 POST。
- 角色分配、按钮权限标识和后端鉴权须对应，隐藏按钮不能作为接口拒绝访问的证明。
- 消费端业务菜单留在消费端；修改 core 公共菜单或权限机制时先核实消费端兼容影响。
- 需要落库时先定位既有脚本、配置、执行入口与数据库保护规则；不编造 Liquibase 命令，也不重写已执行迁移。
- 本技能不自动授权调用真实环境的菜单/角色写接口；按本次用户授权范围执行并记录变更及恢复方法。

## 验证

按 AC 选取有权限、无权限和适用租户账号，核对菜单树、页面打开、刷新与直接 URL 访问。
对按钮操作同时验证 UI 状态、实际网络请求和后端拒绝结果；不能仅凭管理员可见就判定权限正确。
执行适用的 [API 验证](../yuheng-api-verification/SKILL.md) 与 [UI 验证](../yuheng-ui-verification/SKILL.md)。
记录角色/租户测试条件、权限标识、AC/T、实际命令、时间、退出码和日志/截图，敏感认证信息脱敏。
环境、账号或菜单数据未就绪不算行为红灯；必需权限验证缺证据时为 `BLOCKED`，不改权限绕过验收。

## 输出

把节点、路由、权限、角色之间的对应关系及验证结果写入同一 `workId` 的证据文档，无关项写 `N/A` 和理由。
执行 [自检](../yuheng-self-review/SKILL.md) 与 [完成前验证](../verification-before-completion/SKILL.md) 后报告剩余缺口。
不默认提交、推送、发布或扩大已授权的环境操作范围。
