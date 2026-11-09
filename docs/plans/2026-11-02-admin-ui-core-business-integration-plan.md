# Yuheng Admin UI Core/Business Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reconstruct the complete Yuheng management UI by distributing reusable platform capabilities to the `yuheng-ui` NPM package and product business screens to the `yuheng-demo-ui` consumer, following the `athena-server`/`athena-ui` plus demo dependency model.

**Architecture:** `yuheng-core/yuheng-ui` owns the Vue runtime, authentication, tenant-aware request layer, shell, shared components, common Home/Login/Profile/Error screens, and system/infra pages. `yuheng-demo/yuheng-demo-ui` consumes only the public `yuheng-ui` package from `package.json`, and owns business APIs, views, route/menu metadata, and product-specific assets. Maven continues to assemble the backend from `yuheng-server`; pnpm independently builds the browser application.

**Tech Stack:** Vue 3, TypeScript, Vite 8, Vue Router 5, Pinia 3, Element Plus, pnpm, Vitest, Spring Boot 3.5, Maven.

---

## Repository and Change Safety

- Core repository: `/Users/huhua/study/ai/yuheng/yuheng-core`; frontend package: `yuheng-ui/`.
- Consumer repository: `/Users/huhua/study/ai/yuheng/yuheng-demo`; frontend app: `yuheng-demo-ui/`.
- Read-only migration source: `/Users/huhua/study/ai/yuheng/yudao-ui-admin-vue3`.
- Before each implementation session, record `git status --short` independently in core and demo. Do not stage, rewrite, or revert demo's existing Liquibase/config/spec edits or unrelated test edits.
- Do not copy `.git`, `node_modules`, `.env*` secrets, IDE files, source maps, build output, or upstream docs into either target.
- Keep core and demo changes in their own repositories. Never add a source-path dependency from demo into `yuheng-core/yuheng-ui/src`.

## Source Ownership Inventory

The baseline currently contains 48 layout files, 330 component files, 7 style files, 22 API domains, and 18 view domains. A quick count reports 14 API/72 view files for AI, 10/39 for AI1, 12/53 BPM, 24/119 CRM, 23/63 ERP, 26/85 FMS, 62/203 HRM, 28/139 IM, 16/96 IoT, 40/186 Mall, 10/32 Member, 131/287 MES, 11/72 MP, 41/161 OA, 11/23 Pay, 29/83 PMS, 0/3 Report, and 17/42 WMS. Counts are inventory hints; generated migration manifests must provide exact file-level totals and status.

Ownership rules:

- Core: authentication, tenant/token context, request and response handling, permission runtime, layout, shared stores/components, common Home/Login/Profile/Error/Redirect, and system/infra production APIs and screens.
- Demo: `ai`, `ai1`, `bpm`, `crm`, `erp`, `fms`, `hrm`, `im`, `iot`, `mall`, `member`, `mes`, `mp`, `oa`, `pay`, `pms`, `report`, and `wms` APIs, views, business components, route metadata, and business-only assets.
- Any source with mixed ownership is split at the smallest independently meaningful module boundary. A platform-owned file must not import a business API or business state; a consumer-owned file may use core only through package exports.

## Task 1: Freeze Baselines and Create Migration Inventories

**Files:**
- Create: `yuheng-core/yuheng-ui/docs/admin-ui-migration-inventory.md`
- Create: `yuheng-demo/docs/specs/admin-ui-business-migration-inventory.md`
- Create: `yuheng-core/yuheng-ui/scripts/check-migration-inventory.mjs`
- Test: `yuheng-core/yuheng-ui/tests/release/migration-inventory.test.ts`

