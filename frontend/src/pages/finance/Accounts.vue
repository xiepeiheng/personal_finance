<template>
  <div class="accounts">
    <n-h1>账户管理</n-h1>
    <n-card title="账户列表">
      <template #header-extra>
        <n-button
          v-if="canAdd"
          type="primary"
          @click="handleAdd"
        >新增账户</n-button>
      </template>

      <n-space align="center" style="margin-bottom: 12px">
        <n-select
          v-model:value="filterType"
          :options="filterTypeOptions"
          placeholder="全部类型"
          clearable
          style="width: 160px"
        />
      </n-space>

      <n-data-table
        :columns="columns"
        :data="displayData"
        :loading="loading"
        :pagination="false"
        size="small"
      />

      <n-modal v-model:show="showModal" preset="card" :title="isEdit ? '编辑账户' : '新增账户'" style="width: 480px">
        <n-form :model="form" label-placement="top">
          <n-form-item label="名称" required>
            <n-input v-model:value="form.name" placeholder="请输入账户名称" />
          </n-form-item>
          <n-form-item label="类型" required>
            <n-select
              v-model:value="form.account_type"
              :options="typeOptions"
              placeholder="选择账户类型"
            />
          </n-form-item>
          <n-form-item label="初始余额">
            <n-input-number
              v-model:value="form.initial_balance"
              style="width: 100%"
              placeholder="0.00"
            >
              <template #suffix>元</template>
            </n-input-number>
          </n-form-item>
          <n-form-item label="备注">
            <n-input v-model:value="form.remarks" type="textarea" placeholder="可选备注" />
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
  NInput, NInputNumber, NSelect, NSpace, NRadioGroup, NRadioButton,
  useMessage, NPopconfirm,
} from 'naive-ui'
import { getAccounts, createAccount, updateAccount, deleteAccount, getAccountTypes } from '@/api/finance'
import { useAuthStore } from '@/stores/auth'
import type { Account, AccountTypeItem } from '@/api/finance/type'

const authStore = useAuthStore()
const message = useMessage()
const loading = ref(false)
const submitting = ref(false)
const showModal = ref(false)
const isEdit = ref(false)
const data = ref<Account[]>([])
const accountTypes = ref<AccountTypeItem[]>([])
const filterType = ref<number | null>(null)

const canAdd = computed(() =>
  authStore.isSuperuser || authStore.permissions?.actions?.account?.includes('add')
)

const canChange = (): boolean =>
  !!(authStore.isSuperuser || authStore.permissions?.actions?.account?.includes('change'))

const canDelete = (): boolean =>
  !!(authStore.isSuperuser || authStore.permissions?.actions?.account?.includes('delete'))

const typeOptions = computed(() =>
  accountTypes.value.map((t) => ({ label: t.name, value: t.id }))
)

const typeLabels = computed(() => {
  const m: Record<number, string> = {}
  for (const t of accountTypes.value) {
    m[t.id] = t.name
  }
  return m
})

const filterTypeOptions = computed(() =>
  typeOptions.value
)

const displayData = computed(() => {
  if (!filterType.value) return data.value
  return data.value.filter((r) => r.account_type === filterType.value)
})

const columns = [
  { title: '名称', key: 'name' },
  {
    title: '类型',
    key: 'account_type',
    width: 100,
    render: (row: Account) => typeLabels.value[row.account_type] ?? row.account_type_name,
  },
  {
    title: '当前余额',
    key: 'current_balance',
    render: (row: Account) => {
      const bal = Number(row.current_balance)
      const color = bal >= 0 ? '#d03050' : '#18a058'
      return h('span', { style: { color, fontWeight: 'bold' } }, `${bal >= 0 ? '+' : ''}${row.current_balance}`)
    },
  },
  { title: '备注', key: 'remarks', ellipsis: { tooltip: true } },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render: (row: Account) => {
      const btns: any[] = []
      if (canChange()) {
        btns.push(h(NButton, { size: 'small', onClick: () => handleEdit(row) }, { default: () => '编辑' }))
      }
      if (canDelete()) {
        btns.push(h(NPopconfirm, { onPositiveClick: () => handleDelete(row.id) }, {
          trigger: () => h(NButton, { size: 'small', type: 'error' }, { default: () => '删除' }),
          default: () => '确定删除该账户？',
        }))
      }
      if (btns.length === 0) return '-'
      return h(NSpace, { size: 'small' }, { default: () => btns })
    },
  },
]

const form = ref({
  id: null as number | null,
  name: '',
  account_type: null as number | null,
  initial_balance: 0,
  remarks: '',
})

const loadData = async () => {
  loading.value = true
  try {
    const res = await getAccounts({ size: 500 })
    data.value = res.data.items
  } catch {
    console.error('Failed to load accounts')
  } finally {
    loading.value = false
  }
}

const loadAccountTypes = async () => {
  try {
    const res = await getAccountTypes()
    accountTypes.value = res.data
  } catch {
    console.error('Failed to load account types')
  }
}

const handleAdd = () => {
  isEdit.value = false
  form.value = { id: null, name: '', account_type: null, initial_balance: 0, remarks: '' }
  showModal.value = true
}

const handleEdit = (row: Account) => {
  isEdit.value = true
  form.value = {
    id: row.id,
    name: row.name,
    account_type: row.account_type,
    initial_balance: Number(row.initial_balance),
    remarks: row.remarks,
  }
  showModal.value = true
}

const handleDelete = async (id: number) => {
  try {
    await deleteAccount(id)
    message.success('删除成功')
    loadData()
  } catch {
    console.error('Failed to delete account')
  }
}

const handleSubmit = async () => {
  if (!form.value.name) {
    message.warning('请输入名称')
    return
  }
  if (!form.value.account_type) {
    message.warning('请选择账户类型')
    return
  }
  submitting.value = true
  try {
    const payload = {
      name: form.value.name,
      account_type: form.value.account_type,
      initial_balance: String(form.value.initial_balance),
      remarks: form.value.remarks,
    }
    if (isEdit.value && form.value.id) {
      await updateAccount(form.value.id, payload)
      message.success('更新成功')
    } else {
      await createAccount(payload)
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
  loadAccountTypes()
})
</script>
