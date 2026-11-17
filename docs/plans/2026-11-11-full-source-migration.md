# 完整源码迁移实施计划

**workId:** YH-20261111-full-source-migration  
**授权依据:** 用户要求按既定计划完成前后端迁移；沿用完整管理端设计及此前确认的三仓库和 SQL 治理边界。  
**规格:** `docs/specs/2026-11-02-admin-ui-full-integration-design.md`，以及 `yuheng-core/docs/superpowers/specs/2026-11-10-yuheng-three-repository-architecture-design.md`。  
**版本:** core、demo 和基线均以工作区当前版本及未提交变更为准；验证时记录提交和状态。  
**PHASE_GATE:** 规格和实施授权已确认，完整管理端截图为视觉基线；范围内技术拆解由本计划补录，implementationAllowed: true。保留现有业务变更、历史密码和已执行 Liquibase changeset。

**2026-11-15 续验状态：** 菜单管理、文件列表、文件配置已完成同隔离数据桌面对照；WebSocket 仍有 CONNECTING/CLOSED 差异待排除代理传输影响，窄屏视口未能统一，不计响应式验收。专用 schema、用户及 Redis DB 5 已精确清理。证据见 `docs/verification/2026-11-11-full-source-migration/verification.md`。T1/T3/T4 均保持开放。

**2026-11-17 配置页续查：** Demo 桌面筛选/重置/取消通过，隔离配置和密码快照不变；原版窄屏的菜单浮层同样拦截搜索，Demo 窄屏资源连接重置及原版桌面超时尚未排明。先前两张菜单截图均来自 Demo，不是两端对照；详细条件和资源清理证据见 verification.md 的“配置页响应式探针续查”。T1/T3/T4 保持开放。

**2026-11-17 配置页同数据复跑：** 两端桌面筛选/重置/取消及弹窗几何一致；移动端两端在填写前已被相同基础设施菜单浮层覆盖，触发机制尚未确认。此次无浏览器资源失败，上一轮连接重置未复现；隔离快照不变且资源已清理。详见 verification.md“配置页同数据桌面对照及浮层定位”。T1/T3/T4 保持开放。

**2026-11-17 配置页移动续查：** 两端通过侧栏展开后点遮罩关闭，可恢复搜索并完成 10→0→10 筛选；两端编辑框均宽 156px、内容宽 177px，键值字段不可见，移动编辑未完成。菜单路由自动展开与折叠状态是待验证线索；详情见 verification.md“配置页移动抽屉循环与编辑框”。T1/T3/T4 保持开放。

**2026-11-17 配置弹窗定位：** 两端默认 40% 宽度在 390px 视口为 156px，表单输入框实际宽 0；全屏后可修改并取消，隔离配置/密码快照不变。默认窄屏可用性问题尚未修复，详情见 verification.md“配置弹窗窄屏字段定位”。T1/T3/T4 保持开放。

**配置表单窄屏修复方案：** 已有隔离浏览器红灯证明默认 40% 宽度在 390px 使实际输入框宽度为 0。优先限定配置表单的 Dialog 宽度：桌面保持 40%，窄屏提供足够的字段空间且不超过视口；不统一覆盖所有显式 Dialog 宽度。先在真实组件预览验证 320/390 和桌面尺寸、字段可编辑及取消，再对 Demo 实际消费构建和隔离浏览器复验；原版作为差异基线保留。其它默认宽度表单须单独盘点，不能据这一页宣称共享组件全范围完成。

**配置表单窄屏修复结果：** Core `ConfigForm` 使用 `min(100%, max(40%, 400px))`；Demo 真实隔离浏览器在 320/390/1440 视口均可直接编辑和取消，弹窗及字段宽度符合约束，原版仍保留零宽字段作为基线。Core 125 项 UI 测试、生产/声明构建和边界检查，Demo 14 项测试、类型、生产构建和导入边界均通过；隔离数据和密码快照不变。静态资源连接重置在服务端对应 200 响应，完整网络清洁度仍开放。详见 verification.md“配置表单窄屏可用性修复”。

**角色页窄屏续查（2026-11-17）：** 隔离浏览器在 320px 下侧栏宽度为 0、遮罩不存在，但系统菜单浮层覆盖新增按钮；展开侧栏再点遮罩后可打开角色表单、填写并取消，弹窗宽 320px、输入框宽 156px、未发角色写请求。这是恢复路径，不是初始遮挡修复。390px 本轮 CSS 请求连接重置导致登录页未加载，整轮未通过；隔离容器及端口已清理。Core 与本地原始网页的菜单文件除导入路径外一致，具体触发机制仍待验证。详见 `role-page-sidebar-cycle-20261117/result.json`；T1/T3/T4 保持开放。这里的窄屏指管理后台网页，不代表独立 uni-app 移动应用验收。

**T3 折叠菜单浮层修复门禁：** 沿用本 workId、冻结规格/计划及用户持续实施授权，codeVersion `0.1.0-SNAPSHOT`、governanceVersion `0.2.0`、knowledgeVersion `0.1.0`；原型不需要，implementationAllowed: true。已知 320px 隔离浏览器红灯；Element Plus 折叠时清空展开项，而菜单同步在折叠后仍调用 `open`。验收：收起时不自动打开路径，重新展开时恢复当前路由菜单；320/390/桌面真实页面可操作，桌面折叠悬停及菜单导航不回归，记录 Console/Network 和清理结果。仅修改 Core 菜单与定向测试、Demo 隔离探针及证据；不操作共享服务、历史密码和已执行迁移。

**本轮未完成结果：** Core 菜单同步暂加折叠状态检查，未提交；真实隔离页面 320px 新增按钮无遮挡、角色表单可填及取消，1440px 同样通过，均无角色写请求。390px 遭多项静态资源 `ERR_CONNECTION_RESET`，登录未完成，整轮失败；服务端默认连接等待队列为 5，是否是原因尚未证实。隔离容器与四个端口均已清理。Core 现有 Vitest 29 文件/125 项通过，Demo 使用本地 Vite 构建 3673 模块通过；`pnpm run build` 自动安装遇 registry 404，不能作为固定版本构建通过。桌面折叠悬停、展开后路由定位、390px 和定向回归仍需验证，不能宣称该修复完成。证据见 `role-page-collapse-fix-20261117/result.json`。

**默认弹窗宽度盘点：** 当前 Core 兼容 Dialog 默认宽度仍为 `40%`；`python3 scripts/verification/dialog_width_inventory.py` 扫描到 System 21 处、Infra 12 处直接调用没有显式 width，其中包含角色、字典、用户和部门表单。该结果只是静态候选清单，动态组件、包装组件与 `v-bind` 透传无法由此脚本解析；具体页面需要以真实浏览器的 `.el-dialog` 与表单字段几何、可操作性和取消/写入行为逐项核验。配置表单已有专门修复，不能把该修复推广为其它表单已通过；T3 整体仍开放。

**2026-11-16 当前运行态复核：** 共享 UI `/login` 静态页面 HTTP 200，隔离 In-App Browser 可读到登录表单；只点空密码登录，未提交凭据，未产生登录或业务写入。共享后端未认证权限信息 GET 等待 6 秒超时，`/actuator/health` 404/约 0.09 秒；生命周期日志出现 `NoClassDefFoundError: ch/qos/logback/classic/spi/ThrowableProxy`，但尚未证明该异常是所有 API 超时根因。没有重启/停止共享进程或操作共享 DB/Redis。证据：`docs/verification/2026-11-11-full-source-migration/current-state-20261116.json`。本轮没有登录后页面/Network/Console/响应式验收；T3、T1、T4 均保持开放。

**2026-11-16 T3 隔离浏览器抽查续验：** 独立 MySQL/Redis、schema `yuheng_t3_20261116`、后端/UI 48173/5174 成功冷装并运行。Liquibase 54/54、150 表、21 用户均有密码字段、`system_operate_log.success` 列为 0；登录真实成功，首页显示授权/入口计数及系统/基础设施快捷入口，用户管理页真实 API 加载 15 行，基础设施侧栏能展开。只读控件观察，未做状态切换或其它业务写。隔离 app/UI 和容器均清理，专用端口关闭，共享资源不变。受 browser wrapper 限制没有截图、Console/Network 完整记录、视口控制与全页面/写交互覆盖；T3 仍开放，完整证据见 verification.md 的本标题小节。

**2026-11-15 WebSocket 修复：** 已用本地真实 Upgrade 握手和帧回声测试确认 Demo 静态代理原先将 `/infra/ws` 当作 SPA 路由返回 200 HTML；在 `scripts/ui_server.py` 添加 WebSocket 握手转发和双向 TCP 隧道后，测试验证收到 101 且帧往返一致。Demo 生命周期/模块回归 26 项通过、7 项按隔离服务条件跳过；T3 仍需真实 Core WebSocket 端点浏览器验收及其它未完成覆盖，T1/T4 保持开放。

**2026-11-15 WebSocket 后端续验：** 隔离 JAR 的 `/infra/ws` Upgrade 返回 404；嵌套 starter 和自动配置声明存在，但 MVC 映射/条件尚未查明。隔离 MySQL schema/用户、Redis DB 8 已清理，历史口令未改。首轮因 Redis 索引属性误用进入默认 DB 0，未做清理以免误删既有键；事故和边界见 verification.md。WebSocket 真实端到端子项未完成。

**2026-11-15 WebSocket 续验完成：** 根因是 `SpaController` catch-all HandlerMapping 先于 Spring WebSocket HandlerMapping 返回 404；Demo bootstrap 仅提升 `webSocketHandlerMapping` 优先级。修复前测试编译失败，修复后目标回归和 40 项 Maven 全量通过；隔离运行实际 `/infra/ws` 握手 101、ping/pong、示例消息回声和关闭均通过，专用 DB/schema/用户已清理。T3 WebSocket 子项关闭，T1/T3 其他覆盖/T4 保持开放，详见 verification.md。

**2026-11-15 T3 登录日志续验更正：** 后续 Chrome 控制恢复后，已使用同一隔离 schema `yuheng_t3_loginlog_20261115`、后端 48124、Demo UI 5179、原版 Vite 5186 和 Redis DB 12 完成浏览器验证。原先“本轮无法导航、没有页面 DOM/截图”的记录是当时状态，现由本轮实际页面观察和同尺寸截图补正；此前旧记录描述的清理发生于更早的同名环境，不能作为本轮清理依据。本轮最终停止 PID 59145/59146/59147，精确删除本轮专用 schema/账号，并将启动前为空的 Redis DB 12 清至 0；共享 `yuheng_demo` 保留且历史密码未改。登录日志桌面对照、390×844 响应式子项已完成；T3 其余覆盖、T1/T4 仍开放。

**2026-11-15 T3 System/Infra 页面续验：** 隔离空库 `yuheng_t3_pages_20261115` 首次运行 54/54 changeset，21 个初始化用户密码字段非空；Demo 5187 与上游 Vite 5188 最终均代理至后端 48125。原版首次误代理共享 48080 时曾点击登录，请求超时；没有成功业务写入证据。修正 Vite 代理目标后，两端以隔离 `admin` 登录，以下页面证据均来自隔离后端。相同桌面视口比较用户管理（15 条）、租户列表（3 条）、租户套餐（2 条）和 API 错误日志空状态；用户名称筛选不存在值时两端均显示空状态，重置后两端恢复 15 条。用户管理桌面对照截图已保存至 `loginlog-session-20261115/demo-user-desktop.png`、`original-user-desktop.png`。更大范围页面进行了路由加载尝试，但异步页面尚未加载完成时的 DOM 读取不稳定，故不把该批次计为逐页对照。隔离服务、schema/grant 已精确清理，Redis DB 13 回到 0，共享 schema 保留；T3 仍开放，详情见 verification.md。

**2026-11-15 T4 站内信夹具复核：** 重新核实租户 163 管理角色没有 `system:notify-message:query`，因此先前管理端 page/get 的 403 只能证明权限拦截，不能证明跨用户隔离；该组不计通过。只读确认相关专用 schema、MySQL 用户、Redis DB 4 和端口 48132 均已清理。源码显示自服务查询/更新从登录主体固定 userId/userType，管理查询允许按请求 userId 过滤；有效权限下的跨用户读取、跨用户已读更新不变和数据库前后快照仍待隔离 HTTP 验证。验证记录见 `docs/verification/2026-11-11-full-source-migration/verification.md`。

**2026-11-16 T4 站内信隔离 HTTP 续验：** 有效 `system:notify-message:query` 权限下管理查询可以按 userId 读取另一用户消息（符合现有管理契约）；自服务分页、未读计数/列表和已读更新通过双用户 HTTP 请求及完整消息 SQL 快照验证。首轮 userType 夹具错误已纠正并排除为无效结果。专用 MySQL schema/账号已删除并复核为 0；确认 Redis DB 13 启动前为空且本轮隔离实例独占，精确清空后复核为 0。T4 余项及 T1/T3 继续开放，详见 verification.md。

**2026-11-16 T4 OAuth2 批准主体静态续审：** Controller 仅从登录态取得 userId/userType，授权批准 Mapper 按 userId、userType、clientId、scope 定位；HTTP 参数不允许调用者覆盖主体。源码检查完成，隔离 OAuth HTTP/跨主体 SQL 前后快照仍未执行，不计运行验收。T4 保持开放。

**2026-11-16 T4 社交绑定主体静态续审：** bind/unbind/list 的目标用户均来自当前登录主体，外部身份由 code/state 兑换；换绑写入有事务保护。第三方 state/code 回调、跨租户账号竞争、关联表 SQL 快照和失败回滚未做隔离 HTTP 验收，T4 继续开放。

**2026-11-16 T3 角色菜单权限续验及 Core 种子修复：** 原隔离 UI 取消和保存路径证据保留；API 对照删除的 28 个 menu ID 已追溯为 Core 005 初始化脚本中 system_menu 缺失、但角色 1/2 关系仍存在的 56 条孤儿授权，不是套餐过滤。Core 新增 010 changeset 精确软删除这 56 条，首装 56/56、重跑幂等、rollback 事务恢复 56 行后回滚，以及历史密码和合法关联核验通过；专用 schema/账号/Redis15/进程清理归零。历史保存 schema 已删除，UI 保存后重新打开仍未补验；整体 T1/T3/T4 继续开放。证据见 Demo `role-menu-20261116/result.md` 与 Core `docs/verification/role-menu-seed-orphans/verification.md`。

**2026-11-16 续验更正：** 在含 Core 010 的隔离 Demo 版本中已真实完成 role 2 勾选 WebSocket (565)→保存→关闭→重新打开→节点仍 checked；Network 代理日志确认菜单列表与 role menu GET 均 200，SQL 精确确认一条目标活动关系、0 条 Core 010 范围活动孤儿，Console warn/error 为 0。隔离 schema/账号/grant/Redis DB15/端口清理后归零，共享 yuheng_demo 未写。该结果关闭保存回读子项，但不追认旧 schema 全表差异。详情见 `docs/verification/2026-11-11-full-source-migration/role-menu-reopen-20261116/result.md`。

**2026-11-16 T1 当前 tarball 消费续验：** 最新 `yuheng-ui@0.1.0-SNAPSHOT` tarball 已在 workspace 外 Demo 消费副本通过安装、typecheck、11/11 测试、平台导入边界和 3548 模块生产构建；消费者实际解析到 tarball 解包文件而非 Core 源码。配置的内网 npm group 和公共 npm registry 均对固定版本返回 404，未发布、未改锁文件。因此包外离线消费闭环，固定坐标发布/安装仍开，T1 不关闭。Core 证据见 `docs/verification/yuheng-ui-package-identity/verification.md`。

**范围状态：** 本轮完成站内信子项隔离 HTTP/SQL、角色菜单 UI 保存回读子项、Core UI 当前 tarball 包外消费并完成专用资源清理；后续又验证了用户创建时跨租户岗位 ID 拒绝及 `assignUserRole` 失败回滚。OAuth2/社交仍只有静态主体链路审查，社交运行期验收需要有效第三方 code/state 来源，当前没有可用凭据。总目标仍未完成：T1 固定版 registry 发布/干净安装、T3 全部页面/交互/Console/Network/响应式覆盖、T4 全量 Controller/Mapper 权限与租户矩阵、OAuth2/社交运行期矩阵、49 个 ServiceImpl 写事务与回滚实测、Quartz 和文件对象存储故障注入均有未验收项。不得将已完成子项记作全量迁移通过。

**2026-11-16 T3 浏览器抽查补证：** 重新核实仍存活的隔离视觉环境，登录后首页、用户管理及基础设施代码生成页在真实浏览器可见；用户列表异步加载后为 15 条，配置/代码生成页显示结构完整。首页、用户管理、代码生成页浏览器 warn/error 均为 0。用户管理第一次即时空态是数据加载完成前的瞬时 DOM，后端日志确认分页实际返回 10 行；代码生成页显示空态，数据源配置表查询返回 0 行。源码复核表明服务会动态补入 master，不能由表空推断接口列表为空；本次未核对接口响应体或导入操作。专用 PID、容器已清理并复核端口关闭，共享 Demo PID 保留。该样本不覆盖全页面、完整 Network、原版同尺寸对照或窄屏；T3、T1、T4 继续开放，详见 `docs/verification/2026-11-11-full-source-migration/verification.md`。

**2026-11-16 T1 registry 复查：** 当前私有 npm group 和公共 npm registry 对 `yuheng-ui@0.1.0-SNAPSHOT` 均返回 404。尝试创建可控的本地 Verdaccio 重放环境时，Docker Hub 拉取超时、私有 registry 下载 Verdaccio 超时，公共 registry 对指定 Verdaccio 版本返回 notarget；未发布包或修改任何 registry/锁文件。既有离线 tarball 消费通过记录保持有效，但固定坐标 registry 安装仍无证据，T1 继续开放。详见 Core `docs/verification/yuheng-ui-package-identity/verification.md`。

**2026-11-19 当前状态复核：** 最新 Core UI 源码测试 124/124 通过，Vite 构建、`vue-tsc -p tsconfig.build.json` 声明检查和包边界检查通过。Demo UI 测试 14/14 与平台导入边界检查通过；当前工作区缺少 `@iconify/vue`、`@iconify/json`、`echarts`、`lodash-es`，所以 `vue-tsc --noEmit` 报模块缺失，Vite 生产构建在解析 `@iconify/vue` 时失败。未运行会触发 workspace 依赖变更的安装，因为固定版 `yuheng-ui@0.1.0-SNAPSHOT` registry 仍无可用证据；锁文件未改。Chrome 只读观察到原版页面 5186 首页可渲染但堆积“操作失败，系统异常”消息，连接后端的数据源/租户无法从当前进程状态证实，因此不把该页作为 T3 成对验收并停止了进一步交互。共享 5173 返回 HTTP 200，48080 根路径 404；隔离进程 48099/48100/48129 归属 Codex 其它任务，本轮未触碰。该快照不关闭 T1/T3/T4，详情见 verification.md 的“2026-11-19 本地构建与浏览器现态复核”。

## 任务与验收

**2026-11-16 T4 ERP 默认切换事务缺陷修复与续验：** 故障注入先证实账户 API 第二次写失败后旧默认被取消；给模板与 Demo 账户默认切换方法同步添加事务，契约测试先红后绿。修复后的临时 JAR 通过真实隔离 HTTP/SQL 重跑：仓库和账户在第二次 UPDATE 注入失败后完整快照均恢复，21 个历史种子密码不变。Demo Maven 40/40、模板 Python 67/67 通过，隔离进程及容器清理。与上游的事务注解差异为已验证缺陷修复，不改变接口或正常行为。详细红绿结果见 `docs/verification/2026-11-11-full-source-migration/erp-default-rollback-20261116/result.md`。该证据只关闭默认项切换原子性子项，T1/T3/T4 总项仍开放。

**2026-11-16 T4 ERP 默认状态权限续验：** 已在专用 MySQL/Redis 和端口 48192 上，通过 Core API 创建两个普通用户及最小更新权限角色，再使用真实密码登录令牌验证仓库/结算账户默认状态接口。无角色用户两个请求均 code 403，完整业务表快照不变；仅授予 `erp:warehouse:update`、`erp:account:update` 的用户两个接口开启/取消均 code 0，默认标志符合预期。历史 21 个用户密码在内存逐行比较不变；专用进程/容器/数据卷已清理，三个专用端口无监听。模板专项 12/12、Demo Maven 40/40 通过。证据见 `docs/verification/2026-11-11-full-source-migration/erp-default-permissions-20261116/result.md`；不计事务失败原子性或跨租户覆盖，T1/T3/T4 总项继续开放。

