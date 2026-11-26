import type { RouteRecordRaw } from 'vue-router'
import Home from '../views/Home/index.vue'

// Consumers register views for selected business templates here.
export const businessViewComponents: Record<string, () => Promise<unknown>> = {}

export const publicBusinessRoutes: RouteRecordRaw[] = []

export const businessRoutes: RouteRecordRaw[] = [
  { path: '/business/home', name: 'BusinessHome', component: Home, meta: { title: '业务首页' } }
]
