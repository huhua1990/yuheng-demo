import request from 'yuheng-ui/compat/config/axios/index.ts'
import type { HrmEmployeeCertificateVO } from '@/api/hrm/employee/certificate/index.ts'

// 获得当前员工的证书列表
export const getEmployeeCertificateList = async () => {
  return await request.get<HrmEmployeeCertificateVO[]>({
    url: '/hrm/portal/employee/certificate/list'
  })
}
