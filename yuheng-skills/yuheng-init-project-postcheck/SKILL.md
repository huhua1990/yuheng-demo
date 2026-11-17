---
name: yuheng-init-project-postcheck
description: Use when Yuheng 工程刚初始化、复制模板、接入框架或刷新治理快照后需要检查真实资产与版本。
metadata:
  version: "0.2.0"
  entry: specialist
---

# Yuheng 初始化后检查

遵守 [SDD 契约](../yuheng-workflow-router/references/sdd-contract.md)，本技能执行只读体检及已授权的非发布校验。
沿用任务 `workId`、REQ/AC/T 和产物路径，记录 `codeVersion`、`governanceVersion`、`knowledgeVersion`；未提供验收时先明确最小检查范围。
已有授权不重复形式审批；体检不扩大为安装依赖、改运行时、升级包、提交或发布。

## 定位真实工程

1. 确认当前根、Git 仓库、已有修改、core/消费端身份及后端、前端实际目录，不根据模板名假设结构。
2. core 读取 `release/yuheng-manifest.yaml`，消费端读取 `yuheng-manifest.yaml`，核对字段、兼容约束及知识元数据。
3. 对照实际 `pom.xml`、`package.json`、已有锁文件和可读依赖元数据核实包名/版本；缺文件或安装状态未知就记录未知。
4. 核对前端实际包 `yuheng-ui` 与 manifest 的标识，不能把版本字符串相同当作资产一致。

## 资产与入口

- 检查 core 的 `governance/rules/`、`governance/skills/` 和消费端的 `yuheng-rules/`、`yuheng-skills/` 及相关知识快照是否真实存在。
- 普通体检只报告本地链接/快照漂移并运行只读 `check`；只有用户明确授权修复治理入口时才运行本地安装写入模式。消费端 `apply` 或版本刷新必须单独获授权，不属于 postcheck。
- 检查 `.agents/skills/<name>/SKILL.md`、`.claude/skills/<name>/SKILL.md`、`.qoder/skills/<name>/SKILL.md` 的入口或链接；未安装可直接读标准源目录。
- 逐个解析本链路所需技能与资源，保留 `../<name>/SKILL.md` 等目录关系；旧平铺文件不能当作发现成功的证据。
- 读取实际构建和测试脚本、所需配置与示例环境文件，记录可执行入口及缺口，不运行猜测的脚本。
- 前端包工程可能只有 test/typecheck/build 等脚本；没有 `dev` 就报告，不把 `pnpm dev` 当作通用启动方式。
- 数据库先找真实迁移脚本、构建依赖和运行配置；测试建表 SQL 不证明已有生产迁移，不虚构 Liquibase 执行命令。

## 知识与源码差异

用 [知识路由](../yuheng-knowledge-routing/SKILL.md) 抽查本次任务依赖的关键符号、类型、HTTP 方法、包导出和文档示例。
确认 `createYuhengRequest`、`installYuhengUi`、`useUserStore`、`usePermissionStore`、`useDictStore`，静态 `request`/`useMenuStore` 不属于当前导出。
核实已有 `runtime.context.request` 的复用与解包，后端 Service 接口/Impl、GET/PUT/DELETE 等方法以当前源码为据。
记录每个差异的知识位置、源码位置、实际版本、影响和建议归属；core 共性能力与消费端业务修正分开定位。
只在授权范围内处理治理问题；运行时故障、版本升级和依赖安装列为后续任务，不自动修复或刷新快照。

## 报告与下一阶段

在同一 `workId` 证据中记录实际检查、时间、命令、退出码、日志位置和局限，手工核对注明方式。
必需资产、兼容依据、技能链接或验证证据缺失则该阶段 `BLOCKED`；不影响当前任务的差异才可 `WARN`。
环境不可用不算行为红灯；未运行的构建、启动、API/UI 均写未验证，不能据静态检查宣称系统可用。
输出真实资产清单、版本差异、可执行脚本、知识差异、阻塞及后续动作，再由 [流程路由](../yuheng-workflow-router/SKILL.md) 选择下一阶段。
按 [完成前验证](../verification-before-completion/SKILL.md) 核对体检结论；不执行发布或自动修运行时。
