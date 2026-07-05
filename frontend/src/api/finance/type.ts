export type LedgerType = 'time' | 'category'

export interface Ledger {
  id: number
  ledger_type: LedgerType
  ledger_type_display: string
  name: string
  balance: string
  is_complete: boolean
  remarks: string
  created_at: string
  updated_at: string
}

export interface Category {
  id: number
  name: string
  time_ledger: number | null
  time_ledger_name: string | null
  category_ledger: number | null
  category_ledger_name: string | null
  budget: string
  actual_amount: string
  is_complete: boolean
  star: number
  remarks: string
  created_at: string
  updated_at: string
}

export interface Transaction {
  id: number
  category: number
  trade_time: string
  partner: string
  amount: string
  star: number
  channel: string
  detail: string
  ticket_file: string | null
  remarks: string
  created_at: string
  updated_at: string
}

export interface LedgerCreate {
  ledger_type: LedgerType
  name: string
  is_complete?: boolean
  remarks?: string
}

export interface CategoryCreate {
  time_ledger?: number | null
  category_ledger?: number | null
  name: string
  budget: string
  is_complete?: boolean
  star?: number
  remarks?: string
}

export interface CategorySummary {
  id: number
  name: string
  total: string
  count: number
}

export interface DailySummary {
  date: string
  income: string
  expense: string
}

export interface Summary {
  total_income: string
  total_expense: string
  net: string
  categories: CategorySummary[]
  recent_transactions: Transaction[]
}

export interface BatchCreateItem {
  category: number
  trade_time: string
  partner: string
  amount: string
  star?: number
  channel?: string
  detail?: string
  remarks?: string
}

export interface BatchResult {
  total: number
  succeeded: number
  failed: BatchError[]
}

export interface BatchError {
  row: number
  success: false
  errors: Record<string, string[]>
}
  category: number
  trade_time: string
  partner: string
  amount: string
  star?: number
  channel?: string
  detail?: string
  remarks?: string
}
