# Yuheng Server 能力索引

本文档提供 Yuheng 后端框架的能力快速索引。

---

## 框架能力（yuheng-framework）

### Web 支持

| 能力 | 提供者 | 说明 |
|------|--------|------|
| 统一返回 | `CommonResult` | 成功/失败统一封装 |
| 统一异常 | `GlobalExceptionHandler` | 全局异常处理 |
| 跨域配置 | `CorsConfig` | CORS 支持 |
| 请求日志 | `ApiAccessLogFilter` | API 访问日志 |

### 安全框架

| 能力 | 提供者 | 说明 |
|------|--------|------|
| 认证 | `TokenAuthenticationFilter` | JWT Token 认证 |
| 授权 | `@PreAuthorize` | 基于注解的权限控制 |
| 密码加密 | `PasswordEncoder` | BCrypt 加密 |
| OAuth2 | `OAuth2Service` | OAuth2 集成 |

### 数据访问

| 能力 | 提供者 | 说明 |
|------|--------|------|
| BaseMapper | `BaseMapperX` | MyBatis Plus 增强 |
| 分页 | `PageResult` | 统一分页结果 |
| 乐观锁 | `@Version` | MyBatis Plus 乐观锁 |
| 逻辑删除 | `@TableLogic` | 软删除支持 |

### 缓存支持

| 能力 | 提供者 | 说明 |
|------|--------|------|
| Spring Cache | `@Cacheable` | 声明式缓存 |
| Redis | `RedisTemplate` | Redis 操作 |
| 分布式锁 | `RedissonClient` | Redisson 分布式锁 |

### 任务调度

| 能力 | 提供者 | 说明 |
|------|--------|------|
| 定时任务 | `@Scheduled` | Spring 定时任务 |
| Quartz | `QuartzJobBean` | Quartz 调度 |
| 异步任务 | `@Async` | 异步执行 |

### 消息队列

| 能力 | 提供者 | 说明 |
|------|--------|------|
| RabbitMQ | `RabbitTemplate` | RabbitMQ 集成 |
| Kafka | `KafkaTemplate` | Kafka 集成 |

### 多租户

| 能力 | 提供者 | 说明 |
|------|--------|------|
| 租户隔离 | `TenantContextHolder` | 租户上下文 |
| 租户拦截器 | `TenantLineHandler` | MyBatis Plus 租户插件 |

### 数据权限

| 能力 | 提供者 | 说明 |
|------|--------|------|
| 行级权限 | `DataPermissionInterceptor` | 数据权限拦截 |
| 部门权限 | `@DataScope` | 部门数据权限 |

### 监控

| 能力 | 提供者 | 说明 |
|------|--------|------|
| Metrics | `Micrometer` | 指标采集 |
| Trace | `SkyWalking` | 链路追踪 |
| 健康检查 | `/actuator/health` | Spring Boot Actuator |

---

## 系统模块（yuheng-module-system）

### 用户管理

| API | 说明 |
|-----|------|
| `/system/user/page` | 用户分页 |
| `/system/user/get` | 获取用户 |
| `/system/user/create` | 创建用户 |
| `/system/user/update` | 更新用户 |
| `/system/user/delete` | 删除用户 |

### 角色管理

| API | 说明 |
|-----|------|
| `/system/role/page` | 角色分页 |
| `/system/role/list-all-simple` | 精简角色列表 |
| `/system/role/create` | 创建角色 |
| `/system/role/update` | 更新角色 |
| `/system/role/delete` | 删除角色 |

### 菜单管理

| API | 说明 |
|-----|------|
| `/system/menu/list` | 菜单列表 |
| `/system/menu/get` | 获取菜单 |
| `/system/menu/create` | 创建菜单 |
| `/system/menu/update` | 更新菜单 |
| `/system/menu/delete` | 删除菜单 |

### 部门管理

| API | 说明 |
|-----|------|
| `/system/dept/list` | 部门列表 |
| `/system/dept/get` | 获取部门 |
| `/system/dept/create` | 创建部门 |
| `/system/dept/update` | 更新部门 |
| `/system/dept/delete` | 删除部门 |

### 字典管理

| API | 说明 |
|-----|------|
| `/system/dict-type/page` | 字典类型分页 |
| `/system/dict-data/list` | 字典数据列表 |

### 参数管理

| API | 说明 |
|-----|------|
| `/system/config/page` | 参数分页 |
| `/system/config/get-value-by-key` | 根据 key 获取值 |

---

## 基础设施模块（yuheng-module-infra）

### 文件管理

| API | 说明 |
|-----|------|
| `/infra/file/upload` | 文件上传 |
| `/infra/file/get/{id}` | 获取文件 |
| `/infra/file/delete` | 删除文件 |

### 代码生成

| API | 说明 |
|-----|------|
| `/infra/codegen/table/page` | 数据库表分页 |
| `/infra/codegen/create` | 生成代码 |
| `/infra/codegen/preview` | 预览代码 |

---

## 常用工具类

| 工具类 | 说明 |
|--------|------|
| `CollectionUtils` | 集合工具 |
| `DateUtils` | 日期工具 |
| `JsonUtils` | JSON 工具 |
| `NumberUtils` | 数字工具 |
| `StringUtils` | 字符串工具 |
| `ValidationUtils` | 校验工具 |

---

## 常用注解

| 注解 | 说明 |
|------|------|
| `@OperateLog` | 操作日志 |
| `@DataPermission` | 数据权限 |
| `@TenantIgnore` | 忽略租户 |
| `@ApiAccessLog` | API 访问日志 |

---

**版本**: 0.1.0-SNAPSHOT  
**更新时间**: 2026-11-09
