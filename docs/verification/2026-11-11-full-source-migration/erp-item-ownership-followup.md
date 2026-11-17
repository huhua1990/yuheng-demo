# ERP 明细归属续验（2026-11-14）

关联 `YH-20261111-full-source-migration`，codeVersion `0.1.0-SNAPSHOT`、governanceVersion `0.2.0`、knowledgeVersion `0.1.0`。销售订单 T4-SO-OWNER 和采购入库 T4-PI-OWNER 沿用用户对完整迁移和同一风险类别的持续授权。实现变更限于模板与 Demo 的两个 Service、错误码和专项测试；没有更改 SQL、接口、事务或业务口径。

## T4-PI-OWNER 采购入库

新增采购入库拒绝客户端指定明细 ID；编辑时非空 ID 必须属于当前入库单且不得重复，错误码 `1030102009`。模板和 Demo 同步。

修复前 Service 测试显示外单 ID 未触发业务拒绝；新增携带 ID 的请求未在依赖校验前被拒绝，测试替身不完整导致后续空指针，该 NPE 不是生产环境观测。修复后专项 3 项通过，覆盖外单、不存在、重复、新增自带 ID 和合法混合新增/编辑。Maven 全量 16 项通过，模板 60 项通过。日志：`/tmp/yuheng-pi-owner-red.log`、`/tmp/yuheng-pi-owner-green.log`、`/tmp/yuheng-pi-template-tests.log`。

## T4-SO-OWNER 销售订单

新增销售订单拒绝客户端指定明细 ID；编辑时非空 ID 必须属于当前订单且不得重复，错误码 `1020201011`。模板和 Demo 同步。

修复前 Service 测试证明外单 ID 未被拒绝。新增自带 ID 用例未在产品校验前拒绝，后续因测试替身未提供产品服务而触发空指针，该 NPE 不是生产环境观测。修复后专项 3 项及 Maven 全量 13 项通过，模板 60 项通过；覆盖外单、不存在、重复、新增自带 ID 和合法混合编辑。日志：`/tmp/yuheng-so-owner-red.log`、`/tmp/yuheng-so-owner-green.log`、`/tmp/yuheng-so-template-tests.log`。

## T4-PR-OWNER 采购退货

新增采购退货拒绝客户端指定明细 ID；编辑时非空 ID 必须属于当前退货单且不得重复，错误码 `1030103009`。模板和 Demo 同步。

修复前 Service 测试证明外单 ID 未被拒绝；新增 ID 同样未在依赖校验前拒绝，后续 NPE 来自测试替身缺少订单服务，不是生产环境观测。修复后专项 3 项及 Maven 全量 19 项通过，模板 60 项通过；覆盖外单、不存在、重复、新增自带 ID 和合法混合编辑。日志：`/tmp/yuheng-pr-owner-red.log`、`/tmp/yuheng-pr-owner-green.log`、`/tmp/yuheng-pr-template-tests.log`。

## T4-SO-OUT-OWNER 销售出库

新增销售出库拒绝客户端指定明细 ID；编辑时非空 ID 必须属于当前出库单且不得重复，错误码 `1020202009`。模板与 Demo 同步。修复前专项测试复现外单 ID 未被拒绝；修复后 3 项测试及 Maven 全量 22 项通过，覆盖外单、不存在、重复、新增自带 ID 和合法混合编辑。模板 60 项通过。日志：`/tmp/yuheng-so-out-owner-red.log`、`/tmp/yuheng-so-out-owner-green.log`、`/tmp/yuheng-so-out-template-tests.log`。

## T4-SR-OWNER 销售退货

新增销售退货拒绝客户端指定明细 ID；编辑时非空 ID 必须属于当前退货单且不得重复，错误码 `1020203009`。模板与 Demo 同步。修复前专项测试确认外单 ID 未被拒绝；修复后 3 项测试及 Maven 全量 25 项通过，模板 60 项通过，覆盖外单、不存在、重复、新增自带 ID 和合法混合编辑。日志：`/tmp/yuheng-sr-owner-red.log`、`/tmp/yuheng-sr-owner-green.log`、`/tmp/yuheng-sr-template-tests.log`。

## T4-STOCK-OUT-OWNER 库存出库

新增其它出库拒绝客户端指定明细 ID；编辑时非空 ID 必须属于当前单据且不得重复，业务错误码 `1030402099`。修复前专项 Service 测试复现外单 ID 未被拒绝。首次错误码选择 `1030402006` 与既有库存调拨错误码重复，完整测试立即发现冲突；随后改用本组未占用编号 `1030402099`。最终专项 3 项和 Maven 全量 28 项通过，模板 60 项通过，覆盖非法 ID 及合法混合更新。日志：`/tmp/yuheng-stock-out-owner-red.log`、`/tmp/yuheng-stock-out-owner-green.log`、`/tmp/yuheng-stock-out-template-tests.log`。

## T4-STOCK-IN-OWNER 其它入库

