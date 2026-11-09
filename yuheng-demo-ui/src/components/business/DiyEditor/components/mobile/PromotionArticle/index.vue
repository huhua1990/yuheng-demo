<template>
  <div class="min-h-30px" v-html="article?.content"></div>
</template>
<script setup lang="ts">
import { PromotionArticleProperty } from '@/components/business/DiyEditor/components/mobile/PromotionArticle/config.ts'
import * as ArticleApi from '@/api/mall/promotion/article/index.ts'

/** 营销文章 */
defineOptions({ name: 'PromotionArticle' })
// 定义属性
const props = defineProps<{ property: PromotionArticleProperty }>()
// 商品列表
const article = ref<ArticleApi.ArticleVO>()
watch(
  () => props.property.id,
  async () => {
    if (props.property.id) {
      article.value = await ArticleApi.getArticle(props.property.id)
    }
  },
  {
    immediate: true
  }
)
</script>

<style scoped lang="scss"></style>
