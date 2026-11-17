# ERP 消费端集成验证记录

验证日期：2026-11-13  
消费端：`yuheng-demo`  
核心依赖：`yuheng-core` 的版本化 `yuheng-server`、workspace 中的 `yuheng-ui`  
数据库：本机 Docker `mysql8`，数据库 `yuheng_demo`

## 验证范围

本次验证覆盖 ERP 模板复制到消费端后的后端、前端、Liquibase、动态菜单、构建产物、生命周期脚本和代表性 HTTP 接口。

ERP 源码位于：

- 后端：`yuheng-demo-server/yuheng-demo-business/src/main/java/com/yuheng/demo/module/erp`
- Mapper XML：`yuheng-demo-server/yuheng-demo-business/src/main/resources/mapper`
- Liquibase：`yuheng-demo-server/yuheng-demo-server-bootstrap/src/main/resources/db/changelog/business/erp`
- 前端 API：`yuheng-demo-ui/src/api/erp`
- 前端页面：`yuheng-demo-ui/src/views/erp`

Demo 复制业务模块后独立维护源码和数据库变更。运行时不引用 `yuheng-business-templates` 源码目录；平台能力通过 `yuheng-core` 的公开 Java/UI 入口提供。

## 数据库证据

只读查询结果：

| 项目 | 结果 |
| --- | ---: |
| ERP 业务表 | 33 |
| 会员业务表 | 11 |
| ERP Liquibase changeset | 35 |
| 会员 Liquibase changeset | 11 |
| `system_operate_log.success` 列 | 0 |
| 管理员历史密码散列 | 保留 |
| `yudao_demo*` 表 | 5 |

ERP changeset 由以下文件组成：

- `001-erp-schema.sql`：33 张 ERP 业务表
- `002-erp-identifier-width.sql`：`erp_product.unit_id` 宽度增量修复
- `003-erp-stock-active-uniqueness.sql`：租户、商品、仓库有效库存唯一性修复

平台、Quartz、Flowable 和 `yudao_demo*` 由 `yuheng-core` 的独立 Liquibase 入口管理；ERP 迁移没有创建这些表，也没有写入示例业务数据、凭据或密钥。

## 前端组件和菜单

当前数据库权限接口返回 633 个菜单节点、1924 个权限项。ERP 根菜单为 `597`，路径为 `/erp`，ERP 页面菜单覆盖产品、库存、采购、销售和财务。

Demo 的动态组件解析规则为：

1. 先从 `yuheng-demo-ui/src/views` 的业务 glob 中解析；
2. 再从 `yuheng-ui/compat/views` 的 Core 平台 glob 中解析；
3. 未注册的叶子组件显示明确的“页面组件未注册”提示。

ERP 的 23 个带组件菜单均解析到 Demo 页面。系统和基础设施页面解析到 Core 的完整兼容页面，包括用户、角色、菜单、部门、岗位、字典、配置、定时任务、代码生成、日志、文件、社交等页面。

历史平台快照还包含 CRM、BPM、商城、OA、MES、HRM、FMS、PMS、WMS、AI、IoT 等业务菜单。它们目前没有全部复制到 `yuheng-demo`，因此不能把这些菜单的存在描述为对应业务源码已经完成迁移。后续选择某个模板后，应按同一消费者复制、脚本、Liquibase、构建和接口验证流程接入。

## 构建和运行验证

已执行：

```bash
pnpm --filter yuheng-demo-ui typecheck
pnpm --filter yuheng-demo-ui test
pnpm --filter yuheng-demo-ui lint:platform-imports
./scripts/build.sh
python3 -m unittest discover -s scripts/tests -p 'test_*.py' -v
```

结果：

- `vue-tsc --noEmit`：通过
- Demo UI 测试：5 项通过
- 平台导入边界：通过
- Maven reactor package：通过
- 前端生产构建：通过，4317 个模块转换成功
- 前端资源已复制到 Spring Boot JAR 的 `static` 目录
- 生命周期测试：通过
- 打包 HTTP 测试：6 项中 5 项通过，1 项按条件跳过；修复 API 前缀回退问题后重新执行通过

构建产物：

- `yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar`
- `yuheng-demo-ui/dist/index.html`

启动脚本使用 macOS `launchctl` 托管：

- `com.yuheng.demo.backend`
- `com.yuheng.demo.ui`

验证时两个服务均为 running：

- 后端：`http://127.0.0.1:48080`
- 前端：`http://127.0.0.1:5173`

## HTTP 验证

使用 `admin/admin123`、`tenant-id: 1` 登录，登录接口返回 `code: 0` 和 access token。

以下请求均返回 `code: 0`：

- `GET /admin-api/system/auth/get-permission-info`
- `GET /admin-api/erp/product/page?pageNo=1&pageSize=10`
- `GET /admin-api/erp/stock/page?pageNo=1&pageSize=10`
- `GET /admin-api/erp/account/page?pageNo=1&pageSize=10`
- `GET /admin-api/erp/finance-payment/page?pageNo=1&pageSize=10`
- `GET /admin-api/erp/finance-receipt/page?pageNo=1&pageSize=10`

当前 ERP 表没有业务数据，上述分页接口的 `total` 均为 `0`，`list` 均为空。这证明接口、权限、Mapper 和表结构已连通，不代表业务数据初始化已经完成。

前端静态服务此前只把 `/admin-api` 当作 API 路径，`/app-api` 未知请求会错误回退到 `index.html`。现已统一识别 `/admin-api` 和 `/app-api` 并代理到后端；`/app-api/nonexistent-test` 现在返回后端 JSON，而不会返回 HTML。

## 尚未覆盖

- 2026-11-13 浏览器续验补充：默认租户名称缺失已修复；使用 `芋道源码` 租户通过 UI 登录。系统管理用户列表真实加载组织树和 15 条用户记录，基础设施代码生成页面加载筛选与空数据表，ERP 首页显示零统计，ERP 产品信息页加载筛选、分类选择、按钮和空数据表。浏览器记录的 console warning/error 为 0。未逐页覆盖其它系统/基础设施和 ERP 子页面，也未完整验证新增、修改、删除等写交互。
- 首页显示“授权模块 0、可访问入口 0”，同时历史权限响应包含大量菜单，属于模块授权统计与历史菜单快照的口径差异，需后续核查展示定义；不能由此认定业务模块已全部授权或迁移。
- `yuheng-ui@0.1.0-SNAPSHOT` tarball 的 workspace 外安装消费验证已有独立记录 `yuheng-core/docs/verification/yuheng-ui-package-identity/verification.md`：实际 tarball 安装、Demo 消费端测试、类型检查和构建通过；npm registry 发布及基于 registry 锁文件的干净安装尚未执行。
- 尚未将历史快照中其它业务模板全部复制到 Demo；它们仍属于按需接入范围。
- 2026-11-14 已在专用 MySQL schema/Redis DB/端口完成代表性采购、入库、销售、出库、付款和收款闭环（53 次请求）及权限/租户续验；具体结果、失败记录、参数边界缺口和清理结果见 `2026-11-11-full-source-migration/verification.md`。不代表全部 ERP 工作流或浏览器验收完成。
- 当前验证只读使用现有本地 `yuheng_demo`；没有在共享库中写入测试业务数据。
