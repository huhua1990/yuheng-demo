# T4 ERP 业务闭环与租户边界续验

## 2026-11-23 P2 ERP 当前固定 JAR 明细归属与状态/库存复验

使用当前 Demo JAR SHA-256 `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1`，为每类探针创建一次性 MySQL schema 和独立 Redis 容器，执行后精确删除容器并确认所有专用端口无监听。Liquibase 每个 schema 均冷装 59 个 changeset；共享 `yuheng_demo`、宿主 `mysql8`、历史用户密码均未使用或修改。此轮范围为已有 ERP 单据所有权校验和已实现业务状态，并不覆盖模板尚未建模的部门/本人数据范围。

- 明细新增归属：登录加十类采购、销售、库存单据新增请求共 11 次。十类均拒绝客户端自带明细 ID，逐次完整 ERP 业务表快照不变，结果 `p2-erp-owner-current-20261123/create.json`。
- 明细更新归属：99 次请求覆盖十类单据外单明细、不存在明细、重复明细及 SQL 构造的异租户明细 ID；非法请求返回各资源既有业务错误，全部表快照不变；有效编辑成功，结果 `p2-erp-owner-current-20261123/update.json`。
- 采购/销售/财务主流程：53 次请求完成来源单审核、入库/出库、付款/收款、撤审及再审；超额付款/收款被拒并回滚。库存最终为 6，流水及金额与 API 断言一致，结果 `p2-erp-owner-current-20261123/workflow.json`。
- 库存生命周期：37 次请求覆盖其它入库/出库、调拨、正负盘点审核/反审核、库存不足多行整单回滚及并发出库竞争。并发两单各请求 4 件时恰好一单审核成功、一单库存不足；最终仓库库存为 1 和 2，流水只记一次，结果 `p2-erp-owner-current-20261123-retry/stock-lifecycle.json`。
- 非法审核状态：十二类单据提交 `status=99` 均返回业务码 400，逐次比较 ERP 全表行快照不变；结果 `p2-erp-owner-current-20261123-status-retry/audit-status.json`。

两次未进入业务探针的批次失败单独保留在 `p2-erp-owner-current-20261123/runtime.json` 和 `p2-erp-owner-current-20261123-retry/runtime.json`：一次性 schema 带安全后缀，但两个探针入口只允许日期命名；调整为探针原有命名后完整重跑通过。随后以红灯测试固定入口约束，在 `erp_stock_lifecycle_probe.py` 和 `erp_audit_status_probe.py` 放宽为可选的小写字母数字后缀，同时仍限定各自隔离 schema 前缀。ERP 定向 Python 回归 8/8 通过，Demo 全量 Python 回归 103 项（96 通过、7 项因外部环境条件跳过、0 失败），相关脚本 `py_compile` 和 `git diff --check` 通过。标准 Spring access log 曾记录本轮临时登录密码，已对本轮新生成日志脱敏并复核无密码或令牌；sidecar runner 已增加日志脱敏和回归测试。当前无对应隔离容器，13420-13422、16495-16497、48290-48292 均无监听。

本轮未发现需要修复 Core 或 ERP 模板产品源码的缺陷，因此没有改动 Core/Templates 或将模板源码同步覆盖 Demo。ERP 部门、本部门及本人级数据范围仍是未实现的模板能力：业务表仅有租户与审计信息，没有 `dept_id/user_id` 归属列和注册规则；按既定计划应先为业务模板定义字段、写入语义、迁移和更新 Skill 策略，再进行实现与验证，当前结果不冒充该能力已通过。

## 2026-11-23 P2 ERP 全资源双租户当前固定 JAR 复验

Demo 当前固定 JAR SHA-256 `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1` 在专用 schema `yuheng_t4_erp_full_tenant_20261123_p2` 冷装 59 个 changeset。两个真实租户分别完成登录、ERP 23 个资源族/33 张业务表的代表创建、审核和读取，共 263 个 HTTP 请求；本租户详情/分页可见、跨租户详情/分页不可见、跨租户单据审核/删除后 SQL 快照不变、伪造租户头拒绝。平台历史用户密码逐行保持不变。结构化证据为 `p2-erp-full-tenant-current-20261123/runtime.json`。

运行使用 MySQL/Redis 容器 `yh-erp-full-tenant-p2-*` 和 13430/16505/48300 专用端口，结束后确认容器不存在、端口释放、`cleanup.passed=true`。当前 runner 在应用停止后自动脱敏 backend 日志；对应回归覆盖密码与 Bearer token。ERP 部门或本人级数据范围仍不在当前模板模型内，本轮仅关闭当前固定包下已建模的租户隔离复验子项。

## 2026-11-23 Core 固定 npm 包的 Demo UI-only 消费验证

- Demo UI 独立临时副本从 npm 公共 registry 按现有 `pnpm-lock.yaml` 执行 `pnpm install --frozen-lockfile --ignore-scripts --registry=https://registry.npmjs.org/`，508 个包与冻结锁文件匹配；`yuheng-ui@0.1.0-SNAPSHOT` 实际解析到临时消费者 `.pnpm` 包目录，integrity 为 `sha512-zYstszt9JvGc7CHWLkV/dgxq8WcQWRYSDXbhVze5RLXy2notLDhlicUjhHo5FPh/aY37wF94lleBhdRVH74icA==`。
- 临时消费者 `vue-tsc --noEmit` 通过；Vitest 4 个文件/20 项通过；`node scripts/check-platform-imports.mjs` 为 PASS；Vite 生产构建 3548 模块通过（存在既有大 chunk 警告）。Vite 开发服务使用 registry 安装的 Core 包启动成功。pnpm 首次安装因脚本审批策略以非零退出，使用冻结锁文件的 `--ignore-scripts` 重跑成功；安装包检查和全部命令验证均通过。
- 临时副本路径 `/tmp/yuheng-demo-ui-registry-J9isPf`，未改正式 Demo 的 manifest、锁文件、node_modules、后端或业务模块，未发布 npm 制品。`npm whoami` 的 401 仅说明该执行环境未登录为发布者，不影响匿名读取公共包；此子项验证固定 UI 包消费，不代表 JAR/浏览器业务流程。本轮隔离浏览器尝试首因临时符号链接自循环，修正后确认 registry 包 Vite 配置解析和生产构建通过；完整 ERP 销售浏览器闭环仍以固定 Demo JAR 的 `erp-sales-browser-20261123/` 证据为准。

## 2026-11-23 ERP 收款单桌面与来源金额闭环

沿用 workId `YH-20261111-full-source-migration`、当前 P2 计划与既有实施授权。任务范围限定为 Demo 中已初始化 ERP 模板的收款页面端到端验收；Core 提供平台源码，Templates 提供业务模板源码，Demo 保持最终可定制工程，模板更新继续通过 Skill 选择性合并。管理后台只验证桌面视口。

使用 Demo 固定验收 JAR SHA-256 `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1`，runner 先对 JAR 内 612 个静态资源与 UI dist 做逐项 SHA-256 比对并通过，再启动专用 MySQL/Redis 容器、schema `yuheng_t4_finance_browser_20261123`、后端/UI 端口 48274/5233。Liquibase 首次冷装 59 个 changeset。仅在该一次性 schema 创建临时财务账号并用 SQL 创建销售客户、采购供应商、结算账户、商品库存、已审核采购入库和销售出库夹具；历史种子用户密码字段逐行快照在运行前后相同。

Playwright 1440×900 真实登录 `/erp/finance/receipt`，通过页面“添加销售出库单”选择当前客户可收款单据，录入 3 元，提交并审批；随后登录 `/erp/finance/payment`，通过“添加采购入库单”选择当前供应商可付款单据，录入 4 元，提交并审批。收款和付款的创建、审核 API 均 HTTP 200，创建 API 各返回 ID 1。浏览器路由最终为付款页面，page errors、console errors、failed requests 均为空。SQL 对账：收款主单 `status=20,total_price=3,discount_price=0,receipt_price=3`；明细 `biz_type=21,biz_id=993109,total_price=36,receipted_price=0,receipt_price=3`；来源销售出库 `status=20,receipt_price=3,total_price=36`；付款主单 `status=20,total_price=4,discount_price=0,payment_price=4`；明细 `biz_type=11,biz_id=993204,total_price=20,paid_price=0,payment_price=4`；来源采购入库 `status=20,payment_price=4,total_price=20`；均为 tenant 1。机器证据位于 `erp-finance-browser-20261123/runtime.json` 和 `browser.json`，复跑入口为 `scripts/verification/erp_finance_browser_runner.py`，浏览器探针为 `scripts/verification/erp_finance_browser_probe.js`。

验收期间曾出现探针按钮定位器、SQL 夹具插入顺序和 MySQL readiness 处理问题，均在实际业务请求前失败，没有形成独立可复核的失败 JSON；修正后使用同一最终 runner 在全新隔离环境重跑通过。最终应用/UI 进程停止，专用容器和 13432/16487/48274/5233 清理并复核无监听。没有访问共享 `yuheng_demo`、共享 Redis、宿主 `mysql8` 或更改历史密码。本子项未发现产品缺陷，未修改 Core/Templates/Demo 业务运行代码。

验证：`python3 -m unittest scripts.tests.test_erp_finance_browser_probe scripts.tests.test_erp_sales_browser_probe scripts.tests.test_erp_probe_changelog -v`（10 项通过）；`python3 -m py_compile scripts/verification/erp_finance_browser_runner.py`、`node --check scripts/verification/erp_finance_browser_probe.js` 与 `git diff --check` 通过。此结果仅关闭真实销售出库收款和采购入库付款的限定桌面创建/审批闭环，不代表 ERP 全量页面或 P2 总体验收完成。

## 2026-11-23 ERP 销售订单、出库及退货桌面闭环

- **状态：限定桌面业务闭环通过，P2 总体验收继续进行中。** 使用当前 Demo JAR SHA-256 `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1`、一次性 schema `yuheng_t4_erp_sales_browser_20261123` 和隔离 MySQL/Redis，在 1440×900 桌面浏览器真实登录。页面创建销售订单并审核；通过销售出库弹窗的“选择销售订单”创建并审核出库单；再通过销售退货弹窗的“选择销售订单”创建并审核退货单。所有创建/审核 API 返回 HTTP 200，浏览器 page errors、console errors、failed requests 均为 0。
- SQL 核验 59 个 Liquibase changeset；销售订单、出库单和退货单数量均为 3，来源订单、客户、租户关系正确，三类单据审核状态均为 20。库存从 8 降至 5，再由退货增加回 8；库存流水依次记录初始 8、销售出库 `-3`、销售退货 `+3`。种子用户密码字段前后相同。专用容器、后端/UI 进程及 13404/16485/48272/5231 端口已清理。
- 结构化证据为 `erp-sales-browser-20261123/runtime.json`、`browser.json`；运行入口和桌面探针为 `scripts/verification/erp_sales_browser_runner.py`、`erp_sales_browser_probe.js`。此前失败轮均为验收接线/日期控件/静态服务日志管道问题，未产生销售写入或已由隔离 schema 销毁；最终轮完整通过。此项只关闭销售订单→出库→退货的限定桌面主流程，不代表退款/收款 UI 或 ERP 全量页面已通过。

## 2026-11-20 T4 部门精简列表认证与租户隔离

使用当前 Demo JAR（SHA-256 `5e632e65db0af402c43c2e8823601c11a03cfe60b01d738af52dd042384283ef`）在全新隔离 MySQL/Redis 和 schema `yuheng_t4_deptlist_20261120` 中运行 `scripts/verification/dept_simple_list_security_probe.py`。专用端口为 MySQL 13358、Redis 16438、后端 48195；Liquibase 冷装完成 56 个 changeset。只在隔离 schema 启用临时租户 121/122、创建部门夹具和临时用户，历史密码、共享数据库与共享 Redis 未触碰。

匿名 `GET /admin-api/system/dept/simple-list` 返回业务码 `401`。tenant 121 临时用户通过真实登录取得 token，并绑定一个不授予菜单权限、但数据范围为 `ALL` 的隔离角色，以使本项只验证全局认证与租户过滤；匹配 `tenant-id: 121` 请求返回业务码 `0`，只包含 tenant 121 部门，tenant 122 部门不出现。将同一 token 的请求头改为 `tenant-id: 122` 返回业务码 `403`，日志确认 `TenantSecurityWebFilter` 拒绝主体租户越权，部门查询日志确认实际 SQL 带 `tenant_id = 121`。请求前后部门表完整有序快照一致。结构化证据见 `controller-security-inventory-20261119/dept-simple-list-runtime.json`，探针为 `scripts/verification/dept_simple_list_security_probe.py`。

首次运行使用无角色临时用户，Core 数据权限规则按设计计算为 `self=true`；由于 `system_dept` 没有 `user_id` 字段，SQL 追加 `null = null` 并返回空列表。该运行只作为夹具诊断，不计入验收；修正为隔离 `data_scope=ALL` 角色后全流程通过。应用优雅关闭，专用容器及其 schema 随容器销毁，13358/16438/48195 均无监听。

该结果关闭部门精简列表的匿名认证、真实 token 租户头校验和两租户查询范围子项；不覆盖部门写权限、数据权限各范围组合、跨实例并发及完整 Controller/Mapper 矩阵。T4 总项与 T1/T3 全范围继续开放。

## 2026-11-20 T4 用户精简列表认证、部门筛选与租户隔离

使用当前 Demo JAR（SHA-256 `5e632e65db0af402c43c2e8823601c11a03cfe60b01d738af52dd042384283ef`）在全新隔离 MySQL/Redis 和 schema `yuheng_t4_userlist_20261120` 中运行 `scripts/verification/user_simple_list_security_probe.py`。专用端口为 MySQL 13359、Redis 16439、后端 48196；Liquibase 冷装完成 56 个 changeset。临时用户、部门、角色和租户只存在于本轮 schema，未触碰共享数据库、共享 Redis 或历史用户密码。

匿名 `GET /admin-api/system/user/simple-list` 返回业务码 `401`。tenant 121 临时用户通过真实登录取得 token，绑定不授予菜单权限但数据范围为 `ALL` 的隔离角色；无筛选请求返回 tenant 121 的两个临时用户，tenant 122 用户不出现。`deptId=990601` 请求只返回该部门的两个用户；将同一 token 的请求头改为 `tenant-id: 122` 返回 `403`。日志确认无筛选 SQL 带 `tenant_id = 121`，部门筛选 SQL 同时带 `dept_id = 990601` 和 `tenant_id = 121`。用户表完整有序快照前后不变。结构化证据见 `controller-security-inventory-20261119/user-simple-list-runtime.json`，探针为 `scripts/verification/user_simple_list_security_probe.py`。

该结果关闭用户精简列表的匿名认证、真实 token 租户头校验、部门筛选及两租户查询范围子项；不覆盖用户分页/写入、角色数据范围各组合、跨实例并发及完整 Controller/Mapper 矩阵。T4 总项与 T1/T3 全范围继续开放。

## 2026-11-17 配置表单窄屏可用性修复

修复前的隔离浏览器红灯已确认：Demo 与原版 `ConfigForm` 使用 Dialog 默认 `40%` 宽度，在 390px 视口弹窗宽 156px、参数键值输入框宽 0px；320px 视口同样不可用。全屏后才可编辑。该问题位于配置表单调用方的窄屏宽度约束，不修改共享 Dialog 默认行为。

Core 将配置表单 Dialog 宽度设为 `min(100%, max(40%, 400px))`。修复后的 Demo 消费构建在同一隔离后端中真实浏览器验证：1440px 弹窗宽 576px、键值输入框宽 412px；390px 弹窗宽 390px、输入框宽 226px；320px 弹窗宽 320px、输入框宽 156px。三个视口均无横向弹窗溢出，筛选/重置为 10→0→10，编辑字段可直接修改并取消，无需全屏。原版仍保留为对照：390px/320px 输入框宽 0px，探针需全屏后才能继续。

隔离 schema `yuheng_t3_configresponsive_20261120` 的完整配置快照和用户密码字段前后相同，专用 MySQL/Redis 及端口 13356/16436/48191/5198/5199 已清理。Demo 这次不同视口切换期间出现若干静态 JS `ERR_CONNECTION_RESET`，服务端日志对相应资源均记录 HTTP 200，页面断言和 API 请求均完成；因此本项记为布局行为通过，完整静态资源网络清洁度仍不计通过。结构化结果见 `config-responsive-fixed-20261117/runtime.json`。

Core 本地二进制验证：Vitest 29 个文件/125 项通过，Vite 生产构建和 `vue-tsc -p tsconfig.build.json` 声明构建通过，边界检查通过。Demo 本地二进制验证：Vitest 3 个文件/14 项通过，`vue-tsc --noEmit`、Vite 生产构建和平台导入边界检查通过。通过 pnpm 运行的命令被 workspace 依赖状态检查触发，固定版 `yuheng-ui` 在配置 registry 返回 404，未改变锁文件或依赖目录；普通 Core `vue-tsc --noEmit` 仍有既有 compat 全目录类型错误，不作为本次修复回归失败。T1 registry、T3 其它页面/完整网络验收、T4 全范围继续开放。

### 默认宽度静态盘点续查

当前 Core 兼容 Dialog 的默认 `width` 为 `40%`，配置表单已显式使用响应式宽度。运行 `python3 scripts/verification/dialog_width_inventory.py` 对 `compat/views/system` 与 `compat/views/infra` 的直接 `<Dialog>` 调用进行静态盘点：分别有 21 处和 12 处没有显式 `width` 属性；另外分别有 12 处和 7 处显式指定宽度。候选包括角色、字典、用户、部门及数据源表单，脚本输出每处文件路径与行号。

这只是当前源码直接调用清单，不能解析动态组件、封装调用或 `v-bind` 透传的宽度，也未逐项运行浏览器；数量不代表实际故障数。后续需在真实视口测量 `.el-dialog`、输入控件及按钮边界并验证交互，再决定修复范围，不能仅凭这一清单宣称其它页面通过或失败。本轮没有改 Core UI、数据库或运行服务；T3 其余页面和 T1/T4 总项继续开放。

## 2026-11-17 配置弹窗窄屏字段定位

在 `config-responsive-dialog-20261117/` 的同一隔离数据中，Demo 与原版 390×844 均测得默认弹窗宽 156px（Dialog 默认 40%），表单项宽 94px、内容区宽 14px、输入框实际宽 0px，因此该字段不可见并非仅需纵向滚动。点击弹窗全屏按钮后，两端输入框可见，可以修改再取消；移动端筛选/重置均 10→0→10，桌面筛选/重置/编辑取消均通过。两端 console errors、page errors、requestfailed 均为空；配置全表和用户密码字段前后不变，专用容器及五个端口已清理。

浏览器记录 `completed: true` 仅表示探针完成了含抽屉循环和全屏的操作，不表示默认窄屏布局通过。`*-mobile-390x844-dialog.png` 在弹窗动画期间捕获，不能用于判断稳定视觉效果；实际计算几何及零宽输入框是本次依据。默认窄屏 Dialog 可用性问题在两端均存在，尚未修复；菜单初始浮层触发链仍未证实。T1/T3/T4 保持开放。

## 2026-11-17 配置页移动抽屉循环与编辑框

使用 `config-responsive-cycle-20261117/` 的独立 MySQL/Redis 和同一后端，Demo 与原版在 390×844 初始搜索按钮均被基础设施浮层遮挡；通过真实点击汉堡展开侧栏、再点击遮罩关闭后，两端搜索按钮中心均恢复命中按钮本身，筛选无匹配 0 行、重置恢复 10 行。之后打开首条编辑，详情请求成功，但两端弹窗均测得实际宽 156px、scrollWidth 177px，键值输入框等待可见超时，编辑取消未完成。两端 console errors 和 requestfailed 均为空。此结果确认一次正常抽屉开关可恢复搜索，不证明初始浮层的完整触发链；弹窗字段不可见及溢出也需要进一步检查实际样式、滚动容器和动画状态。

源码线索：Core compat 与本地原版均在菜单折叠状态变化后按当前路由调用 `menu.open()`，Element Plus 自身则在折叠时清空展开项；该行为与初始浮层现象相符，但尚未通过调用时序实验证实因果。完整配置及密码字段快照不变，专用容器删除且 13356/16436/48191/5198/5199 无监听。只关闭本段移动筛选/重置的抽屉循环子项，移动编辑及 T1/T3/T4 总项保持开放。

## 2026-11-17 配置页同数据桌面对照及浮层定位

在独立 MySQL/Redis 和同一隔离后端重跑 Demo 生产包、原版 Vite：两端 1440×900 初始 10 行，搜索不存在名称后 0 行，重置后恢复 10 行；编辑首条配置、修改表单值并取消，两端弹窗边界均为 left 432/right 1008、宽 576px。两端本轮 console errors、page errors 和 requestfailed 均为空；配置全表及用户密码字段前后比较不变。这个结果只覆盖配置页所述桌面操作，不代表其它页面或完整 T3。

390×844 两端在填写筛选输入框之前，搜索按钮中心均已被 Element Plus 的“基础设施”弹出菜单内 WebSocket 项覆盖；浮层矩形 left 47/top 45/宽 200、高 626px，侧栏容器宽 0。筛选前后命中相同 SVG；已捕获的菜单 mouseover 事件为空，因此当前证据不能确定浮层的触发机制。真实点击均超时，移动筛选、弹窗和取消未通过，也不能将这一现象归因于 Demo 独有迁移差异。本次没有重现上一轮 JS 资源连接重置，不足以证明其原因已解决。

结构化数据及截图见 `config-responsive-hit-20261117/`；探针记录筛选前后命中元素及祖先和鼠标事件。容器删除，13356/16436/48191/5198/5199 均无监听；共享服务未触碰。T1/T3/T4 保持开放。

## 2026-11-17 配置页响应式探针续查

独立 MySQL/Redis、schema `yuheng_t3_configresponsive_20261120` 和端口 13356/16436/48191/5198/5199 复跑配置页，Demo JAR SHA-256 `e50bcf20ec4ca4157638393fcfd9730707bd7395e08a08296e5a9e2266da1e9f`；Demo 生产包和原版 Vite 均连接同一隔离后端。浏览器 context 分别登录，临时账号只存在隔离 schema。配置全表快照和用户密码字段前后均一致，专用容器删除且五个端口释放；详见 `config-responsive-pointer-20261117/runtime.json`。

Demo 1440×900 初始 10 行，搜索不存在名称后 0 行、重置后 10 行；编辑弹窗内改值并取消，配置快照不变。列表前三行高均为 201px，弹窗宽 576px；浏览器 console、pageerror、requestfailed 在该视口为空。该结果仅为桌面单页子项，并不构成同视口原版对照。

原版 390×844 初始 10 行、前三行高 293px，侧栏容器宽 0、文档无横向溢出，但填写筛选后搜索按钮中心被 `el-popper-container` 下菜单 SVG 命中，Playwright 点击持续被菜单拦截；没有完成筛选或弹窗验收。先前 Demo 在同尺寸也遇到菜单浮层拦截，提示此现象并非已证实的 Demo 独有差异；实际触发链及两端可复现条件仍待调查。原版桌面加载超时；Demo 移动登录页未渲染，同时一个 JS 资源请求报告 `ERR_CONNECTION_RESET`，原因未确认，不计通过。旧 `config-responsive-20261120` 中两张移动截图都是 Demo 测试过程的不同帧，不能作为原版与 Demo 的成对截图，也不能据此断定菜单透明度缺陷。

探针现在等待登录表单异步挂载，鼠标先移离侧栏，并分别保留视口错误、命中元素、快照与清理状态。该目录的前一次失败运行被后一次同名运行覆盖，现存 JSON 是最后一次结果；此前编号失败尝试仍保留。T1、T3 全页面/交互/响应式与 T4 全范围继续开放。

## 2026-11-20 T4 基础设施配置接口权限矩阵

沿用 workId `YH-20261111-full-source-migration`、codeVersion `0.1.0-SNAPSHOT`、governanceVersion `0.2.0`、knowledgeVersion `0.1.0` 及用户已确认的完整迁移验收授权。本次只验证当前 Core ConfigController 契约，不修改业务源码。Demo JAR SHA-256 `e50bcf20ec4ca4157638393fcfd9730707bd7395e08a08296e5a9e2266da1e9f`，独立 MySQL/Redis 容器、schema `yuheng_t4_configperm_20261120`、端口 13355/16435/48190；冷装 54 个 Liquibase changesets。两个临时用户仅在该 schema 创建，通过真实登录取得令牌，历史密码未读取或修改。

无角色真实用户依次调用配置 create、update、single delete、batch delete、export，五个 API 均 HTTP 200/业务码 403；每次拒绝后都重新读取完整 `infra_config` 表有序快照并与请求前逐字比较。前后 SHA-256 均为 `6ccf78b290e1679e07917aaceb787360b91f1471d98bdd394309bb469b1b8e77`。同租户用户只获授 `infra:config:{create,update,delete,query,export}` 五项权限，正向对照的分页查询、三条新增、修改并持久化、单条删除、批量删除均业务码 0；导出 HTTP 200 并返回 6466 字节 xls 数据。三条探针配置最终均逻辑删除。数据表 `ConfigDO` 标注 `@TenantIgnore`，因此本测试结论限于权限拒绝/放行，不把配置行解释为租户隔离证据。

最终结构化证据为 `controller-security-inventory-20261119/config-permission-runtime.json`，可复跑入口 `scripts/verification/config_page_permission_probe.py`。之前成功运行的第一份证据错误地直接复用了基线 hash 作为 after 字段，已移至 `config-permission-first-20261120.json` 并明确排除；最终复跑记录了拒绝后实际查询得到的哈希。专用应用 graceful shutdown，MySQL/Redis 容器删除，13355/16435/48190 无监听。该测试仅关闭基础设施配置这五类端点对“无角色”和“五项精确授权”两类用户的权限子项；匿名全局过滤、单项权限拆分、跨租户、所有 Controller/Mapper、T4 全事务及 T1/T3 总项仍开放。

## 2026-11-17 T3 配置页桌面写入续验

沿用 workId `YH-20261111-full-source-migration`、codeVersion `0.1.0-SNAPSHOT`、governanceVersion `0.2.0`、knowledgeVersion `0.1.0` 和已确认的完整迁移授权；本次为验证，沿用既有规格和计划，未修改产品行为。独立 MySQL/Redis、schema `yuheng_t3_configcrud_20261117`，端口 13353/16433/48188/5300，Demo JAR SHA-256 `e50bcf20ec4ca4157638393fcfd9730707bd7395e08a08296e5a9e2266da1e9f`，冷装 54 changesets；随机临时账号只存在隔离库，历史密码未修改。

1440×900 真实浏览器通过配置页创建唯一参数 `yh.browser.crud.probe`，编辑值为 `updated-value`，确认删除后列表不再显示。POST create、PUT update、DELETE delete 各一次，HTTP 均 200、业务码均 0；隔离数据库中该行值为 `updated-value`、`deleted=1`。随后修改另一行表单并取消，未增加写请求。排除测试行的其余 `infra_config` 全行有序快照前后 SHA-256 相同：`ead12429850bea951ded466088c253f04da2397f4cc7ecc9fafda449ee1314e2`。截图 `config-crud-20261117/browser-after-crud.png` 显示新增、修改、删除成功及过滤后的空列表。

首次测试在新增成功后因弹窗关闭动画导致筛选输入定位歧义退出；第二次在更新成功后未等待列表刷新而断言旧值退出。两次均保留在 `config-crud-first-attempt-20261117/`、`config-crud-second-attempt-20261117/`，各自隔离资源已清理；最终运行修正了等待条件。最终 `browser.json` 记录 favicon 404、requestfailed 为空；UI 代理日志另记录跳转期间租户列表、未读数和公告请求的 502/BrokenPipe，不能据此声明完整 Console/Network 通过。最终容器及以上四个端口均已清理。复跑入口为 `scripts/verification/config_page_crud_runner.py` 和 `config_page_crud_probe.js`；脚本语法检查及 `git diff --check` 通过。Demo Python 测试 27 项，其中 20 项通过、7 项因未配置专用环境跳过。

该证据仅覆盖一个自定义配置的桌面新增、编辑、删除和另一行取消；批量删除、导出、权限与失败路径、移动端及原版同运行态对照仍开放，T1/T3/T4 总项不关闭。

## 2026-11-17 配置页批量删除、导出与 UI 代理续验

在全新隔离 MySQL/Redis schema `yuheng_t3_configextended_20261117`、后端/UI 13354/16434/48189/5301 使用同一 Demo JAR（SHA-256 `e50bcf20ec4ca4157638393fcfd9730707bd7395e08a08296e5a9e2266da1e9f`），Liquibase 冷装 54 changesets。真实 1440×900 浏览器重复验证筛选/重置、单条新增编辑删除、两条唯一参数批量删除、导出下载及编辑取消。单条及批量写接口均 HTTP 200/业务码 0；导出 API HTTP 200，浏览器实际下载 `参数配置.xls`，大小 6270 bytes。删除后重置列表恢复 10 行。数据库中三条唯一探针值均 `deleted=1`，其中 CRUD 探针保留已更新值；其余配置全行有序快照前后 SHA-256 均为 `9e2ecc698d1cffe25c9a134a801fd4b3b6912cbb285056ce14a33e6053a4aa6f`。取消没有增加写请求。

浏览器 console errors 与 requestfailed 均为空；`/favicon.ico` 返回 HTTP 200。UI 代理仍有三条页面跳转时已由客户端取消的请求，日志写出 200 头后向关闭 socket 写响应产生 BrokenPipe；旧实现随后尝试写 502，造成误报及未处理 traceback。对该根因新增 RST socket 红灯/绿灯测试，并确认真实上游连接失败仍返回 502。修复仅调整 `scripts/ui_server.py` 异常处理，客户端连接断开或响应已开始后的传输错误关闭连接，不再伪装成上游 502；生命周期测试 9 项、完整脚本测试 30 项（23 通过，7 项因独立环境未配置而跳过）通过。

迁移 UI 的入口缺少 favicon 声明及静态文件，已从原始 RuoYi Vue3 `public/favicon.ico`（SHA-256 `14de90436b4dd01dd803ff34c5f0c734bc853de0f8f13df781b79ada42f2e43f`）复制到 Demo UI `public/` 并加入入口 link；Vite build 退出 0，构建产物 icon hash 与源文件相同。保留构建已有的大 chunk 提示。一次早期复制落入工作区错误子目录导致构建未带图标，已在最终构建前更正到实际 Demo UI 工程路径。

曾有扩展验收探针自身步骤顺序错误及运行器比较时未排除批量测试键的失败尝试，均保留在 `config-extended-first-attempt-20261117/` 与 `config-extended-second-attempt-20261117/`；最终运行的 browser/runtime JSON 在 `config-extended-20261117/`，全部写入、导出、快照及清理断言通过。最终容器已移除，13354/16434/48189/5301 均无监听。此项只关闭配置管理桌面所述 CRUD、批量删除、导出和本地代理特定断连行为；权限拒绝、外部故障矩阵、移动端、原版运行态对照、全页面网络验收及完整 T1/T3/T4 继续开放。

## 2026-11-17 T3 配置页筛选、重置和编辑取消

在独立 MySQL/Redis 容器和 schema `yuheng_t3_configbrowser_20261117` 中运行 Demo JAR（SHA-256 `e50bcf20ec4ca4157638393fcfd9730707bd7395e08a08296e5a9e2266da1e9f`），后端 48187、UI 5299；Liquibase 冷装 54 个 changeset。临时随机账号仅在该 schema 中创建并通过真实登录，未读取或修改历史密码，也未使用共享 DB/Redis。

Playwright 1440×900 打开 `/infra/config`，初始页有 10 行；按不存在的参数名称搜索为 0 行，重置后恢复 10 行。打开第一条配置的编辑对话框，GET 详情返回 HTTP 200/业务码 0，修改表单中的值后点击取消；未发送任何配置写请求，列表仍有 10 行。三次分页 GET 均 HTTP 200。请求前后完整 `infra_config` 有序快照 SHA-256 均为 `f92aefeec225319e49b0645d9c9c953c4a1818bf22bd617117486be64b2dfb08`。浏览器 console 有 `/favicon.ico` 404，requestfailed 为空；UI 代理日志另有页面跳转时取消公告请求的 BrokenPipe/502，不将完整 Network/Console 标为通过。

截图 `config-browser-20261117/browser-after-cancel.png` 显示长参数值在窄列中频繁折行并显著增高表格行；Core 与本地上游配置页该列同样没有固定宽度或溢出提示，本次只记录该可读性问题，不将其判为迁移差异。运行器精确移除专用容器和 schema，13352/16432/48187/5299 无监听；5200 预检发现被既有 Node 进程占用，未触碰该进程。结构化证据在 `config-browser-20261117/`，复跑入口为 `scripts/verification/config_page_browser_runner.py`。

本项仅验证配置列表筛选/重置和编辑取消的桌面路径；新增/保存/删除、其它记录、移动端、原版同运行态对照及完整 T3 仍需验收。T1 和 T4 总项保持开放。

## 2026-11-20 T3 岗位页桌面筛选与窄屏菜单抽屉复验

使用当前 Demo JAR（SHA-256 `e50bcf20ec4ca4157638393fcfd9730707bd7395e08a08296e5a9e2266da1e9f`）、全新专用 MySQL/Redis 容器和空 schema `yuheng_t3_postbrowser_20261116`，后端/UI 端口为 48186/5199。Playwright 在 1440×900 桌面视口登录并打开 `/system/post`：初始 4 行；按不存在的岗位名搜索后 0 行；重置后恢复 4 行。岗位分页 API 三次均返回 200，桌面文档无横向溢出。

同一运行器以独立浏览器 context 在 390×844 窄屏复验：初始岗位页有 4 行、文档宽度等于视口，Core 兼容布局将侧栏收起到宽度 0；点汉堡后侧栏抽屉宽 200px、遮罩覆盖视口；点遮罩后遮罩节点消失，表格 4 行仍保留。附图 `post-browser-20261116/browser-mobile-initial.png` 是初始收起态，`browser-mobile-after-hamburger.png` 是菜单展开态，`browser-mobile-after-overlay.png` 是收起后的状态。用户提供的菜单覆盖截图对应展开抽屉状态，遮挡在点遮罩收起前是预期交互；本次未验证抽屉展开时表格内容仍可操作，也未验收岗位编辑/新增/删除等写流程。

本轮最终浏览器记录中移动视口 Playwright `errors` 和两种视口的 `failed` 均为空；桌面 `errors` 仅含缺少 `/favicon.ico` 的静态 404，岗位 API 返回 200。UI 代理日志还记录了路由跳转中途客户端取消请求后产生的 502/BrokenPipe（对应通知、租户和公告旁路请求），这些不是岗位 API 失败，但完整 Console/Network 清洁度仍不计通过。独立 GET 窄屏 CSS 文件返回 200。应用、容器/schema 已清理，13351/16431/48186/5199 均无监听，专用容器不存在；共享服务、数据库、Redis 和历史用户密码未触碰。结构化证据与截图位于 `post-browser-20261116/`，探针为 `scripts/verification/post_page_browser_probe.js`、`post_page_browser_runner.py`。

本项只关闭岗位页桌面筛选/重置及窄屏菜单打开/遮罩收起子项。T3 的全页面、写操作、完整 Network/Console、原版同尺寸全面对照和更多响应式矩阵仍开放；T1 registry 固定版消费和 T4 全范围矩阵也未完成。

## 2026-11-19 T4 岗位精简列表认证与租户隔离运行验证

在当前 Demo JAR 的隔离实例中，匿名 `GET /system/post/simple-list` 返回业务码 401；无角色、无岗位 query 权限的 mock 主体在租户 121 与 122 分别请求时，均成功且只返回各自租户的启用岗位。另在同一隔离 schema 中创建只存在于本轮的 tenant-121 用户，真实登录获得 access token：带 `tenant-id: 121` 请求成功并只返回 tenant-121 岗位，把同一 token 的请求头改为 `tenant-id: 122` 后返回业务码 403。专用 schema 中 SQL 快照确认两个岗位夹具 tenant_id 分别为 121/122。由于两个历史租户种子已过期，本轮只在 disposable schema 内将其状态启用、有效期延长一年；Redis 使用独立容器。应用优雅退出，schema 和容器已销毁，专用端口全部释放。证据及限制见 `controller-security-inventory-20261119/post-simple-list-runtime.json` 与 `result.md`。这关闭一个路由的匿名认证、两个方向的岗位租户查询及真实 token 租户头不一致拒绝子项，不代表其它 Controller 或全量 Mapper 租户矩阵。

## 2026-11-19 T4 System/Infra Controller 路由安全静态盘点

为按计划扩展到 Controller 层，新增可复跑脚本 `scripts/verification/controller_security_inventory.py`，静态扫描 Core System/Infra 管理端全部 `*Controller.java` 方法路由。结果为 47 个 Controller、322 条路由映射，251 条有方法/类级 `@PreAuthorize`，22 条有 `@PermitAll`，10 条有 `@TenantIgnore`，49 条仅受全局认证兜底。全局 Security 配置确认无 `@PreAuthorize` 仍要求已认证；TenantSecurityWebFilter 校验主体租户与请求租户一致，MyBatis TenantDatabaseInterceptor 依据 `TenantBaseDO`、实体 `@TenantIgnore` 与配置决定是否加行级过滤。

静态清单中包含岗位 simple-list、参数配置 get-value-by-key、文件创建/上传/预签名、租户精简列表及公开文件读取等代表性候选。它们不因注解形式自动判为缺陷；需要逐条上游契约比较，并在隔离 Demo 中用匿名/无权限/有权限/跨租户请求与 SQL 快照验证。机器结果和方法级边界见 `controller-security-inventory-20261119/`。脚本语法检查通过；Demo Python 生命周期/模块测试为 27 项通过、7 项按需跳过。该结果只关闭静态路由清单子项，不关闭 Mapper 租户 SQL 归属分析、Controller 运行时权限矩阵或 T4/T1/T3 总体验收。

### 参数配置值读取运行续验

在专用 schema、Redis 与 Demo 后端端口 48184 中，以无角色 tenant-121 用户真实登录验证 `/infra/config/get-value-by-key`：匿名请求 code 401；可见平台配置返回 code 0 和期望值；不可见配置返回 `1001000004` 且没有数据；相同 token 的请求租户头改为 122 时返回 403。配置行请求前后快照（键、值摘要、visible、deleted）一致，测试用户没有角色关联，确认此次请求为只读。应用正常关闭，专用容器删除，13349/16429/48184 无监听；结构化结果与清理证据见 `controller-security-inventory-20261119/config-value-runtime.json`，可由 `scripts/verification/config_value_security_probe.py` 复跑。该项仅关闭该路由的上述有限验证，不关闭配置管理其它路由或 T4/T1/T3 总验收。

同一探针匿名请求 `/system/tenant/simple-list`（不带 tenant-id）返回 HTTP 200/code 0，结果 ID `[1,121,122]` 与隔离 schema 的启用租户一致。所有非空字段仅为 `id`、`name`，其余 VO 字段以 null 序列化；租户状态/有效期前后快照一致。源码和行为与上游一致。此项只关闭此公共精简列表路由的匿名调用、忽略当前租户和有效数据字段范围子项。

### 岗位分页细粒度权限运行续验

独立 MySQL/Redis/schema 和 Demo 后端中，对 `/system/post/page` 运行真实权限矩阵：匿名请求 code 401；真实登录但无角色用户 code 403，岗位表快照不变；仅授予 `system:post:query` 的普通角色用户 code 0 并读取 4 条岗位。权限来自原始 SQL 菜单 ID 43；应用优雅关闭，专用容器删除，13350/16430/48185 均无监听。脚本和结构化证据为 `scripts/verification/post_page_permission_probe.py` 与 `controller-security-inventory-20261119/post-page-permission-runtime.json`。这只关闭岗位分页单租户匿名/无权限/有权限子项。

## 2026-11-16 T3 共享运行环境只读现态复核

复核时共享 Demo UI PID 39370 仍监听 `127.0.0.1:5173`，后端 PID 23945 仍监听 `*:48080`；Docker `mysql8` 与 `redis` 容器均显示运行中且健康。只读请求 `GET http://127.0.0.1:5173/login` 返回 HTTP 200，响应为 Demo 已构建静态入口。未认证只读请求 `GET /admin-api/system/auth/get-permission-info` 等待 6 秒后超时；无凭据 GET `/actuator/health` 返回 404/约 0.09 秒。后端生命周期日志记录未认证探测之后线程反复抛出 `NoClassDefFoundError: ch/qos/logback/classic/spi/ThrowableProxy`，同时 `/actuator/health` 请求本身在 access log 中约 53ms 完成。该证据提示共享旧运行时的日志依赖缺失会干扰错误路径，但未确认该异常为所有 API 超时的唯一根因；不继续向共享服务发送探针。未重启或停止进程，未发送登录或业务写请求，未访问/修改共享数据库与 Redis。

Chrome 控制通道不可用后，使用独立 In-App Browser 打开相同 `/login`。页面成功渲染登录表单，辅助树读取到租户“芋道源码”、用户名 `admin`、空密码和登录/手机/二维码/注册入口。只点击了主登录按钮，未填写或发送任何凭据；页面仍在 `/login`，未观察到导航。该空凭据检查仅是登录页前端现态观察，不证明成功登录、错误提示或后端认证。此结果只确认 UI 静态入口和登录组件可渲染、共享后端对未认证权限探测无响应且日志异常；不作为登录或登录后页面功能验收 PASS。T3 仍需在响应的隔离后端完成登录后页面、交互、Network/Console 与响应式覆盖。结构化快照：`current-state-20261116.json`。

### 隔离 Demo 登录后页面抽查

为绕开共享后端超时，在独立 Docker MySQL/Redis 容器中建立 schema `yuheng_t3_20261116`、schema-scoped 账号和 Redis DB 5，隔离后端/UI 分别运行于 48173/5174。冷启动运行 54/54 Liquibase changesets、150 表；用户表 21 行且 password 字段均非空，`system_operate_log.success` 列为 0。原始租户 websites 不含隔离 UI host，故只在隔离 schema 添加 `127.0.0.1:5174`；admin 凭据数据仅在隔离 schema 内调整以完成本次登录验收，schema/容器随后销毁。Redis 首次无密码运行导致后端启动失败，设置仅本轮容器的 Redis requirepass 后重启成功；首次无效启动未处理真实请求。

真实隔离登录 API 成功，In-App Browser 页面随后导航到 `/index`。首页显示欢迎用户、21 个授权模块、506 个可访问入口和系统管理/基础设施等快捷入口；点快捷入口进入 `/system/user`，实际加载 15 条记录、筛选项、部门树、分页与新增/导入/导出/修改控件；侧栏的基础设施可展开且展示代码生成、数据源、文件、任务、配置等菜单。代理运行日志确认登录/授权加载及 `GET /admin-api/system/user/page?pageNo=1&pageSize=10` 返回 HTTP 200。浏览器 DOM/辅助树内未见错误提示；该控制面没有可用截图、浏览器 performance/resource API 或 console 捕获能力，故不声称视觉对照、完整 Network/Console、其它页面、写交互或响应式通过。页面内用户状态开关等写控件均未操作。

之后隔离后端优雅关闭、隔离 UI 进程停止，专用 MySQL/Redis 容器删除；48173/5174/13373/16473 均无监听，共享 `mysql8`/`redis` 容器仍健康，共享 Demo PID 23945/39370 仍运行且未被重启/停止。隔离 token 所在标签已转回登录 URL，本地站点 token 的显式清除 API 在当前 browser wrapper 不可用，标签仍开在隔离 `/login`，但隔离服务与数据已销毁，token 不能再用于认证。证据限本段所列范围，T3 全范围仍开放。

### 2026-11-16 T3 隔离 Demo 浏览器抽查补证

复核确认此前新建的本轮视觉环境仍真实运行：后端 PID 27646/48174、UI PID 27813/5175，专用 schema `yuheng_t3_visual_20261116` 及容器 `yh-t3-visual-mysql-20261116`、`yh-t3-visual-redis-20261116` 均存在；没有使用共享数据库或 Redis。通过全新的 `localhost:5175` origin 打开隔离 Demo 后，首页已渲染授权模块 21、可访问入口 506、已加载字典 388，以及系统管理/基础设施快捷入口。首页 console warn/error 捕获为空。页面截图在本次会话中观察到，但没有导出为仓库文件。

初次点击用户管理后的即时 DOM 快照处于异步加载窗口，显示“暂无数据”；该瞬时快照不得作为故障证据。稍后同页真实加载出部门树、用户筛选、操作控件和共 15 条用户的分页；后端 SQL 日志确认 `GET /admin-api/system/user/page?pageNo=1&pageSize=10` 的列表查询返回 10 行并完成请求。该页没有执行新增/修改/删除/导入/导出等写操作，页面 console warn/error 捕获为空。

从实际菜单进入基础设施代码生成页，页面筛选控件、表格列及空状态可见，console warn/error 捕获为空。后端分页 COUNT 查询日志的 `Total: 1` 仅表示返回一行统计结果，不能据此断言元数据数量；数据源配置查询返回 0 行。页面空结果受测试夹具限制，不将其计为数据源/生成操作或完整页面等价验收。浏览器 wrapper 没有提供可复核的 Network 面板导出，后端访问日志确认相应请求完成；未覆盖所有请求、所有页面、原版同尺寸逐页对照或窄屏响应式。

补充更正：上述“数据源配置查询返回 0 行”仅指数据库表 `infra_data_source_config` 的 Mapper 查询，不能推断 API 返回空列表或缺少主数据源。原始 `ruoyi-vue-pro.sql` 同样没有该表的种子行；Core `DataSourceConfigServiceImpl.getDataSourceConfigList()` 会在查询结果首位动态添加由运行配置构造的 `master` 数据源，ID 为 0。此前隔离环境曾直接观察到 master；本次 48174 环境未捕获此 API 的响应体、未打开导入对话框，不能以数据库行数推断本次 API 的实际响应或代码生成导入可用性。

清理时向专用后端/UI 进程发 TERM，随后停止并删除本轮两个专用容器；复核 48174/5175/13374/16474 无监听、没有 `yh-t3-visual-*` 容器，先前共享 Demo PID 23945/39370 仍运行。该补证仅关闭本次可见首页、用户列表和代码生成空状态的有限抽查，不关闭 T3 总项；T1 固定坐标 registry 安装及 T4 全范围矩阵仍开放。

清理更正：上述容器删除后 MySQL 匿名卷 `7d835539b77e7086d4a5e43b79b215bbb4da31820262e89655d8dec73b30a630` 仍存在，隔离 schema 因而仍留在该卷中。后续核对该卷为先前专用容器挂载、无任何容器引用后，已精确删除该匿名卷并通过 `docker volume inspect` 验证不存在；共享卷未操作。

## 2026-11-16 T1 当前 Core tarball 包外 Demo 消费续验

从当前 Core 源码重建 `yuheng-ui@0.1.0-SNAPSHOT`：29 文件/125 测试通过、边界检查通过、Vite 1466 模块构建成功、声明构建通过。新 tarball SHA-256 `125b85b912806f517489c8824bc8c7651712d52723a59f1e0562497584e2d524`，更新在 Core 仓库受跟踪的 vendor tarball。

隔离复制 Demo UI，确认 `node_modules/yuheng-ui` 指向解包 tarball（元数据包名/版本正确、realpath 位于隔离副本）。复用本机已安装的其他依赖二进制和存储链接，没有 registry 安装或消费 Core 源码。消费者 Vitest 3 文件/14 项、`vue-tsc --noEmit`、平台导入边界检查及 Vite 生产构建（3547 模块）均通过。没有请求共享后端，也没有更改 Demo manifest/lockfile。

这关闭了当前 tarball 的隔离包身份、消费者解析、测试、类型、边界和构建子项。固定坐标 registry 干净安装仍开放：私有 npm group 对该版本此前 404；本轮未发布或重试 registry。故 T1 和全量迁移仍未完成。详情见 Core `docs/verification/yuheng-ui-package-identity/verification.md` 本节。

## 2026-11-16 T4 ERP 默认项第二次写入失败验收

修复前，在独立环境触发第二次 UPDATE 失败：仓库完整表快照恢复，账户旧默认取消已提交。红灯确认后，给模板与 Demo 账户默认状态方法同步补事务。使用新建临时包、mock 关闭和全新隔离环境重跑相同触发器；两个接口均返回 code 500，日志 marker 命中，仓库与账户完整业务表快照均前后相同，默认标志恢复原值。模板/Demo 的修复前后与上游差异已分类，账户事务差异属于本次缺陷修复。

全部原始用户密码在内存比较不变。修复前后两次有效/无效探针环境的专用进程、容器和数据卷已清理，48193/13371/16471 无监听，共享容器仍运行。新增模板契约测试的修复前红灯、修复后绿灯已实测；模板全量 67/67、Demo Maven 40/40 通过。证据与范围见 `erp-default-rollback-20261116/result.md`、`red/runtime.json`、`green/runtime.json`；不关闭 T4 全矩阵、T1 固定坐标消费或 T3 全页面验收。

## 2026-11-16 T4 ERP 默认状态接口真实登录权限验收

已补齐此前缺少的仓库与结算账户默认状态接口无权/有权请求证据。独立 MySQL/Redis 容器和后端 48192 中，Core API 新建普通用户及最小角色，真实登录后无角色用户两个请求均 HTTP 200/code 403、完整业务表快照不变；仅有 `erp:warehouse:update`、`erp:account:update` 的普通角色用户开启和取消两个默认项均 code 0，SQL 状态一致。原有 21 个种子用户密码内存逐行比较不变。模板专项 12/12、Demo Maven 40/40 通过；应用优雅退出，两个专用容器及匿名数据卷移除，48192/13370/16470 无监听。

详情、初始无效夹具尝试、缓存干扰排除、打包四个类身份与完整证据边界见 `erp-default-permissions-20261116/result.md`；最终结果为 `runtime.json`。本次仅关闭两接口权限及正常状态写入子项，不证明事务失败原子性、并发或跨租户行为；T1/T3/T4 全范围仍开放。

## 2026-11-16 T3 基础设施配置页同隔离后端对照续验

使用本轮仍运行的隔离环境：Demo 静态 UI `http://127.0.0.1:5178`、上游 Vite `http://127.0.0.1:5189`，均指向后端 `127.0.0.1:48190`。实际进程命令行和监听端口已核对；Docker 中本轮专用 Redis 容器 `yh-t3-redis-20261116` 在运行。两端页面均从用户管理通过站内可见的“基础设施 → 配置管理”路径打开，最终 URL 均为 `/infra/config`。

浏览器实测两端均显示 28 条配置，第一页记录相同（含 ID、分类、键名、值、备注和时间）；筛选控件均为参数名称、参数键名、系统内置和创建时间，表格列及 10 条/页的分页一致。Demo Console 无 warn/error；原版没有 error，只有既有 Vue Router `next()` 弃用 warning。该证据只覆盖配置页桌面视口和当前只读列表，不代表其他页面或完整 Network 审计。

通过 Docker 内 MySQL 客户端核对隔离 schema：`DATABASECHANGELOG` 56 条、`system_users` 21 条、密码字段为空的用户 0、`system_operate_log.success` 列 0、配置记录 28 条。当前 MySQL 非系统 schema 仅有本轮 `yuheng_t3_full_20261116`，共享 `yuheng_demo` 不存在。页面比较未提交数据变更，历史密码未读取或修改。浏览器对照本身可复核，但隔离运行进程后续清理状态尚未核实，本轮不声称环境已清理。

**状态**：关闭 T3 的基础设施配置页桌面同数据只读对照子项。响应式、其余未覆盖页面、主要交互和全量 Network/Console 验收仍开放；T1 固定版本 registry 安装与 T4 全量权限/租户/事务矩阵仍开放。

## 2026-11-16 T4 ERP 权限与业务模板消费复核

重新核对模板与 Demo 当前代码后，`ErpWarehouseController.updateWarehouseDefaultStatus` 和 `ErpAccountController.updateAccountDefaultStatus` 分别带有 `erp:warehouse:update`、`erp:account:update` 的 `@PreAuthorize`。模板 `test_default_status_mutations_require_update_permission` 定向测试通过。此前迁移计划中的缺注解发现属于历史状态；修复和红绿测试记录见计划 2026-11-14 条目。此次没有调用这两个写接口，故没有新增运行期无权/有权请求证据。

运行 `scripts/verification/business_template_parity_audit.py` 对当前模板仓库与 Demo 消费副本进行复核：ERP 模板/消费端运行源码路径 305/305，会员 227/227，缺失和额外文件均为 0。30 个 ERP 与 17 个会员规范化内容差异均已检查分类：请求 API 与 tagsView 改为复用 `yuheng-ui` compat runtime，另有 Demo 严格 TypeScript 的显式类型注解/断言；ERP 汇总图表用可选链和类型收窄更新 dataset。源码路径齐全，已检查的差异未发现业务流程或 API 契约变化。JSON 结果为 `business-template-source-parity.json`。

验证结果：模板 `python3 -m unittest discover -s tests -p 'test_*.py' -v` 66/66 通过；Demo `mvn -o -Dexec.skip=true test` 40/40 通过；Demo UI `vue-tsc --noEmit` 退出 0、`vite build` 转换 3673 个模块并成功。Vite 仍报告已有超 500 kB chunk 警告；Maven 显示 Byte Buddy 动态 agent 提示，不影响测试结果。JSON 解析、审计脚本 `py_compile` 和 Demo `git diff --check` 通过。

**状态**：关闭 ERP/会员模板到 Demo 的当前源码路径完整性及已知适配差异复核子项。ERP 默认状态接口的无权拒绝/有权允许运行时安全测试仍未执行；T4 完整权限/租户/事务矩阵、T3 全页面与响应式验收、T1 固定版本 registry 消费仍开放。

## 2026-11-16 T1 Core compatibility AutoImport dependency

当前 Demo workspace-linked Core UI 中，消费者测试最初稳定发现 Vite dev 对 Core `compat/utils/formRules.ts` 的 `useI18n()` 注入缺失；生产 build 曾能通过 AutoImport 注入，导致 dev 与 prod 行为依赖不同。Core 现已将该 compat 模块改为显式导入 Core `compat/hooks/web/useI18n`，并新增直接导入行为回归。测试先红（`ReferenceError: useI18n is not defined`），修复后 Core 全量 29 文件/125 项通过。

使用当前 workspace link 重新执行 Demo 三个消费者测试文件，14/14 通过；`vue-tsc --noEmit`、平台导入边界和 Vite 生产构建也通过，生产构建转换 3673 模块。Core 新 tarball 已生成，SHA-256 为 `850f8844ac28f587bacd97284130f09504f2c9e6369a0adadf637aabd336cd81`。因临时消费者离线重装时缺少 pnpm store 中的图标和 Sass 平台包，本轮没有声称更新 tarball 的全新隔离安装通过；固定 registry 查询仍 404，T1 整体保持开放。T3 浏览器全页面覆盖和 T4 全范围矩阵也继续开放。

后续复验通过在全新临时 Demo UI 副本中直接解包该 tarball，并复用已安装工具依赖的只读符号链接完成，未使用 Core workspace 链接。消费者三个测试文件 14/14、`vue-tsc --noEmit` 和平台边界检查通过。以真实 Vite dev server 5190 请求 tarball 内的 `compat/utils/formRules.ts`，响应已包含显式 `useI18n` import；临时服务已停止。tarball 哈希仍为 `850f8844ac28f587bacd97284130f09504f2c9e6369a0adadf637aabd336cd81`。该证据关闭当前 Core 包的离线消费和 dev 转换子项，但固定 registry 坐标仍因 404/本机 npm 未认证未闭合，T1 总项继续开放。

## 2026-11-15 T3 启动白屏修复与原版页面对照续验

- 沿用 `YH-20261111-full-source-migration` 和已确认的迁移授权。本轮使用专用隔离 JAR（端口 48120）、schema `yuheng_t3_more_20261115`、专用 DB 用户 `yh_t3_more15`、Redis DB 5，以及 Demo 静态 UI 5175、原版源码 Vite 5184；两端代理均指向同一隔离后端。启动前 Redis DB 5 为 0。Liquibase 执行 54 个 changeset，产生 150 张表和 21 个租户/用户种子记录。未访问共享 `yuheng_demo`，未改任何密码。
- 根因确认：消费端在 `app.use(router)` 后增加了顶层 `await router.isReady()`，随后才 `app.mount('#app')`。匿名打开受保护根路由时，路由守卫会先请求权限接口；Core 对 401 已实现清 token 并重定向 `/login`。等待期间若启动导航还在进行，挂载被不必要地延后，页面呈空白。移除该等待后重建，干净浏览器标签访问 `/` 实际落在 `/login?redirect=/index` 并渲染登录表单；隔离后端匿名权限接口返回 401。修改仅一行，未改 Core 公共路由行为。
- Demo UI 执行 `vite build` 成功（4321 模块）、`vue-tsc --noEmit` 退出码 0、Vitest 2 文件/11 项通过、平台导入边界检查 PASS、`git diff --check` PASS。构建保留既有大 chunk 警告。
- Core `yuheng-ui` 的 `tests/router/guards.test.ts` 与 `tests/runtime/install.test.ts` 共 24 项通过，Core UI `vue-tsc --noEmit` 通过；Demo 后端 `mvn -o -Dexec.skip=true test` 成功，39/39 测试通过。该 Maven 命令跳过 UI 构建 exec，使用前面已验证的 Demo dist 复制资源；没有启动应用或访问共享库。
- Demo 与原版使用隔离租户 `芋道源码`、用户 `admin` 登录均成功并进入 `/index`。同一浏览器视口比较用户管理、岗位、角色、配置管理、代码生成、数据源配置和表单构建：页面关键筛选项、列、行数/主要值一致。用户管理 15 条、岗位 4 条、角色 5 条、配置 28 条；代码生成在空库显示暂无数据；数据源页显示隔离库连接；表单构建器组件、主要控件一致，Demo 比原版多显示 `Class` 配置和“按钮组”组件。仅进行导航和只读观察，未提交表单或业务写请求。
- CSS preload：浏览器能正常渲染登录表单；登录页动态注册表单 CSS 请求为 HTTP 200、`text/css`、247 字节，响应体 SHA-256 与 dist 文件一致。此前 preload 控制台提示本轮未能复现，且没有证据指向 UI 代理的 OPTIONS 处理，因此不作为本次根因或代码改动依据。
- 路由盘点确认 System/Infra 菜单实际 URL 需依平台菜单树判断；部分臆测路径会显示 404，不代表缺页。原版文件列表直达 `/infra/file` 页面主体为空，Demo 的文件列表菜单路由为 `/infra/file/file-list`，文件配置菜单路由为 `/infra/file/file-config`；本轮对文件页、操作/登录日志、租户及其它 Infra 页面仍未完成完整的可比运行验收。WebSocket、监控等页面遵守既有本轮排除范围。当前证据不覆盖全部页面、响应式断点、完整 Network/Console 或所有可取消表单，因此 T3 保持开放。
- 结束时只向本轮 PID 37871/38195/38220 发送 TERM；三个 PID 均退出，48120/5175/5184 无监听。精确清理本轮专用 schema 和用户（清理前查询已为空，Liquibase/schema 用户临时资源已回收），Redis DB 5 清理后 `DBSIZE=0`。共享 `yuheng_demo` 仍存在，原共享服务未停止，历史密码保持原状。

**状态**：匿名入口白屏修复及本轮覆盖页面的前端回归验证完成。T3 整体继续开放，待补剩余 System/Infra 页面、主要只读/可取消交互、完整 Network/Console、响应式检查和按实际菜单路径的逐页基线。T1 固定版本 registry 发布/干净安装仍受私有制品 404 阻塞；T4 全量后端权限、租户、事务与异常回滚矩阵仍未完成。

## 2026-11-15 T3 菜单与文件页面续验

沿用上节隔离 JAR 和数据环境，通过应用菜单导航检查菜单管理 `/system/menu`、文件列表 `/infra/file/file`、文件配置 `/infra/file/file-config`。两端显示相同菜单树、筛选和操作入口；文件列表均为空且筛选项、表格列相同；文件配置均显示 11 条相同记录及字段、操作入口。此结果补充此前同一隔离环境的页面比较，未执行刷新菜单缓存、文件上传/删除、文件配置测试或修改。

WebSocket 页面两端状态不同：原版显示 `CONNECTING`，Demo 显示 `CLOSED`。浏览器页面代理未转发 WebSocket upgrade，现有证据无法区分代理限制与消费端连接配置，因此记录为待核差异，不作为页面迁移缺陷结论。尝试设置 390×844 浏览器视口后，实际页面仍分别为 582×1260 与 1333×1272；本轮没有形成响应式成对证据。Demo Console 未见 error；原版有 Vue Router `next()` 与 Element Plus `el-link underline` 弃用 warning。完整 Network 请求审计未覆盖。

收尾时先确认本轮后端、Demo 代理和原版 Vite 均已退出，再查询专用资源：隔离 schema 原有 54 个 changeset/150 张表，专用用户对该 schema 有 1 条授权；Redis DB 5 为 13 keys（启动前 0）。随后精确删除 schema `yuheng_t3_more_20261115` 和专用用户 `yh_t3_more15`，清空专用 Redis DB 5。复核 schema、用户和授权均为 0，Redis DB 5 为 0，共享 `yuheng_demo` 仍存在，48120/5175/5184 均无监听；共享服务及历史用户密码未改。此前本节第一条关于“Liquibase/schema 用户临时资源已回收”的记录不准确，以上述实际清理及复核结果为准。

**状态**：本轮关闭菜单管理、文件列表、文件配置的桌面只读页面对照子项。WebSocket 传输层差异、窄屏成对比较、完整 Network/Console、剩余 System/Infra 页面和主要交互继续开放；T3、T1、T4 总项均未完成。

## 2026-11-15 Demo WebSocket 代理修复

根据上一节浏览器观察与当前代码追踪 `/infra/ws` 数据流：Core 页面从当前站点 origin 建立 `ws(s)://<origin>/infra/ws?token=...`；Demo 的 `ui_server.py` 原先只处理 HTTP API 前缀，普通 GET 则按无扩展路由返回 SPA `index.html`。新增回归测试在修复前稳定失败，实际收到 `HTTP/1.0 200 OK` 和 HTML，而非 WebSocket `101 Switching Protocols`，因此已将故障定位到 Demo HTTP 静态代理边界，而非后端 WebSocket 配置。

现由 Demo 静态代理保留原始 WebSocket 路径、查询参数与握手头，将 Upgrade 请求转发至配置的 HTTP(S) 后端；仅在后端成功返回 101 后进入双向 socket 中继，后端非 101 时不伪装成成功握手。新测试使用真实本地 TCP sockets 和合法 WebSocket 握手，验证 101 响应及 masked frame 字节经代理往返完全一致。专项测试修复前失败、修复后通过。

验证：`python3 -m unittest discover -s scripts/tests -p 'test_*.py' -v` 共 26 项通过、7 项按条件跳过（一个需显式配置的隔离仓库 HTTP 测试和六个需打包服务的 HTTP 测试）；`python3 -m py_compile scripts/ui_server.py scripts/tests/test_lifecycle.py` 通过；相关变更 `git diff --check` 通过。此项证明代理握手和原始双向字节转发，不等于 Core WebSocket 认证后应用消息协议、浏览器重连或真实后端端点的端到端验收。

**证据边界更正**：检查原版 `yudao-ui-admin-vue3/vite.config.ts` 发现仅配置 `/admin-api` 且 `ws: false`，没有 `/infra/ws` 代理，故不能据此前页面瞬时状态推断原版 Vite 支持 WebSocket 隧道。Demo 代理故障已有独立红灯证明并已修复；原版与 Demo 浏览器状态差异的根因比较仍未完成。

**状态**：Demo 代理的 WebSocket Upgrade 缺失已修复并具备自动回归；需在新隔离实例中经真实浏览器确认 `/infra/ws` 状态 OPEN、应用消息收发和关闭行为。窄屏、完整页面、Network/Console、主要交互仍未完成；T3/T1/T4 不关闭。

### 2026-11-15 WebSocket 真实后端续验未通过

使用 JAR SHA-256 `eccd2caf2a81ed75411e3a5c38838f0f1c621b46100a076637fb8d9ca9beb2d4`、端口 48122、专用 schema `yuheng_t3_ws_20261115`、专用 MySQL 用户 `yh_t3_ws15` 和 Redis DB 8。空库 Liquibase 执行 54 changeset、创建 150 张表；核对 21 个种子用户口令哈希非空。管理员隔离登录成功。Demo 静态代理在 5177 转发 `/infra/ws` 后，后端返回 HTTP 404，尚未建立 Upgrade，也没有发送 WebSocket 应用消息；这说明代理隧道测试通过，但实际 Boot JAR 并未证明 WebSocket 端点可用。

源码、嵌套 starter JAR 和其 `AutoConfiguration.imports` 均包含 `YudaoWebSocketAutoConfiguration`；Demo `application.yaml` 配置 `yudao.websocket.enable=true`、`path=/infra/ws`、`sender-type=local`。然而对实际运行 JAR 的 `/infra/ws` Upgrade 收到 404，访问 MVC `/actuator/mappings` 未见 WebSocket 映射；当前 Spring Security 也把这些 Actuator 诊断路径作为 SPA 保留路径返回 404，无法读取条件报告。自动配置为何未创建握手映射仍待定位，不据此归咎 Core 或关闭 T3 子项。

安全收尾：第一轮启动时误传了 Redis 索引属性 `spring.redis.database`，应用使用默认 DB 0，并进行数次仅限隔离管理员的登录与只读诊断。发现后即停止实例；随后重启改用 `spring.data.redis.database=8`，确认第二轮使用专用缓存。因 DB 0 启动前没有逐键基线，未对共享 DB 0 执行删除或 FLUSH，保留其当前状态。最终精确删除专用 schema/用户，复核 schema、用户、授权均为 0；Redis DB 8 清理后为 0；共享 `yuheng_demo` 仍存在；48122/5177 均无监听。隔离种子用户口令哈希保持非空；没有运行密码恢复或修改口令。

**结论**：代理本地回归通过；真实后端 WebSocket 端到端验收未通过且根因仍在调查。后续需先在不访问共享 Redis DB 0 的环境下，用正确 Redis 属性和隔离 schema，以 Actuator 或条件报告确认自动配置条件、实际注册的 `WebSocketConfigurer` 与握手映射，再做浏览器 OPEN/消息/关闭验证。T3、T1、T4 仍开放。

### 2026-11-15 WebSocket SPA 映射优先级修复及隔离端到端验证

回到实际 404 的请求分发路径后确认：WebSocket 自动配置类、starter 依赖、`AutoConfiguration.imports` 和 `yudao.websocket.path=/infra/ws` 均存在并已装入 JAR；握手请求仍进入 `SpaController` 的 `@GetMapping({"/", "/{*path}"})`，由其保留路径逻辑返回 404。问题不是自动配置缺失，而是 Spring WebSocket `HandlerMapping` 的默认顺序晚于 `RequestMappingHandlerMapping`，全路径 SPA fallback 先行匹配。此前“自动配置未注册”的推断已由本次隔离实测纠正。

TDD 修复：新增 `WebSocketHandlerMappingOrderConfigurationTest`，修复前因配置类不存在而编译失败；在 Demo bootstrap 添加 `BeanPostProcessor`，仅将 bean 名 `webSocketHandlerMapping` 对应的 `WebSocketHandlerMapping` order 设为 `-1`，使它排在普通 MVC catch-all 之前。定向 Maven 回归 1/1 通过；Demo bootstrap 全测试 `mvn -o -pl yuheng-demo-server/yuheng-demo-server-bootstrap -am -Dexec.skip=true test` 为 40/40 通过；Python 生命周期/WebSocket 代理测试 6/6 通过；Python 编译和 `git diff --check` 通过。隔离 JAR 已成功 package，SHA-256 `4bc65f4f34047dcdb44e6cf7d5bd989dd0412ea3063d6db469fb27bc6294767e`。

真实运行验收：新 JAR 端口 48123、隔离 schema `yuheng_t3_wsfix_20261115`、专用用户 `yh_t3_wsf15`、Redis DB 9；空库 54/54 changesets、150 tables，21 个 seed 用户密码均非空。Demo 静态代理 5178；隔离管理员登录成功。针对 `/infra/ws?token=...` 的真实握手返回 `101 Switching Protocols`；同一连接发 `ping` 收到 `pong`；随后发送 `{type:"demo-message-send", content:{text:"isolated ws roundtrip"}}`，收到 `{type:"demo-message-receive", content:{fromUserId:1,text:"isolated ws roundtrip",single:false}}`；客户端发起正常 socket close 后连接结束。浏览器实际打开隔离 Demo 登录路由并成功加载页面资源，但这轮消息/状态断言使用协议客户端，不声称完成浏览器 WebSocket 页视觉与交互验收。

清理前 Redis DB 9 有 4 keys，均属于本轮专用环境；完成后清为 0。精确删除隔离 schema、专用账号/授权，复核其计数均为 0；`yuheng_demo` 仍存在；48123/5178 无监听；共享服务 48080/5173 保持运行。此轮没有再连接 Redis DB 0，也未修改共享库或历史用户密码。之前首轮误用默认 Redis DB 的事故记录仍保留，不清理其未知历史键。

**结论**：Demo SPA catch-all 与 WebSocket HandlerMapping 顺序缺陷已修复，隔离真实握手、心跳、示例消息回声及关闭均通过。此项关闭 T3 的 WebSocket 传输/协议子项，不代表全页面、全部交互、窄屏或完整 Network/Console 验收完成；T1 固定版 registry 安装、T3 其它覆盖、T4 全量后端矩阵继续开放。

## 2026-11-15 T3 租户套餐页面续验

- 使用隔离 JAR SHA-256 `eccd2caf2a81ed75411e3a5c38838f0f1c621b46100a076637fb8d9ca9beb2d4`，端口 48121；专用 schema `yuheng_t3_tenantpackage_20261115`、MySQL 用户 `yh_t3_tenantpackage15`、Redis DB 7；Demo UI 5176、原版源码 Vite 5185 均指向该后端。首次 Liquibase 运行 54/54 changeset，schema 共 150 张表。没有访问/更改共享 schema 或密码。
- 从两端可见菜单“系统管理 → 租户管理 → 租户套餐”进入真实路由 `/system/tenant/package`。初始页面两版筛选项、搜索/重置/新增/批量删除入口、列头一致。Demo 与原版显示隔离数据库中的相同两条数据（套餐 ID 113、111，名称、状态、备注、时间相同）。
- 两端分别打开新增表单后取消。套餐名输入、菜单权限树及全选/展开控件、状态、备注、确定/取消入口相同；取消后两端仍显示 2 条，未提交写请求。Demo 和原版浏览器 Console error 均为空。
- 该结果也确认初次 schema 记录核对时连接目标应显式使用 `-D yuheng_t3_tenantpackage_20261115`；重核隔离 DB 时发现 2 条套餐、3 条租户种子，故不将先前空状态读数当作准确证据。所有验收均以浏览器同隔离实例实际读取的两条一致记录为准。
- 结束时仅停止本轮原版 Vite PID 40764、原版代理 40815、Demo 代理 40747、隔离后端 40657；48121/5176/5185 均无监听。Redis DB 7 清理后为 0；精确删除本轮 schema 与用户后复核两者不存在，`yuheng_demo` 与共享用户 `yuheng` 仍存在，5173 仍返回 HTTP 200 且 48080 仍由原共享 PID 23945 监听。共享服务未停止，历史用户密码未变。

**状态**：关闭租户套餐页面同数据对照及新增表单打开/取消子项。T3 仍缺剩余页面、全组件和更多写入交互、完整 Network/Console 及响应式覆盖。T1 固定版本发布安装和 T4 全后端权限/租户/事务矩阵仍未完成。

## 2026-11-14 T3 隔离运行与同尺寸页面对照

- 沿用 `workId: YH-20261111-full-source-migration`、已批准迁移范围和版本：code `0.1.0-SNAPSHOT`、governance `0.2.0`、knowledge `0.1.0`。本轮只读浏览器验证；表单仅打开后取消。无业务 API 写操作、文件操作、任务执行或共享库访问。
- 后端从已存在 JAR 复制到 `/tmp/yuheng-demo-t3-followup-20261114.jar`，SHA-256 `eccd2caf2a81ed75411e3a5c38838f0f1c621b46100a076637fb8d9ca9beb2d4`，避免 Maven repackage 触及现有运行进程打开的正式制品。PID 31790 使用端口 48117、全新 schema `yuheng_t3_followup_20261114`、MySQL 用户 `yuheng` 仅对此 schema 的授权、Redis DB 15（启动前 0 keys），显式关闭 security mock 与 Quartz 自动启动。空库 Liquibase 首次运行 54/54 changesets，Rows affected 6702。Demo UI 静态代理 PID 31870/5174，原版源码 Vite PID 31918/5183，两者均代理同一隔离后端；启动后两版登录均成功。
- 用户管理：两版同为 15 条，部门树名称/层级、筛选、列、行操作、10 条分页一致。
- 字典管理：两版同为 385 条/39 页，筛选项、表格列、首屏 10 行、修改/数据/删除操作一致。新增表单的字典名称、字典类型、状态、备注及确定/取消一致；两版仅打开并取消，返回后仍为 385 条。
- 岗位管理：两版同为 4 条，筛选项、列、记录、行操作一致。新增表单标题、编码、顺序、状态、备注及确定/取消一致；两版仅打开并取消，返回后仍为 4 条。
- 菜单管理：两版均显示菜单名称/状态筛选、搜索/重置/新增/展开折叠/刷新菜单缓存，菜单树的图标、排序、权限标识、组件路径、组件名称、状态及节点新增/修改/删除操作相同。没有刷新缓存或打开有写入效果的提交操作。
- 文件列表：两版均为空，文件路径/类型/时间筛选、搜索/重置/上传/批量删除入口及文件名/路径/URL/大小/类型/内容/上传时间列一致；没有上传或删除。文件配置：两版同为 11 条，字段和操作一致；没有编辑、测试、设为主配置或删除。
- 配置管理：隔离空库没有配置种子，两版均为空；参数名称/键名/内置状态/创建时间筛选以及参数主键、分类、名称、键名、值、可见、内置、备注、创建时间、操作列一致。
- Demo 浏览器 `console warn/error` 为 0。原版有 Vue Router `next()` 弃用 warning，无应用 error。截图同为 1332×1272，两个页面分别运行同一 UI 源码/版本以外的原版和 Demo 构建，调用相同后端数据。该证据限以上页面与表单；未覆盖其它页面、全部编辑字段、完整 Network 请求逐项审查及响应式断点。
- 清理前只读数据库核对：54 changesets、150 张表、`system_users` 21 行且 admin 密码哈希非空、字典类型 385 行、字典数据 1726 行；`system_operate_log.success` 列为 0。收到 TERM 后 PID 31790 graceful shutdown，PID 31870/31918 退出；精确删除专用 schema 和授权，清空启动前为空的 Redis DB 15。最终 schema=0、grant=0、Redis DB 15=0，48117/5174/5183 无监听；共享 `yuheng_demo` 仍存在，PID 23945/39370/88324/88411 及其端口均保持。没有改历史密码或共享数据。
- 状态：本轮关闭用户/岗位/字典/菜单/文件列表/文件配置/配置管理上述限定页面的同尺寸对照子项和新增表单取消子项。T3 总体仍需其它页面、编辑交互、响应式及完整 network 覆盖；T1 固定版本 registry 安装和 T4 全量后端差异矩阵仍未完成。

## 2026-11-14 T1/T3/T4 总体验收续查

- 沿用 `workId: YH-20261111-full-source-migration` 与既有完整迁移授权；`codeVersion=0.1.0-SNAPSHOT`、`governanceVersion=0.2.0`、`knowledgeVersion=0.1.0`。本轮仅运行已安装工具、读取现有浏览器和服务状态并补充台账；未修改运行时代码、SQL、已执行 changeset 或共享数据库，未变更历史用户密码。
- 浏览器当前 `http://127.0.0.1:5173/swagger-ui/index.html` 的 Swagger 静态 UI 与 OpenAPI 定义可见，API Server URL 指向 `http://127.0.0.1:48080`。5173 返回 HTTP 200；48080 的 HTTP HEAD 在 3 秒内超时，未得到后端响应。浏览器日志只见既有 Statsig SDK 初始化 warning；此文档页不能证明管理页面或 API 可用。
- PID 23945/39370/88324/88411 与 48080/5173/48099/48100 均保留。Java 进程仍持有 `yuheng-demo.jar`；未构建覆盖 JAR。仅对 48080 发出一次 3 秒超时的 HTTP HEAD 探测，没有登录、调用业务/API 路由、表单操作、写 API 或访问共享数据库。
- 实际检查：Demo UI `./node_modules/.bin/vitest run`：2 个文件、11 项通过；`./node_modules/.bin/vue-tsc --noEmit`：通过；`./node_modules/.bin/vite build`：4321 个模块构建成功，有既有大 chunk 警告。Demo `mvn -o -Dexec.skip=true test`：39/39 通过；命令跳过 Maven 内部前端 exec，但资源阶段复制现存 700 个 dist 文件。业务模板 `python3 -m unittest discover -s tests -p 'test_*.py' -v`：66/66 通过。构建输出更新了 Demo UI `dist/` 与 Maven target 静态资源；没有执行 Maven package/repackage，正式 JAR SHA-256 保持为 `eccd2caf2a81ed75411e3a5c38838f0f1c621b46100a076637fb8d9ca9beb2d4`。
- T1/T3/T4 仍未关闭。T1 缺固定发布坐标的可用制品及干净安装消费证据；T3 缺后续页面和交互的真实浏览器验收、同版本逐屏和响应式覆盖；T4 缺全量选定能力的静态差异、权限/租户矩阵和外部副作用故障注入。下一轮运行复验需新建专用 schema/账号、确认独立 Redis DB 为空并选用空闲端口，配置完成后再启动隔离实例；本轮没有创建这些资源。

## 2026-11-14 T1/T4 Core UI 包续验

- 当前 Core `yuheng-ui` 使用 Node `v22.23.2` 的本地已安装工具执行 Vite production build、`vue-tsc -p tsconfig.build.json`，均退出 0。Vite 输出 1,466 modules transformed；存在 `SystemDataListPage.vue` 动态导入与 `infra/index.ts` 静态导入同一模块的 chunk 提示，不影响本次构建。
- 全量 Vitest 串行运行结果：25 个测试文件、110 项通过。第一次将 build 与 test 并发启动时，包出口测试在 declaration emit 之前读取产物，报告缺失 `dist/index.d.ts`；检查确认 build 命令随后已生成声明，串行重跑全量测试全部通过。该失败是验证顺序竞态，不是当前包持续缺声明。
- 从刚构建的当前源码生成 `/tmp/yuheng-ui-0.1.0-SNAPSHOT.tgz`，包元数据为 `yuheng-ui@0.1.0-SNAPSHOT`，791 个 package exports，655 个文件，包含 `dist/index.js`、`dist/index.d.ts` 和 `dist/styles.css`。SHA-256：`0c9cd4c27af38d51b0b0e381a3797bc42b0c3ca4fa96311ee8bcdd55715c27a3`。本次只在 `/tmp` 生成临时包，未覆盖仓库中较旧的 vendor tarball。
- Demo 依赖树里的 `node_modules/yuheng-ui` 目前仍符号链接到 Core 源码目录，故 Demo 当前工作树不是版本化包消费验证。Core 执行标准 `pnpm build` 因 pnpm workspace 自动尝试解析 Demo 锁定的固定版本、私有 registry 返回 404 而在 install 阶段终止；公共 npm registry 对相同版本也返回 404。新 tarball 的独立消费者目录准备完成，但从公共 registry 安装 Demo 其余依赖长时间无输出，本轮中止该安装；没有运行新 tarball 消费副本的类型检查或生产构建。此前隔离消费旧 tarball 的通过证据仍有效，但不覆盖本次新增源码。
- Core 两模块 DAL 没有 XML Mapper；6 条自定义 SQL 注解已逐项检查。API access/error/job 日志按时间删除，其 DO 为平台共享忽略租户数据；OAuth2 token 按过期时间物理删除，token DO 带租户字段；字典类型软删除更新平台共享字典 DO。未发现这 6 条 SQL 漏加 `TenantBaseDO` 条件。此静态结论不覆盖 MyBatis wrapper 全字段组合和运行期跨租户请求。
- 运行状态只读复测：Demo UI `127.0.0.1:5173/` 返回 200；Core/Demo 后端 `127.0.0.1:48080/admin-api/system/auth/get-permission-info` 2 秒内没有响应。当前服务没有提供可用登录态和后端 API，未做真实浏览器页面/全局样式验收；未重启或停止旧进程，未操作数据库。
- 结果：Core UI 当前源码构建、类型声明生成、单测及临时 tarball 生成通过；固定版本发布和本次新 tarball 消费端 typecheck/build、T3 浏览器视觉验收仍未完成。T1、T3、T4 总项不关闭。

- workId：`YH-20261111-full-source-migration`
- 计划：`../../plans/2026-11-11-full-source-migration.md`；沿用用户已批准的三仓库、业务模板复制消费及隔离数据库验收范围。
- 验证日期：2026-11-14（Asia/Shanghai）
- codeVersion：`0.1.0-SNAPSHOT`；Demo HEAD `b9c4906`、Core HEAD `afbd19e`、模板 HEAD `a754b17`，均含本轮开始前已有工作区修改。
- governanceVersion：`0.2.0`；knowledgeVersion：`0.1.0`（消费端 manifest）。
- 本轮仅新增探针、证据和治理说明，未修改运行时 Java/前端业务代码、历史 changeset 或共享库数据；测试使用此前已构建 JAR。
- JAR SHA-256：`db94df4c4885924b2d61db448b05e7c85ef77c26306e9d2261188bfc0ca94093`。

## 范围与门禁

沿用 T4 平台 API、权限、租户、迁移与密码保留的验收目标。本轮补齐代表性采购/销售/付款/收款真实写流程、九个 Core 自服务/文件/OAuth 写入口匿名认证及代表性跨租户矩阵。使用已有批准规格、计划与实施授权；未新增页面，原型不适用。本轮验收不等于 T3 浏览器验收或全部后端端点穷尽验证。

## 隔离环境

- Docker MySQL `mysql8`；首次 schema `yuheng_t4_flows_20261114`，纠正探针后新建 `yuheng_t4_flows_20261114_retry`，两者均从空库执行 Liquibase 54/54 changeset。
- JAR 使用 local profile、`127.0.0.1:48088`、显式临时数据源、关闭安全 mock 和 Quartz 自动启动；普通密码登录获取真实 token。
- Redis 使用专用 DB 15，开始前 `DBSIZE=0`；应用与共享实例的缓存、令牌、单据号不混用。
- 未向共享 `yuheng_demo` 发出 DDL/DML；最后只读核实共享 schema 仍存在。

## 2026-11-19 本地构建与浏览器现态复核

此轮无数据库访问、依赖安装或共享服务写入。当前源码检查结果：

| 仓库/检查 | 实际结果 | 结论 |
| --- | --- | --- |
| Core `yuheng-ui` Vitest | 29 文件、124 项通过 | PASS |
| Core `yuheng-ui` Vite build | 1466 个模块，构建成功；存在 `infra/api` 静态/动态导入合并提示 | PASS，保留提示 |
| Core `vue-tsc -p tsconfig.build.json` | 退出码 0 | PASS |
| Core package boundary | `yuheng-ui boundary: PASS` | PASS |
| Core compat 全目录 `vue-tsc --noEmit` | 多处既有 TS 配置、AutoImport 全局类型、`.ts` 扩展名与 type-only import 错误 | FAIL；不能用包级声明检查替代 |
| Demo UI Vitest | 3 文件、14 项通过；Vite 依赖扫描提示当前缺包 | PASS，但有环境缺包提示 |
| Demo UI platform import boundary | `PASS` | PASS |
| Demo UI `vue-tsc --noEmit` | 缺 `@iconify/vue`、三个 `@iconify/json` 集合、`echarts`、`lodash-es` | FAIL：依赖未安装，不判为类型源码错误，也不判通过 |
| Demo UI Vite production build | 3670 个模块已转换，最终解析 `@iconify/vue` 失败 | FAIL：依赖未安装，当前源码无法在此工作区构建 |

未运行 pnpm/npm install，未改 manifest/lockfile。原因是 Demo 直接依赖固定坐标 `yuheng-ui@0.1.0-SNAPSHOT`，既有私有与公共 registry 检查均为 404；不能把不完整安装或临时 tarball 路径冒充固定版本消费验收。Core 当前 Vite build 更新了忽略的 `yuheng-ui/dist` 本地产物，不改变包版本或正式消费端锁文件。

Chrome 中已有原版 Vite 页面 `http://127.0.0.1:5186/index` 可渲染首页，但页面 DOM 出现大量“操作失败，系统异常!” toast。当前 Vite 5183 和共享静态 UI 5173 在线；48080 根路径实际返回 404。其余 48099、48100、48129 后端是 Codex app-server 的长驻子进程，数据源归属其它任务；本轮未向它们发请求，也未停止任何进程。原版页面请求的数据源/租户无法建立隔离证明，故不继续点菜单或操作，不计入 T3 页面通过。此观察是原版当前环境状态，不推断迁移代码引入了该异常。

结论：本节首次检查时 Demo UI 的当前测试/边界检查通过，但类型检查及 production build 因断裂依赖链接未通过；后续根因与恢复结果见下节。T3 全量浏览器验收、T1 registry 固定版干净安装及 T4 全范围后端矩阵继续开放。

### 2026-11-19 Demo 工作区依赖链接恢复与回归

复核前述失败后确认，Demo UI `node_modules` 中五个直接依赖符号链接指向不存在的 `yuheng-demo/node_modules/.pnpm` 目录；相应包实际已在 workspace pnpm store 中，包版本分别为 `@iconify/vue 5.0.5`、`@iconify/json 2.2.555`、`echarts 6.1.0`、`lodash-es 4.18.1`、`@types/lodash-es 4.17.12`。曾有 ECharts 5.6.0 留在 `.ignored`，未使用。没有运行安装器、改 manifest/lockfile 或触碰共享服务。

只将上述五个依赖链接恢复到已存在的根 workspace store 后，`require.resolve` 解析到预期 store 路径。Demo UI `vue-tsc --noEmit` 退出 0；Vitest 3 文件/14 项通过；平台导入边界通过；Vite production build 3673 个模块成功。构建保留既有超过 500 kB 的 chunk 警告。Demo `mvn -o -Dexec.skip=true test` reactor BUILD SUCCESS，40 项测试 0 failure/error/skip；前端 dist 由已通过的 Vite build 生成并被 Maven resource 阶段读取。模板仓库 Python unittest 全量 66 项通过。

Core UI 并行复核：Vitest 29 文件/124 项通过，Vite 构建成功，`vue-tsc -p tsconfig.build.json` 声明检查和 `scripts/check-boundary.mjs` 通过；兼容层全目录 `vue-tsc --noEmit` 仍有既有自动导入全局类型、TS 扩展名、type-only import 等错误，未作包级通过推断。Core `verify_bundle.py --json` 为 PASS，`sync_agent_assets.py --check` 为 PASS（0 个资产链接待更新）。

依赖链接恢复仅修改本机忽略的 `node_modules`，未改变仓库源码或锁定版本。私有 npm group 与公共 npm registry 对 `yuheng-ui@0.1.0-SNAPSHOT` 的当前查询仍均返回 404，因此 T1 版本化 registry 干净消费未闭合。浏览器原版 `/index` 异常及未知后端归属按前节记录，未转化为 T3 页面验收。T1/T3/T4 全范围继续开放。

## 真实 ERP 请求结果

脱敏的 53 次请求记录见 `erp-workflows.json`；探针为 `../../../scripts/verification/erp_workflow_probe.py`。请求均检查 HTTP 200 与预期业务码，业务失败不以 HTTP 200 判成功。

| 流程/边界 | 实际断言 | 结果 |
| --- | --- | --- |
| 基础数据 | API 新建分类、单位、供应商、客户、账户、仓库和产品 | PASS |
| 采购订单 → 采购入库 | 未审核订单被业务码 `1030101006` 拒绝；审核订单后创建 10 件入库；入库审核前 `inCount=0`、审核后 `inCount=10` | PASS |
| 采购库存 | 入库审核后有效库存 `10.000000`；重复审核 `1030102003`，未重复增加库存 | PASS |
| 付款创建/审核 | 入库金额 100；付款创建时源单 `paymentPrice=100`、付款状态 10；审核后状态 20；重复审核 `1030601003` | PASS |
| 付款边界/回滚 | 有付款时入库反审核返回 `1030102008`；追加付款 1 返回 `1030102007`，付款主表/明细仍各 1 条，源单金额仍 100 | PASS |
| 销售订单 → 销售出库 | 未审核订单返回 `1020201006`；审核后创建 4 件出库；创建待审核单时 `outCount=4`，库存仍为 10；审核后库存才降为 6 | PASS |
| 销售重复审核 | 重复审核返回 `1020202003`，没有重复扣库存 | PASS |
| 收款创建/审核 | 出库金额 80；收款创建时源单 `receiptPrice=80`、收款状态 10；审核后状态 20；重复审核 `1030602003` | PASS |
| 收款边界/回滚 | 有收款时出库反审核返回 `1020202008`；追加收款 1 返回 `1020202007`，主表/明细仍各 1 条、源单金额仍 80 | PASS |
| 财务反审核/重审核 | 付款与收款 20 → 10 → 20 均成功；源单金额保留 100/80 | PASS |
| 最终数据库与 API | 六种单据均为状态 20、tenant 1；库存 API 1 行、数量 6；数据库库存唯一有效行 `1:6.000000`；流水为 `70:+10`、`50:-4` | PASS |

创建采购/销售单据使用 `POST /admin-api/erp/{resource}/create`，审核使用 `PUT .../update-status?id=...&status=20`；业务类型采购入库 11、销售出库 21。金额断言遵守当前 Service：财务创建时占用来源金额，状态更新不重新计算金额。

首次探针在销售待审核阶段把 `outCount` 预期写成 0，实际为 4，故失败，记录保存在 `erp-workflows-first-attempt.json`。对照 `ErpSaleOutServiceImpl.updateSaleOrderOutCount`，上游、模板与 Demo 均汇总全部未删除出库单；采购的已审核进度语义不同。修正的是测试假设，没有改生产行为或把错误断言算作 TDD 红灯；随后使用全新 schema 重跑完整 53 次请求通过。

## Core 认证与跨租户请求矩阵

脱敏的 24 次请求见 `security-boundaries.json`。

九个匿名写入口逐路由均为业务码 401：

- `PUT /system/notify-message/update-read`、`PUT /system/notify-message/update-all-read`。
- `POST /system/oauth2/authorize`。
- `PUT /system/user/profile/update`、`PUT /system/user/profile/update-password`。
- `POST /system/social-user/bind`、`DELETE /system/social-user/unbind`。
- `POST /infra/file/upload`（multipart）、`POST /infra/file/create`。

本轮未向外部 OAuth/社交服务发请求，也没有执行认证后的真实文件上传或密码修改。九个 401 只证明相应路由的未认证拒绝，不代表全部自服务业务成功路径。

跨租户测试通过平台 API 创建新套餐、新租户和该租户管理员（仅临时 schema），授予仓库 create/update/query 与库存 query 及必要父菜单，不授予 `system:tenant:visit`：

1. 租户 1 管理员伪造 `tenant-id:121` 读库存、写仓库均返回 403。
2. 新租户账号读库存返回 0 行，读取租户 1 仓库 ID 返回 null；对该 ID 更新返回 `1030400000`（不存在），租户 1 仓库名称未变。
3. 新租户账号伪造 `tenant-id:1` 返回 403；保持自身 tenant-id 加 `visit-tenant-id:1` 也返回 403。
4. 新租户账号正常创建自己的仓库成功，数据库 `tenant_id` 为其自身租户 ID。
5. 平台管理员合法 `visit-tenant-id` 新租户读库存为 0；下一请求不带 visit header 恢复租户 1，库存 1 行，证明请求上下文清理。
6. 初始 21 个种子用户密码哈希在内存中前后精确比较相同；不保存哈希、密码或 token 到证据。

夹具准备有两次失败：第一次套餐只包含按钮菜单、漏掉父菜单，权限响应过滤后目标权限为空；按 `MenuServiceImpl.filterDisableMenus` 补齐父链。第二次仓库名 `T4 tenant own warehouse` 超过当前 DDL `varchar(20)`，返回业务码 500，日志明确为 MySQL `Data too long for column 'name'`；改用合规长度重跑通过。原历史租户 121/122 已过期，本轮未修改其有效期或密码。

**保留问题**：仓库 VO 没有与当前 DDL 一致的长度校验，超长输入会落到数据库异常并返回 500；未作为迁移差异擅自扩大字段或修改既有 changeset。需要后续核对字段来源并补参数边界验收。财务精度、多明细、退货、任意负值/非法状态、全部自服务业务成功路径与所有实体跨租户边界仍未穷尽。

## 自动回归与清理

2026-11-14 实际执行：

- 模板：`python3 -m unittest discover -s tests -p 'test_*.py' -v`，58 项通过、退出码 0。
- Core：`python3 -m unittest discover -s tools/governance/tests -v`，51 项通过、退出码 0；三个仓库 `git diff --check`、新增探针语法及三份证据 JSON/脱敏检查通过。
- Demo：`YUHENG_TEST_URL=http://127.0.0.1:48088 python3 -m unittest discover -s scripts/tests -p 'test_*.py' -v`，21 项中 20 项通过、1 项自定义 Controller fixture 缺失跳过、退出码 0。日志 `/tmp/yuheng-t4-demo-tests-20261114.log`。
- Demo 回归首次因停止实例与 HTTP 测试并行而连接拒绝（8 个 error）；重新启动同一 schema 后，按顺序重跑得到上述通过结果。不是业务修复或被隐藏的通过项。
- 最后一次启动 Liquibase 无新增执行；真实业务失败和异常日志保存在 `/tmp/yuheng-t4-flows-20261114-retry-console.log`，首轮和最终日志同前缀。
- Core 治理包检查 `python3 tools/governance/verify_bundle.py . --json` 为 PASS；`sync_agent_assets.py --check` 报告迁移 skill 的三个 agent 发现入口存在 DRIFT，未执行安装或消费端快照刷新。规则要求普通验收只做 check，本轮不宣称三个入口已同步；技能规范补充已写入 Core 唯一治理来源。
- 回归全部结束后向验证过身份的专用 JAR 发 SIGTERM，等待退出；精确删除本轮两个 schema、撤销对应授权；SQL 断言临时 schema 0、临时授权 0、共享 schema 1。仅清理开始前为空的 Redis DB 15，未清理共享 DB 0；48088 无监听。

## 当前结论

本轮 T4 子项通过：代表性采购、销售、收付款闭环与回滚，Core 九个写入口的匿名认证，代表性租户过滤/越权拒绝/合法访问恢复。T4 总项继续保持未完成，待补参数边界、其它代表性业务/权限/事务覆盖；T3 浏览器与同尺寸视觉验收、本机服务恢复不在本轮验证结果中。T1 registry 固定版本 404 的既有阻塞仍保留，不发布、不改锁文件。

## 复用探针

先手工创建全新专用 schema 并将 JAR 指向它，使用独立端口及空闲专用 Redis DB；本探针不创建、删除 schema，也不能仅凭参数证明 HTTP 服务实际绑定该 schema，运行人必须先核对进程数据源配置。显式设置 `YUHENG_PROBE_USERNAME`、`YUHENG_PROBE_PASSWORD` 环境变量后执行：

```sh
python3 scripts/verification/erp_workflow_probe.py \
  --base-url http://127.0.0.1:48088 \
  --schema yuheng_t4_flows_20261114 \
  --output /tmp/erp-workflows.json
```

以上是已删除 schema 名的复现示例，须先创建新的隔离环境；不要对现有共享服务运行。探针拒绝常用正式端口和不符合临时命名的 schema，并要求商品表为空；完成全部 HTTP 回归后停止测试实例，再精确清理所建 schema、授权和专用缓存。Core 迁移 skill 的唯一来源已补入工作流副作用、菜单父链、夹具字段长度及清理顺序要求，尚未刷新消费端托管快照或安装缺失 agent 入口。

## 2026-11-14 T4-WH 仓库名称边界修复

沿用本 workId、code/governance/knowledge 版本及 T4-WH 子计划。用户在报告该缺口和下一步后明确要求继续，构成局部修复授权。本节为后续修复结果，前文的未修复状态保留为历史记录。

### 根因、设计与最小变更

实际迁移 `001-erp-schema.sql` 的 `erp_warehouse.name` 是 `varchar(20)`；上游、模板和 Demo 保存 VO 只有 `@NotEmpty`，表单没有长度约束。此前真实 JAR 日志明确为 `MysqlDataTruncation: Data too long for column 'name'`。原始完整生产 DDL 来源仍有既有核验缺口，本次遵守当前已执行表结构，不据此宣称第三方结构来源问题关闭。

- 两份 `ErpWarehouseSaveReqVO.name` 添加 `@Size(max = 20)` 与中文错误消息，保留 `@NotEmpty`；新增和修改继续共用该 VO。
- 两份 `WarehouseForm.vue` 名称输入添加 `maxlength="20"`，名称规则添加 `max:20`。未修改布局、其它字段或 API 契约。
- 未更改数据库脚本、Core 认证/异常处理、仓库 Service、上游源码；POST create / PUT update 的方法、权限与租户边界保持原样。模板/Demo VO 归一包名后完全一致，表单完全一致。
- 长度按现有 Bean Validation/HTML 字符串计数约定；已验证 ASCII 和中文 BMP，补充字符（如 emoji）的计数与 MySQL 字符数差异尚未覆盖。

### AC → 测试与执行证据

| 验收 | 实际证据 | 结果 |
| --- | --- | --- |
| AC-T4-WH-1 | `ErpWarehouseValidationTest`：真实 Hibernate Validator 接受 ASCII/BMP 20 字符，拒绝 21 字符，create/update 两种 id 状态及 null/空串保留原校验 | PASS |
| AC-T4-WH-2 | `warehouse-name-boundaries.json`：独立 JAR 23 次请求，20 字符可创建/修改，21/空串/null/缺失名称在 POST/PUT 均为业务码 400，且逐次 SQL 比较记录及原值不变；最终有效仓库 2 条、tenant=1 | PASS |
| AC-T4-WH-3 | 模板 2 项新增契约测试、Demo 1 项新增前端契约测试；浏览器名称框输入 21 个字母实际只保留 `abcdefghijklmnopqrst`，空名称提交显示必填提示，取消后列表仍 2 条，刷新原路由正常 | PASS |

红灯先于修复：`mvn -o -Dexec.skip=true -Dtest=ErpWarehouseValidationTest -Dsurefire.failIfNoSpecifiedTests=false test` 运行 3 项，其中拒绝 21 字符断言失败（预期 1 个 violation，实际 0；无编译/环境错误）；模板 2 项与 Demo 前端 1 项因缺少限制失败。对应日志 `/tmp/yuheng-wh-validation-red-maven.log`，随后仅作上述最小修复。

实际绿灯/构建命令（均退出码 0）：

- `mvn -o -Dexec.skip=true test`：8 项通过（5 项 SPA、3 项仓库 Validator）。日志 `/tmp/yuheng-wh-validation-green-maven.log`。
- `vitest run`：8 项通过；`vue-tsc --noEmit`、`node scripts/check-platform-imports.mjs` 通过。
- `vite build`：成功，有既有大 chunk 警告。前端使用当前已安装依赖，未重新执行 registry 安装或修改锁文件。
- `mvn -o -Dexec.skip=true package`：8 项测试通过并成功生成包含最新前端 dist 的 JAR；仅跳过重复调用前端 exec，因为本次已单独完成前端 build。日志 `/tmp/yuheng-wh-package.log`。
- 新 JAR SHA-256：`a4e2b94aa6aadbe4868804b38f8233d56adc1e77e18434753846143143127b6a`。
- 模板 `python3 -m unittest discover -s tests -p 'test_*.py' -v`：60 项通过。
- Demo `python3 -m unittest discover -s scripts/tests -p 'test_*.py' -v`（配置隔离 URL/schema/账号及证据输出变量）：22 项中 21 项通过、1 项自定义 Controller fixture 缺失跳过。日志 `/tmp/yuheng-wh-demo-retry-tests.log`。

HTTP 首次探针只写了字段消息，遗漏 Core 统一包装的 `请求参数不正确:` 前缀，实际已返回业务码 400，故消息断言失败。核对 `GlobalExceptionHandler.methodArgumentNotValidExceptionExceptionHandler` 后修正探针，另建全新 schema 重跑完整 23 次请求；生产异常处理没有变化。首次记录保存在 `warehouse-name-first-attempt.json`，不当作生产修复红灯。

### 浏览器与隔离清理

浏览器：IAB，截图 1332×1272，临时 origin `http://127.0.0.1:48089`，种子管理员、tenant 1。从 ERP 系统 → 库存管理 → 仓库信息打开新增框，测试名称输入上限、必填提示和取消；未通过 UI 保存或删除，两个仓库来自上述 HTTP 探针。截图 `warehouse-name-limit.png` 显示最终只保留 20 个字母。此次只覆盖这一表单与路由刷新，不替代 T3 全页面同尺寸对照、编辑表单逐项 UI 验收或全局样式结论。浏览器临时标签已关闭，原 5173 标签未操作。

数据库：`yuheng_t4_wh_20261114` 与 `yuheng_t4_wh_20261114_retry` 均从空库执行完整 54 个 changeset，独立端口 48089、安全 mock 关闭、Quartz 自动启动关闭、专用 Redis DB 15 开始前为空。所有回归和浏览器步骤结束后，正常停止专用 JAR 并等待退出，精确删除两个 schema 及对应授权，清理本次专用 Redis DB 15。最终断言：临时 schema 0、授权 0、共享 `yuheng_demo` schema 1、48089 无监听。本轮未写共享库、未调用密码更新、未修改历史用户密码。

**结论**：T4-WH 的仓库名称 500 缺口已修复并通过上述验收。其它字段参数边界、ERP 其它写流程、T3 全页面/样式对照、T1 registry 和治理 skill 发现入口余项仍保留；本轮没有发布、提交 Git 或重启原有 48080/5173 服务。

### T4-WH 收尾复查

- 已将模板迁移矩阵中“仓库名称超长返回 500”的旧描述更新为本次修复和验收结果，并在模板 SQL 来源审计补记；ERP 的 `generated-pending-verification` 状态保留，没有以参数校验证据代替 DDL 来源、许可和完整业务验收。
- 再次执行模板全量测试：60 项通过；Demo `mvn -o -Dexec.skip=true test`：8 项通过。本地 `node_modules/.bin/vitest run`：8 项通过；本地 `node_modules/.bin/vue-tsc --noEmit` 及 `node scripts/check-platform-imports.mjs` 通过。
- 本次收尾最初使用 `pnpm test/typecheck/lint:platform-imports`，触发其自动依赖安装并遇到既有私有 registry 的 `yuheng-ui` 404；这三个命令未进入目标检查，不能记作测试失败或通过。发现后停止使用该入口，改为上述已安装本地工具完成验证。未继续发布或解析 registry，也未修改锁文件；此记录不撤销此前“不再操作 registry”的约束。
- 清理环境后重新执行 Demo 脚本测试：共 22 项，15 项通过，7 项因未配置隔离 HTTP 实例而按条件跳过。该结果与此前实例存活时的 21 通过、1 夹具跳过分别记录，不以跳过项替代那次 23 请求的运行证据。
- 三个仓库 `git diff --check` 均通过；迁移矩阵与两个仓库名称 JSON 可解析，证据扫描无 token、口令或密码哈希，HTTP 探针 Python 语法通过；两份 VO 归一业务包名后内容一致，两份表单字节一致。
- 重新只读核对：本次两个临时 schema 数量 0、对应授权 0、共享 `yuheng_demo` schema 1，48089 无监听。JAR SHA-256 与上述实测制品相同。没有重建临时环境或重复发出写请求。

收尾日志：`/tmp/yuheng-wh-final-template-tests.log`、`/tmp/yuheng-wh-final-demo-script-tests.log`、`/tmp/yuheng-wh-final-maven.log`、`/tmp/yuheng-wh-final-frontend-direct.log`、`/tmp/yuheng-wh-final-typecheck-direct.log`、`/tmp/yuheng-wh-final-imports-direct.log`、`/tmp/yuheng-wh-final-temporary-database-cleanup.log`。这些临时日志是本机辅助记录；长期验收证据为本目录中的文档、脱敏 JSON 和截图。

## 2026-11-14 T4-RET 双明细退货与精度验证

沿用 `workId: YH-20261111-full-source-migration`；codeVersion `0.1.0-SNAPSHOT`、governanceVersion `0.2.0`、knowledgeVersion `0.1.0`。范围、授权、REQ/AC、隔离方式及回滚见计划的 T4-RET 小节。此次仅新增验证探针与记录，未改生产源码、SQL、Core 或共享库。

### 源码依据与证据

采购/销售退货和对应订单的四个 Service，在归一化包名及空白后与工作区 `ruoyi-vue-pro` 当前源码一致。创建退货时订单退货数即被占用，审核及反审核改变库存；超量在更新订单明细时抛错，由事务回滚此前写入。`MoneyUtils` 对明细金额及百分比计算执行两位小数 `HALF_UP`，再按 Service 顺序汇总税费、优惠和其他金额。订单/退货响应明细不暴露 `totalPrice`，因此该字段以数据库核对；其它响应数值以 Python `Decimal` 解析比较。

| 验收 | 执行证据 | 结果 |
| --- | --- | --- |
| AC-T4-RET-1 | 采购订单、销售订单及两种退货均为双商品；6 位小数单价、3 位小数数量和不同税率，实际响应的明细税额/主单金额及 MySQL 订单、退货主明细字段逐项与独立 Decimal 计算比对。采购退货总额 1.05，销售退货总额 0.46 | PASS |
| AC-T4-RET-2 | 创建、审核、反审核、再审核、重复审核、已审核编辑/删除拒绝、反审核后删除。创建/状态变化期间核对订单退货数量和两商品库存；最终库存分别 7、6，库存流水按业务类型分别为 50/70 各 2 条、60/61/80/81 各 4 条 | PASS |
| AC-T4-RET-3 | 每种退货让第二条明细超量：对比写入前后两个订单、明细、退货、明细、库存及流水完整行快照一致；新建隔离库的全部种子用户 id/密码值在内存中逐行比较一致，证据不保存口令、哈希或令牌 | PASS |

命令：在确认 JAR 实际连接 `yuheng_t4_returns_20261114_final`、专用 DB 用户和 Redis DB 15 后，设置隔离种子账号的 `YUHENG_PROBE_USERNAME` / `YUHENG_PROBE_PASSWORD`，执行 `python3 scripts/verification/erp_returns_probe.py --base-url http://127.0.0.1:48090 --schema yuheng_t4_returns_20261114_final --output docs/verification/2026-11-11-full-source-migration/erp-returns-boundaries.json`。退出 0，51 次 HTTP 请求通过；详细方法、路径、业务码、金额与覆盖范围见同目录 JSON。所有写入在新建隔离库，权限为管理员、tenant 1；本次不构成所有角色和租户的权限覆盖。

首次探针错误地预期响应明细存在 `totalPrice`，读取时抛 `KeyError`；对照响应 VO 后改为 SQL 验证。第二次探针误用单数 `_item` 表名而触发 MySQL 查询失败；对照实体和 DDL 修正为 `_items`，并将表快照检查移到所有业务写入前。两次均是探针缺陷，不是产品行为失败或 TDD 红灯；分别保留 `erp-returns-first-attempt.json`、`erp-returns-second-attempt.json`。修正后在第三个全新隔离库完整重跑通过。

### 环境、回归与清理

JAR SHA-256 `a4e2b94aa6aadbe4868804b38f8233d56adc1e77e18434753846143143127b6a`；每个空库均由 JAR 的 Liquibase 执行 54 个 changeset；隔离端口 48090，安全 mock 关闭、Quartz 自动启动关闭，专用 Redis DB 15 初始为空。连接隔离服务执行 Demo 脚本 22 项：20 项通过，2 项因仓库空库专用探针及自定义 Controller 夹具未配置而跳过；Demo Maven 8 项及模板全量 60 项通过。日志分别为 `/tmp/yuheng-returns-20261114-demo-http-tests.log`、`/tmp/yuheng-returns-20261114-maven-tests.log`、`/tmp/yuheng-returns-20261114-templates-tests.log`。

按顺序停止三次专用 JAR、等待退出后，精确删除本轮三个临时 schema 和专用用户/授权，清理本轮使用的 Redis DB 15。最终核对临时 schema、用户、授权均为 0，Redis DB 15 为 0，48090 无监听，共享 `yuheng_demo` schema 仍存在。没有对共享库写入，也没有修改历史用户密码；没有使用 npm registry 或重启既有服务。

**自检结论**：T4-RET 的限定场景完成；退款单财务联动、负数量/非法状态、并发退货、所有业务字段边界、UI 写流程及生产 DDL 来源未覆盖。T4、T3、T1 仍未完成，ERP 模板保留 `generated-pending-verification`。

## 2026-11-14 T4-REFUND 退货财务联动

沿用 `workId: YH-20261111-full-source-migration`，codeVersion `0.1.0-SNAPSHOT`、governanceVersion `0.2.0`、knowledgeVersion `0.1.0`；局部规格、授权与 AC 见计划 T4-REFUND。生产源码、SQL 和共享数据库均未修改。

源码和上游 UI 明确采购退货通过付款单 `bizType=12`、销售退货通过收款单 `bizType=22` 传入负数金额；财务单创建即占用源退货退款金额，而非等财务审核。扩展 `scripts/verification/erp_returns_probe.py`，在此前 T4-RET 流程上同时核对财务主明细、源单和数据库行快照。

| 验收 | 实际结果 |
| --- | --- |
| AC-1 | 采购退货 1.05、销售退货 0.46 分别以负数财务明细创建，源单退款额分别为正 1.05/0.46；再申请 0.01 均返回超额业务错误，相关主表、明细、源单、订单、库存和流水的完整行快照不变。PASS |
| AC-2 | 有占用的退货反审核被拒绝；财务单审核后无法删除，财务单反审核后退款占用仍保留；删除财务单将占用归零，退货可反审核和删除。PASS |
| AC-3 | 继承 T4-RET 双明细、金额、库存与超量回滚验证；最终库存 7/6、流水 20 条，隔离库种子密码逐行比较一致。PASS |

在确认实例数据库实际为 `yuheng_t4_returns_20261114_refund`、专用 DB 用户、端口 48091、Redis DB 15 后，运行 `YUHENG_PROBE_USERNAME=... YUHENG_PROBE_PASSWORD=... python3 scripts/verification/erp_returns_probe.py --base-url http://127.0.0.1:48091 --schema yuheng_t4_returns_20261114_refund --output docs/verification/2026-11-11-full-source-migration/erp-refund-boundaries.json`，退出 0、77 次真实请求通过。JAR 与 T4-RET 为同一构建；空库执行 54 changeset，安全 mock 和 Quartz 自动启动关闭。新证据不包含凭据、token 或密码哈希；旧的 51 次 T4-RET 证据保留，现有脚本已扩展为 77 次覆盖。

连接隔离实例执行 Demo 脚本 22 项，20 项通过、2 项因仓库空库专用探针和自定义 Controller fixture 未配置而跳过；Demo Maven 8 项和模板 60 项通过。日志：`/tmp/yuheng-refund-demo-tests.log`、`/tmp/yuheng-refund-maven-tests.log`、`/tmp/yuheng-refund-template-tests.log`。

全部回归结束后正常停止 JAR，删除本轮专用 schema 和 DB 用户/授权，清理初始为空的 Redis DB 15；确认临时 schema、用户和授权为 0，48091 无监听，共享 `yuheng_demo` schema 仍存在。未操作 registry，未更改历史密码。

**风险与未覆盖**：两个财务明细 Mapper 当前通过 `MapUtil.getDouble` 将 MySQL `SUM(decimal)` 转为 double 再构造 BigDecimal；本次 1.05/0.46 场景通过，不能据此认定大金额或高精度安全。财务单编辑、并发退款、非预期正负号和非法状态、UI 交互未覆盖。T4-REFUND 限定场景完成，T1/T3/T4 总项及 ERP DDL 来源与许可审计仍未完成。

## 2026-11-14 T4-MONEY 财务汇总精度修复

关联 `YH-20261111-full-source-migration`，codeVersion `0.1.0-SNAPSHOT`、governanceVersion `0.2.0`、knowledgeVersion `0.1.0`；规格、授权与 AC 见计划 T4-MONEY。模板和 Demo 的付款/收款明细 Mapper 原来将 SQL `SUM(decimal)` 经 `MapUtil.getDouble` 再构造 `BigDecimal`，丢失大额或小数低位；现按既有库存 Mapper 模式直接读取 BigDecimal，空结果或 SQL NULL 仍为 0。SQL、租户/逻辑删除过滤、Service 及已执行 changeset 未改。

| 验收 | 实际证据 |
| --- | --- |
| AC-1 | 新增 `ErpFinanceSumPrecisionTest`，真实调用 Mapper 默认方法、模拟数据库返回 BigDecimal：修复前付款和收款 2 项均断言失败（不是编译/环境错误），修复后均通过，覆盖正负 `9007199254740991.123456`、`0.000001`、空列表与 SQL NULL。红灯 `/tmp/yuheng-finance-precision-red.log`，绿灯 `/tmp/yuheng-finance-precision-green.log`。 |
| AC-2 | 模板与 Demo 四个 Mapper 同步；离线 Maven `-Dexec.skip=true test` 共 10 项通过，`-Dexec.skip=true package` 成功（使用已有 UI dist，不执行 registry 安装）。新 JAR SHA-256 `8190e4d5008b2d2f582ce3c50ede493dd5b80af8125a7cb694c1a7c65046059a`。 |
| AC-2 | 真实 JAR + 独立 MySQL 共 26 次请求，付款及收款各 `9007199254740991.12`，源单 API 与数据库均精确匹配；再次申请 `0.01` 被拒绝，完整行快照不变。详见 `erp-finance-precision.json`。另在全新 schema 重跑退货/退款闭环 77 请求通过，详见 `erp-refund-after-finance-fix.json`。 |

大额探针首次在端口尚未监听时发生连接拒绝，无业务请求，保留 `erp-finance-precision-startup-failure.json`；确认实例启动后在同一仍为空的 schema 重跑通过，此失败不是生产逻辑红灯。MySQL DECIMAL 六位小数的 Mapper 返回值由单元测试覆盖，大额 HTTP 选择两位金额以符合现有订单金额计算；并未证明前端 JavaScript 数值能无损表示该大额金额。

隔离端口 48092、两个新 schema、专用用户及开始前为空的 Redis DB 15；两次空库各执行 54 changeset，安全 mock、Quartz 自动启动关闭。回归：模板 60 项通过，连接隔离实例的 Demo 脚本 22 项中 20 项通过、2 项条件跳过。正常停止实例后删除两个临时 schema 和专用账号/授权并清理 Redis DB 15；核对临时 schema、用户及授权均为 0，端口关闭，共享库仍存在。种子密码逐行比对不变，共享库和历史密码未写。无 registry 操作。

范围限制：Mapper 单测以模拟结果验证 Java 转换，真实 MySQL/API 覆盖两位大金额；六位精度真实数据库路径、前端金额表示、退款财务编辑、并发以及其他业务汇总未穷尽。T4-MONEY 仅关闭本次两个 Mapper 已验证的精度缺口，T1/T3/T4 总项与 ERP 生产 DDL 来源审计仍未完成。

## 2026-11-14 T4-FIN-EDIT 财务明细编辑

`workId: YH-20261111-full-source-migration`，codeVersion `0.1.0-SNAPSHOT`、governanceVersion `0.2.0`、knowledgeVersion `0.1.0`。局部规格及授权见计划 T4-FIN-EDIT。模板和 Demo 的付款、收款 Service 编辑明细时，原 `diffList` 对相同 ID 只保留新对象；若同一明细改指向另一业务单，重算集合不含旧对象，旧单已付款/已收款或退款占用不会释放。两个 Service 现于明细写入后重算旧、新明细引用的全部业务单，仍在原事务内；没有改变 SQL、VO、权限、租户或数据库结构。

真实 HTTP 红灯：采购付款明细原关联入库单 1，金额由 10 改为 20 后切换到入库单 2；请求成功，但旧单仍为 20，预期 0。23 次请求的红灯和旧值保存在 `erp-finance-edit-red.json`。修复后全新 schema 的 46 次请求验证采购/销售同类型切换、金额修改、超额回滚、删除旧项并新增项（`erp-finance-edit-green.json`）。继续扩展探针覆盖采购入库与退货、销售出库与退货之间同 ID 切换；完整新库 66 次请求、16 次源单金额检查通过（`erp-finance-edit-types.json`）。超额编辑前后数据库主表、明细、订单、退货、库存和流水快照一致；两种类型切换后旧业务单金额归零、新单金额正确。

跨类型探针首次采购部分通过，随后销售出库因采购退货测试夹具尚未反审核造成库存不足；这是夹具顺序错误，失败保留在 `erp-finance-edit-types-fixture-failure.json`。修正夹具、全新 schema 重跑通过。另在独立新库重跑既有退货退款 77 次请求通过（`erp-refund-after-finance-edit.json`）。红灯仅对采购真实复现，收款同类缺陷由相同代码路径和绿灯请求覆盖，不将销售写成已单独观察的红灯。

新 JAR SHA-256 `ccbc7b6cd10a28820705d393ec1ad2b8f7ae0658e345416df3c169e603bdea62`；`mvn -o -Dexec.skip=true package` 和后续 `test` 均通过，后端测试 10 项。模板 60 项通过；隔离实例上的 Demo 脚本 22 项中 20 项通过、2 项按条件跳过。新空库各执行 54 changeset，专用端口 48093、专用 DB 用户、Redis DB 15 初始为空，安全 mock 和 Quartz 自动启动关闭。

测试结束后顺序停止所有专用 JAR 并删除本轮 5 个临时 schema、专用用户和授权，清理 Redis DB 15；最终临时库/用户/授权均为 0、缓存为空、48093 无监听，共享 `yuheng_demo` 仍存在。隔离库种子密码逐行比对不变，共享库和历史密码未写；未执行 registry 操作。

本次覆盖同一租户、管理员、单条财务明细及其替换，不等于跨租户恶意明细 ID、跨单据明细归属、并发编辑或全部财务流程已验证；这些边界和前端 UI 仍待审计。ERP 模板仍为 `generated-pending-verification`，T1/T3/T4 总项未完成。日志 `/tmp/yuheng-edit-package.log`、`/tmp/yuheng-edit-maven-tests.log`、`/tmp/yuheng-edit-template-tests.log`、`/tmp/yuheng-edit-demo-tests.log`。

## 2026-11-14 T4-FIN-OWNER 财务明细归属

沿用 `workId: YH-20261111-full-source-migration`，codeVersion `0.1.0-SNAPSHOT`、governanceVersion `0.2.0`、knowledgeVersion `0.1.0`；授权与 AC 见计划 T4-FIN-OWNER。付款/收款新增时禁止客户端提交明细 ID；编辑时非空 ID 必须属于当前单据现有明细，且不得重复。无效付款明细返回 `1030601006`，收款明细返回 `1030602006`；原事务保证失败不写入。模板和 Demo Service 与错误码同步，没有更改历史 SQL 或 Core。

红灯：隔离真实 JAR 以付款单 B 的明细 ID 编辑付款单 A，旧实现返回业务码 500；证据 `erp-finance-owner-red.json`，只证明采购付款的该负例。修复后，空库实测付款与收款各覆盖外单 ID、不存在 ID、重复 ID、新增提交 ID，均返回相应业务错误并逐次比较相关订单、财务主表/明细、退货和库存完整行不变；合法编辑金额仍成功，38 请求通过（`erp-finance-owner-green.json`）。

进一步在另一个独立空库，为付款和收款各通过 SQL 插入 `tenant_id=999` 明细作为隔离夹具，再用租户 1 管理员编辑本租户单据并传入该异租户明细 ID；均被业务错误拒绝，所有相关表行快照不变。该夹具不包含异租户财务主单或登录账号，只验证目标明细 ID 归属边界，不代表完整跨租户用户/权限矩阵；包含上述负例和合法编辑总计 40 请求通过（`erp-finance-owner-tenant.json`）。独立新库的既有财务编辑探针 66 请求通过（`erp-finance-edit-after-owner.json`）。

新 JAR SHA-256 `84c74e66a80032590a0a761ba70d941870fc544fc738d766d96e0bc38dc05fb0`。`mvn -o -Dexec.skip=true package` 及后续 `test` 通过，后端 10 项；模板 60 项通过；隔离服务 Demo 脚本 22 项中 20 项通过、2 项条件跳过。空库各执行 54 changeset，专用端口 48094、专用 DB 用户和开始前为空的 Redis DB 15，安全 mock 与 Quartz 自动启动关闭。

验证结束后正常停止所有专用 JAR，精确删除 4 个临时 schema 和专用用户/授权，清理 Redis DB 15；核对临时库、用户、授权均为 0，缓存为空，48094 无监听，共享 `yuheng_demo` 仍存在。隔离库原有用户密码逐行比较不变；没有写共享库、修改历史密码或操作 registry。日志 `/tmp/yuheng-owner-package.log`、`/tmp/yuheng-owner-maven-tests.log`、`/tmp/yuheng-owner-template-tests.log`、`/tmp/yuheng-owner-demo-tests.log`。

本次没有覆盖完整跨租户用户登录/授权矩阵、并发编辑与其他单据的明细归属，前端写操作和生产 DDL 来源仍待核验；ERP 继续为 `generated-pending-verification`，T1/T3/T4 总项未完成。

## 2026-11-14 T3 隔离配置页视觉续验与清理

在已启动的隔离验证环境中，通过 `http://127.0.0.1:5174/infra/config` 检查配置管理页。页面请求和列表渲染正常，共显示 28 条记录，筛选、分页和编辑/删除入口存在；Console warn/error 为 0。本次只读观察，未提交任何新增、编辑、删除或导出。

实测首行参数值单元格约 92px 宽，表格行高约 224px。该记录的长编号模板被按标点逐段折行，导致列表密度明显异常。对照原版 `/Users/huhua/study/ai/yuheng/yudao-ui-admin-vue3/src/views/infra/config/index.vue` 与 Core 迁移副本，三者的值列均未设置固定宽度或 `show-overflow-tooltip`；当前值列又使用 `overflow-wrap: break-word`。因此可确认页面可用性问题来自表格窄列下长字符串换行，并非 API 返回乱码、接口失败或 Demo 特有的页面迁移遗漏。待全局样式验收时，应使用相同视口对照原版，评估对该列增加省略号和可查看完整值的 tooltip/详情，而不要全局改变普通文本的换行策略。本次未修改源码。

隔离 JAR PID 84311 和 UI 代理 PID 84329 已通过 TERM 正常退出；端口 48095、5174 均无监听。Redis DB 15 清理后 `DBSIZE=0`。Docker MySQL 中专用 schema `yuheng_t4_continue_20261114` 已不存在，针对该 schema 的 `yuheng` 权限计数为 0，共享 `yuheng_demo` 仍存在。未更改共享数据或历史用户密码。

**状态**：本次仅完成 T3 的一个基础设施只读页面抽样和精确清理，不构成所有页面、全局样式或主要交互验收；同尺寸原版对照仍缺，T3 不关闭。T1 固定版本 registry 发布/消费验证仍阻塞；T4 全量运行配置、授权/租户矩阵与显式异常事务回滚审计仍未完成。

### 原版同库对照阻塞及环境清理

随后为同尺寸原版对照新建独立 schema `yuheng_t3_visual_20261114`，新隔离 JAR 使用端口 48096、原版源码 Vite 使用 5175、Demo 静态 UI 使用 5176，二者均指向同一隔离服务。空库 Liquibase 54 changeset 成功；没有连接共享 schema。

原版登录无法通过：浏览器点击登录后，`/admin-api/system/auth/get-permission-info` 请求等待超时；原版 `src/views/Login/components/LoginForm.vue` 的 `handleLogin` 在 `finally` 中无条件调用 `loading.value.close()`，但失败发生在创建 `ElLoading` 实例之前，触发 `Cannot read properties of undefined (reading 'close')`。当前 `.env.local` 为 `VITE_APP_CAPTCHA_ENABLE=false`，所以进入无验证码直接登录路径。此错误解释了登录页无法继续进行页面截图对照，但不表示 Demo/Core 登录存在同样错误。本次未编辑原版源码，未向业务表写入数据。

隔离 JAR 收到 TERM 并完成 Spring/Tomcat graceful shutdown；原版 Vite、Demo UI 代理和 JAR 端口 5175、5176、48096 均已关闭。Redis DB 14 清理后为 0；测试 schema `yuheng_t3_visual_20261114` 已删除，其对应 `yuheng` 授权为 0；共享 `yuheng_demo` 仍存在。T3 同尺寸的登录后页面对照仍待完成，需在原版登录故障可绕过且不改变共享数据的环境中重试。

### 原版同视口页面对照与图标注册修复

使用新隔离 schema `yuheng_t3_login_api_20261114`、JAR `48097`、原版源码 Vite `5175` 和 Demo 静态代理 `5176` 做同源比较。前端代理均明确指向隔离后端，空库由 Liquibase 成功执行 54 个 changeset。前次原版登录超时的根因是 Vite 代理未设置隔离后端地址、请求落到不可用的 `48080`；设置 `VITE_BACKEND_ORIGIN=http://127.0.0.1:48097` 后，浏览器登录成功，隔离后端登录 HTTP 200（约 0.41s），登录权限接口 HTTP 200（约 0.21s）。

同一浏览器视口约 1910×1075、相同租户、相同隔离后端及数据：

| 页面 | 原版与 Demo 对比结果 |
| --- | --- |
| 基础设施 / 配置管理 | 菜单、筛选字段、操作入口、28 条结果及表格列宽相同；参数值列 157px，首行约 132px。长编号模板在窄值列换行是原版已有表现，不是迁移样式回归。 |
| 系统管理 / 用户管理 | 菜单、部门树、筛选/操作、15 条用户数据和表格结构一致；表格主体宽约 1367px，首行约 49px，按钮 SVG 和宽度一致。 |

第一次对比配置页时，Demo 的搜索/重置/新增/批量删除/导出按钮没有 SVG，按钮宽约 64px；原版按钮有 SVG、宽约 80px。源码比较发现原版入口注册 Iconify ep/fa/fa-solid collections，而 Demo 入口遗漏注册。`consumer-entry.test.ts` 增加图标集合注册契约后，初次测试目标断言失败（8 项中的 1 项）；在 `main.ts` 使用 `@iconify/vue` 的 `addCollection` 注册三组本地 JSON 集合后，目标测试通过。更新 dist 并重载 Demo 后五个操作按钮均有 SVG，宽度与原版一致，表格宽度和行高保持一致。Demo 页面 Console warn/error 为 0；原版 Console 有 Vue Router `next()` 弃用 warning，本次未修改原版工程。

验证命令：Demo `npm test`：2 个文件、9 项通过；`npm run lint:platform-imports`：PASS；`npm run typecheck`：PASS；`npm run build`：PASS（构建输出含大型 chunk 警告）。`git diff --check` PASS。

清理：原版 Vite、Demo 代理和隔离 JAR 均已停止；端口 5175、5176、48097 无监听。专用 schema 已删除，对应 `yuheng` grants 为 0；Redis DB 13 清理后 `DBSIZE=0`；共享 `yuheng_demo` 保留。没有写共享 schema，也未修改历史用户密码。

**结论**：已修复一个 Core compat UI 在 Demo 消费端遗漏 Iconify 集合注册导致的按钮图标缺失，且两个代表性页面的桌面布局与原版一致。T3 尚缺剩余页面逐项对照、390×844 窄屏原版成对比较和主要写流程验证，不能据本次样本声称全局迁移验收完成。T1 registry 固定版本消费与 T4 全量后端审计仍未关闭。

### 2026-11-14 T3 窄屏同视口续验受阻及清理

尝试复用隔离服务（JAR 48098、原版 Vite 5175、Demo 静态代理 5176）比较 `/infra/config`。尽管浏览器 viewport capability 接受 390×844，原版页面实际 `innerWidth/innerHeight` 仍为 1910×1075，Demo 页面为 582×1260，视口覆盖没有作用于这两个既有标签；因此截图、表格列宽及行高不构成同尺寸证据。Demo 截图中折叠菜单浮层覆盖筛选区与表格，但因视口不同，不能据此断言是迁移回归。未做 UI 写操作，也没有修改业务页面。

清理后确认隔离 JAR、UI 进程已停止；48098、5175、5176 均无监听。Redis DB 12 清理后为 0。隔离 schema `yuheng_t3_mobile_20261114` 已删除，`yuheng` 对该 schema 的 grants 为 0；共享 `yuheng_demo` 仍存在。数据库账号还有其他历史隔离库授权，清理只针对本次 schema，没有对账号做全局撤权。浏览器视口 override 已 reset。

**状态**：窄屏原版与 Demo 成对验收仍受浏览器视口覆盖不生效阻塞，T3 不关闭；需用能对两个页面施加相同 CSS viewport 的新浏览器上下文重新验收配置管理和用户管理，并扩展其余页面及主要交互。T1 registry 固定版本消费和 T4 全量后端差异审计仍未完成。

## 2026-11-14 T3 隔离原版与 Demo 页面复验

使用同一个浏览器窗口分别查看 Demo (`127.0.0.1:5174`) 与原版源码 (`127.0.0.1:5175`)，两端指向隔离后端 `127.0.0.1:48107`、同一个隔离 schema、同一个管理员与租户数据。浏览器视口约 1512×1272，按页面截图观察，没有执行页面写操作。

| 页面 | 对比结果 |
| --- | --- |
| 基础设施 / 配置管理 | 面包屑、文档提示、筛选项、按钮、列名、记录与操作入口对应一致。长参数模板值列很窄并逐段折行，Demo 和原版均复现，属于上游既有布局表现。 |
| 系统管理 / 用户管理 | 面包屑、三个文档提示、部门树、筛选及新增/导入/导出/批量删除入口、用户表格列与行数据对应一致。 |

原版首次打开时 Vite 代理使用默认后端 `48080`，产生接口超时；将本轮启动的 Vite 显式设置为 `VITE_BACKEND_ORIGIN=http://127.0.0.1:48107` 后登录成功。重启复用已有依赖目录里的 Vite 可执行文件，没有触发 pnpm 安装或修改 lockfile。Demo 页面未见功能缺失或样式差异；此轮只覆盖两个列表页面，不代表全部路由、交互或响应式样式均已验收。

清理核实：本轮隔离 schema `yuheng_t3_ui_20261114` 与用户 `yh_t3_ui` 均不存在，用户 schema grants 为 0；Redis DB 3 为 0；48107、5174、5175 无监听。共享 `yuheng_demo` 仍存在，原有 5173 服务仍由 PID 39370 提供，本轮未停止。

**状态**：配置管理和用户管理桌面列表完成原版同视口复验，结果一致。T3 全页面/主要交互/窄屏验收仍未完成；T1 registry 固定版本消费及 T4 全量权限、租户和事务审计仍开放，整体迁移不关闭。

### 2026-11-14 T3 窄屏同视口续验

在同一受控浏览器上下文设置并核实 CSS viewport `390×844`，对照原版 Vite `5176` 与 Demo 静态 UI `5174`。二者使用同一隔离后端 `48108`、同一个隔离 schema、管理员和租户数据；对照 `/infra/config` 与 `/system/user`，没有执行业务写操作。

- `/infra/config`：两版的筛选表单、表格与菜单内容在窄屏下布局对应一致。响应式侧栏以浮层展开时会盖住页面内容；表格可视宽约 328px，内部列内容需横向查看，但 `documentElement` 和 `body` 的 scrollWidth 均为 390px，没有造成整页横向溢出。该行为在原版也存在。
- `/system/user`：两版用户管理页均有同样的侧栏浮层遮挡现象；部门树和筛选表单纵向排列，表单内容宽约 340px、可视宽约 328px，表格内部宽 328px。整页宽度仍为 390px，布局结果相同。
- 原版开发服务出现 Vue Router `next()` 弃用 warning；Demo 页面布局/接口检查未观察到额外错误。该 warning 属上游现有行为，本轮未编辑原版。

视口 reset 后停止本轮原版 Vite、Demo 代理和隔离 JAR。schema `yuheng_t3_mobile2_20261114` 与专用用户 `yh_t3_mob2` 删除；Redis DB 3 清理后为 0；48108、5174、5175、5176 均无监听。共享 `yuheng_demo` 仍存在，5173 服务仍由 PID 39370 提供，未停止。

**结论**：配置管理与用户管理窄屏原版/Demo 成对布局一致；已确认窄屏侧栏遮挡是原版既有表现。T3 仍缺其它页面、主要写工作流与完整样式验收；该抽样不关闭 T3。T1 固定版本 registry 消费和 T4 全面后端审计仍开放。

### 2026-11-14 T3 系统角色与菜单页面续验

在独立 schema `yuheng_t3_system_20261114`、后端 `48109`、Demo UI `5174`、原版 Vite `5177` 上复核系统管理页面。Demo 与原版的角色管理均显示 5 个角色、相同字段、权限操作和分页，桌面布局一致。

打开两版菜单管理后，均显示系统菜单树（首屏可见“作者动态”“Boot 开发文档”“系统管理”“基础设施”等），工具栏、树表列、状态开关和行操作一致。此前“Demo 树表行未渲染”的临时判断错误：使用了普通 `el-table` 的 DOM 选择器统计 Element Plus `el-table-v2` 虚拟表格，因而计数为零；页面截图和可见文本已经显示树表正常。进一步对照原版和 Core compat 的 `index.vue`，数据请求、`handleTree` 转换与虚拟表格绑定相同，差异仅为迁移后的模块导入路径。没有刷新菜单缓存、新增、修改或删除。

测试环境 Liquibase 从空库执行，后端 JAR SHA-256 为 `eccd2caf2a81ed75411e3a5c38838f0f1c621b46100a076637fb8d9ca9beb2d4`。结束后专用 schema 和账号已删除，Redis DB 3 为 0，48109、5174、5175、5176、5177 均无监听；共享 `yuheng_demo` 仍在，5173 服务 PID 39370 未停止。

**状态**：角色管理和菜单管理桌面页完成成对复验，未发现迁移差异。T3 仍需复核部门及其它页面、主要写工作流；T1/T4 未关闭。

### 2026-11-14 T3 部门管理桌面对照

在隔离 schema `yuheng_t3_dept_20261114`、后端 48110、Demo UI 5174、原版 Vite 5178 下对照 `/system/dept`。两版均显示租户根部门、深圳/长沙分公司、研发/市场/财务/运维部门及子部门；负责人、排序、启停状态、创建时间和修改/删除操作相同，筛选栏和新增/展开折叠/批量删除入口一致。两版的“展开/折叠”都能收起部门树。没有提交新增、修改或删除。

Console 中原版重复出现 Vue Router `next()` 弃用 warning；Demo 未观察到额外页面异常。隔离 schema 和专用用户已删除，Redis DB 3 清理后为 0；48110、5174、5178 无监听；共享 `yuheng_demo` 仍存在，5173 PID 39370 未停止。

**状态**：部门管理桌面对照通过。T3 的 system/infra 其余页面和主要写操作仍未全部验收，T3 不关闭；T1 固定版本消费和 T4 全量后端审计仍开放。

### 2026-11-14 T3 角色管理主要 UI 交互对照

在隔离 schema `yuheng_t3_interaction_20261114`、后端 48111、Demo UI 5174、原版 Vite 5179 下，对照角色新增表单和超级管理员“菜单权限”面板。两版表单字段均为角色名称、标识、显示顺序、状态和备注，并提供确定/取消；菜单权限面板的角色信息、全选/展开折叠控件、菜单树节点和确定/取消一致。两版分别打开表单及权限面板后都通过取消关闭，没有创建角色、保存或变更权限。相关页面 API 请求返回 200。

隔离 schema/专用账号已删除，Redis DB 3 清理后为 0；48111、5174、5179 无监听；共享 `yuheng_demo` 仍存在，5173 PID 39370 未停止。

**状态**：角色表单与菜单权限面板的打开/取消流程完成同视口对照。T3 仍缺租户/用户等其它页面表单、主要业务写流程和剩余页面覆盖；T1/T4 仍未完成。

### 2026-11-14 T3 Infra API 日志页面续验

在隔离 schema `yuheng_t3_infra_20261114`、后端 48112、Demo UI 5174、原版 Vite 5180 下对照 API 错误日志和访问日志。两版的筛选字段、搜索/重置/导出入口、表格列头、面包屑与空数据状态一致；隔离库无日志数据，因此详情抽屉没有可供打开的行。Demo 通过可见菜单“基础设施 → API 日志 → 错误日志”能稳定进入 `/infra/log/api-error-log`；访问日志菜单项也存在并可进入 `/infra/log/api-access-log`。曾尝试的 `/infra/api-error-log` 和 `/infra/api-access-log` 是错误旧路径，返回 404 页面，不属于菜单实际路由，不作为迁移差异。

本次为只读页面检查，没有调用处理状态变更或导出。原版 Vite 输出 Vue Router `next()` 弃用 warning；Demo 没有观察到额外页面异常。停止本轮服务后，专用 schema/账号删除，Redis DB 3 为 0，48112、5174、5180 均无监听；共享 `yuheng_demo` 仍存在，5173 PID 39370 未停止。

**状态**：错误日志和访问日志列表桌面对照通过；空库限制了日志详情交互覆盖。T3 仍缺其它 Infra 页面、非空日志详情、主要写流程及整体响应式验收；T1/T4 继续开放。

## 2026-11-14 T4 销售出库多明细事务回滚

在隔离 JAR（SHA-256 `b799c21bca8cf41215dabe6922c10277d0ccc0ec3cd03f05ece86a6d2f7144ae`）、新 schema `yuheng_t4_atomic_20261114_final`、端口 48101 与 Redis DB 9 上验证。空库执行 Core/Demo Liquibase 54 个 changeset，种子管理员登录后经 21 次 HTTP API 请求创建两种商品、采购订单/入库、销售订单及两条明细的待出库单。商品一有库存 5，商品二库存为 0。

审核销售出库时第一条明细先尝试扣减商品一，第二条明细因商品二库存不足拒绝，API 返回业务码 `1030404000`。逐行数据库快照显示审核前后均为：商品一库存 `5.000000`，商品二无库存行，库存流水只有采购入库 `+5.000000`，出库单状态仍为待审核 `10`。因此本真实 Controller/Service/MySQL 路径确认 `@Transactional(rollbackFor = Exception.class)` 回滚了第一条明细的库存行/数量变化及出库状态更新，没有留下部分库存流水。

探针调试记录：首个隔离库因漏掉销售订单审核步骤，在出库创建时被正确业务拒绝；第二个隔离库触发目标不足库存拒绝，但探针误用了错误码；两者均未作为产品缺陷，完整隔离数据随库删除。第三个全新库补齐业务前置条件及预期码后通过，脱敏请求与 SQL 快照 `/tmp/yuheng-t4-atomic-rollback.json`。验证后 JAR 优雅停止；本轮三个 schema 均删除、对应 grants 为 0；Redis DB 9 为 0；48101 无监听；共享 `yuheng_demo` 仍存在，未更改历史密码。

**范围**：证明销售出库审核的第二条明细库存不足会原子回滚，不外推到采购入库、退货、盘点、调拨、财务写流程的异常注入，也不等于完整权限/租户矩阵或事务语义审计。T4 总项继续未完成；T1 固定版本消费与 T3 全量视觉/交互验收也仍开放。

## 2026-11-14 T4 ERP 单价与优惠率边界

金额范围契约测试先红：采购/销售订单、采购入库/退货、销售出库/退货六类保存 VO 中，可选明细 `productPrice` 没有拒绝负值，文档中的百分比优惠 `discountPercent` 也没有 0–100 边界。模板和 Demo 均同步加入 `@DecimalMin(value = "0", message = "产品单价不能小于 0")` 以及 `discountPercent` 的 `@DecimalMin(0)` / `@DecimalMax(100)`。字段继续允许为空以兼容现有 Service 默认处理；本项没有约束“其它金额”、定金、财务已付/本次金额等口径不明确或可能承载冲销的字段。

隔离 JAR/schema `yuheng_t4_moneybounds_20261114`、端口 48104、Redis DB 6 上执行 11 个真实 API 负例：采购/销售订单负单价；采购/销售订单、采购入库、采购退货、销售出库、销售退货的优惠率边界（-1 或 101）；采购入库/退货、销售出库/退货负单价。均在参数校验层返回业务码 400 和对应中文提示。SQL 前后计数确认除四份有效前置采购订单/入库及销售订单/出库外，没有新增采购/销售订单、入库/出库或退货行；两类退货主/明细表仍为 0。没有已审核业务金额变化或库存写入。

模板 Python 全套治理测试 62 项通过；Demo 离线 Maven package 成功，`mvn -o -Dexec.skip=true test` 37 项通过。实例已优雅停止；测试 schema 与 grants 清零，Redis DB 6 为 0，48104 无监听，共享 `yuheng_demo` 保留。没有改 SQL 或历史用户密码。

**范围**：拒绝负产品单价及优惠率 <0 或 >100，不约束零单价、可空字段默认值、税率、其它金额、财务项金额、价格精度或舍入，也不关闭 T4 其余业务流程/权限/租户矩阵及 T1/T3。

## 2026-11-14 T4 ERP 库存移动数量边界

源码红灯定位到五类 VO 的明细 `count` 仅非空、未校验正数：销售出库、采购退货、销售退货、其它入库、其它出库；采购退货/销售退货/销售出库另缺少列表级联 `@Valid`，单独给字段加约束不会执行。模板治理测试 `test_physical_stock_movement_quantities_must_be_positive` 修复前红灯覆盖 5 个缺约束 VO 和 3 个缺级联验证列表；模板与 Demo 同步增加 `@DecimalMin(value = "0", inclusive = false, message = "产品数量必须大于 0")`，并为三类列表补 `@Valid`。测试要求采购入库、采购/销售退货、销售出库及其它入/出库 6 类物理库存移动都具备正数约束和列表级联校验；模板适用测试全绿。

使用当前源码打包 JAR（本次重新 package）、隔离 schema `yuheng_t4_qty_20261114`、端口 48102、Redis DB 8 实测。种子管理员经 HTTP 登录后，对销售出库（-1）、销售退货（0）、采购退货（-0.5）、其它入库（-1）、其它出库（0）提交非法数量，五个接口均在参数绑定/校验阶段返回业务码 400 和“产品数量必须大于 0”；采购入库已有正数校验保持。相关十张出入库/退货单主表及明细表请求前后有效记录数均为 0；无库存、流水或单据写入。另有最初验证脚本的重复种子名称/错误字段假设中止，没有认定为应用失败；随后使用已建隔离夹具完成五接口校验。

验证：模板 `python3 -m unittest discover -s tests -p 'test_*.py' -v` 61 项通过；Demo Maven 离线 reactor package 成功；`mvn -o -Dexec.skip=true test` 37 项通过。普通 `mvn -o test` 被现存 pnpm lockfile 与 package 版本不一致挡住：lockfile 仍为 `workspace:*`，manifest 为 `0.1.0-SNAPSHOT`；为本次 Java 回归跳过内嵌前端步骤后测试通过，没有改动 lockfile。`/tmp/yuheng_t4_qty_20261114` 未留敏感数据或测试凭据。

清理：隔离 JAR 优雅停止；schema 已删除且对应 grants 为 0，Redis DB 8 为 0，48102 无监听，共享 `yuheng_demo` 仍存在。没有写共享库、清空历史密码或改动 SQL changeset。

**范围**：修正并验证五类负数/零数量入口及列表级联校验，不外推到价格、折扣、金额符号、数量小数精度等全部参数边界，也不关闭其余 ERP 事务和权限/租户审计。变化属于模板和 Demo 共有源码缺口，已同步；T1/T3/T4 总项仍未完成。

## 2026-11-14 T4 ERP 采购/销售订单数量边界

在前一项库存移动数量修复后继续审查，发现采购订单和销售订单明细也只有 `@NotNull`，列表没有级联 `@Valid`。模板测试先红确认这两个 VO 的正数及级联约束缺失；模板与 Demo 同步增加 `@DecimalMin(value = "0", inclusive = false, message = "产品数量必须大于 0")`，并为订单明细列表增加 `@Valid`。已有相同契约测试覆盖 8 类采购/销售订单、入库、出库和退货入口。

隔离 JAR、schema `yuheng_t4_orderqty_20261114`、端口 48103、Redis DB 7 上，API 初始化租户管理员和基础分类、单位、供应商、客户、账户及商品后，POST 负数量采购订单与零数量销售订单均返回业务码 400、消息“请求参数不正确:产品数量必须大于 0”。请求前后 `erp_purchase_order`、`erp_purchase_order_items`、`erp_sale_order`、`erp_sale_order_items` 有效记录数均为 0，确认未创建主表或明细行。

模板 Python 全量治理测试 61 项通过；Demo 离线 Maven 编译/打包成功，`mvn -o -Dexec.skip=true test` 37 项通过。隔离实例已优雅停止，schema 和授权已删除，Redis DB 7 为 0，48103 无监听，共享 `yuheng_demo` 保留。没有修改 SQL、共享数据或历史密码。

**范围**：关闭订单、库存移动及退货 VO 数量必须为正且列表需级联验证的这一组边界，不表示价格/折扣等所有 ERP 金额参数均已审计，也不关闭 T4 全量权限/租户/事务审计或 T1/T3。

## 2026-11-14 T4-PO-OWNER 采购订单明细归属

关联 `YH-20261111-full-source-migration`，codeVersion `0.1.0-SNAPSHOT`、governanceVersion `0.2.0`、knowledgeVersion `0.1.0`；局部规格见计划 T4-PO-OWNER。模板与 Demo 的采购订单新增时拒绝提交明细 ID，编辑时非空明细 ID 必须属于当前订单且不得重复，违反时返回业务码 `1030101011`。变更位于原事务内，未修改 SQL 或已执行 changeset。

隔离真实 JAR 红灯使用订单 B 明细编辑订单 A，旧实现返回业务码 500，见 `erp-purchase-owner-red.json`。修复后独立空库 16 次请求覆盖外单、不存在、重复、新增自带及异租户明细 ID，非法请求被拒绝且相关表完整行快照不变，合法编辑通过，见 `erp-purchase-owner-green.json`。异租户明细以 SQL 构造孤立夹具，没有异租户主单或登录账号，不代表完整跨租户权限矩阵。独立空库的财务编辑和采购销售链路回归 66 次请求、16 项检查通过，见 `erp-finance-edit-after-po-owner.json`。

离线 Maven package 和 test 通过，后端 10 项；模板测试 60 项通过，Demo 脚本测试 22 项中 20 项通过、2 项按条件跳过。JAR SHA-256 `179b0f7cfc348e04182561f6063d3d7757041901d3b7df63e4d79fe0411c4167`。回归实例首次启动漏传 Redis 密码导致认证失败，未发业务请求；重新创建该专用空库并补齐配置后回归通过。日志 `/tmp/yuheng-po-owner-regression.log`、`/tmp/yuheng-po-owner-regression-retry.log`、`/tmp/yuheng-po-maven-tests.log`、`/tmp/yuheng-po-template-tests.log`、`/tmp/yuheng-po-demo-tests.log`。

隔离实例停止后精确删除本轮三个临时 schema 与专用用户和授权，清理初始为空的 Redis DB 15；核对临时库、用户、授权均为 0，端口关闭，共享 `yuheng_demo` 仍存在。隔离库种子密码比较不变，未写共享库、修改历史密码或操作 registry。

另有九类采购、销售、库存单据使用类似明细差异处理，尚未逐项验证或修复；并发、完整跨租户用户权限、前端写操作和生产 DDL 来源仍待核验。ERP 保持 `generated-pending-verification`，T1/T3/T4 总项未完成。

## 2026-11-14 T4-SO-OWNER 销售订单明细归属

沿用 `YH-20261111-full-source-migration` 和计划 T4-SO-OWNER。模板与 Demo 新增销售订单时拒绝客户端提交明细 ID，编辑时非空 ID 必须属于当前订单且不得重复，错误码 `1020201011`；未修改 SQL、接口或事务边界。

真实 Service、模拟 Mapper 的测试在修复前显示外单 ID 没有被拒绝；新增自带 ID 的用例在进入产品校验时因测试未注入产品服务触发空指针，说明未提前拒绝，但不代表真实环境也会产生同一异常。测试代码首次因 Mapper 重载匹配器歧义未编译，修正后才取得上述红灯；日志 `/tmp/yuheng-so-owner-red.log`。修复后 3 项测试覆盖外单、不存在、重复、新增自带 ID 以及合法已有明细与新增明细混合，离线 Maven 全量 13 项通过，模板 60 项通过，日志 `/tmp/yuheng-so-owner-green.log`、`/tmp/yuheng-so-template-tests.log`。

这些是 Service 和模拟依赖层面的验证，未在真实 HTTP/MySQL 复现销售订单非法输入，也不能证明事务回滚、跨租户用户权限或并发行为；当前运行 JAR 亦未更新。另有八类采购、销售和库存单据使用类似差异处理待审计，ERP 仍为 `generated-pending-verification`，T1/T3/T4 总项未完成。本次未操作数据库或 registry。

## 2026-11-14 T4 ERP 税率与参考价格边界

沿用 `YH-20261111-full-source-migration`，继续金额输入边界审计。代码证据确认采购/销售单据行的税率用于 `税额 = 产品金额 * 税率 / 100`，客户及供应商默认税率会复制到单据行；因此六类采购/销售订单、入库/出库、退货的税率和客户/供应商默认税率统一限制在 0–100，空值仍允许。产品重量、采购/销售/最低参考价及盘点、其它入库/出库、调拨单价限制为非负，均保持可选。模板和 Demo 后端同步增加 Bean Validation；八个前端税率输入同步增加 `max=100`。

负数语义按现有流程保留：库存盘点差额可正可负；采购退货付款明细及销售退货收款明细会用负值表示退款；财务明细可能承载冲销。本轮没有给这些字段加非负约束，也没有扩展到其它费用、定金、折扣金额、财务优惠金额、金额精度或舍入口径。

模板契约测试新增两项，修复前两项均红，修复后模板全量 Python 治理测试 64 项通过。Demo 新增 `ErpMoneyBoundsValidationTest`，直接运行 Hibernate Validator 检查 8 个税率 DTO 接受 0/100、拒绝 -0.01/100.01 且允许空值，并检查 9 个产品/库存参考价格字段拒绝 -0.01、接受 0 且允许空值；Demo Maven 全量测试 39 项通过。Demo UI `vue-tsc --noEmit`、Vitest 9 项、平台导入边界检查和 Vite production build 均通过。模板和 Demo `git diff --check` 通过；构建仅有既有大 chunk 警告。

本轮没有运行隔离 HTTP/MySQL 请求：共享旧服务的只读打包 HTTP 回归对 `127.0.0.1:48080` 返回 SPA 路径 404、API 超时，且此前已确认该进程是旧 JAR 并存在日志类加载故障，不能作为当前代码验收。因此结论限于模板契约、Demo Bean Validation 运行时和前端构建测试；数据库未连接、共享数据和历史密码未修改。T4 其它业务输入、服务写矩阵、并发及跨租户矩阵仍待完成；T1 固定版本 registry 消费、T3 全量页面视觉和剩余交互也未关闭。

### T4 税率与参考价边界真实 HTTP 续验

随后在同日补做隔离 HTTP 验收，使用新打包 Demo JAR、独立 schema `yuheng_t4_taxbounds_20261114`、专用 MySQL 用户、端口 48105 和原本为空的 Redis DB 12。空库由 Liquibase 首次执行 54/54 changeset，种子密码恢复 changeset 仅作用于临时 schema；登录后未更新或修改任何用户密码。

可复用探针 `scripts/verification/erp_tax_price_bounds_probe.py` 发出 19 次请求（1 次登录、18 次非法输入）：客户及供应商税率 -0.01/100.01；产品重量、采购价、销售价、最低价 -0.01；采购/销售订单、采购入库/退货、销售出库/退货的税率越界；其它入库/出库、盘点、调拨参考单价 -0.01。18 个非法请求均返回 HTTP 200 / 业务码 400，并包含对应校验提示。每次请求前后对当前 schema 所有 `erp_*` 表逐表比较行数，均未变化，确认拒绝发生在业务写入前。详细脱敏请求记录见 `erp-tax-price-bounds.json`。

关停隔离实例后精确删除本轮 schema 和 `yh_taxbounds` 用户，Redis DB 12 清理后为 0，48105 无监听；只读检查确认测试 schema/用户为 0、共享 `yuheng_demo` 仍存在。没有操作共享数据或固定版本 registry。此项现在有模板契约、Hibernate Validator、真实 HTTP/隔离 SQL 和前端构建证据；未覆盖有效 0/100 税率的完整业务创建、金额精度/舍入、其它金额、财务正负值、各角色权限和租户组合。T1/T3/T4 总体仍未关闭。

## 2026-11-14 T4-AUDIT-STATUS ERP 审核状态边界

### 发现与实现

沿用 `workId: YH-20261111-full-source-migration`，codeVersion `0.1.0-SNAPSHOT`、governanceVersion `0.2.0`、knowledgeVersion `0.1.0`。源码审计发现 12 个采购、销售、库存和财务 `update-status` Controller 都接收任意 `Integer`。各 Service 只判断 `status == 20` 为审核，所有其它数字均进入反审核逻辑，并把原始数字写入单据状态；有库存联动的单据还会按反审核方向写库存与流水。因此 `status=99` 可能同时造成非法单据状态和错误库存副作用。上游存在相同代码，但与 `ErpAuditStatus` 仅定义 10/20、前端仅发送这两个值的接口契约不符。

第一轮只在模板和 Demo 的 12 个 Controller 参数增加 `@InEnum(ErpAuditStatus.class)`，但隔离 HTTP 证明当前 Spring MVC 调用链没有触发该方法参数校验；该轮 65 项模板测试及 39 项 Demo Maven 测试不能证明运行时拦截，记录的旧 JAR 请求也不是本修复证据。根因确认后，模板和 Demo 的 12 个 Controller 均在调用 Service 前显式调用 `ErpAuditStatusValidation.validate(status)`。共享验证器通过 Core `ValidationUtils.validate` 校验非空及 `ErpAuditStatus` 枚举成员，保留参数 `@InEnum` 作为接口契约声明。Demo 同步遗漏最初导致 12 个 Controller 无法编译，新增同步契约先红后绿，验证器源码随后与模板保持一致。

### 最新验证结果（2026-11-14）

| 验收 | 证据 | 结果 |
| --- | --- | --- |
| 模板契约 | `python3 -m unittest discover -s tests -p 'test_*.py' -v`，66 项通过；覆盖全部 12 个 Controller 的显式校验调用和共享验证器的 Core 校验约束 | PASS |
| Demo 同步与编译 | 新增 `test_erp_audit_status_validator_is_present_in_demo_business_module`，先因 Demo 文件缺失失败，补入后通过；`mvn -o -Dexec.skip=true test`，39 项通过，401 个业务类及 bootstrap 编译成功 | PASS |
| 可执行制品 | `mvn -o -Dexec.skip=true -DskipTests package` 成功；Boot JAR 恰含一个 `yuheng-demo-business-0.1.0-SNAPSHOT.jar`，内嵌业务 JAR 可见 `ErpAuditStatusValidation.class`；SHA-256 `eccd2caf2a81ed75411e3a5c38838f0f1c621b46100a076637fb8d9ca9beb2d4` | PASS |
| 隔离 HTTP 与数据库副作用 | `erp-audit-status-runtime.json`：新 Boot JAR 在专用 schema `yuheng_t4_status_20261114`、端口 48106 运行；12 个端点的 `status=99` 均返回 HTTP 200 / 业务码 400。每次请求后对全部 `erp_*` 表做逐行快照比较，均完全不变；请求共 13 次（含登录） | PASS |
| 合法状态流程 | 本轮新建的 status 专用隔离 schema 未覆盖 10/20 成功路径；同 workId 既有 `erp-workflows.json` 在真实隔离库中以合法 20 审核采购订单、采购入库、销售订单、销售出库、付款和收款，并对付款/收款执行 10 反审核及 20 再审核，库存/资金联动断言通过。该证据覆盖代表性现有流程，不覆盖其余六类单据各自完整的 10/20 成功组合 | PASS（代表性覆盖） |

隔离 HTTP 前探针因未注入临时管理员环境变量在登录前退出，没有业务请求；随后从本机临时 secret 文件仅向探针进程注入环境后成功。服务退出后先将临时 schema 管理员哈希恢复为初始化值并确认相等，再删除 schema 与专用 DB 用户，清理 Redis DB 4；最终 schema/用户计数均为 0、Redis DB 4 为 0、端口无监听，共享 `yuheng_demo` 仍存在。没有更改共享库或历史用户密码。

因此非法状态输入拦截及其无副作用现已由隔离真实 HTTP/MySQL 验证；模板和 Demo 同步、编译及测试也完成。合法状态已有代表性业务工作流证据，但没有逐一覆盖 12 类单据的 10/20 所有转换组合。T4 的其它权限/租户/事务覆盖以及 T1/T3 仍开放，整个全源码迁移未完成。

### 历史首轮记录

首轮确实因没有注入隔离管理员环境变量而未能运行 HTTP 探针；当时共享服务 lifecycle 配置也没有可复用的专用 schema。该状态已由上面的 2026-11-14 最新隔离验收取代。首轮及旧 JAR 请求保留作历史审计，不作为当前修复证据；整体迁移仍因 T1、T3 和 T4 其它开放项而未完成。

### 2026-11-14 T3 定时任务与执行日志同库对照

使用隔离 schema `yuheng_t3_job_20261114`、专用用户 `yh_t3_job`、后端端口 48113、Demo UI 5174、原版 UI 5181 和 Redis DB 3。Quartz 自动启动已关闭，只进行页面读取；未运行、同步、启停、编辑、删除、导出任务，也未写入业务数据。

- `/infra/job` 两版均显示 33 条任务、每页 10 条、共 4 页；任务名称/状态/处理器名筛选项、搜索/重置/新增/批量删除/导出/执行日志/同步任务入口、7 个表格列及首屏 10 条任务字段逐项一致。
- 两版首屏相同记录 `12909` 的名称均显示为 `EAM 周期保养è®¡åˆ’`，为相同的既有数据乱码，不是 Demo 迁移差异。
- 只打开“执行日志”入口后，两版均导航至 `/job/job-log`。筛选项（处理器名、开始/结束执行时间、任务状态）、搜索/重置/导出入口、8 个表格列及“暂无数据”空状态一致。隔离库未产生调度记录，因此详情内容未覆盖；未导出日志。
- 浏览器加载和两页查询请求均成功；原版 Vite 有既有 Vue Router `next()` 弃用 warning，Demo 页无页面级异常。对照以同一隔离后端、并列页面可见文本和运行数据为证。

完成后后端以 Spring graceful shutdown 退出，Demo 代理与原版 Vite 停止。精确删除隔离 schema 与专用用户；只清空原先专用 Redis DB 3，最终 `DBSIZE=0`。复核 `yuheng_demo` 仍存在、隔离 schema/账号均不存在，48113/5174/5181 无监听；现有 5173 仍由 PID 39370 监听且 HTTP 200，未停止或重启。未操作共享库及历史用户密码。

该轮关闭 T3 的定时任务列表和空执行日志页成对核验。T3 仍缺其余 System/Infra 页面、非空日志详情、主要写工作流和全局样式/响应式的系统覆盖；T1 版本化 registry 包消费仍受固定版本 404 阻塞，T4 全量权限/租户/事务审计仍未穷尽，完整迁移计划继续开放。

### 2026-11-14 T3 字典/岗位续验受隔离登录态阻塞

准备独立 schema `yuheng_t3_sysref_20261114`、专用账号 `yh_t3_sysref`、后端 48114、Demo 静态代理 5174、原版源码 Vite 5182 和 Redis DB 3。空库 Liquibase 54/54 changeset 成功；原版 Vite 直接使用现有 `node_modules/.bin/vite` 启动，避免 pnpm workspace 自动安装。显式用 pnpm 启动时再次遇到固定版 `yuheng-ui` registry 404，未更新依赖或锁文件。

原版 Chrome 标签原先保留着到隔离后端的有效登录态，可只读看到 `/system/dict`：385 条、10 条/页、39 页；筛选项为字典名称/类型、状态、创建时间，表格列为编号、名称、类型、状态、备注、创建时间、操作。该页面是原版既有会话中的单侧观察，不能充当同会话下的 Demo 对照。新建的 Demo IAB 标签没有登录态；其隔离账号登录返回“账号密码不正确”。未猜测口令、重置或修改用户密码，也未尝试复制跨站令牌。岗位页因此没有进入，字典和岗位都不能记为完成成对验收。

收到阻塞后以 TERM 关闭隔离后端，Spring graceful shutdown 完成；5174 代理与 5182 Vite 均已停止。精确删除本轮 schema 与专用账号，Redis DB 3 清空后为 0；验证隔离 schema/用户均不存在、共享 `yuheng_demo` 仍存在，48114/5174/5182 无监听，现有 5173 PID 39370 未停止。没有对共享库、历史密码或业务数据执行修改。

状态：本轮没有关闭 T3 的字典/岗位成对验收。后续需在隔离环境取得受控且有效的两端登录会话，再继续该组只读列表和取消式表单对照；整体迁移仍因 T1 registry 消费、T3 页面覆盖和 T4 全量后端矩阵未完成而保持开放。

### 2026-11-14 T4 Core System/Infra 事务与外部副作用静态续审

重读 Core 当前工作树的 System/Infra ServiceImpl 源码，对 51 个实现中 16 个声明 `@Transactional` 或 `@DSTransactional` 的实现作定位，并按调用链核对用户、租户、角色权限、代码生成、文件和定时任务等代表性写入。确认租户创建/修改、租户套餐菜单同步、用户记录及岗位/角色关联、用户删除后的权限及岗位关联、菜单删除权限清理、代码生成表列配置、文件主存储切换和 Quartz 任务 DB 配置变更均有数据库事务声明；单表岗位/字典/公告/配置/部门写路径没有因此判定为缺陷。扫描的 51/16 是源码文件层级计数，不是全部方法审计完成数。

识别出以下需要独立评估的一致性边界，均未作运行故障注入，也未更改 Core/Demo 实现：

- `FileServiceImpl.createFile(byte[], ...)` 先写对象存储再插入文件元数据。若 DB 插入失败，对象可能成为孤儿；单据库事务不能撤销对象存储写入。
- `FileServiceImpl.deleteFile` 和批量删除先删对象再删数据库记录；批量过程中外部存储失败可能已删除前面的对象而 DB 记录尚未批量删除，后续重试可能遇到对象缺失。接口当前不声明数据库事务，也不能以普通事务获得对象存储原子性。
- `JobServiceImpl` 对创建、更新、启停和删除同时操作业务 DB 与 Quartz；方法有数据库事务，但 Quartz 是另一资源，若 Quartz 操作成功后数据库提交失败或反向次序失败，恢复行为要靠 Quartz 持久化/调度同步机制确认，本轮没有注入异常验证。
- `AdminUserServiceImpl.updateUser` 在数据库事务方法内发布 Spring `AdminUserProfileUpdateMessage`。Producer 通过 `ApplicationContext.publishEvent` 同步发布；Core System 源码扫描未找到此消息的 `@TransactionalEventListener(AFTER_COMMIT)` 消费者。尚未确认其它可选模块的监听及实际异步配置，因此列为待核查的事件时序边界，不直接定为缺陷。

该静态续审记录在计划 T4 台账。文件存储与 Quartz 外部一致性、用户资料事件监听需后续确认恢复/幂等策略并做隔离故障注入；仍缺全部目标 Service 写方法矩阵、所有跨租户 mapper 查询复核和系统性异常回滚验证，T4 继续开放。T1 固定版本包消费及 T3 全量页面验收同样未完成。

### 2026-11-14 T1 Core UI 当前制品包外消费

使用当前 Core UI 工作树打包的 `yuheng-ui-0.1.0-SNAPSHOT.tgz`（SHA-256 `0c9cd4c27af38d51b0b0e381a3797bc42b0c3ca4fa96311ee8bcdd55715c27a3`），在 Core 源码目录之外的临时消费者 `/tmp/yuheng-ui-consumer-current.CSVU3S/consumer` 安装并验证。`node_modules/yuheng-ui` 的真实解析路径位于该临时消费者自己的 `.pnpm` 包目录，包导出指向已打包的 `dist/index.js` 和 `dist/index.d.ts`，没有解析到 `yuheng-core/yuheng-ui` 源码。

包外初验发现 Demo manifest 漏声明四个直接运行依赖：`@iconify/json`、`@iconify/vue`、`echarts`、`lodash-es`。增加依赖后，独立生产构建可处理 3548 个模块并成功完成。包外 TypeScript 检查随后发现 `lodash-es` 还需 `@types/lodash-es`；Demo manifest 已增加 `^4.17.12`，`consumer-entry.test.ts` 增加直接类型依赖契约。最终临时消费者验证：Vitest 2 个文件、11 项通过；`vue-tsc --noEmit` 退出码 0；平台导入边界脚本通过；Vite production build 成功。Vite 输出既有大 chunk 警告，未影响构建。

根 workspace 的私有 npm mirror 对 `yuheng-ui@0.1.0-SNAPSHOT` 返回 404。尝试更新 Demo 依赖时 pnpm 在该缺失制品解析处中止，未能更新正式 workspace lockfile；本轮也没有将临时 tarball 地址写入正式 manifest/lockfile。故本记录证明的是当前源码 tarball 的 workspace 外包消费能力，不证明 registry 固定版本安装成功。registry 制品可用后仍需干净安装和版本发布验收，T1 保持未完成。全量迁移的 T3 页面/交互覆盖与 T4 权限、租户、事务审计仍未完成。

验证边界补充：工作区 pnpm 在 registry 404 前将若干既有 `node_modules` 直连目录移至 `yuheng-demo-ui/node_modules/.ignored`，未删除这些目录；由于安装命令中止，Demo 工作区内 pnpm 测试不能运行。正式代码验证以独立临时消费者的上述完整结果为准。本轮结束时未尝试恢复/删除 `.ignored` 内容，以保留 pnpm 自动保护的既有依赖数据。

### 2026-11-15 T1 当前 Core tarball 包外消费复验

从当前 Core `yuheng-ui` 工作树重新生成 `/tmp/yuheng-ui-0.1.0-SNAPSHOT.tgz`：SHA-256 `d92f0f81da2848b34b40ec27755ae37a55b04e961cc8460121c79f29980d900a`，655 个文件，包元数据为 `yuheng-ui@0.1.0-SNAPSHOT`，包含 `dist/index.js`、`dist/index.d.ts`、`dist/styles.css` 和 compat 资源。没有覆盖 Core 仓库中既有 vendor tarball。

在 `/tmp/yuheng-ui-consumer-current.CSVU3S/consumer` 保留 Demo UI 当前源码和已有依赖，临时将该目录 manifest 指向刚生成的 tarball 并离线安装；安装后的解析路径是消费者自身 `.pnpm/yuheng-ui@file+...tgz.../node_modules/yuheng-ui`，不是 Core 源码符号链接。恢复临时副本 manifest 的固定版本字符串后，以本地二进制执行验证：Vitest 2 个文件/11 项通过、`vue-tsc --noEmit` 通过、平台导入边界通过、Vite 生产构建 3548 模块成功。构建保留既有多个大 chunk 警告。

本次证明当前 tarball 在 workspace 外可被消费，不证明 npm registry 固定版本可解析。私有 registry 仍未提供 `yuheng-ui@0.1.0-SNAPSHOT`；未尝试发布或再次查询 registry，正式 Demo manifest/lockfile 未修改。T1 仍开放；T3/T4 全范围也未完成。

### 2026-11-14 T3/T4 Demo 直跑与 ERP 模板消费端源码对照

沿用 `YH-20261111-full-source-migration`，当前消费端 manifest 为 `yuheng-manifest.yaml`：codeVersion `0.1.0-SNAPSHOT`、governanceVersion `0.2.0`、knowledgeVersion `0.1.0`。由于 pnpm 在运行测试前会自动 install 并因固定版 `yuheng-ui@0.1.0-SNAPSHOT` registry 404 中止，本轮通过现存 `node_modules/.bin` 直接执行等价工具，没有再次调用 pnpm。

| 检查 | 命令/方法 | 结果 |
| --- | --- | --- |
| Demo UI 单测 | `./node_modules/.bin/vitest run`（目录 `yuheng-demo/yuheng-demo-ui`） | 2 个文件、11 项通过，退出码 0 |
| Demo UI 类型检查 | `./node_modules/.bin/vue-tsc --noEmit` | 退出码 0 |
| Core/Demo 平台导入边界 | `node scripts/check-platform-imports.mjs` | PASS |
| Demo UI 生产构建 | `./node_modules/.bin/vite build` | 成功；存在既有大 chunk 警告 |

使用 Python 只读逐文件对照 Demo `yuheng-demo-business` 与 `yuheng-business-templates/template-erp`，仅把消费包名 `com.yuheng.demo.module.erp` 规范化为模板包名后比较正文：33/33 DataObject、47/47 Service、88/88 Controller 与模板完全一致；Demo 的 `package-info.java` 为项目包装文件，不纳入业务源码比较。Demo 与模板两份统计 Mapper XML 内容完全一致。三份 ERP Liquibase SQL 的两边 SHA-256 分别为：`001-erp-schema.sql` `3eb5c0e2111ee393900e14051fc17106c3b623c4a984349ea1f0681dd6a2c368`、`002-erp-identifier-width.sql` `c310693d0d53cbff0cb9664d4430e0d704e3de438b2c390657572c0f6997a642`、`003-erp-stock-active-uniqueness.sql` `068b4f16a1e020fb81e96ec7c02a1c9cea1693807271bb58ad959cd5358497f5`，逐项相同。

前端模板路径对照：63/63 ERP 页面有同名模板；56 个正文完全一致，7 个差异仅在事件行参数补充 `number`/`any` TypeScript 类型，未改业务分支。23/23 API 文件有对应模板，差异仅是将模板 `@/config/axios` 改为消费端公开的 `yuheng-ui/compat/config/axios`。以上是源码迁移一致性证据，不外推运行期全量工作流、权限或租户矩阵。

#### 当前运行实例的登录限制

浏览器只读打开 `http://127.0.0.1:5173/login?redirect=/system/user`，租户和用户名预填正确；使用已有本地验收文档中的测试凭据尝试一次登录后仍停留在登录页，没有进入用户页面。本轮浏览器没有提交任何业务写操作。`logs/lifecycle/backend.log` 的当前末尾记录 `NoClassDefFoundError: ch.qos.logback.classic.spi.ThrowableProxy`，且 `/admin-api/system/tenant/get-by-website` 曾处理约 60 秒；这说明现运行旧实例不适合作为当前代码行为验证，不能据此断言 Demo 登录逻辑回归。没有重启 PID 23945（后端）或 PID 39370（5173 UI），没有执行 SQL 或改共享数据库/历史密码。T3 登录后页面、整体视觉和剩余交互仍 BLOCKED，待以可确认制品和安全隔离运行实例补验。

Demo 后端另执行 `mvn -o -Dexec.skip=true test`（Demo 根目录），Maven reactor 成功，bootstrap 后端测试 39/39 通过，业务模块与 bootstrap 编译均成功。`-Dexec.skip=true` 跳过会调用 pnpm 的前端 Maven exec，Maven 资源阶段复制了本轮已构建的 UI dist 到 `target/classes/static`；该命令没有启动 JAR、连接数据库或触碰运行中 PID 23945。模板库同时执行 `python3 -m unittest discover -s tests -p 'test_*.py' -v`，66/66 通过。两项均是本轮新鲜结果，不代表隔离 HTTP 全量权限/租户矩阵已完成。

## 2026-11-14 T4 构建生命周期保护与运行配置续审

### 构建时保护运行中的 Boot JAR

只读进程检查确认 PID `23945` 是监听 `48080` 的 Java 进程，`lsof -p 23945` 显示它打开 `yuheng-demo-server-bootstrap/target/yuheng-demo.jar.original`。运行目录中正式 `yuheng-demo.jar` 的修改时间为 `2026-11-14 17:26:48`，SHA-256 为 `eccd2caf2a81ed75411e3a5c38838f0f1c621b46100a076637fb8d9ca9beb2d4`。既有生命周期日志曾记录 Logback、Spring Boot、Tomcat、Reactor、Redisson、dynamic-datasource 等多个嵌套依赖 `NoClassDefFoundError`。Boot JAR manifest 指向 `JarLauncher` 且有 `BOOT-INF/classpath.idx`；`.jar.original` 是 Maven 未 repackage 的薄包。证据与 Spring Boot Maven repackage 的原路径改名行为相符：构建会把输入 JAR 移至 `.jar.original` 并写入新包，已运行的 JarLauncher 后续仍需按原路径读取嵌套依赖，因此原包被替换/删除后出现类缺失。该证据确认脚本缺少保护且机制与异常一致；没有在故障进程上做破坏性重现，也未停止或重启该进程。

在 `scripts/tests/test_backend_modules.py` 新增 TDD 回归：先运行看到运行中场景失败（脚本仍调用 Maven，退出码 0），空闲场景通过；随后 `scripts/build.sh` 增加对正式 JAR 和 `.jar.original` 的 `lsof` 占用检查。最终 `python3 -m unittest scripts.tests.test_backend_modules -v` 为 10 项通过；构建被占用时拒绝调用 Maven，未占用时继续。`python3 -m unittest scripts.tests.test_lifecycle -v` 为 5 项通过；`bash -n scripts/build.sh scripts/start.sh scripts/stop.sh` 与 `git diff --check` 通过。首次绿灯检查的提示文字断言与实际中文提示不一致，修正测试断言后重跑专项测试通过；产品检查逻辑未因该文字断言调整。

### 配置与装配对照

以 `/Users/huhua/study/ai/yuheng/ruoyi-vue-pro/yudao-server/src/main/resources/` 为上游、Demo `yuheng-demo-server-bootstrap/src/main/resources/` 为迁移端，逐项查看三份 YAML、Logback 和 bootstrap POM。`application-local.yaml` 对数据库/Redis 默认值、包名日志级别有明确的 Yuheng 项目适配；`application-dev.yaml` 改为必填 `YUHENG_DB_NAME/USERNAME/PASSWORD`，不使用上游硬编码数据库口令。Demo 主配置将 Flowable schema update 设为 false，Quartz JDBC schema init 设为 `NEVER`，并通过 `spring.liquibase.change-log` 纳入受控 changelog；与 Core BPM/Quartz 单独迁移脚本归属一致。bootstrap POM 在 Maven `generate-resources` 调用 UI 构建，并聚合 Demo business 与 Core server 能力。此次范围检查未发现新的配置遗漏，但不外推为所有 profile 和外部集成均已运行验收。

运行前后端当前状态未更改：PID `23945` 仍监听 `48080`，PID `39370` 仍监听 `5173`；本轮没有发送停止信号、重启、登录、数据库连接或业务写请求。构建保护不会修复这个已运行旧进程，也没有用新包替换其文件。下一步需确认 PID 23945 的实际数据源后有序停止，再用最新 `scripts/build.sh`/`scripts/start.sh` 启动，并完成登录、核心 API 与原版同视口页面验收；在此之前 T3 运行验收仍 BLOCKED。T1 固定版 UI registry 404 和 T4 全量 Service/权限/租户/事务异常注入矩阵仍开放。

### 隔离运行尝试与环境保护

Docker `mysql8` 与 Redis 均为 healthy。只读查询确认共享 `yuheng_demo` 有 54 条 `DATABASECHANGELOG`、150 张表和 1 个非空 `admin` 种子。用户提供的 MySQL `yuheng` 账号只被授权访问既有 schema，不能创建隔离库；容器内 root 管理账号可用。新建空 schema `yuheng_t3_runtime_20261114_a`，仅给 `yuheng` 授权，Redis DB 13 初始 `DBSIZE=0`。

启动 48115 隔离实例时，启动 shell 实际没有留下本轮 Java 子进程，日志文件为空，schema 中没有 `DATABASECHANGELOG` 或业务表；等待健康接口只得到 connection refused。随后 `pgrep` 发现两个此前未纳入状态清单的 Java 验证实例 PID `88324`/`88411`，分别监听 `48099`/`48100`，其命令使用 Demo JAR、local profile 与 Redis DB 11/10。本轮未停止或探测这两个实例，也未再次启动，避免与其它验证工作冲突。仅删除本轮刚建的空 schema 和其专用授权；验证 schema 数量 0、授权数量 0、Redis DB 13 仍为 0。共享库、历史密码以及 PID `23945`/`39370` 均未变更。

结论：未取得本轮运行期证据。下一次运行验收前需先确认 PID `88324`/`88411` 的所属任务或等待端口释放，然后用新端口、全新 schema 和开始为空的 Redis DB 再启动；T3 保持 BLOCKED。

### T3 隔离运行续验成功

对两个额外实例的只读归属核对显示，PID `88324`/`88411` 是当前 Codex app-server `26466` 子进程，各自 health 与 OpenAPI 为 200，MySQL connection 使用 `yuheng_t4_atomic_20261114` 及 `_retry`，Redis DB 为 11/10；它们不属于本轮 T3，因此保持运行不动。

随后启动当前 JAR（SHA-256 `eccd2caf2a81ed75411e3a5c38838f0f1c621b46100a076637fb8d9ca9beb2d4`）于端口 48116，明确配置新 schema `yuheng_t3_runtime_20261114_b`、MySQL 用户 `yuheng`、Redis DB 9、关闭 Quartz 自动启动。首次 Liquibase 执行 54/54 changesets 成功，日志显示 Rows affected 6702。HTTP：管理员登录与 `/system/auth/get-permission-info` 均返回 HTTP 200/业务码 0，权限响应含 24 个顶层菜单组；health URL 被全局认证保护而返回业务码 401，因此不把该路由称为匿名健康通过。

使用真实浏览器在 `http://127.0.0.1:48116/` 登录后检查：首页显示授权模块 21、可访问入口 506；System 用户页 15 条、岗位页 4 条；Infra 配置页 28 条；ERP 产品信息页显示正确筛选项、表头和空数据。系统管理、基础设施、ERP 菜单均可展开，路由分别到 `/system/user`、`/system/post`、`/infra/config`、`/erp/product/product`。DevTools browser logs 返回空数组；没有提交新增、修改、删除、导出等写操作。

数据库只读检查：54 个 changesets、150 张表、admin 密码字段非空；`system_operate_log.success` 不存在；`erp_product` 与 `member_user` 均为空。结束时本轮 PID 27811 收到 TERM，Tomcat graceful shutdown 完成，Druid datasource 均正常关闭。精确删除 `yuheng_t3_runtime_20261114_b` 与对应 schema 授权，Redis DB 9 清理后为 0；验证临时 schema/grant 计数 0、共享 `yuheng_demo` 仍存在、48116 无监听。未变更用户密码或共享数据，PID `23945`/`39370`/`88324`/`88411` 均未停止。

本轮关闭 T3 的隔离登录、首页、System 用户/岗位、Infra 配置及 ERP 产品页运行验收子项。T3 总项仍未完成：其它 System/Infra/ERP 页面、主要写交互、原版同尺寸对照、响应式覆盖、完整 network/console 审查尚未全部验收；T1 registry 固定版本和 T4 全量后端矩阵也继续开放。

### 2026-11-14 T3 基础设施页面续验

在隔离 JAR `eccd2caf2a81ed75411e3a5c38838f0f1c621b46100a076637fb8d9ca9beb2d4`、schema `yuheng_t3_infra_followup_20261114`、后端 48118、Demo UI 5174、原版 Vite 5183 和 Redis DB 15 上继续检查。通过 Demo 已认证会话逐页打开代码生成、数据源配置、表单构建和 API 接口：代码生成列表可加载，空库显示“暂无数据”；数据源配置显示当前 master 连接（该连接字符串属于隔离 schema）；表单构建器显示基础、子表单、辅助、布局和系统字段组件及表单配置；API 接口内嵌 Swagger UI 成功载入 `all` 定义、Yuheng 管理平台 OpenAPI 3.1 标题及各分组接口。只读观察，没有导入/删除代码生成表、增删数据源、生成或清空表单，也没有在 Swagger 执行业务请求。

只读核对确认隔离库基线中 `infra_codegen_table=0`、`infra_data_source_config=0`、API 访问/错误日志均为 0；系统公告 3 条、通知消息 95 条、文件配置 11 条、登录日志 1 条。代码生成、数据源以及空日志列表因此只能记录空状态，不代表导入、编辑、详情或真实数据行流程已验收。原版标签此时已显示“登录超时，请重新登录”，没有重试登录或修改凭据，所以本轮无法完成原版逐屏比较。Demo 前端 console 日志接口未能成功读取，本轮不把 Console/Network 检查记为通过；此前 CSS preload 提示也未完成持续复现判断。

清理时仅向 TERM 发送给本轮记录的 PID 32753（隔离后端）、32805（Demo UI 代理）和 32881（原版 Vite），确认三者均已退出且 48118/5174/5183 无监听。容器 root 环境变量授权的管理命令精确删除本轮 schema 并确认 schema/grant 均为 0；仅清空开始前为空的 Redis DB 15，最终 `DBSIZE=0`。复核共享 `yuheng_demo` 仍存在；共享 UI PID 39370、旧后端 PID 23945 和其它验证实例未停止，历史用户密码未改。

**状态**：本轮只关闭代码生成、数据源、表单构建器和 Swagger 页面的 Demo 只读加载观察。原版成对比较、系统管理其它页面、Infra 文件/监控/WebSocket 页面、非空日志详情、表单与主要写交互、完整 Console/Network 及响应式覆盖仍未完成；T3 不关闭。T1 固定版本 registry 消费和 T4 全量后端权限/租户/事务矩阵仍开放。

### 2026-11-14 T3 浏览器白屏恢复续验

沿用 `YH-20261111-full-source-migration`、已确认的完整前后端迁移授权及只读浏览器验收范围。隔离 JAR SHA-256 `eccd2caf2a81ed75411e3a5c38838f0f1c621b46100a076637fb8d9ca9beb2d4` 运行于端口 48119，专用 schema `yuheng_t3_more_20261114`，Redis DB 6（启动前确认 0）；Demo 静态 UI 5174，原版 Vite 5183。

- 初始白屏复现于两端 `/`。Demo HTML 与 JS/CSS 资源都返回 200，浏览器 `#app` 为空且没有可读 Console 错误。Demo UI 直接打开白名单 `/login` 后表单及完整样式立即渲染；使用已记录隔离验收账号 `admin/admin123` 登录成功，首页显示授权模块 21、可访问入口 506、已加载字典 388，System/Infra 和其它模块菜单均可见，Console warn/error 为空。没有执行任何业务写操作。
- 根路径白屏与未登录状态下启动导航守卫调用 `fetchUserInfo` 的流程吻合：core UI `installYuhengUi` 会在受保护的首页路由初始化用户权限，未认证调用返回 401 并使 `router.isReady()` reject，Demo `main.ts` 随后不会运行 `app.mount('#app')`。本轮证据能复现“/ 白屏、/login 正常、登录后首页正常”，但未提取隔离账号 access token 后再次匿名复测，因此不能把上述调用链推断写成已完成的最终根因证明，也没有修改 Core 行为。
- 原版 Vite 页面从 `/` 白屏；切至 `/login` 仍无法挂载。原版 5183 的 `/admin-api/system/auth/get-permission-info` 在浏览器/HTTP 请求中超过 30 秒，控制台记录 Axios timeout 与 Vue Router 启动失败；该原版对照服务不可用，未把它计作页面差异或迁移回归。本轮没有进行两端登录后同页面对照，因此没有关闭新增页面验收子项。
- 安全收尾：仅停止本轮 PID 35441/35473/35522；48119/5174/5183 均无监听。隔离 schema 删除，Redis DB 6 清理后为 0。清理时发现 MySQL 账号 `yuheng` 同时是共享 `yuheng_demo` 连接账号，已按原凭据恢复账号及仅 `yuheng_demo` 的授权，并用该账号验证共享 schema 仍有 54 条 changelog、150 张表、21 个用户；`yuheng_demo` 数据未做写操作。共享前后端 PID 23945/39370 保留，5173 仍返回 HTTP 200，未改历史用户密码。

**状态**：本轮确认 Demo 直达登录及登录后首页可用，初始 `/` 白屏仍需修复或以明确的登录入口规避并建立回归证据；原版同页面对照被原版 5183 请求超时阻塞。没有关闭 T3。下一轮应先让原版服务在隔离后端可成功响应，再使用同一数据、登录态和视口继续 system/infra 页面、样式、交互及 Console/Network 对照。T1 固定版本 registry 消费和 T4 全量后端权限/租户/事务矩阵仍未完成。
## 2026-11-15 T3 登录日志隔离续验（后续浏览器证据已补）

沿用 `YH-20261111-full-source-migration` 和 T3 页面核验范围。重建隔离 schema `yuheng_t3_loginlog_20261115`，专用 MySQL 用户 `yh_t3_loginlog15` 仅获该 schema 权限；后端端口 48124、Demo UI 5179、原版 Vite 5186，三者均只连接本轮隔离后端。空库初始化为 54/54 Liquibase changesets、150 张表，21 个种子用户 password 字段均非空。Redis DB 12 启动前为 0。

经 Demo 静态代理执行一次临时管理员登录，Core 返回业务码 0，隔离库生成成功登录记录；随后权限接口包含 `system:login-log:query`，登录日志分页接口返回业务码 0、total=1、list=1。表字段核对使用 `result`（本轮探针首次误将其称作 `log_status`，该只读查询失败后按实际 DDL 更正；没有数据库写入）。完成读取后，隔离 `system_login_log` 中有两条成功登录记录，均由本轮验收请求产生。

本节最初记录的浏览器操作失败反映了当时控制状态，不是本轮最终结果。随后浏览器控制恢复：Demo 真实标签能显示 4 条登录日志，筛选 `not-a-user` 后两端均为空，重置后均恢复 4 条；同选记录 7944 打开的详情字段和值相同。页面对应的详情字段和值相同。最终修复构建加载后、隔离后端仍运行期间未见浏览器 error；停止隔离 UI/后端后，通知未读数的定时轮询出现两条预期 `AxiosError: Network Error`，此为服务关闭后的浏览器记录，不归为运行期页面错误。页面顶部和表格的真实 DOM、截图已保存；旧的“未取得 DOM/截图”结论由这些后续证据更正。`/actuator/health` 返回 404，仍不作为健康证据。

同一标签、同一后端与隔离数据，在确认实际 CSS viewport 为 390×844 后，先后直达 Demo 和原版登录日志页面。两端均显示同样的筛选字段、操作入口、表格列和 4 条记录；documentElement 的 viewport 与 scrollWidth 均为 390，未见整页横向溢出。响应式截图分别保存为 `loginlog-session-20261115/demo-mobile.png` 与 `loginlog-session-20261115/original-mobile.png`。此前单独记录的白屏图 `demo-empty.png` 是发生于首次未认证受保护路由的瞬时观察，不能作为移动布局失败证据；导航完成后 Demo `#app` 已有布局和页面节点、日志请求成功，刷新/再次直达正常。按实证将状态限定为“首次标签启动时有短暂空白观察，尚未稳定复现、无异常 Console 根因”，不以推测新增修复。

收尾顺序为停止 Demo UI PID 59146、原版 Vite PID 59147、隔离后端 PID 59145，确认三进程退出后，精确删除本轮 schema `yuheng_t3_loginlog_20261115` 和专用账号 `yh_t3_loginlog15`；最终 schema=0、用户=0、共享 `yuheng_demo` 仍存在。Redis DB 12 启动前为 0，本轮运行后为 10 keys，清理后为 0；48124/5179/5186 均无监听。未改共享库、历史密码或其它 Redis DB。桌面登录日志、筛选/重置、详情和 390×844 成对布局子项完成；T1 固定版 registry 消费、T3 其余页面/交互、T4 全量权限/租户/事务矩阵继续开放。

### 2026-11-15 Core 默认 UI 会话续期修复及真实页面续验

根因定位于 Core `createYuhengUiContext()` 创建默认 `createYuhengRequest()` 时没有提供 `refreshToken` 回调。底层请求层虽已具备过期后刷新和原请求重放逻辑，但默认 runtime 未接入平台端点，因而遇到 401 时失败并清除会话，已显示的数据不会被成功查询替换。Core `yuheng-ui/src/runtime/options.ts` 现使用同一请求实例 POST `/system/auth/refresh-token`，以 `refreshToken` query 参数传递当前刷新令牌，再返回新 token pair 给请求层；请求 override/注入和错误清理契约保持不变。

新增 `yuheng-ui/tests/runtime/options.test.ts` 使用真实本地 HTTP server，覆盖刷新 endpoint 的方法、URL 编码、tenant header、无旧 access Authorization、令牌保存、原查询重放、并发刷新合并及失败时清理/回调一次。修复前测试以 `YuhengApiError: Refresh failed` 失败；修复后通过。Core UI 全套 26 个文件/113 项通过；`vue-tsc --noEmit`、平台导入边界、Vite production build 与声明构建通过。Demo UI 2 个文件/11 项通过，类型检查、平台导入边界和 Vite production build 通过。Build 保留原有 chunk 警告；没有运行 Maven 或替换被其它进程使用的 JAR。

用此版本 Demo dist 经隔离 UI 5179 和后端 48124 实测：使本轮新管理员访问 token 在隔离 schema 中过期后点击重置，浏览器成功 POST 刷新端点并重放登录日志查询，列表恢复为 4 条；数据库显示旧 token 已过期并生成新 token。请求证据存放于 `loginlog-session-20261115`，敏感刷新参数已从整理后的记录中去除；没有打印或归档 token 值。Console 从最终修复构建加载后未发现 error。该验证关闭 Core 默认 runtime 令牌刷新和 Demo 登录日志会话续期子项，不代替所有页面/租户权限工作流验收。

### 2026-11-15 登录日志直达与短暂启动状态复核

原 Demo 标签跨标签共享已登录会话，仍可显示登录日志页面；新标签首次直达受保护路径时，本轮观察到 `#app` 暂时为空，但后续路由恢复/再次直达已实际加载布局、4 条数据和页面组件。随后同标签从 `/login` 和登录日志路径往返，并以 390×844 对 Demo/原版逐一核对，未稳定重现持续白屏，浏览器 error 日志为空。该时间序列不支持“Core 令牌刷新缺失导致直达白屏”的推断，也不支持另一个已修复顶层 `router.isReady()` 故障就是本次空白的唯一原因；记录为短暂启动状态待持续监控，不添加猜测性改动。首个现象截图保留作诊断证据，不作为失败布局快照。

## 2026-11-15 T3 System/Infra 页面隔离续验

使用当前已构建 Demo JAR（SHA-256 `4bc65f4f34047dcdb44e6cf7d5bd989dd0412ea3063d6db469fb27bc6294767e`）的临时副本运行于 48125，连接全新隔离 schema `yuheng_t3_pages_20261115`；Redis 使用 DB 13，启动前确认 0 keys。Liquibase 首轮执行 54/54 changeset；只读核对 21 个种子用户密码字段均非空。Demo 静态 UI 5187 和原版源码 Vite 5188 均代理至该隔离后端。原版 Vite 首次沿用默认 48080 时曾点击登录，请求共享后端超时；没有成功业务写入证据。发现后停止并以 `VITE_BACKEND_ORIGIN=http://127.0.0.1:48125` 重启，后续登录及页面证据来自隔离后端。两端随后以同一隔离账号登录成功。

| 页面/交互 | Demo | 原版 | 结果 |
| --- | --- | --- | --- |
| `/system/user` | 15 条；同筛选字段、表头、分页及行操作 | 15 条；与 Demo 行数据相同 | 桌面对照通过 |
| 用户名称 `not-a-user` 搜索、重置 | 搜索空状态；重置回 15 条 | 搜索空状态；重置回 15 条 | 通过 |
| `/system/tenant/list` | 相同 3 个租户记录，含 121、122、1 | 相同 3 条及字段值 | 桌面对照通过 |
| `/system/tenant/package` | 相同套餐 113、111，共 2 条 | 相同 2 条及字段值 | 桌面对照通过 |
| `/infra/log/api-error-log` | 筛选、搜索/重置/导出、10 列及空状态 | 相同筛选、操作、10 列及空状态 | 桌面对照通过 |

用户页两端同视口截图保存在 `loginlog-session-20261115/demo-user-desktop.png` 与 `original-user-desktop.png`。本轮批量尝试其余菜单路由时，导航 API 返回后页面主体仍可能只有应用壳；后续实际等待桌面页面组件/表格挂载后即可读取，因此批量循环里提前读取的空 body 不可作为白屏或页面等价证据。本轮不把角色、菜单、部门、岗位、字典、通知、操作日志、配置、文件、任务及访问日志页面的批量尝试记为通过；已有先前同 workId 的逐页证据仍按各自范围有效。本轮无业务写入、没有提交任何 UI 表单。

清理顺序：停止 PID 62821（Demo UI）、62947（原版 Vite）、62439（隔离 Java），并确认端口 5187/5188/48125 已无监听；删除且只删除 `yuheng_t3_pages_20261115` schema；DROP schema 后其授权仍有 18 条，并非自动清除；随后显式 REVOKE 本轮 schema 权限，复核 schema/grant 为 0、共享 schema `yuheng_demo` 仍存在、MySQL 共享账号 `yuheng` 仍存在。仅清理启动前为空的 Redis DB 13（运行后 41 keys），最终为 0。历史用户密码和其他 Redis DB 未修改。T3 其它页面、写交互、完整网络/控制台与系统级响应式验收继续开放。


## 2026-11-15 T3 剩余系统页面成对验收及种子编码修复

沿用 `YH-20261111-full-source-migration` 和既有迁移授权。隔离环境为 schema `yuheng_t3_remaining_20261115`、后端 48126、Demo 静态代理 5189、原版 Vite 5190、Redis DB 14；JAR 副本 SHA-256 `4bc65f4f34047dcdb44e6cf7d5bd989dd0412ea3063d6db469fb27bc6294767e`。原版明确代理 48126。所有证据位于 `system-remaining-20261115/`。

### 页面实际观察

两端桌面实际 viewport 1512×805，连接同一隔离数据；从真实菜单进入并等待数据加载后读取。

| 页面 | 两端记录数/状态 | 已验范围 |
| --- | --- | --- |
| 通知公告 | 2 条 | 列表、标题 `not-a-notice` 搜索空、重置 2 条；新增表单含富文本/类型/状态/备注，取消后仍 2 条 |
| 短信渠道/短信模板/短信日志 | 3 / 16 / 0 条 | 筛选字段、表头、数量、列表/空状态；16 条第一页显示 10 条 |
| 邮箱账号/邮件模板/邮件记录 | 2 / 2 / 0 条 | 筛选、表头、可见按钮、数量及空状态 |
| 站内信模板/站内信记录 | 0 / 95 条 | 筛选、表头、可见按钮、数量及空状态；消息首屏 10 条 |
| OAuth 应用/OAuth 令牌 | 4 / 2 条 | 表头、筛选、操作结构、数量；证据未保存 token 值 |
| 三方应用/三方用户 | 0 / 0 条 | 相同筛选、表头、可见按钮及空状态 |
| 地区树 | 两端北京市、天津市等节点一致 | 展开 110000 后实际子节点为“北京市 110100”；以 `*-area-expanded.txt` 为准 |

汇总 JSON 经离线比较，12 组页面的 headers、labels、totals、visibleRows 相同。首版采集器在 Demo 短信渠道/模板另采到了隐藏的“查看全部”按钮；此项属于采集范围不同，不作为可见按钮差异或完全相同的证据。其它 10 组的按钮集合相同。临时原始短信 DOM 含可能的密钥字段，已精确删除，仅保留结构化标签/表头/数量；未提交表单、发送短信/邮件、强退令牌或操作三方认证。

异步页面初始“暂无数据”不一定是最终状态；站内信页面等待后为 95 条。非空页以真实总数及数据行加载为准，空页结合完成状态与隔离 SQL 计数，不把瞬态空壳计为通过。

Demo 保存的 Console warn/error 为 `[]`。原版日志是同标签跨会话累计 100 条，包含旧 5188 的两条未读数轮询 Network Error 及 5190/旧会话的 Router next 废弃和菜单 indexPath 警告，不能称本轮原版 Console 无错误；完整 Network 审查尚未完成。

390×844 两端 documentElement scrollWidth 都为 390，但截图中原版保留 70px 折叠侧栏，Demo 有半透明展开菜单浮层；菜单状态不同，不能判同状态视觉或响应式通过。保留 `demo-notice-mobile.png`、`original-notice-mobile.png` 作待复测证据，已恢复视口。

### T3-SEED-PLAN 实现与验证

根因：005 平台种子中残留混合编码文本，007 局部修复未覆盖；原始完整 SQL 中对应同表同 ID 的正确名称可核对。新增 `009-fix-platform-plan-labels.yaml`，由既有 MySQL changelog 尾部 include 注册，包含内联守卫 UPDATE 和反向 rollback。精确修复 43 个字段：infra_config.name 1、infra_job.name 1、system_dict_data.label 3、system_dict_type.name 4、system_dict_type.remark 1、system_menu.name 33。历史通知消息等其它乱码不在本配置修复范围，保留原值。

每条 UPDATE 同时匹配 ID、稳定身份字段和 BINARY 旧文本，使用 UTF-8 hex 文本避免客户端编码歧义；显式 `update_time=update_time`，不触碰用户表、密码、权限、路径或审计人。反向 rollback 同样守卫，仅供审查后使用：它无法区分后来恰好改成相同正确文本的用户编辑，真实环境必须先备份匹配行，不能盲目自动回退。MySQL 8 执行有 BINARY 表达式废弃警告，现版本执行成功；已执行 009 不为消除警告而改写，后续迁移可使用 CAST AS BINARY。

- 红灯：实际 MySQL 上 43 项均返回不符合来源的 0，专项行为断言失败；`seed-repair-red.log`。不是缺少文件/编译失败代替业务红灯。
- CLI 前两次尝试分别因旧 Main 不接受 searchPath、完整消费端 classpath 内存在旧 Core 同名 changelog 而停止；只读确认总数仍为 54、009 不存在后才改用最小依赖 classpath，原始失败日志保留。没有设置重复资源 WARN 或跳过 checksum 来绕过错误。
- Liquibase 4.31.1 + Java 21 + MySQL：第一次实际执行 Run 1、Previously 8（仅 Core 根，共 9）；第二次 Run 0、无待执行项。数据库包含业务根的总 changelog 从 54 增为 55。日志 Rows affected 44 含迁移记账，不能解释为 44 个配置字段。
- 001–008 共 8 个文件 SHA-256 与原有 54 条 DATABASECHANGELOG checksum 完全不变；`seed-repair-baseline.json`、`seed-repair-after.json`。
- 真实事务测试验证自定义值不覆盖、连续两次执行、反向文本恢复、update_time 保留、用户密码集合摘要不变；摘要只在 MySQL 内部比较，不输出/归档值。事务 ROLLBACK 后再核对 43 个正确字段。
- 最终 Core 治理套件 54 项全部通过，无跳过（环境变量显式指定专用 schema）；`seed-final-governance-tests.log`。
- Core 离线 `mvn -o -pl yuheng-server -am -DskipTests package` 成功；该命令跳过 Maven 测试，不称为后端全量测试通过。实际 JAR 中已核对 009 内容和注册 include 与源码一致，`seed-core-package.log`。

修复已在 Core 源码/本地产物中交付，未 install/发布 registry、未刷新 Demo 的已安装 Core 包或重启共享实例，故共享 Demo 尚未应用此数据迁移。升级消费端 Core 时由 Liquibase 应用；该项不代表 T1 版本发布完成。

### 迁移技能发现入口

用户已授权业务模块复制流程形成 skill 供 AI 复用。现有技能内容不改；发现安装检查仅报告三个缺失入口，确认不存在冲突后，通过官方 `sync_agent_assets.py` 补齐 `.agents/.claude/.qoder` 下的 `yuheng-business-template-migration` 链接。再次 check 为 PASS/0 drift，verify_bundle 为 PASS；没有改消费端规则快照或假定已完成所有工程升级。

### 环境收尾与真实边界

仅向已核实身份的 PID 63644/63660/63612 发送 TERM，确认三者退出、5189/5190/48126 无监听后，完成独立 Liquibase 与事务验证，再清理 schema。显式 DROP `yuheng_t3_remaining_20261115` 并 REVOKE 其对共享账号 `yuheng` 的 schema 授权，最终 schema/grant 均为 0；共享 `yuheng_demo` 及账号仍存在。两份本任务临时 JAR 均在确认无人使用且 SHA 相符后精确删除。其它 PID 23945/39370/88324/88411 保持运行。

Redis DB14 没有紧挨启动的空库基线，不声称有。停止后确认无 DB14 客户端，32 个可见键均符合本轮菜单/角色权限或隔离库 access token（值未输出）；仅 DEL 已核实的精确键，没有 FLUSHDB，最终 DBSIZE=0。其它 Redis DB 未修改。完整收尾见 `cleanup.json`。

**最终状态**：本轮上述桌面只读子项、43 字段新增迁移和技能发现修复完成。T1 固定版本 registry 消费仍未完成；T3 其余 System/Infra/ERP 页面、主要写交互、统一菜单状态的响应式和完整网络检查继续开放；T4 全量权限/租户/事务矩阵继续开放。不把本次结果外推为全量迁移完成。

## 2026-11-15 公告与岗位主要交互、窄屏及权限续验

对应 T3-MOBILE-FOLLOWUP / T4-SYSTEM-NOTICE-POST-PERM，证据在 `mobile-followup-20261115/`。同一浏览器标签依次访问两端，真实视口 390×844，UI 折叠菜单并关闭遮罩后，两端公告列表 width/scrollWidth 均 390、collapsed=true、overlay=0，截图视觉一致（品牌/页脚除外）。长标题折行、列裁切与分页不舒适同样存在于原版，仅判同状态迁移一致。公告表单两端宽 390、scrollWidth=800，且截图有悬浮菜单遮挡，表单窄屏仍为 NOT_PASSED，不用列表结论替代。

公告：空表单出现标题/内容/类型必填提示；真实 UI 新增 id5、编辑标题与关闭状态，原版 UI 回读一致；取消修改未保存；标题筛选/重置通过。岗位：真实 UI 新增 id9，编辑名称/排序，原版 UI 回读名称、编码、排序、备注一致。两条夹具最后均通过 HTTP DELETE 清理，租户1公告/岗位分别回到2/4条；删除未通过 UI 验证。富文本最初 fill 未触发正确事件，改用实际输入后成功，不能当成产品缺陷。公告备注输入在原版与 Core 都存在，但两端 VO、DO、真实表均无 remark，保存后不保留，作为继承契约限制记录，本轮没有增加列或扩展业务。

权限：支持的 API 创建无角色临时用户，permission-info 的 roles/permissions 为空，SQL 有效角色关联为0；公告、岗位各 page/get/create/update/delete 共10项返回业务码403，前后完整表快照不变。管理员携 tenant-id121 的两个 page 返回403（只证明 header 拒绝，不代表行级租户矩阵通过）；两个匿名 page 返回401。最后删除临时用户，活动行0。证据 `system-permission-boundaries.json` 无口令或令牌。

历史密码使用 MySQL 内部逐行 BINARY 比较已执行006对应21名历史用户，21项均匹配；未输出或保存密码/hash。初始 GROUP_CONCAT 摘要可能被默认1024长度截断，不能单独证明全部用户，最终以 `password-preservation.json` 的逐行检查为准。历史公告行保持。

Console：Demo 保存0 warn、1条未定位的 Object error（空表单提交时）；原版30 warn、10 error，含开发配置失败及 loading.close 等，不称全局干净。原版首次 `--mode local` 被 Vite 拒绝；随后 `--mode dev` 错误继承远端 VITE_BASE_URL，浏览器曾提交登录尝试但失败，不能称无远端请求。最后明确 VITE_BASE_URL=''、VITE_BACKEND_ORIGIN=http://127.0.0.1:48127，以 development 模式启动5192后才进行上述成功验收。

收尾 `cleanup.json`：停止本轮 PID65712/65758/66003，48127/5191/5192关闭；只删除 schema `yuheng_t3_mobile_20261115` 和专属用户 `yh_t3_mobile15`，最终均0。Redis DB15启动前0、运行后34、清理后0；临时 JAR/私密文件已删除。共享schema/账号存在，其它记录的四个PID仍运行。消费者不可变 JAR 本轮仍为原54 changesets，不包含009；没有 install、registry发布或共享库升级。手工浏览器操作退出码 N/A。总任务仍未完成。

## 2026-11-15 T3 公告/岗位表单校验异常修复

对应计划 T3-SYSTEM-FORM-VALIDATION。Core 公告、岗位两份表单直接 await Element Plus `validate()`；校验失败时该 Promise 拒绝的是字段错误对象，Vue 事件异常处理器因此收到不透明 Object。上游相同位置也有该写法，属于继承行为，不将它描述为迁移新增缺陷。最小修复将 ref 守卫改为 `formRef.value`，并使用 `validate(() => {})` 令预期校验失败返回 false；保留既有 `if (!valid) return`、请求方法/参数、成功事件和 finally。没有添加吞掉所有异常的 catch，API 失败仍向上传播。

### 行为测试与构建

新增 `yuheng-core/yuheng-ui/tests/compat/system-form-validation.test.ts`，实际挂载 Vue 与 Element Plus 的 Form/FormItem/Input/Select/Button，单测仅替换 Dialog 外壳、富文本编辑器及 API。每个表单覆盖空提交、合法新增、合法编辑、API 拒绝，共8项。空提交需出现必填提示、零请求/零成功事件、弹窗保留、无 Vue 事件异常；API 拒绝需保留原始 Error、释放 loading 且不报成功。

最初 Node 外置 ESM 依赖互操作导致 async-validator 行为异常，不能作为产品红灯；测试改用 Element Plus 实际 CommonJS 发行版后，真实复现两份表单的字段对象拒绝，`red.log` 为2项失败/6项通过。修复后 `green.log` 为8/8通过。测试文件通过动态路径加载旧 compat SFC，避免把公共包类型检查范围扩展为整个旧消费端代码；浏览器补验使用实际 ESM 组件，未替换校验器。

2026-11-15 09:38起使用已安装 Node22.23.2 再次运行，以下命令全部退出0，原始输出与退出码在 `form-validation-20261115/*-final.log` 和 `final-checks.json`：

| 命令（Core yuheng-ui 目录） | 结果 |
| --- | --- |
| `node node_modules/vitest/vitest.mjs run` | 27个文件、121项通过，含本次8项，无跳过 |
| `node node_modules/vue-tsc/bin/vue-tsc.js --noEmit` | 通过 |
| `node scripts/check-boundary.mjs` | 通过 |
| `node node_modules/vite/bin/vite.js build` | 1466个模块，成功 |
| `node node_modules/vue-tsc/bin/vue-tsc.js -p tsconfig.build.json` | 声明构建通过 |

单测保留5项预期 required 的 async-validator stderr 提示；构建保留原有 Infra API 动静态混合导入 warning，不能称全程无 warning。未运行本轮 Maven/数据库测试，没有安装依赖、发布 registry、替换消费端安装包或共享实例。

### 实际浏览器组件补验

专用预览仅监听 `127.0.0.1:5193`，配置与源码保存在 `form-validation-20261115/preview/`。加载实际 Core NoticeForm/PostForm、Dialog、WangEditor、Element Plus，独立 Pinia/runtime，使用内存请求适配器；Icon 替换为本地字符以避免图标供应商网络请求。未连接后端/数据库，以下结果严格限定为组件浏览器层：

| 操作 | 可见结果 |
| --- | --- |
| 公告空提交 | 3项必填提示；模拟写请求0、成功0、异常0；弹窗保留 |
| 填标题、选择通知并在真实富文本键入内容后提交 | 模拟写请求1、成功1、异常0；新增成功，弹窗关闭 |
| 岗位空提交 | 2项必填提示；计数仍1/1/0，无额外请求或异常 |
| 填岗位标题、编码、顺序后提交 | 累计写请求2、成功2、异常0；弹窗关闭 |
| 注入岗位请求 Error 后提交合法表单 | 累计写请求3、成功仍2、异常1；原始错误进入错误处理器，弹窗保留，DOM提交按钮无 disabled |

故障注入前 Console warn/error 为 `[]`；注入后恰有一条预期 `Error: 模拟请求失败`，堆栈回到真实岗位 API/submitForm。截图、DOM、分阶段 Console 与 `browser-results.json` 可复核。富文本首次 `fill()` 未同步编辑器内容，随后使用真实逐字键入成功；不把初次未生效动作当成功。

窄屏390×844另测没有菜单/下拉浮层的公告表单：可见 dialog width390、scrollWidth800，编辑器宽656；document clientWidth/scrollWidth均390，overlay计数0。截图 `notice-mobile-browser.png` 证实内部内容溢出，不能仅凭整页未溢出判响应式通过；此问题仍未修复，本轮不改布局。它补充上一轮悬浮菜单干扰的诊断，不代替完整Demo/原版成对验收。

清理：专用浏览器标签页关闭、临时视口reset；预览进程收到SIGINT后退出0，5193无监听。没有创建schema、数据库账号或Redis夹具。自检范围限定两份表单、8项专项测试及证据；没有发现本修复改变成功/API失败契约的证据，完整Demo联调仍未覆盖。T3该校验子项源码与组件层完成，T1/T3/T4总项继续开放。


## 2026-11-15 T3 共用Dialog窄屏宽度修复

对应同计划 T3-DIALOG-MOBILE-WIDTH；代码/治理/知识版本沿用0.1.0-SNAPSHOT / 0.2.0 / 0.1.0，已有完整迁移与全局样式修复授权持续有效。上一轮公告窄屏记录需精确解释：Element Plus的 `role=dialog` 在 `.el-overlay-dialog` 遮罩上，测得width390并非内层面板宽度。本轮读取实际 `.el-dialog`，390×844视口下面板width800、right800，提交和取消按钮right分别708.109375/784，遮罩scrollWidth800，编辑器width656，max-width=none。真实断言“面板和页脚应在视口内”失败；见 `mobile-dialog-20261115/red-measurements.json`、`red-assertion.txt`、`red-390.png`。这是目标布局断言红灯，非工具/编译失败。

对照原版与Core的Dialog/Editor，差异仅为迁移导入路径；窄屏缺少面板最大宽度约束属于继承缺陷。本次仅在Core compat/components/Dialog/src/Dialog.vue已有.com-dialog样式添加 `max-width: 100%`，保留原width属性、拖动/关闭/全屏和全部表单字段/API。没有重新设计移动端或改变业务契约。

### 实际浏览器红绿与兼容

最初使用上一轮只读预览5193保存红灯及单项CSS HMR绿灯；后续新建本轮preview5194，沿用真实Core Dialog/Editor/Form、独立Pinia/runtime和内存请求，增加百分比/默认全屏检查入口和可访问的本地Icon按钮，不修改上轮证据预览。仅监听127.0.0.1，无后端/数据库。

| 视口宽度 | 实际面板宽度 | 面板scrollWidth | 编辑器宽度 |
| --- | --- | --- | --- |
| 320 | 320 | 320 | 176 |
| 390 | 390 | 390 | 246 |
| 768 | 768 | 768 | 624 |
| 1512 | 800 | 800 | 656 |

每项均断言面板left/right在视口内、scrollWidth不超过clientWidth+1、两个页脚按钮横向边界可见；1512另断言仍800。宽度及截图见 `width-matrix.json` 与notice-*.png。富文本工具栏自然换行，390下表单高837，初始页脚可能在屏幕下方；实际点击确定时浏览器滚动遮罩后，页脚top746/bottom778位于844高视口内。没有添加隐藏overflow或裁掉内容来冒充适配；长表单仍通过原遮罩纵向滚动。

移动端公告空提交保留3项必填提示、模拟请求0/成功0/异常0；真实编辑器逐字输入内容并选通知后提交，累计模拟写请求1/成功1/异常0，弹窗关闭。390岗位取消、320公告取消均可通过实际按钮操作且计数不增。百分比width60%在1512下907.1953125，在390下234；切换全屏为390，退出恢复234；defaultFullscreen为390，均实际断言。浏览器warn/error保存为[]。手工浏览器操作退出码N/A，数值断言在工具中执行，无失败。

截图检查说明：post-390-final.png截图采集在弹窗进入动画期间，存在背景文字透过的瞬态，不能据此判弹窗永久透明或全局样式通过；宽度结论来自数值和交互。green-390-required.png可见完整字段横向边界与页脚，同时顶端因纵向滚动在视口外，符合长表单状态。未验富文本上传及每个工具栏弹出菜单，不将组件预览外推为完整Demo手机流程。

### 回归、自检与清理

09:46起使用已安装Node22.23.2执行Core UI完整27文件121项测试、vue-tsc --noEmit、平台导入边界、Vite生产构建及tsconfig.build声明构建，全部退出0；checks.json及对应log保存。构建1466模块成功；保留原有Infra动静态导入warning，单测有预期required提示。生产代码差异仅一条CSS声明，未修改后端、SQL、权限、租户、历史密码、依赖、registry或消费者安装包，前一轮表单校验修改保留。

已停止两个本轮预览进程（退出0），5193/5194均无监听，专用浏览器标签关闭且视口reset。未创建schema/账号/Redis资源。acceptance.json、cleanup.json可复核。该子项Core源码与组件层宽度修复通过；消费端版本应用及完整Demo移动端验收仍待完成，T1/T3/T4总项继续开放。

## 2026-11-15 T3 Vite Core 兼容源码开发态续验

沿用 `YH-20261111-full-source-migration`、完整迁移授权和既有 T3 范围。此次只修改 Demo UI Vite AutoImport 排除规则及对应回归测试；没有改 Core 包源码、依赖坐标、registry、共享数据库或历史密码。

根因核对：`node_modules/yuheng-ui` 是指向 Core 工作树包目录的符号链接，实际 `formRules.ts` 位于 Core 的 `yuheng-ui/compat/utils`。AutoImport 原排除正则只放行 `node_modules/yuheng-ui/compat` 路径，却不接受符号链接解析后的 Core 实际文件路径，因此该模块没有被自动导入转换。冷缓存期间，通过 Vite 实际请求 Core 文件转换端点观察到只有裸 `useI18n()`、没有 import；Vite 并未将 formRules 列入 optimize metadata，故失败根因是 AutoImport 文件过滤规则，而非仅由 optimizeDeps 预打包造成。

在 `yuheng-demo-ui/vite.config.ts` 中精确放行 pnpm/Core 包目录下的 `yuheng-ui/compat` 文件，同时保留其它 `node_modules` 排除。`tests/vite-config.test.ts` 现在动态创建项目 Vite server，使用 `require.resolve('yuheng-ui/compat/platform')` 定位当前实际包，再通过 Vite `transformRequest` 转换 Core `formRules.ts`，断言转换输出含 `useI18n` import。真实回归修复前因缺少 import 失败，修复后通过；不依赖绝对机器路径。

修复后 `/@fs/<实际 Core 路径>/compat/utils/formRules.ts` 的响应含 `import { useI18n }`。隔离 Demo 登录页浏览器 DOM 正常渲染，说明本次转换缺陷已从实际模块与页面入口复核；未登录后页面不代表登录后路由通过。Demo UI 全量 Vitest 3 文件、13 项通过；`vue-tsc --noEmit` 通过；Vite 生产构建 4321 模块成功，保留既有大 chunk 警告；`git diff --check` 通过。生产 bundle 通过不代表该开发模式问题已由 registry 发布版安装消费验证。

运行边界：本轮临时 Vite 5187 已停止。隔离 Boot PID 78090/48129 仍属 Codex app-server 子进程，先前启动上下文未能确定 DB/Redis schema 的精确清理账目，因此保留、不误停、不清理 Redis；只读检查 `/admin-api/system/tenant/get-by-website?website=127.0.0.1` 返回 `data:null`，不能据此尝试登录。共享服务 PID 23945/39370 未修改；共享后端 `/admin-api/system/auth/get-permission-info` 仍在 3 秒只读探测内无响应，而共享 UI `/`、`/login` 均为 200。浏览器仅对 5187 登录页进行只读加载，未提交凭据或表单。

诊断中 Vite 首次启动命令误用 `pnpm exec` 触发 workspace 安装并因私有 registry 固定版 `yuheng-ui` 404 退出；pnpm 输出显示将 5 个直连依赖移动到 `node_modules/.ignored`。已按原命令输出精确恢复 `@iconify/json`、`@iconify/vue`、`@types/lodash-es`、`echarts`、`lodash-es`，保留 `.ignored` 其它目录；之后只用本地 Vite 二进制，不再次安装。该 404 再次证明 T1 固定坐标消费仍未完成。

页面首次完整启动时还观察到 Vue 插件和组件重复注册 warnings。源码链显示 `installYuhengUi` 安装现代 Element Plus、Vue I18n 和 Core components；Demo 之后又调用 `setupCompletePlatform`，其中再次安装 Vue I18n/FormCreate，同时 Demo 再注册 Core 已注册的 `Pagination`、`ContentWrap`、`ContentDetailWrap`、`Dialog` 等名字。Vue I18n 11 的 `globalInstall` 默认会注册 `i18n-t`/`I18nT`、`i18n-n`/`I18nN`、`i18n-d`/`I18nD` 和 `t` directive；两次安装与显式组件注册可解释对应重复告警。FormCreate Designer 的 `install` 本身只注册 `FcDesigner`，不把 Element Plus 重复告警归咎于它。此次仅完成根因源码追踪，没有改变兼容层初始化架构或压制 warning；该兼容安装重复仍待设计与回归，不能声称全局 Console 干净。

本记录只关闭 Demo Vite 开发态 Core compat 文件自动导入缺口。浏览器登录、完整 System/Infra/ERP 页面、主要交互、响应式和完整 Network/Console 审查仍开放；T1 registry 固定版消费和 T4 全量后端审计也仍开放。

## 2026-11-15 T3 重复插件与组件注册修复

沿用 `YH-20261111-full-source-migration` 和既有完整 UI 迁移/全局样式修复授权。根因由源码链和浏览器警告共同确认：Core `installYuhengUi` 已安装 Vue I18n、Element Plus 与 Core 组件；兼容 `setupCompletePlatform` 随后再次安装另一份 Vue I18n；FormCreate 组件集合还直接注册一批 Core 已提供的 Element Plus 组件；Demo 入口又重复注册 `Pagination`、`ContentWrap`、`ContentDetailWrap`、`Dialog`。Vue I18n 11 默认每次 install 会注册 `i18n-t`/`I18nT`、`i18n-n`/`I18nN`、`i18n-d`/`I18nD` 和 `t` directive。

变更：Core compat i18n 初始化优先复用 app 上 Core composer，合并原版中文/英文资源，按兼容 locale store 更新当前及 fallback locale，不再重复 app.use；单独使用 compat setup、没有 Core i18n 时使用 `globalInstall:false` 安装 i18n，使其 `useI18n` API可用但不重复全局组件/directory 注册。FormCreate 安装仅注册 Core 尚未提供的组件。Demo 删除对 Core 已注册组件的二次导入与注册，并保留带存在性检查的 `DocAlert`、`DictTag`。

行为回归先红后绿：真实 Vue app + Core runtime 后再执行 compat i18n 时，红灯复现七项 Vue 重复注册告警；执行 FormCreate 时红灯复现 Element Plus 重复组件告警。修复后两个行为均通过。Core UI 全量 28 文件/123 项测试通过，平台导入边界通过，Core Vite 1466 模块生产构建成功，声明构建通过。Core `vue-tsc --noEmit` 既有配置会把整套旧 compat 消费源码纳入严格检查，并报大量历史 `.ts` 扩展/AutoImport 全局类型等错误；修正本次测试文件自身重复导入和动态导入类型错误后，相关错误均来自原有旧 compat 范围，该命令不作为通过证据。Demo UI 全量 14 项通过、`vue-tsc --noEmit` 和平台导入边界通过、生产 Vite 构建4314模块成功，保留既有大chunk warning。

隔离浏览器通过 Demo production bundle + 静态代理 5187→隔离后端48129只读打开 `/login`，页面显示中文登录字段，Console warn/error 均为空；重复 Vue I18n/Element Plus 注册警告未出现。没有输入或提交凭据、没有登录或业务写请求。本轮临时 5187 已停止，未改动隔离后端 PID78090或共享服务；登录后页面仍未验收。固定版 registry 404 仍未解决，生产 Core 包来源为当前 workspace symlink，不能外推固定版本安装消费完成。

此项关闭重复初始化告警的登录入口验证，不代表所有页面 Console/Network、登录后 System/Infra/ERP 及交互响应式验收完成。T1、T3、T4 总体仍开放。

## 2026-11-15 T3 角色菜单取消路径组件续验

沿用 `YH-20261111-full-source-migration` 和已授权迁移验收范围。本轮使用 Core 实际 `RoleAssignMenuForm`、Element Plus `ElTree`/表单/按钮和受控 API 边界，无后端、数据库、浏览器持久状态或 registry 操作。测试装载角色 2 已有菜单权限，展开树后实际点击子节点复选框，确认勾选节点数量发生变化，再点击真实取消按钮。

断言结果：Dialog 关闭；菜单勾选改动未调用 `assignRoleMenu`；未发出 success 事件。新增 `tests/compat/role-menu-cancel.test.ts` 单项通过。Core UI 完整 Vitest 为 29 个文件、124 项通过；Vite 生产构建 1466 模块成功（保留既有 Infra 动静态导入 warning）；`vue-tsc -p tsconfig.build.json`、`scripts/check-boundary.mjs` 和 Core/Demo `git diff --check` 通过。

`vue-tsc --noEmit` 仍失败于既有 compat 源码范围，包括 `.ts` 扩展导入与 AutoImport 全局类型缺失；本轮新增测试没有被识别为错误来源，该命令不计通过。测试只证明取消按钮的前端行为，不证明 HTTP/数据库行为。上轮角色权限真实隔离流程在误点保存后留下无法从旧快照解释的三条活动关系；其专用 schema 已删除，当前组件证据无法补足当时缺失的重复行/租户元数据，因此“精确全表数据库差异”仍未完成。

本轮未启动服务、未访问或修改 MySQL/Redis、未改历史用户密码、未修改业务运行时代码。T3 的剩余页面与响应式/Console/Network覆盖、T4 的完整权限/租户/事务矩阵及异常回滚审计、T1 固定版本 registry 包消费仍开放；全量源码迁移未完成。

## 2026-11-15 T4 Core System/Infra Mapper 租户策略清点

本轮以当前 Core 源码为准，只读盘点 `yuheng-module-system` 与 `yuheng-module-infra` 的 Mapper、DO 租户基类/注解及 XML 资源。共 54 个 Mapper：7 个关联 `TenantBaseDO`，22 个关联 `@TenantIgnore` DO，24 个关联不含租户列且未标忽略的 `BaseDO`，1 个自定义 Mapper（FileContent）；目标模块资源中没有 Mapper XML。归类脚本对实体解析 0 个未解析项。该统计描述实体策略，不单独证明每个方法的授权/租户语义。

六个注解 SQL 已逐条读源码：`DictTypeMapper.updateToDelete` 更新 `@TenantIgnore DictTypeDO` 的共享字典软删除字段；OAuth2 access/refresh token 的过期清理按 expires_time 批量物理删除，其清理不受请求租户影响；按 access token 或 refresh token 查询的两个 OAuth mapper 方法显式 `@TenantIgnore`，而 userId/userType 与 refreshToken 列表查询使用实体默认租户条件；job log、API access log、API error log 的时间清理作用于 `@TenantIgnore` 平台日志表。未发现该六条注解 SQL 与 DO 租户模型直接冲突。此检查没有执行跨租户运行请求，不能替代 HTTP 矩阵。

运行状态续验：当前隔离 PID 78090/端口 48129 的进程命令含 `YUHENG_DB_NAME=yuheng_t3_vitedev_20261115`、Redis DB 2；只读 API 返回匿名业务码 401。但 MySQL `information_schema` 中该 schema 和表数均为 0，说明数据库基线已被清理，不能登录或继续任何写验收。本轮未停止该 app-server 子进程、未访问或清理 DB 2，也未改共享服务。5173 登录页正常渲染；在隔离浏览器提交历史凭据后没有建立登录会话，页面停留登录表单，故没有取得 T3 页面证据。

范围限制：目前只完成 Mapper 实体策略归类、六条注解 SQL 阅读和 XML 数量核实；54 个 Mapper 的全部 default/wrapper 方法及租户绕过调用点尚未逐一人工审阅，47 个 Controller 的请求级矩阵也没有扩展；Core 49 个 System/Infra ServiceImpl 的逐写方法事务矩阵、Quartz/对象存储故障注入仍开放。T4 不关闭，T3 本轮登录受已清理 schema 阻断，T1 固定版本 registry 消费仍开放。没有以静态清点代替整体迁移验收。

### T4 Core System/Infra Service 源码逐文件归一复核

当前工作区 Core 与 `ruoyi-vue-pro` 对应上游源码进行路径相对位置匹配，分别找到 System 34 个、Infra 15 个 `*ServiceImpl.java`，两侧均无缺失或额外文件。对完整包名前缀按 `com.yuheng.platform` → `cn.iocoder.yudao`、`com.yuheng.boot` → `cn.iocoder.boot` 归一后，System 34/34、Infra 15/15 字节完全一致；49 个文件无残余内容差异。先前仅替换业务包前缀的脚本把框架包名变化误报为行差异，本结果纠正该比较口径。

此证据证明当前这 49 个 Core System/Infra Service 实现与本地上游源码一致，不证明 Mapper default 方法、Controller 注解/请求映射、Java 以外资源或运行期事务语义全部一致。先前写入的“目标 94 个服务实现”没有对应源码清单或范围定义，本轮全仓路径核对也确认 Core 这两个模块当前共 49 个 `ServiceImpl`；故 94 不再作为 Core 服务数或验收基准。逐写方法事务矩阵和 Quartz/对象存储故障注入仍开放，T4 不关闭。

### T4 租户忽略调用链定向续审

继续检查全局 `@TenantIgnore` 实现和此前盘点到的调用链：MyBatis 拦截器先检查 `TenantContextHolder.isIgnore()`，再按表实体 `TenantBaseDO` / `@TenantIgnore` 决定是否附加 tenant 条件；未知表默认忽略。AOP 注解仅在 `enable` 表达式为真时设置忽略状态，并在 finally 恢复原值。Controller 级注解由租户安全过滤器启动时扫描映射并加入忽略 URL 集合。

方法级路径复核：三个租户发现接口（租户名解析、租户精简列表、域名查租户）均为公开读取并明确忽略租户；验证码 get/check 是公开协议入口；四类短信供应商回调均为公开入口并忽略租户；文件内容下载为公开 GET 并忽略租户。文件下载仍调用 `FilePathUtils.validatePath`，根据配置 ID 解析文件客户端，并从全局 `@TenantIgnore` FileDO 按配置 ID + path 查询附件名；上传/创建/删除接口并未因下载注解而整体忽略租户，写入口仍需登录，管理查询/删除另有菜单权限注解。

需要保留的风险边界：SMS 回调 Service 按供应商解析结果中的 `logId`（缺省时部分适配器用 serial number）更新 `@TenantIgnore` SMS 日志；本轮适配器源码未看到独立签名或回调令牌校验。该路径、各供应商回调契约及信任验证实现与本地上游四个适配器逐文件归一后相同，属于继承行为，不能记为本次迁移差异或据此擅改第三方协议。本轮没有向真实短信回调 endpoint 发请求，也没有模拟伪造回调的隔离安全测试；其回调认证和任意日志 ID 更新风险仍需独立安全评审/实测，不以源码相同证明其安全。

其它此前盘点的忽略租户用法是共享字典、任务定义与日志、API 日志、短信/邮件配置与发送日志、代码生成元数据、文件元数据/内容、租户与套餐等平台全局实体；OAuth token 按原版契约在无 tenant header 时可由 token 值定位，但 token 所属行实体仍有 tenant_id，用户/用户类型与 refresh-token 列表查询保留实体租户条件。Mapper 实体及六条注解 SQL 清单见本节上文。

本续审只确认源码调用链和与上游的迁移差异；当前已知 app-server 隔离 schema 被清理，未做运行期跨租户/伪造回调/文件下载 HTTP 矩阵。故 T4 的所有 Controller/Mapper 方法级租户语义及权限请求矩阵仍未完成，T4 保持开放。

### T4 Core 关联 Mapper 调用方租户边界续审

本轮只读跟踪 `UserRoleMapper`、`UserPostMapper`、`RoleMenuMapper`、`SocialUserBindMapper`、`OAuth2ApproveMapper`、`NotifyMessageMapper` 的调用方及对应 Controller。这里更正租户策略解释：`TenantDatabaseInterceptor` 对已映射、没有配置为忽略的表默认增加当前 tenant 条件；`TenantBaseDO` 用于明确保证租户表不被忽略，`@TenantIgnore` 才让实体忽略租户。故普通 `BaseDO` 不表示 SQL 没有行级租户条件。上述关联 DO 未标 `@TenantIgnore`，且本轮运行 SQL 日志实际显示 `system_user_role` 查询带 `tenant_id = 当前请求租户`；但该条件只约束关联行的 tenant_id，不验证关联行的 userId/roleId 所指向对象属于同一租户。

需要优先进入隔离 HTTP 矩阵的路径：

- `PermissionController.assignUserRole` 与 `listAdminRoles` 受 `system:permission:assign-user-role` 权限保护，但接受调用者提供的 `userId`。Mapper SQL 仍由租户拦截器限制关联行的 tenant_id；接口没有显式加载并验证目标用户的 tenant_id，也没有逐个验证 roleIds 的租户归属。实际隔离 HTTP 已证明，指定外租户用户会在当前租户下生成孤儿关系；指定外租户角色会替换并逻辑删除当前租户用户原有关联，之后角色查询因角色租户条件而取不到外租户角色，造成该临时管理员失权。没有观察到外租户授权或修改。`getUserRoleIdListByRoleId` 读取的是当前租户下关联行，不是全局关联行；后续 `AdminUserServiceImpl.getUserPage` 再用带租户条件的 AdminUser mapper 查用户。页面 total 已在隔离 HTTP 中对外租户角色 ID 验证为 0。
- `PermissionController.assignRoleMenu` 受菜单权限保护，并先按当前租户套餐过滤 menuIds；`RoleMenuDO` 继承 `TenantBaseDO`，该关联的读写会自动带当前 tenant 条件。不过此处未显式验证 roleId 属于当前租户。隔离 HTTP 请求对租户 1 的角色 ID 返回业务成功，但请求 tenant 条件使其只查询/删除/插入当前租户关联；本轮有限 SQL 读数没有发现目标租户行被改变，但不具备完整 655 行 before/after 快照，故不能据此报告全表不变。
- `AdminUserServiceImpl.createUser/updateUser` 先校验用户及 postIds，关联岗位的 userId 来自已验证/刚创建的 AdminUserDO；用户删除先 `validateUserExists`，批量删除也先逐个验证，随后才清理岗位关系。`UserPostDO` 虽继承普通 `BaseDO`，已映射表仍按请求 tenant 过滤。跨租户岗位 ID 的隔离 HTTP 未能得到有效结论：当前新租户没有部门/岗位夹具，而本轮受支持创建用户路径先受用户表权限或部门归属校验阻断；返回这些前置错误不能证明岗位校验通过。

当前源码能确认的主体来源与查询边界：社交绑定 Controller 不接收 userId/userType，绑定、解绑和绑定列表均从 `getLoginUserId()` 与固定 ADMIN 类型构造；绑定目标社交用户来自第三方 code/state 换取的 AuthUser，解绑按当前登录用户、用户类型和社交类型删除。后台社交用户的通用详情/分页另受 `system:social-user:query` 菜单权限保护。OAuth2 授权批准的 userId/userType 来自已认证 OAuth 主体，Mapper 每次都按 userId、userType、clientId 查询或更新；批准实体为普通 `BaseDO`，隔离依赖该主体参数可信及 OAuth 会话认证。站内信自服务的分页、未读列表/计数及已读更新均在 SQL 中固定 userId + userType，Controller 从登录态构造；管理端通用分页/详情受 `system:notify-message:query` 权限保护，可按请求筛选 userId，但未显式校验目标用户归属。以上仍需跨用户/跨租户 API 矩阵验证。

迁移判断：本轮未发现上述调用代码相对本地上游的修改证据。表级租户拦截能按请求 tenant_id 限制这些关系行，但不验证被关联对象的租户归属；当前已证明的实际影响是请求成功返回并写入当前租户孤儿行，以及角色集合替换行为可使当前租户管理员失权，而非外租户行被直接读写。完整确认仍需对通知管理权限下的跨用户 page/get、站内信已读写、OAuth2 批准主体、社交绑定和岗位关系做成对 HTTP 请求及精确表快照；当前不连接共享库，不重用 schema 已清理且数据源不明的 PID 78090。

本续审完成 Mapper 关联方法及主要 Controller/Service 调用方的静态追踪；没有运行期请求、没有修改代码或数据库。Core 方法级权限/租户完整矩阵、事务回滚矩阵、Quartz/对象存储故障注入继续开放，T4 不关闭；T1 固定版本 registry 消费和 T3 剩余页面/交互/响应式验收也继续开放。

### T4 权限关联跨租户 ID 隔离 HTTP 续验

使用当前工作区重新打包的 Demo JAR（SHA-256 `61fba9414357444edbb929ca77a572c60659c7586e665a2c898e25fbd724fae6`），端口 48131，专用 schema `yuheng_t4_perm_20261115_a`、仅授权该 schema 的 `yh_perm15`、Redis DB 4。Redis DB 4 启动前为 0。空库 Liquibase 执行 54/54 changeset、建立 150 张表；21 个种子用户密码字段均非空；未修改历史密码。所有账号和数据仅存在于新建隔离库。匿名 API 返回业务码 401。凭据、access/refresh token 均未写入本记录。

使用隔离平台管理员创建临时有效套餐租户 162（仅拥有少量权限）及租户 163（普通套餐），后者管理员用户 ID 250、角色 ID 170。原有租户 121 用户 ID 110、角色 ID 109；平台角色 ID 2 属于 tenant 1。分别从 SQL 核实这些 ID 的归属，再用租户 163 管理员身份发请求：

- 调用 `GET /system/permission/list-user-roles?userId=110` 和 `POST /system/permission/assign-user-role` 为用户 110 分配平台角色 2，均返回业务码 0。SQL 显示租户 121 的原关系 `(110,109,tenant=121)` 未变，平台原关系 `(110,2,tenant=1)` 未变；新增一行 `(110,2,tenant=163)`。tenant 163 的关联行无法加入 tenant 121 用户的有效授权上下文，故本次未观察到权限提升，但接口没有拒绝跨租户目标，并会产生不可达关联数据。
- 对当前用户 250 指定外租户角色 109，分配接口返回业务码 0。SQL 显示租户自身角色 170 关联被逻辑删除，并新增 `(250,109,tenant=163)`；随后 permission-info 中角色与权限均为空，目标角色 109 因 `system_role` tenant 条件而不可见。该操作对临时 tenant 163 管理员造成失权，对 tenant 121 角色及其数据无影响。它证明错误角色 ID 可导致本租户用户自我失权和孤儿关系，不证明能取得外租户角色权限。
- 对租户 1 角色 2 调用 `GET /system/permission/list-role-menus` 与 `POST /system/permission/assign-role-menu` 均返回业务码 0。随后 SQL 逐行检查 role 2 的关联：tenant 1 的 655 条有效记录未变，tenant 163 下没有为 role 2 新增的关系。当前租户套餐菜单过滤及 `RoleMenuDO extends TenantBaseDO` 让写请求落不到目标角色，但接口没有拒绝不属于当前租户的 roleId。
- 租户 163 管理员对站内信管理 page/get 的跨用户探测均返回 403，因为该角色不具有 `system:notify-message:query` 权限；自服务查询继续由 Controller 从登录主体取 userId/userType，未尝试伪造主体。

请求结束后先对比隔离库关联表与租户/角色归属，再优雅停止 PID 88980。仅清空启动前已证明为 0 的 Redis DB 4（最终 0），删除本轮唯一 schema 和专用 DB 用户（最终计数均 0）；端口 48131 无监听。保留旧 schema `yuheng_t3_vitedev_20261115`、PID 78090、共享 schema/服务和其它 Redis DB。没有改任何共享数据或历史密码。

结论：该组探针没有证明跨租户权限提升或对外租户关联行的直接修改。`system_user_role`、`system_role_menu` 读写仍受当前 tenant 条件约束，但接口不拒绝属于其他租户的 userId/roleId，造成请求成功语义和孤儿行；向当前用户提交不可见的外租户角色，还会按集合替换语义删除当前用户原有关联并造成失权。该行为与当前上游迁移源码一致。本轮不擅自改权限契约；T4 后续需核对全量服务事务标注/实际回滚，以及产品是否要求对目标归属做显式校验，再据原版契约与 Core 规则决定迁移修复。证据不扩展到其它关联 Mapper、通知管理权限或完整 tenant matrix；T4、T1、T3 均保持开放。

#### 本轮证据更正与补充

随后对当时隔离实例的 SQL 日志和检查命令复核，收窄两个表述：一是 role 2 的 `system_role_menu` 只核对了有效记录数 655、指定目标组合和租户 163 下目标行未出现；没有完整导出并比较所有 655 行，因此前述“逐行检查/未变”应理解为这些限定查询未发现变化，不构成全表逐行快照证明。二是租户 163 管理员探针在套餐角色中查不到 `system:notify-message:query`，故管理 page/get 的 403 仅证明方法权限拦截；没有证明跨用户目标本身的授权边界。相关完整矩阵仍待补做。

当前登录主体补充分辨：租户 163 管理员绑定外租户角色 109 后，下一次 `get-permission-info` 查询在 `system_user_role` 看到 tenant 163 的绑定，但 `RoleMapper.selectByIds` 受租户条件过滤，角色不存在，最终 roles/permissions 为空。由于同一运行随后被停止，这个主体的后续请求不能再补测；不把它计为恢复/回滚行为验证。

静态追踪还确认 Core 有两个免鉴权用户精简查询：`GET /system/user/get?id=...` 通过 `AdminUserDO` 的 tenant 条件查询单用户；`GET /system/user/list-by-nickname?nickname=...` 通过同样带租户过滤的 Mapper 查询。它们只返回精简 DTO。`GET /system/user/page` 的角色筛选先全局读取普通 `BaseDO` 的 user-role 关联，再把 userId 集合交给 `AdminUserDO` 租户过滤，并在该 Mapper 查询 `total`；该调用链静态上不会从外租户用户拼出返回行，但本轮未从隔离 HTTP 复核跨租户总数。

本节与旧 T4 Mapper 续审记录共同构成本轮进度，不关闭 T4。后续隔离实测已覆盖用户创建/更新拒绝外租户岗位 ID、岗位列表/详情/更新/删除边界，以及免鉴权精简用户 `get` 和昵称搜索的租户过滤。当前剩余项包括用户列表及岗位 CRUD 的更多组合；通知管理员有效权限下跨用户 page/get；站内信自服务只读/已读写不变与跨用户尝试；OAuth 授权批准主体隔离；社交绑定及回调身份验证；全部关联表的权限/租户矩阵和事务原子性。

#### 2026-11-18 T4 免鉴权用户精简查询跨租户过滤

沿用同一 Demo JAR SHA-256 `e50bcf20ec4ca4157638393fcfd9730707bd7395e08a08296e5a9e2266da1e9f`，其嵌套 Core System 模块哈希为 `55115b0639ef5491567c360ce04b09e8829007be4348323ec63b2395a84c4b72`。在新隔离 schema `yuheng_t4_userpublic_20261118` 冷装 54 changesets，后端 48148，schema 专属账号及独立密码保护 Redis 容器 16385。只在隔离进程开启带随机密钥的 Core mock 上下文，以 user 1 / tenant 1 执行读取；没有读取或变更种子密码。

在 schema 内插入唯一租户 999 用户 340，昵称 `FOREIGN-NICK-340`。`GET /admin-api/system/user/get?id=340` 返回 HTTP 200 / 业务码 0 / `data=null`；`GET /admin-api/system/user/list-by-nickname?nickname=FOREIGN-NICK-340` 返回 HTTP 200 / 业务码 0 / 空列表。两次只读请求后 SQL 仍查到该用户为 tenant 999 活动记录。首次不带认证上下文的请求得到全局认证层 401，未作为租户过滤证据；以隔离 mock 建立有效用户上下文后的结果才计入本项。脱敏 JSON：`service-write-audit-20261118/anonymous-user-query-tenant-boundary.json`。

应用优雅退出；专用 Redis 清理前 5 keys，容器移除；临时 schema/账号删除并核实为 0，共享 `yuheng_demo` 仍存在，48148/16385 无监听。该证据关闭这两个精简用户读取接口的单夹具租户过滤子项，不覆盖角色筛选分页、其他查询组合或全局 Controller 权限/租户矩阵；T4 总项以及 T1/T3、全量迁移仍未完成。

#### T4 续验 B：精简用户查询与岗位前置校验

使用同一当前工作区 JAR SHA-256、第二个全新隔离 schema `yuheng_t4_perm_20261115_b`、专属 DB 用户 `yh_perm15b`、端口 48131 和 Redis DB 4（启动前为 0）。Liquibase 再次在空库执行 54/54，建立 150 张表。请求目标租户 121 的用户 ID 110；调用者为隔离平台管理员或受支持 API 创建的普通租户管理员。只测试只读行为及参数校验，没有改写租户 121 用户、共享数据库或历史密码。

- 匿名访问 `/system/user/get?id=110` 与 `/system/user/list-by-nickname` 返回 401；携租户 163 header 但 token 属于租户 1 的请求返回 403（租户安全过滤器拒绝不匹配 header）。使用合法租户管理员并保持 `tenant-id:163` 后，`GET /system/user/get?id=110` 返回 `data:null`，按目标用户昵称搜索返回空数组；`GET /system/user/page?roleId=109` 返回 `total=0,list=[]`。这些结果与普通关联 Mapper 先收集 ID、再由 TenantBaseDO 用户查询过滤的调用链一致。
- 为验证岗位校验，当前 Core 包含的租户初始化不创建部门/岗位。通过平台端新建岗位 ID 9 和部门 ID 122 均成功；合法租户管理员创建用户并引用平台部门/岗位时，业务层先因当前租户内部门不存在返回 `DEPT_NOT_FOUND`。创建仅含空套餐的租户时，用户创建先被权限拦截器 403。尝试给平台套餐加入系统用户管理菜单 ID 后新建租户，得到 14 个 `pay:*` 权限而非系统用户权限，租户的部门/岗位列表仍为空；因此没有形成一条满足“普通租户调用者具有合法用户创建权限且已有本租户部门、再仅伪造外租户岗位”的有效请求。拒绝响应不能单独证明岗位校验通过，岗位跨租户归属和关联写入仍记为未验收。

本轮无权从租户套餐菜单 ID 推断任意模块授权：HTTP 记录显示所选 ID 仍按数据库状态/套餐过滤映射到付费模块，本轮没有继续扩大配置或写更多平台夹具。第二个实例 PID 92099 优雅停止；清理前仅检查本轮 schema 后，删除 `yuheng_t4_perm_20261115_b` 和专用用户，清空启动前已证实为空的 Redis DB 4。清理后 schema/user 计数 0、DB 4 为 0、48131 无监听。第一轮与第二轮结果都不覆盖通知/OAuth/社交全部跨主体和事务矩阵，T4 不关闭。

#### T4 续验 C：站内信跨用户探针夹具复核

复核上轮隔离站内信探针：租户 163 管理员实际有效权限数为 0，套餐角色没有 `system:notify-message:query`。因此管理端 `page/get` 返回 403 只证明权限拦截生效，既没有测试到管理查询，也不能作为跨用户隔离通过；这与下文此前的证据更正一致。本轮没有复用该管理员或对任何现存服务发请求。

对上轮专用资源做只读收尾核查：Docker MySQL 中 `yuheng_t4_notify_20261115_c` schema 不存在，`yh_notify15c` 用户计数为 0；Redis DB 4 `DBSIZE=0`；TCP 48132 无监听。该核查确认资源已清理，不改变站内信隔离验收状态。

**结果**：管理权限下的跨用户 page/get、当前用户站内信列表/未读计数/已读更新及精确数据库前后快照仍未验收。有效权限夹具建立前，不将空结果或权限拒绝解释为数据边界证据；T4 保持开放。

### T4 站内信有效管理权限与自服务隔离 HTTP 续验

使用隔离 Demo JAR（SHA-256 `61fba9414357444edbb929ca77a572c60659c7586e665a2c898e25fbd724fae6`）、端口 48133、schema `yuheng_t4_notify_20261116_a`、专用账号 `yh_notify16a` 和 Redis DB 13。空 schema 执行 54/54 Liquibase changeset 并建立 150 张表。仅使用隔离数据与 API 建立测试主体和消息；没有连接或修改共享 `yuheng_demo`，历史密码未清空或修改。

先给隔离管理会话配置 `system:notify-message:query` 权限，再验证管理查询：有该权限的管理 page/get 可以按请求 userId 查询另一用户的站内信。这符合当前 Controller/权限契约，说明管理权限本身允许跨用户运维查询；不能把它描述为自服务隔离失败，也不能把“未按用户归属拒绝”说成未授权访问。自服务请求则由登录主体固定 userId/userType：管理员主体的 userType 为 2，普通用户主体为 1。普通用户 A、B 的分页分别返回 2、1 条，本人未读计数各为 1，未读列表只含本人消息。第一轮夹具错误使用会员 userType，因 SQL 身份条件不匹配返回空列表/零计数；纠正为管理员 userType 后重测，首轮不作为产品缺陷或验收通过证据。

读取调用前后完整消息行快照：B 对 A 的消息调用 `update-read` 返回业务成功，但快照无变化；B 调用 `update-all-read` 只更新 B 自己的行。A 更新本人消息后，其未读行变为已读。该结果与 Mapper 的消息 ID、userId、userType 和未读条件相符。它验证了本隔离数据下这些站内信自服务请求，不覆盖其它消息 API、跨租户全部通知路径或管理页面的租户数据归属策略。

收尾时确认 48133 无监听、Java PID 95225 已退出；隔离 MySQL schema 原有 150 张表，专用账号仅有该 schema 的授权。已删除该 schema 和专用账号，复核计数均为 0。第一次清理判断时只读发现 Redis DB 13 有 31 个带 TTL 键；随后复核本轮启动前 DB 13 为 0 且无客户端，测试期间由本轮隔离应用独占，清理前亦无 DB 13 活跃客户端，因此确认这些键属于本轮隔离运行。只对 DB 13 执行 FLUSHDB，随后 `DBSIZE=0` 且活动客户端为 0。未触碰其他 Redis DB、共享 schema、历史密码或 PID 23945 等共享进程。

**结果：** 站内信有效管理权限跨用户查询行为，以及自服务分页、未读计数/列表和已读更新的隔离行为均有 HTTP 与 SQL 快照证据；schema、账号和本轮专用 Redis DB 13 均已清理并复核。该子项不关闭 T4：OAuth2 主体、社交绑定/回调、岗位关联、全量 Service 事务与回滚矩阵、Quartz/对象存储故障注入仍未完成；T1 与 T3 也保持开放。

### T4 OAuth2 批准主体静态续审

重新追踪 `OAuth2OpenController`、`OAuth2ApproveServiceImpl` 与 `OAuth2ApproveMapper`：授权信息读取调用使用 `getLoginUserId()`、`getUserType()`；自动预授权检查、人工批准写入以及授权码/implicit token 主体也从同一登录上下文取得 userId/userType。批准 Mapper 的查询条件为 userId、userType、clientId，更新另加 scope；HTTP 参数中没有可覆盖 userId/userType 的字段。批准记录更新/插入由 `@Transactional` Service 方法包裹。此项为源码静态证据，未在本轮隔离 API 中构造 OAuth client、会话和授权回调，也未用不同主体对批准记录做前后 SQL 快照；因此不能关闭 OAuth2 运行期主体隔离、跨主体记录访问或事务回滚验收。相关隔离数据库已随站内信探针删除，不复用共享缓存或未知服务进程。T4 继续开放。

#### 2026-11-18 T4 OAuth2 批准主体隔离真实 API 续验

使用当前 Demo JAR SHA-256 `e50bcf20ec4ca4157638393fcfd9730707bd7395e08a08296e5a9e2266da1e9f`（嵌套 Core System SHA-256 `55115b0639ef5491567c360ce04b09e8829007be4348323ec63b2395a84c4b72`），在新隔离 schema `yuheng_t4_oauthprincipal_20261118` 执行完整 54 changesets。后端端口 48149，schema 专属 DB 账号和独立密码保护 Redis 容器端口 16386；临时 OAuth client 只写入该 disposable schema。Core mock 只在该隔离实例开启，两个主体分别使用 user ID 1003、1004、tenant 1。

两主体均通过 `GET /admin-api/system/oauth2/authorize?clientId=yh-principal-20261118` 读取独立客户端 scope，初始 `probe.read=false`。主体 1003 提交同意后 API 业务码 0，后续 GET 只显示自己的 `true`；主体 1004 提交拒绝后 API 业务码 0，后续 GET 仍显示自己的 `false`。SQL 的两条有效批准记录分别精确为 user 1003/ADMIN/`probe.read`/approved=true 与 user 1004/ADMIN/`probe.read`/approved=false，tenant 均为 1；subject 1004 从未读到主体 1003 的批准。回调 `state` 只用于响应，不作为持久证据。首轮探针的 BIT 字节断言有误；保留临时库后以未使用的新主体 1003/1004 重跑，并按 SQL 布尔值归一化验证，首轮不计通过。脱敏证据 `service-write-audit-20261118/oauth-approval-principal-boundary.json`。

服务优雅关闭后专用 Redis（清理前 1 key）容器移除，隔离 schema/账号删除并核对为 0，共享 `yuheng_demo` 仍存在，48149/16386 无监听。该项关闭一个客户端下 OAuth2 批准读取、同意、拒绝的主体隔离子项；token 交换/刷新/撤销、其它 userType、并发更新及全部事务故障时序仍未验证。社交主体、Quartz/对象存储失败注入与完整 Service/Controller 权限租户矩阵继续开放，T1/T3 与全量迁移未完成。

#### 2026-11-18 T4 文件存储与 Quartz 故障路径源码复核（早期静态快照）

Core 源码确认文件上传顺序为存储客户端写入后插入 `infra_file` 元数据；DB 客户端另先插入 `infra_file_content`。若后续 SQL 失败，可能留下内容行或外部对象孤儿。删除路径先删存储内容再逻辑删除元数据；批量删除在所有对象逐个删除后才批量更新元数据，途中失败可能令活动元数据对应已删除或部分删除的内容。上述结论来自当前代码顺序，尚无隔离故障注入与前后快照。

Quartz 方面，`JobServiceImpl` 的任务 CRUD、状态变更和同步使用 Spring DB 事务并调用 `SchedulerManager`。Demo local/dev 使用 `LocalDataSourceJobStore`，未配置独立 non-transactional Quartz DataSource；Spring 的实现通过 `DataSourceUtils.doGetConnection` 获取事务连接，Spring Boot SchedulerFactoryBean 使用应用 DataSource。Quartz 表和 `infra_job` 均为 InnoDB。这些配置和连接实现支持 Quartz JDBC 更新参与当前 Spring 事务的判断，但没有隔离故障注入验证每个操作的实际回滚结果。当前 `yuheng` MySQL 账号仅有 `yuheng_demo.*` 授权，root 登录被拒，因此本轮没有创建隔离 schema 或运行注入；共享库、历史用户密码、Redis、服务进程和任务均未更改。

**当时状态：** 该段只记录静态源码和配置复核；写入时尚未进行文件/Quartz 故障注入。后续 2026-11-15 隔离运行记录已补充 DB/local 文件上传失败、本地文件删除失败和 Quartz create-job 回滚证据。FTP/SFTP/S3、批量删除及 Quartz 其它操作仍未完成。T4、T3、T1 与整体迁移继续开放。详细范围记录见 `service-write-audit-20261118/result.md`。

#### T1 当前 Core UI 包外消费续验

使用当前 Core 源码重新构建 `yuheng-ui@0.1.0-SNAPSHOT`，不是复用仓库旧 vendor tarball。Core 包构建（Vite 1466 模块及声明构建）、发布出口/包身份/迁移清单测试 10/10、包 boundary、manifest 和 bundle 检查均通过。新 tarball SHA-256 为 `1840c0433a51502796da817b7ba88d9abac858408752e624d2c903e0f559a72c`。

在 workspace 外建立独立 Demo UI 消费副本并安装该 tarball。安装后 `node_modules/.pnpm` 中包入口 SHA-256 与本次 Core build 和 tarball 内 `dist/index.js` 均为 `9a52da06117c7a95eb459d1008beb3d93b58df4903a9734bc37f14dded07e04e`。包外 consumer entry 和 ERP 测试 12/12；安装包路由探针确认 Login/Home 基础路由、System 用户/角色、Infra 配置/文件/任务路由以及兼容视图组件映射；consumer `vue-tsc --noEmit`、3544 模块生产构建和三个公共入口符号 ESM 导入均通过。正常 Demo 工作区的 `node_modules/yuheng-ui` 是 Core 源码符号链接，不作为包外消费证据。

固定 registry 仍未闭环：先前配置的私有 npm registry 查询返回 401，2026-11-15 后续对 `yuheng-ui@0.1.0-SNAPSHOT` 的查询返回 404，公共 npm 也返回 404；未执行发布。Core 开发态全目录 `vue-tsc --noEmit` 仍有 compat 旧式导入/AutoImport/类型错误，但支持的声明构建与独立消费者类型检查通过。以临时 `file:` manifest 执行完整 Demo 测试时有两项环境差异（固定版本字符串断言及仅适用于源码 symlink 的 AutoImport transform）；恢复固定版本文本后相关 consumer/ERP 12 项通过。详细记录见 `service-write-audit-20261118/result.md` 与 `ui-package-consumer-20261115.json`。

**状态：** 当前源码构建 tarball 的隔离消费、导出、路由、类型和生产构建子项完成；固定版本 registry 安装仍未验收，因此 T1 不关闭。T3 全页面/交互/响应式/Network/Console 及 T4 完整权限租户和故障矩阵仍未完成。

#### T4 多写方法调用链定向复核

重新沿当前 Core 调用链检查 188 项写方法索引中“没有方法级事务且直接含多次 Mapper 写入”的 14 项。除一个需要继续验证的跨资源路径外，其余主要是由事务 public entry 调用的 private helper、外层已有 `@DSTransactional` 的租户创建/权限关联，或单次 Mapper 写入；不能将索引的 `none` 直接算作缺陷。Codegen create/sync helper 由已标注 `@Transactional(rollbackFor=Exception.class)` 的入口调用；Demo03 两类子表 helper 由同类事务更新入口调用；用户岗位替换由事务 `updateUser` 调用；社交身份写入每次仅 insert 或 update 一行，bind 调用本身有事务；角色关联清理由事务删除入口调用。

需重点续验的路径是停用用户：`AdminUserServiceImpl.updateUserStatus` 先更新用户状态，再调用 `OAuth2TokenServiceImpl.removeAccessToken(userId,userType)`，而该批量重载逐一删 MySQL access/refresh token 行及 Redis 键，没有事务。失败可能造成状态更新或部分 token 撤销先完成、剩余 Redis/DB token 未处理。当前只有 `removeAccessToken(accessToken)` 单令牌重载有事务，不能覆盖批量调用链。该问题目前是源码风险判断，缺 Redis/SQL 故障注入及状态/令牌快照，未确认运行期是否可被部分失败触发。

**当时状态：** 该段记录 14 项调用链静态分类；批量停用用户风险和本地文件/Quartz 风险已有后续隔离故障注入证据，参见本记录后续对应小节与 `service-write-audit-20261118/result.md`。完整 T4 权限/租户/事务矩阵仍未完成。

#### 2026-11-15 T4 用户停用与 OAuth2 批量令牌撤销故障注入

使用当前 Demo JAR SHA-256 `e50bcf20ec4ca4157638393fcfd9730707bd7395e08a08296e5a9e2266da1e9f`，在专用 MySQL 8.0.33/Redis 容器、schema `yuheng_t4_disable_20261115` 和后端 48150 上运行，冷装 54 个 Liquibase changeset、150 张表。仅该进程启用随机隔离 mock 登录。测试主体、token、缓存及 `DEL` ACL 故障均只在容器内；没有访问共享数据库/Redis，也未读取或修改历史密码。

正常控制组调用真实停用接口返回业务码 0，用户变为禁用，两条 access/refresh token 均逻辑删除，4 个缓存键全部消失。故障组在专用 Redis 拒绝 `DEL` 后重复调用，接口返回业务码 500；SQL 显示用户仍已禁用，第一条 access token 已逻辑删除、该 refresh token 仍有效，第二条 access/refresh token 均仍有效，4 个 Redis 键全部保留。该注入证明 DB/Redis 跨资源失败可留下部分撤销状态，详见 `service-write-audit-20261118/user-disable-token-revocation-failure.json` 和审计结果文档。

隔离应用已优雅退出，本轮 MySQL/Redis 专用容器及其夹具均已停止并移除；共享数据库、共享 Redis、历史密码及既有服务未更改。此为已复现的 T4 问题，不据此推断其它 token 生命周期；T4 仍需确定并落实修复后回归，且完整权限/租户/事务矩阵未完成。T1 registry 固定版消费与 T3 全页面、交互、响应式、Network/Console 总验收仍开放。

随后将两个目标方法与原始 `ruoyi-vue-pro` checkout 逐段比较，方法体一致，因此这项非原子行为属于上游既有行为，不是本轮源码迁移遗漏。给 Core 简单增加 MySQL `@Transactional` 也无法让 Redis 删除具备原子性或自动恢复缓存；迁移验收据此保留上游行为并记录差异风险，不擅自引入产品行为变更。若后续要求修复，需另行定义 Redis 失败后的 API/重试契约，并以回归测试和隔离运行验证；本次未改 Core 源码。

#### 2026-11-15 T4 数据库文件上传元数据失败注入

使用当前 Demo JAR SHA-256 `e50bcf20ec4ca4157638393fcfd9730707bd7395e08a08296e5a9e2266da1e9f`，在独立 MySQL/Redis 容器、schema `yuheng_t4_file_20261115`、后端端口 48151 运行，Liquibase 冷装 54 个 changeset/150 张表。仅本隔离进程启用随机 mock 登录，并在临时 schema 将 DB 文件配置 ID 4 设为主配置。

仅对临时 schema 的 `infra_file` 元数据插入设置 `BEFORE INSERT` 失败触发器，经真实上传接口发送 37 字节文本后，API 返回业务码 500；数据库快照为 `infra_file=0`、`infra_file_content=1`、内容 37 字节，留下路径 `20261115/yh-t4-file-probe.txt` 的孤立内容。确认数据库文件内容写入先于元数据写入，且该调用链没有共同回滚。完整脱敏数据见 `service-write-audit-20261118/file-upload-db-metadata-failure.json`。

隔离应用已优雅关闭，专用 MySQL/Redis 容器及其数据已移除；共享库/缓存和历史密码未触碰。该证据仅覆盖 DB 文件客户端的一次上传失败，外部对象存储、删除失败与补偿仍未验收；T4、T1、T3 及整体迁移继续开放。

随后在新的隔离实例用本地文件客户端重复该上传失败注入。设置仅存在于隔离 schema 的 `infra_file` BEFORE INSERT 触发器后，真实上传接口返回业务码 500，元数据表为 0 行；隔离文件目录留下 34 字节 `20261115/yh-t4-local-probe.txt`（SHA-256 `25503219d4d3d37f251edb134d61efa67c7ce834bc77930347226a667b904590`）。这证明本地外部存储写入同样会先于元数据失败而保留。证据 `service-write-audit-20261118/file-upload-local-metadata-failure.json`。服务优雅停止，测试目录及专用容器已精确清理；FTP/SFTP/S3 和文件删除失败次序仍未覆盖，不能据此关闭文件存储全矩阵。

另一次删除故障探针的 fixture INSERT 因误写 `infra_file.tenant_id` 而失败，shell 链因此没有创建后续触发器；当时接口成功删除不能归因于触发器未覆盖 Mapper。该次仅为正常删除，不作为失败回滚证据。后续已在独立隔离实例先分别建立夹具和触发器、查询确认触发器存在，再成功复现下文所述删除不一致。

随后在新隔离实例重跑，先将触发器与隔离文件元数据夹具分别建立并查询确认触发器已存在。真实删除 API 返回业务码 500，32 字节测试文件（SHA-256 `e0e7f8619e88c88a4c8c8d263ad8cf22db06baea7095ba77603692f3c20e2bb0`）已被本地客户端删除，但 `infra_file` 中测试行仍为活动状态（`deleted=0`），确认“元数据有效但文件不存在”的反向不一致。证据 `service-write-audit-20261118/file-delete-local-metadata-failure.json`。应用优雅停止，专用容器与精确存储目录已清理；无共享资源被触碰。

#### 2026-11-15 T4 Quartz 任务创建事务回滚注入

在全新隔离 MySQL/Redis 容器与 schema `yuheng_t4_quartz_20261115` 启动当前 Demo JAR，Liquibase 冷装 54 changeset/150 表。为启用真实 JDBC JobStore，仅本进程覆盖 local profile 的 Quartz 自动配置排除项，并保持 `spring.quartz.auto-startup=false`，没有启动调度器或执行任何任务。共享数据库/缓存和历史密码未触碰。

在专用 schema 单独创建并查询确认 `QRTZ_JOB_DETAILS` BEFORE INSERT 触发器，然后经真实任务创建 API 使用有效种子处理器 `demoJob`。Quartz JobDetail 插入被拒，接口返回业务码 500；前序 `infra_job` 插入被 Spring 事务回滚，失败后 `infra_job`、`QRTZ_JOB_DETAILS`、`QRTZ_TRIGGERS` 均无该任务记录。证据 `service-write-audit-20261118/quartz-job-create-rollback.json`。应用优雅关闭，SchedulerFactoryBean 关闭前调度器未启动；专用容器已移除。

该结果关闭一次 Quartz 任务创建时 JDBC JobStore 失败的回滚子项，不覆盖更新、暂停/恢复、单删、批删、同步及并发行为；T4 完整事务矩阵、T1 固定版 registry 消费、T3 全页面与交互/响应式/Network/Console 验收仍未完成。

### T4 社交绑定主体静态续审

`SocialUserController` 的 bind/unbind/get-bind-list 不接收 userId/userType：绑定将当前 `getLoginUserId()` 与固定 ADMIN 类型写入 DTO，解绑和列表同样从登录态构造主体；外部身份来自 code/state 兑换出的 AuthUser。社交绑定 Service 对换绑执行有回滚事务，查询和解绑 Mapper 仍需连同 MyBatis 租户拦截器一起评估。后台社交用户详情/分页有 `system:social-user:query` 权限保护。该静态复核不覆盖第三方回调 state/code 重放、跨租户账号绑定竞争、已有绑定 before/after 快照、匿名/无权限 HTTP 请求或事务故障注入；这些运行证据仍缺，不能据代码路径关闭社交回调安全及关联租户矩阵。T4 继续开放。

### T4 匿名写入口全局认证矩阵（2026-11-17）

使用隔离 Demo JAR SHA-256 `61fba9414357444edbb929ca77a572c60659c7586e665a2c898e25fbd724fae6`、后端 48140、schema `yuheng_t4_auth_boundary_20261117`、专用账号 `yh_auth17`、Redis DB 14。启动前 schema/账号不存在，DB14 为 0 且无客户端、端口空闲；空库运行 54/54 changeset。无 Authorization token、带租户头的匿名请求覆盖站内信已读/全部已读、OAuth2 授权批准、个人资料/密码更新、社交 bind/unbind、文件登记共 8 个 JSON 写入口，以及 multipart 文件上传；所有请求均 HTTP 200、业务码 401“账号未登录”，未进入控制器输入校验或外部社交兑换。

请求前后相关 SQL 快照一致：`system_users=21`、`system_notify_message=95`、`system_oauth2_approve=0`、`system_social_user=0`、`infra_file=0`、`infra_file_content=0`。这证明全局认证过滤器阻止匿名写入，不证明已认证权限、OAuth2 用户主体隔离、社交 state/code 校验、跨租户账号竞争或对象存储故障语义。服务优雅退出后专用 schema/账号/grant、Redis DB14、48140 均复核归零；共享 `yuheng_demo` 保持 150 表，既有 PID 78090/88411 未触碰。完整逐端点记录见 `anonymous-write-auth-20261117/result.md`。

**状态：**关闭所列匿名认证子项；T4 认证用户权限与租户矩阵、OAuth2/社交运行期主体、事务异常回滚和 Quartz/对象存储故障注入仍开放。T1/T3 与整体迁移继续未完成。

### T3 角色菜单权限取消隔离续验

隔离 JAR SHA-256 `61fba9414357444edbb929ca77a572c60659c7586e665a2c898e25fbd724fae6`，取消验证后端 48134、Demo production UI 代理 5197、专用 schema `yuheng_t3_role_menu_20261116`、专用账号 `yh_rm16`、Redis DB 15。空库执行 54/54 已登记 changeset；该 JAR 早于 Core changeset 009，不作为最新 Core 版本消费证据。使用真实角色管理页面打开 role 2 菜单权限，展开树、选择 WebSocket 菜单 565 后点击“取消”。对话框关闭，完整 `system_role_menu` 行快照（按主键排序并包含 id、role_id、menu_id、tenant_id、deleted）前后均为 1552 行，SHA-256 都是 `2bafdca7517b45e920ee3d65671c2b6140985b9973eb755784f9135346d462ef`；目标关系活动行数仍为 0。

另起保存验证后端 48135、UI 代理 5198、schema `yuheng_t3_role_save_20261116` 和专用账号 `yh_rs16`。真实 UI 选择 WebSocket 并点击“确定”，页面显示“修改成功”；数据库出现活动关系 `(role_id=2, menu_id=565, tenant_id=1)`，ID 9127。该 schema 保存前后行数从 1552 增至 1556，新增 role 2 的 menu 12090、1894、1951 关系；完整前后快照已保留。多个旧关联发生软删除并被重建，符合服务按集合差异分配的实现形态。首轮取消快照来自不同且已删除的 schema，不能作为保存运行的同库行级基线；本轮新增三项的 entitlement 来源仍需在保存 schema 已删除后结合 changeset/menu/package 种子证据解释，不能据此宣称这三项一定由保存请求新添或是缺陷。保存后再次打开权限树时浏览器自动化超时，因此 GET 回读仍未验证。

两次隔离服务均已优雅停止，端口无监听；各自专用 schema/账号计数为 0；确认 DB 15 各次启动前为空且实例独占，两个实例结束后仅清空该 DB，最终为 0。共享实例与历史密码未改。子项状态为取消行为和保存写入已验证；新增额外关联的业务含义与读取回显仍待确认，不将此项标为整体通过。详细记录见 `role-menu-20261116/result.md`；T3/T4/T1 及全量迁移继续开放。

随后使用全新隔离 schema `yuheng_t3_role_api_20261116` 和后端 48136，只读调用 `GET /system/permission/list-role-menus?roleId=2`，返回 655 个角色菜单 ID，且不包含 WebSocket/额外三项；这是新 schema 的 API 基线，不能当作保存 schema 的回读。再起一个独立隔离 schema `yuheng_t3_role_api2_20261116` 和后端 48137，执行同库 API 集合契约：登录成功，GET 返回 655 个菜单 ID，POST 仅附加 565 后业务成功，紧接着 GET 返回 628 个 ID（含 565），相对提交前返回集合少 28 项；差异完整保存在 `role-menu-20261116/api-delta.json`，SQL post 快照为 `api-after.tsv`。后续追溯确认这 28 个 ID 全部不存在于 Core `system_menu` 种子，却在 005 中为 tenant 1 角色 1/2 各留下有效关联（共 56 行）；该探针为系统租户，其菜单可见集合不受普通套餐过滤。Core 新增 changeset 010 精确软删除这 56 条，隔离冷装、重跑、rollback 事务验证和清理证据见 Core `docs/verification/role-menu-seed-orphans/verification.md`。后续在含 Core 010 的隔离 Demo 版本完成真实 UI 保存后关闭并重新打开权限对话框：role 2 的 WebSocket 节点仍为 checked，GET 回读 HTTP 200，SQL 确认目标活动关联且 010 目标孤儿为 0。详见 `role-menu-reopen-20261116/result.md`。这只关闭该保存回读子项，不追认历史保存 schema 的全表差异，不关闭 T3/T1/T4。

### T4 Core System/Infra 服务事务审计基线

核查范围以 Core 当前源码路径为准：`yuheng-module-system/.../service/**/*ServiceImpl.java` 与 `yuheng-module-infra/.../service/**/*ServiceImpl.java`，共 49 个实现（System 34、Infra 15）。公开方法体静态扫描识别 413 个方法、162 个直接包含 Mapper 写调用的方法、32 个方法级 `@Transactional`/`@DSTransactional` 声明。扫描规则基于 Java 文本/花括号定位，只用于建立索引；重载、委托调用、接口默认方法、私有 helper、副作用调用和注解继承仍需结合源码逐项复核，因此这些数字不作为完成量或测试覆盖率。

已按真实调用顺序复核两个跨资源高风险路径：

- 文件上传 `FileServiceImpl.createFile(byte[], ...)` 先执行 `FileClient.upload`，再插入 `infra_file` 元数据；删除先执行对象/内容删除、再逻辑删除 `infra_file`，批量删除逐个删对象后最后批量更新元数据。Local/FTP/SFTP/S3 客户端的对象写入不是 MySQL 事务资源；DB 客户端则先写 `infra_file_content`，再由 FileService 写 `infra_file`，当前上传方法没有统一事务包住两次写入。故上传元数据写失败可能留下孤儿对象或孤儿内容行，批量删除中途失败可能形成部分对象已删而活动元数据保留。此处为源码顺序证据，尚无隔离对象客户端故障注入及逐表快照验收。
- `JobServiceImpl` 的 create/update/status/delete/bulk-delete 在 DB 写入与 `SchedulerManager` 调用之间使用普通 `@Transactional`；`syncJob` 在事务中逐条执行 Quartz delete/add/pause；立即触发只调用 Quartz。Demo local/dev 的 `LocalDataSourceJobStore` 使用应用 DataSource，Spring 实现通过 `DataSourceUtils` 获取事务连接，故 Quartz JDBC 更新可以参与当前事务。运行时事务回滚及 Scheduler 失败矩阵仍未通过隔离注入验证。

本轮没有修改 Core/Demo 运行代码，也没有对共享 DB、未知数据源进程或对象存储执行写入。已完成的是 49 个实现的范围基线及 File/Quartz 的顺序复核，不是 162 个 Mapper 写方法逐项完成审计；仍需逐方法核对调用链、事务代理自调用/异常类型、跨租户查询和批量失败前后状态，并在可控隔离依赖下针对文件写/删及 Quartz 同步各注入失败。T4 保持开放。

### T4 Core System/Infra Controller 与 Mapper 上游归一差异续审

使用本地 `ruoyi-vue-pro` 上游 Java 源码做相对路径匹配，并将完整业务包前缀 `cn.iocoder.yudao` 归一为 `com.yuheng.platform` 后逐文件比较。System 管理端 Controller 为 32/32、Infra 管理端 Controller 为 15/15；System MySQL Mapper 为 32/32、Infra MySQL Mapper 为 22/22。四组均无缺少文件、消费端额外文件或归一后内容差异（共 101 个文件）。脚本按实际文件内容比较，没有把普通作者注释以外的格式改写为通过；本次结果是完整文本一致。

这补足此前“仅 49 个 ServiceImpl 一致”的源码迁移证据，证明当前选定 Core System/Infra Controller 与 Mapper 的上游复制范围完整。它不证明 Java 之外资源、Mapper 拦截器动态运行语义、Controller 的允许/拒绝运行矩阵或所有事务副作用；特别是，已归一一致的上游行为仍包含前述跨租户目标 ID 不显式拒绝与集合替换行为，迁移一致性不能代替安全验收。T4 的方法级运行请求、全量写方法事务/异常回滚及 Quartz/对象存储故障注入继续开放；T1 固定版本 registry 安装消费及 T3 全页面/交互/响应式验收也继续开放。

### T4 Core System/Infra method-level write index (2026-11-18)

Using the sibling Core checkout's current `yuheng-module-system` and `yuheng-module-infra` service trees, a method-level index was generated at `service-write-audit-20261118/core-system-infra-write-methods.csv`. It contains 188 methods with direct Mapper/DAO calls named `insert*`, `update*`, `delete*`, `save*`, or `remove*`; 24 have a direct `@Transactional`/`@DSTransactional` declaration and 164 do not. This scan is an index, not a defect count: it does not infer class/interface annotations, follow helper calls, or establish runtime proxy/transaction behavior. It is broader than the older 162-method scan and must not be compared as a regression count.

The index makes several multi-write paths reviewable. Codegen public create/update/sync/delete methods and role-menu/user-role assignments do carry transactions; private Codegen helpers can appear unannotated while executing inside those public transactions. Two isolated failure injections now verify public transaction boundaries:

- `createCodegenList` inserted the parent table definition before a schema-local trigger rejected the child column batch. The request returned application code 500 and SQL snapshots showed `infra_codegen_table=0` and `infra_codegen_column=0` both before and after, confirming parent insert rollback. The isolated JAR used port 48141, a dedicated schema/account and a separate temporary Redis container.
- `assignRoleMenu` attempted to remove one existing role relation and add a new isolated menu relation; a schema-local insert trigger rejected the new relation. The HTTP response was application code 500 and the full 656-row role 2 relation snapshot was byte-identical before/after, proving deletion rollback. This test packaged the current Core checkout; the nested System module hash matched its Core build output.

These results verify only the two listed transaction paths. OAuth token/cache coordination, object storage and Quartz still need focused failure injection and snapshots. No controllable FileClient or Scheduler failure adapter was available in this continuation, so no object-store or Quartz runtime result is claimed. Detailed scope and evidence are recorded in `service-write-audit-20261118/result.md`, `codegen-create-rollback.json`, and `role-menu-rollback.json`.

**Status:** this closes only creation of the method-level navigation index. Core multi-write transaction behavior, OAuth/cache consistency, object storage, Quartz and full permission/tenant runtime matrices remain open. T1 registry installation and T3 full page/interaction/network/responsive coverage remain open; overall migration is not complete.

#### 2026-11-18 T4 跨租户岗位 ID 创建与更新续验

针对此前岗位测试被部门/权限前置校验挡住的问题，本轮使用当前 Demo JAR 的隔离运行实例重新验证。JAR SHA-256 为 `e50bcf20ec4ca4157638393fcfd9730707bd7395e08a08296e5a9e2266da1e9f`，其嵌套 Core System 模块与当前 Core 构建哈希一致。第一次隔离 MySQL 用户创建未持久化，应用启动报数据库拒绝连接；未发出 HTTP 请求，复核后 schema/账号均不存在。后续新 schema `yuheng_t4_postupdate_20261118` 冷启动成功，运行 54/54 changesets、150 张表，专用 Redis 初始 0 key，后端端口 48146、Quartz 自动启动关闭。

有效正向控制：租户 1 管理员在合法部门 100 下，以当前租户岗位 ID 2 创建用户成功；SQL 确认用户及岗位关联均为 `tenant_id=1`。随后仅在 disposable schema 插入一条有效且 `tenant_id=999` 的岗位。租户 1 管理员用同一合法部门和该外租户岗位分别创建用户及更新用户 1 的岗位，真实 API 均返回 HTTP 200 / 业务码 `1002005000`（`POST_NOT_FOUND`）。两个拒绝请求前后完整有序 `system_users`、`system_user_post` 快照均为 22/12 行，SHA-256 分别为 `a264eecafa547620ea36430aec104092c6cd6fc0bf4dd275c76fe716a0641e51`、`37cb46cac6242b44c2bd426efa4d2531a296267352109dada1b30cb2c2a788ce`；没有留下创建用户或错误关系。脱敏请求证据：`scripts/verification/user_post_tenant_boundary_probe.py` 与 `service-write-audit-20261118/user-post-tenant-boundary.json`。

隔离应用优雅退出后，schema/账号删除并核对为 0；专用 Redis 容器清理前有 9 个运行时 key，随后停止并移除；48146 及专用 Redis 端口均无监听。共享 `yuheng_demo`、历史用户密码、共享 Redis 与既有服务未改。

该证据关闭“用户创建和更新时拒绝外租户岗位 ID”子项；用户列表与岗位 CRUD 租户行为仍未覆盖。T4 的 OAuth2/社交认证主体、全量 Service 事务与异常回滚、Quartz/对象存储故障注入及其它 Controller 权限/租户矩阵继续开放；T3 全页面/交互/响应式/Network 覆盖与 T1 固定版 registry 消费继续开放，整体迁移未完成。

#### 2026-11-18 T4 岗位 API 跨租户可见性与写入边界

使用 Demo JAR SHA-256 `e50bcf20ec4ca4157638393fcfd9730707bd7395e08a08296e5a9e2266da1e9f`（嵌套 Core System SHA-256 `55115b0639ef5491567c360ce04b09e8829007be4348323ec63b2395a84c4b72`）启动隔离服务。schema `yuheng_t4_postapi_20261118` 从空库冷装 54 个 changeset，专用 DB 账号仅获该 schema 权限；后端端口 48147，Redis 使用绑定 127.0.0.1:16384 的独立密码保护容器。仅此隔离进程启用了 Core mock 登录，密钥为随机临时值；没有读取或修改历史密码。

在隔离库插入活动岗位 207（`tenant_id=999`），再以 tenant 1、user 1 调用真实接口：按唯一岗位编码查询分页返回 0 行；活动岗位简单列表 4 行且不含 207；详情接口返回 `data=null`；更新与删除均返回 `1002005000`（`POST_NOT_FOUND`）。请求后直接查表仍为 tenant 999 的活动原行（名称 `Foreign API post`、编码 `T4-XPOST`、排序 1），未被读取、更新或逻辑删除。脱敏证据 `service-write-audit-20261118/post-api-tenant-boundary.json`。

应用优雅退出后移除独立 Redis 容器（清理前 9 keys）、精确删除 schema 与 DB 账号；最终临时 schema/账号计数均为 0，共享 `yuheng_demo` 仍存在，48147/16384 无监听。该结果仅关闭列表、详情、更新、删除在一个外租户岗位夹具下的边界子项，不代表所有 Mapper 或全部权限矩阵。OAuth2/社交主体、全量事务/外部副作用故障注入和其它权限/租户组合仍未完成；T1、T3 与总体迁移继续开放。

#### 2026-11-18 T4 用户角色关系替换回滚注入

使用当前 Demo JAR（SHA-256 `e50bcf20ec4ca4157638393fcfd9730707bd7395e08a08296e5a9e2266da1e9f`，嵌套 Core System 哈希与当前 Core 构建一致），独立 Redis 容器初始 0 key，专用端口 48144。第一次失败注入误用物理 DELETE；实际 Mapper 对关联执行逻辑删除 UPDATE，故第一次请求成功并仅改了 disposable schema 的种子用户 2 角色关系。该轮未当作通过，服务停止后专用 schema 被销毁重建，恢复全新 54 changesets/150 表基线。

重跑中对 `system_user_role` 的 `BEFORE UPDATE` 逻辑删除步骤注入 SQLSTATE 45000。真实 `POST /admin-api/system/permission/assign-user-role` 在先插入替换角色后、更新删除旧角色时失败，返回 HTTP 200 / 业务码 500。整张 `system_user_role` 有序快照 23 行，前后 SHA-256 同为 `13dd30040092cabe756d07fb7ec766265ba769dcec5d130e6e681cceb2f558a4`；旧 role 2 关系仍有效，新 role 362 未留下，证明事务回滚了前序插入。探针与脱敏 JSON：`scripts/verification/user_role_assignment_rollback_probe.py`、`service-write-audit-20261118/user-role-assignment-rollback.json`。

重跑实例优雅退出；专用 schema 与账号删除后均为 0，独立 Redis 清理前 10 keys 且无应用客户端，容器已移除，48144/16382 无监听。该结果只覆盖一次用户角色集合替换回滚，不覆盖 Redis 缓存失效的分布式故障时序或全量写方法。T4、T3、T1 和整体迁移均保持开放。

#### 2026-11-19 T4 用户角色授权缓存即时可见性

在隔离 MySQL 8.0.33/schema `yuheng_t4_urcache_20261119`、schema-scoped 账号、独立 Redis 7.2.17 和后端 48175 上启动当前 Demo JAR；冷装 54/54 changesets、150 表。选择同一个 tenant 1 测试主体 90002；仅在临时 schema 为其建立角色关联夹具。角色 2 含 `system:role:query` 菜单权限。

分配前主体调用受保护的角色分页接口返回 HTTP 200/业务码 403，Redis `user_role_ids:90002` 缓存空集合。管理员真实调用 `POST /system/permission/assign-user-role` 分配角色 2 后，该 Redis key 立即不存在；同一主体下一次分页请求返回业务码 0，并重建缓存为 `[2]`。随后管理员提交空角色集合，SQL 活动关联归零、Redis key 再次立即清除；同一主体后续分页请求返回业务码 403 并缓存空集合。第一次探针把分配给 90002 的角色错误地拿 user 999999 做验权，明确排除；以上一致主体序列是有效证据。

脱敏结构化证据：`service-write-audit-20261118/user-role-cache-runtime.json`。隔离应用优雅关闭，专用 schema/账号与 MySQL/Redis 容器清理，48175/13342/16421 无监听；共享服务进程未变。该项关闭单租户顺序分配/移除后的 Redis 授权缓存可见性子项，不覆盖并发访问、Redis 故障或全量 T4 矩阵；T1/T3/T4 总体继续开放。

#### 2026-11-19 T4 单角色删除关联级联回滚

使用当前 Demo/Core 制品在隔离 MySQL 8.0.33/schema `yuheng_t4_roledel_20261119`、schema-scoped 用户、专用 Redis 7.2.17 和后端 48176 上运行；Liquibase 执行 54/54 changesets、150 表。首次请求删除角色 155 发生在触发器安装前，成功修改的仅是本轮 disposable schema；该尝试不作为回滚证据，记录见 JSON 中 `excluded_attempt`。

在全新种子中的活动自定义角色 162 上，查询确认有 2 条活动 `system_user_role` 和 3 条活动 `system_role_menu`。随后在专用 schema 安装并查询确认 `system_role_menu` BEFORE UPDATE 失败触发器，调用真实 `DELETE /admin-api/system/role/delete?id=162`。API 返回 HTTP 200/业务码 500。SQL 复核角色 162 仍活动，两条用户角色关联仍活动，三条角色菜单关联仍活动，证明角色软删和前序用户角色清理一并回滚。

结构化证据：`service-write-audit-20261118/role-delete-cascade-rollback.json`。隔离应用优雅关闭、精确 schema/账号和容器清理，48176/13343/16422 无监听，共享进程未变。该项仅覆盖一次单角色级联删除在菜单关系阶段失败的回滚；批量删除、成功后的缓存/级联可见性、并发和完整 T4 矩阵仍开放。

#### 2026-11-19 T4 批量角色删除级联回滚

当前 Demo JAR SHA-256 `e50bcf20ec4ca4157638393fcfd9730707bd7395e08a08296e5a9e2266da1e9f`（嵌套 Core System SHA-256 `55115b0639ef5491567c360ce04b09e8829007be4348323ec63b2395a84c4b72`）在隔离 MySQL 8.0.33/schema `yuheng_t4_rolebatch_20261119`、schema-scoped 用户、独立 Redis 7.2.17 和后端 48177 上运行；Liquibase 冷装 54/54 changesets、150 张表。成功正向对照通过真实 `DELETE /system/role/delete-list?ids=155&ids=162` 删除 disposable 种子角色及其关联，业务码 0。

随后插入并核验两个仅用于本轮的自定义角色 900101/900102、三条活动用户角色关系和三条活动菜单关系。在隔离 schema 安装并查询确认 `system_role_menu` BEFORE UPDATE 故障触发器后，真实调用 `DELETE /admin-api/system/role/delete-list?ids=900101&ids=900102`，接口返回 HTTP 200/业务码 500。请求后两个角色均未删除，三条用户角色关联和三条菜单关系均保持活动，ID、租户及目标关联值未变；批量角色软删及先行用户角色清理整体回滚。

结构化证据：`service-write-audit-20261118/role-batch-delete-rollback.json`。第一次成功对照只改动 disposable schema，后续回滚结论来自独立的明确夹具。应用优雅退出，临时 schema/账号和 MySQL/Redis 容器移除，48177/13344/16423 无监听；共享服务 PID 23945/39370 保持不变。该项关闭一次两角色批量删除在菜单关联阶段失败的回滚情形；并发、其它关联故障点及完整 T4 权限/事务矩阵仍未完成，T1/T3 也继续开放。

#### 2026-11-19 T4 租户套餐批量删除占用保护

当前 Demo JAR 在隔离 MySQL 8.0.33/schema `yuheng_t4_pkgdel_20261119` 与专用 schema 用户、独立 Redis 7.2.17、后端端口 48178 启动；Liquibase 执行 54/54 changesets、150 张表。基线 SQL 确认套餐 111 被活动租户 121、122 使用，套餐 113 未被租户使用。只在 disposable schema 新建未被引用的套餐 900114。

真实调用 `DELETE /admin-api/system/tenant-package/delete-list?ids=900114&ids=111` 返回 HTTP 200/业务码 `1002016001`（套餐正在使用）。请求后套餐 111 仍活动且两条租户引用未变；套餐 900114 也仍活动，证明批量校验在删除前整体拒绝，没有部分删除。随后单独删除未引用套餐 900114 返回业务码 0，该测试套餐软删；租户 121、122 对套餐 111 的引用保持不变。脱敏结构化证据：`service-write-audit-20261118/tenant-package-delete-guard.json`。

隔离应用优雅退出，精确 schema/账号及容器已删除，48178/13345/16424 无监听，共享 PID 23945/39370 未变。该证据关闭套餐占用拒绝和一个混合批量请求原子拒绝子项；并发变更竞争、其它套餐/租户 CRUD 和全量 T4 矩阵仍开放，T1/T3 亦未完成。

#### 2026-11-19 T4 租户套餐更新跨租户角色菜单事务

当前 Demo JAR 在隔离 MySQL 8.0.33/schema `yuheng_t4_pkgupd_20261119`、schema 限定用户、独立 Redis 7.2.17、后端 48179 上运行；Liquibase 首装 54/54 changesets、150 张表。套餐 111 由租户 121、122 使用，管理员角色分别为 109、111；更新前活动菜单关联行分别为 292、257，有序合并全表快照为 549 行，SHA-256 `9586f3f4d6d2c9ab3b8685c6a59fa9f1a65ce3513b8c01353bd94792ef7c64cc`。

在仅对 role 111 生效的 `system_role_menu` BEFORE UPDATE 失败触发器已查询确认后，真实调用套餐更新 API，将菜单改为 `[1,2,3]` 并修改备注。接口返回业务码 500；套餐备注和原菜单 JSON 保持原值，role 109/111 的所有 549 条关联快照哈希仍完全相同，证明第二租户处理失败时套餐更新和第一租户已完成的关联调整一并回滚。删除触发器后重复提交成功，套餐菜单集合更新为 `[1,2,3]`，两个租户管理员角色均只剩 3 条对应活动菜单，越界菜单活动数为 0。结构化证据：`service-write-audit-20261118/tenant-package-update-rollback.json`。

隔离应用优雅退出，schema/账号与 MySQL/Redis 容器移除，48179/13346/16425 无监听，共享 PID 23945/39370 未变。该证据关闭顺序处理两个租户时的单次成功传播及第二租户 SQL 失败整体回滚子项；并发套餐变更、缓存可见性和其它租户 CRUD/隔离组合仍开放，T1/T3/T4 总体继续开放。

#### 2026-11-16 T4 用户更新岗位关联回滚注入

隔离 Demo 实例使用专用 MySQL/Redis、端口 48182，Liquibase 冷装 54 changesets、150 张表。正向准备将用户 1 昵称设为 `T4PreTrigger`、岗位设为 2；确认 `system_user_post` 的 BEFORE UPDATE 失败触发器后，真实用户更新请求尝试修改昵称、备注并替换为岗位 4，返回业务码 500。请求前后用户相关字段及该用户全部岗位关系快照 SHA-256 均为 `4906044249d093eb00b573d15b8a92b39271914679ca34f8511e0ad08a187303`；SQL 确认昵称和岗位 2 保留，岗位 4 无活动关联。证据见 `service-write-audit-20261118/user-post-update-relation-rollback.json`。

触发器已删除且复核为 0；应用优雅退出，专用 schema、账号及两个容器已删除，48182/13351/16431 无监听。该结果只覆盖一次关系替换失败的数据库回滚；其它更新和并发路径、T4 全矩阵以及 T1/T3 继续开放。

#### 2026-11-18 T4 用户创建岗位关联事务回滚注入

使用当前 Demo JAR 和当前 Core System 嵌套模块，在全新隔离 schema `yuheng_t4_usercreate_20261118`、专用 Redis 容器初始 0 key、端口 48145 上执行验证；Liquibase 54/54 changesets、150 张表，Quartz 自动启动关闭。针对 `system_user_post` 安装仅存在于临时 schema 的 `BEFORE INSERT` 失败触发器，真实租户 1 管理员调用 `POST /admin-api/system/user/create` 创建带合法部门 100、同租户岗位 2 的用户。触发器在用户主表已插入后拒绝岗位关系写入，API 返回 HTTP 200 / 业务码 500；完整有序快照前后相同：`system_users` 21 行 SHA-256 `f990b133f112fba47a5754397e38d8ffd3fdea7c141b02a0ad78279e8b8f6c17`，`system_user_post` 11 行 SHA-256 `0618c46b2832c1237ffcf41def3ced4f5be85d3caa88920a56f2c757d23159e5`，测试用户名不存在。详见 `service-write-audit-20261118/user-create-relation-rollback.json` 和探针 `scripts/verification/user_create_relation_rollback_probe.py`。

隔离应用优雅退出；专用 schema 和账号删除后为 0，Redis 运行产生 7 keys 且无应用连接后移除容器，48145/16383 无监听。该证据关闭用户创建主表+岗位关系在关系插入失败时的 DB 回滚子项，不覆盖消息事件外部副作用、其它更新/删除/导入路径。T4/T3/T1 及整体迁移仍未完成。

#### 2026-11-18 T4 Quartz 同步及单任务删除回滚注入

当前 Demo JAR SHA-256 `e50bcf20ec4ca4157638393fcfd9730707bd7395e08a08296e5a9e2266da1e9f` 运行在 `dev` profile、后端 48156，使用一次性 MySQL 8.0.33 容器/专用 schema `yuheng_t4_qtzdel_20261118`/schema-scoped account 与独立 Redis 7.2 容器。冷启动执行 54/54 Liquibase changesets、150 张表；Quartz JDBC Scheduler 已初始化，自动启动关闭，无任务执行。首次验证确认 local profile 会显式排除 Quartz，故使用未排除 Quartz 的 dev profile；全局 demo 写保护关闭、仅本隔离进程使用 Core mock admin 身份。此前无效参数尝试没有创建任务或改动任务数据，不计入验收。专用 SQL trigger 在各注入前已查询确认存在。

先经真实 `POST /admin-api/infra/job/sync` 成功建立 33 个 JobDetail/Trigger，作为非空 Quartz 基线；然后 BEFORE INSERT on `QRTZ_JOB_DETAILS` 注入重复同步失败。接口 HTTP 200/业务码 500，日志确认 SQL 标记 `T4_QUARTZ_SYNC_RETRY_INJECTED`。`infra_job`、`QRTZ_JOB_DETAILS`、`QRTZ_TRIGGERS` 与 `QRTZ_CRON_TRIGGERS` 的排序全字段快照哈希前后同为 `32aba5390b42b26c155e021a7e1217e226fa1f4c36b0ba070bf78aec56c363e1`，行数仍为业务任务 33、JobDetail 33、Trigger 33。

保持相同基线，再对 `QRTZ_JOB_DETAILS` BEFORE DELETE 注入 `T4_QUARTZ_DELETE_INJECTED`，调用真实 `DELETE /admin-api/infra/job/delete?id=33`。接口业务码 500，业务任务 ID 33 保持活动且状态 2，匹配 JobDetail/Trigger 均仍存在；相同四表全字段快照哈希保持不变。结构化证据分别为 `service-write-audit-20261118/quartz-sync-rollback.json`、`quartz-delete-rollback.json`。

结束时应用与 Quartz 均优雅关闭；专用 schema/account 删除后复核为 0，两个专用容器及临时凭据文件已移除，48156/13324/16395 无监听；共享 MySQL/Redis 继续运行且未被用于本测试。该证据关闭重复同步与单任务删除失败注入两个子项，不覆盖更新、暂停/恢复、批量删除、同步并发及 Quartz 成功后业务库提交失败。T4 全矩阵、T3 与 T1 仍未完成。

#### 2026-11-18 T4 Quartz 任务状态变更回滚注入

在独立 MySQL/Redis 容器、schema `yuheng_t4_qtzstatus_20261118`、专用账号与后端 48157 上启动当前 Demo JAR（SHA-256 `e50bcf20ec4ca4157638393fcfd9730707bd7395e08a08296e5a9e2266da1e9f`）。`dev` profile 冷装 54/54 changesets、150 张表并初始化 JDBC Quartz；自动执行关闭，mock admin 仅用于本轮。

真实正向接口 `PUT /admin-api/infra/job/update-status?id=33&status=1` 返回业务码 0，任务状态为 1，Quartz Trigger 为 `WAITING`。随后在隔离 schema 建立并查询确认 `QRTZ_TRIGGERS` BEFORE UPDATE 失败触发器，调用同一接口改为 status 2。请求返回业务码 500，服务日志确认注入 SQL marker `T4_QUARTZ_PAUSE_INJECTED`；数据库中 `infra_job` 仍为 status 1 且未删除，Quartz Trigger 仍为 `WAITING`/`CRON`，即之前业务状态 UPDATE 已回滚。证据见 `service-write-audit-20261118/quartz-status-rollback.json`。

应用与 Quartz 优雅关闭；专用 schema/账号删除并核对为 0，容器及临时凭据删除，48157/13325/16396 无监听。没有使用共享数据库、缓存或历史密码。本项关闭一次成功启用状态转换和一次暂停失败回滚，不外推至恢复失败、更新任务 reschedule、批量删除或并发操作；T4 全范围、T1 固定版本消费和 T3 完整浏览器验收继续开放。

同轮尝试 `PUT /admin-api/infra/job/update` 的故障注入未建立有效验收：首个触发器设在 `QRTZ_CRON_TRIGGERS UPDATE`，但 Quartz reschedule 实际删除并重建 trigger，因此请求成功；后续任务状态夹具没有满足 Service 的“仅允许开启任务修改”条件，接口返回业务码 `1001001004`，注入 marker 未命中。该尝试明确排除为失败回滚证据，隔离服务/schema/账号/容器/凭据和端口均已清理。更新任务与 Quartz reschedule 一致性仍未验证；详见 `service-write-audit-20261118/result.md`。

#### 2026-11-18 T4 Quartz 批量删除事务回滚注入

在全新隔离 MySQL 8.0.33/Redis 7.2 容器、schema `yuheng_t4_qtzbatch_20261118`、专用 DB 用户及后端端口 48160 启动当前 Demo JAR（SHA-256 `e50bcf20ec4ca4157638393fcfd9730707bd7395e08a08296e5a9e2266da1e9f`）。`dev` profile 冷装 54/54 changesets、150 张表，Quartz JDBC Scheduler 初始化且自动任务执行关闭；mock 登录仅用于隔离进程。先调用真实 sync API 成功同步 33 个种子任务，并确认 ID 27 `jobLogCleanJob` 与 ID 33 `demoJob` 均为活动业务记录、Quartz JobDetail/Trigger/Cron 记录完整且 Trigger 为 PAUSED。

在隔离 schema 建立并查询确认 `QRTZ_JOB_DETAILS` BEFORE DELETE 失败触发器后，调用 `DELETE /admin-api/infra/job/delete-list?ids=27&ids=33`。API 返回 HTTP 200/业务码 500，日志确认 SQL marker `T4_QUARTZ_BATCH_DELETE_INJECTED`。覆盖所有 `infra_job` 行及 Quartz JobDetail、Trigger、Cron 表的排序全字段快照哈希前后相同：`0ea71dc3dfabded4dda73beb7a2371fd98f3e7dd018fe387f25f1876bc431eec`；两条业务行均未删除，两个 JobDetail 和 PAUSED Trigger 均保留。结构化证据为 `service-write-audit-20261118/quartz-batch-delete-rollback.json`。

隔离应用及 Quartz 优雅关闭；专用 schema/账号删除后核对为 0，两个本轮容器与临时凭据已移除，48160/13328/16399 无监听；共享 MySQL、Redis 和历史密码未动。该证据只关闭两条任务的一个批量删除失败回滚场景；`updateJob`/reschedule、恢复状态、并发和 Quartz 成功后提交失败仍开放，T4 总矩阵、T1 固定包安装和 T3 全页面浏览器验收继续开放。

#### 2026-11-18 T4 Quartz 恢复任务回滚注入

在全新隔离 MySQL 8.0.33/Redis 7.2 容器、schema `yuheng_t4_qtzresume_20261118`、专用用户及后端 48161 启动当前 Demo JAR（SHA-256 `e50bcf20ec4ca4157638393fcfd9730707bd7395e08a08296e5a9e2266da1e9f`）。`dev` profile 冷装 54/54 changesets、150 张表，Quartz JDBC Scheduler 初始化但不自动执行任务；mock 身份只用于本隔离进程。真实 sync 后先成功启用再暂停 job 33，确认业务状态 2、JobDetail 存在、cron Trigger 为 `PAUSED`。

在隔离 schema 建立并查询确认 `QRTZ_TRIGGERS` BEFORE UPDATE 失败触发器后，调用真实 `PUT /admin-api/infra/job/update-status?id=33&status=1`。接口 HTTP 200/业务码 500，服务异常日志确认 `T4_QUARTZ_RESUME_TRIGGER_INJECTED`，失败点为 `SchedulerManager.resumeJob` 的 `resumeTrigger`。SQL 显示业务任务仍为状态 2 且未删除，Quartz JobDetail 保留、Trigger 仍是 `PAUSED`，证明前序业务状态更新和 Quartz 恢复操作一并回滚。结构化证据见 `service-write-audit-20261118/quartz-resume-rollback.json`。

应用和 Quartz 优雅退出；专用 schema/账号删除后核查为 0，容器与临时凭据移除，48161/13329/16400 无监听；共享 MySQL/Redis 和历史密码未动。本项仅关闭一次恢复失败回滚场景；`updateJob`/reschedule、并发和 Quartz 成功后业务库提交失败仍开放，T4 全矩阵与 T1/T3 全范围验收继续开放。

#### 2026-11-18 T4 角色菜单替换事务回滚

当前 `PermissionServiceImpl.assignRoleMenu` 的事务实现先插入新菜单关联，再软删除旧关联。本轮使用隔离 Demo/Core 临时制品，在 `yuheng_t4_role_menu_20261115` 的 `system_role_menu` 上建立并确认 `BEFORE UPDATE` 失败触发器，真实调用 `POST /admin-api/system/permission/assign-role-menu`，以角色 2 将菜单集合替换为仅菜单 566。删除旧关联阶段按预期返回 HTTP 200/业务码 500；有序全表 `id,role_id,menu_id,tenant_id,deleted` 快照前后均为 1552 行、SHA-256 `feb737488c053c4bba1cf65d60258c2d724d30a74b4ac12ab79df2d50513271c`，先前插入的新关联也未残留，证明替换事务整体回滚。隔离账号、schema、Redis/MySQL 专用容器与 48172/33317/16377 端口均已清理并复核；共享服务、共享库和历史口令未动。

该结果关闭角色菜单替换在“插入后删除失败”这一事务回滚子项；插入阶段失败、缓存可见性、并发替换、更多角色/租户及完整 T4 权限/事务矩阵仍开放。详见 `service-write-audit-20261118/result.md` 与 `service-write-audit-20261118/role-menu-assignment-rollback.json`。

#### 2026-11-19 T4 角色数据范围写入与部门归属边界

使用当前 Demo JAR（SHA-256 `e50bcf20ec4ca4157638393fcfd9730707bd7395e08a08296e5a9e2266da1e9f`，嵌套 Core System JAR 与当前 Core 构建一致）在端口 48174 启动。MySQL 8.0.33 专用容器/schema `yuheng_t4_dscope_20261119`、仅授权该 schema 的账号和独立 Redis 7.2.17 容器端口 16420；Liquibase 执行 54/54 changeset、创建 150 张表。仅该进程启用 mock 身份，没有读取或修改历史用户密码，也未使用共享 MySQL/Redis。

真实调用 `POST /admin-api/system/permission/assign-role-data-scope` 将 tenant 1 自定义角色 155 设为自定义范围并赋部门 `[100,102,103]`，返回业务码 0；SQL JSON 值和角色详情 API 回读一致。随后在隔离 schema 为 `system_role` 安装并确认 BEFORE UPDATE 失败触发器，重试变更后 API 返回业务码 500，角色的数据范围、部门 JSON、租户和删除状态完整保持原值。移除触发器后，再提交外租户部门 110（tenant 121）和不存在部门 999999，接口仍返回 0，SQL 将两者都持久化在 tenant 1 的角色 155 上。

结构化证据：`service-write-audit-20261118/role-data-scope-runtime.json`。与本地 `ruoyi-vue-pro` checkout 对应 `updateRoleDataScope` 的方法体和注解归一比较一致，因此部门 ID 校验缺失属于该对照方法继承行为，不认定为迁移差异，也未擅改业务契约。源码有 `@CacheEvict`，但隔离 mock 调用未建立目标角色缓存命中，故缓存实际可见性/失效不记通过。应用优雅关闭；精确 schema/账号及两个隔离容器删除，48174/13341/16420 无监听；共享 PID 23945/39370 和共享服务保持不变。该项关闭合法范围持久化和单次 SQL 失败不改行两个子项；运行期缓存失效及完整 T4 仍开放。

#### 2026-11-19 T4 部门创建/更新的父部门租户边界

在专用 MySQL schema `yuheng_t4_deptparent_20261119`、schema-scoped 账号及独立 Redis 端口 16426 上复用隔离 Demo JAR，后端仅绑定 48180，Liquibase 已执行 53 个 changeset。仅隔离进程启用 mock 身份。插入活动父部门 900199（tenant 999）作为外租户夹具。

以 tenant 1 调用真实创建接口：同租户父部门 100 返回业务码 0 并创建测试部门 900200；外租户父部门 900199 返回 `1002004001`“父级部门不存在”，没有创建对应行。随后同租户更新将 900200 改挂到部门 101 成功；改挂到 900199 被同一业务码拒绝。最终 SQL 中 900199 仍为活动 tenant 999 行，900200 仍为活动 tenant 1 行且 `parent_id=101`、名称/排序/状态均保持已成功更新值，拒绝请求无行变更。

结构化响应与 SQL 证据：`dept-parent-tenant-boundary-20261119.json`。共享服务、共享数据库、Redis 和历史密码均未使用或改动。该结果关闭一个活动跨租户父部门在 create/update 两个入口的拒绝与非变更子项；禁用/删除父部门、循环引用、其它租户组合与完整部门权限矩阵仍开放，不能替代 T4 总验收。

#### 2026-11-15 T4 角色数据范围缓存失效

使用独立 MySQL schema `yuheng_t4_rolecache_20261119`、schema-scoped 账号、独立 Redis 和后端 48181 冷启动当前 Demo JAR，Liquibase 首次执行 54/54 changesets、150 张表。仅隔离进程启用 mock 身份；未使用共享库或共享 Redis。

tenant 1 用户 100 经真实 `GET /admin-api/system/user/profile/get` 读取关联角色 155，确认 Redis `role:1:155` 已缓存旧部门集合 `[112,100,102,103,104,105,107,108]`。管理员真实调用 `POST /admin-api/system/permission/assign-role-data-scope` 将部门范围更新为 `[100,102,103]`，业务码为 0。请求后 Redis `EXISTS role:1:155` 为 0，SQL 行保存新集合；再次读取用户资料后，该 key 重新存在且其中集合为 `[100,102,103]`。这证明缓存命中、`@CacheEvict` 运行失效及后续按新数据库值重载形成闭环。

结构化证据：`service-write-audit-20261118/role-data-scope-cache-runtime.json`。首次无租户头登录与不具备缓存调用的角色详情 API 均排除，不计入通过。隔离服务优雅退出后精确删除 schema/账号并核验为 0，两个专用容器移除，48181/13350/16430 已释放。该项只证明一个租户、角色、用户和顺序请求；并发与 Redis 故障、其它缓存键和 T4 总矩阵仍开放。

#### 2026-11-15 T4 文件批量删除中途失败

在专用 MySQL/Redis 容器、schema `yuheng_t4_filebatch2_20261118`、schema-scoped 用户、独立本地存储目录和后端端口 48163 上运行当前 Demo JAR。Liquibase 冷装 54/54 changesets、150 张表；未使用共享数据库或 Redis。查询确认 `selectByIds` 返回 ID 2332 在前、2333 在后：2332 指向 config 29 下真实存在的 341 字节本地对象，2333 指向不存在的 config 999999。调用真实 `DELETE /admin-api/infra/file/delete-list?ids=2332&ids=2333` 返回 HTTP 200/业务码 500。首个对象已被删除；第二条记录解析客户端时报错，故批量逻辑删除尚未执行，两个 `infra_file` 行均保持活动状态。对象删除前 SHA-256 为 `5ded57e79c3addb883ea2587e4268f08aa3811b6050f98139f3ada265804b36d`。结构化证据见 `service-write-audit-20261118/file-batch-delete-partial-failure.json`。

应用优雅退出；专用 schema/账号删除并核验为 0，容器、凭据和存储目录已清理，48163/13331/16402 无监听；共享 MySQL/Redis 仍运行且未修改。该证据确认文件批删在客户端失败时可能留下活动元数据指向已删除对象的部分状态；本项没有实现补偿语义。其它对象存储后端、重试/补偿设计及 T4 其余矩阵仍开放；T1 固定版 registry 消费与 T3 完整前端验收继续开放，整体迁移未完成。

#### 2026-11-15 T4 Quartz 更新任务重排回滚注入

在专用 MySQL/Redis 容器与 schema `yuheng_t4_qtzupdate_20261115` 中以当前 Demo JAR 冷启动，Liquibase 54/54、150 表，后端端口 48164，Quartz JDBC JobStore 已初始化但自动执行关闭。对 ID 33 `demoJob` 先执行成功的任务同步和状态启用，确认业务状态为 1、Quartz Trigger 为 `WAITING`，满足更新前置条件。

在 schema 内建立并查询确认 `QRTZ_CRON_TRIGGERS` BEFORE INSERT 触发器（`T4_QUARTZ_UPDATE_RESCHEDULE_INJECTED`）。真实 `PUT /admin-api/infra/job/update` 将任务名、参数、cron、重试次数和间隔改为测试值；Quartz `rescheduleJob` 删除旧 Trigger 后插入 CronTrigger 时触发失败。接口返回 HTTP 200/业务码 500，服务日志命中 marker。失败后直接 SQL 核对 `infra_job` 的名称、handler 参数、cron、重试、监控值、状态和删除标记均与请求前相同；原 JobDetail 保留，Trigger 仍为 `WAITING`，原 Cron、时区及 fire time 仍在。结构化证据见 `service-write-audit-20261118/quartz-update-reschedule-rollback.json`。

应用与 Quartz 优雅退出；专用 schema/账号删除并核验为 0，容器、临时凭据及日志已清理，48164/13332/16403 无监听；共享 MySQL/Redis 仍运行且未修改。该证据关闭一次 Quartz 更新重排过程中 cron 插入失败的回滚子项，不覆盖并发调度及 Quartz 成功变更后业务库提交失败；T4 其余方法矩阵和 T1/T3 全范围继续开放。

#### 2026-11-15 T4 Codegen 父子记录删除事务回滚

在隔离 schema `yuheng_t4_codegenupdate_20261115`、专用数据库账号/Redis 容器及后端 48165 上运行当前 Demo JAR，Liquibase 执行 54 changesets、150 表。插入并查询确认活动父表记录 900020 和两条字段记录 900021/900022；在专用 schema 建立并查询确认 `infra_codegen_column` BEFORE UPDATE 失败触发器。调用真实 `DELETE /admin-api/infra/codegen/delete?tableId=900020` 返回 HTTP 200/业务码 500，日志确认字段 Mapper UPDATE 触发 marker `T4_CODEGEN_DELETE_COLUMN_INJECTED`。失败后 SQL 确认父表和两条字段记录仍活动且行数未变，证明父表先前逻辑删除已由事务回滚。结构化证据见 `service-write-audit-20261118/codegen-delete-rollback.json`。

隔离应用优雅退出；schema/账号删除并核验为 0，容器/凭据已清理，48165/13333/16404 无监听；共享 MySQL/Redis 未修改。两次 `create-list` 前置尝试因加密数据源密码格式及 Generator 辅助连接缺少密码而未进入 Codegen 写入，明确排除在证据外。该项只关闭 Codegen 单表删除时父子逻辑删除回滚场景；创建、更新、同步、批删的其它故障条件及 T4 全方法矩阵、T1/T3 全范围仍开放。

#### 2026-11-15 T4 Codegen 父子记录更新事务回滚

使用全新隔离 schema `yuheng_t4_codegenupdate2_20261115`、专用数据库账号、独立 Redis 和后端 48166 冷启动当前 Demo JAR；Liquibase 54/54 changesets、150 表。直接在隔离库插入并查询确认父行 910020 和两条活动字段 910021/910022 的原始目标值，随后安装并查询确认 `infra_codegen_column` BEFORE UPDATE 注入触发器。真实 `PUT /admin-api/infra/codegen/update` 请求修改父表说明/备注/类说明和两个字段说明，返回 HTTP 200/业务码 500；服务日志命中字段 `updateById` 失败。SQL 复核父行所有目标字段及两条子字段的说明/排序/删除状态均保持请求前值，证明父表先行 UPDATE 和此前子行操作都处于同一回滚事务。结构化证据：`service-write-audit-20261118/codegen-update-rollback.json`。

应用优雅退出；精确 schema/账号删除并核验为 0，专用容器、凭据和请求输出已移除，48166/13334/16405 无监听；共享 MySQL/Redis 未改。该项关闭一次 Codegen 父子更新失败回滚场景；同步与批量删除的失败路径以及 T4 其它服务矩阵、T1/T3 全范围仍开放。

#### 2026-11-15 T4 Codegen 批量父子记录删除回滚

使用隔离 schema `yuheng_t4_codegenbatch_20261115`、专用数据库账号与 Redis 容器、后端 48167 冷启动当前 Demo JAR，Liquibase 执行 54 changesets/150 表。直接插入并查询确认父记录 920020、920030 和四条活动字段；安装并查询确认 `infra_codegen_column` BEFORE UPDATE 触发器后，调用真实 `DELETE /admin-api/infra/codegen/delete-list?tableIds=920020&tableIds=920030`。API 返回 HTTP 200/业务码 500，日志命中 `T4_CODEGEN_BATCH_DELETE_INJECTED`；失败后 SQL 确认两条父记录和四条字段均保持 `deleted=0`，总行数与请求前相同。父表批量逻辑删除因此由事务整体回滚。结构化证据：`service-write-audit-20261118/codegen-batch-delete-rollback.json`。

隔离应用/Quartz 优雅退出；精确 schema/账号删除并核验为 0，容器和临时凭据已清理，48167/13335/16406 无监听；共享 MySQL/Redis 未改变。该项关闭一次 Codegen 批量删除的父子回滚场景；同步路径、其它 T4 方法级事务/权限/租户矩阵，以及 T1/T3 全范围仍开放。

#### 2026-11-15 T4 Codegen 批量父子记录删除回滚

使用隔离 schema `yuheng_t4_codegenbatch_20261115`、专用数据库账号与 Redis 容器、后端 48167 冷启动当前 Demo JAR，Liquibase 执行 54 changesets/150 表。直接插入并查询确认父记录 920020、920030 和四条活动字段；安装并查询确认 `infra_codegen_column` BEFORE UPDATE 触发器后，调用真实 `DELETE /admin-api/infra/codegen/delete-list?tableIds=920020&tableIds=920030`。API 返回 HTTP 200/业务码 500，日志命中 `T4_CODEGEN_BATCH_DELETE_INJECTED`；失败后 SQL 确认两条父记录和四条字段均保持 `deleted=0`，总行数与请求前相同。父表批量逻辑删除因此由事务整体回滚。结构化证据：`service-write-audit-20261118/codegen-batch-delete-rollback.json`。

隔离应用/Quartz 优雅退出；精确 schema/账号删除并核验为 0，容器和临时凭据已清理，48167/13335/16406 无监听；共享 MySQL/Redis 未改变。该项关闭一次 Codegen 批量删除的父子回滚场景；同步路径、其它 T4 方法级事务/权限/租户矩阵，以及 T1/T3 全范围仍开放。

#### 2026-11-15 T4 OAuth2 撤销 Redis/SQL 失败顺序

当前 Demo JAR SHA-256 `e50bcf20ec4ca4157638393fcfd9730707bd7395e08a08296e5a9e2266da1e9f` 在专用 MySQL 8.0.33 和 Redis 7.2 容器运行，schema `yuheng_t4_oauthorder_20261118`、端口 48168/13336/16407。schema-scoped DB 账号仅授权该 schema；Liquibase 冷装 54/54 changesets、150 表；Redis DB 0 启动时 0 keys。共享 MySQL/Redis 与既有服务未用于探针。

经真实 OAuth `client_credentials` API 生成 token，并由真实 check-token API 将合法 JSON 记录加载到 access/refresh 两个 Redis key。对临时 schema 的 refresh-token 逻辑删除安装并查询确认 BEFORE UPDATE 失败触发器后，真实 `DELETE /admin-api/system/oauth2/token` 返回 HTTP 200/业务码 500，服务日志命中 `T4_OAUTH_REFRESH_DELETE_INJECTED`。数据库事务回滚后 access 与 refresh 两行仍为活动状态；Redis 中两个 key 均已删除。脱敏结构化结果：`service-write-audit-20261118/oauth-revocation-redis-order.json`。

第一次尝试使用非 JSON 占位 Redis 值，API 在 token lookup 阶段即失败，没有命中触发器；明确排除为失败顺序证据。之后清除占位值，通过真实 check-token API 建立有效缓存并重跑。应用优雅关闭后随专用 MySQL 容器销毁隔离 schema/账号及数据；Redis 容器移除；48168/13336/16407 无监听。共享 MySQL/Redis、48080/5173 服务和历史用户密码保持原状。

该运行证据确认当前 OAuth 撤销实现存在 MySQL/Redis 非原子窗口：刷新 token SQL 失败会回滚数据库，但已经完成的 Redis 删除不会恢复。本次仅记录迁移审计证据，未改变继承自上游的行为。它不覆盖 Redis 删除异常、refresh-token 过期清理、并发撤销及 OAuth 全方法矩阵；T4、T3、T1 与全量迁移继续开放。

#### 2026-11-15 T4 OAuth2 过期 refresh token 清理

在专用 MySQL/Redis 容器和隔离 schema `yuheng_t4_oauthexp_20261115` 中运行当前 Demo JAR SHA-256 `e50bcf20ec4ca4157638393fcfd9730707bd7395e08a08296e5a9e2266da1e9f`，后端端口 48169，数据库端口 13337，Redis 端口 16408。Liquibase 冷装 54/54 changesets、150 表，Redis 启动时为空。默认种子 OAuth client 没有可用密钥且改密后仍命中旧缓存；这些设置尝试均排除。之后只在临时 schema 建立独立 client，经真实 client-credentials API 生成 token pair，把 refresh row 过期时间设为过去，并通过真实 check-token API 为两个 Redis key 填充有效 token JSON。

真实 refresh-token API 返回 HTTP 200/业务码 401“刷新令牌已过期”；随后 SQL 中旧 access/refresh token 均为逻辑删除，Redis 两个 key 均不存在。这与 `@Transactional(noRollbackFor = ServiceException.class)` 一致：预期过期异常不回滚已执行的令牌清理。脱敏证据：`service-write-audit-20261118/oauth-expired-refresh-token.json`。

应用优雅关闭，专用 MySQL/Redis 容器已删除，临时 schema、账号、客户端、token 和缓存随之销毁；48169/13337/16408 无监听。共享数据、缓存、进程和历史密码未触碰。该证据关闭一个客户端、一个租户的过期刷新清理子项，不覆盖并发 refresh/revoke、刷新期间 Redis 失败、其它用户类型或完整 OAuth 流程。T4、T3、T1 与全量迁移继续开放。

#### 2026-11-15 OAuth token 生命周期源码逐方法续审与 refresh Redis 故障探针排除

对 Core `OAuth2TokenServiceImpl` 的 `createAccessToken`、`refreshAccessToken`、`getAccessToken`、`checkAccessToken`、两个 `removeAccessToken` 重载和 `getAccessTokenPage`，以及 `AdminUserServiceImpl.updateUserStatus`，与本地原始 `ruoyi-vue-pro` checkout（commit `128a0e3bd3847d11b7f2f9e169dd36fce3b0b581`）对应方法体逐个归一比较。包名、`jakarta`/`javax` 导入及注释/空白归一后，所列方法均一致。此前已记录的令牌撤销和停用用户非原子失败行为因此属于上游既有行为；本次不改产品契约或 Core 业务源码。

本轮另启动专用 refresh-token Redis 故障探针，但多次 ACL 注入/恢复与同一长期运行的 Redisson 连接交织，且同一 refresh token 被重试和后续成功刷新复用，无法形成干净的单请求基线与状态快照。因此该运行整体排除，不把其中任一响应或数据库状态记为验收通过；隔离应用已优雅关闭，MySQL/Redis 专用容器及其 schema、账号、keyspace 已销毁，48170/13338/16409 无监听。共享 MySQL/Redis、48080/5173 及历史密码未触碰。后续若重做此故障项，应使用全新 schema/token，并以 Redis 代理对一次目标 DEL 注入失败，避免动态改 ACL 对连接池的持续影响；在获得干净证据前，刷新期间 Redis 失败分支仍开放。

#### 2026-11-15 Core System/Infra `src/main` 全文件源码对照

新增可复跑审计脚本 `scripts/verification/source_parity_audit.py`，默认对照当前 `../yuheng-core` 与 `../ruoyi-vue-pro` 两个干净 checkout；完整逐文件哈希和差异清单见 `core-system-infra-source-parity.json`。System 共 472 个文件（419 Java、53 资源），Infra 共 317 个文件（205 Java、112 资源）；规范化包路径、Java namespace/注释/空白、BOM 和换行后，路径集合完全相同且内容差异为 0。

本项关闭 Core System/Infra 两个 `src/main` 树的静态文件迁移对照，不覆盖 POM、bootstrap 配置、其它模块、运行行为、权限/租户/事务语义、Liquibase 或浏览器验收；T4 总矩阵及 T1/T3 全范围继续开放。详见 `service-write-audit-20261118/result.md` 的 “Core System/Infra full main-source parity audit”。

#### 2026-11-18 ERP/会员模板到 Demo 源码完整性对照

新增可复跑脚本 `scripts/verification/business_template_parity_audit.py`，将模板 Java、ERP MyBatis XML、前端页面和 API 分层映射至 Demo 消费端；数据库 Liquibase、README、HTTP 示例和其它辅助资产单独报告，不混入运行源码差异。完整逐文件哈希和差异列表见 `business-template-source-parity.json`。

当前模板与 Demo 对应运行源码路径集合完全一致：ERP 305/305 文件、会员 227/227 文件均无模板独有或消费端独有的运行源码。ERP 217 个 Java 文件、会员 185 个 Java 文件，以及 ERP 2 个统计 Mapper XML，经业务包名、Java 注释/空白、换行和 Jakarta/Javax 规范化后内容一致。模板自带 SQL 迁移分别为 ERP 4 个文件（含 changelog）和会员 2 个文件（含 changelog），由独立模块迁移流程治理，不视为 Demo 运行源码副本缺失。

前端内容并非字节/规范化等价：ERP 23 个 API 文件和会员 10 个 API 文件将请求实例从模板相对别名切换到 `yuheng-ui/compat/config/axios`；所列差异需结合 Core 运行时消费验收，不能作为原样复制。页面的差异主要是 strict TypeScript 类型注解/断言；会员详情页另将 tagsView store 改接 `yuheng-ui/compat/store/modules/tagsView`。审计因此报告 `DIFF`，而不是把导入适配误写成完全相同；此静态对照也不替代 T3 的逐页面、交互、浏览器 Network/Console 和响应式验收。

验证：审计脚本重跑产生相同分类；Python `py_compile`、JSON 解析和 `git diff --check` 通过。模板仓库 `python3 -m unittest tests.test_template_migrations tests.test_template_resources tests.test_schema_contract -v` 为 46/46 通过；Demo UI Vitest 为 3 文件、14/14 通过。Demo UI `vue-tsc --noEmit` 未通过：当前安装环境缺少已声明的 `@iconify/vue`、`@iconify/json`、`echarts`、`lodash-es` 依赖；Vitest 的 Vite 依赖扫描也报告相同模块无法预打包。没有运行包管理器安装或改动锁文件，因此该类型检查保持未验证，不归类为源码类型错误或通过。

本项关闭 ERP/会员模板运行源码的文件路径完整性子项，并确认后端内容迁移一致；前端 Core 适配差异及运行态页面验收仍开放。它不证明 SQL 草稿完整/生产可用，也不关闭 T1 固定版本 registry 消费、T3 全量 UI 或 T4 全量权限/租户/事务矩阵。

#### 2026-11-15 T1/T3 当前环境只读快照

再次查询固定版本 `yuheng-ui@0.1.0-SNAPSHOT`：配置的私有 npm group registry 返回 404，公共 registry 也返回 404；没有发布或改变包版本。现有 Demo UI PID 39370 在 5173 返回 HTTP 200；共享后端 PID 23945 在 48080 的权限信息 API 探测 3 秒超时。MySQL/Redis 容器均为 healthy。本轮未重启/停止后端、未发写请求、未访问或改动共享数据库及历史密码。结构化状态见 `current-state-20261115.json`。该快照更新当前阻塞事实，不关闭 T1 或 T3；固定制品发布/干净消费和完整浏览器验收仍待完成。
## 2026-11-20 T4 岗位分页权限运行验收

使用当前 Demo JAR（SHA-256 `e50bcf20ec4ca4157638393fcfd9730707bd7395e08a08296e5a9e2266da1e9f`）在全新隔离 MySQL/Redis 和 schema `yuheng_t4_postpage_20261120` 中运行真实登录探针。专用端口为 MySQL 13350、Redis 16430、后端 48185；Liquibase 冷装完成后仅在隔离库创建两个临时用户、一个角色和 `system:post:query` 关系，未读取或修改共享库及历史密码。

`GET /admin-api/system/post/page` 的匿名请求返回 HTTP 200、业务码 401；无权限真实登录用户返回 HTTP 200、业务码 403，拒绝前后的 `system_post` 完整有序快照一致；只授予 `system:post:query` 的真实用户返回 HTTP 200、业务码 0，返回 4 条岗位、总数 4。结构化证据见 `controller-security-inventory-20261119/post-page-permission-runtime.json`，探针为 `scripts/verification/post_page_permission_probe.py`。

探针结束后应用优雅关闭，专用容器、schema、临时用户和端口均已清理，`cleanup.containers_absent=true` 且 13350/16430/48185 均无监听。该结果关闭岗位分页端点的匿名认证、无权限拒绝和精确查询权限放行子项；不代表全部 Controller、跨租户组合或 T4 总体验收完成。

## 2026-11-20 Demo/Core UI 构建链复核

本轮未运行会触发 workspace 安装的 pnpm 命令。Demo UI 的现有本地依赖链接恢复后，直接执行本地二进制得到：`vue-tsc --noEmit` 通过，Vitest 为 3 个文件/14 项通过，平台导入边界检查通过，Vite 生产构建转换 3673 个模块并退出 0。构建保留既有大 chunk 与插件耗时提示。

Core UI 的公开入口 `package.json` 声明 `exports["."].types=./dist/index.d.ts`。一次并行执行 Vite 与声明构建时，Vite 清理 `dist` 后暂时移除了声明文件，Demo 类型检查因此报告入口缺少声明；按正式串行顺序重新执行 `vue-tsc -p tsconfig.build.json` 后生成 `dist/index.d.ts`（1102 字节），Demo `vue-tsc --noEmit` 随即通过。该结果证明消费端声明解析正常，也记录了验证顺序约束；不等同于固定坐标 `yuheng-ui@0.1.0-SNAPSHOT` 已发布到 registry。workspace lockfile 仍记录 Demo 对 Core 的 `workspace:*` 链接，T1 registry 发布与干净安装保持开放。

## 2026-11-20 T4 OAuth2 令牌生命周期运行验收

使用当前 Demo JAR（SHA-256 `e50bcf20ec4ca4157638393fcfd9730707bd7395e08a08296e5a9e2266da1e9f`）在全新隔离 MySQL/Redis 和 schema `yuheng_t4_oauthtoken_20261120` 中运行真实 OAuth2 HTTP 探针。专用端口为 MySQL 13349、Redis 16429、后端 48184；冷装完成 54 个 Liquibase changeset 后，仅在隔离库创建随机 OAuth2 客户端，客户端密钥未写入证据，历史用户密码未读取或修改。

错误客户端密钥的 `client_credentials` 请求返回 HTTP 200、业务码 `1002020006`；正确密钥发放访问令牌和刷新令牌，数据库各有 1 条活动记录，访问令牌 Redis key 存在，`check-token` 返回业务码 0。使用同一刷新令牌刷新后，旧 access token 的校验返回 401，新 access token 返回 0，刷新令牌保持不变，旧 Redis key 消失、新 key 存在。撤销新 access token 后，访问令牌和刷新令牌活动记录均为 0，Redis key 消失，再次校验返回 401。

结构化证据见 `service-write-audit-20261118/oauth-token-lifecycle-runtime.json`，复跑入口为 `scripts/verification/oauth_token_lifecycle_probe.py`。应用优雅关闭，专用容器已移除，13349/16429/48184 均无监听。该结果关闭一个客户端、一个租户下的 OAuth2 错误密钥、发放、校验、刷新和撤销生命周期子项；不覆盖授权码/密码模式、多客户端并发、Redis 删除失败、跨租户令牌组合及完整 OAuth2 事务矩阵，T4 总项仍开放。

## 2026-11-20 T4 OAuth2 密码与授权码模式及授权码绑定修复

本轮先用旧 Demo JAR 在隔离 schema `yuheng_t4_oauthgrants_20261120` 中执行红灯探针：密码模式和授权码成功兑换可用，但错误 `redirect_uri` 返回业务码 `1002021001`、错误 `state` 返回 `1002021002` 后，授权码行已被删除。根因是 Core `OAuth2GrantServiceImpl` 先调用会删除授权码的服务，再校验 client、redirect URI 和 state；错误参数会因此消耗授权码。

Core 修复为：`OAuth2CodeServiceImpl` 通过 `selectOneForUpdate` 锁定授权码，`OAuth2GrantServiceImpl.grantAuthorizationCodeForAccessToken` 在事务中完成 client/redirect URI/state 全部校验，校验成功后才删除授权码并创建访问令牌。新增 `OAuth2GrantServiceImplTest` 3 项契约测试，分别验证错误 redirect、错误 state 不调用删除，以及所有绑定匹配后才消费；Core 指定测试 3/3 通过，Core 离线安装流程中的既有测试 51/51 通过。

修复后的 Demo JAR SHA-256 为 `5e632e65db0af402c43c2e8823601c11a03cfe60b01d738af52dd042384283ef`。在同一隔离探针中使用当前 Core 001–010 共 56 个 changeset，创建一次性临时用户和 OAuth2 client：password grant 返回业务码 0 且 token 主体为用户 990202；授权申请返回业务码 0 且 state 原样回传；错误 redirect 和错误 state 均被拒绝且各自 `code_row_remaining=1`；合法授权码兑换返回业务码 0 并只消费该合法授权码；同一授权码 replay 返回业务码 `1002022000`。最终隔离容器、schema、临时数据和 13356/16436/48191 端口均清理，应用优雅关闭。结构化证据为 `service-write-audit-20261118/oauth-grant-modes-runtime.json`，复跑入口为 `scripts/verification/oauth_grant_modes_probe.py`。

该结果关闭 OAuth2 password grant、authorization-code grant 的限定运行子项，以及错误 redirect/state 不应消费授权码的迁移缺口；不覆盖多客户端并发、Redis 故障、社交回调、跨租户 token 组合和完整 OAuth2 事务矩阵。T1、T3、T4 总项仍开放。

## 2026-11-20 T4 OAuth2 授权码并发消费

使用当前 Demo JAR（SHA-256 `5e632e65db0af402c43c2e8823601c11a03cfe60b01d738af52dd042384283ef`）在全新隔离 MySQL/Redis 和 schema `yuheng_t4_oauthconcurrency_20261120` 中运行真实授权码探针。专用端口为 MySQL 13357、Redis 16437、后端 48194；Liquibase 冷装完成 56 个 changeset。临时用户和 OAuth2 客户端只存在于本轮 schema，未读取或修改共享数据库、共享 Redis 或历史用户密码。

先通过真实登录和授权接口申请一个授权码，再使用同一 `code`、正确 `redirect_uri`、正确 `state` 并发发送 8 个 token exchange 请求。8 个请求中恰好 1 个返回业务码 `0`，其余 7 个返回 `1002022000`（授权码不存在或已消费）；SQL 复核显示活动 access token 1 条、活动 refresh token 1 条、授权码 0 条。日志同时确认授权码读取使用 `SELECT ... FOR UPDATE`。结构化证据见 `service-write-audit-20261118/oauth-grant-concurrency-runtime.json`，探针为 `scripts/verification/oauth_grant_concurrency_probe.py`。

随后申请第二个授权码，以错误 `redirect_uri` 兑换，返回 `1002021001`；请求前后活动 token 行均为 access=1、refresh=1、code=1，目标授权码仍为 1 行，证明错误绑定不会消费授权码或创建 token。应用优雅关闭，schema/临时凭据随隔离容器销毁，13357/16437/48194 均无监听。

该结果关闭一个租户、一个客户端、单授权码 8 路并发消费及错误绑定无 token 创建的运行子项；不覆盖多实例并发、跨租户令牌组合、Redis 故障、社交回调和完整 OAuth2 事务矩阵。T4 总项及 T1/T3 全范围继续开放。

## 2026-11-20 T4 角色精简列表认证、启用状态与租户隔离

在独立 MySQL 8.0.33/Redis 7.2.17 容器中冷启动当前 Demo JAR，隔离 schema 为 `yuheng_t4_rolelist_20261120`，后端、MySQL、Redis 端口分别为 48197、13360、16440；Liquibase 执行 56/56 changeset。探针为 `scripts/verification/role_simple_list_security_probe.py`，结构化证据为 `controller-security-inventory-20261119/role-simple-list-runtime.json`。

匿名 `GET /admin-api/system/role/simple-list` 返回业务码 `401`。tenant 121 临时用户通过真实登录取得 token，绑定仅用于数据范围的隔离角色后，接口返回 tenant 121 的两个启用角色；tenant 122 的启用角色不出现，tenant 121 的禁用角色也不出现。将同一 token 的请求头改为 `tenant-id: 122` 返回 `403`。应用 SQL 日志确认实际查询包含 `system_role ... tenant_id = 121`，角色表所有行的所选字段有序快照前后不变；该快照不覆盖所有列。

隔离应用优雅关闭；临时 MySQL/Redis 容器已删除，48197/13360/16440 均无监听。历史用户密码、共享数据库和共享 Redis 未使用或修改。该结果关闭角色精简列表的匿名认证、启用状态过滤、租户查询范围及伪造租户头子项；不覆盖角色分页/写入、数据权限范围组合、并发及完整 Controller/Mapper/T4 矩阵，T4 总项与 T1/T3 全范围继续开放。

## 2026-11-20 T4 字典类型精简列表认证与平台共享契约

在独立 MySQL 8.0.33/Redis 7.2.17 容器中冷启动当前 Demo JAR，隔离 schema 为 `yuheng_t4_dicttypelist_20261120`，后端、MySQL、Redis 端口分别为 48198、13361、16441；Liquibase 执行 56/56 changeset。探针为 `scripts/verification/dict_type_simple_list_security_probe.py`，结构化证据为 `controller-security-inventory-20261119/dict-type-simple-list-runtime.json`。

匿名 `GET /admin-api/system/dict-type/simple-list` 返回业务码 `401`。tenant 121 和 tenant 122 的临时用户分别通过真实登录取得 token，两次请求返回相同的两个共享字典类型夹具；禁用状态的字典类型也按 Controller 契约保留。两次完整响应未逐行比较。`DictTypeDO` 显式标注 `@TenantIgnore`，SQL 日志确认查询只包含 `deleted = 0`，没有错误追加 `tenant_id` 条件；字典类型表所有行的所选字段有序快照前后不变，不覆盖所有列。

隔离应用优雅关闭；临时 MySQL/Redis 容器已删除，48198/13361/16441 均无监听。历史用户密码、共享数据库和共享 Redis 未使用或修改。该结果关闭字典类型精简列表的匿名认证、共享数据跨租户可见性、禁用项契约和只读子项；不覆盖字典类型权限写入、字典数据联动、并发及完整 Controller/Mapper/T4 矩阵，T4 总项与 T1/T3 全范围继续开放。

## 2026-11-20 T4 字典数据精简列表认证、状态过滤与平台共享契约

在独立 MySQL 8.0.33/Redis 7.2.17 容器中冷启动当前 Demo JAR，隔离 schema 为 `yuheng_t4_dictdatalist_20261120`，后端、MySQL、Redis 端口分别为 48199、13362、16442；Liquibase 执行 56/56 changeset。探针为 `scripts/verification/dict_data_simple_list_security_probe.py`，结构化证据为 `controller-security-inventory-20261119/dict-data-simple-list-runtime.json`。

匿名 `GET /admin-api/system/dict-data/simple-list` 返回业务码 `401`。tenant 121 和 tenant 122 的临时用户分别通过真实登录取得 token，两次请求返回相同的两个启用字典数据夹具，分别属于两个 `dict_type`；禁用夹具和逻辑删除夹具均未返回，两次完整响应未逐行比较。`DictDataDO` 显式标注 `@TenantIgnore`，应用 SQL 日志确认查询为 `deleted = 0 AND (status = ?)`，相邻绑定参数均为 `0(Integer)`，没有追加 `tenant_id` 条件；字典数据表所有行的所选字段有序快照经替换解码后前后一致，不能证明所有列或非法字节逐字节不变。

本轮首次运行因历史种子中存在非法 UTF-8 字节而在探针快照解码阶段退出，第二次运行已完成业务请求但初版断言错误地要求预编译 SQL 直接出现 `status = 0`；两次均未计入产品验收。修正探针后完整重跑通过，专用应用优雅关闭，临时 MySQL/Redis 容器已删除，48199/13362/16442 均无监听。历史用户密码、共享数据库和共享 Redis 未使用或修改。该结果关闭字典数据精简列表的匿名认证、启用/删除状态过滤、平台共享读取和只读子项；不覆盖字典数据写入、类型联动、并发及完整 Controller/Mapper/T4 矩阵，T4 总项与 T1/T3 全范围继续开放。

### T4 OAuth2 refresh-token Redis 删除失败复验

使用当前可执行 Demo JAR（SHA-256 `5e632e65db0af402c43c2e8823601c11a03cfe60b01d738af52dd042384283ef`）在全新隔离 MySQL/Redis 和 schema `yuheng_t4_oauthrefreshredisfail_20261120` 中启动应用，后端端口 48200，MySQL 13363，Redis 16443；Redis 16444 为只转发的临时 RESP 代理。Liquibase 冷装完成后，仅在隔离库创建随机 OAuth client，通过真实 `client_credentials` 和 `check-token` 请求建立有效 access/refresh 记录及两个 Redis key。

代理在刷新请求前才 armed，并只对下一条包含 `oauth2_access_token:<access-token>` 的 `DEL` 返回一次 `T4_REFRESH_REDIS_DELETE_INJECTED`，没有修改 Redis ACL 或复用受污染连接池。真实 `refresh_token` 请求返回 HTTP 200、业务码 500，代理记录命中一次目标 `DEL`。请求前后 SQL 活动 access/refresh 行均为 1/1，两个预先存在的 Redis key 均保持存在，证明 MySQL 事务回滚且本次注入发生在 Redis 删除实际生效之前；没有把该结果误写成跨存储补偿或全流程原子性证明。

结构化证据与可复跑探针分别为 `service-write-audit-20261118/oauth-refresh-redis-failure.json` 和 `scripts/verification/oauth_refresh_redis_failure_probe.py`。应用优雅关闭，临时容器/schema/账号和 13363/16443/16444/48200 均清理归零；共享 MySQL、Redis、既有服务和历史密码未触碰。该证据关闭“单次 Redis 删除失败导致 refresh 请求状态不可归因”的验证缺口，但不覆盖 Redis 连接中断、删除成功后数据库提交失败、多实例并发 refresh/revoke、其它 userType 或完整 OAuth2/T4 矩阵；T1、T3、T4 总项继续开放。

## 角色新增弹窗窄屏初查

使用 `role-dialog-mobile/preview/` 在 5312 端口挂载当前 Core 源码中的 `RoleForm`、Dialog 和 Element Plus，使用内存请求适配器，不连接后端或数据库。浏览器设置 390×844 后，实际 `innerWidth` 和 `documentElement.clientWidth` 均为 582px；不能将该轮作为 390px 验收。稳定后实际角色弹窗宽约 232.84px（视口的 40%），角色名称输入框宽约 68.87px；取消后内存写入计数仍为 0。测量表明即使实际视口为 582px，默认百分比宽度也造成输入空间偏窄。

本轮未修改 Core 表单，未验证 320/390px 的真实视口、输入和提交行为，也未将隔离预览视作完整 Demo 页面验收。后续需在支持准确视口的浏览器环境重现并完成红绿验证，覆盖桌面宽度和取消行为后再决定局部修复。T1/T3/T4 总项继续开放。

### 角色弹窗准确视口复验与局部修复

使用 Chrome 的实际视口控制继续上述隔离源码预览。修复前实测 `innerWidth=390`，弹窗宽 156px，角色名称输入宽 0；这是默认 40% 宽度与表单标签和内边距共同造成的空间不足。Core `RoleForm.vue` 局部采用配置表单已有的 `min(100%, max(40%, 400px))` 宽度，不改变共享 Dialog 的默认值。

修复后 `innerWidth=390` 时弹窗宽 390px、输入宽 226px，填写名称并取消后内存写入计数为 0；`innerWidth=320` 时弹窗宽 320px、输入宽 156px、页脚按钮右边界为 304px，名称可填写并取消；`innerWidth=1440` 时弹窗宽 576px（40%）、输入宽 412px。320px 取消后经页面重载才观察到计数为 0，因此不将其作为独立取消无写的强证据。上述为内存适配器下的真实组件预览，不覆盖完整 Demo、真实 API 提交、其它表单或所有交互。

Core UI Vitest 29 文件、125 项通过（必填校验测试输出预期的 async-validator stderr）；边界检查通过，Vite 生产构建和 `vue-tsc -p tsconfig.build.json` 声明生成退出 0。标准 `vue-tsc --noEmit` 退出 2，报告大量 compat 类型问题，包括 TS5097、缺少自动导入符号及 TSX 配置等；尚未完成独立基线对照，不能声称标准类型检查通过或将全部错误归因于本次改动。浏览器视口已恢复，预览服务停止；未访问共享数据库、Redis 或历史用户密码。T1/T3/T4 总项继续开放。

### 当前 Core 包的离线消费复核

在 Core 提交 `576e83004cb7d0c1d5431ae93404c9b1fdb38f07` 上重新执行生产构建、声明构建和 `npm pack --ignore-scripts`，生成 `yuheng-ui@0.1.0-SNAPSHOT` tarball，SHA-256 为 `d8b098e5acb3e74e014013969c128b1581dfe8846e0f4f4e62ae972b391c6d0b`。在独立临时目录使用 npm 离线安装后，读取包 manifest 确认为 `yuheng-ui@0.1.0-SNAPSHOT`，公共入口 `installYuhengUi`、`registerPlatformRoutes` 和 `YuhengShell` 均成功解析；安装包中的 `RoleForm.vue` SHA-256 为 `e4d1db2553dcb7cb7dc1024ddbaa4a58aa8eb07496d01e7a2925acaf3045c2b1`，并确认包含 `min(100%, max(40%, 400px))`。

机器可读证据：`ui-package-consumer-20261120-role-dialog.json`。这证明当前提交可以形成并被独立消费者离线安装的版本化包，也证明本次角色修复进入包内容；配置的私有 registry 仍返回 401，公共 registry 仍返回 404，未发布或伪造固定坐标消费，因此 T1 registry 子项继续开放。临时包和消费者目录位于 `/tmp`，未修改 Demo workspace、共享数据库、Redis 或历史密码。


### 2026-11-18 P1 跟踪 UI 制品一致性与最终 JAR 复验

沿用 `YH-20261111-full-source-migration`，code `0.1.0-SNAPSHOT` / governance `0.2.0` / knowledge `0.1.0`；按用户既有完整实施和 P1 优先验证授权继续。Core 源码基线 `836125c`；其旧跟踪 tarball `125b85…` 未包含已提交的 Menu/ConfigForm/RoleForm 修复。旧包构建的角色页在 390/320px 鼠标视口被系统菜单浮层拦截。临时 defaultOpeneds 源码改动无效，已撤回；输入方式不是充分根因。Core 新增发布包逐文件一致性检查，旧包红灯列出上述三个文件，最终包绿灯。

从相同 Core 源码重建的 tarball 为 `7d5adb2d1a27e0c68956ed64646dd1850adb733fb0e3b5467ff6adff0d9dcebc`。Core UI 30 文件/126 项测试、导入边界、Vite 和声明构建通过；默认 `vue-tsc --noEmit` 仍失败，不能计为通过。Demo 构建脚本修复 Maven 子模块工作目录下相对 `YUHENG_UI_PACKAGE` 的解析；Python 测试 36 项、29 通过/7 跳过，新增路径回归先红后绿。Demo 固定 tarball 临时消费者类型检查和 3544 模块构建、612 静态资源 JAR 打包通过；额外独立消费者 14 项测试和平台导入边界通过。测试装包时临时 file: manifest 使固定版本断言失败，恢复原始 manifest 后通过，不称为 registry 安装。

最终 JAR SHA-256 `9a7b8fa44a02a2d42da0da98b518018a7c1c2f2e5e83d15711bd5afac156dcbd`。`python3 scripts/verification/role_page_browser_runner.py` 退出 0：1440×900、390×844、320×844 鼠标和 390×844、320×844 触摸共五场景真实登录、表格加载、新增打开/填写/取消通过，无角色写请求，无 console/page/request 错误；桌面折叠菜单悬停/重新展开通过。`python3 scripts/verification/p1_platform_probe.py` 退出 0：同一 JAR 完成 56 changesets 冷装及重启，21 个种子用户密码不变，用户角色 CRUD/授权、权限拒绝、文件下载、任务查询与启停脚本通过。独立容器和端口均已清理，共享库和历史密码未触碰。

证据：`p1-fixed-package-20261117/p1-build-20261118.json`、`platform-runtime.json`，及 `role-page-collapse-desktop-20261117/result.json`/`browser.json`。截图继续保留本地未提交。P1 浏览器 runner 现于启动前逐文件校验 JAR 与 dist 的 612 项资源完全一致。Demo Python 测试 38 项、31 通过/7 跳过，含资源不匹配拒绝和匹配放行回归。P1 本地 tarball 闭环通过，固定 registry 坐标安装和独立锁文件仍缺失，因此 P1 总项继续进行中；全量 T1/T3/T4 和 P2/P3 不外推为完成。

### 2026-11-21 Member 与 ERP 模板 Liquibase 隔离验收

Member 和 ERP 的模板迁移在专用容器 `codex-qc-schema-mysql`、映射端口 `51045` 的一次性 schema 中按正式 Liquibase formatted SQL 执行。未连接共享 `yuheng_demo`、本机 `mysql8` 或历史用户数据；测试 schema 在验证后删除。

Member 模板入口冷装成功，执行 14 个 changeset；同一 changelog 再次执行没有新增 changeset。构造原历史 `(mobile, tenant_id)` 复合唯一索引后应用 `002-member-mobile-uniqueness.sql`，旧索引被移除，新 `uk_tenant_mobile_active` 生效。两个空手机号可共存；同租户不同活动手机号可用，活动重复被唯一键拒绝；逻辑删除后同手机号可重新使用，不同租户可使用相同手机号。通过保留用户邮箱长度 51 的历史夹具验证 preflight HALT：Liquibase 退出失败，旧索引仍存在、`active_mobile_marker` 未创建、changeset 未记录，会员行保持原样。验证发现旧索引前置条件曾按索引列计数，复合索引导致删除步骤误标 `MARK_RAN`；现改为按索引名去重计数。模板与 Demo 增量 SQL 相同，SHA-256 `1b8f6da037f75dae86f3cc258a90dd2a62a1046c3c72f34e85f099e4dc019f2e`。

ERP 模板入口冷装成功，执行 35 个 changeset 并创建 33 张 ERP 表；重启后仍为 35。`erp_product.unit_id` 最终为 bigint。库存约束拒绝同租户、同商品和仓库的重复活动行，允许逻辑删除后重建，也允许不同租户各自维护记录。插入历史重复库存后单独执行唯一性 changeset，Liquibase 按 precondition HALT，`active_marker` 未创建、changeset 未记账、原数据未修改。模板与 Demo 的三份 ERP SQL SHA-256 一致：`001` `3eb5c0e2111ee393900e14051fc17106c3b623c4a984349ea1f0681dd6a2c368`、`002` `c310693d0d53cbff0cb9664d4430e0d704e3de438b2c390657572c0f6997a642`、`003` `068b4f16a1e020fb81e96ec7c02a1c9cea1693807271bb58ad959cd5358497f5`。

模板迁移/资源/Schema 合约测试 47 项通过；Demo Python 脚本测试 39 项，32 项通过、7 项因需要外部服务跳过、0 失败。Core 模板迁移 Skill 已同步至 Demo，治理同步 `--verify` 通过。Member/ERP 的 SQL 验收通过不替代 Demo HTTP/API 业务流程验收；下一项是隔离环境中 ERP 主单、明细、库存、状态流转和失败回滚的端到端验证。

### 2026-11-21 当前分支按 Skill 重新初始化 ERP/Member

按用户指示直接在当前 Demo 分支验证，不创建 worktree。执行前将现有模块后端、前端及迁移文件备份到本机临时目录 `/tmp/yuheng-demo-module-sync-backup-20261121`；分别移除 Demo 中 ERP/Member 后端源码目录、前端 API/页面目录和模块迁移目录，再从 `yuheng-business-templates/template-erp` 与 `template-member` 初始化。模板源码包名归一为 `com.yuheng.demo.module.<module>`，`jakarta` 按当前 Demo Core 版本适配；ERP Mapper XML namespace 一并迁移。模板 README/教程不作为运行代码复制。前端保留已审计的消费端差异：23 个 ERP API、10 个 Member API 改用 `yuheng-ui/compat/config/axios`，其余严格 TS 标注及等价写法维持原样。重跑 parity 审计后，ERP 305/305、Member 227/227 文件路径集合均匹配；后端 Java/XML 无差异，原有 47 个前端接入适配差异仍是唯一差异，没有新增或遗漏文件。

保留数据库历史兼容边界：ERP changelog 中原有 `db/changelog/business/erp/*.sql` 逻辑路径不变，避免改写已执行 changeset 的身份；Member 已执行 `001-member-schema.sql` 保持逐字节不变，仅从模板加入新的 `002-member-mobile-uniqueness.sql` 并注册到 Member changelog。业务总 changelog 在隔离 schema `yuheng_selected_modules_probe_20261121` 冷装 49 个 changeset（ERP 35、Member 14），第二次执行无新增；生成 33 张 ERP 表与 11 张 Member 表，`erp_product.unit_id` 为 bigint、`member_user.mobile` 可空。随后删除专用 schema；未连接共享数据库或访问历史密码。

消费构建验证：Maven `mvn -o -Dexec.skip=true test` 编译 402 个业务 Java 源文件，后端 40/40 测试通过；Demo Python 39 项、32 通过/7 个外部实例条件跳过；Demo UI `typecheck` 通过，Vitest 3 文件/14 项通过，平台导入边界检查通过，Vite 3545 模块生产构建通过（保留既有大 chunk 警告）。首次编译失败确认模板 `javax` 与当前 Jakarta Core 不兼容，按消费端适配为 `jakarta` 后通过。模板迁移治理测试 47/47 通过。没有运行有写入的真实 ERP/Member HTTP 工作流，本轮不能据此关闭 P2 业务闭环。

当前分支原有 `AGENTS.md`、治理技能、升级草稿及历史截图均保留；临时初始化前备份仅作为本机可恢复副本，没有清理。下一项继续在隔离服务和数据库中验收 ERP 主单、明细、库存变化、状态流转、权限拒绝与失败回滚。

### 2026-11-21 当前 Demo JAR ERP API/SQL 主流程及退货闭环

使用当前 Demo JAR（SHA-256 `dfa2bf7863a2d31afbe7ef06f704b8a074a4b290cb2274d46a79c2d32ae46b5c`）在 Docker 隔离 MySQL 容器 `codex-qc-schema-mysql` 的一次性 schema 和本轮专用密码保护 Redis 中运行真实后端 API。未连接共享 `yuheng_demo`、宿主机 `mysql8:3306` 或共享 Redis。每个 schema 冷装 59 个 Liquibase changeset；为登录仅在各自一次性 schema 创建随机临时管理员并复制种子管理员角色关系。历史用户密码未读取或修改，证据不含临时凭据或密码哈希。

采购/库存/付款和销售/库存/收款工作流运行 53 次真实 HTTP 请求，通过未审核来源拒绝、重复审核拒绝、超额付款/收款事务回滚、资金审核/反审核、租户归属和 SQL 状态断言。最终采购入库数量 10、销售出库数量 4、库存结余 6，付款 100、收款 80，库存流水为入库 `+10` 和出库 `-4`。机器证据为 `erp-workflows-20261121.json`。

双明细采购/销售退货工作流运行 77 次真实 HTTP 请求，通过金额精度、第二明细超量时整单回滚、审核/反审核/重审库存一致性、负金额退款、退款超额事务回滚与释放；最终库存为 `[7, 6]`，库存流水 20 条，种子密码哈希前后相同。机器证据为 `erp-returns-20261121.json`。

本轮发现 ERP 工作流与退货探针将 Liquibase 行数硬编码为 54，已改为拒绝少于 54 的不完整基线，同时在结果中记录实际数量；新增测试覆盖 53 拒绝和扩展基线接受。两个专用 schema 已删除，专用 Redis 容器已删除，后端及 Redis 端口均释放。以上通过的是 ERP API/SQL 代表业务闭环，不覆盖 ERP 前端浏览器、全角色/租户矩阵及所有业务边界；这些仍属 P2/P3 后续验收。

### 2026-11-21 ERP 采购页面浏览器烟测

使用同一 Demo JAR 在隔离 MySQL schema `yuheng_t4_erp_browser_20261121`（59 changesets）、Redis 容器 `yh-erp-browser-redis-20261121` 和独立后端/UI 端口 48192/5204 上运行 Chrome Playwright。临时管理员仅写入本轮隔离 schema，使用完随 schema 删除；未连接共享数据库或 Redis。桌面 1440×900 和窄屏 390×844 均真实登录，依次打开 `/erp/purchase/order` 与 `/erp/purchase/in`，等待页面列表及新增对话框资源加载，打开新增表单后取消。

四个页面/视口组合均成功；采购订单和采购入库新增对话框在两个视口均处于视口边界内，文档没有横向溢出。探针观察到 ERP 下拉数据 API 均返回 HTTP 200；浏览器 page error、console error、request failure 均为 0。截图保存在 `erp-browser-20261121/screenshots/`，机器结果为 `browser-result.json`，运行环境及 JAR 摘要为 `runtime.json`。

### 2026-11-21 ERP 采购到入库浏览器业务闭环

首次真实浏览器提交发现选择产品后缺少后端必需的 `productUnitId`。对照模板与 Demo，确认采购订单、销售订单、库存入库/出库、调拨、盘点共 6 个商品明细表单均有同一遗漏。业务模板新增回归测试先红（6 个表单失败），再将 `row.productUnitId = product.unitId` 同步修复至模板源和 Demo；测试转绿，Demo `vue-tsc` 通过。构建 UI 时配置的 npm 代理对固定坐标返回 404，本轮改用 Core 本地 tarball（SHA-256 `7d5adb2d1a27e0c68956ed64646dd1850adb733fb0e3b5467ff6adff0d9dcebc`）及已安装依赖构建 3545 个模块，再离线打包后端。新 Demo JAR SHA-256 为 `9596b4d8fc524b825a7537dc1d51817372b288a0369e88833aa9b9f123dec72b`。

在隔离 schema `yuheng_t4_erp_browser_flow_20261121k`（59 changesets）、专用 Redis 和后端/UI 端口 48203/5215/16503 中，浏览器通过真实登录创建采购订单、执行审批；再从“可入库订单”选择该订单，选择仓库和结算账户，创建并审批采购入库。4 个业务写请求均返回 HTTP 200，浏览器错误、控制台错误和失败请求均为 0。最终 SQL 为采购订单 `status=20`、采购入库 `status=20`、库存 `1.000000`、库存流水 1 条。浏览器机器结果见 `erp-browser-flow-20261121/browser-flow-result.json`，运行与 SQL 结果见 `runtime-flow.json`，截图在对应 `screenshots-run-*` 目录。专用 schema 和 Redis 已删除，16503/48203/5215 端口已释放。

### 2026-11-21 ERP 财务编辑与明细归属复验

使用当前 Demo JAR SHA-256 `9596b4d8fc524b825a7537dc1d51817372b288a0369e88833aa9b9f123dec72b`，在两个顺序隔离 schema 中重新运行既有 ERP 财务探针。财务编辑 schema `yuheng_t4_edit_20261121` 覆盖采购付款和销售收款金额修改、源单切换、超额编辑回滚、移除旧明细后新增、切换为采购/销售退货负金额退款及来源余额联动，共 66 次真实 HTTP 请求和 16 项来源金额断言通过。超额请求前后完整相关表快照一致。

第二 schema `yuheng_t4_owner_20261121` 覆盖付款/收款各自的外单明细 ID、不存在 ID、重复 ID、创建请求携带明细 ID，以及 SQL 构造的 tenant 999 明细 ID。非法请求均返回对应业务错误，前后行快照不变；合法更新成功，40 次真实 HTTP 请求通过。两个隔离 schema 使用独立临时管理员，不修改历史种子密码；密码和 token 未写入结果。专用 MySQL/Redis 容器删除，13376、16457、48211 均无监听。结果为 `erp-finance-20261121/runtime.json`、`finance-edit.json` 和 `finance-owner.json`。

为允许当前 59 changeset JAR 复用，修正财务编辑与明细归属探针中的旧 `== 54` 断言，统一调用 `installed_changesets` 最低完整性检查；测试覆盖扩展基线接受和不完整基线拒绝，3 项通过。另有一次编排失败源于 owner probe schema 必须匹配 `yuheng_t4_owner_YYYYMMDD` 且临时用户 SQL 最初错误写入另一 schema；失败运行的隔离容器和端口均按 finally 清理，修正后全新环境通过，不把失败轮次记为产品结果。

后台 ERP 属于管理端 Web。本轮用户明确要求除非工程本身是手机端程序，否则不纳入手机视口验收；因此之前保存的 390×844 采购弹窗截图只作为本地诊断历史，不作为本轮通过项，也不据此修改 ERP 表单。窄屏诊断使用的临时浏览器探针已移除，既有截图及 JSON 证据保留。

### P2 补充验证（2026-11-22）

会员模板的详情和列表增加可选业务集成开关，默认不调用 Pay、Product、Trade、Promotion；会员账户的等级、成长值及积分保持显示。模板源修复同步到 Demo，未清空或重建消费工程。隔离运行使用后端 JAR SHA-256 `fb66307402876756a689c7a9e4a079ceb351d16619d05404d2f67138fdc81302` 与本次单独构建的 UI dist，59 个 Liquibase changeset，会员 API/SQL、标签 CRUD、积分调整及详情自有标签浏览器验证通过；无上述跨模块请求，浏览器错误和失败请求为零。证据 `p2-member-optional-final-20261122/member-runtime.json`；首次浏览器运行因断言选择器不唯一失败，结果保留 `p2-member-optional-20261122/`。两个容器和四个专用端口已清理。UI 类型检查、20 项 Vitest、平台导入检查及 3546 模块生产构建通过，模板迁移及会员测试 53 项通过。开启 Pay/Mall 后的实际集成及会员独立源码构建仍待验证。

同一后端 JAR 的 ERP 隔离补充验证 `erp-p2-sidecar-20261122/runtime.json` 包括创建/更新明细归属、采购销售与财务流程及库存单据审核/反审核；隔离资源清理通过。ERP 负向盘点、库存不足、并发与完整权限矩阵仍待验证；上述结果不代表 P2 全部完成。

随后在同版 JAR 的新隔离环境补充了 31 请求的盘亏、库存不足事务回滚验证，以及 37 请求的并发出库验证。盘亏审核、反审核、再审核保持库存一致；两行出库的第二行库存不足时，第一行变动、单据状态和库存流水全部回滚；两个并发出库各申请 4 件时只有一单成功，另一单返回库存不足，库存只扣减一次。两轮容器和专用端口均已清理，结构化结果分别为 `erp-stock-negative-20261122/runtime.json` 和 `erp-stock-concurrency-20261122/runtime.json`。完整权限及租户组合仍待验证。

本轮继续补充 ERP 产品/仓库的权限与租户组合。使用同版 JAR 在一次性 schema `yuheng_t4_erp_tenant_20261122` 冷装 59 个 changeset，为租户 121、122 分别建立有权限和无权限的真实登录用户。56 个 HTTP 请求逐项验证了产品和仓库的查询、创建、更新、默认状态写入及删除：无权限请求全部返回 403 且 SQL 快照不变；本租户可以读取和维护自己的记录；跨租户详情和分页不返回对方记录；同一 token 伪造 `tenant-id` 读取和写入均返回 403，快照不变；历史种子用户密码保持不变。结构化证据为 `erp-tenant-permission-20261122/runtime.json`，入口为 `scripts/verification/erp_tenant_permission_runner.py`。专用 MySQL、Redis、48235/13390/16471 均已清理。该轮只关闭产品/仓库的权限与租户组合，不代表其它 ERP 控制器、数据权限范围、并发授权或 P2 全部完成。

同一版 JAR 在另一隔离 schema `yuheng_t4_status_20261122` 中继续验证非法审核状态。对采购订单、采购入库、采购退货、销售订单、销售出库、销售退货、其它入库、其它出库、库存盘点、库存调拨、付款单、收款单共 12 个 `update-status` 接口提交 `status=99`，全部返回业务码 400；登录加 12 次请求共 13 次，ERP 全表快照在每次请求后保持不变。当前 schema 执行 59 个 changeset，结构化证据为 `erp-p2-sidecar-20261122/audit-status.json`，可复跑入口为 `scripts/verification/erp_audit_status_probe.py`，编排结果为同目录 `runtime.json`。专用容器和 13386/16467/48231 均已清理。该证据只关闭非法状态输入边界，不代表完整 ERP 权限、数据权限或 P2 总体验收完成。

随后用同版 JAR 在一次性 schema `yuheng_t4_erp_acl_20261122` 执行 ERP 方法级权限矩阵。隔离夹具创建了产品、分类、单位、供应商、客户、结算账户和仓库，再用真实登录但无角色的普通用户访问 20 个 ERP 控制器的详情、分页、导出、创建、更新、审核和删除入口。最终 128 个请求中，111 个带 `@PreAuthorize` 的入口均返回 HTTP 200、业务码 403；每次拒绝后查询 33 张 ERP 业务表，完整快照均未改变。另有 8 个上游控制器方法没有 `@PreAuthorize`：产品、分类、单位、供应商、客户、账户、仓库的 `simple-list`，以及库存 `get-count`。这些接口要求先认证，但无 ERP 权限用户可以读取；Core 的 `anyRequest().authenticated()` 仍阻止匿名访问。该行为在原始 `ruoyi-vue-pro` 与 Templates 源码中一致，本轮只记录继承契约，没有在 Templates 或 Demo 擅自改变业务接口。

结构化结果为 `erp-permission-matrix-20261122/runtime.json`，可复跑入口为 `scripts/verification/erp_permission_matrix_runner.py`，脚本回归为 `scripts/tests/test_erp_permission_matrix_probe.py`。结果记录 `erp_snapshot_unchanged_after_denials=true`、`cleanup.passed=true`，固定 Demo JAR SHA-256 为 `fb66307402876756a689c7a9e4a079ceb351d16619d05404d2f67138fdc81302`；专用 MySQL、Redis 及 13391/16472/48236 已清理。该轮关闭 ERP 方法级权限拒绝子项，不代表角色授权成功矩阵、数据权限范围、全量跨租户组合或 P2 总体验收完成。

在同版 JAR 的另一隔离 schema `yuheng_t4_erp_auth_20261122` 中继续验证授权后的基础资料正向路径。为一个真实普通用户建立只包含 7 类基础资料 create/query/update/delete 权限的角色，完成分类、单位、供应商、客户、账户、仓库、产品的创建、详情/精简列表/分页查询、更新、仓库默认状态切换和删除，共 44 个 HTTP 请求；每个夹具行最终在对应 ERP 表中 `deleted=1`。历史种子密码前后相同，专用 MySQL、Redis 及 13392/16473/48237 已清理。结构化结果为 `erp-authorized-master-20261122/runtime.json`，可复跑入口为 `scripts/verification/erp_authorized_master_runner.py`，脚本回归为 `scripts/tests/test_erp_authorized_master_probe.py`。本轮只证明基础资料角色的正向可用性，单据、库存和统计接口的授权成功矩阵、数据权限范围及 P2 总体验收仍开放。

### 2026-11-22 ERP 库存与统计授权正向矩阵

同版 Demo JAR（SHA-256 `fb66307402876756a689c7a9e4a079ceb351d16619d05404d2f67138fdc81302`）在一次性 schema `yuheng_t4_erp_stock_auth_20261122` 冷装 59 个 Liquibase changeset。为真实普通用户建立只包含 `erp:stock:query`、`erp:stock:export`、`erp:stock-record:query`、`erp:stock-record:export` 和 `erp:statistics:query` 的角色，使用最小 SQL 夹具写入一个商品、仓库、库存、库存流水及采购/销售统计单据。

11 个真实 HTTP 请求全部通过：库存详情、分页和 Excel 导出；库存明细详情、分页和 Excel 导出；登录后的 `stock/get-count`；采购统计和销售统计的 summary、time-summary。统计结果符合模板 Mapper 的业务定义，采购为入库 100 减退货 20 得 80，销售为出库 200 减退货 30 得 170。库存详情和库存明细能够返回夹具数据，历史种子密码未修改。结构化证据为 `erp-stock-statistics-auth-20261122/runtime.json`，可复跑入口为 `scripts/verification/erp_stock_statistics_runner.py`，契约回归为 `scripts/tests/test_erp_stock_statistics_probe.py`。专用 MySQL、Redis 和 13393/16474/48238 均已清理。

本轮关闭的是库存/统计查询的正向授权子项。`stock/get-count` 仍按上游契约只要求认证而没有方法级 ERP 权限；ERP 全量角色授权成功矩阵、数据权限范围组合、Member 外部认证和 Pay/Mall 开启后的真实联调仍属于 P2 开放项。

### 2026-11-22 ERP 单据授权正向矩阵

同版 Demo JAR 在一次性 schema `yuheng_t4_erp_document_auth_20261122` 冷装 59 个 Liquibase changeset。为真实普通用户建立只包含采购订单、采购入库、销售订单、销售出库、付款单、收款单各自 `create/query/export/update-status` 权限的角色，并通过最小 SQL 夹具提供供应商、客户、账户、仓库、单位和商品。

30 个真实 HTTP 请求全部通过：六类单据各自完成创建、详情、分页、Excel 导出和审核。采购入库与销售出库审核后的库存为 6，付款单 SQL 金额为 100，收款单 SQL 金额为 80，六个核心单据状态均为 20。结构化证据为 `erp-document-auth-20261122/runtime.json`，可复跑入口为 `scripts/verification/erp_document_authorized_runner.py`，契约回归为 `scripts/tests/test_erp_document_authorized_probe.py`。历史种子密码未修改，专用 MySQL、Redis 和 13394/16475/48239 均已清理。

本轮关闭的是采购/销售/资金主单的正向授权子项。退货、其它入库/出库、库存盘点/调拨的角色成功路径，以及 ERP 全量权限、数据权限组合、Member 外部认证和 Pay/Mall 开启后的真实联调仍属于 P2 开放项。

### 2026-11-22 ERP 退货与库存辅助单据授权正向矩阵

同版 Demo JAR 在一次性 schema `yuheng_t4_erp_aux_auth_20261122` 冷装 59 个 Liquibase changeset。为真实普通用户建立只包含采购/销售来源单、采购/销售退货、其它入库/出库、库存调拨/盘点各自 `create/query/export/update-status` 权限的角色，并通过最小 SQL 夹具提供供应商、客户、账户、两个仓库、单位和商品。

50 个真实 HTTP 请求全部通过：采购/销售退货、其它入库/出库、库存调拨和库存盘点均完成创建、详情、分页、Excel 导出和审核。SQL 核对所有 10 个单据状态均为 20；库存变化按业务顺序正确，辅助单据完成后两个仓库分别为 4 和 3。结构化证据为 `erp-auxiliary-auth-20261122/runtime.json`，可复跑入口为 `scripts/verification/erp_auxiliary_authorized_runner.py`，契约回归为 `scripts/tests/test_erp_auxiliary_authorized_probe.py`。历史种子密码未修改，专用 MySQL、Redis 和 13395/16476/48240 均已清理。

本轮关闭的是退货和库存辅助单据的正向授权子项。ERP 全量数据权限范围、其它 update/delete 权限组合、Member 外部认证和 Pay/Mall 开启后的真实联调仍属于 P2 开放项。

### 2026-11-22 ERP 单据更新与删除授权矩阵

同版 Demo JAR 在一次性 schema `yuheng_t4_erp_mutation_auth_20261122` 冷装 59 个 Liquibase changeset。为真实普通用户建立覆盖 12 类 ERP 单据的 `create/query/export/update/update-status/delete` 权限。验证顺序先创建采购/销售来源单并完成必要审核，再分别创建草稿单据，调用 `update` 修改请求内容，随后调用 `delete`。

49 个真实 HTTP 请求通过，覆盖采购订单、采购入库、采购退货、销售订单、销售出库、销售退货、其它入库、其它出库、库存盘点、库存调拨、付款单和收款单。SQL 确认每个草稿行最终 `deleted=1`，采购/销售来源单链仍可用于后续业务动作。结构化证据为 `erp-mutation-auth-20261122/runtime.json`，可复跑入口为 `scripts/verification/erp_mutation_authorized_runner.py`，契约回归为 `scripts/tests/test_erp_mutation_authorized_probe.py`。历史种子密码未修改，专用 MySQL、Redis 和 13396/16477/48241 均已清理。

本轮关闭的是 ERP 单据 `update/delete` 的正向授权子项。已审核单据的删除保护策略、全量数据权限范围以及 Member 外部认证和 Pay/Mall 开启后的真实联调仍属于 P2 开放项。

### Member 单模块前端消费验证（2026-11-22）

会员模板核心页面已移除 Pay/Mall 静态导入，改为依赖无业务导入的集成契约和空适配器。Demo 在消费端自己的 `yuheng-demo-ui/src/views/member/integration-components.adapter.ts` 注册现有钱包、订单、售后、收藏、推广和优惠券组件；这部分属于 Demo 定制。使用临时消费者排除所有 Pay/Mall API、商城页面及会员可选组件，并替换为空适配器后，`vue-tsc --noEmit` 和 `vite build` 均通过。Demo 类型检查、20 项 Vitest、平台导入边界和模板 76 项测试也通过。结果见 `p2-member-standalone-20261122/runtime.json`。临时目录已删除，未使用共享数据库、Redis 或凭据。Pay/Mall 开启后的真实联调仍待验证。
### 2026-11-22 ERP 全业务租户边界验证

使用当前 Demo JAR（SHA-256 `fb66307402876756a689c7a9e4a079ceb351d16619d05404d2f67138fdc81302`）在一次性 schema `yuheng_t4_erp_full_tenant_20261122` 中执行 59 个 Liquibase changeset，使用租户 121、122 的两个真实登录账号和完整 ERP 权限角色，验证 23 个 ERP 资源族及模板 SQL 定义的 33 张业务表。验证入口为 `scripts/verification/erp_full_tenant_permission_runner.py`，探针为 `scripts/verification/erp_full_tenant_permission_probe.py`，契约测试为 `scripts/tests/test_erp_full_tenant_permission_probe.py`。

263 个真实 HTTP 请求通过：两个租户各自完成采购、销售、退货、其它入库/出库、库存调拨/盘点、付款、收款单据的创建和审核，并完成基础资料、库存、库存流水及统计的详情/列表读取；跨租户详情和分页不可见；跨租户审核与删除请求没有改变 33 张 ERP 表的完整 SQL 快照；伪造 `tenant-id` 的请求被拒绝；历史种子用户密码前后保持一致。上游删除服务对租户过滤后的空结果返回成功值，因此跨租户删除以 SQL 快照不变作为安全断言，没有把该兼容行为误判为漏洞。

机器证据为 `docs/verification/2026-11-11-full-source-migration/erp-full-tenant-20261122/runtime.json`，其中 `result=PASS`、`resource_count=23`、`business_table_count=33`、`foreign_write_sql_unchanged=true`、`seed_passwords_unchanged=true`。专用 MySQL、Redis、应用进程及 13397/16478/48242 已清理。中途三次探针失败分别修正了夹具密码长度、资源键映射和列表响应形态，均未修改 Core 或业务模板源码；最终全新隔离环境重跑通过。

该证据关闭 ERP 全业务资源的代表性租户读取和跨租户写入边界，仍不等于关闭 P2 全部范围。Member 外部短信/微信/社交认证、Pay/Mall 开启后的真实联调、ERP 更细的数据权限范围和外部依赖仍按计划开放。

本轮随后使用当前 Demo JAR `963149b3978618f370df9f63fe1db1a2841b7c3b2298d80766086cae27da5c97` 重跑同一全业务探针，结果为 `PASS`：59 个 changeset、263 个 HTTP 请求、23 个 ERP 资源族、33 张业务表，跨租户读取不可见，跨租户审核/删除前后 SQL 快照不变，伪造租户头拒绝，历史种子用户密码保持不变；专用容器及 13397/16478/48242 已清理。机器证据仍位于 `erp-full-tenant-20261122/runtime.json`。

源码边界审查同时确认，`yuheng-business-templates/template-erp/db/changelog/001-erp-schema.sql` 的业务表按当前模板定义使用 `tenant_id` 和审计 `creator` 等字段，没有 `dept_id` 或 `user_id` 归属列；模板和 Demo 也没有为 ERP 注册 `DeptDataPermissionRuleCustomizer`。因此本轮关闭的是当前 ERP 的全资源租户隔离，不宣称部门、本部门及子部门、仅本人四类数据范围已经支持。该能力如果未来需要，应先在业务模板中定义字段、写入归属规则、SQL/索引迁移和 Skill 更新策略，再由 Demo 通过模板更新流程接入；本轮没有擅自改变业务模型。

### 2026-11-22 Member 外部认证边界与 Core 修复

本轮在独立 MySQL/Redis、schema `yuheng_p2_member_auth_20261122` 和应用端口 48255 中使用重新打包的 Demo JAR（SHA-256 `963149b3978618f370df9f63fe1db1a2841b7c3b2298d80766086cae27da5c97`）完成 Member 外部认证边界验证。Liquibase 执行 59 个 changeset；短信参数校验、调试短信渠道发送、错误短信验证码、调试短信成功登录、社交参数校验、非法社交类型、无效社交 code、微信小程序参数校验和无效 code 均返回预期业务码。成功路径验证了隔离库生成的验证码被消费、会员按手机号创建且 `tenant_id=1`、OAuth access/refresh token 各增加一条、登录日志增加一条；令牌值只在内存中校验，没有写入证据。短信错误请求相对初始快照没有新增会员或 OAuth token，社交/微信失败请求相对短信成功快照没有新增会员、社交用户、绑定关系或 OAuth token，系统用户历史密码摘要保持不变；临时容器、应用进程和 13388/16468/48255 已清理。结构化证据为 `docs/verification/2026-11-11-full-source-migration/p2-member-external-auth-20261122/member-external-auth-runtime.json`，可复跑入口为 `scripts/verification/p2_member_external_auth_probe.py`。

2026-11-23 在当前固定 Demo JAR SHA-256 `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1` 上复验上述边界：schema `yuheng_p2_member_auth_20261123_current` 冷装 59 changesets；调试短信成功登录创建正确租户会员、消费验证码并新增 OAuth access/refresh token 与登录日志；无效短信码、未配置的社交渠道/无效社交 code、无效微信小程序 code 均被拒绝，失败后会员、社交用户/绑定关系和 OAuth token 快照不变。token 值未写入证据，系统用户密码摘要不变；专用 MySQL/Redis、应用及 13436/16491/48278 已清理。结构化运行结果 `p2-member-external-auth-current-20261123/runtime.json`，底层请求和 SQL 结果 `member-external-auth-runtime.json`，入口 `scripts/verification/p2_member_external_auth_current_runner.py`。本次依旧没有真实第三方账号或成功回调，因此真实社交/微信授权和供应商验收仍开放；无 Core/Templates 产品源码修复。

验证过程中定位并修复了 Core 两个边界问题：JustAuth 未配置可选 `extend` 时 `AuthRequestFactory` 的空指针，以及社交请求构建阶段/第三方调用阶段异常未统一转换为 `SOCIAL_USER_AUTH_FAILURE`。修复位于 `yuheng-core/yuheng-module-system/src/main/java/com/yuheng/platform/module/system/framework/justauth/core/AuthRequestFactory.java` 和 `.../SocialClientServiceImpl.java`，新增 5 项 Core 定向回归测试，全部通过；修复后的 Core JAR SHA-256 为 `f281a3d229f40fc3ad0ed09c93cca5acd70950a761181856ad099126da7531cb`，该制品已重新安装并进入 Demo 最终 JAR。P2 探针契约测试最终为 5 项通过。

本轮关闭的是 Member 外部认证的调试短信成功闭环及失败/不写入边界。该成功路径不等同于真实运营商短信服务；没有真实第三方账号，因此没有把社交/微信成功授权、回调、Pay/Mall 开启后的联调或其它外部服务验收记为通过；P2 其它开放项继续按计划执行。

### 2026-11-22 P2 模板更新治理闭环

本轮按三仓库关系验证模板更新边界：`yuheng-core` 提供平台能力和迁移 Skill，`yuheng-business-templates` 提供业务模板源码及更新工具，`yuheng-demo` 作为最终可运行、可交付、可定制工程。模板不是 Demo 的运行时依赖；模板更新必须由使用者显式触发，更新时保留 Demo 定制，不重建、不清空、不整目录覆盖 Demo。

在 Templates 中修正 ERP 示例映射，移除不存在的 `template-erp/api`、`convert` 和 `job` 等源路径；映射现在覆盖实际的 controller、dal、enums、framework、service、resources、db/changelog 以及 UI API/页面目录。新增 `tools/template_update.py` 支持基线记录、只读预览和显式 `--apply`，默认阻止冲突、未分类差异和模板删除，数据库文件仅参与比较，不改写已执行 changeset、checksum 或业务数据。

以当前 Demo 初始化结果建立 ERP 基线后，运行预览得到 309 个 `unchanged`，`template_added`、`template_changed`、`consumer_only`、`consumer_customized`、`conflict`、`template_deleted`、`unclassified_difference` 均为 0；预览输出明确 `consumer files were not modified`。当前基线已经包含 Demo 的包名、请求实例、UI 集成和 changelog 适配，因此没有执行 `--apply`。机器证据为 `docs/verification/yuheng-template-update/erp-preview-20261122.json`，对应 Core 提交 `40f0e40`、Templates 提交 `0802802`；本机基线为 `/tmp/yuheng-erp-template-state-20261122.json`，基线不提交。

验证中发现并修复两处更新工具分类缺陷。第一处是已记录的消费端适配在源文件和目标文件均未变化时被误报为 `unclassified_difference`；第二处是基线已存在适配时模板后续修改可能被错误归类为 `template_changed` 并覆盖消费端。两项均按红灯测试复现后最小修复；Templates 更新工具定向测试 7 项、全量测试 83 项通过。Core `AuthRequestFactoryTest` 与 `SocialClientServiceImplTest` 定向测试 5 项通过，Demo 升级 Skill 测试 4 项通过，Demo 全量 Python 脚本测试 82 项（7 项因外部服务条件跳过）通过。

Core 的模板迁移 Skill 已同步到 Demo，`sync-specs-api.py --apply` 返回 `changes: []`，随后 `--verify --json` 为 `PASS`；没有覆盖 Demo 的业务代码、业务 SQL、升级 Skill、计划或历史截图。三仓库 `git diff --check` 通过；本轮没有新增未跟踪的 `target`、`dist`、`node_modules`、JAR 或日志。P2 总项仍继续进行中，Pay/Mall 开启后的真实联调、真实社交/微信授权、ERP 更细数据权限及其它外部依赖继续按计划开放。

### 2026-11-22 Member 管理端权限矩阵

本轮在当前 Demo JAR（SHA-256 `963149b3978618f370df9f63fe1db1a2841b7c3b2298d80766086cae27da5c97`）上使用一次性 schema `yuheng_t4_member_acl_20261123`、隔离 MySQL/Redis 和 13399/16480/48260 端口，冷装并等待 59 个 Liquibase changeset 完成后执行 Member 管理端权限矩阵。验证结束后临时容器、应用进程和端口均已清理。

`member_permission_matrix_runner.py` 建立两个真实登录账号：无角色账号和只授予 Member 权限的普通账号。67 次真实 HTTP 请求覆盖会员用户、标签、分组、等级、会员配置、经验记录、等级记录、积分记录、签到配置和签到记录的查询与授权写入口。无角色账号对所有方法级保护入口均收到 HTTP 200、业务码 403；有权限账号对对应入口均收到业务码 0。标签、分组和等级的三个 `list-all-simple` 方法在源码中没有 `@PreAuthorize`，本轮按既有“认证可读”契约单独记录为成功，不将其误报为权限缺陷。

每次拒绝请求前后均比较 `member_config`、`member_level`、`member_group`、`member_tag`、`member_user`、`member_address`、`member_experience_record`、`member_level_record`、`member_point_record`、`member_sign_in_config` 和 `member_sign_in_record` 11 张表的完整 SQL 快照，均未发生写入；历史系统用户密码字段保持不变。结构化结果为 `docs/verification/2026-11-11-full-source-migration/member-permission-matrix-20261123/runtime.json`，契约测试为 `scripts/tests/test_member_permission_matrix_probe.py`。证据未记录凭据、token 或密码哈希。

本轮没有发现需要修复 Core 或业务模板的产品缺陷；运行中暴露的用户名格式、创建夹具唯一性和快照基线问题均属于验证脚本，已通过红绿测试和隔离重跑修正。该结果只关闭 Member 管理端权限矩阵子项；Member 调试短信成功路径已由后续当前 JAR 证据关闭，真实社交/微信授权、Pay/Mall 开启后的真实联调、ERP 更细数据权限和 P2 总体验收继续开放。

### 2026-11-22 Member App 当前 JAR 复验

为避免历史 Member 证据继续支撑当前版本，本轮使用当前 Demo JAR（SHA-256 `963149b3978618f370df9f63fe1db1a2841b7c3b2298d80766086cae27da5c97`）在一次性 schema `yuheng_p2_member_20261117` 中重新启动隔离 MySQL/Redis 和 Demo，Liquibase 执行 59 个 changeset 后完成复验。验证入口为 `scripts/verification/p2_member_platform_probe.py`，结构化结果写入 `docs/verification/2026-11-11-full-source-migration/p2-member-platform-20261117/member-runtime.json`，浏览器结果写入同目录 `member-browser.json`。

真实请求覆盖后台匿名 401、无角色 403、伪造租户头拒绝和授权操作；App 密码登录；地址超长姓名返回 400 且没有数据库写入、地址增改查删、另一会员列表/详情不可见；积分记录故障注入时会员积分和积分流水事务回滚，移除故障后正常加分；标签/分组/等级创建更新查询、引用保护和软删除；签到配置增改删及重复日期拒绝。桌面浏览器完成标签 CRUD、会员搜索和扣积分，以及分组、等级、积分、签到配置/记录、会员参数读取，浏览器 console/page error 和失败请求均为 0。数据库断言确认租户归属、积分值及流水值与 API 一致，历史系统用户密码未修改。

本轮结果 `completed=true`，应用/UI 已停止，隔离容器已删除，13373、16453、48220、5203 均无监听。该证据关闭当前 JAR 下 Member App/API/SQL 及桌面代表页面的限定复验子项；真实社交/微信授权回调、Pay/Mall 开启后的真实联调、ERP 更细数据权限组合和 P2 总体验收仍开放。ERP 是桌面后台，本轮没有增加手机视口验收。

### 2026-11-22 Pay/PMS 临时消费者运行验证

桌面补验：隔离消费副本将分享页面注册为顶层匿名路由，使用 Core `067f48e` 本地 UI 包；生产构建及开发模式均在同轮隔离后端生成令牌后立即启动 1440×900 浏览器，实际文档内容可见，浏览器错误和失败请求均为零。后端重启前后均为 107 个 changeset，隔离容器及端口已停止。将分享路由错误挂在 Home 下时会发起认证请求并产生刷新令牌错误，顶层接线消除此问题；中途 502 是验证环境未就绪。开发模式因 `qs` CommonJS 未预构建出现默认导入错误，消费端 Vite 设置 `optimizeDeps.include: ['yuheng-ui > qs']` 后复验通过，Templates `c3049cd` 已补充说明。浏览器结构化结果见 `p2-pay-pms-consumer-20261122/desktop-share.json`。

补充：Templates `8d727bf` 增加 Pay/PMS 映射示例及 Pay 转账可选回调的前向 changeset，`04d0544` 声明 PMS 消费端共享 UI 资产。隔离映射消费者 JAR SHA-256 `15993a3d1986380abc84a9c07e7c0a0e8a0e6f1831e831605d1a99531571e8a5` 的 `p2-pay-pms-consumer-20261122/runtime.json` 记录 107 个 changeset 首次及重启一致，Pay 应用、钱包余额、PMS 项目、知识库文档和匿名分享代表调用通过；Pay 匿名查询返回 401、PMS 无权限查询返回 403，拒绝前后 Pay/PMS 表快照一致。隔离容器已删除。该证据不覆盖普通角色完整授权、租户隔离、桌面浏览器、真实支付渠道及回调。Core `067f48e` 完成严格消费兼容修复和本地包重建，UI 130 项测试通过；Templates `05530e5` 修复 Pay/PMS/Member 类型及直接依赖说明，99 项测试通过。独立安装的隔离消费工程使用本地 Core tarball `e517810021a1567784935a76ff196356431259aa7f6a2cafd19b07793d7397d2`，补齐消费端依赖、修正请求类型转发并更新 Member 字典类型后，完整类型检查和生产构建通过，存在大 chunk 警告。该 tarball 未发布 npm；正式 Demo 未预置 Pay/PMS，P2 总体验收继续进行中。

前端补充检查：隔离复制 Demo UI，将 Pay/PMS 模板前端接入后，直接调用已有 `vue-tsc` 失败，149 行诊断包括模板隐式 `any`、缺失的本地兼容转发及类型声明。Core 的已发布包包含 Qrcode、FilePreview、用户/部门选择组件及部分工具，Demo 当前声明尚未覆盖这些用途；模板自身和依赖错误仍需逐项确认。Pay API 目录与 Demo 副本已有文件合并，因此此结果只证明当前组合不可编译，不代表干净模板接入结果。未执行前端构建、浏览器或真实支付渠道验证；P2 保持进行中。正式 Demo 未接入 Pay/PMS，也未修改共享数据库。

将 Demo 复制到临时目录，人工复制 Pay/PMS 后端源码及模块 changelog，适配包名并加入 Pay SDK 依赖；该轮没有实际执行 Skill 初始化流程，也没有验证 Pay/PMS 前端。补充 Core 的 `lombok.config` 后，临时消费者离线编译 910 个 Java 文件并打包成功，JAR SHA-256 `f7a5dc29077b2f9230e0809ba89075d6615f32cd42f545a87d3eb1ddd2c379f1`。首次链式 setter 编译失败源于临时消费者缺少 Core Lombok 配置，并非 Pay Java 源码缺陷。Templates 的 Pay README 已补充该配置和支付 SDK 依赖要求。

专用 MySQL/Redis 中应用启动成功，Liquibase 记录 106 个 changeset，包含 Pay 14 张和 PMS 33 张表；再次启动时没有新增 changeset。管理员真实登录后，Pay 应用完成创建、读取、更新和逻辑删除，应用、订单、钱包空列表查询成功，匿名应用查询返回业务码 401。PMS 项目完成创建、读取、更新、回收、恢复、归档、恢复、回收和删除；知识库完成创建、读取、更新和删除。项目及应用活动探针记录的 SQL 计数为零，知识库删除后分页为空。

首次启动因验证命令漏传 Redis 端口而尝试连接本机 6379，认证失败；修正为专用端口后启动成功。探针曾因漏传令牌收到 401，及尝试回收已归档项目收到状态错误，随后按真实状态机完成验证。上述不是生产源码修复。正式 Demo 未加入 Pay/PMS 源码；Pay/PMS 前端、Skill 实际初始化、普通用户权限矩阵、支付渠道、真实支付宝/微信回调和会员支付联动仍待验证，P2 总项继续进行中。

补充租户及普通角色验证：固定 JAR `15993a3d1986380abc84a9c07e7c0a0e8a0e6f1831e831605d1a99531571e8a5` 在新隔离 MySQL/Redis 中复跑 `scripts/verification/p2_pay_pms_consumer_probe.py`。两个独立登录租户分别创建 Pay 应用、PMS 项目和知识库，直接查询对应业务表确认 `tenant_id` 与当前租户一致；双方读取自身记录成功，跨租户读取返回空或资源不存在，PMS 跨租户更新被拒绝，拒绝前后业务表快照相同。限定普通角色的五项越权写入和伪造租户头均返回 403，快照不变。首次与重启均为 107 个 changeset，隔离容器清理成功；结构化结果为 `p2-pay-pms-tenant-20261122/runtime.json`。Pay 应用继承 `BaseDO` 但没有 `@TenantIgnore`，Core 当前拦截器仍对其追加租户条件；此结果不证明所有 Pay/PMS 接口、外部支付渠道或第三方回调均已验证。

### 2026-11-22 Pay/PMS 模板 SQL 迁移复验

本轮使用 `yuheng-business-templates/template-pay/db/changelog/changelog.yaml` 和 `template-pms/db/changelog/changelog.yaml`，通过隔离 MySQL 8.0.33 容器 `codex-qc-schema-mysql` 的临时 probe 用户执行 Liquibase 4.29.2。Pay 首次更新执行 14 个 changeset，重复更新执行 0 个；PMS 首次更新执行 33 个，重复更新执行 0 个。Pay 14 张业务表和 PMS 33 张业务表均创建成功，所有业务表初始行数为 0；`DATABASECHANGELOG` 只记录各自对应的 14/33 个 changeset，没有示例订单、钱包、支付凭据、知识库文档或其他初始化业务数据。

在两个新的冲突 schema 中分别预创建 `pay_app` 和 `pms_project`，再次执行对应 changelog 均在首个 changeset 以 `PreconditionFailedException` 退出，更新摘要 `Run: 0`，原有表未被覆盖，未留下错误的 Liquibase 执行记录。结构化结果为 `docs/verification/2026-11-11-full-source-migration/p2-template-sql-20261122/runtime.json`，其中记录业务表数、changeset 数、空数据断言、冲突保护和清理状态。验证结束已删除 probe 用户、四个临时 schema；共享 `yuheng_demo`、历史密码、Redis 和运行服务未触碰。

该证据只关闭 Pay/PMS 模板 SQL 的冷装、重复执行、空初始化和已有表冲突保护子项。当前 Demo 后端仅初始化 ERP、Member；Core 的 Pay/PMS 路由是禁用占位入口，Templates 当前也没有完整 Trade/Promotion/Product 后端接入，因此没有把本轮 SQL 结果记为 Pay/PMS API 或商城支付联调通过。后续若验证这些业务，必须先按 Skill 将完整模板源码和自有 changelog 显式复制到 Demo，再在当前 Core 版本上构建和执行真实 API/SQL 验证。

### 2026-11-22 Member 与 Pay 钱包桌面联动

通过显式初始化 Pay/PMS 的临时消费 JAR（SHA-256 `15993a3d1986380abc84a9c07e7c0a0e8a0e6f1831e831605d1a99531571e8a5`），并用 Demo 正式 UI 源码开启 `VITE_MEMBER_ENABLE_PAY=true` 构建临时 dist；Pay/PMS 源码没有写入正式 Demo。隔离 schema `yuheng_p2_member_pay_20261122` 首次和重启均为 107 个 Liquibase changeset，平台种子用户密码以及新建会员密码字段均保持不变。

桌面 1440×900 浏览器登录后打开会员详情和余额流水，确认初始 1.25 元；在列表使用“修改余额”增加 2.50 元，再减少 0.75 元。页面/API 金额与 SQL 分一致，最终钱包余额 300 分，流水依次为 `125/125`、`250/375`、`-75/300`。只读角色无法看到写操作，直接更新请求返回 403；匿名更新返回 401；伪造 `tenant-id: 2` 返回 403。通过 `pay_wallet_transaction` 插入触发器故障注入，更新返回 500 后钱包和流水完整快照均与操作前一致；移除触发器后正常更新成功。浏览器 page/console error、失败及取消请求均为 0。

回归入口为 `scripts/verification/p2_member_pay_runner.py`、`scripts/verification/p2_member_pay_browser_probe.js`，对应契约测试 `scripts/tests/test_p2_member_pay_runner.py`。完整结果位于 `docs/verification/2026-11-11-full-source-migration/p2-member-pay-second-20261122/member-pay-runtime.json` 与 `member-pay-browser.json`；首轮未通过记录和角色菜单夹具修正前截图另存于 `p2-member-pay-first-20261122/`。两轮结束时均确认隔离容器已删除，13402、16482、48262 和 5220 均无监听。Demo 全量 Python 回归 96 项（89 通过、7 条件跳过），Demo UI 类型检查、20 项 Vitest 和平台导入边界检查通过；开启 Pay 的 Vite 生产构建 3548 模块成功并保留既有 chunk 体积警告。此次只关闭 Member 管理 UI 与 Pay 钱包联动的代表性桌面/API/SQL/权限/事务子项；真实支付渠道、支付回调和第三方认证仍未执行，P2 总验收继续进行中。未发现需修复的 Core 或 Templates 产品源码问题。

### 2026-11-23 Member 实际签到与奖励事务

使用当前 Demo JAR `963149b3978618f370df9f63fe1db1a2841b7c3b2298d80766086cae27da5c97`、一次性 MySQL/Redis 和关闭 Pay/Product/Trade/Promotion 的独立 UI 构建，冷装 59 个 changeset。真实 App 登录后，分别对 `member_experience_record` 和 `member_level_record` 注入插入故障，签到接口返回 500，签到、积分、经验、等级流水和会员状态的操作前后快照均相同。移除故障后首次签到获得 4 积分、3 经验并自动升级；重复签到返回 `1004010000` 且快照不变；另一会员的签到分页和统计均为空。桌面会员页完成原有流程，扣减 2 分后的用户积分和流水均为 17；浏览器错误及失败请求为零，系统种子用户密码未变。

最终机器证据 `p2-member-signin-rewards-final4-20261123/member-runtime.json`、`member-browser.json`，探针及对应测试为 `scripts/verification/p2_member_platform_probe.py`、`scripts/tests/test_member_verification.py`。容器和 13373/16453/48220/5203 端口均已清理。首次桌面失败因探针保留签到前的固定积分期望；后续使用了先前开启 Pay 的 UI 构建，导致可选集成关闭断言失败；分别记录在独立目录，最终使用独立默认构建复跑通过。本轮未发现需修改 Core/Templates 的产品缺陷；签到并发幂等、真实第三方授权及 P2 总体验收仍开放。

### 2026-11-23 Member 同日并发签到幂等

源码检查发现签到事务原先先查询最近记录后插入，而 `member_sign_in_record` 没有用户/日期唯一约束；两个并发请求可在检查处竞争。业务模板修复为在事务开始时通过 `MemberUserMapper.selectByIdForUpdate` 锁定会员主行，再读取最近签到。该行在事务提交前保持锁定，因此同一会员请求串行化；第二个请求按原业务码拒绝。没有修改 Core、已执行 changeset 或跨天签到模型。

修复先由 `yuheng-business-templates/tests/test_member_signin_concurrency.py` 红灯确认缺少行锁，再实现后绿灯，并提交为 Templates `3ea638f`。借助 `tools/template_update.py` 按 Demo 原始模板基线预览并选择性应用两个 Java 文件；Demo 目录内三个消费端专有签到服务文件被分类为 `consumer_only` 并保留，未重建 Demo。模板全量治理测试 100 项通过，Demo Member 探针及模块测试 11 项通过。`./scripts/build.sh` 完成后端打包、前端类型检查及 Vite 生产构建（3548 模块，既有大 chunk 警告保留）；JAR SHA-256 为 `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1`，内含 612 个静态资源。

在独立 schema `yuheng_p2_member_20261117` 的最终运行中，59 个 changeset 冷装成功；两个同步起跑的真实 App API 请求一个成功、一个返回重复签到业务码。成功响应为第 1 天、4 积分、3 经验；SQL 确认只有一条新增签到、积分流水和经验流水各一条，会员状态为 4 积分/3 经验。该轮同时复验签到各奖励阶段故障回滚、普通重复请求拒绝、另一会员记录隔离、会员管理端桌面流程和系统种子密码未变。浏览器 `completed=true`，错误与失败请求为零。专用 MySQL/Redis、应用/UI 进程及 13373、16453、48220、5203 端口清理完成。

最终证据为 `p2-member-signin-concurrency-pass-20261123/member-runtime.json` 与 `member-browser.json`。前四个隔离运行目录均保留。逐份检查它们的机器记录，四轮真实并发请求都返回一次成功和一次重复拒绝，随后分别因 `CURDATE()` 时区假设或探针重复签到规则的奖励金额期望不符而失败；前几轮没有逐个失败分支修正重跑。`p2-member-signin-concurrency-diagnostic-20261123/member-runtime.json` 保留成功响应 day 1/point 4/experience 3、单条签到、积分/经验流水和会员状态快照，定位了规则夹具歧义。最终轮复用唯一有效规则，完成所有断言并通过。以上失败是验证夹具问题，不作为产品失败结论。此项关闭同会员同日并发签到幂等子项，不关闭真实社交/微信成功回调、真实支付渠道、ERP 部门或本人级数据范围及 P2 总体验收。

### 2026-11-23 P2 模板更新 Skill 隔离消费验收

使用 Templates 当前提交 `c3049cd3f524b646639681f69478ddc311f880e9` 的 ERP 映射和 `tools/template_update.py`，在临时 Git 消费工程中初始化 271 个映射文件并记录基线。验证首次预览无差异；添加消费端独有文件后，预览仍只读且分类为 `consumer_only`；在临时模板副本单方修改仓库 Service，预览归类 `template_changed`，显式 `--apply` 只更新该文件，消费端独有文件及映射外工程文档保持不变。随后同时修改模板与消费端同一文件，预览归类 `conflict`，`--apply` 返回 1 且消费端字节不变。临时消费者未重建；正式 Demo 源码、数据库及共享服务均未触碰。结构化结果为 `p2-template-update-e2e-20261123.json`。该项验证模板更新工具与 Skill 的选择性同步约束，不代表已对正式 Demo 执行模板更新或完整模块构建。

### 2026-11-23 P2 Member 模板更新映射验收

发现 Member 已通过 Skill 选择性同步模板修复，但模板仓库没有 Member 专用消费映射，使用者无法直接用既有更新工具表达 Member 后端 API、Controller、Convert、DAL、MQ、Service、UI 与 Liquibase 路径。Templates 新增 `docs/template-member-mapping.example.json`，并在 `template-member/README.md` 说明显式预览/选择性更新方式。映射契约测试先红（缺映射文件），新增映射后通过；隔离 Git 消费工程对 237 个映射文件记录基线并确认无差异，模板单方修改只应用目标 Service 文件，消费端独有文件保留；模板与消费端随后同时修改该文件时，更新被分类为冲突并阻止写入。机器证据为 `p2-member-template-update-e2e-20261123.json`。

本轮复跑 Templates 全量 Python 测试为 100/100 通过；Demo 全量 Python 测试为 98 项通过、7 项按条件跳过、0 失败。当前 ERP/Member 源码路径审计分别为 305/305、230/230，缺失和额外路径均为 0；审计仍报告 30 个 ERP、19 个 Member 已知消费端适配/可选集成差异，不能解读为源码逐字节相同。该映射验收没有改写正式 Demo 业务代码、没有执行 Demo 构建或数据库迁移。P2 仍开放真实社交/微信回调、真实支付渠道及外部服务、未提供完整后端模板的商城业务，以及 ERP 部门/本人数据权限模型；不因本轮映射通过而关闭 P2 总验收。

### 2026-11-23 Member 签到规则桌面 CRUD

扩展 P2 Member 浏览器探针，在一次性隔离环境和桌面 1440×900 浏览器中，通过实际路由 `/member/signin/config` 完成签到规则新增、编辑积分 23→24、删除。编辑前等待详情 API 和表单原值加载，提交请求体确认为 `point: 24`，接口业务码为 0，列表刷新显示 24，SQL 回查记录为软删除。浏览器 errors/failed 均为 0。最终机器结果 `p2-member-signin-ui-crud-final2-20261123/member-runtime.json` 与 `member-browser.json` 均为 `completed=true`；冷装 59 changesets，既有签到奖励失败回滚、重复拒绝、跨会员隔离、并发幂等和系统用户密码不变检查均通过。隔离容器及应用/UI 已清理，13373、16453、48220、5203 无监听。

失败轮次分别保留在 `p2-member-signin-ui-crud-*` 目录；根因是验证探针的路由、变量引用及异步等待顺序，不是产品业务缺陷。最终轮对编辑详情、输入值和请求体增加断言后通过。Member 专项契约测试 10/10 通过，Node/Python 语法检查通过；没有修改 Core、Templates 或 Demo 业务产品代码，也没有访问共享数据库或服务。

Member 数据边界初步静态复核曾将 `BaseDO` 误判为默认不受租户条件约束；该判断已由下文 Core 拦截器源码和真实双租户运行纠正。最终结论以修正后的 `TenantDatabaseInterceptor` 源码路径及 35 请求隔离运行证据为准。

### 2026-11-23 Member 配置、地址、等级与账号生命周期

使用当前 Demo JAR SHA-256 `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1`，在一次性 schema `yuheng_p2_member_lifecycle_20261123h` 冷装 59 个 Liquibase changeset。隔离管理员首次保存会员配置后，再次保存更新同一有效行；API 回读值和 SQL 值一致且有效配置行数仍为 1。真实 App 账号创建两个地址，确认新增默认地址取消旧默认；更新第二个地址为默认后 `get-default` 返回第二个地址；删除该默认地址后 `get-default` 为空，原地址仍保留但为非默认，删除行逻辑删除。后台真实 API 将会员调整至新等级后，`member_user`、等级流水及经验流水均记录等级与经验 60；取消等级后主表为 `level_id=0, experience=0`，等级和经验流水均记录 -60 及新经验 0，随后等级逻辑删除。会员资料更新写入昵称、邮箱和性别后，API 回读与 SQL 一致；按 Core 调试短信通道分别取得改绑手机号和修改密码验证码，验证码只在内存中使用。改绑后旧手机号登录返回 `1004003000`、新手机号使用原密码成功；另一个隔离会员修改密码后旧密码返回同一无效凭据码，新密码登录成功。

机器证据 `member-lifecycle-final7-20261123/runtime.json` 的 `result=PASS`、59 changesets、`seed_passwords_unchanged=true`、`credentials_recorded=false`、`completed=true`。探针契约测试 2/2 通过；专用 MySQL/Redis、Demo 进程及 13412/16493/48273 已清理。最终证据没有包含密码、验证码或 token。失败轮次保留于 `member-lifecycle-20261123/` 和 `member-lifecycle-final*-20261123/`：分别是超过姓名长度约束的测试夹具、管理员业务类型枚举值期望错误、MySQL 客户端中文显示编码限制、把等级 `0` 哨兵当作 NULL 的断言错误及同号码一分钟短信频率限制；按 Templates/Core 实际契约修正探针或夹具后，最终在全新隔离 schema 重跑通过。这些不是产品缺陷。本轮确认 Templates 与 Demo 的相关业务源码一致，没有修改 Core、Templates 或 Demo 业务代码。运行日志曾由首版 runner 写入验证目录，已删除这些本轮新增日志，并修正 runner 将日志放入系统临时目录且结束时删除。

该证据仅关闭 Member 配置、地址、等级和账号资料/手机号/密码的限定 API/SQL 生命周期子项；验证码成功路径使用 Core 调试短信，不等同真实短信供应商验收。未覆盖账号资料桌面页面、所有会员生命周期、真实第三方服务或 P2 总体验收。真实社交/微信成功授权、真实短信供应商和支付渠道、尚无完整后端模板的 Trade/Promotion/Product，以及 ERP 部门/本人级数据权限和 P2 总项继续开放。

### 2026-11-23 Member 忘记密码重置 API 补验

在固定 Demo JAR SHA-256 `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1` 的隔离 schema `yuheng_p2_member_lifecycle_20261123j` 冷装 59 个 changeset，使用独立测试会员完成匿名密码重置流程。未注册手机号请求 `POST /member/auth/send-sms-code` 的重置场景返回 `1004001001`，`system_sms_code` 行数不变；错误验证码调用 `PUT /member/user/reset-password` 返回 `1002014000`，会员原密码哈希保持相同；随后发送的有效验证码仅在探针内存中读取并提交，重置成功且对应验证码标记已使用，新密码登录返回该会员 ID。最终证据 `member-lifecycle-final9-20261123/runtime.json` 记录 `result=PASS`、`credentials_recorded=false`、`completed=true`，没有验证码、密码或 token；种子用户密码未变，隔离 MySQL/Redis、应用和 13414/16495/48276 已清理。

短信发送频率按 Core 当前行为对同手机号的所有场景统一限流一分钟；由于同一账号刚完成密码修改后立即发送重置码会被正常限流，本轮使用第三个一次性会员夹具，不修改限流配置。Demo UI 中没有发现忘记密码页面或该 API 调用，因此只记录 API/SQL 子项通过，不声称页面闭环；也不把调试短信视为真实短信供应商验收。

后续使用新隔离 schema `yuheng_p2_member_lifecycle_20261123k` 对手机号改绑增加负向断言：申请改绑到已被另一会员占用的手机号返回 `1004003007` 且不创建验证码；向可用手机号发出有效码后，先提交错误码，接口返回 `1002014000`，用户手机号 SQL 保持原值且验证码 `used=0`，再提交有效码后改绑成功。最终机器证据 `member-lifecycle-final10-20261123/runtime.json`，冷装 59 changesets、`result=PASS`、`credentials_recorded=false`、`completed=true`；种子密码未变，专用 MySQL/Redis、应用及 13415/16496/48277 已清理，凭据和验证码未写入结果。本轮无 Core、Templates 或 Demo 产品源码修复，P2 总体验收及真实外部服务仍开放。

### 2026-11-23 ERP 退货审批、反审批与删除生命周期

使用固定 Demo JAR SHA-256 `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1`，在一次性 schema `yuheng_t4_return_delete_20261123_current` 冷装 59 个 changeset。桌面浏览器在 1440×900 分别完成采购订单→采购入库→采购退货，以及销售订单→销售出库→销售退货；浏览器流程结果均为 PASS。后续以真实登录 API 对已审核退货直接删除：采购返回 `1030103001`，销售返回 `1020203001`；拒绝前后单据状态、主/明细逻辑删除标记、来源订单累计退货数、库存和流水行数均相同。反审批并删除后，两类退货主单和明细均逻辑删除，来源订单 `return_count=0`，只产生一条库存冲销流水；采购库存回到入库后的 20，销售库存回到出库后的 7。59 个 changeset、种子用户密码快照、JAR/dist 静态资源字节一致及隔离资源清理均通过，证据不记录凭据；MySQL/Redis、应用已清理，13437、16492、48279 无监听。完整结果见 `erp-return-delete-current-20261123/runtime.json`，浏览器请求记录为同目录 `purchase-browser.json`、`sale-browser.json`；运行入口为 `scripts/verification/erp_return_delete_current_runner.py`，生命周期 API/SQL 断言位于 `erp_return_delete_lifecycle.py`。

此前探针的 SQL 期望先后误用采购初始库存 10、销售退货前库存 10。按实际流程追踪后确认采购退货前库存为 18，删除冲销后回到 20；销售退货前库存为 10，删除冲销后回到销售出库后的 7。修正期望后在全新隔离环境完整通过；MySQL `BIT` 字段输出改用显式 `CASE` 字符串，以便证据稳定表达 0/1。这些均是探针/证据表示问题，没有发现需修改 Core、Templates 或 Demo 产品业务源码的缺陷。该结果关闭采购/销售退货删除的限定生命周期子项；ERP 部门/本人级数据权限、外部服务与 P2 总验收继续开放。ERP 只按桌面场景验收。

### 2026-11-23 ERP 当前版本采购/销售退货与退款事务

以当前固定 Demo JAR SHA-256 `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1` 在一次性 schema `yuheng_t4_returns_20261123_current` 冷装 59 个 changeset。复用 `erp_returns_probe.py` 完成真实采购/销售 API 与 SQL 事务验收：两行订单及退货的金额、税额和半入舍入精度一致；第二行超出可退数量时，退货主单、明细、订单累计退货量和库存快照全部回滚；有效退货审核、反审核、再审核时库存按方向对称恢复，已审核退货的非法修改/删除不改变 SQL。采购付款与销售收款以负金额联动退款，退货单退款占用与财务单明细相符；超额退款、退款占用下反审核退货均被拒绝且完整业务快照不变；财务反审核/删除、退货反审核/删除后退款额度、来源订单累计退货量及库存均正确释放。最终两产品库存为 7、6，库存流水 20 行，无活动退货或退款财务单。

最终机器证据 `erp-returns-current-20261123/runtime.json`、`returns.json` 均为 PASS；59 changesets、历史种子用户密码字段快照不变，未记录凭据，专用 MySQL/Redis、应用及 13438/16493/48280 已清理。入口为 `scripts/verification/erp_returns_current_runner.py`，契约测试 `scripts/tests/test_erp_returns_current_runner.py`。首轮 runner 的最终密码断言把本轮临时用户包括在种子快照中，造成预期外差异；将前后查询限定为用户 ID `<900000` 后，在全新隔离环境完整复跑通过。该探针是 API/SQL 验收，不表示退货退款桌面 UI 已验收；无 Core、Templates 或 Demo 业务产品源码修复。P2 总体验收和 ERP 部门/本人数据范围仍开放。

### 2026-11-23 ERP 当前版本财务编辑与明细归属复验

使用固定 JAR SHA-256 `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1`，在两个顺序独立 schema `yuheng_t4_edit_20261123_current` 与 `yuheng_t4_owner_20261123_current` 分别重跑既有付款/收款探针。编辑场景 66 个真实 HTTP 请求及 16 项来源金额检查通过：采购付款和销售收款金额更新、切换来源单、超额编辑回滚、替换/新增明细、入库/出库来源切换为退货退款并正确回写 `refundPrice`。归属场景 40 个请求通过：外单、不存在、重复、创建请求自带明细 ID 以及隔离 SQL 构造的 tenant 999 明细 ID 均被拒绝，前后相关业务表快照一致；合法金额更新仍成功。

机器结果 `erp-finance-current-20261123/runtime.json`、`finance-edit.json`、`finance-owner.json` 均为 PASS。两 schema 各冷装 59 changesets，既有系统用户密码快照不变，凭据和 token 未记录；专用 MySQL/Redis、应用及 13439/16494/48281 已清理。runner 为 `scripts/verification/erp_finance_current_runner.py`，契约测试 `scripts/tests/test_erp_finance_current_runner.py`。该组此前最后一次完整证据使用 JAR `9596b4d`；本次在 P2 固定 JAR 上完成复验，没有发现 Core、Templates 或 Demo 业务产品源码缺陷。该结果只覆盖 API/SQL，不声称财务编辑桌面页面通过。

### 2026-11-23 ERP 采购/销售退货退款桌面闭环

使用固定 Demo JAR SHA-256 `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1`，在隔离 MySQL/Redis、专用端口和 1440×900 桌面浏览器中，先经真实业务页面创建并审批采购订单→入库→采购退货及销售订单→出库→销售退货，再从财务收款/付款页面选择退货单，分别创建负数收款 `-2.00` 和负数付款 `-3.00` 并审批。退货及财务创建/审核 API 均 HTTP 200；最终浏览器 page errors、console errors、failed requests 均为空。

隔离 schema 冷装 59 个 changeset。SQL 确认销售退货 `status=20,total_price=36,refund_price=2,tenant_id=1`，收款主单 `status=20,total_price=-2,receipt_price=-2`，明细 `biz_type=22,biz_id=1,total_price=-36,receipt_price=-2`；采购退货 `status=20,total_price=20,refund_price=3,tenant_id=1`，付款主单 `status=20,total_price=-3,payment_price=-3`，明细 `biz_type=12,biz_id=1,total_price=-20,payment_price=-3`。退货退款累计值、财务单及来源明细一致。历史种子用户密码字段快照未变，JAR 与 Demo dist 的 612 个静态资源逐项字节相同，证据未记录临时凭据。

最终机器结果 `erp-refund-browser-20261123/runtime.json`，浏览器记录为同目录 `refund-browser.json`、`purchase-browser.json`、`sale-browser.json`；运行入口 `scripts/verification/erp_refund_browser_runner.py`，契约测试 `scripts/tests/test_erp_refund_browser_probe.py`。专用 MySQL/Redis 容器、应用/UI 进程及 13448、16528、48328、5234 均已清理；含临时凭据环境的原始 backend/UI 日志已删除。

探针最初因退款选择器夹具名称不一致失败；随后修正为显式输入负数，并依据实测 SQL 校准退货累计退款与财务主单、明细的符号语义。静态 chunk 请求偶发重置时，runner 按其他仓库验收入口的现有做法将 UI server 请求队列设为 128，最终运行浏览器请求全部成功。这些是验证脚本/环境问题，没有发现 Core 或业务模板产品缺陷，本轮未修改 Core、Templates 或 Demo 业务源码。该项只关闭采购/销售退货退款的桌面 UI/API/SQL 子项；ERP 部门/本人数据权限、真实第三方服务和 P2 总体验收仍开放。ERP 只按桌面视口验收。

### 2026-11-23 ERP 采购订单、入库及退货桌面闭环

使用当前固定 Demo JAR SHA-256 `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1`，在隔离 schema `yuheng_t4_erp_purchase_browser_20261123` 冷装 59 changesets。1440×900 浏览器从采购订单页新增并审批数量 10 的采购单；从采购入库页的可入库订单选择器选择该单，创建并审批数量 10 的入库；从采购退货页的可退货订单选择器选择该单，创建并审批退货数量 2。订单、入库和退货六个写 API 均 HTTP 200，浏览器 `pageErrors`、`consoleErrors`、`failedRequests` 均为空。

SQL 对账确认三张单据均已审核（status 20），采购订单明细 `count=10,in_count=10,return_count=2`，入库与退货明细分别关联正确订单产品和仓库；库存由 0 增至 10 后退回 8，流水为采购入库类型 70 数量 +10、采购退货类型 80 数量 -2。隔离 JAR 和 `dist` 的 612 个静态资源 SHA-256 逐项一致，59 个 changeset 完整，种子密码字段快照未变，未记录凭据。专用 MySQL/Redis、应用和 13433/16488/48275 已清理。机器证据位于 `erp-purchase-browser-20261123/runtime.json` 与 `browser.json`，可复跑入口为 `scripts/verification/erp_purchase_browser_runner.py` 和 `erp_purchase_browser_probe.js`。

验证过程中的三项失败均不是产品缺陷：首次隔离夹具仓库名超过 `varchar(20)`；第二次自定义静态代理并发加载模块时出现一次 `ERR_CONNECTION_RESET`，runner 随后改为由隔离 Spring Boot JAR 同源提供静态资源与 API；第三次完整浏览器流程已通过，但库存流水断言误将采购退货类型写为 50，经核对业务枚举确认为 80，之后在全新隔离环境复跑通过。没有修改 Core、Templates 或 Demo 业务产品代码；P2 总体验收继续进行中。

### 2026-11-23 ERP 盘点与调拨桌面闭环

使用当前固定 Demo JAR SHA-256 `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1`，在隔离 schema `yuheng_t4_erp_stock_browser_20261123` 冷装 59 个 changeset。1440×900 浏览器从实际库存盘点页面选择仓 A 与产品，页面读取账面库存 5，录入实际库存 7 并审批盘点；随后从库存调拨页面选择仓 A、仓 B 和同一产品，调拨 3 件并审批。创建/审批四个 API 均 HTTP 200，page errors、console errors、failed requests 均为 0。

SQL 确认盘点单状态 20，明细 `stock_count=5,actual_count=7,count=2`；调拨单状态 20，明细关联仓 A、仓 B 与对应产品；最终库存为仓 A=4、仓 B=3。库存流水新增盘盈类型 40 数量 +2、调出类型 32 数量 -3、调入类型 30 数量 +3。JAR/dist 612 个静态资源逐项一致，系统种子密码快照未变且证据未包含凭据；专用 MySQL/Redis、应用和 13434/16489/48276 已清理。机器证据 `erp-stock-browser-20261123/runtime.json`、`browser.json`，可复跑入口 `scripts/verification/erp_stock_browser_runner.py`、`erp_stock_browser_probe.js`。

探针过程中的失败来自验证实现：盘点表单预置一行且需先选仓库再读库存；调拨页仓库选择器的弹层 transition/同名选项使通用定位器选错列；最终 SQL 断言将盘盈流水类型误写为 90，业务枚举与真实流水为 40。每次均在隔离服务执行并由 runner 清理；提交前值断言及选择器定位修正后，在全新隔离环境完整复跑通过。无 Core、Templates 或 Demo 产品代码修复，P2 总体验收继续进行中。

### 2026-11-23 ERP 库存生命周期、失败事务及并发复验

使用当前固定 Demo JAR SHA-256 `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1`，在一次性 schema `yuheng_t4_stock_lifecycle_20261123_current` 冷装 59 个 changeset。真实 API 依次覆盖库存入库、出库、两仓调拨、盘盈和盘亏的审核、反审核、再次审核；每步核对库存。多明细出库的第二行库存不足时，接口返回既有业务码，单据仍未审核，第一行没有部分扣减，库存快照和 `erp_stock_record` 行数均保持不变。之后两个出库单并发审核，一个成功、一个按库存不足拒绝，数据库只有一笔竞争出库流水，最终库存为仓 1=1、仓 2=2。

运行器验证了制品 SHA、59 个 changeset、系统种子密码快照和资源清理；结束时专用 MySQL/Redis 容器已删除，13435、16490、48277 均无监听。结构化结果 `erp-stock-lifecycle-current-20261123/runtime.json`，详细请求和断言 `stock-lifecycle.json`；复跑入口为 `scripts/verification/erp_stock_lifecycle_current_runner.py`，契约测试为 `scripts/tests/test_erp_stock_browser_probe.py`。此前旧版本运行记录中的失败是探针期望忽略零库存行，而应用会保留该库存行；按当前真实 SQL 行为核实后，本轮固定 JAR 完整复验通过。没有发现需修复 Core、Templates 或 Demo 业务源码的缺陷；P2 总体验收仍进行中，真实第三方授权/支付、未提供后端的商城模板，以及 ERP 部门/本人数据权限模型仍未关闭。

**修正上述静态推断：** Core `TenantDatabaseInterceptor` 对已注册实体默认按租户过滤；只有 `TenantBaseDO` 明确返回“不忽略”，`@TenantIgnore` 才显式忽略，普通 `BaseDO` 在 interceptor 的现有分支下并不会自动忽略。因此不能由 DO 没有 `tenantId` 字段推断为全局共享。Templates 与 Demo 的 Member Liquibase 表也都有 `tenant_id` 列，插入由 Core 拦截器按当前租户填入。

跨租户第一次运行使用当前 Demo JAR SHA-256 `963149b3978618f370df9f63fe1db1a2841b7c3b2298d80766086cae27da5c97`，隔离 schema `yuheng_p2_member_dimensions_20261123` 和 59 个 changesets。基线没有第二租户，租户 2 登录返回 `1002015000`，在创建业务数据前停止；失败记录保留于 `p2-member-dimensions-20261123/member-dimensions-runtime.json`。第二次运行通过 Core 正式 `/system/tenant/create` API 创建租户 162 并分配普通套餐生成的角色/权限，未直接写系统租户、套餐、角色或菜单表。租户 1 和 162 各自真实登录后分别创建 Member 标签、分组和等级；35 个 HTTP 请求确认：创建行 SQL `tenant_id` 分别等于 1/162，本租户分页、详情和 `list-all-simple` 可见，对方租户三种读取均不可见；伪造 `tenant-id` 返回 403，拒绝前后标签/分组/等级表快照相同。冷装 59 changesets，种子密码未改变；应用及容器已清理，13375、16455、48222 无监听。最终证据 `p2-member-dimensions-final-runtime.json`。因此 Member 三类维度的租户隔离限定子项通过；不因先前静态误判修改 Core 或 Templates 源码。

### 2026-11-22 PMS 模板前端类型与构建复验

Templates 提交 `95c2903` 修复 PMS 模板 UI 在严格消费工程中的类型契约问题。修复内容包括 Element Plus `TreeInstance` 引用、回收站父级推断、知识库分组命令、项目列表命令、项目成员字典选项、迭代状态统计、工作台页签类型、Sortable 表格引用和项目模板业务 VO 回调类型；工作台“全部/迭代”页签不再把不存在的工作项类型传给 API。该修复属于业务模板，未写入 Demo 业务源码。

修复前新增的 `tests/test_pms_ui_type_contract.py` 按红灯运行；提交 `95c2903` 后 Templates 全量测试为 91 项通过；补充第二处 Sortable DOM 类型收窄后提交 `b2570b3`，定向契约和全量测试仍通过。以两个提交的 `template-pms/ui/pms` 复制到隔离消费工程，直接安装 `sortablejs`、`@types/sortablejs` 与 `@types/lodash-es` 后，正式 `src/views/pms` 路径的 `vue-tsc --noEmit` 诊断为 0，正式 Pay/PMS 目录也无自身诊断，Vite 生产构建退出码为 0；构建保留既有大 chunk 警告。完整隔离消费者类型检查仍有 Core compat 源码、Demo 系统组件重复默认导出，以及模板分享工具被从仓库外部路径直接纳入检查的问题，因此本轮只关闭 PMS 模板前端类型和 Pay/PMS 正式目录生产构建子项。

进一步核对发现，隔离消费者中的 `src/pay/app/index.vue` 是早期实验残留，缺少 `AppForm.vue`；Templates 的 `template-pay/ui/pay/app/components/AppForm.vue` 和原始项目均有该文件。该错误属于实验副本复制不完整，不能认定为模板缺陷；该副本中另有正式位置 `src/views/pay`，因此本次也不是干净的 Pay 模板初始化验收。

模板 README 已说明依赖和更新边界。`yuheng-demo` 仍只初始化 ERP/Member；PMS 页面、路由、后端源码、权限和自己的 Liquibase changelog 不因本轮模板修复自动进入 Demo。需要使用 PMS 时，应由使用者通过 Skill 显式复制和接入；后续模板修复先预览，再选择性合并到已有模块，保留消费端定制。
\n+### 2026-11-23 P2 当前固定 JAR 权限矩阵复验

当前固定 Demo JAR SHA-256 为 `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1`。此前 ERP 方法级拒绝矩阵和多类普通角色正向授权矩阵分别基于旧 JAR `fb663074…`，Member 管理端矩阵基于 `963149b…`；本轮均使用新隔离 schema、容器及专用端口补验，不覆盖历史记录。当前版 ERP 方法级拒绝 128 个请求中 111 个有 `@PreAuthorize` 的入口全部拒绝，逐次拒绝后的 33 张业务表快照不变；另 8 个上游没有方法级权限注解的认证读取入口仍可读。Member 管理权限矩阵 67 个请求通过，冷装 59 changesets。ERP 普通授权角色验证通过：基础资料 44 请求、采购/销售/资金主单据 30 请求、退货及库存辅助单据 50 请求、12 类单据更新/删除 49 请求、库存/库存流水/统计 11 请求；各组均冷装 59 changesets。

结构化结果分别为 `p2-erp-acl-current-20261123/runtime.json`、`p2-member-acl-current-20261123/runtime.json`、`p2-erp-master-auth-current-20261123/runtime.json`、`p2-erp-document-auth-current-20261123/runtime.json`、`p2-erp-aux-auth-current-20261123/runtime.json`、`p2-erp-mutation-auth-current-20261123/runtime.json` 和 `p2-erp-stock-auth-current-20261123-retry/runtime.json`。各运行结果记录当前 JAR SHA、专用容器删除及应用/MySQL/Redis 端口释放；凭据未写入结果。统计矩阵首轮将固定在 `2026-11-22` 的夹具误判为“今日”；实际 API 按 2026-11-23 运行日期正确归入“昨日”。Demo 验收 runner 改为用运行日期生成单据时间，3 项契约测试通过后以新 schema 完整复跑通过。没有发现 Core 或业务模板产品缺陷，本轮未改它们的源码。

本轮只关闭上述限定 API/SQL 授权范围。ERP 部门或本人级数据权限没有在模板中建模，不能视为已验收；真实社交/微信回调、真实短信与支付渠道、缺少完整后端模板的商城业务及 P2 总体验收仍开放。ERP 后台只按桌面场景验收。

### 2026-11-23 P2 代表性验收范围收口

按计划，本次 P2 目标是验证 Demo 已接入并可运行的代表性业务闭环，以及 Core、业务模板、Demo 和 Skill 的消费/选择性更新关系，不扩展成 P3 的逐页和全接口审计。固定验证 JAR SHA-256 `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1` 下，Member 的 App/API/SQL、管理端权限、租户隔离、生命周期、签到奖励事务与并发幂等均有隔离证据；ERP 的销售、采购、退货退款、盘点/调拨、财务桌面闭环，以及库存失败回滚/并发、权限和租户边界均有当前版本代表证据。模板 SQL 冷装/重复执行和 Skill 选择性创建/更新、冲突保护也已在隔离消费者验证。各子项机器证据和限制见本文件前述 P2 记录及计划 `docs/plans/2026-11-17-migration-verification-priorities.md`。

上述为当时的代表性范围结论。后续补验发现 Pay/PMS 从 Skill 创建后的可复用严格类型契约尚未闭合，P2 总项调整为**进行中**。真实社交/微信授权回调、真实短信/支付渠道、缺少完整后端的商城模板及 ERP 部门/本人数据权限仍按既定范围排除并另行跟踪；ERP 管理后台只验桌面。

### 2026-11-23 P2 Skill 首次创建 ERP/Member 消费工程验收

按用户确认的项目边界，在独立临时 Demo 副本中建立 Git 基线后移除副本内 ERP/Member 模块，再使用 Templates `1a48e5c52cae86cd03abd94a416b8be993dd7524` 的 `tools/template_update.py --apply` 和业务模板映射重新创建。源清单独立复核通过：ERP 309/309、Member 237/237，缺失、额外和字节差异均为 0。正式 Demo 未被移除或重建。

Skill 创建的模板文件不会自动包含特定消费者的包名/API 适配、严格类型修正、可选 Pay/PMS 集成、Demo 既有 changeset 身份兼容、动态路由 glob 或业务总 Liquibase changelog 注册。将 Demo 当前已审计的 47 项接入/定制差异选择性带入隔离消费者（本轮从相关映射路径实际应用 37 个有内容差异的文件），保留消费者自己的路由发现和业务 changelog。之后后端 `mvn -o -Dexec.skip=true test` 编译通过并运行 40/40 测试；`pnpm install --frozen-lockfile --ignore-scripts --offline && pnpm typecheck` 通过；Vite 生产构建 3544 模块通过（仍有现存大 chunk 警告）。Core 初始化 SQL 中 ERP 112/112、Member 26/26 权限注解均有对应权限键。Member 模板 SQL 保持模块归属，平台菜单、权限初始化由 Core 管理。

初始化创建与更新是不同阶段：首次创建显式选定模板并加入所需消费端接线；之后模板修复通过更新 Skill 预览、冲突分类与选择性应用，已有业务和定制保留，不会重建或清空 Demo。选择性更新冲突保护 7 项既有测试通过，更新端到端证据见 `p2-template-update-e2e-20261123.json`。结构化首次创建与构建结果为 `p2-template-skill-init-20261123.json`。本轮未重新运行数据库和 HTTP 工作流，相关当前固定 JAR API/SQL 证据仍按本文件前述项目单独索引；本子项关闭的是 Skill 创建、接线及构建验收。

### 2026-11-23 Pay/PMS Skill 消费补验

在隔离 Demo 副本中通过模板更新工具创建 Pay/PMS，并与已创建 ERP/Member 共同编译。Pay 原始映射遇到已有的两个 Member 钱包 API 适配文件时阻止覆盖；隔离映射保留这两个文件并创建其余内容。消费端手工接入 Core BOM、支付 SDK、业务 changelog、路由和 UI compat 路径；Maven 编译 907 个业务 Java 文件、40 项测试通过，前端 21 项测试、类型检查及 3880 模块生产构建通过。前端类型检查仍使用临时扩展的宽松声明，不能证明严格类型契约或 Skill 自动接线完成。

上述消费者打包的 JAR `30777dc9241173617a71838bb3226357857ed00317f81c49d32ec32c8d2c3d7a` 在一次性 MySQL/Redis 中通过 Pay 应用、钱包余额、PMS 项目和知识库公开分享 API/SQL，以及权限拒绝和双租户隔离；首次与重启均为 107 changeset，容器与专用端口已清理。结构化证据 `p2-pay-pms-skill-runtime-20261123.json`。本轮没有运行桌面浏览器或真实第三方支付渠道；先前桌面证据来自不同消费者制品。无 Core 或 Templates 产品源码修复；继续完善严格消费契约和可复用 Skill 接线。

继续使用 Core `8ce0d1f` 源码构建未发布本地 UI tarball `7e8cde7ac4c9b1ed765c6086b3333f9819fd70baee8225577bc7d051b364b07c`。隔离安装后，将 Pay/PMS 新增 compat 路径映射至真实 Core 源码，直接声明 `@element-plus/icons-vue` 和 `echarts-wordcloud`，类型检查、10 项定向测试与生产构建通过；现有请求等通用模块仍使用 Demo 宽松声明。全量测试的固定 registry 坐标断言因使用本地 `file:` 包失败，20 项通过。打包 JAR `0a4706735b78854ca847fb98cc7c8e446ad713a69b2aa99079710bf6b5a5994d` 后，独立环境 API/SQL、权限及租户检查和 107 changeset 冷装/重启通过；1440×900 浏览器实际创建 Pay 应用及 PMS 项目，页面错误和失败请求均为零，资源已清理。证据 `p2-pay-pms-current-core-20261123/runtime.json`、`browser.json`；`first-attempt.json` 记录第一次因 Playwright 未安装在启动浏览器前失败。当前制品公开分享页面浏览器、可复用 Skill 接线及剩余共享严格类型契约仍待验证；没有发布 npm 包或修改 Core/Templates 产品源码。

### 2026-11-23 Core 请求配置类型与 Pay/PMS 复验

Core compat 请求配置改为复用公开的 `YuhengRequest` 参数类型，校验必填字符串 URL 和请求选项；下载默认类型为实际 blob 响应，显式泛型和原有未标注响应兼容。类型负例先因 `any` 未拒绝错误配置失败，修复后独立 TypeScript 检查通过；上传内容类型和配置转发运行测试通过。Core UI 全量 136 项通过，跟踪的 vendor tarball 已刷新；类型检查消费者安装同一 tarball（SHA-256 `9b9baa19530a645d1f19cc078d3593162c6b6e668366535fc3ec7e6c292258bf`）并使用真实请求模块后，前端类型检查和 3880 模块生产构建通过。10 项定向消费者测试通过；完整消费者测试 20 项通过，1 项固定 registry 坐标断言因本地 `file:` 包失败。

包含新 UI 的隔离 JAR SHA-256 `66fdcf7563c025cdc5b5b335f92beca5026af9be7778fbf63aaec67a8bddbea1` 在一次性 MySQL/Redis 环境通过 Pay 应用、钱包、PMS 项目与文档分享 API/SQL、权限及租户检查，107 changeset 首次与重启一致；1440×900 桌面完成 Pay 应用、PMS 项目创建及匿名分享打开/刷新，浏览器错误与失败请求均为零。证据 `p2-pay-pms-core-request-types-20261123/runtime.json`、`browser.json`；专用容器和端口已清理。该轮打包跳过 Maven 测试，沿用此前同消费者 40 项测试证据。未发布 npm，正式 Demo 业务代码未覆盖；其余通用 shim 及未标注业务响应仍未严格类型化，P2 总项保持进行中。

### 2026-11-23 Core compat 类型与当前包复验

Core 提交 `bb90a58` 为 compat platform/setup 提供包内声明，修复 Descriptions 动态属性过滤类型，并去除 tagsView 对旧路由生成器的多余依赖；迁移 Skill 要求使用真实包的源码/声明和消费端直接依赖，不用宽松声明掩盖集成错误。Core UI 139 项、包边界及发布构建通过；治理测试 58 项中 56 项通过、2 项需专用数据库而跳过，治理链接和 bundle 检查通过。UI tarball SHA-256 `4fc06e4b744278e304a57e49edd7695823109e4cf4be032bf963be593d69ed88`。

隔离消费者安装该 tarball，直接声明 `vue-types`，多数 compat 入口解析包内真实源码，保留 platform/setup 接入 shim；完整 `vue-tsc` 和 3880 模块生产构建通过。打包跳过 Maven 测试，JAR SHA-256 `85240edb6794c5e30fb34dbf79ac35e6f1e5e892fe909186911fec5692fe5e17`。一次性 MySQL/Redis 中 Pay 应用、钱包、PMS 项目/知识库分享、权限拒绝和双租户检查通过，107 changeset 首次和重启一致；1440×900 浏览器完成 Pay/PMS 创建、匿名分享直接打开和刷新，页面错误和失败请求均为零。证据 `p2-pay-pms-queue128-20261123/runtime.json`、`browser.json`；隔离容器及 13401/16481/48261/5221 端口已清理。

首次浏览器复验缺少 Playwright 模块路径，随后默认静态服务队列在大量并发资源请求下出现连接重置；改用既有浏览器 runner 的队列大小 128 后完整通过。失败 JSON 保留在 `p2-pay-pms-current-core-20261123/`；该目录此前未跟踪的旧结果被本轮运行覆盖，无法从原路径恢复。含临时令牌的后端日志已删除。固定版本 manifest 下的 21 项测试触发 pnpm 自动安装 registry 包，不能算作上述本地 tarball 的测试。

首次消费验收发现 16 处旧 Core alias 被平台导入边界拒绝；Templates 提交 `c94ed6e` 将 Pay/PMS 用户 store、tagsView 及用户/部门选择器改用 `yuheng-ui/compat` 公共导出，模板契约测试先红后绿，Templates 全量 101 项通过。按旧模板提交建立消费端基线后，更新预览将 Pay 1 个、PMS 13 个文件全部分类为 `template_changed`，冲突、删除和未分类差异为 0；消费端模块文件为未跟踪状态，工具按设计拒绝覆盖，故仅按审查过的导入行在隔离消费者选择性合并，未触碰正式 Demo。更新后消费端 `vue-tsc`、平台导入边界检查、3880 模块 Vite 构建均通过。重新打包并运行 JAR SHA-256 `cb643f6b36d3c86d8c878e2a240e6596add6c27aae9dc7e8d42c3b2d3de6d001` 后，Pay/PMS API/SQL、权限拒绝、双租户隔离、107 changeset 冷装/重启以及 1440×900 浏览器的 Pay 应用/PMS 项目创建和匿名分享打开/刷新均通过；错误/失败请求为 0，专用容器、数据库、Redis 和端口已清理。证据 `p2-pay-pms-template-core-current-20261123/runtime.json`、`browser.json`。

隔离消费者仍有宽泛 compat 类型 shim，未标注业务响应沿用 `any`，platform/setup 另需声明 shim；局部兼容入口类型检查不能证明整棵旧 compat 树严格类型化。固定 registry 消费者的 21 项测试是在 pnpm 恢复 registry 版本后通过，不归属于本地 tarball。Core UI 本地包 SHA-256 `4fc06e4b744278e304a57e49edd7695823109e4cf4be032bf963be593d69ed88`，对应旧 alias 修复消费者 JAR SHA-256 `85240edb6794c5e30fb34dbf79ac35e6f1e5e892fe909186911fec5692fe5e17` 的同类浏览器/API 证据见 `p2-pay-pms-queue128-20261123/`。P2 严格类型契约仍开放；没有将局部通过外推为 P2 完成，也未修改或重建正式 Demo 业务代码。

### 2026-11-23 P2 当前 Core 包 Pay/PMS/Member 消费类型复验

Core `bb90a58` 的当前工作树仅新增公开包消费回归测试 `yuheng-ui/tests/compat/strict-consumer.test.ts`，通过 `yuheng-ui/compat/store/modules/tagsView` 公开导出验证 `useTagsViewStore().delView` 保持类型。定向 2 项、Core UI 全量 140 项测试和包边界检查通过；Core Vite 与发布类型构建通过。另执行裸 `vue-tsc --noEmit` 时，因其配置把整个 compat 旧源码树纳入消费者检查，出现 `.ts` 扩展、自动导入全局、旧组件及历史类型诊断；该命令不是 Core 发布构建配置，不能作为全树类型通过证据。

在 Skill 创建的完整隔离消费工程中，以模板已记录的旧基线先只读预览模板更新。Pay 1 个页面（收银台）、PMS 13 个页面均因消费端接入/定制而被归类为 `conflict`，工具按规则未覆盖；其余 Pay/PMS 映射文件保持 `unchanged`。此前不完整的 UI-only 临时消费者无后端和 Liquibase 目录，未用于更新/构建结论。模板测试全量 101 项通过。

将完整隔离消费者的 Core 依赖临时切换到当前工作树打包的本地 UI tarball（SHA-256 `4fc06e4b744278e304a57e49edd7695823109e4cf4be032bf963be593d69ed88`）后，Pay/PMS/Member 正式业务目录及当前消费接线执行完整 `vue-tsc --noEmit`，诊断数为 0；Vite 生产构建通过（保留既有大 chunk 警告）。前端 21 项测试和平台导入边界检查通过。测试依赖恢复至固定 registry 坐标后重跑，避免将 `file:` 制品坐标断言误记为产品失败。当前 registry 上的同版本 UI 包仍是旧内容，不能代表 Core `bb90a58`；本轮没有发布 npm，也没有修改正式 Demo、模板运行时代码或其定制。

**结论：** 关闭 Pay/PMS/Member 业务目录在当前 Core 包下的严格消费类型与生产构建子项。`pinia-plugin-persistedstate` 是 Core 已声明的运行时依赖；新包公开入口类型测试和业务消费者验证均通过。完整旧 compat 源码树仍存在历史类型诊断和宽泛兼容响应类型，单列为 Core 后续类型治理，不阻塞本次已接入业务目录消费验收。P2 总体验收仍按优先级计划保持进行中；本轮使用桌面业务工程范围，未做手机视口验证。

### 2026-11-23 P2 CRM/BPM 当前模板消费验证

**2026-11-23 CRM 客户主流程续验：限定子项通过。** 当前隔离 JAR SHA-256 `1f68267f1954badd56df05d8c0d9f624863ba7677ee5cb760b01a019c79d89eb`，Liquibase 冷装 91 个 changeset。API/SQL 完成匿名拒绝、登录、客户创建、owner/tenant 与 `crm_permission` 核对、分页、更新、软删除和权限清理；1440×900 桌面浏览器通过真实 CRM 动态菜单进入客户列表并读取该客户，页面错误、Console 错误和失败请求均为 0。21 个原始客户表和增量 changeset 已随 master changelog 生效；历史系统种子用户密码保持不变。证据 `p2-crm-customer-current-20261123/runtime.json`、`browser.json`，入口 `scripts/verification/p2_crm_customer_runner.py` 与 `p2_crm_customer_browser_probe.js`；新增 `test_p2_crm_customer_probe.py` 3 项契约测试通过。首次浏览器失败定位为临时角色夹具缺少 Core 平台 SQL 种子中既有的 CRM 根菜单/客户页菜单；补齐菜单授权后，又修正了同名标签定位器和先创建数据再打开列表的探针顺序，均为验收夹具缺陷，不涉及产品源码修复。专用 schema、Redis 和 16501/48301/48302 端口已清理。此结果关闭 CRM 客户管理代表主流程，不代表 CRM 其它业务页面、BPM 基础消费或 P2 总体验收完成。

**2026-11-23 P2 续验及修复：** 按后端 CRM VO 确认合同创建表单应把商机 `businessPrice` 映射为合同 `contractPrice`，但不能原地修改商机 API 返回值；改为创建独立合同产品对象。客户限制列表补齐后端实际返回的用户/部门类型，并显式标注 formatter 行类型；漏斗 ECharts 局部 option 类型允许合法的 `name`/`type` 配置；回款计划 emit 签名明确返回 `void`。回归契约先失败后通过，Templates 全量 108 项 Python 测试通过。

将审阅后的 CRM 文件选择性复制到既有隔离消费者，没有触碰正式 Demo。当前隔离消费者 `vue-tsc --noEmit` 仍失败，共 200 条：CRM 路径 0 条、BPM/其他业务页面路径 163 条、Core compat 包 37 条；因此 BPM UI 类型消费尚不通过，基础流程页面仍是 P2 待办，缺失的流程设计器/FormCreate/打印编辑器具体资产可按可选重型功能放入 P3。Vite 生产构建成功（3832 个模块）。模板 mapping 中 BPM 已明确声明 Flowable starter 与 `flowable-bpmn-layout`，版本由 Core BOM 管理；隔离消费业务模块执行 Maven 离线 `clean test`，从零编译 906 个 Java 源文件通过。旧记录所述 Flowable 依赖缺失已关闭。

CRM 客户代表页面/API/SQL 真实运行闭环已由上方同日续验关闭；CRM 其它主体页面和 BPM 基础消费仍开放。隔离目录 `/tmp/yuheng-p2-crm-bpm-clean-d5jtBb`；类型日志 `/tmp/yuheng-p2-crm-bpm-typecheck-p2-fixes2.log`；Vite 命令为 `pnpm run build`；Maven 在该目录通过 `mvn -o -f yuheng-demo-server/pom.xml -pl yuheng-demo-business -am clean test`。当前 Core registry 固定包下 CRM+BPM 清洁消费者构建仍失败，不能以旧 tarball 成功记录代替。未使用或修改共享数据库、Redis、用户密码和服务端口。本次没有改 Core/Templates/Demo 产品源码；只改 CRM 隔离验收运行器、浏览器探针及测试、计划和证据；未提交。

在 Demo 基线的临时副本中仅移除已有业务模块目录，初始化临时 Git 基线，再依次通过 `template_update.py` 使用 BPM、CRM 官方 mapping 创建模块。正式 Demo 未增删、重建或改写 ERP/Member 业务代码。隔离消费者使用固定 `yuheng-ui@0.1.0-SNAPSHOT` registry 包和 Demo 锁文件；pnpm frozen offline install 通过。

首次构建定位到 CRM 地区统计 `PortraitCustomerArea.vue` 仍引用消费端私有 `@/plugins/echarts`。在 Templates 添加公共 compat 导入契约后，测试先红；将模板导入改为 `yuheng-ui/compat/plugins/echarts` 后，模板 mapping 契约 3 项通过，模板更新工具把修改归类为唯一 `unclassified_difference`，未覆盖消费者文件。按审查过的单行变更更新隔离副本后，旧本地 Core tarball 下 Vite 生产构建曾通过，3832 个模块转换；此结果现仅作为历史记录。

同一隔离消费者的 `vue-tsc --noEmit` 仍失败，共 262 条诊断，其中 CRM mapping 路径 73 条、BPM mapping 路径 168 条，其余来自 Core compat 源码及现有消费端声明映射。CRM 可确认的模板主体问题包括多个 API 参数隐式 `any`，其余需去除消费端宽泛兼容 shim 并使用当前 Core 本地 tarball 后再分类；不能把 shim 覆盖的导出类型问题都归给模板。BPM 页面还引用消费端私有的部门 API、认证/消息/store 工具及未映射的 SimpleProcessDesignerV2、bpmnProcessDesigner、FormCreate、文件上传等资产，且若干 API 参数隐式 `any`。重型流程建模和打印编辑体验仍属 P3，但使基础模块类型/生产构建可消费所需的公共入口和基础资源仍属 P2。另以同一 Demo 基线单独初始化 CRM（不含 BPM）并 Maven 编译通过，确认缺失 Flowable 依赖只由 BPM 模块引入；将 CRM 与 BPM 一起消费时才触发 Flowable 类型缺失。

按 mapping 初始化后的 Maven 离线编译失败，错误集中在 BPM `org.flowable.*` 类型不可解析：Demo 业务模块只依赖 Core `yuheng-server`，消费 POM 中没有 Flowable 运行时依赖。模板是源码复制而非运行时依赖，因此应在可选模板接入说明/Skill 中显式声明与 Core BOM 对齐的 Flowable 依赖，并由使用者选择启用；目前这一接线尚未补齐，后端编译与 BPM API/SQL 业务流程尚未通过。此前计划表格称“后端编译通过”是旧临时消费者证据，本次当前基线复验已纠正为失败。

**2026-11-23 最新当前包复验补记：** 对上述隔离消费者重新使用当前 Core registry 固定包重新安装依赖，并重跑 `pnpm run build`；Vite 转换 3980 个模块后失败，报告 21 个构建错误，退出码 1。其后在同一隔离消费者、同一 lockfile 状态再次运行，失败可重现为 21 项：`@/utils/formCreate`、`@/utils/file` 和 `@/components/bpmnProcessDesigner/...` 均无法从消费工程解析；Vue 插件读取 `@wangeditor-next/editor/dist/css/style.css` 时也因 package 子路径读取方式失败。该 CSS 路径在消费者安装的 wangEditor 5.7.16 `exports` 中确实存在，因此不能简单归类为缺少 npm 包；需要用公开 CSS import 方式/构建插件验证根因。BPM 页面还直接引用未映射的 SimpleProcessDesignerV2、FormCreate、bpmnProcessDesigner 组件，消费端私有的部门 API、认证/消息/store 工具，以及 Core compat `propTypes` 类型不匹配。Core 包有部分 FormCreate、UploadFile、formCreate、propTypes compat 子路径，但模板仍以消费端源码 alias 直接导入；没有找到两个流程设计器的 Core 源码或公共入口。隔离消费者只通过 Core BOM 管理 BPM 的后端依赖；前端组件自身需要的依赖必须在模板映射中作为选择性消费依赖明确声明。

该失败表明当前 BPM 完整 UI 尚不能清洁消费；不能把它整体降级为 P3，也不能用空 shim 或从验证 Demo 长期携带源码解决。BPM 基础页面/API/SQL、Liquibase、初始化数据及公开依赖接线继续属于 P2；完整流程设计器、表单设计器、打印富文本编辑器及真实外部流程连接可列 P3，但必须在 mapping/Skill 里标明可选功能边界，并让 P2 基础 UI 能独立构建。下一步在 Templates/Core 源头按 P2 页面集合补齐公共接线和显式依赖，先加消费契约回归测试，再通过 `template_update.py` 预览并仅向隔离消费者选择性同步。

截至本次续验，矩阵有 12 个模板标记生成待验收；其中 ERP/PMS 已有较多主体消费证据但需复核矩阵状态，CRM 客户代表闭环刚通过，BPM 基础消费仍未通过。P2-C 尚需主体消费验证的模板是 8 个：AI、IoT、MES、FMS、HRM、IM、OA、WMS，按 P2-C1/P2-C2 分批。不得把依赖外部服务/硬件的长尾要求用于豁免主体业务、桌面页面、表结构、Liquibase 或清洁消费构建。CRM 浏览器夹具在独立隔离 schema 中完成，不改写正式 Demo，也未修改 Core/Templates 产品源码。

### 2026-11-23 P2 WMS 当前模板消费验证

**状态：WMS P2 主体消费闭环通过；P2 总体验收继续进行中。** 在 Demo 风格临时消费者使用 WMS 模板源码、当前 Core UI 包和当前 Demo 后端构建隔离制品，JAR SHA-256 `8fa2b4b8bf689710d2962ff48b15d46ae01ee13745a8f54bfec972c3a10eba92`。专用 schema `yuheng_p2_wms_20261123` 首次与重启均为 76 个 changeset（WMS 17 个），创建 16 张 WMS 表；检查 `wms_inventory` 的租户/SKU/仓库复合唯一索引。API 验证仓库及商品分页、仓库新增/更新/删除、库存查询与匿名拒绝。1440×900 桌面真实浏览器完成登录、仓库列表读取及新增、修改、删除，8 个 WMS API 响应均为 HTTP 200，SQL 证实修改后名称及删除后的软删除状态。具体运行及清理结果见 `p2-wms-current-20261123/runtime.json`。

验证时先后修正了验收探针：登录租户输入默认已有正确名称，早期失败由于探针凭据错误；“修改”按钮曾被探针误称为“编辑”；页面更新数据时等待器错过了列表刷新响应，且编辑详情加载需要等待详情 API。使用仓库现有静态服务器队列后完整复跑通过。这些是夹具/探针问题，没有触发 WMS 产品源码修复。页面中一次现有头像资源请求被 Chromium ORB 拦截，WMS 页面操作和 API 不受影响。模板仓库全量测试 114 项通过。临时 schema、`wms_probe` schema 授权、隔离 Redis、应用与 UI 端口已清理；此前存在的 MySQL 隔离工具容器保留。没有修改正式 Demo 业务源码或共享数据库。

WMS 关闭后曾剩余 7 个 P2-C 模板；2026-11-24 HRM 主体消费闭环通过后，目前尚未闭合的模板为 **6 个**：AI、IoT、MES、FMS、IM、OA。HRM 的 BPM 审批扩展及整仓类型边界仍单独留在 P2 总门禁。WMS 的真实硬件、设备链路和低频业务组合列为 P3；主体业务、桌面页面、表结构和 Liquibase 均已在 P2 覆盖。
## 2026-11-24 P2 FMS 消费验证

**状态：部分通过，FMS 仍为 P2 待验收。** 在 `/tmp/yuheng-p2-fms-consumer` 按 FMS mapping 选择性建立隔离消费者；来源映射复核为 376 个文件一致，2 个消费者独有 ERP 统计 Mapper 保留。最新 Core UI tarball SHA-256 `c6b2e92122d5ca879557b0ed6d86fb4f236936f62d7d70193824084b2d4a8984`；在该包下 FMS 前端完整类型检查无诊断、Vite 3759 模块生产构建通过；Demo 风格隔离消费者 Maven offline 打包通过。用于完整 typecheck 的唯一后续修正是按模板版本选择性同步 Member `UserAftersaleList.vue` 已有的 `getStrDictOptions` 修复。Core UI 141 项测试、Templates FMS/Schema/迁移/资源定向测试 64 项通过。

隔离 MySQL 8.0.33 上通过当前 JAR 的 Liquibase 冷装和重启复验：总计 95 changesets，FMS 36，30 张业务表、494 列、27 个 FMS 主动记录唯一索引；30 张表初始为空。JAR SHA-256 `740d6a4b57f3d4195d0d4e71dee0365959b3912e2b4062a7c24e6d8b2ef1ef34` 的 1440×900 桌面浏览器账套新增/列表流程及 API/SQL 创建、编辑、回读通过，页面错误与失败请求均为 0。

**P2 阻塞：** 账套初始化返回 FMS 业务码 `1052105025`，缺少所需科目 `560107`。失败前后 30 张 FMS 表行数快照一致，证明事务完整回滚；种子系统用户密码未改变。源码追查确认初始化依赖 `fms_subject_template`，但 Liquibase 只建空表，上游工作树、原始全量 MySQL 脚本及本地工作区都没有权威标准科目清单；上游结账模板测试中的科目是测试夹具，不能当作生产种子。FMS README 和 Templates migration matrix 已记录该数据源/授权缺口；不将其降为 P3，也不以单独补一个缺失编码代替完整科目树。

两次临时验证失败分别为消费 changelog 残留了未映射 CRM include，以及标准科目数据缺失；失败结果保存在本目录的 `startup-missing-crm-include.json`、`initialize-missing-subject-seed.json`。最终隔离运行结果 `runtime.json` 和桌面结果 `browser.json`。一次性 MySQL/Redis、schema、应用和 13507/16507/48307 端口均已清理；正式 Demo、共享数据库、共享 Redis 与历史密码未触碰。可复现构建结果使用固定 Core tarball，未修改正式 Demo 或其模板接线。

## 2026-11-24 P2 HRM/BPM 消费边界复核

**状态：HRM API/SQL 与桌面主体流程通过；严格类型消费门禁未闭合，BPM 基础消费也未通过。** 本轮使用 `/tmp/yuheng-p2-hrm-final.mNKZYW` 隔离消费者，不修改正式 Demo。使用 Core vendor UI tarball SHA-256 `cf59be85270246f68434fcac810d88da2e81e6963ef99e63a6ea91bdf616342d`；HRM+BPM 后端离线编译 1202 个源码通过，Vite 生产构建转换 4062 个模块通过。完整 `vue-tsc` 受 BPM 私有设计器/FormCreate 等页面及 `yuheng-ui` compat/layout 源码诊断阻断；模板路径筛选仅是错误归属线索，不能证明 HRM 清洁包消费者类型检查通过。隔离消费者的宽泛 `useTagsViewStore` shim 在当前运行 POM 版本中仍存在，故本轮不能据此宣称 HRM 真实 Core store 类型已验收。Core 包消费者契约 3/3 通过；尚无需修改 Core 运行源码的已证实缺陷。

隔离 JAR SHA-256 `4d73591ba3df70be8db360f92374fe8cdae8f8b09a55f953213eca3f9b88f109` 完成真实 MySQL/Redis 运行：Liquibase 首次和重启均为 118 changesets，HRM 51 个、50 张业务表，HRM 初始业务表为空。员工创建、更新、删除、部门统计/分页和招聘渠道创建/更新读取通过；重复手机号被业务规则拒绝且 SQL 快照未改变。1440×900 桌面 `/hrm/recruit/settings/channel` 完成新增并在列表回显，页面错误、console error、失败请求均为 0。历史系统用户密码不变，隔离 MySQL/Redis、应用和 13509/16509/48309 已清理。机器结果为本目录 `runtime.json`、`browser.json`。

HRM mapping 已声明 Core compat 子路径、直接 npm 依赖、统一 Liquibase、动态 UI 路由及选择 HRM 时需解除的 `/admin-api/hrm/**` 禁用兜底。此前预览出现的 10 个既有消费者 `unclassified_difference` 文件没有被强制覆盖；本轮仍只在隔离消费者验证。HRM 的主体页面/API/SQL、后端/Vite 消费构建及 Liquibase 门槛已有通过证据；严格类型门禁未通过，不能将 HRM 从 P2 待闭合项移除。未覆盖 HRM 全量薪资/绩效组合和 BPM 请假审批扩展。完整 BPM UI 类型消费及基础 API/SQL 流程仍是独立 P2 项；流程设计器和表单/打印重型编辑器可放入 P3，但不能用来豁免 BPM 基础消费。

本轮 HRM 主体 API/SQL/桌面范围通过，但类型门禁未闭合；P2-C 主体仍有 **6 个模板未闭合**：AI、IoT、MES、FMS、IM、OA；HRM 主体已通过但严格类型门禁未闭合。FMS 账套 CRUD 与迁移部分通过，但初始化缺权威标准科目数据，继续阻塞 P2；IM 已通过隔离 Vite/Maven 消费构建，但其类型检查、Liquibase、API/SQL 和桌面业务闭环仍待验证；OA、AI、IoT、MES 的主体清洁消费构建和业务闭环仍待验证。外部模型、真实硬件/时序库及复杂跨域流程维持 P3，主体关系型表、页面、API、Liquibase 和消费构建继续留在 P2。

### 2026-11-24 P2 IM 消费构建预检

**状态：部分通过，IM 仍未达到 P2 主体验收。** 在已有隔离消费者 `/tmp/yuheng-im-p2-consumer-build` 中只验证消费构建，不修改正式 Demo。Maven 首次失败暴露 IM mapping 漏声明直接依赖 `com.github.houbb:sensitive-word`；将版本来源指向 Core `yuheng-dependencies` BOM，并仅在临时消费者 business POM 加入对应依赖后，`mvn -f pom.xml -pl yuheng-demo-server/yuheng-demo-business -am clean test` 编译 680 个源码成功。该 Maven artifact 首次尝试离线时未缓存，在线从配置的 Maven 镜像解析后通过。模板 mapping 契约已增加此依赖断言。

同一隔离消费者完整 `vue-tsc --noEmit` 失败：当前复跑的 IM 源码路径只报告 `src/views/im/home/index.vue` 对 `appStore.getTitle` 的类型错误；其余 18 项来自 Core `yuheng-ui/compat` 当前包源码。此前日志中的 IM 对 Core system user/dict/formatTime/utils exports 缺失及 `FriendAddDialog.vue` 用户形状不匹配，来自不同 Core tarball/临时 shim 状态，不能合并成当前固定包缺陷结论。该检查显示模板依赖 Core store getter 的公开类型契约尚未在当前包复现，应按实际消费包分层验证，不能用宽泛 `any` shim 掩盖。Core compat 诊断不记作 IM 模板错误；在该类型门禁闭合前 IM UI 清洁消费仍失败，属于 P2。尚未完成独立无 shim 类型检查、Vite/Maven 应用打包、Liquibase 冷装/重启、HTTP/SQL、桌面代表流程或真实 LiveKit 外部连接。真实 LiveKit 通话链路可列 P3；IM 关系型消息/好友/群组主体、基础页面和消费构建继续属于 P2。机器测试只有模板消费契约 4 项通过；该批次未产生数据库或服务进程。

**2026-11-24 P2 IM 模板修复与干净初始化消费复验：部分通过，仍留 P2。** 定位到 IM 首页标题使用 `appStore.getTitle` 引发模板路径类型诊断；模板改为从当前 `document.title` 去除已有未读前缀后设置新值，避免依赖该 store getter，也避免子路由切换时重复累积前缀。消息提示音原映射到 Core 包未公开的 `compat/assets` 子路径；将该 MP3 纳入 IM 模板资源 `template-im/ui/assets/audio/im/message-tip.mp3`，mapping 复制到消费端 `src/assets/audio/im/message-tip.mp3`，无需消费端预置文件。新增 IM 消费契约覆盖标题 getter 和音频归属，5 项通过；Templates 全量 Python 测试 124 项通过。使用 Skill `template_update.py` 在临时干净 Git 消费工程初始化/复核 IM 后，Vite 生产构建转换 3877 模块并成功输出提示音资源；Maven `clean test` 离线编译 680 个业务源码通过。全量 `vue-tsc` 仍失败，共 42 条诊断：Core compat 源码诊断和隔离基线中已有的 Member 售后页面类型错误；没有 IM 模板路径诊断。另一个已有 IM 消费副本的首页与模板存在 `unclassified_difference`，更新工具正确拒绝覆盖；未把模板变更强推到它或正式 Demo。当前没有对 IM 执行 Liquibase 冷装/重启、HTTP/SQL、权限/租户或桌面业务浏览器闭环，也未验证运行时标题行为和 LiveKit 外部通话。外部 LiveKit 可另列 P3，基础关系型主体仍是 P2。验证消费副本位于 `/tmp/yuheng-im-p2-clean`，检查日志 `/tmp/yuheng-im-p2-clean/typecheck.log`；临时工程仅用于此构建，正式 Demo 未改动。

### 2026-11-24 P2 OA 消费与 SQL 契约复验

**状态：部分通过，OA 继续留在 P2。** 在 `/tmp/yuheng-oa-p2-consumer` 隔离消费者使用 Templates OA mapping 和 Core vendor UI tarball（SHA-256 `cf59be85270246f68434fcac810d88da2e81e6963ef99e63a6ea91bdf616342d`）。保留消费者既有 Core compat 导入时，严格检查确认 OA 邮件 `timeout`、Core `findNode`、部门 API、wangEditor 直接依赖均能由真实 package contract 解析；新增 3 处 OA 页面类型修复后，OA 源码路径为 0 条类型诊断。整仓 `vue-tsc` 仍有 162 条来自 BPM 基础消费缺口、Core compat 源码及隔离基线 Member 页面的问题，不能据此宣称整个 UI 消费类型门禁通过。隔离后端 BPM+OA+既有业务 `mvn clean test` 离线编译 1335 个 Java 源码通过；Core compat 141 项测试、Templates 全量 Python 测试 125 项通过。OA 48 个实体表与 001 SQL 的 48 张表名及字段契约匹配。

修复留在 Core/Templates 源头：Core compat 树类型、部门树选择器及请求配置消费者契约补强；OA 两个讨论页排序参数显式收窄到 Core 发布契约接受的非空值，文件菜单命令、目录过滤结果和邮件协议事件参数补齐严格类型。mapping 已声明 `@/api/system/dept` 和 wangEditor 依赖。`template_update.py` 预览识别 5 个已有 OA 消费适配文件为未分类差异并拒绝覆盖；没有强制覆盖或修改正式 Demo。Core UI 测试全量 141 项通过，Core 本地 vendor 包重打包成功。

OA Liquibase 既有表保护在一次性 schema `yuheng_p2_oa_conflict_20261124` 上通过验证。使用隔离消费者 bootstrap JAR SHA-256 `0c0b5c1ca888174f919c12c0fb00f3e66523f93ad3707614544488b11c8978b8`，启动后执行 109 个前序 changeset，遇到预置的 `oa_attendance` 表后由 `oa-schema-001` precondition 按预期 HALT；哨兵行 `(1, keep-me)` 未变，OA changelog 执行为 0。

随后在干净 schema `yuheng_p2_oa_cold_20261124` 使用同一 JAR 首次冷装和重启复验均成功：总计 159 changesets、OA 50 个、48 张 OA 表、794 列、56 个非主键索引；OA 业务表行数为 0。两次启动都正常，数据库快照一致。应用停止后精确清理本轮两个 schema、两个一次性 DB 用户、专用 Redis，以及 51783/51784/51785/51786 端口资源。隔离 MySQL 工具容器和既有 `yuheng_p2_oa_20261124` schema 保留，未修改。

仍未完成 OA HTTP/SQL 主流程和桌面浏览器闭环。隔离消费者 Vite 全量构建被 BPM 流程/表单设计器与私有资源缺口阻断；bootstrap Maven 打包正常入口被 Core 强制的固定 registry 坐标检查阻断（本地 `file:` tarball 不接受），本轮为隔离数据库验证使用 `-Dexec.skip=true` 打包。真实邮箱服务和外部发送可按计划列入 P3；OA 基础 API 和至少一条关系型桌面流程继续属于 P2。
