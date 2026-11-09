# Yuheng Demo 部署脚本使用指南

## 一、脚本功能

`yuheng-demo.sh` 是一个功能完整的Shell脚本，用于管理 yuheng-demo 项目的前后端构建、启动、停止等操作。

## 二、快速开始

### 2.1 查看帮助

```bash
./yuheng-demo.sh help
```

### 2.2 完整构建和启动

```bash
# 第一步: 构建前后端
./yuheng-demo.sh build

# 第二步: 启动服务
./yuheng-demo.sh start
```

### 2.3 停止服务

```bash
./yuheng-demo.sh stop
```

## 三、命令详解

### 3.1 完整操作命令

| 命令 | 功能 | 说明 |
|------|------|------|
| `build` | 构建前后端 | 执行 Maven 和 pnpm 构建 |
| `start` | 启动所有服务 | 启动后端 + 前端开发服务器 |
| `stop` | 停止所有服务 | 停止后端和前端服务 |
| `restart` | 重启所有服务 | 先停止再启动 |
| `status` | 查看服务状态 | 显示运行状态和进程信息 |
| `clean` | 清理构建产物 | 删除 target、dist、node_modules 等 |

### 3.2 后端专用命令

| 命令 | 功能 |
|------|------|
| `build:backend` | 仅构建后端 |
| `start:backend` | 仅启动后端 |
| `stop:backend` | 仅停止后端 |
| `restart:backend` | 重启后端 |
| `status:backend` | 查看后端状态 |
| `logs` | 查看实时日志（默认100行）|
| `logs 500` | 查看指定行数的日志 |

### 3.3 前端专用命令

| 命令 | 功能 |
|------|------|
| `build:frontend` | 仅构建前端（生产构建）|
| `start:frontend` | 启动前端开发服务器 |
| `dev:frontend` | 同 start:frontend |

## 四、环境变量配置

可以通过环境变量自定义配置：

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `SPRING_PROFILE` | `local` | Spring 配置文件 (local/dev/prod) |
| `SERVER_PORT` | `48080` | 后端服务端口 |
| `FRONTEND_PORT` | `5173` | 前端开发端口 |
| `JVM_OPTS` | `-Xms512m -Xmx1024m ...` | JVM 内存参数 |

### 使用示例

```bash
# 使用生产环境配置启动
SPRING_PROFILE=prod SERVER_PORT=8080 ./yuheng-demo.sh start:backend

# 调整 JVM 内存
JVM_OPTS="-Xms1g -Xmx2g" ./yuheng-demo.sh start:backend

# 修改前端开发端口
FRONTEND_PORT=3000 ./yuheng-demo.sh dev:frontend
```

## 五、常见使用场景

### 5.1 开发环境

```bash
# 方式一: 后端和前端分别启动（推荐）
./yuheng-demo.sh build:backend
./yuheng-demo.sh start:backend

# 另开一个终端
./yuheng-demo.sh dev:frontend

# 方式二: 一键启动（前端会占用当前终端）
./yuheng-demo.sh build
./yuheng-demo.sh start
```

### 5.2 后端调试

```bash
# 启动后端
./yuheng-demo.sh start:backend

# 查看实时日志
./yuheng-demo.sh logs

# 查看服务状态
./yuheng-demo.sh status

# 重启后端
./yuheng-demo.sh restart:backend
```

### 5.3 生产部署

```bash
# 1. 构建所有
./yuheng-demo.sh build

# 2. 仅启动后端（前端通过 Nginx 代理）
SPRING_PROFILE=prod SERVER_PORT=8080 ./yuheng-demo.sh start:backend

# 3. 前端静态文件在 yuheng-demo-ui/dist 目录
# 配置 Nginx 指向该目录
```

### 5.4 清理和重建

```bash
# 清理所有构建产物
./yuheng-demo.sh clean

# 重新构建
./yuheng-demo.sh build
```

## 六、文件说明

### 6.1 生成的文件

| 文件/目录 | 说明 |
|----------|------|
| `target/yuheng-demo.jar` | 后端可执行 JAR 包 |
| `yuheng-demo-ui/dist/` | 前端生产构建产物 |
| `yuheng-demo.pid` | 后端进程 PID 文件 |
| `logs/application.log` | 后端应用日志 |

### 6.2 项目结构

```
yuheng-demo/
├── yuheng-demo.sh          # 管理脚本
├── pom.xml                 # Maven 配置
├── src/                    # 后端源码
│   └── main/
│       ├── java/
│       └── resources/
│           ├── application.yaml
│           ├── application-local.yaml
│           └── application-dev.yaml
├── target/                 # 后端构建产物
│   └── yuheng-demo.jar
├── yuheng-demo-ui/         # 前端项目
│   ├── package.json
│   ├── src/
│   ├── dist/              # 前端构建产物
│   └── vendor/
│       └── yuheng-ui-*.tgz
├── logs/                   # 日志目录
└── yuheng-demo.pid        # 进程 PID
```

## 七、前置条件

### 7.1 必需工具