- [ ] Record clean/dirty status for core, demo, and source repositories. Save no changes from the source repo.
- [ ] Generate sorted source manifests for layout, styles, components, common views, all platform `system`/`infra` API and view files, all business API/view domains, assets, router definitions, and route metadata.
- [ ] Classify every source row as `core`, `demo`, `shared-split`, `excluded-sample`, or `review-required`, with destination path and import dependencies.
- [ ] Add inventory tests that reject missing destinations for `core`/`demo` rows and reject business paths in the core manifest. Run them against the initial incomplete manifest and confirm the expected failure.
- [ ] Fill the first inventory snapshot from the existing platform import inventory and member design; record exact file counts and unresolved mixed-ownership cases.
- [ ] Run inventory tests and boundary checks. Expected: all source files are classified, no unresolved `review-required` row remains in the initial platform/business scope, and core has no business dependency.

## Task 2: Complete the Core Platform Runtime and Standard Shell

**Files:**
- Modify: `yuheng-core/yuheng-ui/src/layout/**`
- Modify: `yuheng-core/yuheng-ui/src/components/**`
- Modify: `yuheng-core/yuheng-ui/src/styles/**`
- Modify: `yuheng-core/yuheng-ui/src/runtime/**`
- Modify: `yuheng-core/yuheng-ui/src/router/**`
- Modify: `yuheng-core/yuheng-ui/src/stores/**`
- Modify: `yuheng-core/yuheng-ui/src/index.ts`
- Modify: `yuheng-core/yuheng-ui/package.json`
- Test: `yuheng-core/yuheng-ui/tests/runtime/**`
- Test: `yuheng-core/yuheng-ui/tests/router/**`
- Test: `yuheng-core/yuheng-ui/tests/components/**`

- [ ] Add failing tests for shell navigation from dynamic permission menus, nested route rendering, logout/login redirects, browser refresh, tenant selection context, and package-root exports.
- [ ] Run the focused tests and verify each fails because the standard interaction or export is absent.
- [ ] Migrate baseline shell modules from `layout/`, keeping API calls behind the existing Yuheng context/request layer and using platform-owned stores only.
- [ ] Migrate generic components by inventory classification. Leave coupon, product, promotion, BPM, and other business-bound components for Task 5/6.
- [ ] Replace placeholder Home/Login/Profile/Error/Redirect presentations with the complete platform versions while preserving the Yuheng token, tenant, and permission contracts.
- [ ] Export only supported package entry points from `src/index.ts`; add package-root contract tests for each component/runtime export used by the consumer.
- [ ] Run `pnpm test`, `pnpm run typecheck`, `pnpm run build`, and `pnpm run lint:boundary` in `yuheng-core/yuheng-ui`.
- [ ] Run the core application/preview and verify menu shell, login, responsive shell behavior, and no console errors.

## Task 3: Migrate Core System and Infrastructure Pages

**Files:**
- Modify: `yuheng-core/yuheng-ui/src/modules/system/**`
- Modify: `yuheng-core/yuheng-ui/src/modules/infra/**`
- Modify: `yuheng-core/yuheng-ui/src/router/platform-routes.ts`
- Modify: `yuheng-core/yuheng-ui/src/index.ts`
- Update: `yuheng-core/yuheng-ui/docs/platform-import-inventory.md`
- Test: `yuheng-core/yuheng-ui/tests/modules/system/**`
- Test: `yuheng-core/yuheng-ui/tests/modules/infra/**`

- [ ] Add failing route/API contract tests derived from the baseline's system and infra menus, API paths, permission strings, and page component keys.
- [ ] Verify RED against the current placeholder module pages.
- [ ] Migrate system pages and their API/type dependencies into `modules/system`; convert all aliases to package-local imports and all requests to the shared Yuheng client.
- [ ] Migrate infra production pages and APIs into `modules/infra`; exclude `infra/demo` samples from default routes.
- [ ] Implement dynamic menu component resolution for each migrated page key and preserve permission-based visibility.
- [ ] Add route coverage ensuring each production menu component resolves and each API adapter uses the expected `/admin-api` path.
- [ ] Run full core package tests, typecheck, build, boundary scan, and package export tests.
- [ ] Inspect the built NPM package contents with `pnpm pack --dry-run`; confirm source, samples, unrelated business APIs, and secrets are excluded.

