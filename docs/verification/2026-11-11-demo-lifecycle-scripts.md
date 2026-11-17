# Demo 构建与运行验证

workId：2026-11-11-demo-lifecycle-scripts；规格及计划见 `docs/specs/2026-11-11-demo-lifecycle-scripts.md`。manifest 中 codeVersion 0.1.0-SNAPSHOT、governanceVersion 0.2.0、knowledgeVersion 0.1.0。

- AC-1：Node 22.23.2、Maven，显式传入已打包的 `yuheng-ui@0.1.0-SNAPSHOT`；`scripts/build.sh` 成功构建后端、前端，前端类型检查通过。Vite 报告大于 500 kB 的 bundle 警告。
- AC-2：在 18992 / 15173 端口使用授权测试库、临时 Redis、`SPRING_LIQUIBASE_ENABLED=false` 启动；后端启动完成，首页、SPA 路径、API 代理返回 HTTP 200。
- AC-3：停止脚本停止前后端；预先运行的 48080 后端仍返回 HTTP 200。对占用的 48080 端口再次启动时明确拒绝；测试伪造 PID 文件未终止无关进程。
- 自动测试：`python3 -m unittest discover -s scripts/tests -v` 验证 SPA 回退、缺失资源 404、API 转发和无关进程保护。

本次运行使用临时 Redis，未清理用户已有服务；数据库迁移关闭。未验证远程部署、HTTPS 或 WebSocket，静态服务器仅用于本地运行。