**2026-11-15 T3 会话续期缺陷续修 PHASE_GATE：** 沿用已授权完整迁移及冻结规格/计划，implementationAllowed: true。REQ/AC-T3-SESSION：Core 默认 runtime 在访问令牌过期且刷新令牌有效时，应调用原版 `POST /system/auth/refresh-token`（query 参数 refreshToken），保存续期令牌并重放原查询；刷新失败沿用请求层的清理/回调契约，不绕过认证。Only Modify：Core runtime 请求初始化、专项行为测试及本任务证据；保留注入 request 优先级、HTTP/租户契约及其它既有修改。验证以真实本地 HTTP 回归红绿灯、现有请求/runtime 测试、UI 类型检查/构建为准。浏览器旧列表和 Missing refresh token 是观察到的症状；同视口视觉及登录日志筛选闭环仍需补验，不能提前标 PASS。

**AC-T3-SESSION 续验结果：** Core 默认请求实例现配置原版刷新令牌端点，自动保存新令牌并重放请求；无效刷新令牌按既有失败契约清理登录态且不递归。基于本地真实 HTTP server 的专项测试覆盖 query 编码、POST/tenant/认证头、重放、并发单次刷新和失败清理，修复前红、修复后绿；Core UI 113 项测试、类型/边界检查、Vite 与声明构建通过，Demo UI 11 项测试、类型/边界检查和生产构建通过。隔离后端浏览器实测旧 access token 触发 `POST /system/auth/refresh-token` 后重放登录日志查询，4 条记录重新显示。详见 verification.md。本项通过不代表 T1 registry 固定版可安装，也不关闭整个迁移计划。

- [ ] T1: 审计并修复 `yuheng-ui` 完整平台入口的发布包依赖；消费端从版本化包加载完整布局和 system/infra 页面，不引用 core 源码目录。验证安装包实际内容、动态菜单解析和直接刷新。
- [x] T2: 补齐 Demo 前端与原版一致的 Vite、UnoCSS、Sass、自动导入和静态资源配置；保留业务路由并验证构建、类型检查及边界测试。
- [ ] T3: 使用真实浏览器验证登录、首页、系统管理、基础设施、菜单展开、列表及主要操作，检查控制台、网络和原版样式。
- [ ] T4: 对照后端资源、POM、启动装配、配置和 Liquibase 进行差异审计，验证核心 API、权限、租户及数据库迁移，保留历史密码。
- [x] T5: 验证前端资源进入 Demo JAR、客户端路由回退及 API/缺失资源的正确响应；更新构建启动说明。
- [x] T6: 执行相关自动测试和生产构建，记录逐项结果与未完成项，不以文件复制或局部测试代替运行验收。

**本轮 PHASE_GATE 续验记录：** workId `YH-20261111-full-source-migration`；阶段为 T3/T4 验证；规格与计划沿用上述已授权冻结产物；实施仅限只读浏览器验收和隔离资源清理，未修改运行时代码或共享业务数据。Demo 直接打开 `/login` 并登录后可验证首页渲染；两端从 `/` 初始加载时白屏，Demo 原因待进一步确认；原版 Vite API 请求超时，T3 原版成对对照 BLOCKED。T1/T3/T4 均保持开放。

2026-11-15 续验修正：Demo `main.ts` 的顶层 `await router.isReady()` 阻止挂载，已移除；隔离运行中匿名 `/` 现自动落至登录页，两端以同一隔离后端登录成功。UI 构建、类型检查、11 项测试、导入边界和 diff check 均通过。本轮覆盖的用户、岗位、角色、配置、代码生成、数据源、表单构建器与原版主要内容一致；完整页面和响应式验收仍开放。证据见同目录 verification.md。

2026-11-15 租户套餐续验：依真实菜单路径 `/system/tenant/package` 对照原版和 Demo，同一隔离库两条套餐记录、筛选/表格和新增表单一致；两端取消后仍为 2 条，Console error 为空。专用后端、两套 UI 已停止并清理专用 schema/用户和 Redis DB 7。T3 仍开放，证据见 verification.md。

### 2026-11-14 后续续验状态

- 本次浏览器只读检查确认 `http://127.0.0.1:5173/swagger-ui/index.html` 静态 Swagger UI 可以显示完整 OpenAPI 定义，默认 Server URL 指向 `http://127.0.0.1:48080`。同一后端地址在 3 秒 HTTP 检查内无响应；没有登录、执行 API、写数据库或重启现有服务。因此本次不产生 System/Infra 运行验收证据。
- 不安全地重用当前服务无法补齐全页面验收：现有 48080 Java 进程仍打开本轮将重建的目标 JAR，旧日志记录了嵌套依赖 `NoClassDefFoundError`；已有 48099/48100 两个隔离实例也继续保留。运行实例归属及目标数据源未获本轮确认，未对其发送业务请求或停止信号。
- 使用已安装本地依赖执行 Demo UI `vitest run`（2 个文件、11 项通过）、`vue-tsc --noEmit`（通过）、`vite build`（4321 个模块构建成功，有既有大 chunk 警告）；执行 Demo `mvn -o -Dexec.skip=true test`（39/39 通过）；业务模板 `python3 -m unittest discover -s tests -p 'test_*.py' -v`（66/66 通过）。这些结果验证源码构建/自动测试，不替代浏览器运行期验收。
- T1 仍缺发布坐标固定版本可用及干净安装验收；T3 仍缺其余 System/Infra/ERP 页面、取消式表单覆盖、同版本原版逐屏对照和全面响应式验收；T4 仍缺选定范围的完整平台/ERP 后端差异及权限、租户、事务矩阵。当前总迁移未完成。
- 后续只读运行续验已完成：从原 JAR 复制 SHA-256 `eccd2caf2a81ed75411e3a5c38838f0f1c621b46100a076637fb8d9ca9beb2d4` 到 `/tmp`，避免触碰 PID 23945/88324/88411 持有的文件；以专用 schema `yuheng_t3_followup_20261114`、Redis DB 15、后端 48117 启动。空库 Liquibase 54/54 changesets 成功，150 张表，Quartz 自动启动和 security mock 关闭。Demo 静态服务 5174、原版源码 Vite 5183 均明确代理至该隔离后端；两端以隔离种子管理员登录成功。
- 同尺寸浏览器成对检查：用户管理两版各 15 条且部门树、筛选、列和分页相同；字典管理两版各 385 条、筛选项/列/操作相同；岗位管理两版各 4 条、字段和操作相同；菜单管理均显示相同筛选/展开折叠/刷新缓存入口、菜单树列、顶层模块及节点权限操作；文件列表均为空且筛选/列相同；文件配置均 11 条且记录字段/操作相同；配置管理在该空种子库两边均为空，筛选和列相同。仅打开字典新增与岗位新增表单后取消；字段和按钮一致，取消后行数仍为 385/4，用户行数仍为 15。未执行 API 写入、任务操作、文件上传、导出或菜单缓存刷新。
- Demo 浏览器 Console warn/error 为 0；原版只有既有 Vue Router `next()` 弃用 warning。两端页面加载和数据请求成功；没有穷尽 Network 请求清单、所有 System/Infra/ERP 页面、编辑表单每个字段和全部响应式断点，因此 T3 总项仍开放。
- 收尾先优雅停止本轮 Java/UI/Vite，再删除本轮 schema 和专属授权，并清空启动前为 0 的 Redis DB 15（本轮运行后 22 keys）。清理后 schema/grant 均为 0、Redis DB 15 为 0；schema 中核实 54 changesets/150 tables、admin 密码哈希非空、`system_operate_log.success` 列不存在。共享 `yuheng_demo` 仍存在；PID 23945/39370/88324/88411 和端口 48080/5173/48099/48100 均保留。没有修改历史密码或共享业务数据。

变更仅限完整迁移、构建、必要的回归测试与证据。异常时保留工作区和现有服务状态，记录实际错误及未验证范围；不改写已执行数据库迁移。

### 2026-11-14 T1 包外消费续验

从当前 Core UI 工作树生成 `yuheng-ui-0.1.0-SNAPSHOT.tgz`，在 `/tmp/yuheng-ui-consumer-current.CSVU3S/consumer` 以 pnpm 本地 tarball 安装；临时消费者源码来自 Demo UI，实际安装解析路径位于该消费者的 `.pnpm/yuheng-ui@file+...`，不是 Core 源码目录。tarball SHA-256 为 `0c9cd4c27af38d51b0b0e381a3797bc42b0c3ca4fa96311ee8bcdd55715c27a3`。

独立消费验证发现 Demo 直接导入 `@iconify/json`、`@iconify/vue`、`echarts`、`lodash-es`，此前没有在自身 manifest 声明；补齐 runtime dependencies 后生产构建成功。包外类型检查进一步发现 `lodash-es` 缺少直接类型依赖，新增 `@types/lodash-es` 并增加消费契约测试。临时消费者最终 Vitest 2 个文件 11 项通过、`vue-tsc --noEmit` 通过、平台导入边界检查通过、Vite production build 处理 3548 个模块并成功。生产构建有既有单 chunk 超过 500 kB 警告。

固定版本从私有 npm registry 安装仍返回 HTTP 404；根 workspace 的 pnpm 操作也因该缺失制品无法更新 Demo manifest/lockfile。本轮没有发布 registry 包、伪造 registry 锁定或写入本地 tarball 路径。结论限于本地 tarball 的 workspace 外消费已验证，registry 固定版本的干净安装仍未验收，T1 不关闭。全量迁移继续因 T1、T3、T4 开放项而未完成。

2026-11-15 当前源码包外复验：SHA-256 `d92f0f81da2848b34b40ec27755ae37a55b04e961cc8460121c79f29980d900a` 的新 tarball 已离线安装至隔离消费者，解析路径确认位于消费者 `.pnpm` tarball 包目录。当前 Demo UI 副本 11 项测试、类型检查、导入边界、3548 模块生产构建通过。固定 registry 制品解析仍未验证，T1 保持开放；详见 verification.md 的同标题记录。

### 2026-11-14 T3 Swagger 文档页当前运行实例复核

在当前浏览器标签只读检查 `http://127.0.0.1:5173/swagger-ui/index.html`，Swagger UI 页面标题为 Swagger UI，OpenAPI 标题为“Yuheng 管理平台 0.1.0”，定义选择器列出 `all`、`erp`、`infra`、`member`、`system`，并可见用户、租户、岗位及其 API 操作。5173 由既有 PID 39370 提供，后端 48080 由既有 PID 23945 监听；本轮未重启服务、未点 Execute、未发送业务请求。

与 2026-11-13 早期运行实例的 `/swagger-ui/**`、`/doc.html` 404 记录相比，当前可见 Swagger UI 证明接口文档页面后来已恢复。该记录基于浏览器实际显示，不外推本次后端各 OpenAPI URL 的 HTTP 状态；直接诊断请求在本轮超时，未能取得响应。T3 页面只读访问和 Swagger 文档子项可记为已观察，完整 System/Infra 页面、同版本原版逐屏比较、主要交互与权限/租户矩阵仍未完成。

再次尝试执行 Demo workspace pnpm 测试时，pnpm 自动触发安装并因私有 registry 中缺少固定版 `yuheng-ui` 返回 404 中止；其间 pnpm 把五个 npm 直连依赖目录移至 `node_modules/.ignored`。本轮仅将这些目录恢复到原先空缺目标，未删除其它 `.ignored` 内容；没有改动共享数据库、历史密码或运行服务。pnpm 驱动的 workspace 测试仍无法执行。

### 2026-11-14 T3/T4 前端直跑与 ERP 模板对照续验

以当前迁移工作区为准，Demo 根 manifest 为 `yuheng-demo/yuheng-manifest.yaml`（codeVersion `0.1.0-SNAPSHOT`、governanceVersion `0.2.0`、knowledgeVersion `0.1.0`），沿用 `YH-20261111-full-source-migration` 与用户完整前后端迁移授权。复用已冻结的 UI/API/租户契约；本轮只做消费端目录只读对照和现有工作区构建验证，不改运行时源码或数据。本地 pnpm 命令会触发 workspace install 并被固定版 `yuheng-ui` registry 404 阻断，因此改用 `node_modules/.bin` 直接执行前端工具。

实际验证结果：`./node_modules/.bin/vitest run` 2 个文件、11 项通过；`./node_modules/.bin/vue-tsc --noEmit` 退出码 0；`node scripts/check-platform-imports.mjs` 通过；`./node_modules/.bin/vite build` 成功。生产构建有大于 500 kB 的 chunk 警告。此前包外 tarball 的四项独立消费验证也通过，见本计划 T1 续验。

ERP 模板与 Demo Java 逐文件包名归一对照：33/33 DO、47/47 Service、88/88 Controller 内容一致，Demo 独有 package-info.java 不属于业务逻辑差异；两份统计 Mapper XML 内容完全一致；三份 ERP Liquibase SQL SHA-256 两边逐项一致。消费端修改仅呈现明确的包名替换和既有修复。ERP UI 63/63 页面有对应模板文件，其中 7 个表单只补 TypeScript 参数类型，其余文件逐字一致；23/23 API 文件差异均为导入改用 `yuheng-ui/compat/config/axios` 消费端公开兼容入口。没有发现遗漏或未解释的功能逻辑差异。该对照只证明 ERP 模板消费源码的一致性，不替代运行期全流程验收或所有 T4 权限/租户矩阵。

运行中的 5173 与 48080 未重启。浏览器在新增登录页输入已记录的本地验收账号尝试只读登录，页面仍停留在登录页，未进入 System 用户页面；后端生命周期日志出现 `NoClassDefFoundError: ch.qos.logback.classic.spi.ThrowableProxy`，并记录租户域名查找约 60 秒，故不能将此旧运行实例作为当前 Demo 行为验收依据。没有重复提交登录、没有执行业务 API 写请求或数据库操作；未重启 PID 23945/39370。T3 登录后全局视觉与完整页面验收仍 BLOCKED，T4 完整矩阵仍开放。

### T4-WH：仓库名称参数边界修复（2026-11-14）

- 授权：用户在已报告仓库超长名称返回 500、下一步修复参数边界后明确要求“请继续”，沿用本 workId。规格/计划 FROZEN；局部参数校验无新页面原型，implementationAllowed: true。
- REQ-T4-WH：仓库新增/修改名称遵守已执行 DDL 的 `varchar(20)` 边界，非法输入返回可读的参数错误；保留空名称既有拒绝、合法字段与 HTTP/权限/租户契约。
- AC-T4-WH-1：20 字符名称通过真实 Bean Validation，21 字符名称触发 name 字段长度错误；模板与 Demo 均修复。中文 BMP 与 ASCII 均有边界用例。
- AC-T4-WH-2：隔离 MySQL/JAR 下 POST create 和 PUT update 对超长名称返回业务码 400，行数/原值不变；20 字符创建和修改成功；空值/缺失名称仍拒绝。
- AC-T4-WH-3：前端名称输入与表单规则明确 20 字符上限；模板与 Demo 同步，类型检查和适用测试通过。
- 修改范围：两份仓库保存 VO、两份 WarehouseForm、对应回归测试、验证探针及证据；不扩容或改写历史 SQL、不修改上游、Core、共享数据库和历史用户密码。
- 执行顺序：行为测试先红 → 最小校验修复 → 相同测试转绿 → Maven package → 新专用 schema/端口/Redis 实测 → 回归结束后顺序停止与精确清理。
- 回滚：仅撤销本子项代码改动可恢复旧行为；本子项无数据库结构迁移。T4 总项继续保留其它未验证范围。

### T4-REFUND：退货财务联动验证（2026-11-14）

- 沿用 `YH-20261111-full-source-migration` 与用户继续实施授权；codeVersion `0.1.0-SNAPSHOT`、governanceVersion `0.2.0`、knowledgeVersion `0.1.0`。规格/计划 FROZEN，原型 NOT_REQUIRED，implementationAllowed: true。
- REQ-T4-REFUND：在隔离实例验证上游现有退货负数财务明细的占用、超额事务回滚、审核及释放行为。
- AC-1：采购退货通过付款单类型 12、销售退货通过收款单类型 22，创建负数明细后退货退款额正确增加，超额请求主表/明细/退货均回滚。
- AC-2：有退款占用时退货反审核被拒绝；财务单审核、反审核不释放占用，反审核后删除财务单释放占用，退货可继续反审核。
- AC-3：沿用 T4-RET 的完整库存、订单、精度和密码断言，专用库/用户/端口/空 Redis，结束后精确清理；原始失败记录保留。
- Only Modify：验证探针、计划/证据及模板审计文档；Do Not Modify：共享库、历史密码、已执行 SQL、上游、registry 和无关变更。生产缺陷先做真实红灯和根因分析，再依授权实施最小修复。

### T4-MONEY：财务明细汇总精度（2026-11-14）

- 沿用 `YH-20261111-full-source-migration` 与用户继续实施授权，codeVersion `0.1.0-SNAPSHOT`、governanceVersion `0.2.0`、knowledgeVersion `0.1.0`；局部规格/计划 FROZEN、原型 NOT_REQUIRED、implementationAllowed: true。
- REQ：采购付款与销售收款的明细 SUM 必须保留 MySQL DECIMAL 精度，空汇总保持零，兼容现有业务类型、租户和逻辑删除过滤。
- AC-1：真实 Mapper 方法读取超过 double 精确范围的金额和六位小数结果时不失真；无结果和 SQL NULL 返回零；变更前先有断言红灯。
- AC-2：模板与 Demo 的两个 Mapper 一致修正，隔离真实 JAR + MySQL 验证大额付款/收款及超额回滚，且已有退款闭环不回退。
- Only Modify：相关两份模板和消费端 Mapper、回归测试、隔离探针与台账。Do Not Modify：SQL changeset、上游、共享库、密码、registry、无关变更。测试仅用专用库/账号/端口/空缓存，结束精确清理；失败保留证据。

### T4-FIN-EDIT：财务单明细编辑（2026-11-14）

- 延续 `YH-20261111-full-source-migration` 及用户授权，codeVersion `0.1.0-SNAPSHOT`、governanceVersion `0.2.0`、knowledgeVersion `0.1.0`；局部规格/计划 FROZEN，原型 NOT_REQUIRED，implementationAllowed: true。
- REQ：付款/收款明细编辑后，受影响的旧、新业务单金额应等于对应有效财务明细合计；超额更新应原子回滚。
- AC：保留明细 ID 修改金额、切换业务单（含不同业务类型）、删除/新增明细以及超额拒绝均核对数据库实际金额；兼顾租户和已有审核约束。发现缺陷先隔离环境真实请求红灯，再最小修复并回归。
- Only Modify：模板和 Demo 财务 Service、相关测试/隔离探针及台账；不得改共享库、密码、SQL 历史、上游、registry 和无关改动。使用专用库、账号、端口和空缓存，验证结束精确清理。

### T4-FIN-OWNER：财务明细归属（2026-11-14）

- 沿用 `YH-20261111-full-source-migration` 及用户继续实施授权；codeVersion `0.1.0-SNAPSHOT`、governanceVersion `0.2.0`、knowledgeVersion `0.1.0`；规格和计划 FROZEN，原型 NOT_REQUIRED，implementationAllowed: true。
- REQ：新增财务明细由数据库生成 ID；编辑仅允许使用本单据现存明细 ID，每个 ID 至多出现一次；无效输入返回业务错误并事务回滚。
- AC：付款、收款各验证跨单据明细 ID、不存在 ID、重复 ID、新增时提交 ID 均被拒绝，数据库各相关行不变；合法创建、编辑、删改和租户过滤保持。先真实请求红灯，再最小实现、隔离回归。
- Only Modify：模板/Demo 财务 Service 和错误码、探针及记录；不修改历史 SQL、共享库、用户密码、上游、registry。使用专用库/账号/端口/空缓存，结束精确清理。

### T4-PO-OWNER：采购订单明细归属（2026-11-14）

- 沿用 `YH-20261111-full-source-migration` 和用户实施授权；codeVersion `0.1.0-SNAPSHOT`、governanceVersion `0.2.0`、knowledgeVersion `0.1.0`；规格/计划 FROZEN、原型 NOT_REQUIRED、implementationAllowed: true。
- REQ：采购订单新增明细不得携带 ID，编辑时非空明细 ID 必须属于该订单且不重复；非法输入应返回业务错误并保持订单、明细和下游数据不变。
- AC：隔离真实请求覆盖外单、不存在、重复、异租户明细 ID 和新增自带 ID，保留合法新增与编辑；缺陷先红灯再最小修复，回归现有采购销售流程。
- Only Modify：采购订单模板与 Demo 的 Service、错误码、验证探针和记录；不改共享库、历史密码、上游、SQL changeset 或 registry；专用库/账号/端口/空缓存用后精确清理。其他九类风险单据单独跟踪，不以本项外推完成。

