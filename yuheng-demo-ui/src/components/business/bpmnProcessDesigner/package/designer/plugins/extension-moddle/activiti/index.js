/*
 * @author igdianov
 * address https://github.com/igdianov/activiti-bpmn-moddle
 * */

import activitiExtension from '@/components/business/bpmnProcessDesigner/package/designer/plugins/extension-moddle/activiti/activitiExtension.js'

export default {
  __init__: ['ActivitiModdleExtension'],
  ActivitiModdleExtension: ['type', activitiExtension]
}
