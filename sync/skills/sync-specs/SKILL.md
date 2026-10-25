---
id: yuheng-sync-specs
version: 0.1.0
---

# Yuheng 消费端治理同步

治理资产从 `yuheng-core` 的 manifest 版本快照同步到消费端：

```bash
python3 sync/skills/sync-specs/scripts/sync-specs-api.py \
  --source /Users/huhua/study/ai/yuheng/yuheng-core \
  --target /Users/huhua/study/ai/yuheng/yuheng-demo \
  --check

python3 sync/skills/sync-specs/scripts/sync-specs-api.py \
  --source /Users/huhua/study/ai/yuheng/yuheng-core \
  --target /Users/huhua/study/ai/yuheng/yuheng-demo \
  --apply --project-id yuheng-demo

python3 sync/skills/sync-specs/scripts/sync-specs-api.py \
  --source /Users/huhua/study/ai/yuheng/yuheng-core \
  --target /Users/huhua/study/ai/yuheng/yuheng-demo \
  --verify
```

`--check` 只生成差异，`--apply` 暂存后原子替换托管目录，`--verify` 不修改文件。同步写入 `yuheng-rules/`、`yuheng-skills/`、`ai-knowledge-core/` 和 `yuheng-manifest.yaml`。

消费端的 `docs/specs/`、`docs/plans/`、`docs/verification/`、业务源码和 `consumer-overlay/` 永远由项目自己维护。旧的 `athena-rules/` 和 `athena-skills/` 只作为读取兼容命名空间保留，不会被同步覆盖。

初始化后运行：

```bash
python3 sync/skills/sync-specs/scripts/postcheck_project.py \
  --project-root /Users/huhua/study/ai/yuheng/yuheng-demo \
  --project-id yuheng-demo
```
