--liquibase formatted sql

--changeset yuheng-template-erp:erp-stock-active-uniqueness-001
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM (SELECT tenant_id, product_id, warehouse_id FROM erp_stock WHERE deleted = b'0' GROUP BY tenant_id, product_id, warehouse_id HAVING COUNT(*) > 1) duplicate_stock
ALTER TABLE `erp_stock`
  ADD COLUMN `active_marker` tinyint GENERATED ALWAYS AS (IF(`deleted` = b'0', 1, NULL)) STORED,
  ADD UNIQUE KEY `uk_tenant_product_warehouse_active` (`tenant_id`,`product_id`,`warehouse_id`,`active_marker`);
