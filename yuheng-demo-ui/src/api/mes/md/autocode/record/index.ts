import request from 'yuheng-ui/compat/config/axios/index.ts'

// MES 编码生成 API
export const AutoCodeRecordApi = {
  // 生成编码
  generateAutoCode: async (ruleCode: string, inputChar?: string) => {
    return await request.post({
      url: `/mes/md/auto-code-record/generate`,
      data: { ruleCode, inputChar }
    })
  }
}
