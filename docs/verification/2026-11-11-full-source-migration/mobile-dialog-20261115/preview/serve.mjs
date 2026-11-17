import { createRequire } from 'node:module'
import { dirname, resolve } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const root = dirname(fileURLToPath(import.meta.url))
const workspace = resolve(root, '../../../../../..')
const core = resolve(workspace, 'yuheng-core/yuheng-ui')
const require = createRequire(resolve(workspace, 'yuheng-demo/yuheng-demo-ui/package.json'))
const load = async (name) => import(pathToFileURL(require.resolve(name)).href)
const { createServer } = await load('vite')
const { default: vue } = await load('@vitejs/plugin-vue')
const { default: autoImport } = await load('unplugin-auto-import/vite')
const { default: unoCSS } = await load('unocss/vite')
const { presetUno } = await load('unocss')
const server = await createServer({
  root,
  configFile: false,
  envDir: false,
  plugins: [vue(), unoCSS({ configFile: false, presets: [presetUno()] }), autoImport({
    imports: ['vue', {
      [resolve(core, 'compat/hooks/web/useI18n.ts')]: ['useI18n'],
      [resolve(core, 'compat/hooks/web/useMessage.ts')]: ['useMessage']
    }],
    dts: false
  })],
  resolve: {
    alias: [
      { find: '@core', replacement: core },
      { find: /^yuheng-ui$/, replacement: resolve(core, 'dist/index.js') },
      { find: /^vue$/, replacement: require.resolve('vue/dist/vue.runtime.esm-bundler.js') },
      { find: /^pinia$/, replacement: resolve(dirname(require.resolve('pinia')), 'dist/pinia.mjs') },
      { find: /^vue-router$/, replacement: resolve(dirname(require.resolve('vue-router')), 'dist/vue-router.js') },
      { find: /^element-plus$/, replacement: resolve(dirname(require.resolve('element-plus')), '../es/index.mjs') },
      { find: 'element-plus', replacement: resolve(dirname(require.resolve('element-plus')), '..') },
      { find: /^@wangeditor-next\/editor$/, replacement: require.resolve('@wangeditor-next/editor/package.json').replace(/package\.json$/, 'dist/index.mjs') },
      { find: '@wangeditor-next/editor', replacement: resolve(dirname(require.resolve('@wangeditor-next/editor/dist/css/style.css')), '../..') }
    ],
    dedupe: ['vue', 'pinia', 'element-plus']
  },
  define: {
    'import.meta.env.VITE_BASE_URL': JSON.stringify(''),
    'import.meta.env.VITE_API_URL': JSON.stringify('/admin-api'),
    'import.meta.env.VITE_UPLOAD_TYPE': JSON.stringify('server')
  },
  css: { preprocessorOptions: { scss: { additionalData: (source, filename) =>
    filename.endsWith('/styles/variables.scss') ? source
      : `@use "${resolve(core, 'compat/styles/variables.scss')}" as *;\n${source}`
  } } },
  server: { host: '127.0.0.1', port: 5194, strictPort: true, fs: { allow: [workspace] } }
})
await server.listen()
server.printUrls()
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, async () => {
  await server.close()
  process.exit(0)
})
