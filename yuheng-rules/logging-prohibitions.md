# 日志禁止事项规则

适用范围：所有 Java 代码中的日志语句

---

## 强制规则

### 1. 禁止使用 `System.out.println` 或 `System.err.println`

### 2. 禁止在高频循环里无条件打印日志

### 3. 禁止记录密码、Token、Cookie、完整证件号、完整手机号等敏感信息

### 4. 禁止吞掉异常却不记录堆栈

### 5. 禁止为了打印 DEBUG 日志执行昂贵计算而不做级别判断

---

## 错误示例

```java
System.out.println("订单创建成功");

for (Order order : orders) {
    log.debug("处理订单: {}", order.getOrderId());
}

log.info("用户登录, password={}", password);

try {
    doSomething();
} catch (Exception e) {
    log.error("发生异常: {}", e.getMessage());
}
```

---

## 正确示例

```java
log.info("订单创建成功, orderId={}", orderId);

if (log.isDebugEnabled()) {
    log.debug("批处理订单数量={}", orders.size());
}

log.info("用户登录, username={}", username);

try {
    doSomething();
} catch (Exception e) {
    log.error("执行失败", e);
    throw e;
}
```

---

## AI 检查清单

- 是否出现 `System.out` / `System.err`
- 是否在循环、定时任务、批处理明细里逐条打印
- 是否暴露敏感字段
- 是否只打异常 message 而没打堆栈
- 是否需要 `log.isDebugEnabled()`

---

**规则版本**: v1.0  
**更新时间**: 2026-11-09
