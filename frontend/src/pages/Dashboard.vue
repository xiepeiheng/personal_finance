<template>
  <div class="dashboard">
    <n-h1>首页概览</n-h1>

    <div v-if="!hasFinanceAccess" class="welcome">
      <n-h2>欢迎使用财务记账系统</n-h2>
      <p style="color: #888; font-size: 15px;">
        你还没有分配财务相关的权限，请联系管理员开通账本、分类、交易等模块的访问权限。
      </p>
      <n-button type="primary" @click="router.push({ name: 'settings' })">前往设置</n-button>
    </div>

    <template v-else>
    <n-space align="center" style="margin-bottom: 12px;">
    <n-date-picker
      v-model:value="monthRange"
      type="monthrange"
      style="width: 280px"
    />
    </n-space>

    <n-grid :cols="3" :x-gap="16" style="margin-bottom: 16px;">
      <n-gi>
        <n-card title="收入" size="small">
          <n-statistic :value="Number(summary.total_income).toFixed(2)" :style="incomeStyle">
            <template #suffix> 元</template>
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card title="支出" size="small">
          <n-statistic :value="Number(summary.total_expense).toFixed(2)" :style="expenseStyle">
            <template #suffix> 元</template>
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card title="结余" size="small">
          <n-statistic :value="formatNet" :style="netStyle">
            <template #suffix> 元</template>
          </n-statistic>
        </n-card>
      </n-gi>
    </n-grid>

    <n-grid :cols="2" :x-gap="16" style="margin-bottom: 24px;">
      <n-gi>
        <n-card title="分类支出排行" size="small">
          <div v-if="expenseCategories.length === 0" style="padding: 24px 0; text-align: center; color: #888;">
            本月暂无支出
          </div>
          <div v-else class="bar-chart">
            <div v-for="cat in expenseCategories" :key="cat.id" class="bar-row">
              <div class="bar-label">{{ cat.name }}</div>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: (cat.ratio * 100).toFixed(1) + '%' }" />
              </div>
              <div class="bar-value">{{ Number(cat.absTotal).toFixed(0) }}元</div>
            </div>
          </div>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card title="最近交易" size="small">
          <n-data-table
            v-if="summary.recent_transactions?.length"
            :columns="txColumns"
            :data="summary.recent_transactions.slice(0, 4)"
            :pagination="false"
            :bordered="false"
            size="small"
          />
          <div v-else style="padding: 24px 0; text-align: center; color: #888;">
            本月暂无交易
          </div>
        </n-card>
      </n-gi>
    </n-grid>

    <n-card title="日历" size="small">
      <n-calendar
        v-model:value="calendarDate"
        #="{ year, month, date }"
        :is-date-disabled="noop"
        @panel-change="onPanelChange"
        @update:value="showDayDetail"
      >
        <div v-if="dayText(year, month, date)?.income" class="day-income">+ {{ dayText(year, month, date).income }}</div>
        <div v-if="dayText(year, month, date)?.expense" class="day-expense">- {{ dayText(year, month, date).expense }}</div>
      </n-calendar>
      <div class="cal-legend">
        <span class="legend-dot income-dot"></span> 收入
        <span class="legend-dot expense-dot"></span> 支出
      </div>
    </n-card>

    <n-modal v-model:show="dayDetailVisible" preset="card" :title="`${dayDetailDate} 交易记录`" style="width: 920px">
      <n-data-table
        :columns="dayDetailColumns"
        :data="dayDetailList"
        :loading="dayDetailLoading"
        :pagination="false"
        size="small"
      />
      <template #footer>
        <n-space justify="center">
          <n-button size="small" @click="showFormInline = true">
            <template #icon>+</template> 补记一笔
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <TransactionForm
      :show="showFormInline"
      :categories="allCategories"
      :ledgers="allLedgers"
      :initial-date="formInlineDate"
      :edit-transaction="formInlineEdit"
      @close="showFormInline = false; formInlineEdit = null"
      @saved="onFormSaved"
    />
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  NCard,
  NCalendar,
  NModal,
  NDataTable,
  NStatistic,
  NGrid,
  NGi,
  NH1,
  NH2,
  NButton,
  NSpace,
  NDatePicker,
  NPopconfirm,
  useMessage,
} from 'naive-ui'
import { getSummary, getDailySummary, getTransactions, getCategories, getLedgers, deleteTransaction } from '@/api/finance'
import { useAuthStore } from '@/stores/auth'
import type { Summary, Transaction, DailySummary, Category, Ledger } from '@/api/finance/type'
import TransactionForm from '@/components/TransactionForm.vue'

const authStore = useAuthStore()
const router = useRouter()

