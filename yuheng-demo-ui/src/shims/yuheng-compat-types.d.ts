import type { Component, ComputedRef, Ref } from 'vue'

declare global {
  const computed: typeof import('vue').computed
  const defineComponent: typeof import('vue').defineComponent
  const h: typeof import('vue').h
  const nextTick: typeof import('vue').nextTick
  const onBeforeMount: typeof import('vue').onBeforeMount
  const onBeforeUnmount: typeof import('vue').onBeforeUnmount
  const onActivated: typeof import('vue').onActivated
  const onMounted: typeof import('vue').onMounted
  const onUnmounted: typeof import('vue').onUnmounted
  const provide: typeof import('vue').provide
  const reactive: typeof import('vue').reactive
  const ref: typeof import('vue').ref
  const toRef: typeof import('vue').toRef
  const toRefs: typeof import('vue').toRefs
  const unref: typeof import('vue').unref
  const useAttrs: typeof import('vue').useAttrs
  const useSlots: typeof import('vue').useSlots
  const watch: typeof import('vue').watch
  const watchEffect: typeof import('vue').watchEffect
  const useRoute: typeof import('vue-router').useRoute
  const useRouter: typeof import('vue-router').useRouter

  const defineOptions: (...args: any[]) => any
  const useI18n: (...args: any[]) => any
  const useMessage: (...args: any[]) => any
  const useTable: (...args: any[]) => any
  const useCrudSchemas: (...args: any[]) => any
  const required: (...args: any[]) => any
  const DICT_TYPE: Record<string, string>

  interface Fn<T = any> {
    (...args: T[]): T
  }
  type Nullable<T> = T | null
  type Recordable<T = any, K extends string = string> = Record<K, T>
  type ComponentRef<T> = InstanceType<T>
  type LocaleType = 'zh-CN' | 'en'
  type IntervalHandle = ReturnType<typeof setInterval>
  type TimeoutHandle = ReturnType<typeof setTimeout>
  type PageParam = { pageNo?: number; pageSize?: number }
  type PageResult<T> = { list: T; total: number }
  type SummaryMethodProps<T extends Recordable = Recordable> = Parameters<
    import('element-plus').SummaryMethod<T>
  >[0]

  interface GlobalComponents {
    Icon: Component
    DictTag: Component
  }

  interface Tree {
    id: number
    name: string
    children?: Tree[] | any[]
  }
}

declare module 'vue' {
  interface GlobalComponents {
    Icon: Component
    DictTag: Component
  }
}

export type { Component, ComputedRef, Ref }
