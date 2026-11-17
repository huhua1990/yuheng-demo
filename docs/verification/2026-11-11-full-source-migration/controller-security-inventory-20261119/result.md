# T4 System/Infra 管理端路由安全静态盘点

日期：2026-11-19  
Work ID：`YH-20261111-full-source-migration`

## 范围与复跑

盘点 Core `yuheng-module-system` 与 `yuheng-module-infra` 的 `controller/admin/**` 下所有 `*Controller.java`。使用：

```bash
python3 scripts/verification/controller_security_inventory.py
python3 -m py_compile scripts/verification/controller_security_inventory.py
```

机器可读结果：`summary.json`、`routes.csv`。本次发现 47 个 Controller、322 条方法路由映射记录；251 条声明方法级或类级 `@PreAuthorize`，22 条声明 `@PermitAll`，10 条声明 `@TenantIgnore`，49 条既没有细粒度权限注解也没有 `@PermitAll`。计数按路由映射变体计算，别名路径分别计入。

## 框架规则核对

- `YudaoWebSecurityConfigurerAdapter` 将 `@PermitAll` 映射和配置 `yudao.security.permit-all-urls` 放行，其余请求最后由 `anyRequest().authenticated()` 保护。因此“不带 `@PreAuthorize`”不等于匿名可访问，但只证明登录身份，不证明细粒度角色/权限检查。
- `TenantSecurityWebFilter` 对登录主体校验 `tenant-id` 与主体租户一致；未登录且路由未配置为忽略时，要求租户头并校验租户状态。Controller 的 `@TenantIgnore` 用于该过滤器忽略 URL 集合。
- `TenantDatabaseInterceptor` 对 `TenantBaseDO` 加租户过滤；`@TenantIgnore` 实体或全局忽略表不加过滤。静态路由清单不包含每个 Controller 调用链最终读写的 DO/Mapper，不能推出租户 SQL 行为。

## 代表性候选与解释

- `GET /system/post/simple-list`（及 `list-all-simple`）只有全局认证，没有细粒度权限注解；仍需与原始上游同一路由比较，并用隔离实例验证普通登录主体能否读取、返回数据是否按租户过滤。
- `GET /infra/config/get-value-by-key` 同样只有全局认证，Controller 还限制不可见配置值；需核对上游契约及敏感键响应边界，当前静态盘点不把它认定为漏洞。
- `POST /infra/file/create`、`POST /infra/file/upload` 和 `GET /infra/file/presigned-url` 没有方法级权限注解，但不带 `@PermitAll`，受全局认证；需要确认业务授权设计以及租户/文件配置访问边界。
- `GET /system/tenant/simple-list` 同时标记 `@PermitAll` 和 `@TenantIgnore`，属于有意免登录、跨租户查询候选，应与原版一致性及返回字段最小化一起检查。
- `GET /infra/file/{configId}/get/**` 同样免登录并忽略租户，是公开文件读取路由；需要确认路径授权依赖不可猜测对象标识的程度、文件客户端配置边界及上游行为。

已将代表性路由回溯到 `/Users/huhua/study/ai/yuheng/ruoyi-vue-pro` 对应 Controller：岗位精简列表、参数值读取、文件上传/预签名/元数据创建/公开读取、租户精简列表的映射与关键权限/租户注解均与上游一致。Demo `application.yaml` 的安全免认证白名单仅为 `/admin-api/mp/open/**`，租户 URL 忽略项仅为 `/jmreport/*`，因此这些 System/Infra 路由没有由消费端配置扩大为免认证或免租户。

## 证据限制与下一步

这是源码注解盘点，不评估配置白名单、Spring 表达式最终求值、服务方法的数据权限、Mapper/DO 租户过滤或运行时认证结果。路径包含映射常量/表达式的路由需人工解释。没有发现足以仅凭该静态结果直接修改代码的已证实差异；运行时变更须先建立失败断言，并在隔离 Demo 中分别验证匿名、登录无权限、登录有权限及跨租户请求，结合 SQL 前后快照。该盘点关闭的是 T4 静态 Controller 路由清单子项，不关闭全量 Controller/Mapper 权限和租户矩阵、T4 总项或 T1/T3。

## 岗位精简列表隔离运行验证

运行脚本：`python3 scripts/verification/post_simple_list_security_probe.py`。当前 Demo JAR SHA-256 为 `e50bcf20ec4ca4157638393fcfd9730707bd7395e08a08296e5a9e2266da1e9f`；专用 schema `yuheng_t4_postlist_20261119` 冷装 54/54 changesets，MySQL/Redis/后端端口分别为 13348/16428/48183。隔离进程配置了随机 mock secret，但本轮同时创建了一名只存在于 disposable schema 的 BCrypt 测试用户，并通过真实 `/system/auth/login` 获取 access token；没有访问共享 MySQL/Redis 或历史用户密码。

