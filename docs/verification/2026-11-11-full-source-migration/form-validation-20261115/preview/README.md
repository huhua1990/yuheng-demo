# 表单浏览器组件验收

该预览复用工作区已安装依赖和 Core 已构建 dist，无后端或数据库。请求仅由内存适配器计数。它不能替代完整 Demo 联调或消费端版本升级验收。

在工作区根目录，用支持当前 Vite 的已安装 Node 运行：

```sh
node yuheng-demo/docs/verification/2026-11-11-full-source-migration/form-validation-20261115/preview/serve.mjs
```

仅监听127.0.0.1:5193，端口占用会失败。打开页面后可检查公告/岗位空提交、合法新增，以及勾选“模拟请求失败”后的错误传播；不要将计数认作真实业务写入。结束时Ctrl+C。

Dialog、Editor、Element Plus与表单为真实组件；图标显示为本地字符。字典为预览数据；Core dist仅用于共享Store导出，需在Core UI源码更新后按既有构建命令生成。预览读取源码SFC，并不修改消费端安装包。浏览器窄屏检查发现的内部溢出仍未修复，见上一层证据。
