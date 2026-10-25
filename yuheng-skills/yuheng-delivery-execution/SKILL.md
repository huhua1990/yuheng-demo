---
id: yuheng-delivery-execution
version: 0.1.0
entry: public
---

# yuheng-delivery-execution

按计划执行交付，遵循测试先行、最小变更和证据优先。

每个实现循环都要：

1. 先写能表达行为的失败测试；
2. 实现最小代码使测试通过；
3. 执行受影响的 API、UI、数据库和权限验证；
4. 记录失败、修复、回滚和 self-review 结果；
5. 把证据保存到消费端 `docs/verification/`。

没有验证证据时不得声称交付完成。
