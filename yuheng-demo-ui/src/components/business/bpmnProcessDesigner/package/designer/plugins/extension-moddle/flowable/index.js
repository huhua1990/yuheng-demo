/*
 * @author igdianov
 * address https://github.com/igdianov/activiti-bpmn-moddle
 * */
import flowableExtension from '@/components/business/bpmnProcessDesigner/package/designer/plugins/extension-moddle/flowable/flowableExtension.js'

export default {
  __init__: ['FlowableModdleExtension'],
  FlowableModdleExtension: ['type', flowableExtension]
}
