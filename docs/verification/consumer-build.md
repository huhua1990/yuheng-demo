# yuheng-demo 消费端验证

验证日期：2026-10-25
工程：`/Users/huhua/study/ai/yuheng/yuheng-demo`

## Maven 依赖边界

`pom.xml` 只直接声明：

```text
com.yuheng:yuheng-server:0.1.0-SNAPSHOT
```

启动类、运行配置和默认控制器由消费端维护；framework、system、infra 通过 `yuheng-server` 传递依赖进入运行时。

## 构建验证

先安装 core，再构建消费端：

```bash
mvn -s /tmp/yuheng-maven-settings.xml install -DskipTests \
  -f /Users/huhua/study/ai/yuheng/yuheng-core/pom.xml
mvn -s /tmp/yuheng-maven-settings.xml -DskipTests package \
  -f /Users/huhua/study/ai/yuheng/yuheng-demo/pom.xml
```

结果：两个命令均通过，生成：

```text
/Users/huhua/study/ai/yuheng/yuheng-demo/target/yuheng-demo.jar
```

## 治理消费验证

- `yuheng-manifest.yaml` 的 code artifact 使用 `0.1.0-SNAPSHOT`；
- `yuheng-rules/`、`yuheng-skills/` 和 `ai-knowledge-core/` 由 core 快照同步；
- `docs/specs/`、`docs/plans/`、`docs/verification/` 和 `consumer-overlay/` 保持消费端所有权；
- 本次提交前已执行 postcheck、sync check 和 sync verify，结果均为 `PASS`，且 sync check 没有待同步差异。
