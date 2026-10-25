# yuheng-demo

Yuheng 的消费端 bootstrap。运行时代码、配置、数据库迁移和业务扩展放在本仓库；平台基础能力通过 Maven 版本依赖消费：

```text
com.yuheng:yuheng-server:${yuheng.version}
```

消费端不引用 `yuheng-core` 源码目录，也不直接依赖 core 内部模块作为稳定入口。Java 包名首版继续使用 `cn.iocoder.yudao`，保持现有接口、表结构和扫描路径兼容。

## 本地启动

先在 `yuheng-core` 发布到本地 Maven 仓库，再构建本项目：

```bash
mvn -DskipTests install -f ../yuheng-core/pom.xml
mvn spring-boot:run
```

默认配置使用 `local` profile，数据库、Redis 和其他基础设施地址见 `src/main/resources/application-local.yaml`。
