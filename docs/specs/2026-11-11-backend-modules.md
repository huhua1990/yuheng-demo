# 后端 Maven 模块拆分

- workId: 2026-11-11-backend-modules
- codeVersion: b9c49067ffc7e8efe2e884a7fe26899ab92f175e，含既有未提交变更
- governanceVersion: 0.2.0；knowledgeVersion: 0.1.0
- 授权来源：用户要求参考 demo 拆分后端 POM、业务层和 server 层。
- PHASE_GATE: 规格与计划按上述实施授权冻结；implementationAllowed: true；原型不适用。
- 边界：仅调整 Maven 结构、现有后端文件位置及相关脚本和文档；不修改业务行为、数据库迁移内容、权限、租户或前端。

REQ-1 / AC-1：根聚合后端，后端聚合业务和启动模块，启动模块依赖业务模块及版本化平台入口。T-1：配置 POM 并检查 reactor。

REQ-2 / AC-2：现有启动入口、控制器、配置和迁移资源随启动模块打包，生命周期脚本引用新 JAR。T-2：迁移文件并运行构建及脚本检查。

验证：模块结构检查、Maven package 和既有生命周期测试；不启动连接真实数据库的应用。回退方式：还原本任务相关 POM、文件位置及脚本路径，保留原有未提交改动。
