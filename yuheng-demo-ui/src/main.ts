import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import { installYuhengUi } from 'yuheng-ui'
import { completePlatformRoutes, platformViewComponents } from 'yuheng-ui/compat/platform'
import { bindPlatformRuntime, registerViewComponents } from 'yuheng-ui/compat/runtime'
import 'yuheng-ui/styles.css'
import 'virtual:uno.css'
import App from './App.vue'
import { businessExtras } from './router/business-extras'

const businessViews = import.meta.glob('./views/**/*.{vue,tsx}')
const components: Record<string, any> = {}
for (const [path, component] of Object.entries({ ...platformViewComponents, ...businessViews })) {
  const key = path.replace(/^.*?views\//, '').replace(/\.vue$|\.tsx$/g, '')
  components[key] = component
}

async function bootstrap() {
  const app = createApp(App)
  const pinia = createPinia()
  const router = createRouter({ history: createWebHistory(), routes: [], scrollBehavior: () => ({ left: 0, top: 0 }) })
  const runtime = installYuhengUi(app, {
    apiBaseUrl: import.meta.env.VITE_API_URL ?? '/admin-api',
    appTitle: import.meta.env.VITE_APP_TITLE ?? 'Yuheng Demo',
    tenantEnabled: import.meta.env.VITE_APP_TENANT_ENABLE === 'true',
    platformRoutes: completePlatformRoutes,
    resolveComponent: (key: string) => components[key.replace(/^\/+/, '').replace(/\.vue$/, '').split('?')[0]],
    pinia
  })
  bindPlatformRuntime(runtime.context, router)
  registerViewComponents(components)
  const { setupCompletePlatform } = await import('yuheng-ui/compat/setup')
  await setupCompletePlatform(app, runtime.context, router, components)
  const { setupWangEditorPlugin } = await import('./views/bpm/model/form/PrintTemplate')
  setupWangEditorPlugin()
  const { default: FmsAccountSetSwitch } = await import('./views/fms/components/account-set/FmsAccountSetSwitch.vue')
  app.component('YuhengBusinessHeader', FmsAccountSetSwitch)
  runtime.registerRoutes(router)
  for (const route of businessExtras) {
    if (route.name === 'PmsKnowledgeDocumentShare') router.addRoute(route)
    else router.addRoute('Home', route)
  }
  app.use(router)
  await router.isReady()
  app.mount('#app')
}
bootstrap().catch((error) => {
  console.error('管理端启动失败', error)
  const root = document.querySelector('#app')
  if (root) root.textContent = '管理端启动失败，请查看控制台或重启前端服务。'
})