### T4-AUDIT-STATUS：ERP 审核状态参数边界（2026-11-14）

- 沿用 `YH-20261111-full-source-migration` 与用户持续迁移授权。局部规格/计划 FROZEN；原型 NOT_REQUIRED（仅后端参数校验）；implementationAllowed: true。
- REQ：12 个采购、销售、库存和财务单据状态接口只接受 `ErpAuditStatus` 枚举值 10（反审核）和 20（审核）；其它状态在调用 Service 前拒绝，不改主单状态、库存及库存流水。
- AC：模板治理契约测试覆盖全部 12 个 Controller；模板与 Demo 同步在调用 Service 前执行 Core `ValidationUtils` 对 `ErpAuditStatus` 的校验（参数注解保留作契约说明）；Maven 构建和适用测试通过。隔离 HTTP 仍需验证非法状态被拒绝且数据库全行快照不变，合法 10/20 状态转换由既有流程回归验证。
- Only Modify：12 个模板/Demo Controller、模板契约测试与本计划/验收文档。Do Not Modify：Service 状态流程、SQL changeset、共享库、历史密码、上游、registry 和无关工作区修改。HTTP 验收仅在专用 schema、DB 用户、空闲端口、专用 Redis DB 和可用的隔离种子账号下进行。

## 当前执行记录

### T4-SO-OWNER：销售订单明细归属（2026-11-14）

- `PHASE_GATE`：沿用 `YH-20261111-full-source-migration`，codeVersion `0.1.0-SNAPSHOT`、governanceVersion `0.2.0`、knowledgeVersion `0.1.0`；规格和计划 FROZEN，确认来源为用户持续授权完成迁移及既有明细归属修复范围；原型 NOT_REQUIRED（无界面变更），implementationAllowed: true。
- REQ：销售订单新增不能接受客户端指定明细 ID；编辑非空 ID 必须属于当前订单且不重复。现有接口、租户过滤、事务和正常新增/修改明细保持不变。
- AC：真实 Service 测试先复现外单 ID 未被业务拒绝，修复后覆盖外单、不存在、重复、新增自带 ID 及合法混合新增/编辑；模板与 Demo 保持一致，离线编译和适用测试通过。数据库真实事务及跨租户权限以额外隔离验证为准，不从 mock 测试推断。
- Only Modify：销售订单 Service、ERP 错误码、针对性测试及相关计划/验收/模板审计。Do Not Modify：SQL、已执行 changeset、共享库、历史密码、上游、registry 和无关修改。出现失败保留测试输出；回滚仅撤销本子项变更。消费端仅影响 ERP 销售订单非法明细输入的业务错误。

### T4-PI-OWNER：采购入库明细归属（2026-11-14）

- `PHASE_GATE`：同一 workId 与版本；规格/计划 FROZEN，依据用户持续授权、同一 ERP 明细归属审计序列和 T4-PO-OWNER/T4-SO-OWNER 已验证约束；原型 NOT_REQUIRED（无界面变更），implementationAllowed: true。
- REQ：采购入库新增拒绝客户端明细 ID；编辑时非空明细 ID 只能引用当前入库单明细且不得重复。合法条目及现有入库/订单进度处理不变。
- AC：针对 Service 的测试先产生红灯；修复后覆盖外单、不存在、重复、新增自带 ID 和合法混合更新。模板和 Demo 同步，Maven 与模板套件通过。模拟层不宣称真实 HTTP/MySQL、事务回滚或跨租户用户权限已通过。
- Only Modify：采购入库模板/Demo Service、错误码、专项测试及计划/验收/模板审计。Do Not Modify：SQL、已执行 changeset、共享库、历史密码、上游、registry 和无关工作区修改。清晰保留失败结果；无数据库回滚需要。本项不关闭其它单据风险。

### T4-SO-OUT-OWNER：销售出库明细归属（2026-11-14）

- `PHASE_GATE`：沿用 workId/版本，依据用户对全量迁移的持续授权及已确认相同输入风险；规格与计划 FROZEN，原型 NOT_REQUIRED（无页面变化），implementationAllowed: true。
- REQ/AC：新增拒绝客户端指定明细 ID；编辑非空 ID 仅允许当前出库单已有且唯一的 ID。通过 Service 测试红绿验证外单、不存在、重复、新增自带和合法混合更新；模板/Demo 同步并执行 Maven、模板测试。模拟 Mapper 结果不得外推为真实 HTTP、MySQL 或租户验收。
- Only Modify：销售出库 Service、ERP 错误码、专项测试及关联证据。Do Not Modify：SQL、共享数据库、历史密码、上游、registry 和无关修改。

### T4-SR-OWNER：销售退货明细归属（2026-11-14）

- `PHASE_GATE`：沿用 workId/版本及用户持续授权；局部规格/计划 FROZEN，原型 NOT_REQUIRED（无页面变化），implementationAllowed: true。
- REQ/AC：新增拒绝客户端指定明细 ID；编辑时非空 ID 只允许当前退货单已有且唯一的 ID。对外单、不存在、重复、新增自带和合法混合更新执行 Service 红绿测试，模板/Demo 同步，运行 Maven 与模板测试。此层证据不代表真实 HTTP、数据库或租户权限验收。
- Only Modify：销售退货 Service、ERP 错误码、专项测试和记录。Do Not Modify：SQL、共享库、历史密码、上游、registry、无关变更。

### T4-STOCK-OUT-OWNER：库存出库明细归属（2026-11-14）

- `PHASE_GATE`：沿用 workId/版本与用户持续授权；局部规格/计划 FROZEN，原型 NOT_REQUIRED（无页面变化），implementationAllowed: true。
- REQ/AC：新增拒绝客户端指定明细 ID；编辑时非空 ID 只接受本出库单已有且唯一的 ID。Service 红绿测试覆盖外单、不存在、重复、新增自带与合法混合明细；模板/Demo 同步，运行全量 Maven 和模板测试。此层不宣称真实 HTTP/DB/租户权限验证。
- Only Modify：库存出库 Service、错误码、专项测试和验收记录。Do Not Modify：SQL、共享库、历史密码、上游、registry 和无关修改。

### T4-STOCK-IN-OWNER：库存入库明细归属（2026-11-14）

- `PHASE_GATE`：沿用 workId/版本及用户持续授权；局部规格/计划 FROZEN，原型 NOT_REQUIRED（无页面变化），implementationAllowed: true。
- REQ/AC：新增拒绝客户端指定明细 ID；编辑仅接受本入库单已有且唯一的 ID。Service 红绿测试覆盖外单、不存在、重复、新增自带与合法混合更新，模板/Demo 同步并运行 Maven、模板测试。模拟层不等同于真实 HTTP/数据库/租户权限验收。
- Only Modify：其它入库 Service、错误码、专项测试和记录。Do Not Modify：SQL、共享库、历史密码、上游、registry 和无关修改。

### T4-STOCK-CHECK-OWNER 与 T4-STOCK-MOVE-OWNER：盘点/调拨明细归属（2026-11-14）

- `PHASE_GATE`：沿用 workId/版本和用户持续授权；规格/计划 FROZEN，原型 NOT_REQUIRED（无界面变更），implementationAllowed: true。
- REQ/AC：两个单据新增均拒绝客户端指定明细 ID，编辑时非空 ID 仅可属于当前主单且唯一。各有 Service 红绿测试，覆盖外单、不存在、重复、新增自带及合法混合更新；模板/Demo 同步、Maven 和模板测试通过。检查并使用未占用的错误码，不改历史重复编号。
- Only Modify：盘点/调拨 Service、错误码、专项测试和记录。Do Not Modify：SQL、共享库、历史密码、上游、registry 和无关变更；Service 模拟测试不声称真实 DB/租户验收。

### T4-RET：双明细退货与金额精度续验（2026-11-14）

- 沿用本 workId 与用户“请继续”的完整迁移授权；codeVersion `0.1.0-SNAPSHOT`、governanceVersion `0.2.0`、knowledgeVersion `0.1.0`。规格/计划 FROZEN，原型 NOT_REQUIRED（本子项新增自动验证，无页面设计变更），implementationAllowed: true。
- REQ-T4-RET：依据现有 Service/Mapper、Core MoneyUtils 和上游行为，验证采购/销售双明细退货、金额与数量精度、审核/反审核/删除及超量回滚，不改业务口径来迎合测试。
- AC-T4-RET-1：两种订单的双明细、六位小数单价、三位小数数量、税率与优惠率，经真实 HTTP 和 SQL 核对行金额两位 HALF_UP、税额、优惠和总额；JSON 响应按 Decimal 解析，避免浮点断言误差。
- AC-T4-RET-2：采购入库/销售出库后创建双明细退货，验证创建占用订单退货量但不改库存；审核、重复审核拒绝、反审核、再审核的库存与流水；已审核不能编辑/删除，反审核后删除释放订单退货量且保留库存结余。
- AC-T4-RET-3：第二条明细超量时，整个退货主表、两条明细和先更新的第一条订单明细均回滚；源单状态、库存及历史种子密码保持原值。
- Only Modify：专用退货验证探针、必要测试与本计划/验收文档/模板审计状态。Do Not Modify：共享库、历史密码、已执行 changeset、registry、无关已有工作区变更；发现生产缺陷时先保留失败证据并补回归，再做最小修复。
- 顺序：源码核对 → 探针 → 新专用 schema/账号/端口/空缓存启动 → HTTP/SQL 与回归 → 停服务 → 精确删临时库/账号/缓存 → 更新证据。回滚仅移除本子项测试及记录，无预定数据库迁移；T4 总项不因本子项通过而关闭。

