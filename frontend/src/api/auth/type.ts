import type { ApiResponse, User, Permissions, PaginatedData } from '@/api/types'

export interface LoginData {
  username: string
  password: string
}

export interface LoginResponse {
  access: string
  refresh: string
  permissions: Permissions
}

export interface MeResponse {
  id: number
  username: string
  email: string
  is_superuser: boolean
  date_joined: string
  permissions: Permissions
}

export interface UserCreate {
  username: string
  email: string
  password: string
  groups?: number[]
}

export interface UserUpdate {
  username: string
  email: string
  groups?: number[]
}

export interface ChangePassword {
  old_password: string
  new_password: string
}

export interface Group {
  id: number
  name: string
  permissions?: number[]
}

export interface GroupCreate {
  name: string
  permissions?: number[]
}

export interface Permission {
  id: number
  name: string
  codename: string
  content_type: number
}
