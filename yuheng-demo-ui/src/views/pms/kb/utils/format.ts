import { DICT_TYPE, getDictLabel } from 'yuheng-ui/compat/utils/dict.ts'
import { formatFileSize } from 'yuheng-ui/compat/utils/file.ts'
import { PmsKnowledgeDocumentStatus, PmsKnowledgeObjectType } from '@/views/pms/kb/utils/constants.ts'

/** 格式化知识对象类型名称 */
export function getKnowledgeObjectTypeName(type: number) {
  return getDictLabel(DICT_TYPE.PMS_KNOWLEDGE_OBJECT_TYPE, type)
}

/** 获得知识对象图标 */
export function getKnowledgeObjectIcon(type: number) {
  return (
    {
      [PmsKnowledgeObjectType.LIBRARY]: 'ep:notebook',
      [PmsKnowledgeObjectType.FOLDER]: 'ep:folder',
      [PmsKnowledgeObjectType.DOCUMENT]: 'ep:document',
      [PmsKnowledgeObjectType.FILE]: 'ep:paperclip'
    }[type] || 'ep:question-filled'
  )
}

/** 格式化知识库文档状态名称 */
export function getKnowledgeDocumentStatusName(status: number) {
  return {
    [PmsKnowledgeDocumentStatus.DRAFT]: '草稿',
    [PmsKnowledgeDocumentStatus.NORMAL]: '正常',
    [PmsKnowledgeDocumentStatus.TEMPLATE]: '模板'
  }[status]
}

/** 知识库文档状态对应的标签类型 */
export function getKnowledgeDocumentStatusTagType(status: number) {
  return status === PmsKnowledgeDocumentStatus.NORMAL ? 'success' : 'info'
}

/** 格式化知识库文件大小 */
export function formatKnowledgeFileSize(size?: number) {
  if (size === undefined || size === null || size < 0) return ''
  return formatFileSize(size)
}
