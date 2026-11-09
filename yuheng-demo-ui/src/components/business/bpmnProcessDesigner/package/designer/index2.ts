import MyProcessViewer from '@/components/business/bpmnProcessDesigner/package/designer/ProcessViewer.vue'

MyProcessViewer.install = function (Vue) {
  Vue.component(MyProcessViewer.name, MyProcessViewer)
}

// 流程图的查看器，不可编辑
export default MyProcessViewer
