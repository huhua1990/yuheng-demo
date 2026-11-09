import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import { defineConfig, loadEnv } from 'vite'
import { fileURLToPath } from 'node:url'
import { resolve } from 'node:path'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import UnoCSS from 'unocss/vite'

const platform = fileURLToPath(new URL('./node_modules/yuheng-ui/compat', import.meta.url))
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [
      vue(), vueJsx(), UnoCSS(),
      AutoImport({
        include: [/\.[tj]sx?$/, /\.vue$/, /\.vue\?vue/],
        imports: ['vue', 'vue-router', {
          'yuheng-ui/compat/hooks/web/useI18n': ['useI18n'],
          'yuheng-ui/compat/hooks/web/useMessage': ['useMessage'],
          'yuheng-ui/compat/hooks/web/useTable': ['useTable'],
          'yuheng-ui/compat/hooks/web/useCrudSchemas': ['useCrudSchemas'],
          'yuheng-ui/compat/utils/formRules': ['required'],
          'yuheng-ui/compat/utils/dict': ['DICT_TYPE']
        }], dts: 'src/types/auto-imports.d.ts', resolvers: [ElementPlusResolver()]
      }),
      Components({
        globs: [
          `${resolve(platform, 'components')}/**/*.{vue,tsx}`,
          'src/components/business/**/*.{vue,tsx}',
          '!src/components/business/DiyEditor/components/mobile/**/*.{vue,tsx}'
        ],
        dts: 'src/types/auto-components.d.ts', resolvers: [ElementPlusResolver()]
      })
    ],
    resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) }, dedupe: ['vue', 'pinia', 'vue-router', 'element-plus', 'vue-i18n'] },
    server: { host: '127.0.0.1', port: 3000, strictPort: true, proxy: { '/admin-api': { target: env.VITE_BACKEND_ORIGIN ?? 'http://127.0.0.1:48080', changeOrigin: true } } },
    css: { preprocessorOptions: { scss: {
      api: 'modern-compiler',
      additionalData: (source: string, filename: string) => /variables\.scss|global\.module\.scss/.test(filename) ? source : `@use "${platform}/styles/variables.scss" as *;\n${source}`
    } } },
    build: { outDir: 'dist', reportCompressedSize: false, chunkSizeWarningLimit: 2500 },
    optimizeDeps: { exclude: ['yuheng-ui'] }
  }
})
