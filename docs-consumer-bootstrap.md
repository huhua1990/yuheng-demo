# yuheng-demo 消费端 bootstrap

## 边界

`yuheng-demo` 只声明 `com.yuheng:yuheng-server`，由该稳定入口传递 framework、system 和 infra。启动类、运行配置、数据库连接、数据库迁移入口和未来业务模块仍由消费端维护。

当前 Java 包名保留 `cn.iocoder.yudao`，这是首版兼容策略，避免把 Maven 坐标迁移、包名迁移和 API 迁移放在同一变更中。

## 构建

```bash
mvn -DskipTests package
```

发布环境需要把 `com.yuheng:yuheng-server:${yuheng.version}` 指向组织 Maven 仓库；本地开发可以先从 `yuheng-core` 执行 `mvn install -DskipTests`。
