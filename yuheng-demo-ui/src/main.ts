import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import { installYuhengUi } from 'yuheng-ui'
import { addCollection } from '@iconify/vue'
import epIcons from '@iconify/json/json/ep.json'
import faIcons from '@iconify/json/json/fa.json'
import faSolidIcons from '@iconify/json/json/fa-solid.json'
import { completePlatformRoutes, platformViewComponents } from 'yuheng-ui/compat/platform'
import { setupCompletePlatform } from 'yuheng-ui/compat/setup'
import DocAlert from 'yuheng-ui/compat/components/DocAlert/index.vue'
import { DictTag } from 'yuheng-ui/compat/components/DictTag'
import 'virtual:uno.css'
import App from './App.vue'
import { businessRoutes, businessViewComponents, publicBusinessRoutes } from './router/business'
import 'yuheng-ui/styles.css'

addCollection(epIcons)
addCollection(faIcons)
addCollection(faSolidIcons)

const app = createApp(App)
const pinia = createPinia()
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: []
})

app.use(pinia)
const runtime = installYuhengUi(app, {
  apiBaseUrl: import.meta.env.VITE_API_URL ?? '/admin-api',
  appTitle: import.meta.env.VITE_APP_TITLE ?? 'Yuheng Demo',
  basePath: import.meta.env.BASE_URL,
  tenantEnabled: true,
  pinia,
  platformRoutes: completePlatformRoutes,
  resolveComponent: (key) => {
    const normalized = key.replace(/^\/+/, '').replace(/\.(vue|tsx)$/, '')
    return businessViewComponents[`../views/${normalized}.vue`] as never
      ?? businessViewComponents[`../views/${normalized}/index.vue`] as never
      ?? platformViewComponents[`./views/${normalized}.vue`] as never
      ?? platformViewComponents[`./views/${normalized}/index.vue`] as never
  }
})
runtime.registerRoutes(router)
publicBusinessRoutes.forEach((route) => router.addRoute(route))
businessRoutes.forEach((route) => router.addRoute('Home', route))
await setupCompletePlatform(app, runtime.context, router, { ...platformViewComponents, ...businessViewComponents })
if (!app.component('DocAlert')) app.component('DocAlert', DocAlert)
if (!app.component('DictTag')) app.component('DictTag', DictTag)
app.use(router)
app.mount('#app')
