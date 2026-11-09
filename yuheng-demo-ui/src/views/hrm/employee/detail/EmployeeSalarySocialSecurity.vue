<template>
  <EmployeeSalaryInfo
    v-if="checkPermi(['hrm:salary:employee-info:query'])"
    :employee-id="employeeId"
  />
  <EmployeeSalaryCardInfo :employee-id="employeeId" />
  <EmployeeInsuranceInfo
    v-if="checkPermi(['hrm:insurance:employee-info:query'])"
    :employee-id="employeeId"
  />
  <EmployeeSalaryHistoryList
    v-if="checkPermi(['hrm:salary:month-record:query'])"
    :employee-id="employeeId"
  />
  <EmployeeSalaryChangeRecordList :employee-id="employeeId" />
</template>

<script lang="ts" setup>
import { checkPermi } from 'yuheng-ui/compat/utils/permission.ts'
import EmployeeSalaryInfo from '@/views/hrm/employee/detail/EmployeeSalaryInfo.vue'
import EmployeeSalaryCardInfo from '@/views/hrm/employee/detail/EmployeeSalaryCardInfo.vue'
import EmployeeSalaryChangeRecordList from '@/views/hrm/employee/detail/EmployeeSalaryChangeRecordList.vue'
import EmployeeSalaryHistoryList from '@/views/hrm/employee/detail/EmployeeSalaryHistoryList.vue'
import EmployeeInsuranceInfo from '@/views/hrm/employee/detail/EmployeeInsuranceInfo.vue'

defineOptions({ name: 'HrmEmployeeSalarySocialSecurity' })

defineProps<{
  employeeId: number
}>()
</script>
