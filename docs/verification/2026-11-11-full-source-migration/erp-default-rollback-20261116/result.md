# ERP 默认项切换失败回滚验收

workId: `YH-20261111-full-source-migration`；codeVersion `0.1.0-SNAPSHOT`；governanceVersion `0.2.0`；knowledgeVersion `0.1.0`。

PHASE_GATE：沿用 `docs/plans/2026-11-11-full-source-migration.md` 的冻结规格、计划及用户完整迁移实施授权。本次属于 T4 验证，Only Modify 为 Demo 验证探针、计划和证据；不修改业务实现、已执行 changeset、共享服务或历史用户密码。原型 NOT_REQUIRED（无 UI 变更），implementationAllowed=true，门禁 PASS。执行前已核对两个目标仓库干净和当前 Docker 只有共享 mysql8/redis；不复用共享依赖。

AC-T4-ERP-DEFAULT-ROLLBACK：在全新专用 MySQL、Redis、后端中，以真实登录调用仓库和账户默认项切换。先证明正常切换成功；随后只让设置新默认的第二次 UPDATE 失败，核实数据库触发器存在和日志确实命中注入 marker，比较完整表快照及两行状态。仓库应按当前事务恢复原状；账户是否回滚以实测记录，不将部分提交判为通过。原始用户密码只在内存逐行比较，不写入证据。结束时停止专用进程并移除专用容器与数据卷。

修复前源码事实：模板、Demo 和原始 `ruoyi-vue-pro` 的 `ErpAccountServiceImpl.updateAccountDefaultStatus` 均没有事务声明；仓库对应方法已有 `@Transactional(rollbackFor = Exception.class)`。其运行影响由后文实测。

## 2026-11-16 实际结果

通过 `scripts/verification/erp_default_status_rollback_probe.py` 创建全新容器对和 schema `yuheng_t4_default_rollback`；后端 48193、MySQL 13371、Redis 16471，全部仅绑定 loopback。数据库账号仅有本轮 schema 权限，master/slave 环境变量均指向此库，Redis 使用本轮随机密码。后端显式关闭 mock 认证、禁止 Quartz 自动启动；使用隔离种子管理员真实密码登录。Liquibase 执行 54 changesets。

运行 JAR SHA-256 `e50bcf20ec4ca4157638393fcfd9730707bd7395e08a08296e5a9e2266da1e9f`。两个 ServiceImpl class 与当前编译目录字节一致（`artifact-classes.json`）；这不是整个当前 Core 构建的声明，该 JAR 仍使用早期 54 个 changeset，后续 Core 种子修复不在该包内。

两张表各插入同租户的 old=默认、new=非默认两行，先通过真实接口成功切换到 new，证明夹具和权限满足成功路径，再重置为 old。分别建立并查询确认 BEFORE UPDATE 触发器：仅当 NEW.id=990002 且 NEW.default_status=1 才 SIGNAL SQLSTATE 45000。取消 old 的 UPDATE 不受此触发器拦截。两条故障请求都返回 HTTP 200/业务码 500，服务日志分别命中 `T4_DEFAULT_WAREHOUSE_INJECTED` 与 `T4_DEFAULT_ACCOUNT_INJECTED`。

| 方法 | 故障前 | 故障后 | 完整表快照 | 判定 |
| --- | --- | --- | --- | --- |
| 仓库默认切换 | old=true, new=false | old=true, new=false | 前后 SHA-256 相同、均 2 行 | 本次失败原子性 PASS |
| 结算账户默认切换 | old=true, new=false | old=false, new=false | SHA-256 改变、均 2 行 | 失败原子性 FAIL：第一次写已提交 |

`runtime.json` 保存两个控制请求、两个失败请求的状态码摘要、触发器和日志 marker 确认、完整行快照哈希和默认/租户字段。没有保存请求令牌或密码。21 个原始用户密码在内存按 ID/值逐行比较保持一致。

## 根因与范围

`source-parity.json` 将上述两个完整 ServiceImpl 在上游 commit `128a0e3bd3847d11b7f2f9e169dd36fce3b0b581`、模板和 Demo 中归一比较：替换包前缀，去除注释和空白后，两组三方 SHA-256 各自相同。因此该账户部分提交是继承自上游的行为，不是迁移漏掉事务注解；仓库事务在此次第二次写失败路径确实生效。

本轮关闭仓库这一个两次写入回滚子项，账户失败原子性保持 FAIL/待处理。未将“探针按预期观察到部分提交”的成功执行误记为账户验收通过。没有改变业务失败语义或擅自声称一致性已修复。并发默认唯一性、跨租户、更多角色/禁用记录及全部事务路径仍未证明。T4 总项及 T1/T3 继续开放。

