<template>
  <div class="transfers">
    <n-h1>转账记录</n-h1>
    <n-card title="转账列表">
      <template #header-extra>
        <n-button
          v-if="canAdd"
          type="primary"
          @click="handleAdd"
        >新增转账</n-button>
      </template>

      <n-space align="center" wrap style="margin-bottom: 12px">
        <n-select
          v-model:value="filterFrom"
          :options="accountOptions"
          placeholder="转出账户"
          clearable
          style="width: 180px"
        />
        <span style="color: #888">→</span>
        <n-select
          v-model:value="filterTo"
          :options="accountOptions"
          placeholder="转入账户"
          clearable
          style="width: 180px"
        />
        <n-divider vertical />
        <n-date-picker
          v-model:value="filterDateRange"
          type="daterange"
          clearable
          style="width: 240px"
          placeholder="日期范围"
        />
        <n-button v-if="hasFilter" quaternary size="tiny" @click="clearFilters">清除筛选</n-button>
      </n-space>

      <n-data-table
        :columns="columns"
        :data="displayData"
        :loading="loading"
        :pagination="false"
        size="small"
      />

      <n-modal v-model:show="showModal" preset="card" :title="isEdit ? '编辑转账' : '新增转账'" style="width: 480px">
        <n-form :model="form" label-placement="top">
          <n-form-item label="转出账户" required>
            <n-select
              v-model:value="form.from_account"
              :options="accountOptions"
              placeholder="选择转出账户"
              filterable
            />
          </n-form-item>
          <n-form-item label="转入账户" required>
            <n-select
              v-model:value="form.to_account"
              :options="accountOptions"
              placeholder="选择转入账户"
              filterable
            />
          </n-form-item>
          <n-form-item label="金额" required>
            <n-input-number
              v-model:value="form.amount"
              :min="0.01"
              style="width: 100%"
              placeholder="0.00"
            >
              <template #suffix>元</template>
            </n-input-number>
          </n-form-item>
          <n-form-item label="日期" required>
            <n-date-picker
              v-model:value="formDate"
              type="date"
              style="width: 100%"
            />
          </n-form-item>
          <n-form-item label="备注">
            <n-input v-model:value="form.note" type="textarea" placeholder="如：入金、出金" />
          </n-form-item>
        </n-form>
        <template #footer>
          <n-space justify="end">
            <n-button @click="showModal = false">取消</n-button>
            <n-button type="primary" @click="handleSubmit" :loading="submitting">确定</n-button>
          </n-space>
        </template>
      </n-modal>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted } from 'vue'
import {
  NCard, NH1, NButton, NDataTable, NModal, NForm, NFormItem,
  NInput, NInputNumber, NSelect, NSpace, NDatePicker, NDivider,
  useMessage, NPopconfirm,
} from 'naive-ui'
import { getTransfers, createTransfer, updateTransfer, deleteTransfer, getAccounts } from '@/api/finance'
import { useAuthStore } from '@/stores/auth'
import type { Transfer, Account } from '@/api/finance/type'

const authStore = useAuthStore()
const message = useMessage()
const loading = ref(false)
const submitting = ref(false)
const showModal = ref(false)
const isEdit = ref(false)
const data = ref<Transfer[]>([])
const accounts = ref<Account[]>([])
const filterFrom = ref<number | null>(null)
const filterTo = ref<number | null>(null)
const filterDateRange = ref<[number, number] | null>(null)

const canAdd = computed(() =>
  authStore.isSuperuser || authStore.permissions?.actions?.transfer?.includes('add')
)

const canChange = (): boolean =>
  !!(authStore.isSuperuser || authStore.permissions?.actions?.transfer?.includes('change'))

const canDelete = (): boolean =>
  !!(authStore.isSuperuser || authStore.permissions?.actions?.transfer?.includes('delete'))

const accountOptions = computed(() =>
  accounts.value.map((a) => ({ label: a.name, value: a.id }))
)

const hasFilter = computed(() =>
  filterFrom.value || filterTo.value || filterDateRange.value
)

