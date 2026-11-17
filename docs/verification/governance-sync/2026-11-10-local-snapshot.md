# 本地治理快照验证

日期：2026-11-10  
消费端基线：`b9c4906`，另有用户已有 Java 重命名及未暂存修改，本次未修改这些文件。  
core 基线：`afbd19e`，本次同步来源含未提交的规则、技能、包名及知识文件修改。

## 已执行检查

- `python3 -m unittest discover -s sync/skills/sync-specs/scripts -p 'test_*.py' -v`：4 项通过。
- `sync-specs-api.py --source ../yuheng-core --target . --check --json`：同步前预览四项托管资产发生变化。
- `init-project.py --source ../yuheng-core --target . --project-id yuheng-demo --json`：本地同步返回 `PASS`。
- `postcheck_project.py --project-root . --project-id yuheng-demo --json`：返回 `PASS`。
- `sync-specs-api.py --source ../yuheng-core --target . --verify --json`：返回 `PASS`，无待同步差异。

## 限制

同步来源是本地 core 工作树，包含尚未提交的变更；同步结果仅证明其与该工作树一致。manifest 中现有 `sourceCommit: a152cf4` 是上游旧元数据，不代表本次快照的实际内容或提交来源，不能用于复现该快照。

demo CI 当前检出 core 的 `main`，没有固定到本次实际快照。只有在 core 变更提交并可被 CI 获取、来源信息和 CI 引用更新后，才能验证可复现的跨仓库同步。`docs/plans/.gitkeep` 与 `consumer-overlay/.gitkeep` 用于保留 postcheck 需要的空目录。