- 完整平台入口已接入消费端，生产构建使用 Node 22.23.2 执行成功；包安装后发现并修复未发布源码引用、自动导入跳过包目录和语言包动态导入错误。
- 2026-11-11 core UI 测试 104 项通过，Demo UI 测试 4 项通过。浏览器确认完整登录页可以显示；重新登录及登录后页面尚未完成验收。
- 早期 Demo `vue-tsc --noEmit` 失败的配置缺口已在后续修复；2026-11-12 的隔离 Maven 构建重新执行了前端类型检查与生产构建，并成功将 323 项前端资源打入 JAR。
- 2026-11-12 重新运行：core UI 25 个测试文件、108 项测试通过；Demo UI 4 项测试通过；模块及生命周期测试 7 项通过。当前源码复制到新的临时目录，使用 Node 22.23.2、已打包的 core UI 制品及公共 npm registry，Maven 离线依赖解析并完成 package（跳过 Maven 测试），生成的 JAR 在隔离端口通过页面、静态资源、缺失资源 404 和 API 认证检查；本次 JAR 没有自定义控制器 fixture，该项单独跳过。此前带 fixture 的隔离 JAR 对全部 6 项 HTTP 检查通过。
- 当前工作区 `target/yuheng-demo.jar` 和运行中的 48080 进程早于单 JAR 安全修复，不能用它们代表最新源码构建结果；本次未覆盖运行中的 JAR 或重启用户服务。当前 5173 使用独立静态服务。
- 此前业务模块 reactor 为空；system/infra 其余操作、权限与租户边界、全量页面和构建可复现性仍待验收。任务保留未完成状态。
- 2026-11-12 继续接入会员模板：已复制 185 个 Java 源文件与 42 个会员前端文件到 Demo，并添加尚未运行验证的业务表迁移。Demo 编译配置补充 Lombok 和 MapStruct 注解处理及链式访问器约定后，`yuheng-demo-business` 编译成功；整体 package 在默认 Node 22.0.0 环境因版本不足停止。会员前端同时引用支付与商城功能，正在补齐依赖和类型配置；当前 `vue-tsc` 失败，会员功能尚不能交付。新建业务 Liquibase 变更尚未在隔离库执行，禁止将其视为已验证或用于现有数据库。原运行服务未重启。
- 后续澄清：会员代码仅为模板消费验证试验，并非已确定的正式 Demo 业务模块。试验现状已保存在 `/tmp/yuheng-member-validation.IZQzAB`，主工作区保留相关文件，但已从业务 changelog 断开未验收的会员建表脚本，避免启动时自动执行；会员代码仍在主工作区，不能视为隔离完成或可交付。原有平台迁移和其他改动保留。
- 2026-11-13 ERP 消费验证：完整工作区执行 `pnpm --filter yuheng-demo-ui typecheck`、5 项 UI 测试、平台导入边界检查和完整 Maven package 成功；前后端构建产物已生成并通过启动脚本重新启动，launchctl 两个服务均为 running。数据库已有 ERP 33 表、35 个 ERP changeset 和全部 23 个 ERP 页面菜单；登录、权限菜单及产品、库存、账户、付款、收款分页接口均返回成功，空业务表分页总数为 0。`/app-api` 被 SPA fallback 错误返回 HTML 的问题已修复，并通过打包 HTTP 回归测试。
- 当前仍未完成：T1 registry 发布和以发布坐标进行干净安装验证（实际 tarball 的 workspace 外安装消费已在 Core 验证记录通过）；T3 系统/基础设施/ERP 全页面和主要写交互验收；T4 选定平台能力及 ERP 的后端行为差异审计和代表性写入业务工作流。历史菜单快照包含尚未接入 Demo 的其它业务模块，菜单存在不等于模块迁移完成。另需核查首页“授权模块 0、可访问入口 0”与历史菜单返回之间的展示口径。详细证据见 `docs/verification/2026-11-13-erp-consumer-integration.md`。
- 2026-11-13 浏览器续验发现登录租户默认值未从上游 `.env` 迁移：租户模式开启但默认租户名称为空，输入租户 ID `1` 被后端按租户名称解析并返回“租户不存在”。新增 `consumer-entry.test.ts` 回归测试，先观察到失败，再在 Demo `.env` 补齐 `VITE_APP_DEFAULT_LOGIN_TENANT=芋道源码`；6 项 UI 测试、类型检查与生产构建通过。通过 UI 使用名称登录后进入首页，系统管理用户页显示组织树与 15 条用户数据，基础设施代码生成页面显示筛选、导入、表格和空数据状态。完整浏览器控制台、所有子页面及 ERP 写流程尚未验收。
- 2026-11-13 首页快捷入口分组修复：`buildHomeModules` 原先以标题作为分组键，遇到相同标题的顶层菜单会把它们合并；改为使用各自顶层路由路径分组，并增加系统管理、基础设施、ERP 三组的回归用例。Core UI 全量测试 25 个测试文件、110 项通过，类型检查及 `lint:boundary` 通过；Demo 生产构建通过。真实浏览器确认这三组标题分别显示，入口分别为用户管理、代码生成、产品信息等对应页面；浏览器无应用错误，仅有开发工具 Statsig SDK 初始化提示。此项只验证首页分组与入口归属，不代表 T3 的系统/基础设施全页面及主要操作验收完成。
- 2026-11-13 浏览器只读抽查：会话过期后通过现有本地测试账号重新登录；租户列表显示真实租户数据、筛选、分页和行操作，岗位管理显示 4 条真实数据及列表操作，字典管理显示历史字典数据及筛选/分页，配置管理显示 28 条配置数据及筛选/分页，代码生成显示查询筛选和空表状态，访问日志显示筛选、表格列和空数据状态。菜单展开、路由、面包屑均正常；浏览器 console warn/error 为 0。只读检视，没有执行新增、修改、删除、导出或发送操作。文件管理在本轮未成功切换，未计为通过。T3 仍未完成：其余 system/infra 子页面、响应式样式、权限/租户边界和主要写操作尚未逐项验收。
- 2026-11-13 监控页面续验与修复：在 Demo `.env` 为原版 iframe 地址配置补充空 `VITE_BASE_URL`，使同源路径正确生成；`scripts/ui_server.py` 增加对 `/druid/**` 和 `/admin/**` 的后端代理，测试覆盖两个前缀。Demo 生命周期测试 4 项通过，相关脚本总测试 19 项通过（6 项打包 HTTP 测试因未设置隔离打包实例而按条件跳过）；Demo UI 类型检查及生产构建通过。重启本地 UI 服务后，Druid iframe 使用 `/druid/index.html`，显示真实 Druid 监控页面；Redis 页面显示 Redis 运行数据。Java 监控 iframe 使用 `/admin/applications`，但此路径在当前运行后端返回 Demo SPA 首页，而不是 Spring Boot Admin 页面；Java 监控仍有后端路由冲突待查，不能判为通过。Core 含 Admin Server 自动配置类且 Demo 依赖 system/infra 聚合服务，但运行实例的该路径被 `SpaController` 接管，需检查本地 JAR/依赖装配与实际 handler 映射。浏览器另有一条 ECharts 组件告警（displayable z/z2/zlevel 无效），尚未定位来源。文件列表和文件配置页经逐级展开菜单后均显示完整筛选/表格；文件列表为空，文件配置显示历史配置。未点击测试、设主配置、同步任务、执行任务、上传、导入、导出等有副作用操作。未操作数据库。
- 2026-11-13 续做剩余菜单只读核验：重新启动当前 Demo 后使用既有本地测试账号登录。系统侧检查短信渠道、短信模板、短信日志、邮箱账号、邮件模板、邮件记录、站内信模板、站内信消息记录、通知公告、操作日志、登录日志、OAuth 应用、OAuth 令牌、第三方应用、第三方用户、地区管理；这些页面均能从菜单进入并显示对应筛选/树/表格结构，短信渠道等页面显示历史数据。基础设施侧检查 API 错误日志、WebSocket、API 接口文档和链路追踪：错误日志筛选与表格显示正常；WebSocket 面板显示 CLOSED 状态及开启连接按钮，未连接或发送；API 接口 iframe 显示 404，后端 `/doc.html` 与 `/swagger-ui/index.html` 也为 404，说明当前运行 profile 未提供接口文档 UI；链路追踪使用外部 SkyWalking 地址，当前没有本地 12800 服务，依赖外部服务部署。未做任何写操作、发送、导入导出、连接或数据库操作。
- 用户对后续范围作了明确收窄：只盘点剩余 system/infra 页面，不修改 Java 监控路径/context-path 配置，不追踪 ECharts 告警。本轮对这两个未决项不再改代码；之前分析到 Spring Boot Admin context-path 属性与实际 UI 映射不一致，但未据此修改实现。当前仍未逐一检查 system/infra 全部 44 个组件的响应式表现与权限/租户边界；非菜单入口/表单弹窗、写操作和跨租户隔离也未覆盖。T3 保持未完成。
- 2026-11-13 system/infra 页面续验：从可见菜单逐一打开角色管理、部门管理、菜单管理、租户套餐、表单构建、代码生成案例的单表/树表/标准主子表/ERP 主子表/内嵌主子表。前四个系统页面均呈现筛选/树表/分页和现存数据；表单构建显示组件分类、拖拽画布、JSON/Options/组件生成、预览及表单属性配置。五个代码生成案例均显示对应筛选与表格，ERP 主子表页另有课程/班级子表 tabs。未执行任何新增/编辑/删除/导出操作。再次打开基础设施 API 接口页，iframe 明确显示 `http://127.0.0.1:5173/doc.html` 404（File not found），与此前后端 `/doc.html`、`/swagger-ui/index.html` 404 一致。T3 仍有其它 system/infra 页面、响应式、权限/租户边界和交互覆盖未完成；按用户范围不修 Java 监控路径/context-path，也不追 ECharts 告警。
- 2026-11-13 续验数据源、日志和租户：数据源配置显示 `master` 记录，编辑/删除因权限被禁用；访问日志显示筛选/表格及空数据状态，错误日志有 7 条记录且详情抽屉可显示请求信息和堆栈。用户管理页显示部门树和 15 条记录。租户列表页面显示完整筛选、表格和 3 条租户记录；初次打开辅助功能树尚未展开时 AX 暂报空表，稍后展开租户树后数据加载并由页面截图确认。只读查看，没有更改日志处理状态，也没有执行数据源新增、导出或其它写操作。
- 2026-11-13 续验权限与任务：角色管理的菜单权限查看面板可显示全量模块树，数据权限面板显示角色和“全部数据权限”范围；两面板均用“取消”关闭，未确认或保存。定时任务页显示 33 条任务及执行日志/同步任务等入口；仅打开执行日志页，筛选与表格显示正常，当前无日志数据。配置管理显示 28 条记录和筛选/分页。没有运行任务、同步任务、编辑配置或导出。T3 仍需完成其余页面的系统性盘点、响应式表现、权限/租户隔离和主要交互验收。
- 2026-11-13 窄屏响应式抽查：以 390×844 窄屏覆盖测试首页和定时任务列表。首页卡片入口仍可换行排列；定时任务表格字段空间有限，任务名、处理器名和 CRON 列出现多行折断，窄屏下可读性较弱；折叠侧栏展开菜单时浮层遮住部分筛选和表格内容，需再与原版相同尺寸确认是否为预期交互。浏览器视口工具 reset 未清除已应用尺寸，后以桌面尺寸重设并确认窗口回到约 1910×1075；随后刷新页面令本地会话回到登录页。无数据库或数据写操作。此项记录为响应式风险，不据单次截图直接定为缺陷；T3 继续未完成。
- 2026-11-13 登录恢复及岗位复核：使用本地验收文档中记录的 `admin/admin123` 与租户名称“芋道源码”登录成功；岗位管理页显示完整筛选区、表格列、4 条记录及分页控件。部门管理页由可见菜单进入正常，当前辅助功能树节点文字未展开读取，沿用前轮已确认树数据加载的证据。未执行写操作。
- 2026-11-13 续验岗位与字典：岗位管理页面显示 4 条真实记录，字典管理页面显示名称/类型/状态/创建时间筛选、分页控件及 385 条字典记录；数据行关联到 `/dict/type/data/{type}` 路由。未打开编辑面板或执行新增、修改、删除、导出。
- 后端迁移边界复核：Core 当前包含 986 个 Java 源文件，其中系统 419、基础设施 209、框架 358；Demo 业务源码 401 个文件，按需接入 ERP 216、会员 185。Demo bootstrap 只保留启动与 SPA 控制器，平台业务由 Core 依赖提供，业务代码独立在 Demo。上游 `ruoyi-vue-pro` 有 7,019 个 Java 文件，包含未选用的众多业务模块；以全量上游文件数直接要求 Demo 一一复制不符合三仓库边界。仍需按选定的平台能力和 ERP 模板做接口、权限、租户及写工作流差异审计，不能据当前计数宣称逐文件审计完成。
- SQL 模块脚本盘点：模板仓库 16 个业务模板均有自己的 `db/changelog/changelog.yaml` 与至少一个独立 SQL changeset；此项证明脚本入口存在，不替代每个模板在隔离数据库中的迁移执行验收。
- 2026-11-13 system/infra 页面续验：从展开的可见菜单打开邮箱账号、邮件模版、邮件记录、站内信模板、站内信消息记录、操作日志和登录日志。邮箱账号显示 2 条配置记录及筛选、分页；邮件模版显示 2 条记录及筛选、分页，截图确认模板内容和行操作列可见；邮件记录页面筛选项和表格列完整，当前无数据；站内信模板页面筛选和表格结构正常，当前无数据；站内信消息记录显示 95 条记录及用户/模板/时间筛选和分页；操作日志筛选、表格列正常，当前无数据；登录日志显示 25 条记录、搜索/重置/导出入口、分页，成功及失败登录状态可见。只读验收，没有触发增删改、测试发送、导出或状态变更。此前系统管理/基础设施全页面、窄屏风险、权限与租户隔离及主要写交互仍未整体完成，T3 保持未完成。
- 2026-11-13 代表性交互与租户边界续验：在用户管理打开首条用户的编辑表单，确认昵称、部门、手机号、邮箱、性别、岗位、备注及确定/取消控件；打开新增表单，确认昵称、部门、手机号、邮箱、用户名、密码、性别、岗位、备注及确定/取消控件，均通过取消关闭。代码生成页面打开“导入表”面板，确认数据源、表名/描述筛选、可选表清单及关闭路径，未选表或导入；定时任务打开首条任务编辑表单，确认处理器、参数、CRON、重试和监控字段及取消路径；配置管理打开首条配置编辑表单，确认分类、名称、键名、键值、可见性、备注及取消路径。通过顶部租户选择器切换到“小租户”后，用户管理显示租户编号 121，组织树和用户集合按租户变化（加载后显示 2 条用户）；恢复“芋道源码”后返回默认租户编号 1 和 15 条用户。所有表单均未提交，未触发任务、导入、导出、启停或数据变更。
- 2026-11-13 基础设施配置跨租户续验：在配置管理页切换到“小租户”（租户编号 121）后仍显示 28 条参数配置，恢复“芋道源码”（租户编号 1）后仍显示 28 条。页面筛选、分页和编辑入口保持可用；本次仅观察租户上下文和列表结果，未编辑或导出。该结果暂记为配置数据在当前页面表现为公共或统一返回，是否符合 Core 的租户忽略策略需在 T4 对照后端实现确认，不直接判定为迁移缺陷。
- 2026-11-13 配置租户策略源码核对：`yuheng-module-infra` 的 `ConfigDO` 标注 `@TenantIgnore`，`ConfigMapper.selectPage` 只按名称、键名、类型和创建时间过滤，没有租户条件；因此两个租户均返回 28 条配置符合 Core 当前实现。对照用户管理，`AdminUserDO` 继承 `TenantBaseDO`，用户查询使用默认租户过滤，浏览器中默认租户 15 条、小租户 2 条的差异与源码边界一致。该项完成配置页租户策略的解释性核对，但 T4 仍未完成全平台后端差异审计。
- 2026-11-13 系统管理表单续验：角色管理打开新增表单，确认角色名称、角色标识、显示顺序、状态、备注及确定/取消控件；租户列表打开首条租户编辑表单，确认租户名、租户套餐、联系人、联系手机、账号额度、过期时间、绑定域名、租户状态及确定/取消控件。两类表单均通过取消关闭，未保存、删除、导出或改变租户配置。角色列表显示 5 条记录，租户列表显示 3 条记录。
- 2026-11-13 后端只读 API 回归：按 Demo 实际 API 前缀 `/admin-api` 登录成功并读取权限菜单（24 个顶层菜单）。用户、角色、租户、字典、岗位、公告、登录/操作日志、邮箱、邮件模板、站内信、短信、OAuth、社交登录、地区，以及配置、任务、任务日志、访问/错误日志、文件、文件配置、数据源、代码生成和 Redis 监控等 34 个只读端点均返回 HTTP 200 / `code=0`。关键分页总数与 UI 观察一致：用户 15、角色 5、租户 3、字典 385、岗位 4、配置 28、任务 33、文件配置 11、错误日志 7；空日志、文件、代码生成表状态也按预期返回 0。此前失败是请求误用 `/app-api`，非后端接口问题。本轮只登录及读取，无业务新增、修改或删除。
- 2026-11-13 源码静态对照（控制器阶段）：Core system、infra 控制器分别与上游路径对应的 149、68 个 Java 文件逐文件核对；包名替换、去除注释及空白差异后内容完全一致。Demo ERP 216 个 Java 文件与 `yuheng-business-templates/template-erp` 的对应路径和内容在同样归一后完全一致。控制器阶段结果不等于完整服务/持久层、权限租户语义及事务工作流审计。
- 2026-11-13 MySQL 只读复核：`yuheng_demo` 的 `DATABASECHANGELOG` 共 54 项，其中 Core 8、会员 11、ERP 35；Quartz `QRTZ_*`、Flowable `ACT_*`、Core 示例表和 ERP/会员表均存在。21 个历史用户密码非空，`system_operate_log.success` 列不存在。未运行 Liquibase、未写数据库。
- 2026-11-13 API 和 SQL 回归不能据此完成 T4：尚未在隔离库重放全部 changeset，本轮也未覆盖完整写工作流、所有权限注解与租户数据边界；现有数据库台账只证明已执行历史，不替代空库和重复启动迁移回归。
- 2026-11-13 包消费版本复核：Core 包版本为 `yuheng-ui@0.1.0-SNAPSHOT`，Demo 的 manifest 依赖坐标已恢复为固定版本字符串并增加版本化契约测试。工作区 pnpm lockfile 当前仍记录 `workspace:*` 链接；根目录统一 `pnpm install` 和 `pnpm install --lockfile-only` 均从配置的私有 npm registry 请求 `yuheng-ui` 并收到 404。按用户新指示不再对该 registry 进行解析/发布操作，也不更新或伪造锁文件。Demo UI 直接用现有 node_modules 执行 7 项测试、类型检查和平台导入边界检查通过；Demo 生命周期/后端模块测试 19 项通过，6 项需隔离打包服务的 HTTP 测试按条件跳过。registry 版本干净安装仍阻塞 T1；tarball 的包外消费已有此前验证记录，但不代表 registry 发布成功。
- 2026-11-13 续做只读验收：运行服务仍在 `48080`（Java PID 8263）和 `5173`（Python PID 8366）；浏览器已登录后可读用户管理页，组织树、筛选、用户表格、状态开关、分页均呈现，15 条用户记录可见；基础设施菜单展开正常，代码生成页显示筛选、导入入口、表格列和空数据状态。随后直接导航触发登录页，故本轮不声称完成 API 文档页浏览器验收。未执行任何数据写操作。
- 2026-11-13 服务端文档路由实测：对本地运行后端发起只读 GET，`/v3/api-docs` 返回 HTTP 200、`application/json`；`/swagger-ui` 重定向至 `/swagger-ui/index.html` 后返回 404；`/swagger-ui/index.html` 和 `/doc.html` 均为 404。Demo bootstrap 配置启用 Springdoc UI 和 Knife4j，当前 183 MB 可执行 JAR 也确实包含 Springdoc UI、Swagger UI 5.32.2 与 Knife4j UI 依赖，因此已排除依赖未打包。Core UI 的 Swagger iframe 指向 `/doc.html`；Demo `SpaController` 将 `/swagger-ui/**`、`/v3/api-docs/**` 保留给后端，但未保留 `/doc.html`，缺少该端点时会尝试按静态资源返回 404。当前证据还不能解释 Springdoc `/swagger-ui/index.html` 映射为何缺失，需要隔离启动实例获取 MVC handler/条件装配报告后再修复；未改动或重启运行服务，也不改变用户关于不修 Java 监控路径/context-path 的范围收窄。
- 2026-11-13 Swagger UI 根因续查：本机 Actuator 只读诊断确认 Springdoc `SwaggerConfig`、`SwaggerWelcomeWebMvc`、`SwaggerWebMvcConfigurer` 和 `SwaggerResourceResolver` 均已装配；MVC 映射含 `/swagger-ui` welcome controller、`/swagger-ui/**` 到 `META-INF/resources/webjars/swagger-ui/5.32.2/` 的资源 handler，`/webjars/**` 映射也存在；Swagger UI nested JAR 中 `index.html`、CSS 和 initializer 文件均存在；`/v3/api-docs/swagger-config` 正常返回 200 且含全部分组。资源 handler 对对应 swagger-ui 与 webjars URL 实际均返回空体 404，说明错误落在运行时静态资源解析/类加载阶段，而非 Security 拦截、Springdoc 条件未满足、API docs 被禁用或 JAR 缺资源。尚未通过隔离应用上下文做资源 resolver 单元复现，故不做猜测性代码修改；暂不重启当前进程。
- 2026-11-13 隔离端口复现与根因定位：相同 JAR 在 `48081`、`48082` 独立启动（Liquibase 与 Quartz 自动启动均禁用）重现 Swagger 静态 URL 404、`swagger-config` 200；临时实例已停止，原 `48080` 仍监听。Actuator MVC mapping 显示 `SpaController#forwardToIndex` 使用 `/{*path}` 全路径控制器映射，而 Springdoc 静态资源是低优先级 `ResourceHttpRequestHandler`；控制器映射先接管 `/swagger-ui/**` 和 `/webjars/**`，随后 `SpaController.isReserved` 直接返回 404，Springdoc 资源 handler 不会得到请求。该机制解释了资源文件、依赖、handler 和 swagger-config 均存在但静态文件仍 404。下一步按 TDD 增加端到端路由回归用例，再以不影响其它前端直刷路由的方式修复 SPA fallback 与 Swagger 静态资源的冲突；本轮尚未改生产代码。
- 2026-11-13 Swagger UI 修复和打包回归：新增 `SpaControllerTest` 4 项用例，覆盖 Swagger index classpath 资源、版本化 WebJar CSS MIME 类型、API 路径拒绝 SPA fallback、兼容 `/doc.html` 跳转；目标测试先观察到 `/doc.html` 404 红灯，修复后 4 项通过。根因分为两层：`/{*path}` 控制器映射先于静态资源 handler，因此 fallback 必须显式服务 Swagger/WebJar 资源；且 Springdoc 版本是 `SwaggerUiConfigProperties.afterPropertiesSet()` 根据打包依赖自动推导，不存在同名配置属性，直接 `@Value` 读取为空。`SpaController` 现在从 Springdoc 配置 Bean 取得真实 UI 版本、从 `META-INF/resources` 读取对应 classpath 资源，并将原版使用的 `/doc.html` 兼容跳转至 `/swagger-ui/index.html`。`mvn -DskipTests -Dexec.skip=true package` 打包成功；新 JAR 在隔离端口（Liquibase/Quartz 禁用）验证 `/swagger-ui`、`/swagger-ui/index.html`、CSS、JS、`/webjars/swagger-ui/5.32.2/swagger-ui.css`、`/doc.html` 均 HTTP 200 且 MIME 正确，`/v3/api-docs/swagger-config` 为 HTTP 200，未认证 admin API 仍由认证层返回 401。隔离进程已停止；原 `48080` 后端与 `5173` UI 进程未重启或覆盖，数据库未迁移。常规 `scripts/build.sh` 被已记录的 frozen pnpm lockfile / 版本化 yuheng-ui 坐标不一致阻断，因此本次以 `-Dexec.skip=true` 使用现有 `dist` 构建后端包，不代表重新构建前端。
- 2026-11-13 当前运行实例复核：`48080` 的 Swagger index、CSS、JS、swagger-config、`/v3/api-docs/all` 均返回 HTTP 200，initializer 指向 `/v3/api-docs/swagger-config`；`/doc.html` 返回 302 到 Swagger UI。之前关于运行实例 Swagger 404 的记录对应更早启动的 JAR，当前实例的文档静态资源已可访问。遗留隔离诊断进程 `swagger-final-check` 曾监听 `48083`、健康检查返回 404；已只停止该进程，正式 `48080` 与 UI `5173` 未受影响。
- 2026-11-13 UI 文档代理缺陷修复：真实静态服务 `5173` 起初对 `/doc.html`、`/swagger-ui/**`、`/webjars/**` 返回 404，并把 `/v3/api-docs/**` 错误回退至前端 index。新增生命周期回归测试先红（上述路径 6 项均有失败），再为 `scripts/ui_server.py` 增加四组后端代理前缀。目标测试转绿，Demo 生命周期、后端模块及会员模块共 14 项通过。仅 kickstart `com.yuheng.demo.ui` 后验证 `5173` 的 `/doc.html` 302、Swagger index/CSS/JS、swagger-config、OpenAPI all 均 200，登录路由 200；swagger-config 列出 all/erp/infra/member/system 五组，initializer 使用正确 configUrl。后端 PID 23945 未变；UI PID 更新为 39370，`logs/lifecycle/ui.pid` 已同步并通过进程身份匹配检查。未执行业务写操作或数据库操作。
- 2026-11-13 Core 全量 Java 源码路径对照：以本地上游仓库 commit `128a0e3bd3` 为只读基线，分别比较 `yudao-module-system` 与 Core `yuheng-module-system` 的 419 个 Java 文件，以及 `yudao-module-infra` 与 Core `yuheng-module-infra` 的 205 个 Java 文件；路径集合完全对应，统一 `cn.iocoder.yudao` → `com.yuheng.platform` 并移除注释/空白后，624 个文件全部相同，无缺失、额外或归一化差异。此项覆盖 Controller、Service、Mapper、DO、Convert 等 Java 源，不覆盖 POM/YAML/Mapper XML/资源文件、运行行为或 SQL 迁移；也不替代权限、租户、事务的逐项语义验收。
- 2026-11-13 业务持久层源码审计续验：逐文件对照 `yuheng-business-templates/template-erp` 与 Demo ERP 的 216 个 Java 文件、`template-member` 与 Demo Member 的 185 个 Java 文件；包名映射、注释及空白归一后，两模块均无缺失文件、无源码差异。ERP 对照包含模板工作区现有的 `ErpStockDO` 租户基类、带事务的库存更新、按 tenant/product/warehouse 初始化及 `FOR UPDATE` 锁定、精度安全的 BigDecimal 汇总实现；Demo 迁移副本与之相同。会员模块也保留了模板当前 `BaseDO`/`TenantBaseDO` 的对象继承选择、控制器权限注解及服务事务边界。模板仓库执行 `python3 -m unittest discover -s tests -p 'test_*.py' -v`：56 项通过。该结果证明 Demo 业务副本与当前模板源码一致、模板结构契约测试通过；不证明数据库迁移运行、并发业务行为运行或目标业务流程通过。Demo business 当前没有 `src/test` 后端测试。
- T4 业务层缺口续记：模板中 `ErpStockRaceProbe.java`、`ErpStockBalanceProbe.java` 是需要 JDBC 数据库环境的手工探针，未执行；隔离 MySQL 不可用/未建立，因此不能验证库存并发首建、行锁更新、金额精度、首次/重复 Liquibase 重放和既有同名表保护。模板全量治理测试主要验证 SQL/源码契约，不替代这些运行时检查；未对共享 `yuheng_demo` 写入任何测试数据。
- 2026-11-13 后端审计范围核实：Core 的 System/Infra 各含 419/205 个 Java 源文件、47 个 Admin 控制器；此前逐文件包名归一比较覆盖 System/Infra 控制器及 Demo ERP 副本，尚非 services/mappers/DO/配置的全部逐文件比对。Demo 当前 401 个业务 Java 源文件（会员及 ERP）；Liquibase 主 changelog 依次纳入 Core、Demo business，再由业务 changelog 纳入 member 与 ERP，Flowable/Quartz schema 包含于 Core changelog。权限注解、租户实体策略和事务写工作流仍没有全量静态审计/授权写操作验证，T4 不得关闭。
- 2026-11-13 T4 静态资源/POM/SQL 续审：Core System/Infra 的 `src/main/resources` 与上游目录逐路径比较，图片、代码生成模板等资源一致；仅两份 `META-INF/services` 服务实现文件因包路径迁移而不同，内容由 `cn.iocoder.yudao...` 替换为 `com.yuheng.platform...`。System/Infra POM 的依赖集合与上游一致，差异为集团及自有 artifact 坐标改为 `com.yuheng` / `yuheng-*`。Core `yuheng-server` 与上游 `yudao-server` 有意采用不同边界：Core 作为版本化聚合入口依赖 system、infra 和 protection，Demo bootstrap 持有启动类、运行配置、Liquibase 与可选业务模块装配。
- 2026-11-13 Liquibase 静态顺序/所有权审计：Demo master 先 include Core changelog，再 include Demo business changelog；Demo business 按 member、ERP include 独立模块 changelog。Core changelog 依次管理平台 schema、`yudao_demo*` 示例 schema、Quartz schema、Flowable schema、平台初始化种子、历史密码兼容修复、种子编码修复和 `system_operate_log.success` 兼容移除。示例 DDL 与种子合计 36 条 `yudao_demo*` 建表/插入语句；Flowable/Quartz 均由 Liquibase 脚本拥有，应用配置也显式关闭 Flowable schema 自动更新、Quartz JDBC 初始化设为 `NEVER`。密码恢复脚本含 21 条按 ID/用户名/租户精确匹配且附带 `password = ''` 条件的更新，非空历史密码不会被覆盖；当前共享库 21 条非空密码只读台账见本计划前文，不以本次静态审阅代替重放验证。操作日志列删除 changeset 在列存在时才执行，缺列时标记已运行，兼容旧 schema。
- 2026-11-13 T4 结论与缺口：上述结果补齐 POM、模块资源和 SQL 归属的静态审计；未执行任何数据库 changeset，也未连接共享库写入。尚需对全部非 Java 运行配置/Mapper XML 和权限、租户、事务语义完成范围化审阅，并在独立 MySQL 空库执行首次全量 Liquibase、二次重启及密码保留断言，再跑代表性授权写工作流与 ERP 库存并发探针。隔离库/运行写流程证据尚未建立，T4 继续保持未完成。
- 2026-11-14 T4 权限/租户/事务抽样审计：Core 管理用户创建接口要求 `system:user:create`，Service 事务覆盖用户记录及岗位关联写入；用户 DO 继承 `TenantBaseDO`。租户拦截器根据实体类型确定隔离策略：`TenantBaseDO` 自动按租户过滤，`@TenantIgnore` 实体忽略租户；公共配置、定时任务、租户目录/套餐等采用忽略策略。租户切换要求 `system:tenant:visit`，访问结束恢复登录用户租户；请求租户与登录用户租户不匹配时过滤器拒绝。Demo 会员用户继承 `TenantBaseDO`，ERP 主表、明细及库存对象也继承该基类；抽查 ERP 入库创建/审核事务覆盖单据、明细和库存流水，库存余额增量使用租户 ID 初始化行、`FOR UPDATE` 锁定及条件更新。抽查覆盖代表性流程，不代表全部 Controller/Mapper 语义审阅；Demo business 当前没有 Java `src/test` 测试。
- 2026-11-14 管理端写权限静态盘点：对 Demo ERP 的 71 个管理端写映射和会员的 16 个管理端写映射进行源码扫描，会员 16 个均存在 `@PreAuthorize`；ERP 有 2 个未加权限的方法，分别为 `PUT /erp/warehouse/update-default-status` 和 `PUT /erp/account/update-default-status`。它们分别缺少预期的 `erp:warehouse:update` 与 `erp:account:update` 权限检查。与上游模板文件一致，属于模板已有权限缺口而非迁移遗漏；本轮未调用这两个写接口。该结果需作为模板与 Demo 的一致修复项处理，并以无权限拒绝/有权限允许的独立测试验证。
- 2026-11-14 ERP 权限缺口修复：模板及 Demo 两份 `ErpWarehouseController`、`ErpAccountController` 的默认状态更新入口现分别要求 `erp:warehouse:update`、`erp:account:update`；前端按钮已使用相同权限标识。模板 `test_erp_tenant_contract.py` 增加权限契约断言，先在两处缺注解时按预期红灯，修复后目标测试通过；模板 Python 全量治理测试 57 项通过。Demo business 401 个 Java 文件通过 Maven 离线 compile。未调用真实写接口、未写数据库；仍缺独立运行上下文下“无权限拒绝/有权限允许”的请求级安全验证。
- 2026-11-16 续核 T4 ERP 默认状态权限与模板消费一致性：重新查看当前源码确认上述两处 `@PreAuthorize` 及前端对应权限标识都已存在；模板权限契约单测通过。重新运行模板全量 Python 测试 66/66、Demo `mvn -o -Dexec.skip=true test` 40/40、Demo UI `vue-tsc --noEmit` 和 `vite build`（3673 模块）全部通过。当前可复跑源码对照显示模板/Demo ERP 运行源码路径 305/305、会员 227/227，无路径缺失；规范化差异仅为 Demo 接入 `yuheng-ui` 请求/标签页运行时以及严格 TypeScript 类型标注，ERP 图表数据赋值改为等价可选链/类型收窄。证据 JSON：`docs/verification/2026-11-11-full-source-migration/business-template-source-parity.json`。ERP 模板与 Demo 源码一致性子项复核通过；仓库/账户默认状态接口尚无隔离运行时无权限拒绝、有权限成功的请求级安全证据，不将静态注解和单测扩大解释为运行验收。
- 2026-11-14 Dev profile 数据源治理：`application-dev.yaml` 原来仍指向 `ruoyi-vue-pro` 且硬编码 `root/123456`。新增 `test_dev_datasources_require_explicit_database_credentials`，先验证失败，再将 master/slave 改为 `YUHENG_DB_HOST`、`YUHENG_DB_PORT`、必填 `YUHENG_DB_NAME`、`YUHENG_DB_USERNAME`、`YUHENG_DB_PASSWORD`；不提供数据库名及凭据时不会误连默认业务库。Demo lifecycle/backend 脚本测试 21 项通过（6 项需 `YUHENG_TEST_URL` 的已打包服务测试按条件跳过）；Maven `package -DskipTests -Dexec.skip=true` 成功，打包 JAR 内 `application-dev.yaml` 已确认使用新配置。之前单独离线 `process-resources` 因 bootstrap 依赖业务 SNAPSHOT 未缓存而失败，随后完整 reactor package 成功；前端执行被显式跳过，未连接数据库。
- 2026-11-14 Mapper XML 对照：Core System/Infra 没有模块自有 XML Mapper（查询到 0 个）；Demo ERP 有 2 个 XML Mapper，与模板对应文件 SQL 内容一致，差异仅 namespace 包名为消费端 `com.yuheng.demo.module.erp...`。因此该项已完成静态核对。
- 2026-11-14 隔离 MySQL Liquibase 首次/重复验证：在本机 Docker MySQL `mysql8` 创建唯一测试 schema `yuheng_t4_audit_20261114`，使用完整打包 JAR、local profile 和独立端口 48084 运行。首次启动时 Redis 密码未配置，应用在初始化 Redis 阶段退出；但退出前 Liquibase 已成功执行 54/54 changeset（日志 Run 54、Previously run 0、Rows affected 6702）。迁移后只读检查确认 150 张表、Flowable 39 张、Quartz 11 张、`yudao_demo*` 5 张，ERP 商品表和会员用户表均为 0 行，平台 21 个历史种子用户密码均非空，`system_operate_log.success` 列不存在。设置 Docker Redis 实际密码 `Redis@123456` 后再次启动成功，Liquibase 报告 Run 0、Previously run 54、Database up to date；Swagger UI 与 `/v3/api-docs/all` 返回 200，未认证用户 API 的业务响应为 `code=401`。临时实例已正常停止；测试完成后删除了且仅删除该隔离 schema，并撤销测试账号在该 schema 的授权，最终只读确认测试 schema 不存在且共享 `yuheng_demo` schema 仍存在。未改共享库或历史密码。
- 当前 T3/T4 继续未完成：T3 仍缺剩余页面逐项核验、同尺寸视觉对照、租户/权限全边界和主要写工作流验证。T4 已完成 Core Java 源码、System/Infra 资源与 POM，以及 Demo 运行配置范围化对照；System/Infra 无 XML Mapper，Demo ERP 两个 Mapper XML 的 SQL 内容与模板一致，仅 namespace 为消费包名。Core/Demo SQL 所有权、首轮和重复 Liquibase 执行已验证；21 个平台种子用户密码在空库初始化后全部非空，ERP/会员表初始化为空。代表性用户/租户/ERP 权限、事务与租户边界已抽样审计，两个 ERP 默认状态接口权限遗漏已在模板和 Demo 修复并通过红绿契约测试；dev profile 硬编码数据源已改为必填环境变量并通过测试。仍缺权限/租户/事务语义穷尽审计、无权拒绝/有权允许的请求级测试、代表性 ERP 写工作流和库存并发探针。T1 仍受 registry 固定版本 404 阻塞；共享 `yuheng_demo` 未写入，历史用户密码不变。
- 当前 T3/T4 继续未完成：T3 仍缺部分页面逐项核验、同尺寸样式对照、权限/租户全边界及真实主要写流程验证。T4 已完成 Core Java 源码、System/Infra 资源与 POM，以及 Liquibase 顺序/SQL 所有权静态对照；Demo 业务 Java 副本与模板一致。仍缺运行配置/所有 Mapper XML 全量差异审计、权限租户事务语义的全量核查、上述两项权限缺口修复与隔离测试、隔离 MySQL 首次及重复全量迁移、历史密码保留断言、代表性写工作流和 ERP 库存并发探针。T1 仍受私有 npm registry 固定版本返回 404 阻塞；不再尝试发布、解析 registry 或伪造锁文件。未操作共享数据库，历史用户密码保持不变。
- 当前 T3/T4 继续未完成：T3 仍缺剩余页面的完整逐项核验、与原版相同尺寸对照、全权限/租户边界和主要写流程验证；本轮只更新 HTTP API 文档可达证据，没有执行浏览器视觉/交互验收。T4 已补齐 Core System/Infra 共 624 个 Java 文件相对上游的路径/归一内容对照，以及 Demo ERP/Member 对应模板源码对照和模板治理测试证据；仍缺 Core 非 Java 资源、POM/运行配置/Mapper XML/迁移脚本差异核验、权限租户事务语义审计，以及隔离数据库全量 Liquibase 首次/重复重放、写工作流和并发行为证据。T1 仍受私有 npm registry 固定版本返回 404 阻塞；不再尝试发布、解析 registry 或伪造 lockfile。此前已确认保留真实数据库历史密码，不在此次只读续验中清空或改写。
- 2026-11-14 T4 Core 管理端未显式权限注解写入口复核：复核此前扫描出的站内信标记已读/全部已读、OAuth2 授权提交、个人资料/密码更新、社交账号绑定/解绑、文件上传/文件登记共 9 个写映射。全局 Spring Security 只将 `@PermitAll` 和配置白名单放行，其余请求均执行 `authenticated()`；这些入口均无 `@PermitAll`，故未登录请求会被认证层拒绝。站内信分页和已读更新 Mapper 均以当前登录 `userId`、`userType` 限定行；个人资料/密码及社交绑定控制器从 Security 上下文取用户 ID，不接受请求体目标用户 ID；OAuth2 授权读写使用当前主体并校验 client、redirect URI、grant type 与 scope。文件上传和直传登记没有细粒度菜单权限，但需要登录；路径校验、MIME/扩展名校验在 Service 执行，文件元数据为 `@TenantIgnore` 全局共享数据，与 Core 文件服务模型及前端上传调用一致。对应上游源码采用同样策略，未发现迁移差异。HTTP 服务当前不可用，因此本轮对这 9 个路由没有逐路由发送请求；先前隔离 JAR 的未认证用户 API 返回业务码 401，只能证明全局认证链路，不能声称这 9 个端点已逐一做请求验证。
- 同日检查模板手工库存探针：`ErpStockRaceProbe` 的断言预期相同租户/商品/仓库可并发产生两条有效库存行，与已纳入 Liquibase 的有效库存唯一约束 changeset 相冲突，不能用于验证当前模型；`ErpStockBalanceProbe` 直接执行 SQL `count=count+1`，并未调用生产 `ErpStockServiceImpl.updateStockCountIncrement` 或验证 `FOR UPDATE` 服务路径。两者现状均不足以作为生产行为验收证据，需改为隔离 MySQL 中针对当前 Service/HTTP 流程的可重复测试后再关闭 T4。此次未启动服务、未操作数据库、未改业务源码；主后端 `127.0.0.1:48080` 当前无健康响应。T4 保持未完成。
- 同日隔离运行尝试：本地 Docker MySQL 中 `yuheng` 账号只有既有 schema 的授权，创建 `yuheng_t4_write_20261114` 被 MySQL 1044 拒绝；容器内 root 无密码连接也被 1045 拒绝。创建及授权语句未成功执行，没有留下测试 schema，也没有改动 `yuheng_demo`。因没有获准的临时 schema 写权限，本轮未启动 Demo 或运行 ERP 写/并发探针；请求级授权行为仍只保留此前全局 401 证据，T4 不关闭。
- 隔离权限与 ERP 并发工作流续验：发现容器管理员凭据可在容器内使用且不打印凭据；创建唯一 schema `yuheng_t4_write_20261114`，只向 `yuheng` 授予该 schema 权限。新 JAR 首轮执行 54/54 changeset，21 个种子用户密码非空，ERP 商品表初始为空；匿名调用个人资料更新和 ERP 仓库写入口均返回业务码 401。使用隔离库 `admin/admin123` 登录后，从权限接口确认返回 112 个 `erp:*` 权限，并可正常创建隔离测试数据。
- 真实 ERP 写工作流首次失败定位：通过 API 创建分类、单位、供应商、仓库、商品和两张待审核其它入库单；并发审核返回业务码 500。完整异常栈定位为 `DataPermissionInterceptor` 使用 JSqlParser 解析 `ErpStockMapper.insertIfAbsent` 的 MySQL `INSERT ... ON DUPLICATE KEY UPDATE` 时抛出 `UnsupportedOperationException`。`erp_stock` 继承 `TenantBaseDO`，SQL 显式接收当前 `tenantId`，数据权限插件在此场景只负责部门级行条件，不应解析/改写该 upsert。模板与 Demo 原 Mapper SQL 相同，因此属于模板与消费端共有缺陷。
- 按 TDD 在模板 `test_erp_tenant_contract.py` 添加该 Mapper 对部门数据权限 SQL 解析器豁免的契约测试，修复前测试按预期失败；模板和 Demo 的 `insertIfAbsent` 方法现标注 MyBatis-Plus `@InterceptorIgnore(dataPermission = "1")`。该标记仅跳过部门数据权限解析，租户拦截器保留，且 SQL 显式写入上下文租户 ID。模板 `tests.test_erp_tenant_contract` 6 项通过；Demo Maven 离线 reactor package 成功并重新编译 401 个业务 Java 文件，前端 build 按本次命令显式跳过且使用既有 dist。
- 修复后将新 JAR 在端口 48086 指向同一临时 schema 重启；Liquibase 报告数据库已是最新、无重复 changeset。两张已回滚到待审核状态的测试入库单并发审核均返回业务码 0；数据库确认两张单状态均为已审核、有效库存只有一行且 `tenant_id=1`、商品 ID 1/仓库 ID 2、库存 `2.000000`，库存流水 2 条合计数量 `2.000000`；库存分页 API 返回同一库存数 2。隔离进程已正常停止，仅删除测试 schema 并撤销该 schema 授权；只读确认共享 `yuheng_demo` 仍存在且未被写入。此验证覆盖真实权限认证、入库单事务和生产库存初始化/行锁/增量/流水并发路径，不覆盖所有 ERP 流程、跨租户请求矩阵或所有 Core 写接口。
- T4 当前结论：静态权限复核 9 个 Core 未显式细粒度注解的写入口，确认全局认证生效且自服务/当前用户数据边界由 Controller/Mapper 限定；Demo ERP 2 个默认状态权限缺口已在模板和 Demo 修复并通过契约测试；本轮首次发现并修复库存初始化 SQL 被数据权限拦截器误解析的运行缺陷，并完成隔离库真实并发工作流验证。仍需扩大权限/租户/事务的静态覆盖并验证代表性采购、销售、付款/收款工作流及无权/有权方法级访问矩阵；T4 继续未完成。
- 2026-11-14 T4 Demo 写入口权限矩阵续验：扫描 Demo ERP 23 个管理端 Controller 的 69 个 POST/PUT/DELETE/PATCH 映射，以及会员 11 个管理端 Controller 的 16 个写映射；全部 85 个写映射均具有显式 `@PreAuthorize(@ss.hasPermission(...))`，未发现缺权限注解入口。抽查事务边界时确认入库、出库、盘点、调拨、采购订单/入库/退货、销售订单/出库/退货、付款/收款等多表流程在 Service 写入口声明 `@Transactional(rollbackFor = Exception.class)`；仓库/账户默认状态更新也有事务。分类、单位、供应商、客户、商品、会员标签/等级/分组/签到配置等 CRUD 为单表 mapper 写入，不因每个方法都没有事务注解而判缺陷。该项是源码静态审计，不代替逐个 endpoint 的请求实测。
- 同日方法级权限请求验证：在新的隔离 schema `yuheng_t4_auth_20261114` 上执行完整 Liquibase 初始化（54/54）；管理员创建仅位于临时 schema 的用户 `t4noperm`，不分配任何角色。该账号登录成功且权限接口显示 ERP 权限数 0；调用有效请求 `POST /admin-api/erp/warehouse/create` 得到业务码 403、消息“没有该操作权限”，数据库未新增该仓库。以有权限管理员对相同写接口发送有效请求，返回业务码 0 并创建隔离仓库，形成同一接口的拒绝/允许对照。实例端口 48087 已正常停止，隔离 schema 已删除且撤销对应 schema 授权；共享 `yuheng_demo` 未触碰，历史密码未修改。
- T4 余项：当前已有一个真实库存入库审批并发工作流和一个仓库创建接口权限正反向验证；尚未实测采购订单到采购入库、销售订单到销售出库，以及付款/收款状态工作流，也未完成 Core 9 个自服务/文件/OAuth 写入口逐路由的认证请求矩阵与跨租户负向矩阵。85 个 Demo 写映射的静态权限覆盖和多表事务边界抽查不能替代以上流程验证，T4 继续未完成。
- 2026-11-14 T4 ERP 完整代表性闭环续验：在全新隔离 schema、端口 48088 和开始前为空的 Redis DB 15 上运行真实 JAR（安全 mock 关闭）。修正一次将采购进度口径误套到销售的探针假设后，在另一个全新 schema 完整跑通 53 次请求：采购入库 10、销售出库 4、库存结余 6，两条流水 +10/-4；付款 100、收款 80，六种单据最终状态 20。未审核订单拒绝、重复审核拒绝、超额收付款主表/明细回滚、已有收付款时禁止反审核、财务反审核/再审核及源单金额保留均有数据库/API 断言。探针与脱敏 JSON 见 `scripts/verification/erp_workflow_probe.py`、`docs/verification/2026-11-11-full-source-migration/verification.md`。
- 同日 Core 认证/租户矩阵：九个自服务/文件/OAuth 写入口逐路由匿名请求均为 401。临时 schema 通过平台 API 新建专用租户/套餐/账号，证实伪造 tenant-id 和无权限 visit header 被 403 拒绝；其它租户读不到源仓库，更新返回不存在，合法新增记录使用自身 tenant_id；管理员合法 visit 后下一请求恢复原租户。初始 21 个种子用户密码哈希前后完全相同，不保存口令或哈希到证据。夹具曾漏父菜单和仓库名超长；已按源码/DDL 修正后重跑，仓库名超长返回 500 的参数校验缺口单独保留，未改生产代码或数据库结构。
- 同日回归与清理：模板 58 项通过；Demo 21 项中 20 项通过、1 项因自定义 Controller fixture 缺失跳过。首次 Demo 回归误与服务停止并行造成连接拒绝，重新启动后按顺序重跑通过。验证结束已停止 48088、精确删除本轮两个临时 schema 并撤销授权、恢复 Redis DB 15 为空，确认共享 `yuheng_demo` 仍存在且本轮没有写入。T4 仍缺参数边界、其它代表性权限/事务/业务成功路径覆盖，不以当前流程通过声称全部迁移完成；T1/T3 既有余项不变。
- 2026-11-14 T4-WH 完成：真实 Validator 测试先确认 21 字符名称未被拒绝的红灯；模板/Demo 保存 VO 添加 `@Size(max=20)`，两份表单增加 maxlength 与 max 规则，无 SQL/接口/权限变更。Maven 8 项、前端 8 项、模板 60 项通过，类型检查/导入边界/前端 build/Maven package 成功。新 JAR 在 48089、专用 schema/Redis 下的 23 次请求覆盖 ASCII/BMP 20/21 字符、空串/null/缺字段及新增/修改回滚，均符合预期；Demo 脚本 22 项中 21 项通过、1 项夹具跳过。HTTP 首次因漏写 Core 消息前缀而断言失败，修正探针后全新 schema 重跑通过。IAB 实测输入 21 字母截为 20、必填提示、取消及路由刷新正常，截图和 JSON 见本 workId 验证文档。两个临时库/授权、Redis DB 15、48089 及临时浏览器标签均已清理；历史密码与共享库未修改。T4-WH 子项完成，T4 总项和 T1/T3 余项保持未完成。
- 2026-11-14 T4-RET：隔离真实 JAR 51 次请求验证采购/销售双明细退货、行金额两位 HALF_UP 与税额折扣、订单数量、审核/反审核库存流水、已审核编辑删除拒绝及第二明细超量后的完整事务回滚；最终库存 7/6、流水 20 条，隔离库种子密码不变。两次探针自身字段/表名假设失败保留证据，修正后第三个全新库通过。Demo Maven 8 项、模板 60 项通过；隔离服务的 Demo 脚本 20 项通过、2 项按条件跳过。三个临时 schema、专用账号、缓存和服务已清理；共享库未写。退款财务、负数/非法状态、并发退货、UI 和 DDL 来源仍待验证，T4 总项未关闭。详细证据见同 workId 的 verification.md T4-RET 章节。
- 2026-11-14 T4-REFUND：扩展退货探针，隔离真实 JAR 77 次请求验证采购退货付款单与销售退货收款单的负数明细、源单退款占用、超额回滚、反审核限制、财务反审核与删除释放；继承双明细/库存/密码断言。Demo Maven 8 项、模板 60 项通过，隔离实例 Demo 脚本 20 项通过、2 项跳过；专用 schema、账号、缓存和服务已清理。财务 SUM 经 double 存在精度风险，财务编辑、并发、非法符号/状态和 UI 仍待核验，T4 总项未关闭。
- 2026-11-14 T4-MONEY：付款/收款明细 SUM 经 double 导致大数精度丢失，两个 Mapper 回归测试修复前均断言失败；模板与 Demo 改为读取 BigDecimal 并保留空汇总为零后，Maven 10 项和 package 通过。独立 MySQL/JAR 26 请求验证大额 9007199254740991.12 及多付 0.01 回滚，另一个新库 77 请求复验退款闭环通过；模板 60 项、Demo 脚本 20 项通过（2 项跳过）。首次探针因服务未监听连接失败已留证；两个库、专用账号/缓存/服务已清理。前端大数表示、财务编辑并发和其它业务汇总未覆盖，T4 总项未关闭。
- 2026-11-14 T4-FIN-EDIT：真实采购付款编辑红灯确认相同明细 ID 切换源单后旧单金额仍为 20；模板和 Demo 的付款/收款 Service 更新后重算旧、新明细涉及的业务单。新库 66 请求验证采购/销售金额编辑、同类型和跨类型切换、替换及超额回滚；退货退款 77 请求回归通过。跨类型首跑因测试夹具库存不足失败留证，修正后新库通过。Maven 10 项、模板 60 项、Demo 脚本 20 项通过（2 项跳过）；五个临时库、用户和缓存清理。跨单据明细归属、租户恶意输入、并发及 UI 仍待核验。
- 2026-11-14 T4-FIN-OWNER：真实请求确认付款单编辑借用另一单据明细 ID 返回 500；模板和 Demo 增加新增 ID、当前单据归属及重复 ID 校验与明确错误码。隔离库 38 请求验证付款/收款外单、不存在、重复及新增自带 ID 均拒绝且行不变；另以 SQL 创建异租户明细夹具的 40 请求通过，财务编辑 66 请求回归通过。Maven 10 项、模板 60 项、Demo 脚本 20 项通过（2 项跳过）；4 个临时库、专用用户、缓存及服务清理。完整跨租户用户权限矩阵、并发与其他单据明细归属仍待核验。
- 2026-11-14 T3/T4 续查：重读当前清单和证据后确认，真实库存入库审批并发路径此前已在隔离 MySQL/JAR 完成，不作为未完成项重复执行；T4 后端仍有全部权限/租户/事务差异穷尽审计、显式异常注入回滚和完整跨租户身份矩阵缺口。T3 菜单只读盘点覆盖较广，但没有同视口原版与 Demo 的成对截图，也没有全系统全局样式对照。当前 UI `127.0.0.1:5173` 返回静态应用，后端 `127.0.0.1:48080` 的 `/actuator/health` 与 `/actuator/info` 均返回 404；未从浏览器确认登录态，也没有实施浏览器视觉验收。本轮没有向既有进程发送登录或业务请求，没有写共享数据库，没有改服务或页面代码。此前窄屏记录指出 390×844 下定时任务表格多行折断、折叠菜单浮层遮挡部分内容，但因缺少原版同尺寸对照仍属待确认风险。T1 私有 registry 404 继续冻结，不重试。
- 2026-11-14 T3 窄屏续验：沿用独立 schema `yuheng_t3_mobile_20261114`、端口 48098/5175/5176 与 Redis DB 12。浏览器 viewport capability 虽接受 390×844，原版实际 viewport 仍为 1910×1075，Demo 为 582×1260，无法形成同尺寸对照；未从该差异推断迁移缺陷。只读截图显示 Demo 折叠菜单覆盖内容，但因 viewport 不一致不能独立归因。隔离 JAR、Vite 与代理已停止，三端口无监听，Redis DB 12 为 0，schema 已删除且该 schema grants 为 0，共享 `yuheng_demo` 保留；用户账号仍有其它历史隔离库 grants，未执行全局撤权。详细证据见 `docs/verification/2026-11-11-full-source-migration/verification.md`。T3 窄屏成对比较仍需新建可控制 viewport 的浏览器上下文后继续，T1 registry 与 T4 后端审计仍未关闭。
- 2026-11-14 T4 销售出库事务续验：使用新隔离 schema `yuheng_t4_atomic_20261114_final`、端口 48101、Redis DB 9 和当前打包 JAR。21 次真实 API 请求建立商品一有库存、商品二无库存的双明细待出库单；审核因第二条库存不足返回业务码 `1030404000`。逐行对比 SQL 显示审核前后出库状态仍为 10、第一商品库存仍为 5、第二商品无库存行，库存流水仍只有入库 +5，确认销售出库多明细事务原子回滚。两次先行探针失败原因均为夹具漏审核销售订单/断言业务码写错，未认定为产品缺陷；均以第三个全新 schema 完成验收。服务正常停止，三个本轮 schema 及 grants 清零，Redis DB 9 为 0，48101 无监听，共享库保留。详情及 JSON 证据见 verification.md。该结果仅关闭一个销售出库负向事务场景，采购/退货/盘点/调拨/财务异常注入、全量权限租户矩阵仍未完成，T4 不关闭。
- 2026-11-14 T4 ERP 数量输入边界：模板契约测试先红，发现销售出库、采购/销售退货和其它入/出库五类 VO 缺少正数约束，其中三类还缺明细列表级联 `@Valid`。模板/Demo 同步加 `@DecimalMin(0, inclusive=false)` 与级联验证；模板 61 项、Demo 离线 Maven 后端 37 项通过，当前完整 reactor package 成功。隔离 JAR/schema `yuheng_t4_qty_20261114`、端口 48102、Redis DB 8 的真实 HTTP 负数/零数量五路请求均返回参数业务码 400；十张主/明细表有效行数不变。服务、schema/grants、缓存精确清理，共享库保留。常规 Maven test 被已有 pnpm-lock 与 package 版本不匹配阻塞，跳过前端 exec 后 37 项通过；未改 lockfile。范围与证据见 verification.md；金额/折扣等边界、完整业务矩阵仍待续审，T4 不关闭。
- 2026-11-14 T4 ERP 订单数量续验：同一数量契约进一步发现采购/销售订单明细也缺少正数约束与级联校验；模板/Demo 两个订单 VO 已同步补齐。模板 61 项、Demo 后端 37 项通过。隔离 JAR/schema `yuheng_t4_orderqty_20261114`、端口 48103、Redis DB 7 实测负数量采购订单及零数量销售订单均返回 400，采购/销售订单主表和明细表四表行数保持 0；服务/schema/grants/缓存清理完成，共享库保留。具体响应与配置见 verification.md。ERP 价格/折扣参数、其它事务及权限/租户全矩阵仍未完成，T4 不关闭。
- 2026-11-14 T4 ERP 单价/优惠率续审：六类订单、入库、退货保存 VO 之前允许负单价及优惠率越界。模板/Demo 增加可选单价非负、优惠率 0–100 校验，契约测试修复前红灯、修复后通过。模板全量 62 项、Demo Maven 离线 package 及后端 37 项测试通过。隔离 JAR/schema `yuheng_t4_moneybounds_20261114`、48104、Redis DB 6 的 11 个负单价/优惠率越界 HTTP 请求均返回 400；SQL 确认仅存在四份合法前置采购/销售单据，非法请求未增加订单/入库/退货数据或影响库存。实例/schema/grants/缓存清理，共享库保留。其它金额、税率、财务字段及 T4 全量审计仍开放，详情见 verification.md。
- 2026-11-14 T4 ERP 税率/参考价格续审：六类采购/销售文档行及客户/供应商默认税率补 0–100 Bean Validation，产品重量和产品/库存参考单价补非负校验；模板/Demo 同步，八个税率前端控件加 100 上限。保留库存盘点正负差额、退货退款负数财务明细和冲销语义。模板全量 64 项、Demo Maven 全量 39 项、UI 类型检查/Vitest 9 项/导入边界/Vite build 通过。旧 48080 HTTP 回归出现静态路由 404 与 API 超时，已知为旧故障进程，故本轮未用它声称 HTTP 验收通过；没有连接数据库或改共享数据。见 verification.md。
- 2026-11-14 T4-AUDIT-STATUS：审计 12 个审核状态接口发现只要状态不是 20 就进入反审核分支，任意值可被写入并伴随库存副作用。第一轮只增加 Controller 参数 `@InEnum`，但隔离 HTTP 证明当前 Core 调用链未触发方法参数校验，故不能据此阻断 Service。根因确认后，模板和 Demo 12 个 Controller 在 Service 调用前显式调用共享 `ErpAuditStatusValidation`，其内部以 Core `ValidationUtils.validate` 校验非空和 `ErpAuditStatus` 枚举；模板契约测试覆盖全部入口。模板 66 项治理测试、Demo 39 项 Maven 测试通过，Demo 同步契约先红后绿。重新构建的 Boot JAR 内仅含一份业务 JAR 且包含验证器类。端口 48106 的隔离 HTTP 对 12 个接口提交 status=99 均返回业务码 400，每次完整 erp_* 行快照不变；证据见 verification.md 的 erp-audit-status-runtime.json。既有 erp-workflows.json 另覆盖代表性 20 审核及付款/收款 10→20 流程，不外推到全部 12 类单据。测试 schema/账号/Redis DB 已精确清理，未触及共享库或历史密码。
- 2026-11-14 T4 税率/参考价真实 HTTP 续验：隔离新 schema/账号、端口 48105、Redis DB 12 首次执行 54 changesets；19 次 HTTP 请求含登录，18 个非法税率、重量和参考价输入全部返回业务码 400，逐请求前后全部 ERP 表计数不变。专用 schema/用户/缓存清理完成，共享库保留。可复用探针 `scripts/verification/erp_tax_price_bounds_probe.py`；详情见 verification.md 与 `erp-tax-price-bounds.json`。
- 2026-11-14 T4 Core Admin 权限/租户/事务静态续审：按 `@RequestMapping` 与 HTTP mapping 对 Core System/Infra Admin Controller 做源码扫描，覆盖 47 个 Controller、309 个映射方法，其中 163 个写映射。初始方法邻近扫描识别 151 项；随后逐项复核漏掉的注解跨越 Swagger 参数文档块，其中用户导入、API 错误日志处理状态、定时任务状态更新实际均有 `@PreAuthorize`，分别要求 `system:user:import`、`infra:api-error-log:update-status`、`infra:job:update`。其余 9 个写映射是 2 个站内信已读、OAuth2 用户授权提交、用户资料/密码更新、社交绑定/解绑、文件上传/登记；由 `YudaoWebSecurityConfigurerAdapter` 的 `.anyRequest().authenticated()` 要求登录。短信回调和 OAuth2 token 开放协议端点显式使用 `@PermitAll` 并自行校验服务商/客户端凭据。地区接口仅返回内置地区树/IP 解析结果。用户资料和社交绑定从 Security 上下文取得当前用户 ID，站内信更新把当前用户 ID 与 userType 传入 Mapper；未发现可由请求体指定其他用户目标 ID 的路径。文件上传 Service 校验文件名、路径、内容和类型，文件内容/元数据按 Core 文件模型全局共享；认证后的恶意内容、跨租户文件配置访问仍未做请求级矩阵。
- 租户源码核对：`TenantContextWebFilter` 从 `tenant-id` header 设置上下文并在 finally 清理；`TenantDatabaseInterceptor` 对继承 `TenantBaseDO` 的实体注入租户条件，对 `@TenantIgnore` 实体以及未识别的非 MyBatis 实体忽略租户。当前明确归类为租户实体或忽略实体的 System/Infra DO 共 30 个匹配项。`TenantVisitContextInterceptor` 对不同租户的 visit 要求 `system:tenant:visit`，请求完成恢复登录用户租户；缺少登录用户时不授予访问其它租户上下文。Core 的平台公共配置/字典/文件/任务等有意采用 `@TenantIgnore`，用户、部门、角色和 ERP 单据采用 `TenantBaseDO` 的规则与现有页面/API观察一致。此为源码规则盘点，不是所有 Mapper/JSQL 自定义查询逐条租户等价审计。
- 事务源码抽查：Core 当前 `AdminUserServiceImpl` 用户创建/更新/删除/批量导入、角色创建/删除、权限关联、菜单删除、代码生成多表更新、文件主配置切换、定时任务 DB/Quartz 同步等多步骤写流程标注事务；OAuth2 授权存储也使用事务。个人资料单表更新、站内信按当前主体单表标记已读没有额外事务。Demo ERP/Member Service 中既有 ERP 代表流程、退货完整回滚、财务超额回滚、并发库存审批提供了隔离 HTTP 证据。更正范围口径：之前“94 个选定 Core 服务实现”没有源码清单依据；当前 Core System/Infra 实际为 49 个 `ServiceImpl`。本轮对源码方法体定位出 413 个 public 方法、162 个含 Mapper 写调用的方法、32 个方法级事务注解；该扫描为人工逐方法审阅索引，不是通过数。49 个实现的事务矩阵及外部副作用故障注入仍未完成。详见 verification.md 的“T4 Core System/Infra 服务事务审计基线”。
- 本轮服务状态再确认：`GET http://127.0.0.1:5173/` 返回 200；`GET http://127.0.0.1:48080/admin-api/system/auth/get-permission-info` 等待 3 秒后超时（无 HTTP 响应），`/actuator/health` 和 `/actuator/info` 返回 404。本轮没有成功取得浏览器 DOM、视口、Console/Network 面板或已登录状态；此前计划“未向现有进程发送请求”只描述前一轮，本轮这个 API GET 是只读探测，没有认证凭据，也未进行任何写操作。T3 浏览器页面/全局样式验收继续 BLOCKED，不能用历史截图充当本次成对视觉证据。静态审计补充不关闭 T4；需要后续隔离服务上扩大跨租户 Mapper 和无权/有权请求矩阵、事务异常回滚验证。
- 2026-11-14 隔离前只读运行诊断：旧进程 `23945` JVM 版本为 Java 21，监听 `48080`，由旧的生命周期 marker 启动；生命周期 PID 台账记录 PID `8263`，与实际 PID 不匹配，因此未调用停止脚本或发送信号。向 localhost 发起只读 GET：`/` 为 127.0.0.1 返回 404，而 `localhost` IPv6 请求返回 500；`/v3/api-docs` 返回 200；`/admin-api/system/auth/get-permission-info` 及 `/admin-api/actuator/health` 各等待 3 秒超时；直接 `/actuator/health`、`/actuator/info` 为 404。JVM 线程栈显示 Tomcat worker 均在空任务队列等待，没有发现卡在 JDBC/Redis 调用的请求线程。生命周期日志反复记录请求处理期间 `NoClassDefFoundError: ch.qos.logback.classic.spi.ThrowableProxy`，以及更早的 Spring Boot graceful shutdown、Tomcat、Redisson、dynamic-datasource 类加载错误；日志还含带测试密码的历史登录请求，本次没有复制相关行至长期文档。当前运行实例故障根因未完全定位，不能当作最新 JAR 正常性的证据；它不妨碍在隔离实例继续验证，但重启此共享/历史进程前必须确认准确进程归属及当前数据源。T3 实际浏览器/登录验收仍 BLOCKED，本次没有认证、写请求、数据库改动或信号操作。
- 2026-11-14 T1/T4 续审：Core `yuheng-ui` 新源码按顺序完成 Vite production build、`vue-tsc -p tsconfig.build.json` 和 25 个 Vitest 文件/110 项测试；首次把 build 与 test 并行运行时，发布出口测试在声明文件生成前启动而报缺失 `dist/index.d.ts`，随后串行重跑全套测试 110/110 通过。工作树现有 tarball 的时间早于当前源码，本轮以刚打包的 `/tmp/yuheng-ui-0.1.0-SNAPSHOT.tgz` 为新制品；包名/版本为 `yuheng-ui@0.1.0-SNAPSHOT`，含 655 个文件及入口声明文件。公共 npm registry 对该固定版本返回 404；Demo 的 `node_modules/yuheng-ui` 仍是指向 Core 工作树的符号链接，因此源码构建与临时 tarball 证据不能替代发布后 Demo 固定版本安装验收，T1 仍未关闭。Core System/Infra DAL 无 XML Mapper；对 6 条注解 SQL 逐项核对：API access/error/job 日志按时间物理清理，相关日志模型为平台共享 `@TenantIgnore` 数据；OAuth2 access/refresh token 按过期时间清理，相关表具租户列且 token 选择方法保留实体租户规则，按 token 本身查找的方法才显式 `@TenantIgnore`；字典类型软删除更新的是平台共享字典实体。未发现这 6 条 SQL 对 `TenantBaseDO` 实体遗漏租户过滤。该结论仅覆盖两个 Core 模块 DAL 中这 6 条注解语句，不涵盖 wrapper 查询全部字段组合、自定义动态表名、拦截器解析兼容或运行期租户矩阵。实际 Core UI 构建和测试结果已见 `docs/verification/2026-11-11-full-source-migration/verification.md`；T4 事务异常注入、全量 Service 写入矩阵及运行配置差异审计仍未完成。
- 2026-11-14 T3 隔离配置页视觉续验与清理：通过端口 5174 的临时 UI 代理检查配置管理 `/infra/config`，页面显示 28 条记录、筛选/分页和操作入口，接口数据正常，浏览器 Console warn/error 为 0。对照原版 `yudao-ui-admin-vue3/src/views/infra/config/index.vue`，配置值列本来没有 `show-overflow-tooltip` 或固定列宽；当前窄可用列宽下，`overflow-wrap: break-word` 令长业务编号规则逐段折行，实测首行高约 224px、配置值单元格宽约 92px，导致桌面视口表格密度异常。此为已确认可用性问题，非乱码或接口故障；本轮未改页面源码，待 T3 全局样式与原版同尺寸成对比较时决定是否为消费布局约束加省略号/详情 tooltip。配置页交互未提交写操作。隔离 JAR 84311 与 UI 代理 84329 均已正常停止；端口 48095/5174 无监听；仅 DB 15 缓存清为 0；专用 schema `yuheng_t4_continue_20261114` 已不存在、该 schema 的 `yuheng` 授权为 0，共享 `yuheng_demo` 确认仍存在，历史用户密码未动。T1、T3 和 T4 仍未关闭。
- 2026-11-14 T3 原版同库视觉对照尝试：在新的 schema `yuheng_t3_visual_20261114` 启动端口 48096 隔离 JAR，并让原版源码 Vite 5175 与 Demo 静态 UI 5176 指向该实例；空库 Liquibase 54 changeset 完成，未连接共享 schema。原版 UI 浏览器登录尝试未能进入配置页：点击登录后 `/admin-api/system/auth/get-permission-info` 在浏览器侧超时，原版 `LoginForm.vue` 的 `finally` 又无条件执行 `loading.value.close()`，而此失败路径尚未创建 Loading 实例，于是抛 `Cannot read properties of undefined (reading 'close')`。原版当前 `.env.local` 确认 `VITE_APP_CAPTCHA_ENABLE=false`，因此走无验证码直接登录分支；登录故障是原版测试路径自身可复现的未处理异常，不能据此指认 Core 迁移差异。期间未对原版源码做编辑，也未写任何业务表；隔离服务按 TERM 优雅关闭，5175/5176/48096 均无监听；仅 Redis DB 14 清为 0，测试 schema 和其专用授权已移除，`yuheng_demo` 保留。因同源原版登录阻塞，T3 同尺寸登录后页面截图对照仍未完成，需先修复或隔离原版登录故障，或在已认证的原版会话上进行后续对照。
- 2026-11-14 T3 原版/Demo 窄屏与系统管理续验：通过浏览器 viewport capability 在同一上下文实测 `390×844`，配置管理和用户管理两版内容布局一致；侧栏浮层遮挡主体为原版已有表现，表格/表单略宽于可视区域，但 document/body 未产生页面级横向溢出。桌面续验另在隔离 schema `yuheng_t3_system_20261114`、后端 48109、Demo 5174、原版 5177 比较角色和菜单管理，5 个角色、菜单树、工具栏和权限操作一致。曾用普通 `el-table` selector 统计 `el-table-v2` 行数而误报 Demo 菜单树为空；截图、可见文本及两份源码的相同请求/树转换/表格绑定证明两版正常，已更正验证记录。部门管理仅完成原版/Core compat 源码核对，差异仅为导入路径迁移，尚无本轮浏览器成对证据。两次隔离环境均停止并删除专用 schema/用户、清空 Redis DB 3；本轮端口均已关闭，共享 `yuheng_demo` 保留，5173 PID 39370 未停止。T3 仍缺部门及其它页面、主要写交互，不关闭。
- 2026-11-14 T3 部门与角色交互续验：隔离 schema `yuheng_t3_dept_20261114`、后端 48110、Demo 5174、原版 5178 下，部门管理的组织树、负责人、排序、启停状态、时间及行操作对应一致；展开/折叠操作生效，两版均未出现整页横向溢出。另一隔离 schema `yuheng_t3_interaction_20261114`、后端 48111、Demo 5174、原版 5179 下，角色新增表单字段与确定/取消、超级管理员菜单权限面板的全选/折叠控件、树节点和操作对应一致；仅打开并取消，未提交写入。专用库/账号已删除，Redis DB 3 为 0，本轮端口均关闭；共享库及 5173 服务保留。部门桌面页和角色主要 UI 交互证据见 verification.md。T3 仍需其它 System/Infra 页面、其它高风险写流程及整体响应式/console/network 覆盖，不关闭。
- 2026-11-14 T3 Infra 日志续验：隔离 schema `yuheng_t3_infra_20261114`、后端 48112、Demo 5174、原版 5180 下，API 访问日志与错误日志筛选栏、操作入口、表格列及空状态一致；实际菜单导航到 `/infra/log/api-access-log` 与 `/infra/log/api-error-log` 正常。空库没有日志行，因此详情抽屉未覆盖；未执行处理状态变更或导出。曾猜测使用的旧别名 `/infra/api-error-log` `/infra/api-access-log` 返回 404，但可见菜单实际路由正常，不属于产品缺陷。隔离资源停止并清除，Redis DB 3 为 0，48112/5174/5180 关闭，共享库与 5173 保留。Console 原版有 Vue Router 弃用 warning，Demo 无额外页面异常。T3 仍缺非空日志详情、其它 Infra 页、主要写操作和全面响应式验收。
- 2026-11-14 T3 定时任务/执行日志续验：隔离 schema `yuheng_t3_job_20261114`、后端 48113、Demo 5174、原版 5181；Quartz 自动启动关闭。`/infra/job` 两版均为 33 条、10 条/页、4 页，筛选、操作入口、7 个列标题及首屏 10 条记录一致；相同既有任务记录存在同样的乱码名称。仅打开执行日志页 `/job/job-log`，两版筛选项、导出入口、8 个表格列和空状态一致。未运行/同步/启停/编辑/删除/导出任务，无业务写入。后端 graceful shutdown；隔离 schema/专用账号删除，Redis DB 3 清零，48113/5174/5181 关闭，`yuheng_demo` 保留，5173 PID 39370 持续返回 200，历史密码未改。T3 仍缺其它 System/Infra 页面、非空日志详情、主要写流程及全面全局样式/响应式验收；T1 固定版本 404、T4 全量矩阵未完成。
- 2026-11-14 T3 字典/岗位续验受隔离登录态阻塞：独立 schema `yuheng_t3_sysref_20261114`、后端 48114、Demo 5174、原版 Vite 5182，空库 54 changesets 成功。原版现有会话只读看到字典页 385 条/39 页，但新 Demo 会话登录被隔离账号凭据拒绝；没有重置或修改密码，因此该单侧观察不计为成对验收，岗位页未能检查。pnpm 启 Vite 触发 registry 404，随后使用现有 Vite 二进制启动，无依赖改动。后端 graceful shutdown，schema/账号删除、Redis DB 3 清零，48114/5174/5182 关闭，共享 `yuheng_demo` 保留且 5173 PID 39370 未停止。后续需在受控会话登录后继续。T1、T3、T4 均未关闭。
- 2026-11-14 T4 Core System/Infra 事务与外部副作用静态续审：复核当时工作树 System/Infra 51 个 ServiceImpl 中声明事务的实现并抽查多步写入。随后当前工作区路径复核确认 Core 现有 System/Infra 共 49 个 ServiceImpl；过去出现的“94 个选定 Core 服务”无源码清单依据，已从本轮验收基准中撤销。当前方法扫描索引为 413 个 public 方法、162 个 Mapper 写调用方法、32 个方法级事务注解，未把扫描数当通过数。租户创建/修改、权限关联、用户关联、菜单删除、代码生成、文件主配置和 Quartz 同步等代表多步流程有事务声明。文件上传/删除与对象存储、DB 客户端内容 Mapper 的实际先后顺序已复核，确认数据库事务不能覆盖全部存储副作用；Quartz 调度器与业务 DB 事务也没有原子性证据。用户资料事件全仓无消费者的既有结论保留。本轮没有修改 Core/Demo 运行代码；49 个实现的逐方法事务/租户矩阵、文件/Quartz 故障注入仍未完成，详见 verification.md 的“T4 Core System/Infra 服务事务审计基线”。
- 2026-11-14 T4 运行配置和构建生命周期续审：逐项比对上游 `yudao-server` 与 Demo bootstrap 的 `application.yaml`、`application-local.yaml`、`application-dev.yaml`、`logback-spring.xml`、Liquibase changelog 和 bootstrap POM。Demo 使用独立应用名、固定 `local` 默认 profile 与 `yuheng_demo` local 默认 schema；dev profile 要求显式 `YUHENG_DB_NAME/USERNAME/PASSWORD`，与已批准的数据库隔离边界一致。`flowable.database-schema-update=false`、`spring.quartz.jdbc.initialize-schema=NEVER`，架构由 Core Liquibase 拥有；Demo bootstrap 组合版本化 Core server、Demo business 和 UI 静态资源。profile 差异未发现新配置漏迁，但仍不代表外部集成配置与所有业务 profile 全量运行验收。
- 同轮对旧运行故障做只读根因确认：PID 23945 的 `lsof` 显示 Java 进程打开 `target/yuheng-demo.jar.original`，而不是当前重建后的 `target/yuheng-demo.jar`。Spring Boot Maven repackage 产物包含 `BOOT-INF/classpath.idx`，当前正式包含 Logback、Spring Boot、Tomcat、Reactor、Redisson 与 dynamic-datasource 嵌套依赖；旧 `.jar.original` 是未重打包的薄 Maven JAR。既有日志中的多个依赖类 `NoClassDefFoundError` 与运行中重打包后 JarLauncher 仍引用已替换/删除的文件一致。`scripts/build.sh` 原来无进程占用检查，允许对正在运行的唯一目标路径执行 repackage，构成可复现的生命周期缺陷；本轮未停止 PID 23945 或覆盖运行包。
- 修复限定为 `scripts/build.sh`：若正式 JAR 或 `.jar.original` 存在，先要求 `lsof` 可用，再确认两个文件均未被进程打开；占用时拒绝执行 Maven 并提示先运行 `scripts/stop.sh`。TDD 回归测试覆盖占用拒绝和未占用继续构建。专项测试、脚本语法和 diff 检查结果追加在 verification.md。保护避免未来构建再次损坏运行实例；当前已损坏旧实例需要在另行确认进程/数据源后停止并从新构建产物启动，不能以本次脚本测试替代真实浏览器/API 重验。
- 2026-11-14 T3 隔离运行启动续验：检查 Docker `mysql8` 与 Redis 健康，确认共享 `yuheng_demo` 有 54 changesets/150 张表、1 个非空管理员种子；用户提供的 `yuheng` 账号只有现有 schema 授权，容器 root 管理账号可用。创建空隔离 schema `yuheng_t3_runtime_20261114_a` 并只给 `yuheng` 授权，Redis DB 13 起始为空；准备在 48115 启动当前 JAR时发现此前未列出的验证进程 88324/88411 已占用 48099/48100，且本轮 JAR 实际未产生启动进程/日志，schema 中未创建 DATABASECHANGELOG/业务表。没有停止其他进程或改共享库。确认临时 schema、授权已删除，Redis DB 13 仍为 0；故本轮没有运行时登录/API 结果，需先判明 48099/48100 实例是否属于仍在进行的验证任务，再另选空闲端口续验。`yuheng_demo` 和原进程 23945/39370 均保留。
- 2026-11-14 T3 隔离运行成功续验：确认 88324/88411 是 Codex app-server 子进程，健康与 OpenAPI 返回 200，连接 `yuheng_t4_atomic_20261114`/`_retry`、Redis DB 11/10；不属于本轮 T3，未停止或更改。随后以新 schema `yuheng_t3_runtime_20261114_b`、Redis DB 9 和端口 48116 启动当前 JAR；空库首次运行 54/54 Liquibase changeset，管理员登录及权限接口均业务码 0、菜单 24 组。真实浏览器打开隔离实例后，首页显示 21 个授权模块/506 个入口，System 用户 15 条、岗位 4 条，Infra 配置 28 条，ERP 产品页正常显示筛选/表头/空数据；浏览器 DevTools logs 没有应用错误。未提交任何写操作。二次启动核对仍为 54 changesets/150 tables，admin 密码非空，`system_operate_log.success` 列不存在，ERP 商品和会员用户为空。实例收到 TERM 并 graceful shutdown；精确删除新 schema 和授权、清空本次 Redis DB 9，确认临时对象均为 0、共享 `yuheng_demo` 存在、端口 48116 关闭。原 23945/39370 与 88324/88411 均保持运行。该轮关闭 T3 登录、首页、用户/岗位/配置和 ERP 产品页的隔离运行验收子项；全页面/全交互、同一视口原版对照和响应式矩阵仍待完成，T3 不关闭。

