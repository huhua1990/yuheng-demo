# Yuheng 消费端升级 Skill 规格

- workId: `yuheng-consumer-upgrade-skill`
- taskType: 治理工具与文档
- codeVersion: `0.1.0-SNAPSHOT`
- governanceVersion: `0.2.0`
- knowledgeVersion: `0.1.0`
- authorization: 用户明确要求参考 Athena `update-athena` 实现 Yuheng 专用升级 Skill。
- phase: 实施

## 目标

提供可复用的 Yuheng 消费端升级入口，依据 core 发布 manifest 更新 `yuheng-server`、`yuheng-ui` 和消费端版本清单，并验证项目构建。治理快照同步仍由 `sync-specs` 负责。

## 范围

- 新增项目自有 `consumer-overlay/yuheng-upgrade/` Skill、更新脚本和测试，并从 `AGENTS.md` 项目入口路由到该 Skill。
- 脚本先预览，显式 `--apply` 才写入；拒绝无效版本、缺字段和被 Git 修改的目标文件。
- 只更新根 `pom.xml` 的 `yuheng.version`、UI `package.json` 的 `yuheng-ui` 版本、消费端 `yuheng-manifest.yaml` 中对应发布版本字段。
- 升级说明包括兼容矩阵、实际发布依赖验证、构建、启动迁移风险、治理/知识同步边界及证据记录。

## 验收标准

- AC-1：Skill 清楚说明适用场景、前置检查、脚本用法、验证和阻塞条件。
- AC-2：预览模式不改文件；应用模式只改三个版本字段并保留其他内容。
- AC-3：非法版本、损坏/缺失字段及目标文件有未提交改动时安全失败。
- AC-4：自动化测试覆盖解析、预览、应用与保护行为。
- AC-5：交付记录真实测试结果和工作区原有状态。

## 不在范围

- 自动查询或猜测 Nexus/npm registry 地址与认证。
- 覆盖 core changelog、消费端业务迁移、运行时配置或数据库校验和。
- 自动执行治理同步、真实数据库迁移、提交、推送或发布。
