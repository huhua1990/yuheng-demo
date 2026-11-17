# T4 anonymous write endpoint authentication matrix

Date: 2026-11-17
Work ID: `YH-20261111-full-source-migration`

## Isolated environment

- Demo JAR SHA-256: `61fba9414357444edbb929ca77a572c60659c7586e665a2c898e25fbd724fae6`.
- Backend `127.0.0.1:48140`, schema `yuheng_t4_auth_boundary_20261117`, restricted user `yh_auth17`, Redis DB 14.
- Before startup the schema/account were absent, Redis DB 14 had zero keys and zero DB 14 clients, and port 48140 was free. The JAR cold start applied 54/54 changesets. Requests had tenant-id 1 and no authorization token.

## Requests and results

All eight JSON endpoints returned HTTP 200 with business code 401 and message `账号未登录`:

| Endpoint | Method | Result |
|---|---|---|
| `/system/notify-message/update-read?ids=1` | PUT | 401 |
| `/system/notify-message/update-all-read` | PUT | 401 |
| `/system/oauth2/authorize` | POST | 401 |
| `/system/user/profile/update` | PUT | 401 |
| `/system/user/profile/update-password` | PUT | 401 |
| `/system/social-user/bind` | POST | 401 |
| `/system/social-user/unbind` | DELETE | 401 |
| `/infra/file/create` | POST | 401 |

Multipart `/infra/file/upload` also returned HTTP 200/business 401 before multipart validation. The social bind request used deliberately invalid isolated code/state values; authentication rejected it before any third-party exchange. File upload body was empty and likewise rejected before controller validation.

The table snapshots before and after requests matched: `system_users=21`, `system_notify_message=95`, `system_oauth2_approve=0`, `system_social_user=0`, `infra_file=0`, and `infra_file_content=0`. This confirms the global authentication boundary prevents these anonymous writes. Because requests were rejected before controller execution, this does not test authenticated permissions, OAuth2 principal isolation, social callback state validation, or file object-store failure behavior.

## Cleanup

The backend shut down gracefully. The dedicated schema/account/grant were dropped and verified absent; Redis DB 14 started empty, had no clients after shutdown, and was flushed to zero; port 48140 had no listener. Shared `yuheng_demo` retained 150 tables and was not modified. Existing PIDs 78090 and 88411 were left untouched.

## Status

This closes only the anonymous authentication sub-item for the eight listed JSON writes plus file upload. T4 authenticated permission/tenant/transaction matrices remain open; T1/T3 and overall migration also remain open.
