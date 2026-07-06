import request from '@/axios/axios'
import type { AccountTypeItem, AccountTypeCreate } from './type'

export const getAccountTypes = () => {
  return request.get<AccountTypeItem[]>('/finance/account-types/')
}

export const getAccountType = (id: number) => {
  return request.get<AccountTypeItem>(`/finance/account-types/${id}/`)
}

export const createAccountType = (data: AccountTypeCreate) => {
  return request.post<AccountTypeItem>('/finance/account-types/', data)
}

export const updateAccountType = (id: number, data: AccountTypeCreate) => {
  return request.put<AccountTypeItem>(`/finance/account-types/${id}/`, data)
}

export const deleteAccountType = (id: number) => {
  return request.delete(`/finance/account-types/${id}/`)
}