## 无效尝试、验证与资源清理

## 范围内修复设计与实施门禁补录

前述 FAIL 是修复前事实。沿用完整迁移的缺陷修复授权，REQ/AC-T4-ERP-ACCOUNT-ATOMIC 要求同一次默认切换的两个数据库更新整体提交或回滚。采用与仓库相同的 Spring 方法事务 `@Transactional(rollbackFor = Exception.class)`，同时修改模板与 Demo 的账户 Service；接口/正常切换/SQL 表结构保持当前契约。拒绝只捕获异常后手工恢复（恢复也可能失败）、不增加并发锁/唯一索引（属于另一个验收问题）。本次 Only Modify 追加这两个方法的事务声明及其回归证据，implementationAllowed=true；原型仍 NOT_REQUIRED。该修复会让账户 Service 与上游多出有记录的事务注解差异，先前三方一致仅适用于修复前版本。

任务：先将真实 HTTP 探针断言改为账户也必须完整回滚，在未改生产代码前重跑取得 `red/runtime.json`；随后添加事务、编译 business 模块，在临时 JAR 副本仅替换新 business JAR（共享原包正被进程占用，不覆盖）；使用新副本、全新容器重跑并保存 green 结果，最后运行 Maven 和模板回归、核对源码及包身份并清理。

红灯已复现：`account default switch must roll back both writes`，old=true/new=false 变为两者 false；探针退出 1，专用服务和容器已在 finally 清理。此红灯发生在生产源码修改前。

首轮 MySQL 客户端按默认分隔符拆开了触发器 BEGIN/END，CREATE TRIGGER 报错；此时只执行到仓库正向控制，未注入故障，不能作为任何回滚结果。记录保存为 `first-attempt-excluded.json`。修正脚本 DELIMITER 后，使用全新容器对重跑获得上述有效结果；两轮均在 finally 优雅停止后端并删除各自专用容器与匿名数据卷。

有效轮观察到 `Graceful shutdown complete`，容器计数为 0，13371/16471/48193 均无监听；共享 mysql8/redis 仍运行且未用于本轮验证。模板 `python3 -m unittest tests.test_erp_tenant_contract -v` 12/12 通过，探针 `py_compile` 和 Demo `git diff --check` 通过。本轮只新增探针和证据，未重复宣称前一轮 Maven 结果为本轮运行结果。

## 修复后回归

添加了要求事务声明的模板契约测试，先运行并确认缺少注解时以明确 assertion FAIL，再恢复注解。随后在模板和 Demo 两个 `ErpAccountServiceImpl.updateAccountDefaultStatus` 上统一添加 `@Transactional(rollbackFor = Exception.class)`；没有改变接口、查询和默认项选择规则。

针对修复后的 Demo，离线 Maven `package` 构建 business/bootstrap reactor 成功。因共享 PID 23945 正在读取正式路径的原 JAR，没有覆盖该文件；从原 JAR 创建 `/tmp` 临时副本，仅替换嵌套 `yuheng-demo-business-0.1.0-SNAPSHOT.jar` 为本次构建产物，副本 SHA-256 `1b9593228e67b0a9e6d10135a96a1fb46b9421343c4a07aa30cac0eaaa171abf`。其 business JAR SHA-256 为 `c0cbca28a21f73e43d4423a4c2251e0429505894dfb158a1c1c47ba80f3505aa`，修复前正式 JAR 为 `e50bcf20ec4ca4157638393fcfd9730707bd7395e08a08296e5a9e2266da1e9f`。包身份见 `fixed-artifact.json`。

修复后用全新容器/schema，启动该临时 JAR，显式关闭 mock，真实登录；同样先验证正向切换，再用完全相同的两个触发器只拒绝第二次 UPDATE。HTTP 故障均为 code 500、SQL marker 均命中；仓库及账户的完整表快照均前后相同，old=true/new=false 均恢复。21 个种子用户密码值前后逐行相同；应用优雅停止，两个容器及数据卷删除，三个端口无监听。结果见 `green/runtime.json`。这完成账户原子性缺陷的红绿真实运行验证。

回归结果：Demo `mvn -o -Dexec.skip=true test` 40/40；模板全量 Python 测试 67/67（新增事务契约测试）；该定向测试已通过缺注解红灯和加回注解绿灯两次执行；探针 Python 编译和两仓 `git diff --check` 通过。模板/Demo 完整账户 Service 归一哈希相同，上游哈希不同，差异仅为新增 `Transactional` import/注解（`source-parity-fixed.json`）。该更改是本次修复的有意迁移差异：保留一致性要求，不以“和上游相同”为理由保留已验证的部分提交行为。旧账户 FAIL 仅作为修复前历史证据；修复后当前验收结果为 PASS。
