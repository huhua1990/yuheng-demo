import request from 'yuheng-ui/compat/config/axios/index.ts'
import type { HrmEmployeeContactVO } from '@/api/hrm/employee/contact/index.ts'

// 获得当前员工的联系人列表
export const getEmployeeContactList = async () => {
  return await request.get<HrmEmployeeContactVO[]>({
    url: '/hrm/portal/employee/contact/list'
  })
}
