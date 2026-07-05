import request from '@/axios/axios'
import type { PaginatedData, User } from '@/api/types'
import type { LoginData, LoginResponse, MeResponse, ChangePassword } from './type'
import type { UserCreate, UserUpdate, Group, GroupCreate, Permission } from './type'

export const login = (data: LoginData) => {
  return request.post<LoginResponse>('/login/', data)
}

export const getMe = () => {
  return request.get<MeResponse>('/me/')
}

export const getUsers = (params?: any) => {
  return request.get<PaginatedData<User>>('/users/', { params })
}

export const getUser = (id: number) => {
  return request.get<User>(`/users/${id}/`)
}

export const createUser = (data: UserCreate) => {
  return request.post<User>('/users/', data)
}

export const updateUser = (id: number, data: UserUpdate) => {
  return request.put<User>(`/users/${id}/`, data)
}

export const deleteUser = (id: number) => {
  return request.delete(`/users/${id}/`)
}

export const setUserPassword = (id: number, password: string) => {
  return request.post(`/users/${id}/set-password/`, { password })
}

export const getGroups = (params?: any) => {
  return request.get<PaginatedData<Group>>('/groups/', { params })
}

export const getGroup = (id: number) => {
  return request.get<Group>(`/groups/${id}/`)
}

export const createGroup = (data: GroupCreate) => {
  return request.post<Group>('/groups/', data)
}

export const updateGroup = (id: number, data: GroupCreate) => {
  return request.put<Group>(`/groups/${id}/`, data)
}

export const deleteGroup = (id: number) => {
  return request.delete(`/groups/${id}/`)
}

export const getPermissions = (params?: any) => {
  return request.get<Permission[]>('/permissions/', { params })
}

export const changePassword = (data: ChangePassword) => {
  return request.post('/change-password/', data)
}
