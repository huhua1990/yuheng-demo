--liquibase formatted sql

-- Align member_user constraints with social-login creation, tenant scope, and logical deletion.

--changeset yuheng-template-member:member-user-mobile-preflight-000
--preconditions onFail:HALT onError:HALT
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM (SELECT tenant_id, mobile FROM member_user WHERE deleted = b'0' AND mobile IS NOT NULL AND mobile <> '' GROUP BY tenant_id, mobile HAVING COUNT(*) > 1) duplicate_mobile
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM `member_user` WHERE CHAR_LENGTH(`mobile`) > 11
--precondition-sql-check expectedResult:0 SELECT COUNT(*) FROM `member_user` WHERE CHAR_LENGTH(`email`) > 50
SELECT 1;

--changeset yuheng-template-member:member-user-drop-legacy-mobile-index-001
--preconditions onFail:MARK_RAN onError:HALT
--precondition-sql-check expectedResult:1 SELECT COUNT(DISTINCT index_name) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'member_user' AND index_name = 'uk_mobile'
DROP INDEX `uk_mobile` ON `member_user`;

--changeset yuheng-template-member:member-user-active-mobile-unique-002
--preconditions onFail:HALT onError:HALT
ALTER TABLE `member_user`
  MODIFY COLUMN `mobile` varchar(11) NULL DEFAULT NULL COMMENT '手机号',
  MODIFY COLUMN `email` varchar(50) NULL DEFAULT NULL COMMENT '邮箱',
  ADD COLUMN `active_mobile_marker` tinyint GENERATED ALWAYS AS (IF(`deleted` = b'0' AND `mobile` IS NOT NULL AND `mobile` <> '', 1, NULL)) STORED,
  ADD UNIQUE KEY `uk_tenant_mobile_active` (`tenant_id`,`mobile`,`active_mobile_marker`);
