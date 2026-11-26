import type { Component } from 'vue'

interface RequestOptions {
  url: string
  params?: any
  data?: any
  headers?: Record<string, any>
  responseType?: string
  headersType?: string
}

interface RequestClient {
  get<T = any>(options: RequestOptions): Promise<T>
  post<T = any>(options: RequestOptions): Promise<T>
  put<T = any>(options: RequestOptions): Promise<T>
  delete<T = any>(options: RequestOptions): Promise<T>
  download(options: RequestOptions): Promise<Blob>
}

declare const request: RequestClient

export default request

export const CardTitle: Component
export const DescriptionsItemLabel: Component
export const FilePreview: Component
export const Qrcode: Component
export const createImageViewer: (...args: any[]) => any

export const DICT_TYPE: Record<string, string>
export const CommonStatusEnum: Record<string, any>
export const DeliveryTypeEnum: Record<string, any>
export const CouponTemplateValidityTypeEnum: Record<string, any>
export const CouponTemplateTakeTypeEnum: Record<string, any>
export const PromotionDiscountTypeEnum: Record<string, any>
export const PayChannelEnum: Record<string, any>
export const PayDisplayModeEnum: Record<string, any>
export const PayOrderStatusEnum: Record<string, any>
export const ErpBizType: Record<string, number>

export const defaultProps: Record<string, any>
export const handleTree: (...args: any[]) => any
export const useTagsViewStore: (...args: any[]) => any
export const useUserStore: (...args: any[]) => any
export const useMessage: (...args: any[]) => any

export const getAccessToken: (...args: any[]) => any
export const getCurrentUserId: (...args: any[]) => any
export const getTenantId: (...args: any[]) => any
export const formatFileSize: (...args: any[]) => any
export const getFileNameFromUrl: (...args: any[]) => any
export const getAllPageItems: <T = any>(
  fetchPage: (pageNo: number, pageSize: number) => Promise<{ list: T[]; total?: number } | PageResult<T>>,
  pageSize?: number
) => Promise<T[]>
export const propTypes: Record<string, any>
export const isNullOrUnDef: (val: unknown) => val is null | undefined

export const getAreaTree: (...args: any[]) => any
export const getAreaByIp: (...args: any[]) => any
export interface UserVO {
  id?: number
  nickname?: string
  mobile?: string
  avatar?: string
}
export interface DictDataType {
  dictType: string
  label: string
  value: string | number | boolean
  colorType?: string
  cssClass?: string
}

export const getDictOptions: (...args: any[]) => any
export const getIntDictOptions: (...args: any[]) => any
export const getStrDictOptions: (...args: any[]) => any
export const getDictLabel: (...args: any[]) => string
export const dateFormatter: (...args: any[]) => any
export const dateFormatter2: (...args: any[]) => any
export const formatDate: (...args: any[]) => any
export const formatNullableDate: (...args: any[]) => any
export const defaultShortcuts: any[]
export const getSumValue: (...args: any[]) => any
export const erpCountInputFormatter: (...args: any[]) => any
export const erpCountTableColumnFormatter: (...args: any[]) => any
export const erpPriceInputFormatter: (...args: any[]) => any
export const erpPriceTableColumnFormatter: (...args: any[]) => any
export const erpPriceMultiply: (...args: any[]) => any
export const floatToFixed2: (...args: any[]) => any
export const fenToYuan: (...args: any[]) => any
export const yuanToFen: (...args: any[]) => any
export const convertToInteger: (...args: any[]) => any
export const formatToFraction: (...args: any[]) => any
export const checkPermi: (...args: any[]) => any
export const onActivated: typeof import('vue').onActivated
export const getSimpleUserList: (...args: any[]) => any
