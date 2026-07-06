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

export type AccountType = 'bank' | 'securities' | 'cash' | 'credit' | 'alipay'

export interface AccountTypeItem {
  id: number
  name: string
  slug: string
  sort_order: number
}

export interface Account {
  id: number
  account_type: number
  account_type_name: string
  account_type_slug: string
  name: string
  initial_balance: string
  current_balance: string
  remarks: string
  created_at: string
  updated_at: string
}

export interface Transfer {
  id: number
  from_account: number
  from_account_name: string
  to_account: number
  to_account_name: string
  amount: string
  trade_time: string
  note: string
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
  account: number | null
  account_name: string | null
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
  account?: number | null
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

export interface AccountCreate {
  account_type: number
  name: string
  initial_balance?: string
  remarks?: string
}

export interface AccountTypeCreate {
  name: string
  slug: string
  sort_order: number
}

export interface TransferCreate {
  from_account: number
  to_account: number
  amount: string
  trade_time: string
  note?: string
}
