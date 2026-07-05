<template>
  <n-modal
    :show="show"
    preset="card"
    :title="isEdit ? '编辑交易' : '新增交易'"
    style="width: 520px"
    @close="handleCancel"
    @update:show="handleCancel"
  >
    <n-form :model="form" label-placement="left" label-width="110">
      <n-form-item label="按账本筛选分类">
        <n-select
          v-model:value="filterLedgerId"
          :options="ledgerFilterOptions"
          placeholder="全部账本"
          clearable
          filterable
        />
      </n-form-item>
      <n-form-item label="分类" required>
        <n-select
          v-model:value="form.category"
          :options="categoryOptions"
          placeholder="请选择分类"
          filterable
        />
      </n-form-item>
      <n-form-item label="交易日期" required>
        <n-date-picker
          v-model:value="form.trade_time"
          type="date"
          placeholder="选择日期"
          style="width: 100%"
        />
      </n-form-item>
      <n-form-item label="交易对象" required>
        <n-input v-model:value="form.partner" placeholder="请输入交易对象" />
      </n-form-item>
      <n-form-item label="金额" required>
        <n-space style="width: 100%">
          <n-button
            :type="amountType === 'expense' ? 'primary' : 'default'"
            :style="amountType === 'expense' ? { background: '#18a058', borderColor: '#18a058' } : {}"
            size="small"
            @click="amountType = 'expense'"
          >支出</n-button>
          <n-button
            :type="amountType === 'income' ? 'primary' : 'default'"
            :style="amountType === 'income' ? { background: '#d03050', borderColor: '#d03050' } : {}"
            size="small"
            @click="amountType = 'income'"
          >收入</n-button>
          <n-input-number
            v-model:value="form.amount"
            :min="0"
            placeholder="0.00"
            style="flex: 1"
          >
            <template #suffix>元</template>
          </n-input-number>
        </n-space>
      </n-form-item>
      <n-form-item label="满意度">
        <n-rate v-model:value="form.star" :count="5" />
      </n-form-item>
      <n-form-item label="交易渠道">
        <n-input v-model:value="form.channel" placeholder="如：微信支付、支付宝" />
      </n-form-item>
      <n-form-item label="交易细节">
        <n-input v-model:value="form.detail" placeholder="可选" />
      </n-form-item>
      <n-form-item label="备注">
        <n-input v-model:value="form.remarks" type="textarea" placeholder="可选备注" />
      </n-form-item>
    </n-form>
    <template #footer>
      <n-space justify="end">
        <n-button @click="handleCancel">取消</n-button>
        <n-button type="primary" @click="handleSubmit" :loading="submitting">确定</n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  NModal,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NSelect,
  NDatePicker,
  NSpace,
  NRate,
  NButton,
  useMessage,
} from 'naive-ui'
import { createTransaction, updateTransaction } from '@/api/finance'
import type { Category, Ledger, Transaction } from '@/api/finance/type'

const message = useMessage()

const props = defineProps<{
  show: boolean
  categories: Category[]
  ledgers: Ledger[]
  initialCategoryId?: number | null
  initialDate?: number | null
  editTransaction?: Transaction | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'saved'): void
}>()

const isEdit = ref(false)
const submitting = ref(false)

const filterLedgerId = ref<number | null>(null)

const form = ref({
  id: null as number | null,
  category: null as number | null,
  trade_time: null as number | null,
  partner: '',
  amount: null as number | null,
  star: 5,
  channel: '',
  detail: '',
  remarks: '',
})

const amountType = ref<'expense' | 'income'>('expense')

const ledgerFilterOptions = computed(() =>
  props.ledgers.map((l) => ({
    label: `${l.name}（${l.ledger_type_display}）余额：${l.balance}`,
    value: l.id,
  }))
)

const categoryOptions = computed(() =>
  props.categories
    .filter((c) => {
      if (c.is_complete) return false
      if (filterLedgerId.value) {
        return c.time_ledger === filterLedgerId.value || c.category_ledger === filterLedgerId.value
      }
      return true
    })
    .map((c) => {
      const ledgerNames = [c.time_ledger_name, c.category_ledger_name].filter(Boolean)
      const suffix = ledgerNames.length > 0 ? `（${ledgerNames.join(' / ')}）` : ''
      return { label: `${c.name} ${suffix}余额：${c.actual_amount}`, value: c.id }
    })
)

watch(() => props.show, (val) => {
  if (val) {
    filterLedgerId.value = null
    amountType.value = 'expense'
    if (props.editTransaction) {
      isEdit.value = true
      const signed = Number(props.editTransaction.amount)
      amountType.value = signed >= 0 ? 'income' : 'expense'
      form.value = {
        id: props.editTransaction.id,
        category: props.editTransaction.category,
        trade_time: new Date(props.editTransaction.trade_time).getTime(),
        partner: props.editTransaction.partner,
        amount: Math.abs(signed),
        star: props.editTransaction.star,
        channel: props.editTransaction.channel,
        detail: props.editTransaction.detail,
        remarks: props.editTransaction.remarks,
      }
    } else {
      isEdit.value = false
      form.value = {
        id: null,
        category: props.initialCategoryId ?? null,
        trade_time: props.initialDate ?? null,
        partner: '',
        amount: null,
        star: 5,
        channel: '',
        detail: '',
        remarks: '',
      }
    }
  }
})

function handleCancel() {
  emit('close')
}

async function handleSubmit() {
  if (!form.value.category) { message.warning('请选择分类'); return }
  if (!form.value.trade_time) { message.warning('请选择交易日期'); return }
  if (!form.value.partner) { message.warning('请输入交易对象'); return }
  if (!form.value.amount || form.value.amount === 0) { message.warning('金额不能为零'); return }

  submitting.value = true
  try {
    const date = new Date(form.value.trade_time)
    const tradeDate = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
    const payload = {
      category: form.value.category,
      trade_time: tradeDate,
      partner: form.value.partner,
      amount: String(form.value.amount * (amountType.value === 'expense' ? -1 : 1)),
      star: form.value.star,
      channel: form.value.channel,
      detail: form.value.detail,
      remarks: form.value.remarks,
    }
    if (isEdit.value && form.value.id) {
      await updateTransaction(form.value.id, payload)
      message.success('更新成功')
    } else {
      await createTransaction(payload)
      message.success('创建成功')
    }
    emit('saved')
  } catch {
    message.error('操作失败')
  } finally {
    submitting.value = false
  }
}
</script>
