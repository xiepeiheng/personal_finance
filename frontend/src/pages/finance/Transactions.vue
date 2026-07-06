<template>
  <div class="transactions">
    <n-h1>交易记录</n-h1>
    <n-card title="交易列表">
      <template #header-extra>
        <n-button v-if="authStore.isSuperuser || authStore.permissions?.actions?.transaction?.includes('add')" type="primary" @click="handleAdd">新增交易</n-button>
        <n-button v-if="authStore.isSuperuser || authStore.permissions?.actions?.transaction?.includes('add')" @click="showBatchModal = true" style="margin-left: 8px;">批量添加</n-button>
      </template>

      <n-space vertical :size="12" style="margin-bottom: 12px">
        <n-space align="center" wrap>
          <n-select
            v-model:value="filterCategoryId"
            :options="categoryFilterOptions"
            placeholder="选择分类..."
            clearable
            filterable
            style="width: 200px"
          />
          <n-select
            v-model:value="filterLedgerId"
            :options="ledgerFilterOptions"
            placeholder="选择账本..."
            clearable
            filterable
            style="width: 200px"
          />
          <n-select
            v-model:value="filterAccountId"
            :options="accountFilterOptions"
            placeholder="选择账户..."
            clearable
            filterable
            style="width: 200px"
          />
          <n-divider vertical />
          <n-date-picker
            v-model:value="filterDateRange"
            type="daterange"
            placeholder="选择日期范围"
            clearable
            style="width: 240px"
          />
          <n-input
            v-model:value="filterPartner"
            placeholder="搜索交易对象..."
            clearable
            style="width: 160px"
          />
          <n-radio-group v-model:value="filterType" size="small">
            <n-radio-button value="all">全部</n-radio-button>
            <n-radio-button value="income">收入</n-radio-button>
            <n-radio-button value="expense">支出</n-radio-button>
          </n-radio-group>
          <n-input-number
            v-model:value="filterAmountMin"
            placeholder="金额"
            :min="0"
            style="width: 130px"
          >
            <template #suffix>起</template>
          </n-input-number>
          <n-input-number
            v-model:value="filterAmountMax"
            placeholder="金额"
            :min="0"
            style="width: 130px"
          >
            <template #suffix>止</template>
          </n-input-number>
          <n-divider vertical />
          <n-space align="center" :size="4">
            <span style="font-size: 13px; color: #888; white-space: nowrap;">满意度</span>
            <n-rate v-model:value="filterStar" :count="5" size="small" />
            <span v-if="filterStar > 0" style="font-size: 13px; color: #888;">及以上</span>
          </n-space>
          <n-button type="primary" size="small" :disabled="!hasActiveFilter" @click="handleSearch">搜索</n-button>
          <n-button v-if="hasActiveFilter" quaternary size="tiny" @click="clearAllFilters">清除筛选</n-button>
        </n-space>
      </n-space>

      <n-space style="margin-bottom: 8px; font-size: 13px;" align="center">
        <span>收入：<span style="color:#d03050;font-weight:bold">{{ Number(filterSummary.income).toFixed(2) }}</span> 元</span>
        <n-divider vertical />
        <span>支出：<span style="color:#18a058;font-weight:bold">{{ Number(filterSummary.expense).toFixed(2) }}</span> 元</span>
        <n-divider vertical />
        <span>结余：<span :style="{ color: Number(filterSummary.net) >= 0 ? '#d03050' : '#18a058', fontWeight: 'bold' }">{{ Number(filterSummary.net) >= 0 ? '+' : '' }}{{ Number(filterSummary.net).toFixed(2) }}</span> 元</span>
        <span v-if="pagState.itemCount > 0" style="color:#999; font-size:12px;">共 {{ pagState.itemCount }} 笔</span>
      </n-space>

      <n-data-table
        :columns="columns"
        :data="data"
        :loading="loading"
        :pagination="false"
      />
      <n-pagination
        style="justify-content: flex-end; margin-top: 16px;"
        :page="pagState.page"
        :page-size="pagState.pageSize"
        :item-count="pagState.itemCount"
        :page-sizes="[10, 20, 50, 100]"
        show-size-picker
        @update:page="onPageChange"
        @update:page-size="onPageSizeChange"
      />
    </n-card>

    <TransactionForm
      :show="showModal"
      :categories="categories"
      :ledgers="ledgers"
      :accounts="accounts"
      :initial-category-id="newCategoryId"
      :initial-date="newDate"
      :edit-transaction="editTransaction"
      @close="showModal = false; editTransaction = null"
      @saved="onSaved"
    />

    <n-modal v-model:show="showBatchModal" preset="card" title="批量添加交易" style="width: 880px">
      <n-space vertical :size="12">
        <n-alert v-if="batchSubmitted > 0" type="success" :bordered="false">
          已成功添加 {{ batchSubmitted }} 条，{{ batchRows.filter(r => !r._submitted).length }} 条待处理
        </n-alert>
        <n-data-table
          :columns="batchColumns"
          :data="batchRows"
          :pagination="false"
          size="small"
          :max-height="400"
        />
        <n-space justify="space-between">
          <n-button size="small" @click="addBatchRow">添加行</n-button>
          <n-space>
            <n-button @click="showBatchModal = false; resetBatch()">取消</n-button>
            <n-button type="primary" @click="submitBatch" :loading="batchSubmitting">
              提交 {{ batchRows.filter(r => !r._submitted).length }} 条
            </n-button>
          </n-space>
        </n-space>
      </n-space>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, h, watch, onMounted } from 'vue'
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
  NDatePicker,
  NSpace,
  NDivider,
  NRate,
  useMessage,
  NPopconfirm,
} from 'naive-ui'
import { getTransactions, createTransaction, updateTransaction, deleteTransaction, getCategories, getLedgers, getAccounts, batchCreateTransactions, getSummary } from '@/api/finance'
import { useAuthStore } from '@/stores/auth'
import type { Transaction, Category, Ledger, Account, BatchCreateItem } from '@/api/finance/type'
import TransactionForm from '@/components/TransactionForm.vue'

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()
const message = useMessage()
const loading = ref(false)
const showModal = ref(false)
const data = ref<Transaction[]>([])
const categories = ref<Category[]>([])
const ledgers = ref<Ledger[]>([])
const accounts = ref<Account[]>([])
const filterCategoryId = ref<number | null>(null)
const filterDateRange = ref<[number, number] | null>(null)
const filterPartner = ref('')
const filterAmountMin = ref<number | null>(null)
const filterAmountMax = ref<number | null>(null)
const filterStar = ref(0)
const filterType = ref('all')