## Task 4: Establish Versioned Package Consumption in Demo

**Files:**
- Modify: `yuheng-demo/yuheng-demo-ui/package.json`
- Create/Update: `yuheng-demo/yuheng-demo-ui/pnpm-lock.yaml`
- Modify: `yuheng-demo/yuheng-demo-ui/src/main.ts`
- Modify: `yuheng-demo/yuheng-demo-ui/src/App.vue`
- Modify: `yuheng-demo/yuheng-demo-ui/vite.config.ts`
- Modify: `yuheng-demo/yuheng-demo-ui/.env.local.example`
- Modify: `yuheng-demo/.github/workflows/consumer-verify.yml`
- Test: `yuheng-demo/yuheng-demo-ui/tests/consumer-entry.test.ts`
- Test: `yuheng-demo/yuheng-demo-ui/tests/package-boundary.test.ts`

- [ ] Add failing consumer tests requiring a registry-version `yuheng-ui` dependency, public-root imports only, Vite API proxy settings, platform runtime installation, and business route registration.
- [ ] Run focused consumer tests and confirm they fail for the absent integration behavior.
- [x] Replace the `file:`/workspace/source-link idea with the published `yuheng-ui` semver dependency matching the core release line; add all direct runtime dependencies required by migrated business pages to the consumer package.
- [x] Implement local package verification by packing the core package to a temporary directory and installing that tarball into the demo without committing a local-path dependency or overwriting a user's `node_modules` link.
- [ ] Configure Vite to use relative `/admin-api`, a configurable `VITE_BACKEND_ORIGIN`, `strictPort`, and the existing local backend default.
- [ ] Set local UI flags to match the demo local profile: tenant enabled, captcha disabled, API encryption disabled; keep credentials in existing safe local env files and out of committed examples.
- [ ] Update CI to install with the committed pnpm lock, run boundary tests/test/typecheck/build, and assert dependency package name/version.
- [ ] Run consumer tests, typecheck, build, and platform-import boundary scan using the locally packed core NPM artifact.

## Task 5: Migrate Business API and Route Contracts by Domain

**Files:**
- Create: `yuheng-demo/yuheng-demo-ui/src/api/<domain>/**`
- Create: `yuheng-demo/yuheng-demo-ui/src/router/business-modules/<domain>.ts`
- Create: `yuheng-demo/yuheng-demo-ui/src/modules/business-manifest.ts`
- Modify: `yuheng-demo/yuheng-demo-ui/src/router/business.ts`
- Modify: `yuheng-demo/yuheng-demo-ui/src/main.ts`
- Update: `yuheng-demo/docs/specs/admin-ui-business-migration-inventory.md`
- Test: `yuheng-demo/yuheng-demo-ui/tests/api-contracts/<domain>.test.ts`
- Test: `yuheng-demo/yuheng-demo-ui/tests/routes/<domain>.test.ts`

- [ ] Add inventory-driven failing tests for exact business API module exports, URL/method contracts, route names, permission strings, and menu component keys.
- [ ] Verify RED before copying/adapting API and route modules.
- [ ] Migrate business API/type folders by domain, replacing baseline Axios imports with the public `yuheng-ui` request contract while preserving request methods, URL paths, response DTOs, and upload/download behavior.
- [ ] Keep generic runtime needs out of demo: do not add a second axios/token/tenant interceptor or a second permission store.
- [ ] Define a consumer business manifest mapping menu component strings to lazy-loaded view components; verify every baseline business menu component maps or has an explicit excluded-sample disposition.
- [ ] Register business routes through the public runtime route extension contract; avoid importing core internals.
- [ ] Run all consumer API/route contract tests and platform boundary checks.

## Task 6: Migrate Business Views, Components, and Assets

