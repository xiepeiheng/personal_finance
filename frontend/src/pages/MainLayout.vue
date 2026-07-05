<template>
  <n-layout has-sider class="app-layout">
    <n-layout-sider
      bordered
      collapse-mode="width"
      :collapsed-width="64"
      :width="200"
      :collapsed="collapsed"
      show-trigger
      @collapse="collapsed = true"
      @expand="collapsed = false"
    >
      <div class="logo" :class="{ collapsed }">
        <span v-if="!collapsed">财务记账</span>
        <span v-else>记账</span>
      </div>
      <n-menu
        :value="activeKey"
        :collapsed="collapsed"
        :collapsed-width="64"
        :collapsed-icon-size="22"
        :options="menuOptions"
        @update:value="handleMenuSelect"
      />
    </n-layout-sider>

    <n-layout>
      <n-layout-header bordered class="header">
        <div class="header-content">
          <span class="username">{{ authStore.username }}</span>
          <n-button quaternary @click="handleLogout">退出</n-button>
        </div>
      </n-layout-header>

      <n-layout-content class="content">
        <router-view />
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<script setup lang="ts">
import { ref, computed, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NIcon } from 'naive-ui'
import {
  HomeOutline,
  WalletOutline,
  GridOutline,
  ReceiptOutline,
  SettingsOutline,
  PersonOutline,
  PeopleOutline,
  KeyOutline,
} from '@vicons/ionicons5'
import { useAuthStore } from '@/stores/auth.ts'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const collapsed = ref(false)
const activeKey = computed(() => route.name as string)

const renderIcon = (icon: any) => {
  return () => h(NIcon, null, { default: () => h(icon) })
}

const hasFinanceAccess = computed(() => {
  const models = authStore.permissions?.modules?.finance
  return !!models && models.length > 0
})

const hasAuthAccess = computed(() => {
  const models = authStore.permissions?.modules?.auth
  return !!models && models.length > 0
})

const menuOptions = computed(() => {
  const items: any[] = [
    { label: '首页', key: 'dashboard', icon: renderIcon(HomeOutline) },
  ]
  if (hasFinanceAccess.value) {
    items.push(
      { label: '账本', key: 'ledgers', icon: renderIcon(WalletOutline) },
      { label: '分类', key: 'categories', icon: renderIcon(GridOutline) },
      { label: '交易', key: 'transactions', icon: renderIcon(ReceiptOutline) },
    )
  }
  if (hasAuthAccess.value) {
    items.push(
      { label: '用户', key: 'users', icon: renderIcon(PersonOutline) },
      { label: '用户组', key: 'groups', icon: renderIcon(PeopleOutline) },
      { label: '权限', key: 'permissions', icon: renderIcon(KeyOutline) },
    )
  }
  items.push({ label: '设置', key: 'settings', icon: renderIcon(SettingsOutline) })
  return items
})

const handleMenuSelect = (key: string) => {
  router.push({ name: key })
}

const handleLogout = () => {
  authStore.logout()
  router.push({ name: 'login' })
}
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid var(--n-border-color);
}

.logo.collapsed {
  font-size: 14px;
}

.header {
  height: 60px;
  padding: 0 24px;
  display: flex;
  align-items: center;
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 16px;
}

.username {
  color: var(--n-text-color);
}

.content {
  padding: 24px;
}
</style>