const displayData = computed(() => {
  let rows = data.value
  if (filterFrom.value) rows = rows.filter((r) => r.from_account === filterFrom.value)
  if (filterTo.value) rows = rows.filter((r) => r.to_account === filterTo.value)
  if (filterDateRange.value) {
    const [start, end] = filterDateRange.value
    rows = rows.filter((r) => {
      const d = new Date(r.trade_time).getTime()
      return d >= start && d <= end
    })
  }
  return rows
})

const clearFilters = () => {
  filterFrom.value = null
  filterTo.value = null
  filterDateRange.value = null
}

const columns = [
  { title: '日期', key: 'trade_time', width: 110 },
    {
    title: '转出',
    key: 'from_account_name',
    render: (row: Transfer) => h('span', { style: { color: '#18a058' } }, row.from_account_name),
  },
  {
    title: '转入',
    key: 'to_account_name',
    render: (row: Transfer) => h('span', { style: { color: '#d03050' } }, row.to_account_name),
  },
  {
    title: '金额',
    key: 'amount',
    render: (row: Transfer) => h('span', { style: { fontWeight: 'bold' } }, row.amount),
  },
  { title: '备注', key: 'note', ellipsis: { tooltip: true } },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render: (row: Transfer) => {
      const btns: any[] = []
      if (canChange()) {
        btns.push(h(NButton, { size: 'small', onClick: () => handleEdit(row) }, { default: () => '编辑' }))
      }
      if (canDelete()) {
        btns.push(h(NPopconfirm, { onPositiveClick: () => handleDelete(row.id) }, {
          trigger: () => h(NButton, { size: 'small', type: 'error' }, { default: () => '删除' }),
          default: () => '确定删除该转账记录？',
        }))
      }
      if (btns.length === 0) return '-'
      return h(NSpace, { size: 'small' }, { default: () => btns })
    },
  },
]

const form = ref({
  id: null as number | null,
  from_account: null as number | null,
  to_account: null as number | null,
  amount: 0,
  note: '',
})
const formDate = ref<number | null>(Date.now())

const toDateStr = (ts: number) => {
  const d = new Date(ts)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await getTransfers({ size: 500 })
    data.value = res.data.items
  } catch {
    console.error('Failed to load transfers')
  } finally {
    loading.value = false
  }
}

const loadAccounts = async () => {
  try {
    const res = await getAccounts({ size: 100 })
    accounts.value = res.data.items
  } catch {
    console.error('Failed to load accounts')
  }
}

const handleAdd = () => {
  isEdit.value = false
  form.value = { id: null, from_account: null, to_account: null, amount: 0, note: '' }
  formDate.value = Date.now()
  showModal.value = true
}

const handleEdit = (row: Transfer) => {
  isEdit.value = true
  form.value = {
    id: row.id,
    from_account: row.from_account,
    to_account: row.to_account,
    amount: Number(row.amount),
    note: row.note,
  }
  formDate.value = new Date(row.trade_time).getTime()
  showModal.value = true
}

const handleDelete = async (id: number) => {
  try {
    await deleteTransfer(id)
    message.success('删除成功')
    loadData()
  } catch {
    console.error('Failed to delete transfer')
  }
}

const handleSubmit = async () => {
  if (!form.value.from_account || !form.value.to_account) {
    message.warning('请选择转出和转入账户')
    return
  }
  if (form.value.from_account === form.value.to_account) {
    message.warning('转出和转入账户不能相同')
    return
  }
  if (!form.value.amount || form.value.amount <= 0) {
    message.warning('金额必须大于零')
    return
  }
  if (!formDate.value) {
    message.warning('请选择日期')
    return
  }

  submitting.value = true
  try {
    const payload = {
      from_account: form.value.from_account,
      to_account: form.value.to_account,
      amount: String(form.value.amount),
      trade_time: toDateStr(formDate.value),
      note: form.value.note,
    }
    if (isEdit.value && form.value.id) {
      await updateTransfer(form.value.id, payload)
      message.success('更新成功')
    } else {
      await createTransfer(payload)
      message.success('创建成功')
    }
    showModal.value = false
    loadData()
  } catch {
    console.error('Failed to submit')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadData()
  loadAccounts()
})
</script>
