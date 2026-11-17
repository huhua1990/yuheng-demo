--liquibase formatted sql

-- Yuheng business template database migration
-- Source: current template Java data objects; public ruoyi-spring-boot-all ERP DDL at commit 0f3548c74766cb1eb83efdfdfb890935a0da6f55 used for cross-check
-- Purpose: create business-owned tables for a new consumer schema.
-- Target database: MySQL 8.0+
-- Generated from the current Java data objects and Mapper/service usage; public SQL was used only as a cross-check.
-- No sample business rows, credentials, platform tables, Flowable tables, or Quartz tables are included.

--changeset yuheng-template-erp:erp-schema-001 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_account'
CREATE TABLE `erp_account` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '结算账户编号',
  `name` varchar(255) NOT NULL COMMENT '账户名称',
  `no` varchar(50) NULL DEFAULT NULL COMMENT '账户编码',
  `remark` varchar(255) NULL DEFAULT NULL COMMENT '备注',
  `status` tinyint NOT NULL COMMENT '开启状态',
  `sort` int NOT NULL COMMENT '排序',
  `default_status` bit(1) NULL DEFAULT b'0' COMMENT '是否默认',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_no` (`no`),
  KEY `idx_tenant_status` (`tenant_id`,`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 结算账户';

--changeset yuheng-template-erp:erp-schema-002 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_customer'
CREATE TABLE `erp_customer` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '客户编号',
  `name` varchar(255) NOT NULL COMMENT '客户名称',
  `contact` varchar(100) NULL DEFAULT NULL COMMENT '联系人',
  `mobile` varchar(30) NULL DEFAULT NULL COMMENT '手机号码',
  `telephone` varchar(30) NULL DEFAULT NULL COMMENT '联系电话',
  `email` varchar(50) NULL DEFAULT NULL COMMENT '电子邮箱',
  `fax` varchar(30) NULL DEFAULT NULL COMMENT '传真',
  `remark` varchar(255) NULL DEFAULT NULL COMMENT '备注',
  `status` tinyint NOT NULL COMMENT '开启状态',
  `sort` int NOT NULL COMMENT '排序',
  `tax_no` varchar(50) NULL DEFAULT NULL COMMENT '纳税人识别号',
  `tax_percent` decimal(24, 6) NULL DEFAULT NULL COMMENT '税率',
  `bank_name` varchar(50) NULL DEFAULT NULL COMMENT '开户行',
  `bank_account` varchar(50) NULL DEFAULT NULL COMMENT '开户账号',
  `bank_address` varchar(50) NULL DEFAULT NULL COMMENT '开户地址',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_status` (`tenant_id`,`status`),
  KEY `idx_mobile` (`mobile`),
  KEY `idx_telephone` (`telephone`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 客户表';

--changeset yuheng-template-erp:erp-schema-003 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_finance_payment'
CREATE TABLE `erp_finance_payment` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `no` varchar(255) NOT NULL COMMENT '付款单号',
  `status` tinyint NOT NULL COMMENT '状态',
  `payment_time` datetime NOT NULL COMMENT '付款时间',
  `finance_user_id` bigint NULL DEFAULT NULL COMMENT '财务人员编号',
  `supplier_id` bigint NOT NULL COMMENT '供应商编号',
  `account_id` bigint NOT NULL COMMENT '付款账户编号',
  `total_price` decimal(24, 6) NOT NULL COMMENT '合计价格，单位：元',
  `discount_price` decimal(24, 6) NOT NULL COMMENT '优惠金额，单位：元',
  `payment_price` decimal(24, 6) NOT NULL COMMENT '实付金额，单位：分',
  `remark` varchar(1024) NULL DEFAULT NULL COMMENT '备注',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_no` (`no`),
  KEY `idx_supplier_id` (`supplier_id`),
  KEY `idx_account_id` (`account_id`),
  KEY `idx_tenant_status_time` (`tenant_id`,`status`,`payment_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 付款单表';

--changeset yuheng-template-erp:erp-schema-004 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_finance_payment_item'
CREATE TABLE `erp_finance_payment_item` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `payment_id` bigint NOT NULL COMMENT '付款单编号',
  `biz_type` tinyint NOT NULL COMMENT '业务类型',
  `biz_id` bigint NOT NULL COMMENT '业务编号',
  `biz_no` varchar(255) NOT NULL COMMENT '业务单号',
  `total_price` decimal(24, 6) NOT NULL COMMENT '应付欠款，单位：分',
  `paid_price` decimal(24, 6) NOT NULL COMMENT '已付欠款，单位：分',
  `payment_price` decimal(24, 6) NOT NULL COMMENT '本次付款，单位：分',
  `remark` varchar(1024) NULL DEFAULT NULL COMMENT '备注',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_payment_id` (`payment_id`),
  KEY `idx_biz_type_id` (`biz_type`,`biz_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 付款项表';

--changeset yuheng-template-erp:erp-schema-005 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_finance_receipt'
CREATE TABLE `erp_finance_receipt` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `no` varchar(255) NOT NULL COMMENT '收款单号',
  `status` tinyint NOT NULL COMMENT '状态',
  `receipt_time` datetime NOT NULL COMMENT '收款时间',
  `finance_user_id` bigint NULL DEFAULT NULL COMMENT '财务人员编号',
  `customer_id` bigint NOT NULL COMMENT '客户编号',
  `account_id` bigint NOT NULL COMMENT '收款账户编号',
  `total_price` decimal(24, 6) NOT NULL COMMENT '合计价格，单位：元',
  `discount_price` decimal(24, 6) NOT NULL COMMENT '优惠金额，单位：元',
  `receipt_price` decimal(24, 6) NOT NULL COMMENT '实收金额，单位：分',
  `remark` varchar(1024) NULL DEFAULT NULL COMMENT '备注',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_no` (`no`),
  KEY `idx_customer_id` (`customer_id`),
  KEY `idx_account_id` (`account_id`),
  KEY `idx_tenant_status_time` (`tenant_id`,`status`,`receipt_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 收款单表';

--changeset yuheng-template-erp:erp-schema-006 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_finance_receipt_item'
CREATE TABLE `erp_finance_receipt_item` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `receipt_id` bigint NOT NULL COMMENT '收款单编号',
  `biz_type` tinyint NOT NULL COMMENT '业务类型',
  `biz_id` bigint NOT NULL COMMENT '业务编号',
  `biz_no` varchar(255) NOT NULL COMMENT '业务单号',
  `total_price` decimal(24, 6) NOT NULL COMMENT '应收金额，单位：分',
  `receipted_price` decimal(24, 6) NOT NULL COMMENT '已收金额，单位：分',
  `receipt_price` decimal(24, 6) NOT NULL COMMENT '本次收款，单位：分',
  `remark` varchar(1024) NULL DEFAULT NULL COMMENT '备注',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_receipt_id` (`receipt_id`),
  KEY `idx_biz_type_id` (`biz_type`,`biz_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 收款项表';

--changeset yuheng-template-erp:erp-schema-007 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_product'
CREATE TABLE `erp_product` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '产品编号',
  `name` varchar(100) NOT NULL COMMENT '产品名称',
  `bar_code` varchar(50) NOT NULL COMMENT '产品条码',
  `category_id` bigint NOT NULL COMMENT '产品分类编号',
  `unit_id` int NOT NULL COMMENT '单位编号',
  `status` tinyint NOT NULL COMMENT '产品状态',
  `standard` varchar(100) NULL DEFAULT NULL COMMENT '产品规格',
  `remark` varchar(500) NULL DEFAULT NULL COMMENT '产品备注',
  `expiry_day` int NULL DEFAULT NULL COMMENT '保质期天数',
  `weight` decimal(24, 6) NULL DEFAULT NULL COMMENT '基础重量（kg）',
  `purchase_price` decimal(24, 6) NULL DEFAULT NULL COMMENT '采购价格，单位：元',
  `sale_price` decimal(24, 6) NULL DEFAULT NULL COMMENT '销售价格，单位：元',
  `min_price` decimal(24, 6) NULL DEFAULT NULL COMMENT '最低价格，单位：元',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_category_id` (`category_id`),
  KEY `idx_unit_id` (`unit_id`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 产品表';

--changeset yuheng-template-erp:erp-schema-008 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_product_category'
CREATE TABLE `erp_product_category` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '分类编号',
  `parent_id` bigint NOT NULL COMMENT '父分类编号',
  `name` varchar(255) NOT NULL COMMENT '分类名称',
  `code` varchar(100) NOT NULL COMMENT '分类编码',
  `sort` int NULL DEFAULT 0 COMMENT '分类排序',
  `status` tinyint NOT NULL COMMENT '开启状态',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_parent_id` (`parent_id`),
  KEY `idx_tenant_status` (`tenant_id`,`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 产品分类';

--changeset yuheng-template-erp:erp-schema-009 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_product_unit'
CREATE TABLE `erp_product_unit` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '单位编号',
  `name` varchar(50) NOT NULL COMMENT '单位名字',
  `status` tinyint NOT NULL COMMENT '单位状态',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_status` (`tenant_id`,`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 产品单位表';

--changeset yuheng-template-erp:erp-schema-010 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_purchase_in'
CREATE TABLE `erp_purchase_in` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `no` varchar(255) NOT NULL COMMENT '采购入库编号',
  `status` tinyint NOT NULL COMMENT '采购状态',
  `supplier_id` bigint NOT NULL COMMENT '供应商编号',
  `account_id` bigint NOT NULL COMMENT '结算账户编号',
  `in_time` datetime NOT NULL COMMENT '入库时间',
  `order_id` bigint NOT NULL COMMENT '采购订单编号',
  `order_no` varchar(255) NOT NULL COMMENT '采购订单号',
  `total_count` decimal(24, 6) NOT NULL COMMENT '合计数量',
  `total_price` decimal(24, 6) NOT NULL COMMENT '合计价格，单位：元',
  `payment_price` decimal(24, 6) NOT NULL DEFAULT 0.000000 COMMENT '已付款金额，单位：元',
  `total_product_price` decimal(24, 6) NOT NULL COMMENT '合计产品价格，单位：元',
  `total_tax_price` decimal(24, 6) NOT NULL COMMENT '合计税额，单位：元',
  `discount_percent` decimal(24, 6) NOT NULL COMMENT '优惠率，百分比',
  `discount_price` decimal(24, 6) NOT NULL COMMENT '优惠金额，单位：元',
  `other_price` decimal(24, 6) NOT NULL DEFAULT 0.000000 COMMENT '其它金额，单位：元',
  `file_url` varchar(512) NULL DEFAULT NULL COMMENT '附件地址',
  `remark` varchar(1024) NULL DEFAULT NULL COMMENT '备注',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_no` (`no`),
  KEY `idx_supplier_id` (`supplier_id`),
  KEY `idx_account_id` (`account_id`),
  KEY `idx_order_id` (`order_id`),
  KEY `idx_tenant_status_time` (`tenant_id`,`status`,`in_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 采购入库表';

--changeset yuheng-template-erp:erp-schema-011 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_purchase_in_items'
CREATE TABLE `erp_purchase_in_items` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `in_id` bigint NOT NULL COMMENT '采购入库编号',
  `order_item_id` bigint NOT NULL COMMENT '采购订单项编号',
  `warehouse_id` bigint NOT NULL COMMENT '仓库编号',
  `product_id` bigint NOT NULL COMMENT '产品编号',
  `product_unit_id` bigint NOT NULL COMMENT '产品单位单位',
  `product_price` decimal(24, 6) NOT NULL COMMENT '产品单价',
  `count` decimal(24, 6) NOT NULL COMMENT '数量',
  `total_price` decimal(24, 6) NOT NULL COMMENT '总价',
  `tax_percent` decimal(24, 6) NULL DEFAULT NULL COMMENT '税率，百分比',
  `tax_price` decimal(24, 6) NULL DEFAULT NULL COMMENT '税额，单位：元',
  `remark` varchar(1024) NULL DEFAULT NULL COMMENT '备注',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_in_id` (`in_id`),
  KEY `idx_order_item_id` (`order_item_id`),
  KEY `idx_warehouse_product` (`warehouse_id`,`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 销售入库项表';

--changeset yuheng-template-erp:erp-schema-012 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_purchase_order'
CREATE TABLE `erp_purchase_order` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `no` varchar(255) NOT NULL COMMENT '采购单编号',
  `status` tinyint NOT NULL COMMENT '采购状态',
  `supplier_id` bigint NOT NULL COMMENT '供应商编号',
  `account_id` bigint NULL DEFAULT NULL COMMENT '结算账户编号',
  `order_time` datetime NOT NULL COMMENT '采购时间',
  `total_count` decimal(24, 6) NOT NULL COMMENT '合计数量',
  `total_price` decimal(24, 6) NOT NULL COMMENT '合计价格，单位：元',
  `total_product_price` decimal(24, 6) NOT NULL COMMENT '合计产品价格，单位：元',
  `total_tax_price` decimal(24, 6) NOT NULL COMMENT '合计税额，单位：元',
  `discount_percent` decimal(24, 6) NOT NULL COMMENT '优惠率，百分比',
  `discount_price` decimal(24, 6) NOT NULL COMMENT '优惠金额，单位：元',
  `deposit_price` decimal(24, 6) NOT NULL DEFAULT 0.000000 COMMENT '定金金额，单位：元',
  `file_url` varchar(512) NULL DEFAULT NULL COMMENT '附件地址',
  `remark` varchar(1024) NULL DEFAULT NULL COMMENT '备注',
  `in_count` decimal(24, 6) NOT NULL DEFAULT 0.000000 COMMENT '采购入库数量',
  `return_count` decimal(24, 6) NOT NULL DEFAULT 0.000000 COMMENT '采购退货数量',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_no` (`no`),
  KEY `idx_supplier_id` (`supplier_id`),
  KEY `idx_account_id` (`account_id`),
  KEY `idx_tenant_status_time` (`tenant_id`,`status`,`order_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 采购订单表';

--changeset yuheng-template-erp:erp-schema-013 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_purchase_order_items'
CREATE TABLE `erp_purchase_order_items` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `order_id` bigint NOT NULL COMMENT '采购订单编号',
  `product_id` bigint NOT NULL COMMENT '产品编号',
  `product_unit_id` bigint NOT NULL COMMENT '产品单位单位',
  `product_price` decimal(24, 6) NOT NULL COMMENT '产品单价',
  `count` decimal(24, 6) NOT NULL COMMENT '数量',
  `total_price` decimal(24, 6) NOT NULL COMMENT '总价',
  `tax_percent` decimal(24, 6) NULL DEFAULT NULL COMMENT '税率，百分比',
  `tax_price` decimal(24, 6) NULL DEFAULT NULL COMMENT '税额，单位：元',
  `remark` varchar(1024) NULL DEFAULT NULL COMMENT '备注',
  `in_count` decimal(24, 6) NOT NULL DEFAULT 0.000000 COMMENT '采购入库数量',
  `return_count` decimal(24, 6) NOT NULL DEFAULT 0.000000 COMMENT '采购退货数量',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_order_id` (`order_id`),
  KEY `idx_product_id` (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 采购订单项表';

--changeset yuheng-template-erp:erp-schema-014 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_purchase_return'
CREATE TABLE `erp_purchase_return` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `no` varchar(255) NOT NULL COMMENT '采购退货编号',
  `status` tinyint NOT NULL COMMENT '退货状态',
  `supplier_id` bigint NOT NULL COMMENT '供应商编号',
  `account_id` bigint NOT NULL COMMENT '结算账户编号',
  `return_time` datetime NOT NULL COMMENT '退货时间',
  `order_id` bigint NOT NULL COMMENT '采购订单编号',
  `order_no` varchar(255) NOT NULL COMMENT '采购订单号',
  `total_count` decimal(24, 6) NOT NULL COMMENT '合计数量',
  `total_price` decimal(24, 6) NOT NULL COMMENT '合计价格，单位：元',
  `refund_price` decimal(24, 6) NOT NULL DEFAULT 0.000000 COMMENT '已退款金额，单位：元',
  `total_product_price` decimal(24, 6) NOT NULL COMMENT '合计产品价格，单位：元',
  `total_tax_price` decimal(24, 6) NOT NULL COMMENT '合计税额，单位：元',
  `discount_percent` decimal(24, 6) NOT NULL COMMENT '优惠率，百分比',
  `discount_price` decimal(24, 6) NOT NULL COMMENT '优惠金额，单位：元',
  `other_price` decimal(24, 6) NOT NULL DEFAULT 0.000000 COMMENT '其它金额，单位：元',
  `file_url` varchar(512) NULL DEFAULT NULL COMMENT '附件地址',
  `remark` varchar(1024) NULL DEFAULT NULL COMMENT '备注',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_no` (`no`),
  KEY `idx_supplier_id` (`supplier_id`),
  KEY `idx_account_id` (`account_id`),
  KEY `idx_order_id` (`order_id`),
  KEY `idx_tenant_status_time` (`tenant_id`,`status`,`return_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 采购退货表';

--changeset yuheng-template-erp:erp-schema-015 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_purchase_return_items'
CREATE TABLE `erp_purchase_return_items` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `return_id` bigint NOT NULL COMMENT '采购退货编号',
  `order_item_id` bigint NOT NULL COMMENT '采购订单项编号',
  `warehouse_id` bigint NOT NULL COMMENT '仓库编号',
  `product_id` bigint NOT NULL COMMENT '产品编号',
  `product_unit_id` bigint NOT NULL COMMENT '产品单位单位',
  `product_price` decimal(24, 6) NOT NULL COMMENT '产品单价',
  `count` decimal(24, 6) NOT NULL COMMENT '数量',
  `total_price` decimal(24, 6) NOT NULL COMMENT '总价',
  `tax_percent` decimal(24, 6) NULL DEFAULT NULL COMMENT '税率，百分比',
  `tax_price` decimal(24, 6) NULL DEFAULT NULL COMMENT '税额，单位：元',
  `remark` varchar(1024) NULL DEFAULT NULL COMMENT '备注',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_return_id` (`return_id`),
  KEY `idx_order_item_id` (`order_item_id`),
  KEY `idx_warehouse_product` (`warehouse_id`,`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 采购退货项表';

--changeset yuheng-template-erp:erp-schema-016 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_sale_order'
CREATE TABLE `erp_sale_order` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `no` varchar(255) NOT NULL COMMENT '销售单编号',
  `status` tinyint NOT NULL COMMENT '销售状态',
  `customer_id` bigint NOT NULL COMMENT '客户编号',
  `account_id` bigint NULL DEFAULT NULL COMMENT '结算账户编号',
  `sale_user_id` bigint NULL DEFAULT NULL COMMENT '销售用户编号',
  `order_time` datetime NOT NULL COMMENT '下单时间',
  `total_count` decimal(24, 6) NOT NULL COMMENT '合计数量',
  `total_price` decimal(24, 6) NOT NULL COMMENT '合计价格，单位：元',
  `total_product_price` decimal(24, 6) NOT NULL COMMENT '合计产品价格，单位：元',
  `total_tax_price` decimal(24, 6) NOT NULL COMMENT '合计税额，单位：元',
  `discount_percent` decimal(24, 6) NOT NULL COMMENT '优惠率，百分比',
  `discount_price` decimal(24, 6) NOT NULL COMMENT '优惠金额，单位：元',
  `deposit_price` decimal(24, 6) NOT NULL DEFAULT 0.000000 COMMENT '定金金额，单位：元',
  `file_url` varchar(512) NULL DEFAULT NULL COMMENT '附件地址',
  `remark` varchar(1024) NULL DEFAULT NULL COMMENT '备注',
  `out_count` decimal(24, 6) NOT NULL DEFAULT 0.000000 COMMENT '销售出库数量',
  `return_count` decimal(24, 6) NOT NULL DEFAULT 0.000000 COMMENT '销售退货数量',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_no` (`no`),
  KEY `idx_customer_id` (`customer_id`),
  KEY `idx_account_id` (`account_id`),
  KEY `idx_sale_user_id` (`sale_user_id`),
  KEY `idx_tenant_status_time` (`tenant_id`,`status`,`order_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 销售订单表';

--changeset yuheng-template-erp:erp-schema-017 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_sale_order_items'
CREATE TABLE `erp_sale_order_items` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `order_id` bigint NOT NULL COMMENT '销售订单编号',
  `product_id` bigint NOT NULL COMMENT '产品编号',
  `product_unit_id` bigint NOT NULL COMMENT '产品单位单位',
  `product_price` decimal(24, 6) NOT NULL COMMENT '产品单价',
  `count` decimal(24, 6) NOT NULL COMMENT '数量',
  `total_price` decimal(24, 6) NOT NULL COMMENT '总价',
  `tax_percent` decimal(24, 6) NULL DEFAULT NULL COMMENT '税率，百分比',
  `tax_price` decimal(24, 6) NULL DEFAULT NULL COMMENT '税额，单位：元',
  `remark` varchar(1024) NULL DEFAULT NULL COMMENT '备注',
  `out_count` decimal(24, 6) NOT NULL DEFAULT 0.000000 COMMENT '销售出库数量',
  `return_count` decimal(24, 6) NOT NULL DEFAULT 0.000000 COMMENT '销售退货数量',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_order_id` (`order_id`),
  KEY `idx_product_id` (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 销售订单项表';

--changeset yuheng-template-erp:erp-schema-018 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_sale_out'
CREATE TABLE `erp_sale_out` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `no` varchar(255) NOT NULL COMMENT '销售出库编号',
  `status` tinyint NOT NULL COMMENT '出库状态',
  `customer_id` bigint NOT NULL COMMENT '客户编号',
  `account_id` bigint NOT NULL COMMENT '结算账户编号',
  `sale_user_id` bigint NULL DEFAULT NULL COMMENT '销售用户编号',
  `out_time` datetime NOT NULL COMMENT '出库时间',
  `order_id` bigint NOT NULL COMMENT '销售订单编号',
  `order_no` varchar(255) NOT NULL COMMENT '销售订单号',
  `total_count` decimal(24, 6) NOT NULL COMMENT '合计数量',
  `total_price` decimal(24, 6) NOT NULL COMMENT '合计价格，单位：元',
  `receipt_price` decimal(24, 6) NOT NULL DEFAULT 0.000000 COMMENT '已收款金额，单位：元',
  `total_product_price` decimal(24, 6) NOT NULL COMMENT '合计产品价格，单位：元',
  `total_tax_price` decimal(24, 6) NOT NULL COMMENT '合计税额，单位：元',
  `discount_percent` decimal(24, 6) NOT NULL COMMENT '优惠率，百分比',
  `discount_price` decimal(24, 6) NOT NULL COMMENT '优惠金额，单位：元',
  `other_price` decimal(24, 6) NOT NULL DEFAULT 0.000000 COMMENT '其它金额，单位：元',
  `file_url` varchar(512) NULL DEFAULT NULL COMMENT '附件地址',
  `remark` varchar(1024) NULL DEFAULT NULL COMMENT '备注',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_no` (`no`),
  KEY `idx_customer_id` (`customer_id`),
  KEY `idx_account_id` (`account_id`),
  KEY `idx_order_id` (`order_id`),
  KEY `idx_tenant_status_time` (`tenant_id`,`status`,`out_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 销售出库表';

--changeset yuheng-template-erp:erp-schema-019 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_sale_out_items'
CREATE TABLE `erp_sale_out_items` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `out_id` bigint NOT NULL COMMENT '销售出库编号',
  `order_item_id` bigint NOT NULL COMMENT '销售订单项编号',
  `warehouse_id` bigint NOT NULL COMMENT '仓库编号',
  `product_id` bigint NOT NULL COMMENT '产品编号',
  `product_unit_id` bigint NOT NULL COMMENT '产品单位单位',
  `product_price` decimal(24, 6) NOT NULL COMMENT '产品单价',
  `count` decimal(24, 6) NOT NULL COMMENT '数量',
  `total_price` decimal(24, 6) NOT NULL COMMENT '总价',
  `tax_percent` decimal(24, 6) NULL DEFAULT NULL COMMENT '税率，百分比',
  `tax_price` decimal(24, 6) NULL DEFAULT NULL COMMENT '税额，单位：元',
  `remark` varchar(1024) NULL DEFAULT NULL COMMENT '备注',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_out_id` (`out_id`),
  KEY `idx_order_item_id` (`order_item_id`),
  KEY `idx_warehouse_product` (`warehouse_id`,`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 销售出库项表';

--changeset yuheng-template-erp:erp-schema-020 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_sale_return'
CREATE TABLE `erp_sale_return` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `no` varchar(255) NOT NULL COMMENT '销售退货编号',
  `status` tinyint NOT NULL COMMENT '退货状态',
  `customer_id` bigint NOT NULL COMMENT '客户编号',
  `account_id` bigint NOT NULL COMMENT '结算账户编号',
  `sale_user_id` bigint NULL DEFAULT NULL COMMENT '销售用户编号',
  `return_time` datetime NOT NULL COMMENT '退货时间',
  `order_id` bigint NOT NULL COMMENT '销售订单编号',
  `order_no` varchar(255) NOT NULL COMMENT '销售订单号',
  `total_count` decimal(24, 6) NOT NULL COMMENT '合计数量',
  `total_price` decimal(24, 6) NOT NULL COMMENT '合计价格，单位：元',
  `refund_price` decimal(24, 6) NOT NULL DEFAULT 0.000000 COMMENT '已退款金额，单位：元',
  `total_product_price` decimal(24, 6) NOT NULL COMMENT '合计产品价格，单位：元',
  `total_tax_price` decimal(24, 6) NOT NULL COMMENT '合计税额，单位：元',
  `discount_percent` decimal(24, 6) NOT NULL COMMENT '优惠率，百分比',
  `discount_price` decimal(24, 6) NOT NULL COMMENT '优惠金额，单位：元',
  `other_price` decimal(24, 6) NOT NULL DEFAULT 0.000000 COMMENT '其它金额，单位：元',
  `file_url` varchar(512) NULL DEFAULT NULL COMMENT '附件地址',
  `remark` varchar(1024) NULL DEFAULT NULL COMMENT '备注',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_no` (`no`),
  KEY `idx_customer_id` (`customer_id`),
  KEY `idx_account_id` (`account_id`),
  KEY `idx_order_id` (`order_id`),
  KEY `idx_tenant_status_time` (`tenant_id`,`status`,`return_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 销售退货表';

--changeset yuheng-template-erp:erp-schema-021 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_sale_return_items'
CREATE TABLE `erp_sale_return_items` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `return_id` bigint NOT NULL COMMENT '销售退货编号',
  `order_item_id` bigint NOT NULL COMMENT '销售订单项编号',
  `warehouse_id` bigint NOT NULL COMMENT '仓库编号',
  `product_id` bigint NOT NULL COMMENT '产品编号',
  `product_unit_id` bigint NOT NULL COMMENT '产品单位单位',
  `product_price` decimal(24, 6) NOT NULL COMMENT '产品单价',
  `count` decimal(24, 6) NOT NULL COMMENT '数量',
  `total_price` decimal(24, 6) NOT NULL COMMENT '总价',
  `tax_percent` decimal(24, 6) NULL DEFAULT NULL COMMENT '税率，百分比',
  `tax_price` decimal(24, 6) NULL DEFAULT NULL COMMENT '税额，单位：元',
  `remark` varchar(1024) NULL DEFAULT NULL COMMENT '备注',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_return_id` (`return_id`),
  KEY `idx_order_item_id` (`order_item_id`),
  KEY `idx_warehouse_product` (`warehouse_id`,`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 销售退货项表';

--changeset yuheng-template-erp:erp-schema-022 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_stock'
CREATE TABLE `erp_stock` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `product_id` bigint NOT NULL COMMENT '产品编号',
  `warehouse_id` bigint NOT NULL COMMENT '仓库编号',
  `count` decimal(24, 6) NOT NULL COMMENT '库存数量',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_product_warehouse` (`product_id`,`warehouse_id`),
  KEY `idx_warehouse_id` (`warehouse_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 产品库存表';

--changeset yuheng-template-erp:erp-schema-023 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_stock_check'
CREATE TABLE `erp_stock_check` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '盘点编号',
  `no` varchar(255) NOT NULL COMMENT '盘点单号',
  `check_time` datetime NOT NULL COMMENT '盘点时间',
  `total_count` decimal(24, 6) NOT NULL COMMENT '合计数量',
  `total_price` decimal(24, 6) NOT NULL COMMENT '合计金额，单位：元',
  `status` tinyint NOT NULL COMMENT '状态',
  `remark` varchar(255) NULL DEFAULT NULL COMMENT '备注',
  `file_url` varchar(255) NULL DEFAULT NULL COMMENT '附件 URL',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_no` (`no`),
  KEY `idx_tenant_status_time` (`tenant_id`,`status`,`check_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 库存盘点单表';

--changeset yuheng-template-erp:erp-schema-024 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_stock_check_item'
CREATE TABLE `erp_stock_check_item` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '调拨项编号',
  `check_id` bigint NOT NULL COMMENT '调拨编号',
  `warehouse_id` bigint NOT NULL COMMENT '仓库编号',
  `product_id` bigint NOT NULL COMMENT '产品编号',
  `product_unit_id` bigint NOT NULL COMMENT '产品单位编号',
  `product_price` decimal(24, 6) NULL DEFAULT NULL COMMENT '产品单价',
  `stock_count` decimal(24, 6) NOT NULL COMMENT '账面数量（当前库存）',
  `actual_count` decimal(24, 6) NOT NULL COMMENT '实际数量（实际库存）',
  `count` decimal(24, 6) NOT NULL COMMENT '盈亏数量',
  `total_price` decimal(24, 6) NULL DEFAULT NULL COMMENT '合计金额，单位：元',
  `remark` varchar(255) NULL DEFAULT NULL COMMENT '备注',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_check_id` (`check_id`),
  KEY `idx_warehouse_product` (`warehouse_id`,`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 库存盘点项表';

--changeset yuheng-template-erp:erp-schema-025 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_stock_in'
CREATE TABLE `erp_stock_in` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '入库编号',
  `no` varchar(255) NOT NULL COMMENT '入库单号',
  `supplier_id` bigint NULL DEFAULT NULL COMMENT '供应商编号',
  `in_time` datetime NOT NULL COMMENT '入库时间',
  `total_count` decimal(24, 6) NOT NULL COMMENT '合计数量',
  `total_price` decimal(24, 6) NOT NULL COMMENT '合计金额，单位：元',
  `status` tinyint NOT NULL COMMENT '状态',
  `remark` varchar(255) NULL DEFAULT NULL COMMENT '备注',
  `file_url` varchar(255) NULL DEFAULT NULL COMMENT '附件 URL',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_no` (`no`),
  KEY `idx_supplier_id` (`supplier_id`),
  KEY `idx_tenant_status_time` (`tenant_id`,`status`,`in_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 其它入库单表';

--changeset yuheng-template-erp:erp-schema-026 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_stock_in_item'
CREATE TABLE `erp_stock_in_item` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '入库项编号',
  `in_id` bigint NOT NULL COMMENT '入库编号',
  `warehouse_id` bigint NOT NULL COMMENT '仓库编号',
  `product_id` bigint NOT NULL COMMENT '产品编号',
  `product_unit_id` bigint NOT NULL COMMENT '产品单位编号',
  `product_price` decimal(24, 6) NULL DEFAULT NULL COMMENT '产品单价',
  `count` decimal(24, 6) NOT NULL COMMENT '产品数量',
  `total_price` decimal(24, 6) NULL DEFAULT NULL COMMENT '合计金额，单位：元',
  `remark` varchar(255) NULL DEFAULT NULL COMMENT '备注',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_in_id` (`in_id`),
  KEY `idx_warehouse_product` (`warehouse_id`,`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 其它入库单项表';

--changeset yuheng-template-erp:erp-schema-027 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_stock_move'
CREATE TABLE `erp_stock_move` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '调拨编号',
  `no` varchar(255) NOT NULL COMMENT '调拨单号',
  `move_time` datetime NOT NULL COMMENT '调拨时间',
  `total_count` decimal(24, 6) NOT NULL COMMENT '合计数量',
  `total_price` decimal(24, 6) NOT NULL COMMENT '合计金额，单位：元',
  `status` tinyint NOT NULL COMMENT '状态',
  `remark` varchar(255) NULL DEFAULT NULL COMMENT '备注',
  `file_url` varchar(255) NULL DEFAULT NULL COMMENT '附件 URL',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_no` (`no`),
  KEY `idx_tenant_status_time` (`tenant_id`,`status`,`move_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 库存调拨单表';

--changeset yuheng-template-erp:erp-schema-028 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_stock_move_item'
CREATE TABLE `erp_stock_move_item` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '调拨项编号',
  `move_id` bigint NOT NULL COMMENT '调拨编号',
  `from_warehouse_id` bigint NOT NULL COMMENT '调出仓库编号',
  `to_warehouse_id` bigint NOT NULL COMMENT '调入仓库编号',
  `product_id` bigint NOT NULL COMMENT '产品编号',
  `product_unit_id` bigint NOT NULL COMMENT '产品单位编号',
  `product_price` decimal(24, 6) NOT NULL COMMENT '产品单价',
  `count` decimal(24, 6) NOT NULL COMMENT '产品数量',
  `total_price` decimal(24, 6) NOT NULL COMMENT '合计金额，单位：元',
  `remark` varchar(1024) NULL DEFAULT NULL COMMENT '备注',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_move_id` (`move_id`),
  KEY `idx_from_warehouse_product` (`from_warehouse_id`,`product_id`),
  KEY `idx_to_warehouse_product` (`to_warehouse_id`,`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 库存调拨单项表';

--changeset yuheng-template-erp:erp-schema-029 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_stock_out'
CREATE TABLE `erp_stock_out` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '出库编号',
  `no` varchar(255) NOT NULL COMMENT '出库单号',
  `customer_id` bigint NULL DEFAULT NULL COMMENT '客户编号',
  `out_time` datetime NOT NULL COMMENT '出库时间',
  `total_count` decimal(24, 6) NOT NULL COMMENT '合计数量',
  `total_price` decimal(24, 6) NOT NULL COMMENT '合计金额，单位：元',
  `status` tinyint NOT NULL COMMENT '状态',
  `remark` varchar(255) NULL DEFAULT NULL COMMENT '备注',
  `file_url` varchar(255) NULL DEFAULT NULL COMMENT '附件 URL',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_no` (`no`),
  KEY `idx_customer_id` (`customer_id`),
  KEY `idx_tenant_status_time` (`tenant_id`,`status`,`out_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 其它入库单表';

--changeset yuheng-template-erp:erp-schema-030 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_stock_out_item'
CREATE TABLE `erp_stock_out_item` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '出库项编号',
  `out_id` bigint NOT NULL COMMENT '出库编号',
  `warehouse_id` bigint NOT NULL COMMENT '仓库编号',
  `product_id` bigint NOT NULL COMMENT '产品编号',
  `product_unit_id` bigint NOT NULL COMMENT '产品单位编号',
  `product_price` decimal(24, 6) NULL DEFAULT NULL COMMENT '产品单价',
  `count` decimal(24, 6) NOT NULL COMMENT '产品数量',
  `total_price` decimal(24, 6) NULL DEFAULT NULL COMMENT '合计金额，单位：元',
  `remark` varchar(255) NULL DEFAULT NULL COMMENT '备注',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_out_id` (`out_id`),
  KEY `idx_warehouse_product` (`warehouse_id`,`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 其它出库单项表';

--changeset yuheng-template-erp:erp-schema-031 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_stock_record'
CREATE TABLE `erp_stock_record` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `product_id` bigint NOT NULL COMMENT '产品编号',
  `warehouse_id` bigint NOT NULL COMMENT '仓库编号',
  `count` decimal(24, 6) NOT NULL COMMENT '出入库数量',
  `total_count` decimal(24, 6) NOT NULL COMMENT '总库存量',
  `biz_type` tinyint NOT NULL COMMENT '业务类型',
  `biz_id` bigint NOT NULL COMMENT '业务编号',
  `biz_item_id` bigint NOT NULL COMMENT '业务项编号',
  `biz_no` varchar(255) NOT NULL COMMENT '业务单号',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_warehouse_product` (`warehouse_id`,`product_id`),
  KEY `idx_biz_type_id` (`biz_type`,`biz_id`),
  KEY `idx_biz_item_id` (`biz_item_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 产品库存明细表';

--changeset yuheng-template-erp:erp-schema-032 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_supplier'
CREATE TABLE `erp_supplier` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '供应商编号',
  `name` varchar(255) NOT NULL COMMENT '供应商名称',
  `contact` varchar(100) NULL DEFAULT NULL COMMENT '联系人',
  `mobile` varchar(30) NULL DEFAULT NULL COMMENT '手机号码',
  `telephone` varchar(30) NULL DEFAULT NULL COMMENT '联系电话',
  `email` varchar(50) NULL DEFAULT NULL COMMENT '电子邮箱',
  `fax` varchar(30) NULL DEFAULT NULL COMMENT '传真',
  `remark` varchar(255) NULL DEFAULT NULL COMMENT '备注',
  `status` tinyint NOT NULL COMMENT '开启状态',
  `sort` int NOT NULL COMMENT '排序',
  `tax_no` varchar(50) NULL DEFAULT NULL COMMENT '纳税人识别号',
  `tax_percent` decimal(24, 6) NULL DEFAULT NULL COMMENT '税率',
  `bank_name` varchar(50) NULL DEFAULT NULL COMMENT '开户行',
  `bank_account` varchar(50) NULL DEFAULT NULL COMMENT '开户账号',
  `bank_address` varchar(50) NULL DEFAULT NULL COMMENT '开户地址',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_status` (`tenant_id`,`status`),
  KEY `idx_mobile` (`mobile`),
  KEY `idx_telephone` (`telephone`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 供应商表';

--changeset yuheng-template-erp:erp-schema-033 splitStatements:true endDelimiter:;
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'erp_warehouse'
CREATE TABLE `erp_warehouse` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '仓库编号',
  `name` varchar(20) NOT NULL COMMENT '仓库名称',
  `address` varchar(50) NULL DEFAULT NULL COMMENT '仓库地址',
  `sort` bigint NOT NULL COMMENT '排序',
  `remark` varchar(100) NULL DEFAULT NULL COMMENT '备注',
  `principal` varchar(20) NULL DEFAULT NULL COMMENT '负责人',
  `warehouse_price` decimal(24, 6) NULL DEFAULT NULL COMMENT '仓储费，单位：元',
  `truckage_price` decimal(24, 6) NULL DEFAULT NULL COMMENT '搬运费，单位：元',
  `status` tinyint NOT NULL COMMENT '开启状态',
  `default_status` bit(1) NULL DEFAULT b'0' COMMENT '是否默认',
  `creator` varchar(64) NULL DEFAULT '' COMMENT '创建者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(64) NULL DEFAULT '' COMMENT '更新者',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NOT NULL DEFAULT b'0' COMMENT '是否删除',
  `tenant_id` bigint NOT NULL DEFAULT 0 COMMENT '租户编号',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_status` (`tenant_id`,`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ERP 仓库表';
