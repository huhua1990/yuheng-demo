# 代码搜索范围约束

开始任何代码搜索（grep、find、Explore agent、Read）之前，**必须先判定目标层级**，把搜索目录锁定到最小范围。

---

## 判定规则

| 目标 | 搜索根目录 |
|------|-----------|
| 后端 Java 代码（Service/Controller/Mapper/Entity/DTO/VO/配置/工具类） | `yuheng-module-*/src/main/java/` |
| 后端 Mapper XML | `yuheng-module-*/src/main/resources/mapper/` |
| 后端迁移 | 先确认目标模块真实迁移目录/数据库工具配置，再限制到该目录；core 聚合仓库可能不包含消费端迁移 |
| 后端测试 | `yuheng-module-*/src/test/java/` |
| 前端 Vue 页面/组件 | `yuheng-ui/src/` |
| 前端 API 封装 | 先定位 `yuheng-ui/src/modules/{system,infra}/api/`，消费端以其真实 API 目录为准 |
| 规则/Rules | canonical source `governance/rules/`; 按任务读取相关规则 |
| Knowledge | `ai-knowledge-core/` |

---

## 强制要求

1. **先判定，再搜索。** `grep` 的路径参数必须是精确目录，禁止从仓库根 `/` 或项目根目录开始全库扫描。

2. **后端就搜后端目录，前端就搜前端目录。** 除非用户明确要求"全库搜索"或问题明显跨前后端（如接口路径对应关系），否则不同时搜两端。

3. **一次只搜一个层级。** 先用最小范围搜索，不够再扩大，不要上来就用宽泛路径。

---

## 示例

```bash
# ✅ 后端：搜 Java 中的某个类
grep -rn 'UserService' --include="*.java" yuheng-module-system/src/main/java/

# ✅ 前端：搜 Vue 组件
grep -rn 'wg-table' --include="*.vue" yuheng-ui/src/

# ❌ 从仓库根搜索（会扫到 node_modules、target、.git 等）
grep -rn 'UserService' .
```

---

## 禁止事项

- 禁止从项目根目录全局搜索
- 禁止同时搜索前后端（除非明确需要）
- 禁止搜索 node_modules、target、.git 等目录

---

**规则版本**: v1.0  
**更新时间**: 2026-11-09
