# Yuheng Server 后端框架概览

## 框架定位

`yuheng-server` 是 Yuheng 平台的后端核心框架，提供企业级应用开发的基础能力。

---

## 核心能力

### 1. 基础框架能力（yuheng-framework）

- **Web 层**: REST API、统一异常处理、跨域、请求响应封装
- **Security**: 认证、授权、JWT、OAuth2
- **MyBatis**: BaseMapper、分页、代码生成
- **Redis**: 缓存、分布式锁、Session
- **Job**: 定时任务、异步任务（Quartz）
- **MQ**: 消息队列集成
- **租户**: 多租户支持
- **数据权限**: 行级数据权限
- **IP 管理**: IP 黑白名单
- **WebSocket**: 实时通信
- **监控**: Metrics、Trace
- **防护**: 限流、熔断
- **Excel**: 导入导出

### 2. 系统模块（yuheng-module-system）

- 用户管理
- 角色管理
- 菜单管理
- 部门管理
- 岗位管理
- 字典管理
- 参数管理
- 通知公告
- 操作日志
- 登录日志
- OAuth2 认证

### 3. 基础设施模块（yuheng-module-infra）

- 文件管理
- 代码生成
- 数据库文档
- API 文档
- 短信管理
- 邮件管理
- 配置管理

---

## 技术栈

- **Java**: 17
- **Spring Boot**: 3.5.15
- **MyBatis Plus**: 3.5.7
- **Redis**: Lettuce
- **数据库**: MySQL 8.0 / PostgreSQL / Oracle

---

## 包结构

```
com.yuheng.platform
├── framework/              # 框架层（17个starter）
│   ├── common/            # 通用组件
│   ├── web/               # Web支持
│   ├── security/          # 安全框架
│   ├── mybatis/           # MyBatis增强
│   ├── redis/             # Redis支持
│   └── ...
├── module/
│   ├── system/            # 系统模块
│   └── infra/             # 基础设施
└── server/                # 聚合入口
```

---

## Maven 依赖

```xml
<dependency>
    <groupId>com.yuheng</groupId>
    <artifactId>yuheng-server</artifactId>
    <version>0.1.0-SNAPSHOT</version>
</dependency>
```

---

## 快速开始

### 1. 创建项目

```bash
# 使用 yuheng-demo 模板
git clone yuheng-demo my-project
cd my-project
```

### 2. 配置数据库

```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/yuheng
    username: root
    password: password
```

### 3. 启动应用

```bash
mvn spring-boot:run
```

---

## 核心 API 使用

### Result 统一返回

```java
import com.yuheng.platform.framework.common.pojo.CommonResult;

@RestController
public class UserController {

    @PostMapping("/user/list")
    public CommonResult<List<User>> list() {
        return CommonResult.success(userService.list());
    }
}
```

### 分页查询

```java
import com.yuheng.platform.framework.common.pojo.PageResult;

public PageResult<User> pageList(PageParam pageParam) {
    Page<User> page = userMapper.selectPage(pageParam, null);
    return new PageResult<>(page.getRecords(), page.getTotal());
}
```

### 用户上下文

```java
import com.yuheng.platform.module.system.service.auth.AdminAuthService;

Long userId = SecurityFrameworkUtils.getLoginUserId();
AdminUserDO user = userService.getUser(userId);
```

---

## 扩展开发

### 1. 添加业务模块

从 `yuheng-business-templates` 选择模板：

```bash
./scripts/add-module.sh member
```

### 2. 自定义开发

- Controller: 统一 POST，返回 `CommonResult`
- Service: 继承 `ServiceImpl`
- Mapper: 继承 `BaseMapperX`

---

## 相关资源

- **源码**: https://github.com/huhua1990/yuheng-core
- **模板库**: https://github.com/huhua1990/yuheng-business-templates
- **示例项目**: yuheng-demo

---

**版本**: 0.1.0-SNAPSHOT
**更新时间**: 2026-11-09
