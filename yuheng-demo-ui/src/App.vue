<script setup lang="ts">
import { computed } from 'vue'
import { ConfigGlobal } from 'yuheng-ui/compat/components/ConfigGlobal'
import RouterSearch from 'yuheng-ui/compat/components/RouterSearch/index.vue'
import { useAppStore } from 'yuheng-ui/compat/store/modules/app'
import { CACHE_KEY, useCache } from 'yuheng-ui/compat/hooks/web/useCache'
import { isDark } from 'yuheng-ui/compat/utils/is'

const appStore = useAppStore()
const currentSize = computed(() => appStore.getCurrentSize)
const greyMode = computed(() => appStore.getGreyMode)
const { wsCache } = useCache()
appStore.setIsDark(wsCache.get(CACHE_KEY.IS_DARK) ?? isDark())
</script>

<template>
  <ConfigGlobal :size="currentSize">
    <RouterView :class="{ 'yuheng-grey-mode': greyMode }" />
    <RouterSearch />
  </ConfigGlobal>
</template>

<style lang="scss">
html, body, #app { width: 100%; height: 100%; margin: 0; padding: 0; }
body { overflow: hidden; }
.yuheng-grey-mode { filter: grayscale(100%); }
</style>
