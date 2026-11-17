---
name: yuheng-self-review
description: Use when Yuheng 任务实现或治理文档修改后需要检查范围、规格一致性、兼容性和交付证据。
metadata:
  version: "0.2.0"
  entry: specialist
---

# Yuheng 交付自检

先读 [SDD 契约](../yuheng-workflow-router/references/sdd-contract.md)，核对规格、计划、确认依据和当前真实 diff。
沿用 `workId`、REQ/AC/T、既定产物路径与 `codeVersion`、`governanceVersion`、`knowledgeVersion`。
本技能审查本次实际范围，不自动扩成通用审计，也不替代 [完成前验证](../verification-before-completion/SKILL.md)。

## 范围与规格

1. 对照任务开始时的已有修改，检查实际改动、未跟踪文件和允许范围；不覆盖、回退或归功于他人的并行修改。
2. 逐项核对 REQ → AC → T → 实现 → 验证，检查遗漏、无任务依据的新增内容及未填写的占位符。
3. 确认规格/计划冻结依据真实；已有授权持续有效，技术细节调整已记录，业务或契约漂移已有差异决策。
4. 检查 core 框架与消费端业务边界，兼容影响、权限和租户不能因“局部修复”省略。

## 与真实源码一致

- 用 [知识路由](../yuheng-knowledge-routing/SKILL.md) 核对符号、包导出、依赖和规则差异，不能仅信生成说明。
- HTTP 方法、路径和参数位置以实际契约为准，防止 GET/PUT/DELETE 被改写成全 POST。
- 前端包为 `yuheng-ui`；实际有 `createYuhengRequest`、`installYuhengUi` 和用户/权限/字典 Store。
- 不导入静态 `request` 或 `useMenuStore`；已有请求复用 `runtime.context.request`，核实解包和调用签名。
- 后端沿用真实 Service 接口与 Impl，不能一律改为继承 `ServiceImpl`，也不要求固定八类 CRUD 文件。
- 数据库变更必须有实际脚本、配置及执行依据，不编造 Liquibase 命令，不修改已执行迁移。

## 证据与技能文档

检查行为测试是否实际经历断言红灯和绿灯；`method not found`、编译或环境失败不能证明 TDD 红灯。
适用的 API、UI、权限、迁移和兼容证据必须指向实际结果，不把测试计划、模拟或构建成功当作完整验收。
治理技能检查 `<name>/SKILL.md`、标准 `name/description`、元数据和真实触发条件，不能用旧平铺说明冒充可发现入口。
跨技能链接须为 `../<name>/SKILL.md`，检查目标实际存在；契约链接保持兄弟目录关系，不因平铺复制丢失引用。
只运行当前任务适用、工程中真实存在的校验，不凭空要求工具、技能或无关产物。

## 输出与门禁

按影响列出发现项、文件/符号位置、关联 AC/T、证据和修复建议；没有发现也须说明检查范围与局限。
范围内可逆技术修正沿用既有授权；改变业务含义、扩大范围或高风险动作需取得对应决策后再改。
证据中记录实际命令、时间、退出码、日志及未验证项；手工检查明确写出检查方式。
必需证据缺失或验收失败为 `BLOCKED`，非必需缺口才可 `WARN`，豁免按契约保留授权与后续任务。
输出写入同一 `workId` 的证据文档；不默认提交、推送、发布或操作真实环境。
