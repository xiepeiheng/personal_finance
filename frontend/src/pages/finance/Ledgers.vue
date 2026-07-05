<template>
  <div class="ledgers">
    <n-h1>账本管理</n-h1>
    <n-card title="账本列表">
      <template #header-extra>
        <n-button v-if="authStore.isSuperuser || authStore.permissions?.actions?.ledger?.includes('add')" type="primary" @click="handleAdd">新增账本</n-button>
      </template>

      <n-space vertical :size="16">
        <n-space align="center">
          <n-radio-group v-model:value="filterType" size="small">
            <n-radio-button value="all">全部</n-radio-button>
            <n-radio-button value="time">时间维度</n-radio-button>
            <n-radio-button value="category">分类维度</n-radio-button>
          </n-radio-group>
          <n-divider vertical />
          <n-radio-group v-model:value="filterStatus" size="small">
            <n-radio-button value="all">全部</n-radio-button>
            <n-radio-button value="active">进行中</n-radio-button>
            <n-radio-button value="done">已完成</n-radio-button>
          </n-radio-group>
          <n-tag v-if="filteredData.length !== data.length" size="small" type="info">
            筛选出 {{ filteredData.length }} / {{ data.length }} 条
          </n-tag>
        </n-space>

        <n-data-table
          :columns="columns"
          :data="paginatedData"
          :loading="loading"
          :pagination="false"
          :row-key="(row: Ledger) => row.id"
        />
        <n-pagination
          v-if="filteredData.length > 0"
          style="justify-content: flex-end; margin-top: 16px;"
          :page="pagState.page"
          :page-size="pagState.pageSize"
          :item-count="filteredData.length"
          :page-sizes="[10, 20, 50, 100]"
          show-size-picker
          @update:page="onPageChange"
          @update:page-size="onPageSizeChange"
        />
      </n-space>
    </n-card>

    <n-modal v-model:show="showModal" preset="card" :title="isEdit ? '编辑账本' : '新增账本'" style="width: 480px">
      <n-form :model="form" label-placement="top">
        <n-form-item label="名称" required>
          <n-input v-model:value="form.name" placeholder="请输入账本名称" />
        </n-form-item>
        <n-form-item label="类型" required>
          <n-radio-group v-model:value="form.ledger_type">
            <n-radio-button value="time">时间维度</n-radio-button>
            <n-radio-button value="category">分类维度</n-radio-button>
          </n-radio-group>
        </n-form-item>
        <n-form-item label="状态">
          <n-switch v-model:value="form.is_complete">
            <template #checked>已完成</template>
            <template #unchecked>进行中</template>
          </n-switch>
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, h, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  NCard,
  NH1,
  NButton,
  NDataTable,
  NPagination,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NSpace,
  NSwitch,
  NRadioGroup,
  NRadioButton,
  NTag,
  NDivider,
  useMessage,
  NPopconfirm,
} from 'naive-ui'
import { getLedgers, createLedger, updateLedger, deleteLedger } from '@/api/finance'
import { useAuthStore } from '@/stores/auth'
import type { Ledger, LedgerType } from '@/api/finance/type'

const authStore = useAuthStore()
const router = useRouter()
const message = useMessage()
const loading = ref(false)
const submitting = ref(false)
const showModal = ref(false)
const isEdit = ref(false)
const data = ref<Ledger[]>([])

const filterType = ref('all')
const filterStatus = ref('all')

const form = ref({
  id: null as number | null,
  name: '',
  ledger_type: 'time' as LedgerType,
  is_complete: false,
  remarks: '',
})

const filteredData = computed(() =>
  data.value.filter((row) => {
    if (filterType.value !== 'all' && row.ledger_type !== filterType.value) return false
    if (filterStatus.value === 'active' && row.is_complete) return false
    if (filterStatus.value === 'done' && !row.is_complete) return false
    return true
  })
)

const pagState = reactive({ page: 1, pageSize: 20 })

const paginatedData = computed(() => {
  const start = (pagState.page - 1) * pagState.pageSize
  return filteredData.value.slice(start, start + pagState.pageSize)
})

