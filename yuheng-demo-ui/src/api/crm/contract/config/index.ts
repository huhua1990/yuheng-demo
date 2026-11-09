import request from 'yuheng-ui/compat/config/axios/index.ts'

export interface ContractConfigVO {
  notifyEnabled?: boolean
  notifyDays?: number
}

// 获取合同配置
export const getContractConfig = async () => {
  return await request.get({ url: `/crm/contract-config/get` })
}

// 更新合同配置
export const saveContractConfig = async (data: ContractConfigVO) => {
  return await request.put({ url: `/crm/contract-config/save`, data })
}
