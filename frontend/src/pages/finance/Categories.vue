<template>
  <div class="categories">
    <n-h1>分类管理</n-h1>
    <n-card title="分类列表">
      <template #header-extra>
        <n-button v-if="authStore.isSuperuser || authStore.permissions?.actions?.category?.includes('add')" type="primary" @click="handleAdd">新增分类</n-button>
      </template>

      <n-alert v-if="filterLedgerName" type="info" :bordered="false" closable @close="clearFilter" style="margin-bottom: 12px">
        <template #header>
          当前查看：<strong>{{ filterLedgerName }}</strong> 下的分类
        </template>
      </n-alert>

      <n-space vertical :size="12">
        <n-space align="center" wrap>
          <n-input
            v-model:value="searchName"
            placeholder="搜索分类名称..."
            clearable
            style="width: 200px"
          >
            <template #prefix>
              <n-icon><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="14"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg></n-icon>
            </template>
          </n-input>
          <n-divider vertical />
          <n-radio-group v-model:value="filterStatus" size="small">
            <n-radio-button value="all">全部</n-radio-button>
            <n-radio-button value="active">进行中</n-radio-button>
            <n-radio-button value="done">已完成</n-radio-button>
          </n-radio-group>
          <n-divider vertical />
          <n-space align="center" :size="4">
            <span style="font-size: 13px; color: #888; white-space: nowrap;">满意度</span>
            <n-rate v-model:value="filterStar" :count="5" size="small" />
            <span v-if="filterStar > 0" style="font-size: 13px; color: #888;">及以上</span>
          </n-space>
          <n-button v-if="hasActiveFilter" quaternary size="tiny" @click="clearAllFilters">清除筛选</n-button>
        </n-space>

        <n-data-table :columns="columns" :data="paginatedData" :loading="loading" :pagination="false" />
        <n-pagination
          v-if="displayData.length > 0"
          style="justify-content: flex-end; margin-top: 16px;"
          :page="pagState.page"
          :page-size="pagState.pageSize"
          :item-count="displayData.length"
          :page-sizes="[10, 20, 50, 100]"
          show-size-picker
          @update:page="onPageChange"
          @update:page-size="onPageSizeChange"
        />
      </n-space>
    </n-card>

    <n-modal v-model:show="showModal" preset="card" :title="isEdit ? '编辑分类' : '新增分类'" style="width: 520px">
      <n-form :model="form" label-placement="top">
        <n-form-item label="名称" required>
          <n-input v-model:value="form.name" placeholder="请输入分类名称" />
        </n-form-item>
        <n-form-item label="关联时间账本">
          <n-select
            v-model:value="form.time_ledger"
            :options="timeLedgerOptions"
            placeholder="选择时间账本（可选）"
            clearable
            filterable
          />
        </n-form-item>
        <n-form-item label="关联分类账本">
          <n-select
            v-model:value="form.category_ledger"
            :options="categoryLedgerOptions"
            placeholder="选择分类账本（可选）"
            clearable
            filterable
          />
        </n-form-item>
        <n-form-item label="预算金额">
          <n-input-number
            v-model:value="form.budget"
            :min="0"
            placeholder="0.00"
            style="width: 100%"
          >
            <template #suffix>元</template>
          </n-input-number>
        </n-form-item>
        <n-form-item label="状态">
          <n-switch v-model:value="form.is_complete">
            <template #checked>已完成</template>
            <template #unchecked>进行中</template>
          </n-switch>
        </n-form-item>
        <n-form-item label="满意度">
          <n-rate v-model:value="form.star" :count="5" />
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
import { useRoute, useRouter } from 'vue-router'
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
  NInputNumber,
  NSelect,
  NSpace,
  NRate,
  NSwitch,
  NAlert,
  NDivider,
  NIcon,
  useMessage,
  NPopconfirm,
} from 'naive-ui'
import { getCategories, createCategory, updateCategory, deleteCategory, getLedgers } from '@/api/finance'
import { useAuthStore } from '@/stores/auth'
import type { Category, Ledger } from '@/api/finance/type'

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()
const message = useMessage()
const loading = ref(false)
const submitting = ref(false)
const showModal = ref(false)
const isEdit = ref(false)
const data = ref<Category[]>([])
const ledgers = ref<Ledger[]>([])
const filterTimeLedger = ref<number | null>(null)
const filterCategoryLedger = ref<number | null>(null)
const filterLedgerName = ref('')
const searchName = ref('')
const filterStatus = ref('all')
const filterStar = ref(0)

const hasActiveFilter = computed(() =>
  searchName.value || filterStatus.value !== 'all' || filterStar.value > 0
)

const clearAllFilters = () => {
  searchName.value = ''
  filterStatus.value = 'all'
  filterStar.value = 0
}

const timeLedgerOptions = computed(() =>
  ledgers.value
    .filter((l) => l.ledger_type === "time" && !l.is_complete)
    .map((l) => ({ label: l.name, value: l.id }))
)

const categoryLedgerOptions = computed(() =>
  ledgers.value
    .filter((l) => l.ledger_type === "category" && !l.is_complete)
    .map((l) => ({ label: l.name, value: l.id }))
)

const displayData = computed(() =>
  data.value.filter((row) => {
    if (filterTimeLedger.value && row.time_ledger !== filterTimeLedger.value) return false
    if (filterCategoryLedger.value && row.category_ledger !== filterCategoryLedger.value) return false
    if (searchName.value && !row.name.includes(searchName.value)) return false
    if (filterStatus.value === 'active' && row.is_complete) return false
    if (filterStatus.value === 'done' && !row.is_complete) return false
    if (filterStar.value > 0 && row.star < filterStar.value) return false
    return true
  })
)

