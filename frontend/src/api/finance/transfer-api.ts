import request from '@/axios/axios'
import type { PaginatedData } from '@/api/types'
import type { Transfer, TransferCreate } from './type'

export const getTransfers = (params?: Record<string, any>) => {
  return request.get<PaginatedData<Transfer>>('/finance/transfers/', { params })
}

export const getTransfer = (id: number) => {
  return request.get<Transfer>(`/finance/transfers/${id}/`)
}

export const createTransfer = (data: TransferCreate) => {
  return request.post<Transfer>('/finance/transfers/', data)
}

export const updateTransfer = (id: number, data: TransferCreate) => {
  return request.put<Transfer>(`/finance/transfers/${id}/`, data)
}

export const deleteTransfer = (id: number) => {
  return request.delete(`/finance/transfers/${id}/`)
}