### T3-SEED-PLAN：平台种子计划名称乱码（2026-11-15）

- PHASE_GATE：沿用 workId `YH-20261111-full-source-migration`、用户完整迁移/SQL 治理及持续继续授权；codeVersion `0.1.0-SNAPSHOT`、governanceVersion `0.2.0`、knowledgeVersion `0.1.0`。局部规格/计划 FROZEN，原型 NOT_REQUIRED（数据展示修复），implementationAllowed: true。当前 Core HEAD afbd19e、Demo HEAD b9c4906，均保留已有未提交改动。
- REQ：按原始 `ruoyi-vue-pro/sql/mysql/ruoyi-vue-pro.sql` 同表同 ID 的正确文本，修复 43 个仍含混合编码“计划”的平台配置/任务/字典/菜单字段；007 已修值不重复覆盖。历史通知消息不属于本次配置修复，保留原值。
- AC-1：真实隔离 MySQL 在修复前显示错误值并触发断言红灯；新增 009 迁移后 43 个字段均与来源一致。
- AC-2：UPDATE 以 ID、稳定身份与旧文本 BINARY 精确匹配，自定义值不受影响；显式保留 update_time，用户行及密码摘要保持不变；重复运行无数据变动。
- AC-3：真实 Liquibase 首次只增加一个 changeset、再次无待执行项；001–008 文件与已有 DATABASECHANGELOG checksums 保持。新增迁移使用内联 SQL + 注册 include，并提供守卫式反向 rollback；生产回滚须先备份并评审匹配范围，不能逆转用户自定义值。
- Only Modify：Core 新增迁移、changelog 尾部 include、专项测试/无敏感值 fixture、本计划和证据。Do Not Modify：已执行 SQL/changeset、共享数据库、历史密码、通知历史消息、registry、上游源码及无关改动。
- 验证顺序：真实 MySQL 红灯 → 最小新增迁移 → 实际 Liquibase update/重跑 → 事务内自定义值保护/幂等/rollback 验证 → 测试和 diff 检查 → 本轮资源精确清理。隔离库为本轮既有 `yuheng_t3_remaining_20261115`，不新建共享环境连接。

