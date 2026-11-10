# Yuheng Demo

## 项目说明

这是一个**空壳消费端项目**，用于演示如何使用 yuheng-core 平台和业务模板。

## 架构设计

```
yuheng-core              → 平台核心（稳定、版本化）
yuheng-business-templates → 业务模板库（按需选择）
yuheng-demo              → 空壳消费端（集成演示）
```

## 快速开始

### 1. 安装依赖

```bash
mvn clean install
```

### 2. 添加业务模块

使用 AI 驱动工具一键添加：

```bash
# 添加会员管理模块
./scripts/add-module.sh member

# 添加其他业务模块（待实现）
./scripts/add-module.sh bpm
./scripts/add-module.sh mall
./scripts/add-module.sh crm
```

### 3. 或者与 AI 对话

```
"我想添加一个会员管理模块，包括：
- 会员注册登录
- 会员等级系统
- 积分管理"
```

AI 会自动：
1. 从 yuheng-business-templates 拉取模板
2. 拷贝到项目中
3. 重命名包名
4. 生成完整业务代码
5. 集成平台服务

### 4. 运行项目

```bash
mvn spring-boot:run
```

## 目录结构

```
yuheng-demo/
├── src/main/java/com/yuheng/
│   ├── platform/           # 平台启动类
│   └── demo/               # 业务模块（动态添加）
│       └── [按需添加模块]
│
├── scripts/
│   ├── add-module.sh       # 添加模块脚本
│   └── sync-template.sh    # 同步模板脚本
│
├── .ai/
│   ├── config.yaml         # AI 配置
│   └── prompts/            # AI 提示词库
│
└── yuheng-demo-ui/         # 前端项目
```

## 可用的业务模板

从 [yuheng-business-templates](https://github.com/huhua1990/yuheng-business-templates) 选择：

| 模板 | 说明 | 完整度 | 文件数 |
|-----|------|-------|--------|
| **template-member** | 会员管理 | 100% | 217 |
| template-bpm | 工作流 | 待添加 | - |
| template-mall | 商城 | 待添加 | - |
| template-crm | CRM | 待添加 | - |

## AI 驱动开发

### 传统方式 vs AI 驱动

**传统方式**（2-3天）：
1. 手动创建文件结构
2. 手动编写 CRUD 代码
3. 手动编写前端页面
4. 手动配置集成

**AI 驱动**（30分钟）：
1. 描述需求
2. AI 自动完成

**效率提升**: 95%

### AI 配置文件

- `.ai/config.yaml` - AI 行为配置
- `.ai/prompts/add-module.md` - 添加模块提示词
- `.ai/prompts/enhance-module.md` - 增强模块提示词

## 核心依赖

```xml
<dependency>
    <groupId>com.yuheng</groupId>
    <artifactId>yuheng-server</artifactId>
    <version>0.1.0-SNAPSHOT</version>
</dependency>
```

yuheng-server 包含：
- 平台框架（framework）
- 系统模块（system）
- 基础设施（infra）

## 开发流程

1. **选择模板** - 从 yuheng-business-templates 选择需要的业务模板
2. **添加模块** - 使用脚本或 AI 添加到项目
3. **定制开发** - 根据业务需求完善功能
4. **集成服务** - 使用 yuheng-core 提供的平台服务
5. **测试验证** - 单元测试和集成测试
6. **部署上线** - 打包部署

## 注意事项

### 本项目不包含业务代码
- ❌ 不要在这里直接写业务逻辑
- ✅ 从模板库拉取业务模板
- ✅ 在拉取后的代码中开发

### 保持项目整洁
- 只保留平台启动类
- 业务模块按需添加
- 不需要的模块可以删除

## 示例项目

想看完整的实现示例？

1. **快速原型** - 使用本项目 + 模板库
2. **生产项目** - 参考 yuheng-production-example（待创建）
3. **学习参考** - 查看模板库中的 README

## 相关资源

- **yuheng-core**: [待补充]
- **yuheng-business-templates**: https://github.com/huhua1990/yuheng-business-templates
- **文档**: docs/ 目录

## 技术栈

- Java 17
- Spring Boot 3.5.15
- MyBatis Plus
- Vue 3 + TypeScript
- Element Plus

## 许可证

[待补充]

---

**版本**: v0.1.0  
**维护者**: Yuheng 团队  
**最后更新**: 2026-11-09
