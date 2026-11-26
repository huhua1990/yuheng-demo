---
name: yuheng-upgrade
description: Upgrade a Yuheng consumer's versioned yuheng-server and yuheng-ui dependencies from a core release manifest, then verify compatibility and build. Use when asked to upgrade or update Yuheng framework dependencies.
metadata:
  version: "0.1.0"
  owner: consumer-overlay
---

# Yuheng 消费端框架升级

本技能用于升级消费端运行时依赖 `com.yuheng:yuheng-server` 和 `yuheng-ui`。它不是治理快照同步：规则、技能和知识快照仍使用 `sync/skills/sync-specs/SKILL.md`。

## 边界

- 版本依据是目标 `yuheng-core` 发布目录中的 `release/yuheng-manifest.yaml`，并交叉检查 `release/compatibility-matrix.yaml`。不要根据 Maven/npm 的 `latest` 标签推断两个制品版本相同或兼容。
- 消费端只使用版本化 Maven/npm 制品；不得把 core 源码目录加入依赖或复制 core changelog 到消费端。
- 本技能脚本只修改根 `pom.xml` 的 `yuheng.version`、`yuheng-demo-ui/package.json` 的 `yuheng-ui` 和消费端 `yuheng-manifest.yaml` 的发布版本字段。业务 changelog、profile、锁文件和其他业务文件由各自工作流管理。
- 不清理 Liquibase checksum，不修改或删除已执行 changeset，不自动连接数据库，不提交、推送或发布。

## 执行流程

1. 确认消费端仓库根目录与 `git status`，保留已有业务和验证修改。若三个版本目标文件有未提交修改，先审查并纳入升级方案；默认脚本会拒绝覆盖这些文件。
2. 确认 core 发布版本和兼容组合：读取 core `release/yuheng-manifest.yaml`、`release/compatibility-matrix.yaml`，确认 server、UI 版本及其兼容约束；确认对应制品已发布且仓库凭据由 Maven/npm 自身配置提供。不要在 Skill 或命令中写入凭据。
3. 预览版本变更：

   ```bash
   python3 consumer-overlay/yuheng-upgrade/scripts/update_yuheng.py \
     --from-manifest /path/to/yuheng-core/release/yuheng-manifest.yaml
   ```

   检查输出目标版本与兼容矩阵。兼容矩阵需由执行者核对；脚本只解析发布 manifest，不代替兼容性判定。脚本默认只预览，不写文件。

4. 应用已核实的版本：

   ```bash
   python3 consumer-overlay/yuheng-upgrade/scripts/update_yuheng.py \
     --from-manifest /path/to/yuheng-core/release/yuheng-manifest.yaml --apply
   ```

   审查 diff，确认 `yuheng.version`、`yuheng-ui`、manifest 的 `codeVersion` 和 server/UI artifact 版本与发布 manifest 一致。兼容矩阵要求不同于上述直接映射时停止并修订脚本/流程，不要悄悄写入猜测值。

5. 验证解析到的依赖确实来自配置的仓库，并完成构建和适用测试：

   ```bash
   ./scripts/build.sh
   ```

   记录 Maven/npm 解析的实际版本、构建输出和失败信息。当前 Demo 使用独立的 `yuheng-demo-ui/pnpm-lock.yaml` 并以 `--frozen-lockfile` 安装；升级 `yuheng-ui` 版本后需使用 `CI=true pnpm --dir yuheng-demo-ui --ignore-workspace install --no-frozen-lockfile --ignore-scripts` 刷新锁文件再执行构建。检查项目已有测试入口，按升级影响运行必要测试。

6. 检查 core 发布是否包含数据库 changeset 变化。变更由版本化 `yuheng-server` 提供，应用启动时会按消费端 master changelog 加载；启动前先核对 `YUHENG_DB_*` 指向的目标数据库、备份/恢复方案和授权。升级 Skill 不代替数据库迁移审批或已有库接续评估。

7. 如本次还要求刷新治理或知识快照，单独按 `sync/skills/sync-specs/SKILL.md` 执行 `--check`、审阅、`--apply`、`--verify`，再运行 `postcheck_project.py`。同步不得覆盖 `consumer-overlay/`、业务代码和 `docs/`。

8. 更新同一 `workId` 的规格、计划和验证记录，填写升级前后 `codeVersion`、`governanceVersion`、`knowledgeVersion`，记录兼容矩阵来源、实际解析的制品版本、迁移评估、运行命令及结果。失败或未执行的检查保持 FAIL/NOT RUN。

## 阻塞条件

- core 发布 manifest、兼容矩阵或制品来源不可读，或版本组合不匹配。
- 目标版本无法从已发布制品解析，或构建解析到的版本与目标不同。
- 目标文件已有未审查修改、业务源码出现框架契约不兼容，或数据库迁移影响和目标库状态不清楚。

遇到阻塞时保留已生成的预览与证据，报告缺失信息和可继续动作；不得回退依赖、覆盖用户修改或将未运行的验证记为通过。

## 脚本测试

```bash
python3 -m unittest discover -s consumer-overlay/yuheng-upgrade/tests -v
```
