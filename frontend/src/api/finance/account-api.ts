import request from '@/axios/axios'
import type { PaginatedData } from '@/api/types'
import type { Account, AccountCreate } from './type'

export const getAccounts = (params?: { account_type?: string; size?: number; page?: number }) => {
  return request.get<PaginatedData<Account>>('/finance/accounts/', { params })
}

export const getAccount = (id: number) => {
  return request.get<Account>(`/finance/accounts/${id}/`)
}

export const createAccount = (data: AccountCreate) => {
  return request.post<Account>('/finance/accounts/', data)
}

export const updateAccount = (id: number, data: AccountCreate) => {
  return request.put<Account>(`/finance/accounts/${id}/`, data)
}

export const deleteAccount = (id: number) => {
  return request.delete(`/finance/accounts/${id}/`)
}
