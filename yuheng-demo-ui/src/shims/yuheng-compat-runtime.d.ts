import type { Component } from 'vue'

interface RequestOptions {
  url: string
  params?: any
  data?: any
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
export const createImageViewer: (...args: any[]) => any

export const DICT_TYPE: Record<string, string>
export const CommonStatusEnum: Record<string, any>
export const DeliveryTypeEnum: Record<string, any>
export const CouponTemplateValidityTypeEnum: Record<string, any>
export const CouponTemplateTakeTypeEnum: Record<string, any>
export const PromotionDiscountTypeEnum: Record<string, any>
export const ErpBizType: Record<string, number>

export const defaultProps: Record<string, any>
export const handleTree: (...args: any[]) => any
export const useTagsViewStore: (...args: any[]) => any

export const getAreaTree: (...args: any[]) => any
export const getAreaByIp: (...args: any[]) => any
export interface UserVO {
  id?: number
  nickname?: string
  mobile?: string
  avatar?: string
}

export const getDictOptions: (...args: any[]) => any
export const getIntDictOptions: (...args: any[]) => any
export const getStrDictOptions: (...args: any[]) => any
export const dateFormatter: (...args: any[]) => any
export const dateFormatter2: (...args: any[]) => any
export const formatDate: (...args: any[]) => any
export const getSumValue: (...args: any[]) => any
export const erpCountInputFormatter: (...args: any[]) => any
export const erpCountTableColumnFormatter: (...args: any[]) => any
export const erpPriceInputFormatter: (...args: any[]) => any
export const erpPriceTableColumnFormatter: (...args: any[]) => any
export const erpPriceMultiply: (...args: any[]) => any
export const floatToFixed2: (...args: any[]) => any
export const fenToYuan: (...args: any[]) => any
export const convertToInteger: (...args: any[]) => any
export const formatToFraction: (...args: any[]) => any
export const checkPermi: (...args: any[]) => any
export const onActivated: typeof import('vue').onActivated
export const getSimpleUserList: (...args: any[]) => any
