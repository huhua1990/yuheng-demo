import request from 'yuheng-ui/compat/config/axios'

export interface AddressVO {
  id: number
  name: string
  mobile: string
  areaId: number
  detailAddress: string
  defaultStatus: boolean
}

// 查询用户收件地址列表
export const getAddressList = async (params: PageParam & Record<string, any>) => {
  return await request.get({ url: `/member/address/list`, params })
}
