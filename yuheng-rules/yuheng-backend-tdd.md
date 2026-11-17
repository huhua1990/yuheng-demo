# Yuheng 后端 TDD 规则

适用范围：所有 Yuheng 后端编码任务，包括 controller、service、mapper、DTO/VO 边界调整以及后端缺陷修复。

---

## 强制规则

1. **后端实现必须先写测试，再写生产代码**
   - 没有 failing test，不得开始实现。

2. **必须先运行目标测试并看到红灯**
   - 失败原因必须对准本次要实现的能力缺口。
   - 不能用"编译不过""环境没起"冒充红灯。

3. **只有在红灯成立后，才允许写最小实现代码直到绿灯**
   - 实现完成后必须重跑同一组测试，确认转绿。

4. **API smoke test、联调或人工点点看，不能替代 TDD**
   - 这些属于补充验证，不属于实现前置条件。

5. **如果当前任务缺少测试入口，也不能直接跳过 TDD**
   - 应先补测试入口、补计划，或明确说明阻塞并停止声称"已完成实现"。

---

## 输出要求

- 说明本次先写的是哪一个测试文件或测试用例。
- 说明红灯命令和失败点。
- 说明绿灯命令和通过结果。

---

## 示例

### 步骤 1: 写测试（红灯）

```java
@Test
void testCreateUser() {
    User user = new User();
    user.setUsername("test");
    
    // 期望：创建成功
    Long userId = userService.create(user);
    
    assertNotNull(userId);
}
```

执行：`mvn test -Dtest=UserServiceTest#testCreateUser`  
结果：❌ 红灯（方法未实现）

### 步骤 2: 写实现（绿灯）

```java
public Long create(User user) {
    userMapper.insert(user);
    return user.getId();
}
```

执行：`mvn test -Dtest=UserServiceTest#testCreateUser`  
结果：✅ 绿灯（测试通过）

---

**规则版本**: v1.0  
**更新时间**: 2026-11-09