watch(() => filteredData.value, () => { pagState.page = 1 })

const onPageChange = (p: number) => { pagState.page = p }
const onPageSizeChange = (size: number) => {
  pagState.pageSize = size
  pagState.page = 1
}

const navigateToCategories = (row: Ledger) => {
  const paramKey = row.ledger_type === 'time' ? 'time_ledger' : 'category_ledger'
  router.push({ name: 'categories', query: { [paramKey]: row.id, ledger_name: row.name } })
}

const columns = [
  {
    title: '名称',
    key: 'name',
    sorter: (a: Ledger, b: Ledger) => a.name.localeCompare(b.name),
    render: (row: Ledger) => {
      return h(
        'a',
        {
          style: { color: '#2d7cf6', cursor: 'pointer', textDecoration: 'none' },
          onClick: () => navigateToCategories(row),
        },
        row.name
      )
    },
  },
  { title: '类型', key: 'ledger_type_display', width: 100 },
  {
    title: '余额',
    key: 'balance',
    sorter: (a: Ledger, b: Ledger) => Number(a.balance) - Number(b.balance),
    render: (row: Ledger) => {
      const balance = Number(row.balance)
      const color = balance >= 0 ? '#d03050' : '#18a058'
      return h('span', { style: { color, fontWeight: 'bold' } }, row.balance)
    },
  },
  {
    title: '状态',
    key: 'is_complete',
    width: 100,
    render: (row: Ledger) => row.is_complete ? '已完成' : '进行中',
  },
  { title: '备注', key: 'remarks', ellipsis: { tooltip: true } },
  {
    title: '最近修改',
    key: 'updated_at',
    width: 170,
    sorter: (a: Ledger, b: Ledger) => new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime(),
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render: (row: Ledger) => {
      const btns: any[] = []
      if (authStore.isSuperuser || authStore.permissions?.actions?.ledger?.includes('change')) {
        btns.push(h(NButton, { size: 'small', onClick: () => handleEdit(row) }, { default: () => '编辑' }))
      }
      if (authStore.isSuperuser || authStore.permissions?.actions?.ledger?.includes('delete')) {
        btns.push(h(NPopconfirm, { onPositiveClick: () => handleDelete(row.id) }, {
          trigger: () => h(NButton, { size: 'small', type: 'error' }, { default: () => '删除' }),
          default: () => '确定删除该账本？',
        }))
      }
      if (btns.length === 0) return '-'
      return h(NSpace, { size: 'small' }, { default: () => btns })
    },
  },
]

const loadData = async () => {
  loading.value = true
  try {
    const response = await getLedgers({ size: 500 })
    data.value = response.data.items
  } catch (error) {
    console.error('Failed to fetch ledgers:', error)
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  isEdit.value = false
  form.value = { id: null, name: '', ledger_type: 'time', is_complete: false, remarks: '' }
  showModal.value = true
}

const handleEdit = (row: Ledger) => {
  isEdit.value = true
  form.value = {
    id: row.id,
    name: row.name,
    ledger_type: row.ledger_type,
    is_complete: row.is_complete,
    remarks: row.remarks,
  }
  showModal.value = true
}

const handleDelete = async (id: number) => {
  try {
    await deleteLedger(id)
    message.success('删除成功')
    loadData()
  } catch (error) {
    console.error('Failed to delete ledger:', error)
  }
}

const handleSubmit = async () => {
  if (!form.value.name) {
    message.warning('请输入名称')
    return
  }

  submitting.value = true
  try {
    const payload = {
      name: form.value.name,
      ledger_type: form.value.ledger_type,
      is_complete: form.value.is_complete,
      remarks: form.value.remarks,
    }
    if (isEdit.value && form.value.id) {
      await updateLedger(form.value.id, payload)
      message.success('更新成功')
    } else {
      await createLedger(payload)
      message.success('创建成功')
    }
    showModal.value = false
    loadData()
  } catch (error) {
    console.error('Failed to submit:', error)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>
