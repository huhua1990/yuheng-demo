# Yuheng API 响应契约

服务端 JSON envelope 为 `CommonResult<T>`：数字 `code`、`msg`、`data`，正常成功码为 `0`。分页对象为 `list` 和 `total`，请求分页为 `pageNo/pageSize`；禁止混入 `records`。

前端区分两个层级：

1. `createYuhengRequest` 的普通方法在请求层处理错误并解包 `data`，调用方直接读取业务结果，例如 `const page = await context.request.get<PageResult<Row>>(url, config)` 后用 `page.list/page.total`。
2. 使用原始响应方法或直接接口烟测时，按该方法的真实签名取得 envelope，再检查数字 `code`、`data`、`msg`；不把 envelope 和业务对象混用。

当前请求层兼容接受 `0` 与 `200`，这不代表新服务端接口应改为 `200`；修改兼容行为必须有规格与回归证据。不要在页面重复实现请求层的错误处理或 token 刷新。

异常、下载/上传和文件流按真实接口类型单独处理。错误返回复用已有错误码，不臆造 `CommonResult.error(String)` 或无参数成功方法。
