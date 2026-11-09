import request from 'yuheng-ui/compat/config/axios/index.ts'
import type { HrmHomeCalendarItemVO } from '@/api/hrm/home/index.ts'

export type { HrmHomeCalendarItemVO } from '@/api/hrm/home/index.ts'

// 获得员工端首页日历
export const getEmployeeHomeCalendar = async (params: { startDate: string; endDate: string }) => {
  return await request.get<HrmHomeCalendarItemVO[]>({
    url: '/hrm/portal/home/calendar',
    params
  })
}
