'use strict'

import extension from '@/components/business/bpmnProcessDesigner/package/designer/plugins/extension-moddle/camunda/extension.js'

export default {
  __init__: ['camundaModdleExtension'],
  camundaModdleExtension: ['type', extension]
}
