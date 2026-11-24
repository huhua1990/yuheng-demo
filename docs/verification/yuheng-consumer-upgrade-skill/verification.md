# Yuheng 消费端升级 Skill 验证

- workId: `yuheng-consumer-upgrade-skill`
- 日期：2026-11-20（Asia/Shanghai）
- 代码版本：`0.1.0-SNAPSHOT`
- 治理版本：`0.2.0`
- 知识版本：`0.1.0`
- 授权依据：用户要求实现参照 Athena `update-athena` 的 Yuheng 升级 Skill。

## 验收结果

| AC | 结果 | 证据 |
|---|---|---|
| AC-1 Skill 覆盖升级流程与边界 | PASS | `AGENTS.md` 已登记升级路由；`consumer-overlay/yuheng-upgrade/SKILL.md` 明确版本源、兼容检查、构建、数据库迁移风险及 `sync-specs` 边界 |
| AC-2 预览/应用限定更新字段 | PASS | 单测验证仅暂存 POM/UI/manifest 目标字段且保留其他 UI 依赖及 governance 字段；使用真实 core manifest 完成只读 CLI 预览，目标文件保持干净 |
| AC-3 异常版本和脏目标保护 | PASS | 单测验证无效 artifact 版本及已有 Git 修改均停止 |
| AC-4 自动化测试 | PASS | 下列 4 个 unittest 全部通过 |
| AC-5 结果真实记录 | PASS | 本文件记录实际命令和输出；未执行的项目构建未标记为通过 |

## 实际验证

```text
python3 -m unittest discover -s consumer-overlay/yuheng-upgrade/tests -v
Ran 4 tests ... OK

python3 -m py_compile consumer-overlay/yuheng-upgrade/scripts/update_yuheng.py consumer-overlay/yuheng-upgrade/tests/test_update_yuheng.py
PASS

python3 consumer-overlay/yuheng-upgrade/scripts/update_yuheng.py --help
PASS

python3 consumer-overlay/yuheng-upgrade/scripts/update_yuheng.py \
  --root /Users/huhua/study/ai/yuheng/yuheng-demo \
  --from-manifest /Users/huhua/study/ai/yuheng/yuheng-core/release/yuheng-manifest.yaml
PASS；只读预览 codeVersion/server 0.1.0-SNAPSHOT、UI 0.1.0-SNAPSHOT。

git diff --check
PASS
```

未执行完整 Maven/UI 构建或真实依赖升级：本任务实现 Skill 与其安全版本编辑器，不改变当前版本，不访问制品仓库或数据库。当前仓库仍没有 pnpm 锁文件，实际升级时需按 Skill 的依赖解析和构建步骤验证。
