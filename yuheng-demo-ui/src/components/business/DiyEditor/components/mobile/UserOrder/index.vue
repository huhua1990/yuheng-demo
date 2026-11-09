<template>
  <el-image src="https://shopro.sheepjs.com/admin/static/images/shop/decorate/orderCardStyle.png" />
</template>
<script setup lang="ts">
import { UserOrderProperty } from '@/components/business/DiyEditor/components/mobile/UserOrder/config.ts'

/** 用户订单 */
defineOptions({ name: 'UserOrder' })
// 定义属性
defineProps<{ property: UserOrderProperty }>()
</script>

<style scoped lang="scss"></style>
