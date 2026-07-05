import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, getMe } from '@/api/auth'
import type { Permissions } from '@/api/types'
import type { LoginResponse, MeResponse } from '@/api/auth/type'
import { TOKEN_KEY, REFRESH_TOKEN_KEY, resetAuthState } from '@/axios/axios'

interface ApiResponse<T> {
  success: boolean
  code: number
  message: string
  data: T
}

export const useAuthStore = defineStore(
  'auth',
  () => {
    const username = ref('')
    const userId = ref<number | null>(null)
    const isSuperuser = ref(false)
    const permissions = ref<Permissions | null>(null)

    const isLoggedIn = computed(() => !!localStorage.getItem(TOKEN_KEY))

    async function login(username_: string, password: string) {
      resetAuthState()
      const response = await apiLogin({ username: username_, password }) as unknown as ApiResponse<LoginResponse>
      const { access, refresh } = response.data
      localStorage.setItem(TOKEN_KEY, access)
      localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
      await fetchUser()
    }

    async function fetchUser() {
      try {
        const response = await getMe() as unknown as ApiResponse<MeResponse>
        username.value = response.data.username
        userId.value = response.data.id
        isSuperuser.value = response.data.is_superuser
        permissions.value = response.data.permissions
      } catch (e) {
        logout()
      }
    }

    function logout() {
      resetAuthState()
      username.value = ''
      userId.value = null
      isSuperuser.value = false
      permissions.value = null
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)
      localStorage.removeItem('finance-auth')
    }

    return {
      username,
      userId,
      isSuperuser,
      permissions,
      isLoggedIn,
      login,
      logout,
      fetchUser,
    }
  },
  {
    persist: {
      key: 'finance-auth',
      storage: localStorage,
      paths: ['username'],
    },
  }
)