const hasActiveFilter = computed(() =>
  filterCategoryId.value !== null || filterLedgerId.value !== null || filterDateRange.value || filterPartner.value || filterAmountMin.value !== null || filterAmountMax.value !== null || filterStar.value > 0 || filterType.value !== 'all'
)

const handleSearch = () => {
  pagState.page = 1
  loadData()
}

const clearAllFilters = () => {
  filterCategoryId.value = null
  filterLedgerId.value = null
  filterDateRange.value = null
  filterPartner.value = ''
  filterAmountMin.value = null
  filterAmountMax.value = null
  filterStar.value = 0
  filterType.value = 'all'
  pagState.page = 1
  pagState.itemCount = 0
  data.value = []
  filterSummary.value = { income: '0.00', expense: '0.00', net: '0.00' }
}

interface BatchRow {
  _key: number
  _submitted: boolean
  _error: string
  category: number | null
  trade_time: number | null
  partner: string
  amount: number | null
  channel: string
}

const showBatchModal = ref(false)
const batchSubmitting = ref(false)
const batchSubmitted = ref(0)
let batchKeySeq = 0

const batchRows = ref<BatchRow[]>([])

const batchColumns = [
  { title: '#', key: '_key', width: 40, render: (_: any, idx: number) => idx + 1 },
  {
    title: '分类',
    key: 'category',
    width: 150,
    render: (row: BatchRow, idx: number) => {
      const error = row._error?.includes('分类') ? 'error' : null
      return h(NSelect, {
        value: row.category,
        options: categoryOptions.value,
        placeholder: '选择',
        filterable: true,
        style: { width: '100%' },
        status: error,
        'onUpdate:value': (v: number | null) => { batchRows.value[idx].category = v },
      })
    },
  },
  {
    title: '日期',
    key: 'trade_time',
    width: 140,
    render: (row: BatchRow, idx: number) => {
      return h(NDatePicker, {
        value: row.trade_time,
        type: 'date',
        placeholder: '日期',
        style: { width: '100%' },
        'onUpdate:value': (v: number | null) => { batchRows.value[idx].trade_time = v },
      })
    },
  },
  {
    title: '对象',
    key: 'partner',
    width: 120,
    render: (row: BatchRow, idx: number) => {
      const error = row._error?.includes('对象') || row._error?.includes('partner') ? 'error' : null
      return h(NInput, {
        value: row.partner,
        placeholder: '对象',
        status: error,
        'onUpdate:value': (v: string) => { batchRows.value[idx].partner = v },
      })
    },
  },
  {
    title: '金额',
    key: 'amount',
    width: 110,
    render: (row: BatchRow, idx: number) => {
      const error = row._error?.includes('金额') || row._error?.includes('amount') ? 'error' : null
      return h(NInputNumber, {
        value: row.amount,
        placeholder: '金额',
        style: { width: '100%' },
        status: error,
        'onUpdate:value': (v: number | null) => { batchRows.value[idx].amount = v },
      })
    },
  },
  {
    title: '渠道',
    key: 'channel',
    width: 100,
    render: (row: BatchRow, idx: number) => {
      return h(NInput, {
        value: row.channel,
        placeholder: '渠道',
        'onUpdate:value': (v: string) => { batchRows.value[idx].channel = v },
      })
    },
  },
  {
    title: '结果',
    key: '_result',
    width: 80,
    render: (row: BatchRow) => {
      if (row._submitted) return h('span', { style: 'color:#18a058;font-weight:bold' }, '✓')
      if (row._error) return h('span', { style: 'color:#d03050;font-size:12px' }, '✗')
      return ''
    },
  },
  {
    title: '',
    key: '_action',
    width: 50,
    render: (_: any, idx: number) => {
      return h(NButton, {
        size: 'tiny', type: 'error', quaternary: true,
        onClick: () => { batchRows.value.splice(idx, 1) },
      }, () => '✕')
    },
  },
]