### T-GOV-MIGRATION-DISCOVERY（2026-11-15）

沿用用户“业务模块迁移形成 skill、后续直接复用”的授权，补齐已有 `yuheng-business-template-migration` 在 `.agents/.claude/.qoder` 的三个发现链接。Only Modify 为缺失链接，技能内容和消费端快照不变。先以 `sync_agent_assets.py --check` 确认仅三项缺失且无文件冲突，再按既有安装器补齐，最后 check 和 bundle 验证；不得将此视为 registry 发布或消费端规则升级完成。

### 2026-11-15 本轮验收收口

- T3 剩余系统页：通知公告（含不存在标题搜索/重置、新建表单取消）、短信三页、邮件三页、站内信两页、OAuth 两页、三方两页及地区树完成同隔离数据桌面核验；12 组结构化记录的字段/表头/总数/显示行数一致。短信前两页按钮采集含隐藏节点，未当作可见差异；原版累计 Console 含历史错误，未标无错误。窄屏菜单状态未统一，响应式不通过判定，仍待复测。
- T3-SEED-PLAN：009 新增迁移精确修复 43 个平台展示字段，真实红绿测试、Liquibase 首次执行/重跑、用户自定义保护及反向恢复测试完成；旧 8 文件和 54 checksum 保持，最终全治理 54/54 通过。Core 离线 package 成功且 JAR 注册完整。未安装或发布至共享消费者，需后续版本升级应用。
- T-GOV-MIGRATION-DISCOVERY：仅补齐三处缺失链接，安装前无冲突，安装后 check 及 bundle PASS。
- 隔离三服务已停止，专用 schema/grant 归零；DB14 无紧邻启动基线，按停止后无连接及 32 个精确归属键删除清理，最终 0。共享账号、schema、历史密码及其它实例未改。详见同 workId verification 与 `system-remaining-20261115/cleanup.json`。
- 下一顺序：在一致菜单状态下复测公告页窄屏 → 根据已有覆盖表补齐 System/Infra/ERP 主要交互 → 推进 T4 剩余权限/租户/事务边界。T1 registry 发布/解析不自动重试；所有总项继续按实际缺口保留开放。

