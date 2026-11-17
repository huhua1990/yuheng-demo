# Demo 构建与运行脚本

workId：2026-11-11-demo-lifecycle-scripts。用户要求前后端一起构建、启动和停止；明确授权实施。codeVersion、governanceVersion、knowledgeVersion 以 `yuheng-manifest.yaml` 为准。视觉设计不适用；不修改业务、数据库、权限或租户逻辑。

AC-1：构建后端 JAR 和前端生产资源，支持 npm 仓库或显式指定 `yuheng-ui` 包文件，不依赖 core 源码路径。AC-2：启动 JAR 和静态服务，提供 SPA 回退及 `/admin-api` 代理；端口冲突时不终止已有进程。AC-3：停止时只操作本脚本启动且身份校验通过的进程，保留无关进程。AC-4：记录使用方法、运行配置、验证和限制。

实施：添加 `scripts/build.sh`、`scripts/start.sh`、`scripts/stop.sh`、静态服务及测试；运行文件保存在忽略的 `logs/`，服务通过环境变量配置，现有应用启动时的 Liquibase 行为保持不变。先测试服务路由/代理和进程边界，再运行实际构建及隔离端口启动/停止验证。失败可停止本脚本进程并移除本次脚本文件，不更改数据库迁移。

PHASE_GATE：规格及计划 FROZEN，确认来源为用户明确要求实施；Only Modify 为新增脚本、测试、文档；Do Not Modify 为已有业务和迁移。implementationAllowed: true。