const hasFinanceAccess = computed(() => {
  const models = authStore.permissions?.modules?.finance
  return !!models && models.length > 0
})

const noop = () => false

const now = new Date()
const calendarDate = ref(Date.now())
const panelYear = ref(now.getFullYear())
const panelMonth = ref(now.getMonth() + 1)

const onPanelChange = ({ year, month }: { year: number; month: number }) => {
  panelYear.value = year
  panelMonth.value = month
  const start = `${year}-${String(month).padStart(2, '0')}-01`
  const end = `${year}-${String(month).padStart(2, '0')}-${String(new Date(year, month, 0).getDate()).padStart(2, '0')}`
  getDailySummary({ date_from: start, date_to: end })
    .then((res) => { dailyList.value = res.data })
    .catch(() => {})
}

const dayDetailVisible = ref(false)
const dayDetailDate = ref('')
const dayDetailList = ref<Transaction[]>([])
const dayDetailLoading = ref(false)

const showFormInline = ref(false)
const formInlineDate = ref<number | null>(null)
const formInlineEdit = ref<Transaction | null>(null)
const allCategories = ref<Category[]>([])
const allLedgers = ref<Ledger[]>([])

const onFormSaved = () => {
  showFormInline.value = false
  formInlineEdit.value = null
  loadDaily()
  loadSummary()
}

const handleDayEdit = (row: Transaction) => {
  formInlineDate.value = new Date(row.trade_time).getTime()
  formInlineEdit.value = row
  showFormInline.value = true
}

const handleDayDelete = async (id: number) => {
  try {
    await deleteTransaction(id)
    message.success('已删除')
    dayDetailList.value = dayDetailList.value.filter((t) => t.id !== id)
    loadDaily()
    loadSummary()
  } catch {
    message.error('删除失败')
  }
}

const showDayDetail = (_ts: number, { year, month, date }: { year: number; month: number; date: number }) => {
  const day = `${year}-${String(month).padStart(2, '0')}-${String(date).padStart(2, '0')}`
  dayDetailDate.value = day
  formInlineDate.value = new Date(year, month - 1, date).getTime()
  dayDetailLoading.value = true
  dayDetailVisible.value = true
  getTransactions({ page: 1, size: 100, date_from: day, date_to: day })
    .then((res) => {
      dayDetailList.value = res.data.items
    })
    .catch(() => {
      dayDetailList.value = []
    })
    .finally(() => {
      dayDetailLoading.value = false
    })
}

const goAddTransaction = (date: string) => {
  dayDetailVisible.value = false
  router.push({ name: 'transactions', query: { date_from: date, date_to: date } })
}

const message = useMessage()

const categoryInfo = computed(() => {
  const m: Record<number, { name: string; ledgers: string }> = {}
  for (const c of allCategories.value) {
    const names = [c.time_ledger_name, c.category_ledger_name].filter(Boolean)
    m[c.id] = { name: c.name, ledgers: names.join(' / ') || '-' }
  }
  return m
})

const dayDetailColumns = [
  { title: '时间', key: 'trade_time', width: 100 },
  { title: '对象', key: 'partner', width: 100 },
  {
    title: '金额',
    key: 'amount',
    width: 100,
    render: (row: Transaction) => {
      const amt = Number(row.amount)
      const color = amt >= 0 ? '#d03050' : '#18a058'
      return h('span', { style: { color, fontWeight: 'bold' } }, row.amount)
    },
  },
  {
    title: '分类',
    key: 'category',
    width: 120,
    render: (row: Transaction) => categoryInfo.value[row.category]?.name ?? `ID:${row.category}`,
  },
  {
    title: '所属账本',
    key: 'category',
    width: 160,
    ellipsis: { tooltip: true },
    render: (row: Transaction) => categoryInfo.value[row.category]?.ledgers ?? '-',
  },
  { title: '渠道', key: 'channel', width: 80 },
  { title: '备注', key: 'remarks', ellipsis: { tooltip: true } },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render: (row: Transaction) => {
      return h(NSpace, { size: 'small' }, {
        default: () => [
          h(NButton, { size: 'tiny', onClick: () => handleDayEdit(row) }, { default: () => '编辑' }),
          h(NPopconfirm, {
            onPositiveClick: () => handleDayDelete(row.id),
          }, {
            trigger: () => h(NButton, { size: 'tiny', type: 'error' }, { default: () => '删除' }),
            default: () => '确定删除？',
          }),
        ],
      })
    },
  },
]

const summary = ref<Summary>({
  total_income: '0.00',
  total_expense: '0.00',
  net: '0.00',
  categories: [],
  recent_transactions: [],
})