const addBatchRow = () => {
  batchRows.value.push({
    _key: ++batchKeySeq,
    _submitted: false,
    _error: '',
    category: null,
    trade_time: null,
    partner: '',
    amount: null,
    channel: '',
  })
}

const resetBatch = () => {
  batchRows.value = []
  batchSubmitted.value = 0
  batchKeySeq = 0
}

const submitBatch = async () => {
  const pending = batchRows.value.filter(r => !r._submitted)
  if (pending.length === 0) return

  // clear old errors
  for (const r of pending) r._error = ''

  const items: BatchCreateItem[] = pending.map((r) => {
    const date = r.trade_time ? new Date(r.trade_time) : new Date()
    const tradeDate = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
    return {
      category: r.category!,
      trade_time: tradeDate,
      partner: r.partner,
      amount: String(r.amount ?? 0),
      channel: r.channel,
    }
  })

  batchSubmitting.value = true
  try {
    const res = await batchCreateTransactions(items)
    const errors = res.data.failed || []
    const errorSet = new Set(errors.map((e: any) => e.row))

    pending.forEach((r, i) => {
      const errInfo = errors.find((e: any) => e.row === i)
      if (errInfo) {
        const msgs: string[] = []
        for (const [, v] of Object.entries(errInfo.errors || {})) {
          if (Array.isArray(v)) msgs.push(...v)
          else msgs.push(String(v))
        }
        r._error = msgs.join('; ')
      } else {
        r._submitted = true
        batchSubmitted.value++
      }
    })

    if (errorSet.size === 0) {
      message.success(`全部 ${pending.length} 条添加成功`)
      loadData()
    } else {
      const ok = pending.length - errorSet.size
      message.warning(`成功 ${ok} 条，${errorSet.size} 条需修正`)
      loadData()
    }
  } catch {
    message.error('提交失败，请检查网络')
  } finally {
    batchSubmitting.value = false
  }
}

const filterLedgerId = ref<number | null>(null)
const filterAccountId = ref<number | null>(null)

const pagState = reactive({
  page: 1,
  pageSize: 20,
  itemCount: 0,
})

