import { defineConfig, presetUno, toEscapedSelector } from 'unocss'

export default defineConfig({
  content: { filesystem: ['node_modules/yuheng-ui/compat/**/*.{vue,ts,tsx}'] },
  presets: [presetUno({ dark: 'class', attributify: false })],
  shortcuts: { 'wh-full': 'w-full h-full' },
  rules: [
    [/^custom-hover$/, ([], { rawSelector }) => {
      const selector = toEscapedSelector(rawSelector)
      return `${selector}{display:flex;height:100%;padding:0 10px;cursor:pointer;align-items:center;transition:background var(--transition-time-02)}${selector}:hover{background-color:var(--top-header-hover-color)}.dark ${selector}:hover{background-color:var(--el-bg-color-overlay)}`
    }],
    [/^layout-border__(left|right|top|bottom)$/, ([, side], { rawSelector }) => {
      const selector = toEscapedSelector(rawSelector)
      const vertical = side === 'left' || side === 'right'
      return `${selector}:${side === 'left' || side === 'top' ? 'before' : 'after'}{content:"";position:absolute;${side}:0;${vertical ? 'top:0;height:100%;width:1px' : 'left:0;width:100%;height:1px'};background-color:var(--el-border-color);z-index:3}`
    }]
  ]
})
