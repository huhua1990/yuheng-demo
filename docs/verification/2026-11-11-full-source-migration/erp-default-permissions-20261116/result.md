# ERP 默认状态接口权限运行验收

workId: `YH-20261111-full-source-migration`。codeVersion: `0.1.0-SNAPSHOT`；governanceVersion: `0.2.0`；knowledgeVersion: `0.1.0`。

PHASE_GATE: 沿用 `docs/plans/2026-11-11-full-source-migration.md` 的已授权 T4 完整迁移验证。原规格/计划及持续实施授权沿用该计划；本次仅补默认状态权限的技术验收拆解。Only Modify 为 Demo 专用验证探针、计划和证据；不修改运行时业务代码、历史 changeset 或共享数据。原型 NOT_REQUIRED（没有页面变更）。implementationAllowed=true，门禁 PASS。

AC-T4-ERP-DEFAULT-PERM：普通无角色用户调用仓库/结算账户默认状态更新应返回 403，业务表不变；只获对应更新权限的普通角色用户应能开启和取消默认项。使用真实密码登录、HTTP 和 SQL 验证。临时环境用后停止应用并删除专用容器及数据卷。

## 环境与产物身份

2026-11-16 在专用 MySQL 8.0.33 容器 `yh-t4-default-mysql-1116`、schema `yh_default_probe`、schema-scoped 用户和 Redis `yh-t4-default-redis-1116` 上运行；端口分别为 13370、16470、后端 48192。master/slave 均由独立数据库环境变量配置到同一专用库；没有向共享 MySQL/Redis 或 48080/5173 发出本轮验收请求。

JAR 为 `yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar`，SHA-256 `e50bcf20ec4ca4157638393fcfd9730707bd7395e08a08296e5a9e2266da1e9f`。嵌套 business JAR 中两个 Controller 和两个 ServiceImpl 的 class 字节与当前 target/classes 完全相同，详见 `artifact-classes.json`；随后 Maven 确认没有待编译变更。此项限定四个类，不声称整个打包 JAR 与所有当前 Core 源码相同；该 JAR 的 Liquibase 有 54 changesets，未包含后续 Core 种子修复版本。

首次启动因测试 Redis 没有配置密码而应用尝试 AUTH 失败，在业务请求前退出；此时专用库已完成 54 changesets。将 Redis 重建为显式带测试密码的独立容器，并给 JVM 显式配置相同密码后成功启动；重跑 Liquibase 为 0 新执行、54 已执行。Quartz 禁止自动执行。

## 最终有效结果

探针：`scripts/verification/erp_default_status_permission_probe.py`。先用隔离种子管理员真实登录，通过 Core API 新建两个普通用户、一个自定义角色及其授权关系。两个用户随后均用真实密码登录；最终验证没有使用 mock token。JVM local profile 的 mock 功能仍开启，因此本项不证明 mock 关闭配置；普通用户请求使用登录签发的随机 access token，经过真实 Token 校验。

仅将更新按钮 621、683 授予自定义角色；SQL 确认角色 code 是本轮新建 code，不是 super_admin，无权用户没有活动角色。两张业务表各有两条 tenant 1 测试数据。

| 接口 | 无权请求 | 有权开启 | 有权取消 |
| --- | --- | --- | --- |
| `PUT /admin-api/erp/warehouse/update-default-status` | HTTP 200/code 403；完整表快照摘要前后一致 | code 0；990001=false、990002=true | code 0；两个默认标志均 false |
| `PUT /admin-api/erp/account/update-default-status` | HTTP 200/code 403；完整表快照摘要前后一致 | code 0；990011=false、990012=true | code 0；两个默认标志均 false |

`runtime.json` 保存 11 条脱敏请求（含夹具创建/授权，登录凭据与令牌未保存）、业务表行数/完整行快照 SHA-256、状态和租户值。最初已有的 21 个用户密码字段仅在内存读取比较，逐行不变；不保存密码或哈希值。

夹具准备期间先前 shell 少传 docker exec 的 `-i`，导致 INSERT 未执行；当时无权请求和正向“仓库不存在”均排除。补入夹具后使用 mock 用户的初步请求又命中过一个空权限缓存，该轮也排除为正式验收。最终探针重新通过平台 API 创建用户/角色/授权，使用真实登录令牌，对存在的两行数据重置基线，完成以上最终结果。不把任何早期失败尝试计为通过。

## 回归与清理

- 模板 `python3 -m unittest tests.test_erp_tenant_contract -v`：12/12 通过，含两个默认状态接口权限契约。
- Demo `mvn -o -Dexec.skip=true test`：40/40，通过且无 failure/error/skip；摘要 `maven-summary.txt`。
- 探针 `py_compile` 和 `git diff --check` 通过。
- 应用 PID 11673 收到 TERM 后完成 Tomcat graceful shutdown，执行会话退出 143。只删除本轮两个容器，使用 `docker rm -fv` 同时删除其匿名卷。`cleanup.json` 确认容器不存在、48192/13370/16470 无监听；共享 mysql8/redis 仍运行。

本项关闭两个接口的无角色拒绝、仅对应更新权限允许以及成功 true/false 写路径。没有做事务故障注入：仓库 Service 的事务和账户 Service 没有直接事务注解是当前源码事实，本次成功切换不证明失败原子性，也不外推并发、跨租户、其它权限组合。T4 全矩阵、T3 全页面/交互/响应式/Network 和 T1 registry 固定版消费继续开放。