const ledgerFilterOptions = computed(() =>
  ledgers.value.map((l) => ({
    label: `${l.name}（${l.ledger_type_display}）余额：${l.balance}`,
    value: l.id,
  }))
)

const accountFilterOptions = computed(() =>
  accounts.value.map((a) => ({
    label: `${a.name}（${a.account_type_name}）余额：${a.current_balance}`,
    value: a.id,
  }))
)

const categoryFilterOptions = computed(() =>
  categories.value
    .filter((c) => {
      if (filterLedgerId.value) {
        return c.time_ledger === filterLedgerId.value || c.category_ledger === filterLedgerId.value
      }
      return true
    })
    .map((c) => {
      const ledgerNames = [c.time_ledger_name, c.category_ledger_name].filter(Boolean)
      const suffix = ledgerNames.length > 0 ? `（${ledgerNames.join(' / ')}）` : ''
      return { label: `${c.name} ${suffix}`, value: c.id }
    })
)

const categoryOptions = computed(() =>
  categories.value
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

const categoryMap = computed(() => {
  const map: Record<number, string> = {}
  for (const c of categories.value) {
    map[c.id] = c.name
  }
  return map
})

const newCategoryId = ref<number | null>(null)
const newDate = ref<number | null>(null)
const editTransaction = ref<Transaction | null>(null)

const filterSummary = ref({ income: '0.00', expense: '0.00', net: '0.00' })

const handleAdd = () => {
  editTransaction.value = null
  newCategoryId.value = filterCategoryId.value
  newDate.value = filterDateRange.value ? filterDateRange.value[1] : null
  showModal.value = true
}

const handleEdit = (row: Transaction) => {
  editTransaction.value = row
  showModal.value = true
}

const onSaved = () => {
  showModal.value = false
  editTransaction.value = null
  loadData()
}

const form = ref({
  id: null as number | null,
  category: null as number | null,
  trade_time: null as number | null,
  partner: '',
  amount: null as number | null,
  star: 5,
  is_complete: false,
  remarks: '',
})

const amountType = ref<'expense' | 'income'>('expense')

const onPageChange = (p: number) => {
  pagState.page = p
  loadData()
}

const onPageSizeChange = (size: number) => {
  pagState.pageSize = size
  pagState.page = 1
  loadData()
}

const columns = [
  {
    title: '日期',
    key: 'trade_time',
    sorter: (a: Transaction, b: Transaction) => new Date(a.trade_time).getTime() - new Date(b.trade_time).getTime(),
  },
  { title: '对象', key: 'partner' },
  {
    title: '金额',
    key: 'amount',
    sorter: (a: Transaction, b: Transaction) => Number(a.amount) - Number(b.amount),
    render: (row: Transaction) => {
      const amount = Number(row.amount)
      const color = amount >= 0 ? '#d03050' : '#18a058'
      const prefix = amount >= 0 ? '+' : ''
      return h('span', { style: { color, fontWeight: 'bold' } }, `${prefix}${row.amount}`)
    },
  },
  {
    title: '分类',
    key: 'category',
    render: (row: Transaction) => {
      const name = categoryMap.value[row.category]
      if (!name) return `ID:${row.category}`
      return h('a', {
        style: { color: '#2d7cf6', cursor: 'pointer', textDecoration: 'none' },
        onClick: () => router.push({ query: { category_id: row.category, category_name: name } }),
      }, name)
    },
  },
  {
    title: '满意度',
    key: 'star',
    width: 120,
    render: (row: Transaction) => '★'.repeat(row.star) || '-',
  },
  { title: '渠道', key: 'channel' },
  {
    title: '备注',
    key: 'remarks',
    width: 200,
    ellipsis: { tooltip: true },
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render: (row: Transaction) => {
      const btns: any[] = []
      if (authStore.isSuperuser || authStore.permissions?.actions?.transaction?.includes('change')) {
        btns.push(h(NButton, { size: 'small', onClick: () => handleEdit(row) }, { default: () => '编辑' }))
      }
      if (authStore.isSuperuser || authStore.permissions?.actions?.transaction?.includes('delete')) {
        btns.push(h(NPopconfirm, { onPositiveClick: () => handleDelete(row.id) }, {
          trigger: () => h(NButton, { size: 'small', type: 'error' }, { default: () => '删除' }),
          default: () => '确定删除？',
        }))
      }
      if (btns.length === 0) return '-'
      return h(NSpace, { size: 'small' }, { default: () => btns })
    },
  },
]

const loadCategories = async () => {
  try {
    const res = await getCategories({ size: 500 })
    categories.value = res.data.items
  } catch {
    console.error('Failed to load categories')
  }
}

const loadLedgers = async () => {
  try {
    const res = await getLedgers({ size: 500 })
    ledgers.value = res.data.items
  } catch {
    console.error('Failed to load ledgers')
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

const toDateStr = (ts: number) => {
  const d = new Date(ts)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const loadData = async () => {
  loading.value = true
  try {
    const params: Record<string, any> = { page: pagState.page, size: pagState.pageSize }
    if (filterCategoryId.value) params.category_id = filterCategoryId.value
    if (filterLedgerId.value) params.ledger_id = filterLedgerId.value
    if (filterAccountId.value) params.account_id = filterAccountId.value
    if (filterDateRange.value) {
      params.date_from = toDateStr(filterDateRange.value[0])
      params.date_to = toDateStr(filterDateRange.value[1])
    }
    if (filterPartner.value) params.partner = filterPartner.value
    if (filterAmountMin.value !== null) params.amount_min = filterAmountMin.value
    if (filterAmountMax.value !== null) params.amount_max = filterAmountMax.value
    if (filterType.value !== 'all') params.type = filterType.value
    if (filterStar.value > 0) params.star = filterStar.value
    const response = await getTransactions(params)
    data.value = response.data.items
    pagState.itemCount = response.data.total
  } catch (error) {
    console.error('Failed to fetch transactions:', error)
  } finally {
    loading.value = false
  }
  loadSummary()
}

const loadSummary = async () => {
  if (!hasActiveFilter.value) return
  const params: Record<string, any> = {}
  if (filterCategoryId.value) params.category_id = filterCategoryId.value
  if (filterLedgerId.value) params.ledger_id = filterLedgerId.value
  if (filterAccountId.value) params.account_id = filterAccountId.value
  if (filterDateRange.value) {
    params.date_from = toDateStr(filterDateRange.value[0])
    params.date_to = toDateStr(filterDateRange.value[1])
  }
  if (filterPartner.value) params.partner = filterPartner.value
  if (filterAmountMin.value !== null) params.amount_min = filterAmountMin.value
  if (filterAmountMax.value !== null) params.amount_max = filterAmountMax.value
  if (filterType.value !== 'all') params.type = filterType.value
  if (filterStar.value > 0) params.star = filterStar.value
  try {
    const res = await getSummary(params)
    filterSummary.value = {
      income: res.data.total_income,
      expense: res.data.total_expense,
      net: res.data.net,
    }
  } catch {
    console.error('Failed to load summary')
  }
}

const handleDelete = async (id: number) => {
  try {
    await deleteTransaction(id)
    message.success('删除成功')
    loadData()
  } catch (error) {
    console.error('Failed to delete transaction:', error)
  }
}

const applyQueryFilters = () => {
  const query = route.query
  if (query.category_id) {
    filterCategoryId.value = Number(query.category_id)
    if (!query.date_from && !query.date_to) {
      filterDateRange.value = null
    }
  }
  if (query.ledger_id) {
    filterLedgerId.value = Number(query.ledger_id)
    if (!query.date_from && !query.date_to) {
      filterDateRange.value = null
    }
  }
  if (query.date_from && query.date_to) {
    const from = new Date(query.date_from as string).getTime()
    const to = new Date(query.date_to as string).getTime()
    filterDateRange.value = [from, to]
  }
  if (!query.category_id && !query.ledger_id && !query.date_from) {
    const d = new Date()
    filterDateRange.value = [
      new Date(d.getFullYear(), d.getMonth(), 1).getTime(),
      new Date(d.getFullYear(), d.getMonth() + 1, 0).getTime(),
    ]
  }
}

watch(() => route.query, () => {
  applyQueryFilters()
  loadData()
}, { deep: true })

onMounted(() => {
  applyQueryFilters()
  loadData()
  loadCategories()
  loadLedgers()
  loadAccounts()
})
</script>
