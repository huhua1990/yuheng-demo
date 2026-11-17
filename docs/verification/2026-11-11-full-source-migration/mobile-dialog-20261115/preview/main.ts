import { createApp, defineComponent, h, ref } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'virtual:uno.css'
import '@wangeditor-next/editor/dist/css/style.css'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import { useDictStore } from '@core/src/stores/dict'
import { bindPlatformRuntime } from '@core/compat/runtime'
import { setupI18n } from '@core/compat/plugins/vueI18n/index.ts'
import Dialog from '@core/compat/components/Dialog/src/Dialog.vue'
import Editor from '@core/compat/components/Editor/src/Editor.vue'
import NoticeForm from '@core/compat/views/system/notice/NoticeForm.vue'
import PostForm from '@core/compat/views/system/post/PostForm.vue'

const pinia = createPinia()
const router = createRouter({ history: createWebHistory(), routes: [] })
const writes = ref(0)
const events = ref(0)
const errors = ref(0)
const fail = ref(false)
const request = { request: async (config: any) => {
  if (config.method !== 'GET') {
    writes.value++
    if (fail.value) throw new Error('模拟请求失败')
    return 100
  }
  throw new Error('预览不提供后端读取')
} }
bindPlatformRuntime({ pinia, request } as any, router)
useDictStore(pinia).setDictMap({
  system_notice_type: [{ label: '通知', value: '1' }, { label: '公告', value: '2' }],
  common_status: [{ label: '开启', value: '0' }, { label: '关闭', value: '1' }]
})
const App = defineComponent({ setup() {
  const notice = ref()
  const post = ref()
  const sample = ref(false)
  const mode = ref('percent')
  return () => h('main', { style: 'padding:20px;font-family:sans-serif' }, [
    h('h1', 'Yuheng 表单隔离验收'),
    h('p', '真实 Core 组件；请求由内存适配器模拟，未连接数据库。'),
    h('p', { id: 'counters' }, `模拟写请求 ${writes.value}；成功事件 ${events.value}；异常 ${errors.value}`),
    h('button', { onClick: () => notice.value.open('create') }, '打开公告新增'),
    h('button', { onClick: () => post.value.open('create'), style: 'margin-left:12px' }, '打开岗位新增'),
    h('label', { style: 'margin-left:12px' }, [h('input', { type: 'checkbox', checked: fail.value, onChange: (e: Event) => { fail.value = (e.target as HTMLInputElement).checked } }), '模拟请求失败']),
    h('button', { onClick: () => { mode.value = 'percent'; sample.value = true }, style: 'margin-left:12px' }, '打开百分比弹窗'),
    h('button', { onClick: () => { mode.value = 'fullscreen'; sample.value = true }, style: 'margin-left:12px' }, '打开默认全屏'),
    h(Dialog, { modelValue: sample.value, 'onUpdate:modelValue': (v: boolean) => { sample.value = v }, title: '宽度兼容检查', width: '60%', defaultFullscreen: mode.value === 'fullscreen' }, { default: () => h('p', '兼容性检查内容'), footer: () => h('button', { onClick: () => { sample.value = false } }, '关闭检查') }),
    h(NoticeForm, { ref: notice, onSuccess: () => events.value++ }),
    h(PostForm, { ref: post, onSuccess: () => events.value++ })
  ])
} })
const app = createApp(App)
app.config.errorHandler = (error) => { errors.value++; console.error(error) }
app.use(pinia).use(ElementPlus)
app.component('Dialog', Dialog)
app.component('Editor', Editor)
// Avoid icon-provider network calls in this isolated preview.
app.component('Icon', defineComponent({ inheritAttrs: false, props: ['icon'], setup: (props, { attrs }) => () => h('button', { ...attrs, type: 'button', 'aria-label': props.icon?.includes('enter-full-screen') ? '进入全屏' : props.icon?.includes('exit-full-screen') ? '退出全屏' : '关闭弹窗' }, props.icon?.includes('full-screen') ? '□' : '×') }))
await setupI18n(app)
app.mount('#app')