- **Java 17+**: 后端运行环境
- **Maven 3.6+**: 后端构建工具
- **Node.js 18+**: 前端运行环境
- **pnpm**: 前端包管理器

### 7.2 检查工具

```bash
# 检查 Java
java -version

# 检查 Maven
mvn -version

# 检查 Node
node -v

# 检查 pnpm
pnpm -v

# 如果没有 pnpm，安装它
npm install -g pnpm
```

### 7.3 依赖准备

首次运行前，需要确保 yuheng-core 已构建：

```bash
# 构建 yuheng-core 后端
cd ../yuheng-core
mvn clean install -DskipTests

# 构建 yuheng-ui 前端包
cd yuheng-ui
pnpm install
pnpm run pack:local

# 复制到 demo 项目
cp vendor/yuheng-ui-0.1.0-SNAPSHOT.tgz ../yuheng-demo/yuheng-demo-ui/vendor/
```

## 八、故障排查

### 8.1 端口被占用

```bash
# 查看哪个进程占用了端口
lsof -i:48080  # 后端端口
lsof -i:5173   # 前端端口

# 杀死占用端口的进程
kill -9 <PID>
```

### 8.2 后端启动失败

```bash
# 查看详细日志
./yuheng-demo.sh logs 500

# 检查服务状态
./yuheng-demo.sh status

# 手动启动查看错误
cd target
java -jar yuheng-demo.jar
```

### 8.3 前端构建失败

```bash
# 清理 node_modules 重新安装
cd yuheng-demo-ui
rm -rf node_modules pnpm-lock.yaml
pnpm install

# 检查 yuheng-ui 依赖
ls -lh vendor/yuheng-ui-*.tgz
```

### 8.4 数据库连接失败

检查 `src/main/resources/application-local.yaml` 中的数据库配置：

```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/yuheng_demo?...
    username: root
    password: 123456
```

### 8.5 Maven 依赖问题

```bash
# 清理本地仓库缓存
mvn clean install -U

# 或手动删除
rm -rf ~/.m2/repository/com/yuheng
```

## 九、脚本工作原理

### 9.1 后端启动流程

1. 检查 JAR 文件是否存在
2. 检查端口是否被占用
3. 使用 `nohup` 后台启动 Spring Boot 应用
4. 将 PID 写入 `yuheng-demo.pid`
5. 等待健康检查接口响应 (最多60秒)
6. 输出日志文件路径

### 9.2 前端开发服务器

- 使用 Vite 开发服务器
- 支持热更新 (HMR)
- 默认端口 5173
- 会占用当前终端（使用 Ctrl+C 停止）

### 9.3 进程管理

- 后端通过 PID 文件管理
- 停止时先尝试正常终止 (SIGTERM)
- 如果30秒内未停止，强制杀死 (SIGKILL)

## 十、生产环境部署建议

### 10.1 使用 systemd 管理后端

创建 `/etc/systemd/system/yuheng-demo.service`:

```ini
[Unit]
Description=Yuheng Demo Backend Service
After=network.target

[Service]
Type=simple
User=yuheng
WorkingDirectory=/opt/yuheng-demo
ExecStart=/usr/bin/java -Xms1g -Xmx2g -Dspring.profiles.active=prod -jar /opt/yuheng-demo/target/yuheng-demo.jar
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

使用：
```bash
sudo systemctl start yuheng-demo
sudo systemctl enable yuheng-demo
sudo systemctl status yuheng-demo
```

### 10.2 使用 Nginx 代理前端

```nginx
server {
    listen 80;
    server_name demo.yuheng.com;

    # 前端静态文件
    root /opt/yuheng-demo/yuheng-demo-ui/dist;
    index index.html;

    # 前端路由
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /admin-api/ {
        proxy_pass http://localhost:8080/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 10.3 日志管理

使用 logrotate 管理日志：

```bash
# /etc/logrotate.d/yuheng-demo
/opt/yuheng-demo/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 yuheng yuheng
}
```

## 十一、常见问题 FAQ

### Q1: 第一次运行需要什么准备？

A: 需要先构建 yuheng-core 的后端和前端依赖，参考第七章节。

### Q2: 如何查看后端是否正常运行？

A: 使用 `./yuheng-demo.sh status` 或访问 `http://localhost:48080/actuator/health`

### Q3: 前端页面打不开怎么办？

A: 检查：
- 前端开发服务器是否启动 (端口 5173)
- 后端 API 是否正常 (端口 48080)
- 浏览器控制台是否有错误

### Q4: 如何修改数据库配置？

A: 编辑 `src/main/resources/application-local.yaml`，修改 datasource 部分

### Q5: 生产环境应该使用哪个配置文件？

A: 使用 `SPRING_PROFILE=prod` 启动，并确保有 `application-prod.yaml` 配置文件

## 十二、脚本源码位置

脚本已保存在项目根目录：
```
/Users/huhua/study/ai/yuheng/yuheng-demo/yuheng-demo.sh
```

可以根据实际需求修改脚本中的配置参数。
