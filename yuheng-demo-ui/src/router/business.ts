import type { RouteRecordRaw } from 'vue-router'
import Home from '../views/Home/index.vue'

export const businessRoutes: RouteRecordRaw[] = [
  { path: '/home', name: 'BusinessHome', component: Home, meta: { title: '业务首页' } }
]
