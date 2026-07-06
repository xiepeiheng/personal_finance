import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { TOKEN_KEY, REFRESH_TOKEN_KEY } from '@/axios/axios'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/pages/auth/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    component: () => import('@/pages/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'dashboard',
        component: () => import('@/pages/Dashboard.vue'),
      },
      {
        path: 'ledgers',
        name: 'ledgers',
        component: () => import('@/pages/finance/Ledgers.vue'),
      },
      {
        path: 'categories',
        name: 'categories',
        component: () => import('@/pages/finance/Categories.vue'),
      },
      {
        path: 'transactions',
        name: 'transactions',
        component: () => import('@/pages/finance/Transactions.vue'),
      },
      {
        path: 'accounts',
        name: 'accounts',
        component: () => import('@/pages/finance/Accounts.vue'),
      },
      {
        path: 'account-types',
        name: 'account-types',
        component: () => import('@/pages/finance/AccountTypes.vue'),
      },
      {
        path: 'transfers',
        name: 'transfers',
        component: () => import('@/pages/finance/Transfers.vue'),
      },
      {
        path: 'settings',
        name: 'settings',
        component: () => import('@/pages/Settings.vue'),
      },
      {
        path: 'users',
        name: 'users',
        component: () => import('@/pages/users/Users.vue'),
      },
      {
        path: 'groups',
        name: 'groups',
        component: () => import('@/pages/users/Groups.vue'),
      },
      {
        path: 'permissions',
        name: 'permissions',
        component: () => import('@/pages/users/Permissions.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

const publicPages = ['login']

router.beforeEach(async (to) => {
  const authStore = useAuthStore()

  if (publicPages.includes(to.name as string)) return true

  const hasToken = !!localStorage.getItem(TOKEN_KEY)
  if (!hasToken) return { name: 'login' }

  if (!authStore.userId) {
    try {
      await authStore.fetchUser()
    } catch {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)
      return { name: 'login' }
    }
  }

  if (to.name === 'login') return { name: 'dashboard' }
})

export default router