新增其它入库拒绝客户端指定明细 ID；编辑时非空 ID 必须属于当前单据且不得重复，错误码 `1030401099`。修复前专项测试确认外单 ID 未被拒绝。修复后专项 3 项和 Maven 全量 31 项通过，模板 60 项通过，覆盖非法 ID 及合法混合更新。日志：`/tmp/yuheng-stock-in-owner-red.log`、`/tmp/yuheng-stock-in-owner-green.log`、`/tmp/yuheng-stock-in-template-tests.log`。

## T4-STOCK-CHECK-OWNER 盘点

新增盘点单拒绝客户端指定明细 ID；编辑时非空 ID 必须属于当前盘点单且不得重复，错误码 `1030410000`。修复前 Service 测试复现外单 ID 未被拒绝；修复后 3 项专项通过，覆盖外单、不存在、重复、新增自带及合法混合更新。

## T4-STOCK-MOVE-OWNER 调拨

新增调拨单拒绝客户端指定明细 ID；编辑时非空 ID 必须属于当前调拨单且不得重复，错误码 `1030410001`。修复前 Service 测试复现外单 ID 未被拒绝；修复后 3 项专项通过，覆盖相同边界。

盘点/调拨修复后 Maven 全量 37 项、模板 60 项通过。日志 `/tmp/yuheng-stock-check-owner-red.log`、`/tmp/yuheng-stock-final-red.log`、`/tmp/yuheng-stock-check-move-owner-green.log`、`/tmp/yuheng-stock-check-move-template-tests.log`。模板与 Demo 的错误码经扫描未见新编号冲突；历史调拨和其它出库错误码重复定义保持原样，未扩大修改。

新 JAR `yuheng-demo-server-bootstrap/target/yuheng-demo.jar` 离线 package 成功，SHA-256 `cb55eb70c924b5a47fe6fa6b8091dee435751b1ec196305f944aa5976d017a9f`；Maven 37 项测试通过。Demo 脚本在不配置专用 HTTP URL 时 22 项通过、7 项按条件跳过。曾将测试指向既有 48080 实例，页面静态资源返回 404、API 测试亦失败；该实例没有用本轮隔离环境和 schema 启动，故此失败不作新 JAR 行为证据，也没有重启或写入共享数据库。完整日志 `/tmp/yuheng-nine-owner-package.log`、`/tmp/yuheng-nine-owner-demo-script-tests.log`、`/tmp/yuheng-nine-owner-demo-tests-no-url.log`。

随后用该 JAR 在端口 48096、专用空 schema `yuheng_t4_item_owner_20261114_real`、随机专用 DB 用户和开始前为空的 Redis DB 14 执行真实 HTTP 验证。登录加十种单据共 11 次请求（采购/销售订单、采购/销售入库/退货、其它入库/出库、盘点、调拨）；十个新增接口均以客户端携带明细 ID 触发相应错误码，每次请求后完整比较相关订单、单据、明细、库存、流水、财务表行快照不变。探针输出 `erp-item-owner-http-create.json`，可复用脚本为 `scripts/verification/erp_item_owner_http_probe.py`。隔离 JAR 正常停止后精确删除临时 schema、用户和授权并清空初始为空的 Redis DB 14；确认 48096 关闭、临时对象为 0、共享 `yuheng_demo` 仍存在。未修改种子用户密码或共享数据。

真实 HTTP 新增路径覆盖十种单据的客户端自带 ID 拒绝和无副作用。编辑路径在隔离实例依次验证外单、不存在、重复、异租户（SQL 将真实明细复制为 `tenant_id=999`）四种 ID：十种单据共 40 个负例请求；每个请求返回对应业务错误，并比较相关订单、主单、明细、库存、流水、财务等表的完整行快照，均未发生变化。最终 JSON `erp-item-owner-http-update.json` 记录 99 次总请求和十类结果，探针为 `scripts/verification/erp_item_owner_update_http_probe.py`。采购入库和采购退货夹具先审核采购订单；销售出库/退货先准备销售订单及审核库存来源；其它出入库提供供应商/客户；确保负例不被无效业务状态遮蔽。

更新探针前两次夹具准备分别因缺已审核采购入库、缺其它入库供应商被业务校验拒绝；补齐前置来源并每次换用全新 schema 后重跑通过。没有将这些夹具失败当成归属逻辑红灯。三轮编辑 HTTP 服务均正常停止；精确删除各自专用 schema、DB 用户/授权，清理起始为空的 Redis DB 14、13、12、11；端口 48096 至 48099 均关闭，共享 `yuheng_demo` 仍存在。没有改写种子密码或写共享库。

真实 HTTP 已覆盖十种单据新增自带 ID，以及编辑时外单、不存在、重复、SQL 异租户明细 ID 的拒绝和数据不变。异租户检查使用孤立明细夹具（租户 999），没有异租户主单、账号或完整登录权限配置；因此完整跨租户真实用户权限矩阵、并发压力和显式异常注入事务回滚仍待验证。

已盘点的九种同类单据均完成模板/Demo 源码校验、Service 测试及新增/编辑真实 HTTP 归属验证；本轮未写共享数据库或操作 registry。ERP 模板仍为 `generated-pending-verification`，T1/T3/T4 的其它迁移、UI、数据库来源和完整权限/并发验收继续未完成。
