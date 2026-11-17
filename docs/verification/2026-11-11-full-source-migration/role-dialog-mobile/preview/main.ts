import { createApp, defineComponent, h, ref } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'virtual:uno.css'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import { useDictStore } from '@core/src/stores/dict'
import { bindPlatformRuntime } from '@core/compat/runtime'
import { setupI18n } from '@core/compat/plugins/vueI18n/index.ts'
import Dialog from '@core/compat/components/Dialog/src/Dialog.vue'
import RoleForm from '@core/compat/views/system/role/RoleForm.vue'

const pinia = createPinia()
const router = createRouter({ history: createWebHistory(), routes: [] })
const writes = ref(0)
bindPlatformRuntime({ pinia, request: { request: async () => { writes.value++; return 100 } } } as any, router)
useDictStore(pinia).setDictMap({ common_status: [{ label: '开启', value: '0' }, { label: '关闭', value: '1' }] })
const App = defineComponent({ setup() {
  const role = ref()
  return () => h('main', [
    h('button', { id: 'open-role', onClick: () => role.value.open('create') }, '打开角色新增'),
    h('span', { id: 'writes' }, String(writes.value)),
    h(RoleForm, { ref: role })
  ])
} })
const app = createApp(App)
app.use(pinia).use(ElementPlus)
app.component('Dialog', Dialog)
app.component('Icon', defineComponent({ inheritAttrs: false, props: ['icon'], setup: (props, { attrs }) => () => h('button', { ...attrs, type: 'button', 'aria-label': props.icon }, '×') }))
await setupI18n(app)
app.mount('#app')
