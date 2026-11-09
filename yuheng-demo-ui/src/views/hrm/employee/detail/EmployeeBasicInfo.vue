<template>
  <EmployeeDetailsInfo :employee="employee" />
  <ContentWrap title="教育经历">
    <EmployeeEducationExperienceList :employee-id="employeeId" />
  </ContentWrap>
  <ContentWrap title="工作经历">
    <EmployeeWorkExperienceList :employee-id="employeeId" />
  </ContentWrap>
  <ContentWrap title="证书/证件">
    <EmployeeCertificateList :employee-id="employeeId" />
  </ContentWrap>
  <ContentWrap title="培训经历">
    <EmployeeTrainingExperienceList :employee-id="employeeId" />
  </ContentWrap>
  <ContentWrap title="联系人">
    <EmployeeContactList :employee-id="employeeId" />
  </ContentWrap>
</template>

<script lang="ts" setup>
import type { HrmEmployeeVO } from '@/api/hrm/employee/index.ts'
import EmployeeCertificateList from '@/views/hrm/employee/detail/EmployeeCertificateList.vue'
import EmployeeContactList from '@/views/hrm/employee/detail/EmployeeContactList.vue'
import EmployeeDetailsInfo from '@/views/hrm/employee/detail/EmployeeDetailsInfo.vue'
import EmployeeEducationExperienceList from '@/views/hrm/employee/detail/EmployeeEducationExperienceList.vue'
import EmployeeTrainingExperienceList from '@/views/hrm/employee/detail/EmployeeTrainingExperienceList.vue'
import EmployeeWorkExperienceList from '@/views/hrm/employee/detail/EmployeeWorkExperienceList.vue'

defineOptions({ name: 'HrmEmployeeBasicInfo' })

defineProps<{
  employee: HrmEmployeeVO
  employeeId: number
}>()
</script>
