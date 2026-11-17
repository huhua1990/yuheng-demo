# yuheng-demo

Yuheng 的消费端 bootstrap。运行时代码、配置、数据库迁移和业务扩展放在本仓库；平台基础能力通过 Maven 版本依赖消费：

```text
com.yuheng:yuheng-server:${yuheng.version}
```

消费端不引用 `yuheng-core` 源码目录，也不直接依赖 core 内部模块作为稳定入口。平台 Java 包名为 `com.yuheng.platform`，demo 自有代码位于 `com.yuheng.demo`。

后端位于 `yuheng-demo-server/`：`yuheng-demo-business` 承载业务扩展，`yuheng-demo-server-bootstrap` 负责启动和运行配置。MySQL 空库通过启动模块的 `src/main/resources/db/changelog/db.changelog-master.yaml` 按顺序加载 core 迁移和 demo 的 `db/changelog/business/`。历史用户密码散列保留在 core 迁移中，外部服务密码和密钥需按环境配置；部署前应更换历史账号密码。已有数据库不能直接运行空库基线，需另行制定接续方案。

## 构建和运行

需要 Java 17+、Maven、Python 3、rsync、pnpm 和 Node.js 20.19+ 或 22.12+。Maven 仓库中需有 `yuheng-server` 对应版本；npm 仓库需有 `yuheng-ui` 对应版本。一次构建前后端：

```bash
./scripts/build.sh
./scripts/start.sh
./scripts/stop.sh
```

若 UI 包尚未发布到 npm 仓库，可传入版本匹配的已打包文件：

```bash
YUHENG_UI_PACKAGE=/absolute/path/yuheng-ui-0.1.0-SNAPSHOT.tgz ./scripts/build.sh
```

tarball 模式校验包名和版本，并在临时目录离线安装；需要 pnpm 缓存中已有其余全部依赖。当前 Demo 尚无独立锁文件，普通 registry 模式的冻结安装也需先提供匹配的锁文件。

构建产物为 `yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar` 和 `yuheng-demo-ui/dist/`。默认前端地址为 `http://127.0.0.1:5173`，后端端口为 `48080`；前端服务将 `/admin-api` 代理到后端。可用 `UI_PORT`、`UI_HOST`、`BACKEND_PORT` 环境变量调整。启动前检查端口，停止脚本只停止本脚本启动并完成身份校验的进程。日志和 PID 位于 `logs/lifecycle/`。

JAR 也包含构建时的前端文件，可以单独用 `java -jar yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar` 启动，并通过 `http://127.0.0.1:48080/` 访问。启动前同样需要配置数据库和 Redis 环境变量并确认 Liquibase 目标库。`mvn package` 和 `scripts/build.sh` 均会安装前端依赖、执行类型检查与构建后再打包；前端步骤失败时 Maven 构建失败。Maven 的 `-o` 不会使 npm 自动离线，npm 仍需可访问的仓库或完整缓存。当前未提供消费端独立锁文件，依赖版本解析尚不可完全复现。不要在 JAR 仍被进程使用时原地重建它，应先停止对应进程或在独立目录构建。

后端默认使用 `local` profile，数据库、Redis 和其他基础设施地址见启动模块的 `src/main/resources/application-local.yaml`，可通过 Spring 环境变量覆盖。应用启动时 Liquibase 按现有配置执行，启动脚本不会自动关闭迁移；请先确认指向正确的数据库。静态服务面向本地使用，默认只监听回环地址。
