import request from 'yuheng-ui/compat/config/axios/index.ts'
import type { HrmEmployeeQuitInfoVO } from '@/api/hrm/employee/quit-info/index.ts'

// 获得当前员工的离职信息
export const getEmployeeQuitInfo = async () => {
  return await request.get<HrmEmployeeQuitInfoVO>({
    url: '/hrm/portal/employee/quit-info/get'
  })
}
