import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

describe('copied ERP warehouse form contract', () => {
  it('keeps the name input and form rules within the persisted limit', () => {
    const form = readFileSync(
      new URL('../src/views/erp/stock/warehouse/WarehouseForm.vue', import.meta.url), 'utf8'
    )
    expect(form).toMatch(/<el-input[^>]*v-model="formData.name"[^>]*maxlength="20"/)
    const nameRules = form.split('const formRules')[1].split('sort:')[0]
    expect(nameRules).toMatch(/max:\s*20\b/)
  })
})
