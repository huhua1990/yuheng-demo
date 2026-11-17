# 数据库迁移规则

本规则中 Liquibase 命名和结构要求仅适用于已确认使用 Liquibase 的工程。开始前先查目标模块的实际依赖、启动配置、changelog 与执行入口；本规则本身不证明 Yuheng core 或任一消费端已接入 Liquibase。若目标工程使用其他已批准迁移方案，按其真实工具与兼容契约制定计划，不为套用模板擅自引入依赖或假定目录。

先检查目标工程的真实依赖、启动配置和迁移目录。以下是已接入 Liquibase 工程的交付约束；路径仅为推荐结构，实际以配置为准。未接入迁移工具时先在规格/计划中明确接入方案，不能假定本仓库已有 changelog 或可运行的 Liquibase 命令。

## 强制规则

1. 只有目标工程已核实接入 Liquibase 时，才通过其注册迁移脚本交付数据库变更；否则先按真实已批准工具制定规格和计划。不得口头替代迁移记录或绕过已配置的迁移流程直接改共享数据库。
2. 迁移文件命名：changeset YAML `V{版本号}-{描述}.yaml`，SQL `V{版本号}__{描述}.sql`，版本号严格递增
3. 文件放在标准目录：
   - 主 changelog：`src/main/resources/db/changelog/db.changelog-master.yaml`
   - changeset：`src/main/resources/db/changelog/changes/`
   - SQL：`src/main/resources/db/migration/`
4. 业务表使用小写业务前缀（`biz_`），禁止修改 `system_`/`infra_` 基础表
5. 一个 changeset 只做一类变更（建表/加列/建索引/初始化数据分开）
6. 提交前确认：版本号递增、changeset 被主 changelog include、使用外部 SQL 时路径真实存在、表注释/索引/约束已补齐；内联 SQL 不额外创建重复 SQL 文件。

---

## 新增 changeset YAML 强制规则

### A. 用 `sql:` 内联，禁止 `sqlFile`

```yaml
# ✅ 内联 sql
changes:
  - sql:
      sql: |
        CREATE TABLE ...
      splitStatements: true
      stripComments: false
```

### B. DDL 必须加 `preConditions` 防止重复执行

```yaml
preConditions:
  - onFail: HALT
  - onError: HALT
  - not:
      tableExists:
        tableName: biz_order
```

### C. 禁止紧凑格式

为保持 YAML 可读和结构检查一致，`changes:` 与列表项换行；不把此格式约束解释为未经核实的版本限制。

---

## 推荐 changeset 模板

```yaml
databaseChangeLog:
  - changeSet:
      id: V1.0.1-create-order-table
      author: yuheng
      preConditions:
        - onFail: HALT
        - onError: HALT
        - not:
            tableExists:
              tableName: biz_order
      changes:
        - sql:
            sql: |
              CREATE TABLE biz_order (
                  id BIGINT NOT NULL PRIMARY KEY,
                  order_no VARCHAR(32) NOT NULL,
                  order_status VARCHAR(20) NOT NULL,
                  creator VARCHAR(64) NOT NULL,
                  create_time DATETIME NOT NULL,
                  updater VARCHAR(64) NOT NULL,
                  update_time DATETIME NOT NULL,
                  deleted BIT DEFAULT 0 NOT NULL
              ) COMMENT='订单表';
              
              CREATE INDEX idx_order_no ON biz_order(order_no);
            splitStatements: true
            stripComments: false
      rollback:
        - sql: "DROP TABLE IF EXISTS biz_order"
```

---

## 禁止写法

- 用非标准命名
- 一个脚本同时建表、灌数、修历史坏数据
- 没有注释
- 直接改基础表结构
- 只新增 SQL 文件却不注册到 changeset
- 表名使用大写或大小写混合

---

**规则版本**: v1.0  
**更新时间**: 2026-11-09
