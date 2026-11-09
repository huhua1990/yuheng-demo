import request from 'yuheng-ui/compat/config/axios/index.ts'

export interface BargainHelpVO {
  id: number
  record: number
  userId: number
  reducePrice: number
  endTime: Date
}

// 查询砍价记录列表
export const getBargainHelpPage = async (params) => {
  return await request.get({ url: `/promotion/bargain-help/page`, params })
}