### 2026-11-20 T3 岗位页断点菜单交互补验

沿用既定 390×844 窄屏与 1440×900 桌面验收。以实际 Core compat 菜单为对象，确认窄屏初始收起、汉堡打开抽屉、遮罩关闭；桌面岗位筛选/重置按 4→0→4 行验证。使用隔离 schema、Redis 和 UI/后端端口；记录 Console、失败资源和代理日志，精确清理专用资源。只关闭岗位页面上述交互子项，不外推到其它菜单、表格、弹窗或全部 T3。

结果：桌面岗位分页 4 行，搜索无匹配为 0 行，重置回 4 行；岗位 API 均 200。窄屏初始菜单宽 0，点汉堡为 200px 抽屉并显示遮罩，点遮罩后遮罩移除且数据仍为 4 行。移动端 Console errors 和两端 requestfailed 为空；桌面有 `/favicon.ico` 404，跳转时代理日志出现被客户端取消旁路 API 的 502/BrokenPipe，作为完整 Network/Console 验收限制保留。隔离容器和 13351/16431/48186/5199 端口已清理。证据见 `docs/verification/2026-11-11-full-source-migration/verification.md` 与 `post-browser-20261116/`。T1/T3/T4 总项仍开放。

配置页桌面续验（2026-11-17）：独立 MySQL/Redis 与后端/UI 48187/5299；分页 10→搜索 0→重置 10 行，编辑表单改值后取消，配置写请求为 0、`infra_config` 全表快照前后哈希一致。缺失 favicon 与跳转取消请求日志作为网络检查限制保留；长参数值折行导致高行是上游同样存在的可读性问题。隔离资源已清理；新增/保存/删除、移动端与 T1/T3/T4 总项继续开放。详情见 verification.md 的对应小节。

配置页桌面写入续验（2026-11-17）：隔离环境中通过真实 UI 新增、编辑、删除唯一自定义参数，三个写接口 HTTP 200/业务码 0，数据库确认更新值和逻辑删除，其余配置全行快照未变；另一行编辑取消无额外写请求。两次测试等待条件失败及最终结果均保留；favicon 404、批量删除/导出、移动端、权限失败路径和原版运行态对照仍开放。容器及端口已清理，详见 verification.md。

代理断连缺陷修复（2026-11-17）：沿用 `YH-20261111-full-source-migration` 及既有冻结规格、完整迁移实施授权，codeVersion `0.1.0-SNAPSHOT`、governanceVersion `0.2.0`、knowledgeVersion `0.1.0`；局部修复不需要新原型。REQ：客户端在代理转发期间断开，不误报后端不可用或再写响应；真正上游不可用仍返回 502。AC：真实 socket 断连红绿测试、上游不可用回归及生命周期测试；限定修改 Demo 代理、相关测试与记录，不改共享运行实例、上游服务或数据库。回退仅移除本次代理处理和测试。

配置页桌面扩展验收（2026-11-17）：隔离环境中复验新增/编辑/单条删除，批量删除两条唯一参数及导出 xls 下载，确认取消不写、删除后重置回到基线、其他配置行快照不变。发现迁移漏复制原版 favicon 并补齐。代理客户端 RST 根因为 BrokenPipe 被误作上游故障，以真实 socket 回归修复；上游不可用仍为 502。最终浏览器 console/requestfailed 为空、favicon 200、容器及端口已清理。失败尝试与最终证据路径见 verification.md。T1/T3/T4 其余范围不变。

T4 基础设施配置权限续验（2026-11-20）：隔离真实登录用户无角色时 create/update/delete/delete-list/export 均 403，逐次完整 `infra_config` SQL 快照不变；精确授予五项配置权限后 query/create/update/single+batch delete/export 成功。ConfigDO 为平台级 TenantIgnore，本证据仅属权限矩阵。独立 MySQL/Redis/schema 与端口均清理，最终可复核 JSON 在 `docs/verification/2026-11-11-full-source-migration/controller-security-inventory-20261119/config-permission-runtime.json`；此前证据生成字段错误的运行保留并排除。此局部证据不关闭 T4 全 Controller/租户/事务矩阵或 T1/T3。

续验记录（2026-11-15）：核对后端PID23945仍监听48080，但登录接口无响应，`/actuator/health` 返回404；未重启或停止既有服务。原版Vite曾由本轮直接执行在5186以避免pnpm workspace安装；通过后发现既有服务API超时，未进入同状态窄屏对照，随后停止5186。pnpm先前一次意外触发workspace install并将Demo六个依赖目录移至 `.ignored`，已按命令输出逐项恢复，检查确认均在原路径。5186无监听，原版和Demo代码未因该轮改动。窄屏子项仍开放；后端运行阻塞不影响继续做包/registry的静态证据审计。

同日开发态依赖转换续修：Demo Vite 之前把 Core `yuheng-ui` 兼容层作为依赖预打包，导致 `formRules.ts` 的裸 `useI18n()` 未经过消费端 AutoImport。先新增配置回归并观察到 RED，再在 `vite.config.ts` 排除 `yuheng-ui` 的依赖预打包。启动全新优化缓存后，实际开发模块响应已变为显式 `import { useI18n }`，不再有 `ReferenceError: useI18n is not defined`。Demo UI 全量 12 项测试、类型检查、生产构建通过。浏览器实际登录路由仍白屏，因为路由初始化调用共享后端 `fetchUserInfo` 超时；这与本次依赖预打包缺陷区分，未停止/重启共享后端。开发 Console 还观察到重复插件/组件注册告警，待评估 Core 包开发源码与消费端全局插件注册的重复边界。生产 bundle 仍成功生成；5187 已停止。此修复仅作用于开发模式依赖转换，不改变发布包或生产行为；实际登录页验收仍被后端响应阻塞。

### T3-MOBILE-FOLLOWUP（2026-11-15）

PHASE_GATE：沿用 workId、冻结规格/计划与用户继续完成迁移授权；codeVersion 0.1.0-SNAPSHOT、governanceVersion 0.2.0、knowledgeVersion 0.1.0。以原版布局为已认可视觉基线，非新设计。AC：同一隔离数据与390×844视口，通过UI统一菜单折叠状态后比较公告列表/表单，再推进有依据的其它页面响应式与主要交互；验证请求/页面结果。Only Modify：验收证据与计划，发现可复现缺陷时先补真实红灯再最小修复；Do Not Modify：共享实例、历史密码、已执行迁移及registry。不重复安装依赖。专用schema/user/Redis15，结束精确清理。

### T4-SYSTEM-NOTICE-POST-PERM（2026-11-15）

沿用workId/版本及用户完整迁移验证授权，规格/计划FROZEN，implementationAllowed:true（仅隔离验证，无生产代码修改）。REQ/AC：使用受支持API创建无角色临时用户，确认权限集合为空，再验证公告/岗位 GET page/get、POST create、PUT update、DELETE delete 均返回403且表快照不变；管理员携异租户header返回403；合法管理员CRUD及原有历史记录保持。只在本轮schema `yuheng_t3_mobile_20261115`、48127/5191验证，凭据不落证据，夹具用后通过API删除。此子项只覆盖所列端点/条件，不关闭完整T4行级租户及事务矩阵。

