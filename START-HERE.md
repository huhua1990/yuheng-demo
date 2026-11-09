# 完整启动指南

请按照以下步骤操作：

## 第一步：确保后端运行

```bash
cd /Users/huhua/study/ai/yuheng/yuheng-demo
./yuheng-demo.sh stop:backend
./yuheng-demo.sh start:backend
```

等待看到 "后端服务启动成功！" 的提示。

## 第二步：启动前端（新终端）

打开**新的终端窗口**，执行：

```bash
cd /Users/huhua/study/ai/yuheng/yuheng-demo/yuheng-demo-ui
pnpm run dev
```

看到 Vite 启动信息后（显示 Local: http://127.0.0.1:3000/），前端就启动成功了。

## 第三步：访问页面

在浏览器打开: **http://127.0.0.1:3000/**

应该能看到登录页面。
