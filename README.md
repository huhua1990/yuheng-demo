# yuheng-demo

Yuheng 平台的**消费端示例项目**，展示如何基于 `yuheng-core` 构建实际业务应用。

## 项目定位

本项目不是简单的模板展示，而是完整的业务开发示例：

1. **平台能力复用** - 通过 Maven 依赖 `yuheng-server`，复用平台的用户、权限、文件、短信等服务
2. **业务模块开发** - 演示如何基于平台构建完整的业务模块（会员、工作流等）
3. **AI 驱动开发** - 支持 AI 辅助的快速业务开发流程
4. **最佳实践** - 提供代码组织、平台集成、前后端联调的最佳实践

## 快速开始

### 传统方式

```bash
# 1. 发布 yuheng-core 到本地 Maven 仓库
mvn -DskipTests install -f ../yuheng-core/pom.xml

# 2. 启动后端
mvn spring-boot:run

# 3. 启动前端
cd yuheng-demo-ui
pnpm install
pnpm run dev

# 4. 访问应用
# 前端: http://127.0.0.1:3000
# 后端API: http://127.0.0.1:48080/doc.html
# 默认账户: admin / admin123
```

### AI 驱动方式 🤖

使用 AI 快速添加业务模块：

```bash
# 1. 同步业务模板库
./scripts/sync-template.sh

# 2. 添加业务模块（AI 会自动完成拷贝、重命名、生成代码）
./scripts/add-module.sh member

# 或者直接与 AI 对话：
# "我想添加一个会员管理模块，包括会员注册、等级管理和积分系统"
```

AI 会自动：
- ✅ 从模板库拷贝起点代码
- ✅ 重命名包名和类名
- ✅ 生成完整的业务逻辑（集成平台服务）
- ✅ 生成数据库脚本
- ✅ 生成前端页面
- ✅ 更新配置文件

详见 [AI 驱动开发指南](../AI_DRIVEN_DEMO_DEVELOPMENT.md)

## 项目结构

```
yuheng-demo/
├── src/main/java/com/yuheng/
│   ├── platform/server/           # 启动类和默认控制器
│   └── demo/                      # 业务模块演示
│       ├── member/                # 会员管理（完整实现）
│       └── workflow/              # 工作流示例（可选）
│
├── src/main/resources/
│   ├── application.yml            # 应用配置
│   └── db/changelog/              # 数据库变更脚本
│       ├── member/
│       └── workflow/
│
├── yuheng-demo-ui/                # 前端代码
│   └── src/
│       ├── api/demo/              # 业务模块 API
│       └── views/                 # 业务页面
│
├── scripts/                       # 脚本工具
│   ├── add-module.sh             # 添加业务模块
│   └── sync-template.sh          # 同步模板库
│
├── .ai/                          # AI 配置
│   ├── config.yaml               # AI 行为配置
│   └── prompts/                  # AI 提示词库
│       ├── add-module.md
│       └── enhance-module.md
│
└── docs/                         # 开发文档
    └── how-to-add-business-module.md
```

## 业务模块开发

### 方式 1：使用脚本工具

```bash
# 添加新模块
./scripts/add-module.sh <module-name>

# 示例：添加会员管理模块
./scripts/add-module.sh member
```

### 方式 2：与 AI 对话

```
"我想添加一个会员管理模块，需要以下功能：
1. 会员注册（自动创建系统账号）
2. 会员等级管理（普通、银卡、金卡、VIP）
3. 积分系统（注册送积分、消费积分、积分兑换）
4. 注册时发送欢迎短信
5. 等级升级时发送通知短信"
```

AI 会理解需求并自动生成完整的业务代码。

### 方式 3：手动开发

参考文档：
- [业务模块架构设计](../BUSINESS_MODULES_ARCHITECTURE.md)
- [Demo 使用指南](../DEMO_USAGE_GUIDE.md)

## 平台能力

### System 模块（来自 yuheng-module-system）

- **AdminUserService** - 用户管理
- **RoleService** - 角色管理
- **PermissionService** - 权限管理
- **DeptService** - 部门管理
- **SmsService** - 短信服务
- **MailService** - 邮件服务
- **TenantService** - 租户管理
- **OAuth2Service** - OAuth2 认证

### Infra 模块（来自 yuheng-module-infra）

- **FileService** - 文件服务
- **CodegenService** - 代码生成
- **JobService** - 定时任务
- **ConfigService** - 配置管理

### Framework 能力

- `@OperateLog` - 操作日志注解
- `@PreAuthorize` - 权限控制注解
- `@TenantIgnore` - 租户忽略注解
- `CommonResult<T>` - 统一响应格式
- `PageResult<T>` - 分页响应
- `ServiceException` - 业务异常

## 与业务模板库的关系

- **yuheng-business-templates**: 业务模板库（https://github.com/huhua1990/yuheng-business-templates）
  - 提供起点代码和脚手架
  - 不是依赖库，是拷贝使用的模板

- **yuheng-demo**: 消费端示例
  - 从模板库拷贝代码
  - 实现完整的业务逻辑
  - 展示最佳实践

**工作流程**:
```
模板库 → 拷贝代码 → Demo 项目 → 完整实现 → 学习参考
```

## 配置说明

### 数据库配置

默认使用 `local` profile，配置在 `application-local.yaml`：

```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/yuheng-demo
    username: root
    password: your_password
```

数据库由 Liquibase 自动初始化，无需手动执行 SQL。

### Redis 配置

```yaml
spring:
  data:
    redis:
      host: localhost
      port: 6379
```

### 前端配置

前端配置在 `yuheng-demo-ui/.env.local`：

```env
# 后端 API 地址
VITE_BACKEND_ORIGIN=http://127.0.0.1:48080
```

## 常见问题

### Q: 如何添加新的业务模块？

**A:** 三种方式任选其一：
1. 使用脚本：`./scripts/add-module.sh member`
2. 与 AI 对话：描述需求，AI 自动生成
3. 手动开发：参考现有模块代码

### Q: 业务模板更新了，demo 需要同步吗？

**A:** 不需要。demo 拷贝后就独立了，模板更新不影响已有的 demo。

### Q: demo 中的代码可以直接用于生产吗？

**A:** 不建议直接使用。demo 是示例和最佳实践，生产环境需要根据实际需求定制。

### Q: 如何调试业务模块？

**A:**
1. 后端：在 IDE 中以 Debug 模式运行 `YuhengDemoApplication`
2. 前端：`pnpm run dev` 启动开发服务器
3. API 文档：http://localhost:48080/doc.html

## 开发文档

- [业务模块架构设计](../BUSINESS_MODULES_ARCHITECTURE.md) - 架构设计原则和实施方案
- [AI 驱动开发指南](../AI_DRIVEN_DEMO_DEVELOPMENT.md) - AI 辅助开发的完整流程
- [Demo 使用指南](../DEMO_USAGE_GUIDE.md) - Demo 项目的使用说明
- [迁移状态报告](../MIGRATION_STATUS.md) - 功能模块迁移情况

## 技术栈

- **后端**: Spring Boot 3.5.15 + MyBatis Plus + MySQL 8 + Redis
- **前端**: Vue 3 + TypeScript + Element Plus + Vite
- **构建**: Maven + pnpm
- **数据库迁移**: Liquibase
- **API 文档**: Swagger/OpenAPI

## 贡献指南

欢迎贡献新的业务模块示例！请确保：
1. 代码完整可运行
2. 遵循平台规范
3. 包含详细注释
4. 提供使用文档

## 许可证

[根据项目实际情况填写]
