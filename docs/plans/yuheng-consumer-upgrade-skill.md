# Yuheng 消费端升级 Skill 计划

- workId: `yuheng-consumer-upgrade-skill`
- 上游规格：`docs/specs/yuheng-consumer-upgrade-skill.md`
- 授权依据：用户明确要求实现参考 Athena update-athena 的 Yuheng 升级 Skill。
- Only Modify：`AGENTS.md` 的技能路由、本计划、对应规格、`consumer-overlay/yuheng-upgrade/`、本 workId 的验证记录。
- Do Not Modify：业务源码、已执行数据库迁移、治理托管快照、既有验证截图。

## 任务

1. [x] 新增版本更新脚本：读取 core 发布 manifest，提供只读预览和显式应用；保护格式、无关字段及 Git 已修改目标文件。
2. [x] 为脚本添加隔离临时仓库的 unittest，覆盖 manifest 解析、版本校验、字段暂存和脏文件拒绝。
3. [x] 编写消费端升级 Skill，明确版本兼容检查、构建验证、迁移风险、治理同步边界和升级证据要求，并在 `AGENTS.md` 登记入口。
4. [x] 运行测试、脚本帮助和必要的静态校验；记录结果及环境限制。

## 验证命令

```bash
python3 -m unittest discover -s consumer-overlay/yuheng-upgrade/tests -v
python3 consumer-overlay/yuheng-upgrade/scripts/update_yuheng.py --help
```

本任务不运行实际版本升级或连接外部制品仓库。
