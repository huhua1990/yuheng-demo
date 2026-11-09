import request from 'yuheng-ui/compat/config/axios/index.ts'

export interface BargainRecordVO {
  id: number
  activityId: number
  userId: number
  spuId: number
  skuId: number
  bargainFirstPrice: number
  bargainPrice: number
  status: number
  orderId: number
  endTime: Date
}

// 查询砍价记录列表
export const getBargainRecordPage = async (params) => {
  return await request.get({ url: `/promotion/bargain-record/page`, params })
}
