export interface ApiResponse<T = any> {
  success: boolean
  code: number
  message: string
  data: T
}

export interface PaginatedData<T> {
  total: number
  items: T[]
  page: number
  size: number
}

export interface User {
  id: number
  username: string
  email: string
  is_superuser: boolean
  date_joined: string
  groups: [number, string][]
}

export interface Permissions {
  modules: {
    [key: string]: string[]
  }
  actions: {
    [key: string]: string[]
  }
}
