# Yuheng 前端代码规范

- 前端正式包名为 `yuheng-ui`；从其 `package.json`、消费端依赖和实际导出核实可用入口。业务代码复用消费端配置的请求实例，不直接引用 core 源码路径。
- 业务页面按现有路由/解析器约定组织；常规新页面可用 `views/{group}/{module}/index.vue`，不重排既有页面以迎合模板。子组件使用 PascalCase。
- 复用已有 API 模块和 TypeScript 类型；目标工程已有其他文件后缀时沿用，禁止为统一 `.js` 而改写。
- HTTP 复用应用安装后的 `context.request` 或目标模块注入的请求实例。`createYuhengRequest` 是实例工厂，不在每个页面重复创建 axios 或认证刷新链路。
- 普通请求已解包响应 `data`，页面使用业务对象，例如分页 `page.list/page.total`；直接访问原始响应时才按真实 envelope 判断 `code`。先核实返回类型，禁止二次解包。
- 框架实际导出 `useUserStore`、`usePermissionStore`、`useDictStore` 等；使用前检查公开导出和签名。不要假设有静态 `request`、`useMenuStore` 或其他 Athena 专有 hook。
- 登录、权限、字典预热、动态菜单复用现有 runtime/Store；菜单可见性不能替代后端权限验证。
- 样式沿用项目组件和变量，局部样式按既有作用域约定，避免覆盖框架全局基础样式。

页面逻辑变更补测试；交互用真实浏览器验收，保存 Console/Network、成功/失败路径和权限身份的实际证据。
