# 后端模块拆分验证

- workId: 2026-11-11-backend-modules
- 规格及计划：[2026-11-11-backend-modules](../../specs/2026-11-11-backend-modules.md)
- codeVersion: b9c49067ffc7e8efe2e884a7fe26899ab92f175e，含既有未提交变更；governanceVersion: 0.2.0；knowledgeVersion: 0.1.0
- 验证时间：2026-11-11（Asia/Shanghai）
- AC-1 / T-1：`python3 -m unittest discover -s scripts/tests -v` 退出码 0，4 项通过；模块结构检查在改造前因根工程为 jar 而失败，改造后通过。`mvn -B package` 退出码 0，四个 reactor 模块均构建成功。
- AC-2 / T-2：检查启动 JAR，确认包含启动类、默认控制器、业务及平台 JAR、主 changelog 和业务 changelog。`bash -n scripts/build.sh scripts/start.sh scripts/stop.sh` 和 `git diff --check` 退出码 0。
- 未验证：未启动应用或连接数据库；未运行前端安装和构建。业务模块当前为空，Maven 报告空 JAR 警告。