const dailyList = ref<DailySummary[]>([])
const dailyMap = computed(() => {
  const m: Record<string, DailySummary> = {}
  for (const d of dailyList.value) {
    m[d.date] = d
  }
  return m
})

const dayText = (year: number, month: number, date: number) => {
  const iso = `${year}-${String(month).padStart(2, '0')}-${String(date).padStart(2, '0')}`
  const info = dailyMap.value[iso]
  if (!info || (Number(info.income) === 0 && Number(info.expense) === 0)) return null
  return {
    income: Number(info.income) > 0 ? info.income : undefined,
    expense: Number(info.expense) > 0 ? info.expense : undefined,
  }
}

const monthRange = ref<[number, number]>([
  new Date(now.getFullYear(), now.getMonth(), 1).getTime(),
  new Date(now.getFullYear(), now.getMonth() + 1, 0).getTime(),
])

const incomeStyle = { color: '#d03050' }
const expenseStyle = { color: '#18a058' }
const netStyle = computed(() => ({
  color: Number(summary.value.net) >= 0 ? '#d03050' : '#18a058',
}))

const formatNet = computed(() => {
  const n = Number(summary.value.net)
  const prefix = n >= 0 ? '+' : ''
  return `${prefix}${n.toFixed(2)}`
})

const expenseCategories = computed(() => {
  const totalExpense = Number(summary.value.total_expense)
  if (totalExpense === 0) return []
  return summary.value.categories
    .filter((c) => Number(c.total) < 0)
    .map((c) => ({
      ...c,
      absTotal: Math.abs(Number(c.total)),
      ratio: Math.abs(Number(c.total)) / totalExpense,
    }))
    .sort((a, b) => b.absTotal - a.absTotal)
})

const txColumns = [
  { title: '日期', key: 'trade_time', width: 100 },
  { title: '对象', key: 'partner' },
  {
    title: '金额',
    key: 'amount',
    width: 100,
    render: (row: Transaction) => {
      const amt = Number(row.amount)
      const color = amt >= 0 ? '#d03050' : '#18a058'
      return h('span', { style: { color, fontWeight: 'bold' } }, row.amount)
    },
  },
]

const queryRange = computed((): [string, string] | null => {
  if (!monthRange.value) return null
  const [startTs, endTs] = monthRange.value
  let end = new Date(endTs)
  if (end.getDate() === 1) {
    end = new Date(end.getFullYear(), end.getMonth() + 1, 0)
  }
  return [toDateStr(startTs), toDateStr(end.getTime())]
})

const toDateStr = (ts: number) => {
  const d = new Date(ts)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const onMonthChange = () => {
  loadSummary()
  loadDaily()
}

const loadSummary = async () => {
  const range = queryRange.value
  if (!range) return
  try {
    const res = await getSummary({ date_from: range[0], date_to: range[1] })
    summary.value = res.data
  } catch {
    console.error('Failed to load summary')
  }
}

const loadDaily = async () => {
  const start = `${panelYear.value}-${String(panelMonth.value).padStart(2, '0')}-01`
  const end = `${panelYear.value}-${String(panelMonth.value).padStart(2, '0')}-${String(new Date(panelYear.value, panelMonth.value, 0).getDate()).padStart(2, '0')}`
  try {
    const res = await getDailySummary({ date_from: start, date_to: end })
    dailyList.value = res.data
  } catch {
    console.error('Failed to load daily summary')
  }
}

watch(monthRange, () => {
  loadSummary()
})

onMounted(() => {
  loadSummary()
  loadDaily()
  getCategories({ size: 500 }).then(r => { allCategories.value = r.data.items }).catch(() => {})
  getLedgers({ size: 500 }).then(r => { allLedgers.value = r.data.items }).catch(() => {})
})
//   loadDaily()
// })
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
}

.day-income {
  color: #d03050;
  font-size: large;
  font-weight: bold;
}

.day-expense {
  color: #18a058;
  font-size: large;
  font-weight: bold;
}

.cal-legend {
  display: flex;
  justify-content: center;
  gap: 14px;
  margin-top: 10px;
  font-size: 11px;
  color: #888;
  align-items: center;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.income-dot { background: #d03050; }
.expense-dot { background: #18a058; }

.bar-chart {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 4px 0;
}

.bar-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.bar-label {
  width: 130px;
  font-size: 13px;
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex-shrink: 0;
}

.bar-track {
  flex: 1;
  height: 18px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #18a058, #36ad6a);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.bar-value {
  width: 50px;
  font-size: 13px;
  text-align: right;
  flex-shrink: 0;
}
</style>
