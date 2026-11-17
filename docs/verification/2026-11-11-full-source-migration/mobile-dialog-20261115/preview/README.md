# Dialog宽度浏览器复验

在工作区根使用现有Node22运行：

```sh
node yuheng-demo/docs/verification/2026-11-11-full-source-migration/mobile-dialog-20261115/preview/serve.mjs
```

仅监听127.0.0.1:5194；请求为内存模拟，无数据库。复用已安装依赖、实际Core源码表单/Dialog/Editor及已构建dist的Store导出。结束Ctrl+C。

在320/390/768/1512视口打开公告，测量.el-dialog（不是role=dialog遮罩）、其scrollWidth和页脚按钮边界；1512保持800px。检查空提交、合法模拟新增、取消、百分比弹窗与全屏切换。Icon用本地button替代，未验上传和完整Demo登录流程。红灯与绿灯测量保存在上一层。
