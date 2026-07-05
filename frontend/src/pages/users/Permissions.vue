<template>
  <div class="permissions">
    <n-h1>权限管理</n-h1>
    <n-card title="权限列表">
      <n-data-table :columns="columns" :data="data" :loading="loading" :pagination="false" />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  NCard,
  NH1,
  NDataTable,
} from 'naive-ui'
import { getPermissions } from '@/api/auth'
import type { Permission } from '@/api/auth/type'

const loading = ref(false)
const data = ref<Permission[]>([])

const columns = [
  { title: 'ID', key: 'id', width: 80 },
  { title: '名称', key: 'name' },
  { title: 'codename', key: 'codename' },
  { title: 'content_type', key: 'content_type', width: 120 },
]

const loadData = async () => {
  loading.value = true
  try {
    const response = await getPermissions()
    data.value = response.data
  } catch (error) {
    console.error('Failed to fetch permissions:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>
