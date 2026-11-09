<template>
  <doc-alert title="AI 对话聊天" url="https://doc.iocoder.cn/ai/chat/" />

  <ContentWrap>
    <el-tabs>
      <el-tab-pane label="对话列表">
        <ChatConversationList />
      </el-tab-pane>
      <el-tab-pane label="消息列表">
        <ChatMessageList />
      </el-tab-pane>
    </el-tabs>
  </ContentWrap>
</template>

<script setup lang="ts">
import ChatConversationList from '@/views/ai/chat/manager/ChatConversationList.vue'
import ChatMessageList from '@/views/ai/chat/manager/ChatMessageList.vue'

/** AI 聊天对话 列表 */
defineOptions({ name: 'AiChatManager' })
</script>
