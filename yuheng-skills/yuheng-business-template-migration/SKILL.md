---
name: yuheng-business-template-migration
description: Use when copying, integrating, or validating a Yuheng business template in a consumer project, including selective module migration and template consumption tests.
metadata:
  version: 0.1.0
  entry: public
---

# Yuheng 业务模板迁移

业务模板是源码起点，复制后的代码归消费项目独立维护；平台能力来自版本化 `yuheng-core` 和 `yuheng-ui`。需要数据库的模板应交付自身的 Liquibase 迁移及必要业务初始化数据，明确其来源、验证状态和跨模块依赖；平台表及共享组件资产按 core 的归属管理。不得把模板仓库作为运行时依赖；用户可明确要求预览并合并模板更新，不自动或静默同步。先读取项目入口、当前 core 规则、已有规格和计划，并保留工作区原有修改。

## 确定范围与环境

- 确认用户选择的模板、功能、目标工程和验收范围；仅做消费流程测试时，在隔离的工程副本和独立数据库进行，不将试验代码当作正式接入。用户明确要求正式接入时，在其指定工程实施。
- 对照模板及原始源码盘点后端、前端、配置、菜单、权限、字典、表、初始化数据和外部服务；追踪传递依赖，区分 core 已发布能力、其他业务模块和缺失资产。检查实际源码和版本，不以模板说明、文件数量或截图推断功能可运行。数据库来源审计必须同时检查原始仓库当前 `sql/mysql`、Git 历史中被删除或拆分的模块脚本、模块测试结构和对应源码提交；当前目录缺文件时不能直接判定原始 SQL 不存在。
- 依赖超出已授权功能时先查找不扩大业务范围的实现方式；确实需要用户选择业务范围时说明影响。禁止通过空实现、删除功能或伪造接口掩盖缺口。

## 实施

- 按消费端结构复制选定源码，调整业务包名和导入，保留 `com.yuheng.platform`；接入现有构建、组件、路由、请求实例和运行配置。对于 Core 的动态菜单组件解析器，必须把所选模板页面目录纳入消费端实际使用的组件注册表（例如 `businessViewComponents` 中按需 `import.meta.glob('../views/<module>/**/*.{vue,tsx}')`），并确认模板菜单中的 `component` 字符串能解析到页面组件；只复制页面而不注册目录会导致菜单访问落到缺省页。具有显式业务路由的页面还要单独注册顶层/业务路由，并验证刷新和匿名访问行为。检查版本化 core 的真实导出及依赖，避免引用 core 工作区源码或假定模板可以独立构建。
- 公开分享等匿名页面必须注册为不带受保护布局的顶层路由，不能挂在 `Home` 或其他会加载登录态组件的布局下；在采用 Vue Router 的消费端可用 `router.addRoute(route)` 注册公开路由，受保护业务页面才使用 `router.addRoute('Home', route)`。`meta.public` 本身不会改变路由父布局；还需核实实际路由守卫允许该地址，并在全新匿名浏览器上下文中验证直接打开和刷新均不请求受保护接口。
- 使用 Vite 开发模式消费 Core compat 源码时，检查自动导入插件产生的公开子路径是否又被单独预构建。`setupCompletePlatform` 与页面必须使用同一份语言、请求和运行时状态；将自动导入的 `yuheng-ui/compat/hooks/web/useI18n`、`useMessage`、`useTable`、`useCrudSchemas` 及 `yuheng-ui/compat/utils/formRules`、`dict` 子路径加入 `optimizeDeps.exclude`，与 `yuheng-ui` 一起排除；CommonJS 依赖 `qs` 则通过 `optimizeDeps.include: ['yuheng-ui > qs']` 转换。配置变更后强制重启预构建，实际验证登录中文文案、动态菜单和业务请求；不能把出现 `login.*` 文案键的问题仅通过放宽浏览器定位器绕过。生产构建与开发模式分别验证。
- 当消费端直接引用 Core compat 入口时，确认其解析到版本化 `yuheng-ui` 包的真实 compat 源码和随包声明，不依赖 Core 仓库相对路径或消费端宽松声明掩盖问题。消费端运行时直接导入的依赖必须在消费端 manifest 中声明为直接依赖；通过严格类型检查验证集成，避免用宽泛 `any` shim 绕过缺失或冲突类型。保留并记录确有必要的接入 shim，逐项证明其边界；不能据局部入口类型检查通过推断整棵旧版 compat 路由或初始化源码无错误。
- 盘点并复制模块运行资源，包括 MyBatis XML、预置 JSON 和流程定义；同步调整 XML 的 namespace、resultType、OGNL 等业务类名，检查消费端 classpath 和 Mapper 扫描配置。流程文件与预置数据只在其业务流程明确要求时导入，不能把文件存在当作已部署或已验证。
- 将模板已交付的模块迁移随源码复制到消费端，依据原始表结构、实际代码和数据库现状审查业务表、索引、约束和数据，遵守消费端数据库迁移规则并注册统一 Liquibase 入口。模板缺失迁移时记为交付缺口；补齐并验证后再接入。已执行的 changeset 不得改写；未经明确授权不得清理或覆盖现有数据。缺少可信的结构来源时保留未完成状态，不猜测 DDL。
- 接入所选菜单、权限、字典和租户配置，检查冲突及数据归属；不因历史菜单存在就认定对应模块、表和权限已可用。
- 检查消费端是否为未启用模块注册了 catch-all/disabled fallback Controller。模板 mapping 必须声明启用模块需要解除的精确兜底路由、文件和 handler；只移除所选模块对应的兜底映射，保留所有未选择模块的兜底。验证真实模块 Controller 已被 Spring 注册并能处理代表 API，不能仅凭源码复制、编译或 Liquibase 成功认定模块已接通。

