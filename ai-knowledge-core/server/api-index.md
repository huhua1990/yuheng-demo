# Yuheng Server API 索引

本文档提供 Yuheng 后端所有 REST API 的快速索引。

---

## 认证授权

### 登录认证

```http
POST /system/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}

Response:
{
  "code": "0",
  "data": {
    "accessToken": "eyJhbGc...",
    "refreshToken": "eyJhbGc...",
    "expiresTime": 1699999999,
    "userId": 1
  }
}
```

### 刷新令牌

```http
POST /system/auth/refresh-token
Content-Type: application/json

{
  "refreshToken": "eyJhbGc..."
}
```

### 登出

```http
POST /system/auth/logout
Authorization: Bearer {accessToken}
```

---

## 用户管理

### 用户分页查询

```http
POST /system/user/page
Content-Type: application/json

{
  "pageNo": 1,
  "pageSize": 10,
  "username": "admin"
}
```

### 获取用户详情

```http
GET /system/user/get?id=1
```

### 创建用户

```http
POST /system/user/create
Content-Type: application/json

{
  "username": "test",
  "password": "123456",
  "nickname": "测试用户",
  "mobile": "18888888888",
  "email": "test@example.com",
  "deptId": 1,
  "postIds": [1],
  "roleIds": [2]
}
```

### 更新用户

```http
PUT /system/user/update
Content-Type: application/json

{
  "id": 1,
  "nickname": "新昵称",
  "mobile": "18888888888"
}
```

### 删除用户

```http
DELETE /system/user/delete?id=1
```

---

## 角色管理

### 角色分页查询

```http
POST /system/role/page
Content-Type: application/json

{
  "pageNo": 1,
  "pageSize": 10,
  "name": "管理员"
}
```

### 获取精简角色列表

```http
GET /system/role/list-all-simple
```

### 创建角色

```http
POST /system/role/create
Content-Type: application/json

{
  "name": "测试角色",
  "code": "test",
  "sort": 1,
  "status": 0,
  "remark": "测试角色"
}
```

### 更新角色

```http
PUT /system/role/update
Content-Type: application/json

{
  "id": 1,
  "name": "新角色名"
}
```

### 删除角色

```http
DELETE /system/role/delete?id=1
```

---

## 菜单管理

### 获取菜单列表

```http
GET /system/menu/list
```

### 获取菜单详情

```http
GET /system/menu/get?id=1
```

### 创建菜单

```http
POST /system/menu/create
Content-Type: application/json

{
  "name": "用户管理",
  "permission": "system:user:list",
  "type": 2,
  "sort": 1,
  "parentId": 0,
  "path": "/system/user",
  "icon": "user",
  "component": "system/user/index",
  "status": 0
}
```

### 更新菜单

```http
PUT /system/menu/update
Content-Type: application/json

{
  "id": 1,
  "name": "新菜单名"
}
```

### 删除菜单

```http
DELETE /system/menu/delete?id=1
```

---

## 部门管理

### 获取部门列表

```http
GET /system/dept/list
```

### 获取部门详情

```http
GET /system/dept/get?id=1
```

### 创建部门

```http
POST /system/dept/create
Content-Type: application/json

{
  "name": "研发部",
  "parentId": 0,
  "sort": 1,
  "leaderUserId": 1,
  "phone": "18888888888",
  "email": "dev@example.com",
  "status": 0
}
```

---

## 字典管理

### 字典类型分页

```http
POST /system/dict-type/page
Content-Type: application/json

{
  "pageNo": 1,
  "pageSize": 10,
  "name": "系统状态"
}
```

### 字典数据列表

```http
GET /system/dict-data/list?dictType=sys_common_status
```

---

## 参数配置

### 参数分页

```http
POST /system/config/page
Content-Type: application/json

{
  "pageNo": 1,
  "pageSize": 10,
  "name": "系统配置"
}
```

### 根据 key 获取参数值

```http
GET /system/config/get-value-by-key?key=sys.user.initPassword
```

---

## 操作日志

### 操作日志分页

```http
POST /system/operate-log/page
Content-Type: application/json

{
  "pageNo": 1,
  "pageSize": 10,
  "module": "用户管理"
}
```

---

## 登录日志

### 登录日志分页

```http
POST /system/login-log/page
Content-Type: application/json

{
  "pageNo": 1,
  "pageSize": 10,
  "userIp": "127.0.0.1"
}
```

---

## 文件管理

### 文件上传

```http
POST /infra/file/upload
Content-Type: multipart/form-data

file: <binary>
path: /avatar
```

### 获取文件

```http
GET /infra/file/get/{id}
```

### 删除文件

```http
DELETE /infra/file/delete?id=1
```

---

## 代码生成

### 数据库表分页

```http
POST /infra/codegen/table/page
Content-Type: application/json

{
  "pageNo": 1,
  "pageSize": 10,
  "tableName": "sys_user"
}
```

### 创建代码生成

```http
POST /infra/codegen/create-list
Content-Type: application/json

{
  "tableNames": ["sys_user", "sys_role"]
}
```

### 预览代码

```http
GET /infra/codegen/preview?tableId=1
```

### 下载代码

```http
GET /infra/codegen/download?tableId=1
```

---

## 统一响应格式

所有 API 统一返回格式：

```json
{
  "code": "0",
  "data": {},
  "msg": "操作成功"
}
```

- `code`: "0" 表示成功，其他表示失败
- `data`: 返回数据
- `msg`: 提示信息

### 分页响应格式

```json
{
  "code": "0",
  "data": {
    "list": [],
    "total": 100
  }
}
```

---

**版本**: 0.1.0-SNAPSHOT  
**更新时间**: 2026-11-09
