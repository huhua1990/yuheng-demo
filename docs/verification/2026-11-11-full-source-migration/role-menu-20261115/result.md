# T3 role menu permission save verification

Date: 2026-11-15

## Environment and scope

- Demo JAR SHA-256: `4bc65f4f34047dcdb44e6cf7d5bd989dd0412ea3063d6db469fb27bc6294767e`.
- The JAR executed 54 Liquibase changesets and created 150 tables. It predates Core changeset 009 and is used only for the role/menu runtime contract, not as evidence that the latest Core release is consumed.
- The production UI bundle was served at `127.0.0.1:5196`, with `/admin-api` proxied to the isolated Demo backend on `48128`. The development-server path was avoided after reproducing the existing Vite dependency-prebundle error `ReferenceError: useI18n is not defined` in the generated `yuheng-ui_compat_utils_formRules.js`.
- The isolated schema was `yuheng_t3_role_menu_20261115`, the restricted database user was `yh_t3_role_menu15`, and Redis DB 1 started with zero keys. Shared schema `yuheng_demo` was not used.
- Cold start completed all 54 registered changesets. The 21 seeded user password hashes matched the JAR's 006 seed changeset byte-for-byte; no password values were exported into evidence.

## Results

- Logged in through the browser using the isolated Demo and opened System Management > Role Management > `普通角色` > `菜单权限`.
- Confirmed menu `WebSocket` (ID 565) was enabled, not deleted, and initially absent from role 2's menu assignment. Its parent was the enabled Infrastructure menu.
- Selected `WebSocket` in the actual permission tree and submitted through the page. The UI displayed `修改成功`; reopening the permission panel showed the parent half-checked and WebSocket checked.
- The `system_role_menu` table gained the requested active `(role_id=2, menu_id=565)` relation. The API response from GET also included ID 565 after saving.
- Requests without an access token to both `GET /system/permission/list-role-menus?roleId=2` and `POST /system/permission/assign-role-menu` returned application code 401. The follow-up authorized GET confirmed the unauthorized POST had not removed the test grant.
- The UI cancel path was not verified. During the attempted cancel check, the confirm button was clicked again by mistake, yielding a second successful save. Do not count cancel-without-write as passed.

## Baseline and cleanup limitation

The captured `permission-baseline.json` states 1552 relation rows, matching the 1552 lines in `role_menus.tsv` (the file contains duplicate role/menu pairs, so distinct-pair count is lower). After the UI save and the later authorized restore request, the table contained 1556 total rows. The test grant `(2,565)` was then soft-deleted; three active role-2 relations (menu IDs 1894, 1951, 12090) were present but absent from the captured active-pair set. The available snapshot is not sufficient to determine whether those relations were pre-existing tenant-scoped/duplicate data or effects of the permission API's delete-and-reinsert behavior, so they were not manually rewritten. This dedicated database was subsequently dropped in full, so no test state remains in MySQL.

## Resource cleanup

- Stopped the identified isolated Demo JAR PID 73160 and UI server PID 74636; ports 48128 and 5196 have no listeners.
- Dropped only `yuheng_t3_role_menu_20261115` and removed only `yh_t3_role_menu15`@`%`; verification found zero matching schema or user rows.
- Redis DB 1 started at zero keys. After stopping the service, its 10 keys were enumerated by name and found to be role/menu permission caches and OAuth tokens created by this isolated session. Those exact keys were deleted individually; DB size is now zero. No other Redis DB was touched.
- Closed the browser tab created for this run. The existing browser tabs and shared application processes were left open.

## Status

The browser save, success feedback, readback, requested active relation at first save, unauthorized GET/POST rejection, and dedicated-resource cleanup were verified. Cancel behavior and exact full-table preservation could not be established because the UI action was mis-targeted and the available snapshot does not identify all relation metadata/tenant-scoped duplicates. This sub-item remains partially open; overall T1/T3/T4 migration work remains open.
