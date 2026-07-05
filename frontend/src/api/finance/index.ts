import request from '@/axios/axios'
import type { PaginatedData } from '@/api/types'
import type {
  Ledger,
  LedgerCreate,
  Category,
  CategoryCreate,
  Transaction,
  TransactionCreate,
  Summary,
  DailySummary,
  BatchCreateItem,
  BatchResult,
} from './type'

export const getLedgers = (params?: any) => {
  return request.get<PaginatedData<Ledger>>('/finance/ledgers/', { params })
}

export const getLedger = (id: number) => {
  return request.get<Ledger>(`/finance/ledgers/${id}/`)
}

export const createLedger = (data: LedgerCreate) => {
  return request.post<Ledger>('/finance/ledgers/', data)
}

export const updateLedger = (id: number, data: LedgerCreate) => {
  return request.put<Ledger>(`/finance/ledgers/${id}/`, data)
}

export const deleteLedger = (id: number) => {
  return request.delete(`/finance/ledgers/${id}/`)
}

export const getCategories = (params?: any) => {
  return request.get<PaginatedData<Category>>('/finance/categories/', { params })
}

export const getCategory = (id: number) => {
  return request.get<Category>(`/finance/categories/${id}/`)
}

export const createCategory = (data: CategoryCreate) => {
  return request.post<Category>('/finance/categories/', data)
}

export const updateCategory = (id: number, data: CategoryCreate) => {
  return request.put<Category>(`/finance/categories/${id}/`, data)
}

export const deleteCategory = (id: number) => {
  return request.delete(`/finance/categories/${id}/`)
}

export const getTransactions = (params?: any) => {
  return request.get<PaginatedData<Transaction>>('/finance/transactions/', { params })
}

export const getTransaction = (id: number) => {
  return request.get<Transaction>(`/finance/transactions/${id}/`)
}

export const createTransaction = (data: TransactionCreate) => {
  return request.post<Transaction>('/finance/transactions/', data)
}

export const updateTransaction = (id: number, data: TransactionCreate) => {
  return request.put<Transaction>(`/finance/transactions/${id}/`, data)
}

export const deleteTransaction = (id: number) => {
  return request.delete(`/finance/transactions/${id}/`)
}

export const getSummary = (params?: { date_from?: string; date_to?: string }) => {
  return request.get<Summary>('/finance/transactions/summary/', { params })
}

export const getDailySummary = (params?: { date_from?: string; date_to?: string }) => {
  return request.get<DailySummary[]>('/finance/transactions/daily-summary/', { params })
}

export const batchCreateTransactions = (data: BatchCreateItem[]) => {
  return request.post<BatchResult>('/finance/transactions/batch/', { transactions: data })
}

export const recalculateAll = () => {
  return request.post<{ categories: number; ledgers: number }>('/finance/ledgers/recalculate/')
}
