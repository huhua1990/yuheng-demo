# Yuheng 后端代码规范

## 真实契约与兼容

- 包根 `com.yuheng.platform`；框架在 `framework`，平台域在 `module.system`、`module.infra`。`yuheng-server` 为依赖聚合入口，实际启动类、运行配置和业务定制留消费端 bootstrap。
- 现有 Controller 的 HTTP 方法、路径、参数位置和 VO 命名保持兼容。源码包含 GET/POST/PUT/DELETE，禁止批量改成 POST。
- 新接口遵循目标模块真实惯例和已冻结规格，明确参数校验、权限注解、错误码及租户/数据权限行为。
- JSON 返回复用 `CommonResult<T>`，分页复用 `PageResult<T>` 的 `list/total`。下载等特殊响应按原契约。
- `CommonResult.success(data)`、`CommonResult.error(ErrorCode)` 或 `error(Integer, String)` 以真实签名使用；不编造 `error(String)`、无参数 `success()`。

## 分层与文件

- 沿用模块的 Controller、请求/响应 VO、Service 接口及实现、Mapper/DO 等分层，不为修改老逻辑新建平行结构。
- Mapper 复用 `BaseMapperX` 与现有查询能力；Service 是否继承基类以当前实现为准，不强制所有 Service 继承 `ServiceImpl`。
- 现有转换方式可能为 `BeanUtils` 或专用转换器，先复用；不为了凑“8 类产物”新增 XML、DTO、Convert。
- 写操作按事务边界使用 `@Transactional(rollbackFor = Exception.class)`；错误码和异常复用框架已有类型。
- 身份与租户从框架可信上下文获取，不信任请求体中的任意用户/租户 ID 绕过授权。

行为变更遵守 `yuheng-backend-tdd`；日志使用现有日志组件和占位符，不输出敏感值。新增共性 API 记录消费端影响及兼容测试。
