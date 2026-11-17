import type { RouteRecordRaw } from 'vue-router'
import Home from '../views/Home/index.vue'

// Keys match the component paths returned by the platform menu API.
const memberViewComponents = import.meta.glob('../views/member/**/*.{vue,tsx}')
const erpViewComponents = import.meta.glob('../views/erp/**/*.{vue,tsx}')

export const businessViewComponents = {
  ...memberViewComponents,
  ...erpViewComponents
}

export const businessRoutes: RouteRecordRaw[] = [
  { path: '/business/home', name: 'BusinessHome', component: Home, meta: { title: '业务首页' } },
  {
    path: '/member/user/detail/:id',
    name: 'MemberUserDetail',
    component: () => import('../views/member/user/detail/index.vue'),
    meta: { title: '会员详情', noCache: true, hidden: true }
  }
]
