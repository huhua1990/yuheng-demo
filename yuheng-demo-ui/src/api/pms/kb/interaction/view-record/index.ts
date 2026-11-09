import request from 'yuheng-ui/compat/config/axios/index.ts'
import type { PmsKnowledgeInteractionItemVO } from '@/api/pms/kb/interaction/types.ts'

// PMS 知识最近浏览 VO
export interface PmsKnowledgeRecentListVO {
  todayItems: PmsKnowledgeInteractionItemVO[] // 今天浏览列表
  yesterdayItems: PmsKnowledgeInteractionItemVO[] // 昨天浏览列表
  recent30DayItems: PmsKnowledgeInteractionItemVO[] // 更早 30 天浏览列表
}

// 查询最近浏览列表
export const getKnowledgeRecentViewRecordList = (libraryId?: number) => {
  return request.get<PmsKnowledgeRecentListVO>({
    url: '/pms/kb/view-record/recent-list',
    params: { libraryId }
  })
}

export type { PmsKnowledgeInteractionItemVO } from '@/api/pms/kb/interaction/types.ts'