空库种子中租户 121、122 均已到期；只在本轮 schema 内将这两个活动租户启用并延长一年，核验生效后各创建一个启用岗位夹具。匿名 GET `/system/post/simple-list` 返回业务码 401。使用无角色、无岗位 query 权限的 mock 主体请求 tenant 121，返回业务码 0 且仅含 tenant 121 岗位；改为 tenant 122 后仅含 tenant 122 岗位。SQL 直接核验两条夹具分别带 `tenant_id=121/122` 且处于活动状态。该运行结果证明全局认证兜底及两租户方向的岗位查询隔离；mock 登录主体从请求头取得 tenantId，因此不证明真实 token 与伪造 `tenant-id` 不一致时的拒绝行为。

真实 token 的正向请求返回 code 0；将同一 token 的 `tenant-id` 从 121 改为 122 后返回 code 403，证明 `TenantSecurityWebFilter` 拒绝主体租户与请求租户不一致。随机测试密码和散列没有写入证据。应用优雅关闭；专用 MySQL/Redis 容器删除，schema 随 MySQL 容器一并销毁；13348、16428、48183 均无监听。结构化请求、SQL 夹具、制品哈希与清理结果见 `post-simple-list-runtime.json`。关闭岗位精简列表匿名认证、两个租户方向查询范围及真实 token 租户头不一致拒绝子项；其余 Controller 路由和 T4/T1/T3 总体验收继续开放。

## 参数配置值读取隔离运行验证

运行脚本 `scripts/verification/config_value_security_probe.py`，使用当前 Demo JAR（SHA-256 `e50bcf20ec4ca4157638393fcfd9730707bd7395e08a08296e5a9e2266da1e9f`）与专用 MySQL schema、Redis 容器和后端端口 48184。新建 tenant-121 的无角色测试用户并真实登录。匿名读取可见配置得到业务码 401；该用户读取可见平台配置得到 code 0 和预期值；读取隐藏配置得到 `1001000004` 且 data 为空；同一真实 token 配合 `tenant-id: 122` 得到 403。

配置实体是平台共享数据（`@TenantIgnore`），因此匹配租户的登录用户可读取可见配置，不代表配置按租户分行授权。对两个配置夹具的键、值 SHA-256、visible 与 deleted 状态执行请求前后快照，结果完全相同；测试用户没有角色关联。夹具使用随机密码，证据不含明文或散列。应用正常关闭；专用容器不存在，13349、16429、48184 均无监听。结构化结果见 `config-value-runtime.json`。该验证仅关闭此单路由的匿名认证、可见性、真实 token 租户头校验和只读行为子项，不证明其它配置 API、密钥策略、全量权限或 Mapper 租户边界。

同一隔离运行还验证了 `/system/tenant/simple-list` 的上游定义。代码与原版 Controller 一致：`@PermitAll`、`@TenantIgnore`，通过 TenantMapper 查询启用租户并映射为精简 VO。匿名请求不发送 `tenant-id`，返回 HTTP 200/code 0；结果租户 ID 为 1、121、122，与隔离 schema 中启用租户一致。响应中非空字段只有 `id`、`name`，但 Jackson 同时序列化其它 VO 字段为 null；因此结论是有效数据字段最小化，而不是 JSON key 仅含两个字段。请求前后租户行状态与有效期快照一致。该路由源码和行为与上游一致；隔离数据在本轮容器移除后销毁。完整结果写入同一 `config-value-runtime.json`。这不等于证明所有 `@PermitAll`/`@TenantIgnore` 路由都具有适当匿名访问边界。

## 岗位管理分页细粒度权限隔离运行验证

运行 `scripts/verification/post_page_permission_probe.py`，使用独立 schema `yuheng_t4_postpage_20261120`、专用 MySQL/Redis 容器及后端端口 48185。授权夹具使用 `system_menu.id=43`，经 SQL 确认权限码为 `system:post:query`；JAR SHA-256 为 `e50bcf20ec4ca4157638393fcfd9730707bd7395e08a08296e5a9e2266da1e9f`。

对真实 `/system/post/page?pageNo=1&pageSize=10` 请求，匿名请求返回 401；tenant-1 真实密码登录的无角色用户返回 403；只关联一个带 menu 43 权限的普通角色用户返回 code 0、4 行/total 4。拒绝请求前后的岗位表指定字段快照一致，编码和名称按 HEX 记录以避免客户端字符集替换。夹具直接插入本轮隔离 schema，密码随机且不记录；没有操作共享数据库或历史密码。首次尝试生成的密码超过接口 16 位上限，登录得到参数错误，未形成权限验证结果；调整夹具后全新环境重跑。最终应用优雅关闭，专用容器删除，13350/16430/48185 无监听；证据见 `post-page-permission-runtime.json`。该结果仅覆盖单租户岗位分页的上述权限场景，不代表岗位写权限或完整 Controller 矩阵。
