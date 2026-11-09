import request from 'yuheng-ui/compat/config/axios/index.ts'
import type { HrmEmployeeFieldConfigVO } from '@/api/hrm/employee/config/index.ts'

// 获得当前员工的档案字段配置
export const getEmployeeFieldConfigList = async () => {
  return await request.get<HrmEmployeeFieldConfigVO[]>({
    url: '/hrm/portal/employee/field-config/list'
  })
}
