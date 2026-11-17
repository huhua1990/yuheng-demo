--liquibase formatted sql

--changeset yuheng-template-erp:erp-identifier-width-001
ALTER TABLE `erp_product`
  MODIFY COLUMN `unit_id` bigint NOT NULL COMMENT '单位编号';
