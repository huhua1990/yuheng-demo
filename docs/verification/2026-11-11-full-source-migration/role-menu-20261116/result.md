# Role menu cancel and save verification

Date: 2026-11-16

## Environment

- Demo executable JAR SHA-256: `61fba9414357444edbb929ca77a572c60659c7586e665a2c898e25fbd724fae6`.
- Cancel run: backend `127.0.0.1:48134`, production UI proxy `127.0.0.1:5197`, schema `yuheng_t3_role_menu_20261116`, restricted account `yh_rm16`.
- Save run: backend `127.0.0.1:48135`, production UI proxy `127.0.0.1:5198`, schema `yuheng_t3_role_save_20261116`, restricted account `yh_rs16`.
- Separate read-only API baseline run: backend `127.0.0.1:48136`, schema `yuheng_t3_role_api_20261116`, restricted account `yh_ra16`.
- Same-schema API contract run: backend `127.0.0.1:48137`, schema `yuheng_t3_role_api2_20261116`, restricted account `yh_r2_16`.
- Redis DB 15 started with zero keys and no DB 15 clients before each run. Quartz auto-start was disabled.
- The four original role-menu probes used a JAR predating Core changeset 009; their scope and limitations remain as recorded below. A separate Core 010 verification was completed on 2026-11-16 and is appended after cleanup.

## Cancel path

Logged into the isolated UI and opened System Management > Role Management > 普通角色 (role 2) > 菜单权限. Expanded the permission tree, selected WebSocket (menu 565), and clicked 取 消. The dialog closed without submitting the selection. The complete `system_role_menu` snapshot, ordered by primary key and including `id, role_id, menu_id, tenant_id, deleted`, was byte-identical before and after cancel: SHA-256 `2bafdca7517b45e920ee3d65671c2b6140985b9973eb755784f9135346d462ef`, 1552 rows. Active `(role_id=2, menu_id=565)` count remained zero.

Cancel snapshots are preserved as `baseline.tsv`, `after-cancel.tsv`, and `before-save.tsv`; all have 1552 rows and the same hash above.

## Save path

In the second isolated run, role 2's baseline was 1552 rows with active WebSocket relation count zero. The actual UI selected menu 565 and submitted with 确 定. The page displayed 修改成功. SQL showed an active `(role_id=2, menu_id=565, tenant_id=1)` row with id 9127; total table rows increased to 1556, and the target relation count became one.

Full ordered snapshots `save-before.tsv` and `save-after.tsv` have 1552 and 1556 rows. Their hashes are `2bafdca7517b45e920ee3d65671c2b6140985b9973eb755784f9135346d462ef` and `af3cb14aa727b1a94dbce44a771767e6a8615fdb6f76ad9a0d95e026e38cba22` respectively. The snapshots show the requested WebSocket relation plus new active role 2 relations for menu IDs 12090, 1894, and 1951; several prior role 2 rows changed `deleted` from 0 to 1 and replacement rows were inserted. The baseline file belonged to the first, subsequently dropped schema; the second run used a fresh seed. Its own `save-before.tsv` and `save-after.tsv` hashes match, confirming no intervening operation within the save run. Therefore the old snapshot is not a valid same-schema comparator for all pre-existing deleted rows. A third, separate clean schema returned 655 role 2 menu IDs without WebSocket or those three extra IDs; this confirms only the endpoint baseline.

A fourth isolated schema tested the API contract in one run: login succeeded, GET returned 655 menu IDs, POST with exactly the returned set plus 565 returned success, and the following GET returned 628 IDs including 565. The returned set removed 28 IDs (`api-delta.json` records the exact list). SQL confirmed one active 565 relation and 628 active role 2 relations; the full ordered post snapshot is `api-after.tsv`. At the time this result was recorded, those IDs' source was unresolved.

## Cleanup

- Gracefully stopped isolated Java PIDs 97554, 98228, 98904 and 99233 and UI servers 97645 and 98254; ports 48134/5197, 48135/5198, 48136 and 48137 have no listeners.
- Dropped only the four dedicated schemas and removed only `yh_rm16`@`%`, `yh_rs16`@`%`, `yh_ra16`@`%`, and `yh_r2_16`@`%`; schema and user counts verified as zero.
- Redis DB 15 had 11 keys after cancel, 9 after UI save, 8 after the read-only baseline, and 7 after the same-schema API contract run, with no DB 15 clients after shutdown. Each run started empty and the isolated instance was the only DB 15 client, so only DB 15 was flushed and verified at zero. Other Redis DBs were untouched.
- Shared schema, passwords, and pre-existing application PIDs were not modified.

## Status

The initial four probes established cancel-without-write, UI save success, target relation persistence and same-schema API readback. Subsequent source reconciliation found that all 28 removed IDs are absent from `system_menu` but have active role 1/2 relation rows in Core seed 005. This is a Core seed referential-integrity defect, not ordinary-tenant package filtering. Core changeset 010 now soft-deletes the 56 exact orphan seed rows; full evidence follows. UI reopening in the historical save schema remains unverified. This does not close T3/T4 or the full migration plan.

## Core 010 orphan seed repair verification (2026-11-16)

Source reconciliation found the 28 IDs in `api-delta.json` are all absent from `system_menu` seed rows, while Core seed 005 inserts matching active `system_role_menu` rows for both tenant 1 roles 1 and 2. The 28 menu IDs are 1679, 1684, 1703, 1704, 1706, 1707, 1724-1732 (excluding 1733), 1734, and 1842-1847, 1849-1854. This yields exactly 56 orphan relation rows (28 per role). The API run used system tenant 1, whose tenant contract exposes all seeded menus; ordinary package filtering does not explain the removals. `PermissionServiceImpl` returns relation menu IDs on GET, while save computes a diff against accessible current relations and soft-deletes omitted IDs.

Core changeset `010-clean-orphan-platform-role-menus.yaml` is registered after 009. It soft-deletes the 56 exact seed relation primary keys only when they still belong to role 1/2, tenant 1, are active, and their menu remains absent. Rollback restores only those exact rows under the same missing-menu guard. Changesets 001-009 were not modified; their current SHA-256 values were captured during verification.

Verification used a temporary repackaging of the existing Demo JAR with only its nested Core `yuheng-server` resource JAR replaced by the current Core build (outer JAR SHA-256 `0b65a3ad81159c7ff969ba91dd957172f6d4b4a838f537c989d8dd0d607a175f`). The target was a new restricted schema `yuheng_role_orphan_20261116`, port 48138, and Redis DB 15. The first start attempt failed before Liquibase because the temporary MySQL account was not created due to shell quoting; it was corrected and direct authentication tested before the successful run. That failed attempt created no schema objects or Redis keys.

Cold start ran 56/56 changesets, including 010. Database checks showed 1,552 total role-menu rows unchanged, 56 target seed rows inactive, zero active orphan rows, and 851 other active role 1/2 relations joining to existing menus. The admin seed password hash remained populated (60 characters); no password was read or changed. Restart ran zero new changesets: count stayed 56 and 010 appeared exactly once. The rollback UPDATE was executed inside a transaction, affected and reactivated exactly 56 target rows, then transaction rollback returned the active count to zero.

After stopping the isolated process, the temporary schema and restricted MySQL account were dropped and verified absent; Redis DB 15 returned to zero with no DB 15 clients; port 48138 has no listener. Shared schemas, accounts, historical passwords and other Redis databases were untouched. This closes the dangling Core seed relation defect for current clean installs/upgrades; it does not verify a UI reopen in the historical save schema, which had already been dropped, nor close overall T3/T4/T1.
