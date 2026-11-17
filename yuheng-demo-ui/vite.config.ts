import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import UnoCSS from 'unocss/vite'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import { defineConfig, normalizePath } from 'vite'
import { dirname, relative, resolve } from 'node:path'
import { createRequire } from 'node:module'

const require = createRequire(import.meta.url)
const packageRoot = dirname(require.resolve('yuheng-ui/compat/platform'))
const variables = resolve(packageRoot, 'styles/variables.scss')

export default defineConfig({
  plugins: [vue(), vueJsx(), UnoCSS(), AutoImport({
    exclude: [/node_modules\/(?!\.pnpm\/[^/]+\/node_modules\/yuheng-ui\/compat\/|yuheng-ui\/compat\/)/, /\.git\//],
    imports: ['vue', 'vue-router', {
      'yuheng-ui/compat/hooks/web/useI18n': ['useI18n'],
      'yuheng-ui/compat/hooks/web/useMessage': ['useMessage'],
      'yuheng-ui/compat/hooks/web/useTable': ['useTable'],
      'yuheng-ui/compat/hooks/web/useCrudSchemas': ['useCrudSchemas'],
      'yuheng-ui/compat/utils/formRules': ['required'],
      'yuheng-ui/compat/utils/dict': ['DICT_TYPE']
    }],
    resolvers: [ElementPlusResolver()],
    dts: false
  }), Components({ resolvers: [ElementPlusResolver()], dirs: [resolve(packageRoot, 'components')], dts: false })],
  resolve: { alias: { '@': new URL('./src', import.meta.url).pathname } },
  optimizeDeps: { exclude: ['yuheng-ui', 'yuheng-ui/compat/utils/formRules'] },
  css: { preprocessorOptions: { scss: { additionalData: (source: string, filename: string) => {
    const clean = normalizePath(filename.split('?')[0])
    if (clean.endsWith('/styles/variables.scss') || clean.endsWith('/styles/global.module.scss')) return source
    let path = normalizePath(relative(dirname(clean), variables))
    if (!path.startsWith('.')) path = `./${path}`
    return `@use "${path}" as *;\n${source}`
  } } } },
  server: { proxy: { '/admin-api': { target: process.env.VITE_BACKEND_ORIGIN || 'http://127.0.0.1:48080', changeOrigin: true } } },
  build: { outDir: 'dist', target: 'esnext' }
})
