# Yuheng Demo 管理端按 Core/业务分层集成设计

## 目标

将当前独立的 `yudao-ui-admin-vue3` 管理端按职责分入 `yuheng-core` 与 `yuheng-demo`：core 维护可复用通用平台 UI 包，demo 通过 `package.json` 依赖该包并维护自己的业务 UI，最终在 demo 前端应用中组合为完整管理端。

## 当前结构与问题

- `yuheng-demo` 是消费端 Spring Boot 工程，后端通过 Maven `pom.xml` 依赖 `yuheng-server`，管理 API 通过 `/admin-api` 提供。
- `yuheng-core/yuheng-ui` 是可版本化消费的 NPM UI 包，负责前端通用平台能力；`yuheng-demo/yuheng-demo-ui/package.json` 声明 `yuheng-ui` 依赖，负责业务前端并组装完整应用。
- 当前 `yuheng-ui` 已有平台运行时、登录、权限、布局、共享请求和部分 system/infra 路由；当前 `yuheng-demo-ui` 只有消费端骨架和轻量首页。
- 相邻目录 `yudao-ui-admin-vue3` 是独立 Vue 3/Vite 管理端，包含完整的 API、菜单页面和组件。此前为浏览器验证所做的 `.env.local` 和 Vite 代理更改只属于该独立仓库，不会随本次消费端迁移自动带入。
- `yuheng-demo` 工作区已有未提交的 Liquibase、后端配置和文档改动；`yuheng-core` 也可能有独立工作区状态。本次实施必须分别检查并保留两边已有工作。

## 方案

遵循 core 提供共用/通用能力、demo 承载业务能力的分层，并参照 `athena-core` 与 `demo` 的依赖方式：后端通过 Maven 消费 `yuheng-server`，前端通过 NPM 依赖消费 `yuheng-ui`。`yuheng-demo-ui` 不复制或直接引用 `yuheng-core/yuheng-ui/src`，只通过 `package.json` 声明版本化 `yuheng-ui` 包和业务页面所需依赖。

迁移时按功能归属审查 `yudao-ui-admin-vue3`：登录认证、布局、路由守卫、权限、用户/租户上下文、共享请求、通用组件和复用型 system/infra 平台页面属于 `yuheng-ui`；ERP、CRM、MES、会员、商城、OA、HRM、IoT、AI 等产品业务 API、页面和路由属于 `yuheng-demo-ui`。已经存在于 core 包的能力复用并补齐缺失的通用页面；不得把业务 API 或业务表单迁入 core。demo 的 Vite 应用组装平台插件与消费端业务路由，所有业务 API 走 `/admin-api`。

只迁移各层运行和构建所需内容，不把上游 Git 元数据、`node_modules`、开发者 IDE 文件、上游文档站或其他独立项目带入。为 core 平台提取和 demo 业务页面迁移分别维护清单，记录来源路径、最终模块归属、API 前缀、路由/权限码和依赖。保持 core 与消费端各自的包名、版本、锁文件和启动说明。

## 配置与启动

- `yuheng-core/yuheng-ui/package.json` 定义并构建可消费平台包；`yuheng-demo-ui/package.json` 通过版本依赖集成 `yuheng-ui`，并声明业务页面所需依赖。两仓库分别维护锁文件、构建和验证流程。
- 本地默认服务地址使用相对路径 `/admin-api`；Vite 代理目标可由环境变量覆盖，默认值为 `http://127.0.0.1:48080`。
- 租户功能沿用当前后端租户配置；本地验证码和 API 加密开关与本地后端 profile 保持一致。
- 前后端按独立工程构建和运行。Maven 管理后端依赖及产物，pnpm 管理 `yuheng-ui`、demo 业务 UI 和前端构建；不因组合页面而将 Node 构建链隐式塞入 Spring Boot JAR。
- core 与 demo 文档分别说明包发布/本地包联调、前端开发代理、后端启动和整套本地启动方式。

## 兼容与失败处理

- 管理端 API 地址必须始终落到 `/admin-api`，避免开发环境直连跨域或部署后引用 `localhost`。
- 未登录访问应进入平台登录页面；登录成功后读取平台权限和后端动态菜单。
- 业务页面只依赖 `yuheng-ui` 的公开导出，不反向导入 core 源码，也不维护第二套认证、请求或租户上下文。
- 平台通用接口和页面归 core，产品业务 API 和页面归 demo；菜单、路由、权限码应与后端 `yuheng-server`/demo 的模块能力匹配。
- 现有轻量业务首页由完整管理端首页替代；已有业务独立路由若确有有效消费端功能，应在迁移核查中保留并接入菜单，不默认删除未审查的业务页面。

## 验证标准

1. `yuheng-ui` 作为 core NPM 包构建、导出与契约测试通过，且未引入 demo 业务依赖。
2. `yuheng-demo-ui/package.json` 通过本地打包产物联调 `yuheng-ui`，`pnpm-lock.yaml`
   锁定完整依赖图；业务边界测试、类型检查和生产构建通过。正式发布后切回 registry 版本。
3. 消费端 Vite 的 `/`、`/login` 返回组合后的管理端，`/admin-api` 代理可访问本地后端。
4. 使用本地租户与管理员账号登录后，完整首页和动态权限菜单可见，刷新客户端路由仍能加载。
5. 后端 Maven 构建独立通过，前端仍由 npm/pnpm 应用构建提供，不要求 Spring Boot JAR 内嵌 UI。
6. Maven 和前端验证不覆盖或回滚两仓库开始前已有的修改。

## 不在本次范围

- 新增原管理端范围之外的平台或业务功能。
- 将 `yudao-ui-admin-vue3` 的 Git 仓库合并或删除；它作为只读迁移来源保留。
- 设计正式生产域名、TLS、反向代理、多实例部署和前后端静态资源托管拓扑。