## 验证与交付

- 记录模板来源、版本或提交、消费端/core 版本、复制范围、依赖及未覆盖功能。先在隔离数据库验证首次迁移、重启和已有数据兼容，再按授权范围执行；记录环境、命令与结果。
- 按功能风险运行后端测试和构建、前端类型检查与构建，并启动真实服务验证认证、菜单、关键业务操作、权限及租户边界。需要其他模块或外部服务的功能应明确测试条件和结果。
- 对每个工作流分别追踪创建、审核、反审核、删除的实际副作用；订单进度、金额占用和库存变动可能发生在不同阶段。先从 Service/Mapper/调用方建立断言，再对照上游，不将相似流程的语义直接套用。错误断言须保留失败证据和修正依据，不算业务修复红灯。
- 权限夹具通过受支持 API 创建，套餐/角色菜单包含必要父节点；验证目标权限实际返回后再测行级隔离，区分菜单权限拒绝、租户请求头拒绝和 Mapper 租户过滤。历史租户过期时创建专用测试租户，不改历史到期时间或密码；新增夹具遵守实际字段长度。
- 临时环境同时隔离数据库、端口和 Redis 缓存/令牌/编号；使用前确认目标缓存为空，凭据从环境读取，证据不保存 token、口令或密码哈希。全部依赖服务的回归结束后再停止实例、清理本次创建的精确 schema 及授权和专用缓存，不将清理与 HTTP 验证并行执行。
- 通过现有交付、自检和 API/UI 验证技能记录证据，逐项区分通过、失败和未执行。编译通过、文件已复制、测试环境成功均不能替代正式目标环境的验收。试验产物单独标记，只有用户明确选择后才作为正式业务代码交付。

## 可选模板更新

- 模板初始化前确认使用者选择的模块，只把所选模块的源码和迁移资产加入消费端，并记录模板仓库提交或发布版本。
- 仅在用户明确要求更新时运行更新流程。先比较消费端副本与目标模板版本，输出新增、删除、修改文件及冲突分类；预览前不修改消费端。
- 将变更区分为模板业务修复、Core 接入适配、消费端定制和冲突。保留必要的接入适配，定制不反向合入模板；冲突逐项审查，禁止整目录覆盖。
- 单独比较数据库 changeset、checksum、执行历史与实际 schema。已执行 changeset 不得改写，模板修复以新 changeset 前向应用。若存在重复、空值、超长或其它不兼容数据，迁移应停止并报告，不自动删除、截断或覆盖数据。
- 更新结束时记录模板来源版本、应用和保留的差异、迁移状态及验证证据，并运行受影响的构建、测试和隔离数据库验证。不做后台自动同步或静默更新。

### 可复用更新工具

业务模板仓库提供 `tools/template_update.py`。它是消费端的显式更新工具，不是运行时依赖，也不会重建、清空或删除消费工程。消费端为每个模块提供映射 JSON，将模板相对路径映射到自己的源码、资源和 Liquibase 目录，并按需要声明包名替换。映射可以声明 `consumerDependencies`；工具预览时会原样输出依赖清单和版本来源。使用者选择模板后，应逐项检查并按需把依赖加入承载模板代码的消费端模块，确认其版本能由当前 Core BOM 或消费端既有版本目录解析，再运行构建。此步骤只调整已选择模块所需的消费端构建接线，不会自动改 POM，也不为未选择的模块引入依赖。

首次接入或确认一个模板版本后，可执行应用并记录基线（注意：单独使用 `--record-state` 仅记录现状基线而不会写入模板文件；首次初始化需配合 `--apply` 或先 `--apply` 再 `--record-state`）：

```bash
python3 tools/template_update.py \
  --template-root /path/to/yuheng-business-templates \
  --consumer-root /path/to/yuheng-demo \
  --mapping /path/to/erp-mapping.json \
  --apply \
  --record-state /path/to/erp-template-state.json
```

若新增模板的 `consumerDependencies.npm` 修改了消费端 `package.json`，且消费端使用独立 `pnpm-lock.yaml` 并位于父级 workspace 目录内，需使用 `CI=true pnpm --dir <ui-dir> --ignore-workspace install --no-frozen-lockfile --ignore-scripts` 刷新锁文件，避免触发交互式提示或与根 workspace 冲突。

模板仓库有变更且使用者明确要求更新时，先只读预览：

```bash
python3 tools/template_update.py \
  --template-root /path/to/yuheng-business-templates \
  --consumer-root /path/to/yuheng-demo \
  --mapping /path/to/erp-mapping.json \
  --state /path/to/erp-template-state.json
```

预览报告至少区分 `template_added`、`template_changed`、`consumer_customized`、`consumer_only`、`conflict` 和 `template_deleted`。只有模板新增或模板单方修改可以进入安全应用；如果基线记录的源文件和消费端文件已经不同，模板后续修改必须归类为 `conflict`，不能覆盖消费端适配。冲突、无法分类的差异和模板删除必须先人工审查。确认后才可增加 `--apply`；模板删除还必须显式增加 `--allow-delete`。应用前后均审查 Git 差异，并运行受影响的模板测试、消费端构建和隔离数据库验证。

数据库文件也按映射参与比较，但更新工具不会修改已执行 changeset、清理 checksum、删除业务数据或自动运行数据库迁移。数据库结构修复必须在模板中新增前向 changeset，由消费端按自己的迁移流程和目标库状态单独审批、执行和验证。消费端的 UI 适配、包名适配、集成开关和其它定制始终保留；模板修复通过此流程选择性带入，不会覆盖整个模块目录。
