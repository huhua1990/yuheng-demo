import request from 'yuheng-ui/compat/config/axios/index.ts'
import type { HrmEmployeeWorkExperienceVO } from '@/api/hrm/employee/work-experience/index.ts'

// 获得当前员工的工作经历列表
export const getEmployeeWorkExperienceList = async () => {
  return await request.get<HrmEmployeeWorkExperienceVO[]>({
    url: '/hrm/portal/employee/work-experience/list'
  })
}
