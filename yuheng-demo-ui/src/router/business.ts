import type { RouteRecordRaw } from 'vue-router'
import Home from '../views/Home/index.vue'

const ScheduleList = () => import('../views/oa/schedule/list/index.vue')
const ScheduleCalendar = () => import('../views/oa/schedule/calendar/index.vue')

export const businessRoutes: RouteRecordRaw[] = [
  { path: '/home', name: 'BusinessHome', component: Home, meta: { title: '业务首页' } },
  { path: '/oa/schedule/list', name: 'OaScheduleList', component: ScheduleList, meta: { title: '日程管理' } },
  { path: '/oa/schedule/calendar', name: 'OaScheduleCalendar', component: ScheduleCalendar, meta: { title: '日程日历' } }
]
