# 日志规范

---

## 强制规则

- 统一使用 `@Slf4j`，禁止 `System.out` / `System.err`
- 日志级别按标准 Slf4j 使用（ERROR/WARN/INFO/DEBUG）
- 使用占位符，不拼接字符串；不记录密码、Token、身份证等敏感数据
- 关键链路必须记录起止结果：Controller 入参/出参、关键 Service 操作、外部调用失败原因
- 日志内容含业务主键、操作人、关键状态以便排障

---

## 示例

### ✅ 正确写法

```java
@Slf4j
@RestController
public class UserController {
    
    @PostMapping("/create")
    public CommonResult<Long> create(@RequestBody UserCreateReqDTO reqDTO) {
        log.info("[创建用户] 开始处理请求");
        
        try {
            Long userId = userService.create(reqDTO);
            log.info("[创建用户] 成功，用户ID: {}", userId);
            return CommonResult.success(userId);
        } catch (Exception e) {
            log.error("[创建用户] 失败", e);
            throw e;
        }
    }
}
```

### ❌ 错误写法

```java
// 禁止使用 System.out
System.out.println("创建用户: " + reqDTO);

// 禁止字符串拼接
log.info("创建用户: " + reqDTO);

// 禁止记录敏感信息
log.info("用户密码: {}", password);
```

---

## 日志级别

| 级别 | 说明 | 示例 |
|------|------|------|
| ERROR | 系统错误，需要立即处理 | 数据库连接失败、外部接口调用失败 |
| WARN | 警告信息，需要关注 | 参数校验失败、业务规则不满足 |
| INFO | 关键业务流程 | 用户登录、订单创建、支付成功 |
| DEBUG | 调试信息 | 方法入参、SQL 语句、中间变量 |

---

**规则版本**: v1.0  
**更新时间**: 2026-11-09
