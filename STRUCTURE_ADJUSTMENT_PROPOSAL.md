# Yuheng Demo 结构调整建议

## 当前状态

### 问题
完整的 template-member（185个文件）直接迁移到 yuheng-demo 会出现编译错误：
- MapStruct 映射问题
- VO 类不匹配
- 依赖关系复杂

### 原因
ruoyi-vue-pro 的 member 模块与其他模块（mall、pay等）高度耦合，直接迁移需要同时迁移大量依赖。

## 📋 解决方案

### 方案 1：保持 yuheng-demo 使用精简版（推荐）

**理由**：
- yuheng-demo 作为演示项目，重点是展示如何使用平台能力
- 简单清晰的代码更适合学习和参考
- 减少编译和维护成本

**行动**：
- ✅ yuheng-demo 保持使用精简版 member（11个文件）
- ✅ template-member 提供完整版（185个文件）供生产使用
- ✅ 文档中说明两者的区别和适用场景

### 方案 2：创建独立的生产示例项目

创建 `yuheng-production-example` 项目：
- 完整集成 template-member（185个文件）
- 展示生产级完整实现
- 包含所有依赖和配置

### 方案 3：逐步完善 yuheng-demo 的 member 模块

不直接拷贝，而是：
1. 保持基础 CRUD
2. 参考 template-member 逐步添加功能
3. 每个功能独立实现和测试

## 📊 建议采用方案 1

### yuheng-demo 定位
- **目的**：演示如何使用 yuheng-core
- **受众**：学习者、快速原型开发
- **复杂度**：适中，易于理解

### template-member 定位
- **目的**：提供生产级完整代码
- **受众**：正式项目开发
- **复杂度**：完整，功能齐全

### 两者关系
```
学习路径：
yuheng-demo (精简版 member) 
    ↓ 学习如何使用
    ↓ 理解架构设计
    ↓ 
template-member (完整版)
    ↓ 应用到生产项目
    ↓ 根据需求定制
    ↓
生产项目
```

## 📝 文档更新

### README.md 说明
```markdown
## yuheng-demo 的 member 模块

**版本**: 精简版（60%）
**目的**: 演示平台能力使用

### 功能清单
- ✅ 会员 CRUD
- ✅ 会员等级管理
- ✅ 数据库设计
- ✅ 前端基础页面

### 完整版本
如需生产级完整功能，请使用：
- template-member（185个文件，100%功能）
- 位置：yuheng-business-templates/template-member
```

## 结论

**建议**：
1. ✅ yuheng-demo 保持精简版 member
2. ✅ template-member 保持完整版（已完成）
3. ✅ 文档中清晰说明两者区别

这样既保持了 demo 的简洁性，又提供了完整的生产级模板。

---

**日期**: 2026-11-09  
**状态**: 建议中
