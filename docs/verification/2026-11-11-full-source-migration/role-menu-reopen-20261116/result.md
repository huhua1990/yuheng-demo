# T3 role menu save and reopen verification

Date: 2026-11-16
Work ID: `YH-20261111-full-source-migration`

## Isolated environment

- Temporary Demo JAR: `/tmp/yuheng-t3-role-reopen-20261116/yuheng-demo.jar`, SHA-256 `0b65a3ad81159c7ff969ba91dd957172f6d4b4a838f537c989d8dd0d607a175f`.
- The outer JAR was assembled from the existing Demo artifact, replacing only the nested `yuheng-server-0.1.0-SNAPSHOT.jar` with the current Core build. The nested JAR contains changeset 010; the repository Demo JAR was not replaced.
- Backend `127.0.0.1:48139`; production UI proxy `127.0.0.1:5199`; schema `yuheng_t3_role_reopen_20261116`; restricted user `yh_t3_reopen_16`; Redis DB 15.
- Before startup, the schema and user were absent, Redis DB 15 contained zero keys and had no DB 15 clients, and both ports were free.
- Cold start applied 56/56 changesets, including Core 010. The schema had 150 tables, 21 seeded users, and admin retained a non-empty 60-character password hash. Password values were not read or changed.

## Browser save and readback

Using the production UI, signed into the isolated tenant and opened System Management > Role Management > 普通角色 (role 2) > 菜单权限. Expanded Infrastructure and selected the enabled WebSocket menu (ID 565). The UI submitted the assignment and displayed `修改成功`; then the dialog was closed and opened again. After expanding Infrastructure, WebSocket remained checked (`aria-checked=true`).

The actual proxy log showed successful `GET /admin-api/system/menu/simple-list` and `GET /admin-api/system/permission/list-role-menus?roleId=2` requests, each returning HTTP 200 during the permission dialog lifecycle. Browser console warning/error lists were empty. A screenshot of the reopened permission dialog was shown in the task conversation.

SQL after save showed one active `(role_id=2, menu_id=565, tenant_id=1)` relation (ID 9127). The table contained 1,556 rows, including 659 role 2 rows and 631 active role 2 rows. Core 010 left zero active orphan role 1/2 relations. The seed admin password hash remained non-empty.

One ad-hoc login probe without the required tenant header was rejected with business code 400 before authentication; it made no database change. The UI login and all UI requests used the proper tenant context.

## Cleanup

The isolated backend completed graceful shutdown and the UI proxy was stopped. Only the dedicated schema and user were dropped. Redis DB 15 had nine keys after the run, with no remaining DB 15 clients; because it was empty before startup and isolated to this run, only DB 15 was flushed and returned to zero. Schema, grant and account checks returned zero; ports 48139 and 5199 had no listeners. Shared `yuheng_demo` remained at 150 tables and was not written. Historical passwords and other Redis databases were untouched.

## Status

This closes the T3 role-menu save/readback sub-item for a clean install containing Core 010. It does not retroactively establish the exact full-table delta in the deleted 2026-11-15 save schema, nor does it close overall T3, T1 or T4. Remaining migration items stay open in the plan.
