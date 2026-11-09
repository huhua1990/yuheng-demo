<template>
  <doc-alert title="OA 手册（功能开启）" url="https://doc.iocoder.cn/oa/build/" />
  <div class="min-h-full">
    <!-- 各区块独立请求，首页仅负责布局 -->
    <div class="grid grid-cols-1 gap-16px md:grid-cols-2 xl:grid-cols-4">
      <OaHomeAttendance />
      <OaHomeContactCount v-if="checkPermi(['oa:contact:query'])" />
      <OaHomeDiscussionCount v-if="checkPermi(['oa:discussion:query'])" />
      <OaHomeTaskCount />
    </div>
    <el-row :gutter="16" class="mt-16px">
      <el-col :lg="16" :md="24">
        <OaHomeAnnouncement v-if="checkPermi(['oa:announcement:query'])" class="mb-16px" />
        <OaHomePlan v-if="checkPermi(['oa:plan:query'])" />
      </el-col>
      <el-col :lg="8" :md="24" class="lt-lg:mt-16px">
        <OaHomeTaskStatistics />
        <OaHomeCalendar v-if="checkPermi(['oa:schedule:query'])" class="mt-16px" />
        <OaHomeNote v-if="checkPermi(['oa:note:query'])" class="mt-16px" />
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { checkPermi } from 'yuheng-ui/compat/utils/permission.ts'
import OaHomeAttendance from '@/views/oa/home/components/OaHomeAttendance.vue'
import OaHomeContactCount from '@/views/oa/home/components/OaHomeContactCount.vue'
import OaHomeDiscussionCount from '@/views/oa/home/components/OaHomeDiscussionCount.vue'
import OaHomeTaskCount from '@/views/oa/home/components/OaHomeTaskCount.vue'
import OaHomeAnnouncement from '@/views/oa/home/components/OaHomeAnnouncement.vue'
import OaHomePlan from '@/views/oa/home/components/OaHomePlan.vue'
import OaHomeTaskStatistics from '@/views/oa/home/components/OaHomeTaskStatistics.vue'
import OaHomeCalendar from '@/views/oa/home/components/OaHomeCalendar.vue'
import OaHomeNote from '@/views/oa/home/components/OaHomeNote.vue'

defineOptions({ name: 'OaHome' })
</script>