**Files:**
- Create: `yuheng-demo/yuheng-demo-ui/src/views/<domain>/**`
- Create: `yuheng-demo/yuheng-demo-ui/src/components/business/**`
- Create: `yuheng-demo/yuheng-demo-ui/src/assets/business/**`
- Modify: `yuheng-demo/yuheng-demo-ui/package.json`
- Modify: `yuheng-demo/yuheng-demo-ui/tsconfig.json`
- Update: `yuheng-demo/docs/specs/admin-ui-business-migration-inventory.md`
- Test: `yuheng-demo/yuheng-demo-ui/tests/views/<domain>.test.ts`

- [ ] Add failing inventory tests verifying every in-scope business view/component/asset has a destination and all imported business APIs resolve.
- [ ] Verify RED for representative pages from each domain before migrating the page groups.
- [ ] Migrate in dependency batches: shared business editors/selectors first; then `system-independent` business roots; then modules with cross-domain references such as member/mall/pay/trade/promotion and BPM/CRM/ERP/MES.
- [ ] Preserve business behavior, permission directives, component names referenced by dynamic menus, query route parameters, and backend API contracts.
- [ ] Resolve baseline aliases mechanically only after inventory mapping; manually refactor mixed-owner imports and record each split in the inventory.
- [ ] Add direct dependencies for runtime imports actually used by consumer files; keep core peers provided once at the app root.
- [ ] Run targeted view tests after each domain batch, then full consumer typecheck/build and inventory/boundary scans.

## Task 7: Compose Complete Application and Verify End to End

**Files:**
- Modify: `yuheng-demo/yuheng-demo-ui/src/main.ts`
- Modify: `yuheng-demo/yuheng-demo-ui/src/router/business.ts`
- Modify: `yuheng-demo/yuheng-demo-ui/src/views/Home/**`
- Modify: `yuheng-demo/yuheng-demo-ui/index.html`
- Modify: `yuheng-demo/README.md`
- Modify: `yuheng-demo/.github/workflows/consumer-verify.yml`
- Test: `yuheng-demo/yuheng-demo-ui/tests/e2e/admin-entry.test.ts`
- Test: `yuheng-demo/yuheng-demo-ui/tests/e2e/admin-smoke.test.ts`

- [ ] Replace the placeholder Yuheng Demo home with the consumer product home built on the core shell, with full admin navigation sourced from backend permission menus.
- [ ] Add an E2E smoke test that opens `/login`, signs in against a controlled local test service, verifies user context/menu entries, opens representative platform and business routes, and reloads a nested route.
- [ ] Confirm no CAPTCHA-solving automation is used in E2E; tests use a stubbed auth fixture or backend integration test setup with captcha disabled.
- [ ] Start the real local backend and Vite app; verify `admin` can sign in, the homepage and dynamic menu render, one system page and representative business pages load, and API proxy requests stay same-origin.
- [ ] Capture desktop and narrow viewport screenshots for shell/menu overflow and key page layout; fix any blank or overlapping content.
- [ ] Run core and demo full test/typecheck/build suites, package boundary scans, governance postcheck, `git diff --check`, and Maven package with existing Liquibase working tree edits preserved.
- [ ] Record exact verification commands, source/destination inventory totals, known excluded samples, and any unavailable remote package-registry publication step in a consumer verification report.

## Task 8: Documentation and Release Handoff

**Files:**
- Modify: `yuheng-core/yuheng-ui/README.md`
- Modify: `yuheng-demo/README.md`
- Modify: `yuheng-demo/yuheng-manifest.yaml`
- Create: `yuheng-demo/docs/verification/admin-ui-core-business-integration.md`
- Update: `yuheng-core/release/**` only when required by established package version/release metadata

- [ ] Document core platform UI package ownership, supported package exports, and release version separately from backend Maven coordinates.
- [ ] Document demo setup: install package dependencies, start backend, run Vite, configure API target, and login using configured local account.
- [ ] Update manifests only after the package version and resolved dependency version are verified from lockfile/artifact metadata.
- [ ] Run final verification in both repositories and inspect separate diffs/statuses to ensure no pre-existing files were staged or altered by migration tooling.
- [ ] Do not publish NPM packages or push changes during implementation unless the user explicitly authorizes that external release action.