结果：公告列表同状态390×844对照通过；表单内部溢出/悬浮菜单干扰仍未通过。公告UI新增/编辑/取消和岗位UI新增/编辑、原版回读通过，删除只经HTTP。所列10项无角色403、2项异租户header403、2项匿名401及不变快照通过。21名历史密码逐行核对保持，隔离资源已清理。Demo空表单Object错误待定位；详情见verification.md与mobile-followup-20261115/acceptance-summary.json。

### T3-SYSTEM-FORM-VALIDATION（2026-11-15）

PHASE_GATE：沿用本workId及版本、已确认的完整迁移规格/实施授权，规格与计划FROZEN，implementationAllowed:true。原型NOT_REQUIRED（保留原版表单和成功提交契约）。REQ/AC：先以实际Element Plus表单挂载复现公告/岗位空提交的拒绝对象，验证必填提示保留、无API写入、无未处理异常；再最小处理预期校验失败，补合法新增/编辑成功与API失败不被误吞的回归。Only Modify：两处Core表单、专项行为测试、本计划及证据；不改共享实例、历史密码、SQL、上游、依赖版本、registry或消费者安装产物。验证：真实表单红绿测试、Core全量UI测试/类型/边界/构建；实际浏览器缺证时保持该层未验收。回退仅移除本子项局部改动。

浏览器补验使用仅监听127.0.0.1的专用组件预览：实际Core表单、Dialog、Editor和Element Plus，独立Pinia/runtime与模拟请求适配器，不启动后端/数据库、不引用消费者安装源码或修改其依赖。校验DOM/控制台与模拟请求计数，只作为组件浏览器证据，不等同完整Demo登录联调。临时预览用后关闭，配置及源码保留于本轮证据以便复核。

结果：两处表单以 `formRef.value` 守卫及 `validate(() => {})` 处理预期校验失败，保留合法提交和API异常传播。真实Element Plus专项红灯2失败/6通过，修复后8/8；最终Core全量27文件121项、类型、边界、生产构建、声明构建均退出0。保留预期required提示及既有动态导入warning。浏览器实际Dialog/Editor验证公告/岗位空提交均无额外请求或异常、合法新增各成功一次；注入请求Error仍传播且无成功事件，所有请求为内存模拟。390×844无菜单浮层时公告dialog仍scrollWidth800，响应式子项未通过。5193进程和专用标签关闭，视口恢复；无数据库资源、依赖安装、registry或消费端替换。详情见verification.md及form-validation-20261115/。T1固定版消费、T3其余页面/主要交互/移动布局/完整Network、T4全量矩阵仍未关闭。


### T3-DIALOG-MOBILE-WIDTH（2026-11-15）

PHASE_GATE：沿用workId YH-20261111-full-source-migration、codeVersion 0.1.0-SNAPSHOT、governanceVersion 0.2.0、knowledgeVersion 0.1.0，以及用户完整迁移/全局样式修复和持续继续授权。局部规格/计划FROZEN，implementationAllowed:true；原型NOT_REQUIRED（局部溢出修复，保留既有表单布局）。

REQ：公告及共用Dialog在窄屏不得因固定800px宽度令字段和确定/取消按钮超出可视区域；桌面指定宽度、百分比和全屏功能保持。根因：旧证据role=dialog命中了.el-overlay-dialog遮罩；本轮实际.el-dialog在390视口仍800px，Core/原版组件仅导入差异，均无max-width约束。

AC-1/T-1：真实浏览器先保存390×844的.el-dialog、遮罩、编辑器、页脚边界与断言红灯；不得用外层宽度代替实际弹窗。AC-2/T-2：在Core共享Dialog增加最小最大宽度约束，实际公告在320/390/768视口内部不横向溢出、确认取消可达，桌面1512宽仍800；有必要的同源表单/百分比宽/默认全屏/切换全屏补验。AC-3/T-3：实际Core组件浏览器验证必填、合法模拟提交、取消；请求为内存模拟，明确不代表Demo后台联调。AC-4/T-4：Core全量UI/类型/边界/构建、差异审查、证据与清理。

Only Modify：Core compat/components/Dialog/src/Dialog.vue局部样式；本计划、同workId verification及新mobile-dialog-20261115证据/预览。不修改已有证据预览以伪装红灯；不改字段/接口/SQL/权限/租户/上游源码/依赖/消费端安装/registry。优先单项CSS约束，不新增布局系统或视口监听。纯样式使用实际浏览器可重复红绿测量和截图，必要时才增加逻辑单测。回退仅本次CSS声明；保存历史校验修复。完成后停止专用预览、关闭标签和恢复视口。

结果：实际.el-dialog红灯为390视口仍800宽且页脚right784；Core仅增加.com-dialog max-width:100%。320/390/768下真实面板/scrollWidth分别320/390/768，1512桌面仍800；两个底部按钮均不横向超出。实际滚动后可点击必填校验、390公告模拟新增成功、390岗位及320公告取消；百分比60%、全屏切换/恢复及默认全屏均正常。Core全量121项、类型/边界/构建/声明均退出0。长表单保持纵向滚动，不声称全部编辑器工具栏/上传或完整Demo手机验收通过。5193/5194、专用标签已关闭，视口恢复，无数据库或消费端变更。证据见verification.md及mobile-dialog-20261115/。T1/T3/T4保持开放。

### T3-ROLE-MENU-PERMISSION-SAVE（2026-11-15）

续验记录（2026-11-15）：隔离Demo JAR 54 changesets 启动，生产UI bundle经5196代理至隔离后端48128；真实浏览器以admin登录，在普通角色2权限树授予启用的WebSocket菜单565，显示“修改成功”，重新打开后该叶节点勾选、父级半选。首次保存数据库/API回读包含(2,565)；无令牌GET/POST均业务码401。取消子项未通过：误点“确定”再次保存，随后提交了移除测试菜单的恢复请求。恢复后的 role-menu 行多出3条活动角色2关系（1894、1951、12090），无法从本次操作证据确定其是否为保存前状态，未对专用库人工改写，之后整体DROP schema。基线1552行与TSV 1552行相符，但含重复 role/menu 对，不能仅按唯一对集合判断行缺失。专用账号、schema、浏览器标签、48128/5196进程已清理；启动前为空的Redis DB1中10条已核实缓存/token逐键清理为0。详见 `docs/verification/2026-11-11-full-source-migration/role-menu-20261115/result.md`。本子项部分完成，取消行为及精确全表差异核对仍开放；本轮JAR早于Core 009，不能作最新Core消费证据。

PHASE_GATE：沿用 `YH-20261111-full-source-migration`、codeVersion `0.1.0-SNAPSHOT`、governanceVersion `0.2.0`、knowledgeVersion `0.1.0`、用户完整迁移和“如果没有完成请继续”的持续授权。已有 `/system/role` 列表/权限面板打开取消的桌面对照不覆盖保存路径，故增补此冻结子项；基于原版已认可权限面板，原型 NOT_REQUIRED。仅 Core UI 表面和只属本轮的 MySQL schema/Redis DB；不改共享 `yuheng_demo`、历史密码、任何已执行 changeset、权限服务或消费端安装包，不发布 registry。

角色新增表单响应式子项：沿用本 workId 和用户样式修复授权，局部规格/计划 FROZEN，原型 NOT_REQUIRED。实际 390px 视口下默认 40% 弹窗宽 156px，名称输入宽 0；采用已用于配置表单的局部宽度约束，保留桌面 40% 和共享 Dialog 默认契约。验收覆盖 320/390/1440 实际视口、字段可编辑和取消无写；隔离源码预览不等同完整 Demo 验收。

结果：Core `RoleForm.vue` 采用 `width="min(100%, max(40%, 400px))"`。真实 Chrome 视口测量显示 390px 下弹窗/输入为 390px/226px，320px 下为 320px/156px 且页脚按钮右边界 304px，1440px 下为 576px/412px；组件内存适配器取消路径未产生写请求。Core UI 29 个测试文件/125 项、boundary、Vite 构建和声明构建通过；标准 compat 全目录 `vue-tsc --noEmit` 仍有既有类型错误。修复已提交并推送至 Core `feature/balanced-transformation` 的 `576e830`。隔离源码预览不等同完整 Demo 后端验收；T1 registry、T3 全页面和 T4 全矩阵继续开放。

REQ：角色菜单授权保存必须按现有原版契约调用 `GET /system/permission/list-role-menus?roleId=` 和 `POST /system/permission/assign-role-menu`，正确提交角色、叶节点及半选父节点；重新打开能读回，取消不写；所有变更真实隔离并在结束精确清理。

AC/T1：在运行任何 JDBC 服务前，从容器健康和 DB 变量/授权建立证据；创建唯一空 schema 与仅限该 schema 的临时授权；Redis 候选库需经认证实测为0，确保专用端口空闲。复用当前可执行 JAR，只用于系统/权限能力，不以其54个旧 changeset代表Core最新009发布；保存JAR/UI源版本和hash。AC/T2：隔离后端冷启动执行其登记的changeset，核对菜单/角色基线、21个历史密码BINARY一致且admin密码非空；前端静态服务与认证均指向隔离后端。AC/T3：通过实际 `/system/role` 菜单权限对话框，给一个非超级管理员角色加入一个由SQL状态/租户/删除条件确认可访问、未被管理员移除的叶菜单；按原界面选择并保存，验证POST精确roleId/menuIds、页面成功反馈、数据库 `system_role_menu` 精确变化、重新打开GET及UI勾选一致。AC/T4：取消对另一节点的改选后DB不变；无角色权限身份直接调用 GET/POST 被拒且快照不变。AC/T5：验证差异、权限以外行不变、Console/Network、全量适用UI检查、自检和进程/schema/grant/Redis精确清理。

Only Modify：计划、同workId验收证据与本轮验证夹具；不改产品源码、不为使UI写入成功而修改权限/菜单/租户配置，不读取或导出密码明文。临时管理员令牌、随机凭据不落盘；隔离 schema 的初始化为JAR Liquibase，用户密码保留原始变化集写入值。若源制品/合法菜单夹具/可用独立Redis无法确认，继续进行独立只读合同检查并如实 BLOCKED，不写共享环境。验收后先停本轮服务，再删除本轮schema和专属grants，仅清除已证实启动前为空的Redis DB；其他PID/数据库/缓存不动。回滚为关闭专用进程并DROP本轮schema/REVOKE精确grant。

组件取消路径续验（2026-11-15）：使用 Core 真实 `RoleAssignMenuForm`、Element Plus `ElTree` 和受控 API 边界，加载既有菜单权限、实际改变子节点勾选，再点击取消；断言勾选状态变化、Dialog 关闭、`assignRoleMenu` 未调用且没有 success 事件。只新增组件测试，不改产品代码、数据库或 registry。Core UI 29 个测试文件/124 项通过，Vite 生产构建、声明构建、平台边界及 diff check 通过；兼容层全目录 `vue-tsc --noEmit` 仍有既有扩展名/AutoImport 类型错误，不记通过。组件证据关闭取消路径，但不解释上一轮隔离 HTTP 恢复后出现的三条角色关系快照差异；旧专用 schema 已删除且快照缺少重复行元数据，精确全表一致性仍未证明。T3/T4 总体验收继续开放。

### T3-VITE-COMPAT-AUTOIMPORT（2026-11-15）

Core compat 源码在 Demo Vite 开发态须经过消费端 AutoImport 转换；pnpm 符号链接解析出的真实路径也必须覆盖。回归测试动态定位 `yuheng-ui/compat/platform` 所属包路径，调用项目 Vite 的真实 `transformRequest` 处理 `compat/utils/formRules.ts`，验证生成 `useI18n` import。Only Modify：Demo `vite.config.ts`、此转换测试、同 workId 计划和证据；不改 Core 包入口/运行时、依赖版本、registry、共享服务、数据库、密码。TDD 先观察缺少 import 时失败，再修过滤规则；随后跑 UI 全量测试、Vue 类型检查、生产构建和实际模块转换。此项通过只关闭开发态模块转换缺口，不外推为 registry 固定版消费或登录后浏览器验收。

结果：实际符号链接路径下的 AutoImport 文件过滤根因已确认；修复放行 Core compat 模块路径。回归测试修复前失败，修复后通过；Demo UI 13 项、类型检查、4321 模块生产构建、实际 `/@fs` 转换均通过。Vite 5187 已停止。隔离后端归属 app-server 且数据库/Redis 清理基线未知，保留不动；共享后端登录 API 仍超时，未继续登录后页面验收。首次 `pnpm exec vite` 意外触发 workspace install 并遇固定版 registry 404，移动的5个依赖目录按输出恢复。完整证据在 verification.md 的本节。

同次开发态运行观察到重复 Vue I18n 与组件注册 warnings，源码证实 `installYuhengUi` 与 `setupCompletePlatform` 重复安装 i18n，且 Demo 入口对 Core 已注册组件重复调用 `app.component`；仅记录待独立修复项，没有将它并入本次回归或压制警告。T1/T3/T4 总项不关闭。

T4 OAuth refresh Redis 故障子项结果：使用一次性 RESP 代理在单次 access-token `DEL` 上注入错误，真实 refresh-token 请求返回业务码 500；数据库 access/refresh 活动行和两个 Redis key 均保持故障前状态，证明该失败点可重复归因且没有污染共享环境。探针 `scripts/verification/oauth_refresh_redis_failure_probe.py` 和结构化证据 `oauth-refresh-redis-failure.json` 已保存，隔离资源均清理。该证据只关闭该单次失败注入子项，不外推到所有 Redis/事务/并发场景；T1 registry、T3 全页面和 T4 全矩阵继续开放。

### T3-COMPAT-PLUGIN-REGISTRATION（2026-11-15）

新增行为回归：Core runtime 已安装后运行 compat i18n 必须复用同一个 composer、补入 zh-CN/en compat message bundle，不重复注册 Vue I18n built-in components/directive；FormCreate 兼容安装保留其 form-create 能力但不覆盖 Core 已注册 Element Plus components。Demo main 不再重复导入/注册 `Pagination`、`ContentWrap`、`ContentDetailWrap`、`Dialog` 等 Core 组件，仅在未注册时补充 `DocAlert`/`DictTag`。

结果：真实 Vue app 行为测试先复现两类警告，修复后2项通过；Core UI全量28文件/123测试通过，生产构建及声明构建通过，boundary通过。Core旧 compat 全目录 `vue-tsc --noEmit` 存在预先的大量 AutoImport/ts扩展类型错误，不计通过。Demo UI 14项、typecheck、boundary、4314模块生产构建通过。隔离 Demo production bundle 浏览器 `/login` 显示正确中文文本且 warn/error 为空；只读无凭据提交。5187已停止，保留PID78090隔离后端和既有共享进程。完整证据见 verification.md 同标题章节。本项不关闭登录后页面、全量 Console/Network、T1 registry 或T4矩阵。
**2026-11-20 岗位权限续验：** 隔离真实登录探针验证 `system:post:query`：匿名请求 401、无权限用户 403 且 `system_post` 快照不变、精确授予查询权限后返回 4 条岗位；schema、容器、临时用户和端口已清理。该子项关闭，T4 全量 Controller/租户/事务矩阵继续开放。

**2026-11-20 Demo/Core 构建链复核：** 直接使用现有本地依赖执行 Demo UI 类型检查、14 项测试、导入边界和 3673 模块生产构建，均通过。并行 Vite/声明构建曾造成 `dist/index.d.ts` 被清理的短暂竞态，按正式串行顺序生成声明后 Demo 类型检查通过；workspace lockfile 仍为 `workspace:*`，固定 registry 消费仍未完成。

**2026-11-20 OAuth2 令牌生命周期续验：** 隔离真实 HTTP 探针覆盖错误密钥拒绝、`client_credentials` 发放与 `check-token`、合法 `refresh_token`（旧 access 失效、新 access 生效）及撤销（MySQL/Redis 均清理、再次校验 401）；专用 schema、客户端、容器和端口已清理。该子项关闭，授权码/密码模式、并发、Redis 故障和完整 OAuth2 矩阵继续开放。

**2026-11-20 OAuth2 授权码/密码模式续验及绑定修复：** 旧实现红灯确认错误 `redirect_uri/state` 会在绑定校验前删除授权码。Core 现使用事务和 `FOR UPDATE` 锁定授权码，完成 client、redirect URI、state 校验后才消费；新增 3 项 Core 单元契约测试，指定测试 3/3、Core 安装流程既有测试 51/51 通过。修复后 Demo 隔离 HTTP 探针以当前 56 changeset 基线验证 password grant、authorization-code issuance/exchange、错误 redirect/state 保留授权码和 replay 拒绝，专用资源清理归零。该子项关闭，OAuth2 并发、Redis 故障、社交回调及 T4 全矩阵仍开放。

**2026-11-20 OAuth2 授权码并发续验：** 当前 Demo JAR 在隔离 schema 中对同一授权码并发发送 8 个兑换请求，只有 1 个成功，7 个返回已消费错误；SQL 活动 token 行为 1/1，授权码为 0。错误 `redirect_uri` 对第二个授权码返回绑定错误，授权码保持 1 行且 token 行不变。专用容器、schema、端口和临时凭据均清理。该结果关闭单实例单授权码并发消费子项，不关闭多实例、跨租户、Redis 故障、社交回调或完整 OAuth2 矩阵；T1/T3/T4 保持开放。

**2026-11-20 部门精简列表续验：** 当前 Demo JAR 在隔离 schema 中真实验证 `system/dept/simple-list`：匿名请求返回 401；tenant-121 真实用户绑定仅数据范围角色后只读到 tenant-121 部门；伪造 tenant-122 请求头返回 403；SQL 日志确认查询包含 `tenant_id=121`，部门表快照前后不变。首次无角色夹具导致 Core 按设计返回空集，已记录并排除，修正夹具后通过。专用资源已清理。该结果关闭单路由认证与租户子项，不关闭完整 Controller/Mapper/T4 矩阵；T1/T3/T4 保持开放。

**2026-11-20 用户精简列表续验：** 当前 Demo JAR 在隔离 schema 中真实验证 `system/user/simple-list`：匿名请求返回 401；tenant-121 真实用户绑定仅数据范围角色后只读到本租户启用用户；`deptId` 筛选只返回目标部门用户；伪造 tenant-122 请求头返回 403。SQL 日志确认租户和部门条件均实际注入，用户表快照前后不变，专用资源已清理。该结果关闭单路由认证、部门筛选与租户子项，不关闭完整 Controller/Mapper/T4 矩阵；T1/T3/T4 保持开放。

**2026-11-20 角色精简列表续验：** 当前 Demo JAR 在隔离 schema 中真实验证 `system/role/simple-list`：匿名请求返回 401；tenant-121 真实用户只读到本租户启用角色；tenant-122 角色和 tenant-121 禁用角色均不出现；伪造 tenant-122 请求头返回 403。SQL 日志确认角色查询实际包含 `tenant_id = 121`，角色表快照前后不变，专用资源已清理。该结果关闭角色精简列表的认证、启用状态过滤与租户子项，不关闭完整 Controller/Mapper/T4 矩阵；T1/T3/T4 保持开放。

**2026-11-20 字典类型精简列表续验：** 当前 Demo JAR 在隔离 schema 中真实验证 `system/dict-type/simple-list`：匿名请求返回 401；tenant-121 与 tenant-122 的真实用户返回相同的两个共享字典类型夹具，禁用字典类型按源码契约保留；完整响应未逐行比较。SQL 日志确认 `system_dict_type` 查询没有追加 `tenant_id` 条件，所选字段快照前后不变，专用资源已清理。该结果关闭字典类型精简列表的认证与限定夹具的平台共享读取子项，不关闭字典数据联动、完整 Controller/Mapper/T4 矩阵；T1/T3/T4 保持开放。

**2026-11-20 字典数据精简列表续验：** 当前 Demo JAR 在隔离 schema 中真实验证 `system/dict-data/simple-list`：匿名请求返回 401；tenant-121 与 tenant-122 的真实用户返回相同的两个启用字典数据夹具；禁用和逻辑删除夹具均被过滤。SQL 日志确认查询实际为 `deleted = 0 AND (status = ?)`，绑定参数为 `0(Integer)`，没有 `tenant_id` 条件，表快照前后不变，专用资源已清理。首次历史编码解码失败和第二次预编译参数断言错误均排除，修正探针后的第三次完整运行通过。该结果关闭字典数据精简列表认证、状态过滤与共享读取子项，不关闭字典数据写入、类型联动、完整 Controller/Mapper/T4 矩阵；T1/T3/T4 保持开放。

