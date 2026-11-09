import SpuSelect from '@/views/mall/promotion/components/SpuSelect.vue'
import SpuAndSkuList from '@/views/mall/promotion/components/SpuAndSkuList.vue'
import { PropertyAndValues } from '@/views/mall/product/spu/components/index.ts'

type SpuProperty<T> = {
  spuId: number
  spuDetail: T
  propertyList: PropertyAndValues[]
}

/**
 * 提供商品活动商品选择通用组件
 */
export { SpuSelect, SpuProperty }
export type { SpuAndSkuList }
