import request from 'yuheng-ui/compat/config/axios/index.ts'

export interface ImManagerFriendRequestVO {
  id: number
  fromUserId: number
  fromNickname?: string
  toUserId: number
  toNickname?: string
  applyContent?: string
  displayName?: string
  addSource?: number
  handleResult: number
  handleContent?: string
  handleTime?: Date
  createTime: Date
}

// 获得好友申请分页
export const getManagerFriendRequestPage = (params: PageParam) => {
  return request.get({ url: '/im/manager/friend-request/page', params })
}
