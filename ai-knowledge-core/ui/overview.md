# Yuheng UI 前端框架概览

## 框架定位

`yuheng-ui` 是 Yuheng 平台的前端核心框架，提供标准的管理后台页面能力与运行时上下文。

---

## 技术栈

- **Vue**: 3.x
- **TypeScript**: 5.x
- **Vite**: 5.x
- **Element Plus**: 2.x
- **Pinia**: 2.x
- **Vue Router**: 4.x

---

## 核心能力

### 1. 布局系统

- **AppLayout**: 标准管理后台布局
- **顶部导航**: 用户信息、通知、设置
- **侧边菜单**: 动态菜单树
- **标签页**: 多标签页导航
- **面包屑**: 当前位置导航

### 2. 路由系统

- **文件路由**: `views/{group}/{module}/index.vue` → `/{group}/{module}`
- **动态路由**: 基于菜单权限动态生成
- **路由守卫**: 登录验证、权限验证

### 3. 状态管理（Pinia Stores）

| Store | 说明 |
|-------|------|
| `useUserStore` | 用户信息、当前工作站 |
| `useMenuStore` | 菜单列表、菜单权限 |
| `useRoleStore` | 角色列表、角色权限 |
| `useDeptStore` | 部门树 |
| `useDictStore` | 字典数据 |
| `useConfigStore` | 系统参数 |

### 4. 通用组件

- **表格**: `wg-table` - 增强表格组件
- **表单**: `wg-form` - 表单组件
- **按钮**: `wg-button` - 按钮组件
- **图标**: `wg-icon` - 图标组件
- **对话框**: `wg-dialog` - 对话框组件
- **上传**: `wg-upload` - 文件上传组件

### 5. API 请求

```typescript
import { request } from 'yuheng-ui'

// GET 请求
const data = await request.get('/api/user/list')

// POST 请求
const result = await request.post('/api/user/create', { name: 'test' })

// 文件下载
await request.download('post', '/api/user/export', params, 'users.xlsx')
```

---

## 快速开始

### 1. 安装依赖

```bash
pnpm install yuheng-ui
```

### 2. 创建应用

```javascript
import { createApp } from 'vue'
import { createYuhengUI } from 'yuheng-ui'
import 'yuheng-ui/dist/style.css'

const app = createApp(App)

app.use(createYuhengUI({
  baseURL: 'http://localhost:8080',
  systemUri: '/demo'
}))

app.mount('#app')
```

### 3. 使用组件

```vue
<template>
  <wg-table :data="tableData" :columns="columns" />
</template>

<script setup>
import { ref } from 'vue'

const tableData = ref([])
const columns = [
  { prop: 'name', label: '姓名' },
  { prop: 'age', label: '年龄' }
]
</script>
```

---

## 核心 API

### Stores 使用

```typescript
import { useUserStore, useMenuStore } from 'yuheng-ui'

const userStore = useUserStore()
const menuStore = useMenuStore()

// 获取当前用户
const currentUser = userStore.currentUser

// 获取菜单列表
const menuList = menuStore.menuList
```

### 权限判断

```typescript
import { usePagePermission } from 'yuheng-ui'

const { hasPermission } = usePagePermission()

// 判断按钮权限
const canEdit = hasPermission('system:user:edit')
```

### 字典使用

```typescript
import { useDictStore } from 'yuheng-ui'

const dictStore = useDictStore()

// 获取字典列表
const statusList = dictStore.getDict('sys_common_status')

// 获取字典标签
const label = dictStore.getDictLabel('sys_common_status', '0')
```

---

## 页面开发规范

### 目录结构

```
views/
├── system/              # 系统管理
│   ├── user/           # 用户管理
│   │   └── index.vue
│   └── role/           # 角色管理
│       └── index.vue
└── demo/               # 示例模块
    └── example/
        └── index.vue
```

### 标准页面模板

```vue
<template>
  <div class="app-container">
    <!-- 查询条件 -->
    <el-form :model="queryForm" inline>
      <el-form-item label="用户名">
        <el-input v-model="queryForm.username" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleQuery">查询</el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- 操作按钮 -->
    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="primary" @click="handleAdd">新增</el-button>
      </el-col>
    </el-row>

    <!-- 数据表格 -->
    <wg-table
      :data="tableData"
      :columns="columns"
      @selection-change="handleSelectionChange"
    />

    <!-- 分页 -->
    <pagination
      v-model:page="queryForm.pageNo"
      v-model:limit="queryForm.pageSize"
      :total="total"
      @pagination="getList"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { request } from 'yuheng-ui'

const queryForm = ref({
  pageNo: 1,
  pageSize: 10,
  username: ''
})

const tableData = ref([])
const total = ref(0)

const columns = [
  { prop: 'username', label: '用户名' },
  { prop: 'nickname', label: '昵称' },
  { prop: 'status', label: '状态' }
]

const getList = async () => {
  const res = await request.post('/system/user/page', queryForm.value)
  if (res.code === '0') {
    tableData.value = res.data.list
    total.value = res.data.total
  }
}

onMounted(() => {
  getList()
})
</script>
```

---

## 相关资源

- **源码**: https://github.com/huhua1990/yuheng-ui
- **组件文档**: 待补充
- **示例项目**: yuheng-demo-ui

---

**版本**: 0.1.0-SNAPSHOT
**更新时间**: 2026-11-09
