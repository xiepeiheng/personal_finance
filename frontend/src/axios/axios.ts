import axios, {type AxiosInstance, AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { createDiscreteApi } from 'naive-ui'

const { message } = createDiscreteApi(['message'])

const TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'

export { TOKEN_KEY, REFRESH_TOKEN_KEY }

const http: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

http.interceptors.request.use(
  (config: InternalAxiosRequestConfig & { data?: any }) => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    if (config.data && config.method === 'get') {
      config.params = config.data
      delete config.data
    }
    if (config.data instanceof FormData) {
      delete config.headers?.['Content-Type']
    }
    return config
  },
  (error: AxiosError) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

let refreshPromise: Promise<boolean> | null = null
let isRedirectingToLogin = false

export function resetAuthState() {
  refreshPromise = null
  isRedirectingToLogin = false
}

http.interceptors.response.use(
  (response) => {
    if (response.status === 204) {
      return {
        success: true,
        http_status: 204,
        code: 204,
        message: '操作成功',
        data: null,
      }
    }
    return response.data
  },
  async (error: AxiosError) => {
    if (error.response) {
      const status = error.response.status
      const backendData = error.response.data as { message?: string }

      if (status === 401) {
        const refreshed = await refreshToken()
        if (refreshed) {
          const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }
          if (originalRequest && !originalRequest._retry) {
            originalRequest._retry = true
            const token = localStorage.getItem(TOKEN_KEY)
            originalRequest.headers!.Authorization = `Bearer ${token}`
            return http(originalRequest)
          }
        }
        if (!isRedirectingToLogin) {
          isRedirectingToLogin = true
          message.error('登录已过期，请重新登录')
          localStorage.removeItem(TOKEN_KEY)
          localStorage.removeItem(REFRESH_TOKEN_KEY)
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }

      const msgMap: Record<number, string> = {
        403: backendData?.message || '没有操作权限',
        404: '请求的资源不存在',
        500: '服务器内部错误',
      }
      if (msgMap[status]) {
        message.error(msgMap[status])
      } else {
        message.error(backendData?.message || '请求失败')
      }
    } else if (error.request) {
      message.error('网络连接失败，请检查网络')
    } else {
      message.error('请求配置错误')
    }
    return Promise.reject(error)
  }
)

async function refreshToken(): Promise<boolean> {
  if (refreshPromise) return refreshPromise

  const refreshTokenStr = localStorage.getItem(REFRESH_TOKEN_KEY)
  if (!refreshTokenStr) return false

  refreshPromise = axios
    .post(`${http.defaults.baseURL}/token/refresh/`, {
      refresh: refreshTokenStr,
    })
    .then((response) => {
      const { access, refresh } = response.data.data
      localStorage.setItem(TOKEN_KEY, access)
      if (refresh) localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
      return true
    })
    .catch(() => {
      return false
    })
    .finally(() => {
      refreshPromise = null
    })

  return refreshPromise
}

export default http