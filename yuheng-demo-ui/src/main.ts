import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import {
  installYuhengUi,
  registerPlatformRoutes
} from 'yuheng-ui'
import App from './App.vue'
import { businessRoutes } from './router/business'
import 'yuheng-ui/styles.css'

const app = createApp(App)
const pinia = createPinia()
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: []
})

app.use(pinia)
installYuhengUi(app, {
  apiBaseUrl: import.meta.env.VITE_API_URL ?? '/admin-api',
  appTitle: import.meta.env.VITE_APP_TITLE ?? 'Yuheng Demo',
  basePath: import.meta.env.BASE_URL,
  pinia
})
registerPlatformRoutes(router)
businessRoutes.forEach((route) => router.addRoute(route))
app.use(router)
app.mount('#app')
