<!-- 核算准备员工列表 -->
<template>
  <el-table :data="list || []" max-height="480">
    <el-table-column label="员工姓名" min-width="130" prop="employeeName" />
    <el-table-column label="工号" prop="jobNumber" width="120" />
    <el-table-column label="部门" min-width="130" prop="deptName" />
    <el-table-column label="岗位" min-width="130" prop="postName" />
    <el-table-column align="center" label="员工状态" width="100">
      <template #default="scope">
        <dict-tag
          v-if="scope.row.status != null"
          :type="DICT_TYPE.HRM_EMPLOYEE_STATUS"
          :value="scope.row.status"
        />
        <span v-else>-</span>
      </template>
    </el-table-column>
    <el-table-column
      :formatter="dateFormatter"
      align="center"
      label="入职日期"
      prop="entryTime"
      width="110"
    />
  </el-table>
</template>

<script lang="ts" setup>
import type { SalaryPayrollReadinessEmployeeVO } from '@/api/hrm/salary/month-record/index.ts'
import { DICT_TYPE } from 'yuheng-ui/compat/utils/dict.ts'
import { dateFormatter } from 'yuheng-ui/compat/utils/formatTime.ts'

defineOptions({ name: 'HrmSalaryPayrollReadinessEmployeeList' })

defineProps<{
  list?: SalaryPayrollReadinessEmployeeVO[]
}>()
</script>
