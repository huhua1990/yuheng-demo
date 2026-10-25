# Task 3 治理同步验证记录

验证日期：2026-10-25  
消费端：`/Users/huhua/study/ai/yuheng/yuheng-demo`  
治理源：`/Users/huhua/study/ai/yuheng/yuheng-core`

## 同步边界

- core 规则写入 `yuheng-rules/`；
- core 技能写入 `yuheng-skills/`；
- 知识写入 `ai-knowledge-core/`；
- 版本事实写入 `yuheng-manifest.yaml`；
- `athena-rules/`、`athena-skills/` 在 manifest 中声明为旧名称空间兼容入口；
- `docs/specs/`、`docs/plans/`、`docs/verification/`、业务源码和 `consumer-overlay/` 由消费端托管。

## 验证命令

```bash
python3 -m unittest discover \
  -s /Users/huhua/study/ai/yuheng/yuheng-demo/sync/skills/sync-specs/scripts \
  -p 'test_*.py' -v

python3 /Users/huhua/study/ai/yuheng/yuheng-demo/sync/skills/sync-specs/scripts/postcheck_project.py \
  --project-root /Users/huhua/study/ai/yuheng/yuheng-demo \
  --project-id yuheng-demo --json

python3 /Users/huhua/study/ai/yuheng/yuheng-demo/sync/skills/sync-specs/scripts/sync-specs-api.py \
  --source /Users/huhua/study/ai/yuheng/yuheng-core \
  --target /Users/huhua/study/ai/yuheng/yuheng-demo \
  --verify --json
```

结果：

- 4 个同步与初始化测试全部通过；
- postcheck 返回 `PASS`；
- `sync --verify` 返回 `PASS`；
- apply 使用暂存目录和原子替换，失败时保留原快照；
- 符号链接托管目录会被拒绝；
- 同步没有覆盖消费端文档、业务目录或 overlay。

## 更新语义

- `--check` 只计算差异；
- `--apply` 更新托管快照并记录 `.yuheng/last-sync.json`；
- `--verify` 只检查当前快照；
- `postcheck` 检查项目身份、manifest、治理目录、知识轨道和保护路径。
