# Yuheng 框架使用

先运行 `yuheng-knowledge-routing`，只读任务所需轨道：

- 后端：`ai-knowledge-core/server/overview.md`、`capability-index.md`、`api-index.md`、`database-relations.md`；代码生成任务再读 `codegen-guide.md`。
- 前端：`ai-knowledge-core/ui/overview.md`，结合真实 `package.json`、入口导出、请求实现和 Store。
- 数据：`ai-knowledge-core/data/overview.md`，结合目标工程真实迁移/启动配置。
- 版本：core 的 `release/yuheng-manifest.yaml` 或消费端根 manifest，必要时核对 `release-matrix`。

知识文件不是源码可用性的保证。发现概览里的 POST、静态 request、Store 等说明与源码不符时，记录差异并依现有契约与类型定义判断；不能编造符号或强改代码来迎合文档。

当前可核实的框架入口包括：

- `CommonResult`、`PageResult`、`PageParam`：`framework.common.pojo`。
- `SecurityFrameworkUtils`：`framework.security.core.util`。
- UI：`createYuhengRequest`、`installYuhengUi`、`useUserStore`、`usePermissionStore`、`useDictStore`；公开导出以当前版本 `src/index.ts` 为准。
- HTTP 实例从 runtime `context.request` 或既有 API 模块注入复用；普通方法返回已解包业务数据。

编码前给出具体复用文件/符号、版本、参数/返回、已确认限制和知识缺口。公共能力先评估消费端影响；业务逻辑留消费端，不在 core 加专属业务流程。
