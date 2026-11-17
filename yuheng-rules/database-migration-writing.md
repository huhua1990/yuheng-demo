# 数据库迁移编写规则

适用范围：目标工程已确认使用 Liquibase，且新增或修改 changeset / SQL 迁移文件时。开始前按 `database-migration.md` 核实依赖、启动配置、changelog 和真实路径。

---

## 强制规则

### 1. 先确认目标数据库类型

- 当前支持 `mysql`
- 业务项目如只支持单一数据库，必须在规格或交付说明中明确边界

### 2. changeset 必须使用内联 sql 格式

- 使用 `sql:` 直接嵌入 SQL 内容，不要使用 `sqlFile` 引用外部文件
- 涉及存储过程、函数、复杂分隔符时，必须设置 `splitStatements: false`
- 默认保留注释，优先设置 `stripComments: false`

### 3. SQL 文件头部必须说明版本、日期、目的、目标数据库

### 4. DDL 必须可读、可审查，不要把多类动作混在一起

### 5. 建表时优先一次性补齐主键、唯一约束、必要索引和注释

### 6. 涉及删除、重命名、批量更新时，必须显式写出风险和回滚方案

### 7. 物理表名必须使用小写 `snake_case`；同一逻辑表跨版本、跨数据库脚本必须保持同一个小写表名

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
                  id BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
                  order_no VARCHAR(32) NOT NULL COMMENT '订单号',
                  order_status VARCHAR(20) NOT NULL COMMENT '订单状态',
                  creator VARCHAR(64) NOT NULL COMMENT '创建者',
                  create_time DATETIME NOT NULL COMMENT '创建时间',
                  updater VARCHAR(64) NOT NULL COMMENT '更新者',
                  update_time DATETIME NOT NULL COMMENT '更新时间',
                  deleted BIT DEFAULT 0 NOT NULL COMMENT '是否删除'
              ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单表';
              
              CREATE INDEX idx_order_no ON biz_order(order_no);
            splitStatements: true
            stripComments: false
      rollback:
        - sql: "DROP TABLE IF EXISTS biz_order"
```

---

## DDL 编写要求

```sql
CREATE TABLE biz_order (
    id BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    order_no VARCHAR(32) NOT NULL COMMENT '订单号',
    order_status VARCHAR(20) NOT NULL COMMENT '订单状态',
    creator VARCHAR(64) NOT NULL COMMENT '创建者',
    create_time DATETIME NOT NULL COMMENT '创建时间',
    updater VARCHAR(64) NOT NULL COMMENT '更新者',
    update_time DATETIME NOT NULL COMMENT '更新时间',
    deleted BIT DEFAULT 0 NOT NULL COMMENT '是否删除'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单表';

CREATE INDEX idx_order_no ON biz_order(order_no);
```

补充要求：

- MySQL 使用 MySQL 方言
- 字段命名遵循数据库命名规范
- 物理表名使用小写 `snake_case`
- 审计字段使用 `creator`、`create_time`、`updater`、`update_time`
- 软删除字段使用 `deleted`

---

## 回滚要求

- 不是所有脚本都必须提供 rollback
- 但涉及高风险数据修复、删字段、删表、批量更新，就必须在 changeset rollback 中给出明确回滚方案

---

## 禁止写法

- 用非标准命名，例如 `v1_init.sql`
- 一个脚本同时建表、灌数、修历史坏数据、改权限
- 没有注释，导致评审看不出业务目的
- 直接改基础表结构
- 只新增 SQL 文件却不注册到 Liquibase changeset / 主 changelog
- 同一张逻辑表在不同版本迁移脚本中混用 `biz_order`、`BIZ_ORDER`、`Biz_Order`

---

## AI 检查清单

- 文件名是否符合 `V{版本号}__{描述}.sql`
- changeset 文件是否符合 `V{版本号}-{描述}.yaml`
- changeset 是否已被主 changelog include
- DDL 是否缺主键、唯一约束、索引、注释
- 是否存在高风险动作却没有回滚方案
- 物理表名是否全程小写，且跨版本大小写一致

---

**规则版本**: v1.0  
**更新时间**: 2026-11-09