const pagState = reactive({ page: 1, pageSize: 20 })

const paginatedData = computed(() => {
  const start = (pagState.page - 1) * pagState.pageSize
  return displayData.value.slice(start, start + pagState.pageSize)
})

watch(() => displayData.value, () => { pagState.page = 1 })

const onPageChange = (p: number) => { pagState.page = p }
const onPageSizeChange = (size: number) => {
  pagState.pageSize = size
  pagState.page = 1
}

const clearFilter = () => {
  filterTimeLedger.value = null
  filterCategoryLedger.value = null
  filterLedgerName.value = ''
  router.replace({ query: {} })
}

const form = ref({
  id: null as number | null,
  name: '',
  time_ledger: null as number | null,
  category_ledger: null as number | null,
  budget: 0,
  star: 0,
  is_complete: false,
  remarks: '',
})
const navigateToTransactions = (row: Category) => {
  router.push({ name: 'transactions', query: { category_id: row.id, category_name: row.name } })
}

const columns = [
  {
    title: '名称',
    key: 'name',
    sorter: (a: Category, b: Category) => a.name.localeCompare(b.name),
    render: (row: Category) => {
      return h(
        'a',
        {
          style: { color: '#2d7cf6', cursor: 'pointer', textDecoration: 'none' },
          onClick: () => navigateToTransactions(row),
        },
        row.name
      )
    },
  },
  {
    title: '所属账本',
    key: 'ledger_names',
    render: (row: Category) => {
      const names = [row.time_ledger_name, row.category_ledger_name].filter(Boolean)
      return names.join(' / ') || '-'
    },
  },
  { title: '预算', key: 'budget' },
  {
    title: '实际金额',
    key: 'actual_amount',
    render: (row: Category) => {
    const actual = Number(row.actual_amount)
    const color = actual > 0 ? '#d03050' : '#18a058'
      return h('span', { style: { color, fontWeight: 'bold' } }, row.actual_amount)
    },
  },
  {
    title: '状态',
    key: 'is_complete',
    width: 100,
    render: (row: Category) => row.is_complete ? '已完成' : '进行中',
  },
  {
    title: '满意度',
    key: 'star',
    render: (row: Category) => '★'.repeat(row.star) || '-',
  },
  {
    title: '最近修改',
    key: 'updated_at',
    width: 170,
    sorter: (a: Category, b: Category) => new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime(),
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render: (row: Category) => {
      const btns: any[] = []
      if (authStore.isSuperuser || authStore.permissions?.actions?.category?.includes('change')) {
        btns.push(h(NButton, { size: 'small', onClick: () => handleEdit(row) }, { default: () => '编辑' }))
      }
      if (authStore.isSuperuser || authStore.permissions?.actions?.category?.includes('delete')) {
        btns.push(h(NPopconfirm, { onPositiveClick: () => handleDelete(row.id) }, {
          trigger: () => h(NButton, { size: 'small', type: 'error' }, { default: () => '删除' }),
          default: () => '确定删除该分类？',
        }))
      }
      if (btns.length === 0) return '-'
      return h(NSpace, { size: 'small' }, { default: () => btns })
    },
  },
]

const loadLedgers = async () => {
  try {
    const res = await getLedgers()
    ledgers.value = res.data.items
  } catch {
    console.error('Failed to load ledgers')
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const response = await getCategories({ size: 500 })
    data.value = response.data.items
  } catch (error) {
    console.error('Failed to fetch categories:', error)
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  isEdit.value = false
  form.value = { id: null, name: '', time_ledger: null, category_ledger: null, budget: 0, star: 0, is_complete: false, remarks: '' }
  showModal.value = true
}

const handleEdit = (row: Category) => {
  isEdit.value = true
  form.value = {
    id: row.id,
    name: row.name,
    time_ledger: row.time_ledger,
    category_ledger: row.category_ledger,
    budget: Number(row.budget),
    star: row.star,
    is_complete: row.is_complete,
    remarks: row.remarks,
  }
  showModal.value = true
}

const handleDelete = async (id: number) => {
  try {
    await deleteCategory(id)
    message.success('删除成功')
    loadData()
  } catch (error) {
    console.error('Failed to delete category:', error)
  }
}

const handleSubmit = async () => {
  if (!form.value.name) {
    message.warning('请输入名称')
    return
  }
  if (!form.value.time_ledger && !form.value.category_ledger) {
    message.warning('至少关联一个账本')
    return
  }

  submitting.value = true
  try {
    const payload = {
      name: form.value.name,
      time_ledger: form.value.time_ledger,
      category_ledger: form.value.category_ledger,
      budget: String(form.value.budget),
      star: form.value.star,
      is_complete: form.value.is_complete,
      remarks: form.value.remarks,
    }
    if (isEdit.value && form.value.id) {
      await updateCategory(form.value.id, payload)
      message.success('更新成功')
    } else {
      await createCategory(payload)
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

const applyQueryFilters = () => {
  const query = route.query
  if (query.time_ledger) {
    filterTimeLedger.value = Number(query.time_ledger)
    filterLedgerName.value = (query.ledger_name as string) || '时间账本'
  } else if (query.category_ledger) {
    filterCategoryLedger.value = Number(query.category_ledger)
    filterLedgerName.value = (query.ledger_name as string) || '分类账本'
  }
}

onMounted(() => {
  applyQueryFilters()
  loadData()
  loadLedgers()
})
</script>
