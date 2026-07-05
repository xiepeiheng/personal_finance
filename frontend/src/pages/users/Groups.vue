<template>
  <div class="groups">
    <n-h1>用户组管理</n-h1>
    <n-card title="用户组列表">
      <template #header-extra>
        <n-button v-if="authStore.isSuperuser || authStore.permissions?.actions?.group?.includes('add')" type="primary" @click="handleAdd">新增用户组</n-button>
      </template>
      <n-data-table :columns="columns" :data="data" :loading="loading" :pagination="false" />
    </n-card>

    <n-modal v-model:show="showModal" preset="card" :title="isEdit ? '编辑用户组' : '新增用户组'" style="width: 600px">
      <n-form :model="form" label-placement="top">
        <n-form-item label="名称" required>
          <n-input v-model:value="form.name" placeholder="请输入用户组名称" />
        </n-form-item>
        <n-form-item label="权限">
          <n-select
            v-model:value="form.permissions"
            :options="permissionOptions"
            multiple
            placeholder="选择权限（可选）"
            clearable
            filterable
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" @click="handleSubmit" :loading="submitting">确定</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted } from 'vue'
import {
  NCard,
  NH1,
  NButton,
  NDataTable,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NSpace,
  useMessage,
  NPopconfirm,
} from 'naive-ui'
import { getGroups, createGroup, updateGroup, deleteGroup, getPermissions } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import type { Group, Permission } from '@/api/auth/type'

const authStore = useAuthStore()
const message = useMessage()
const loading = ref(false)
const submitting = ref(false)
const showModal = ref(false)
const isEdit = ref(false)
const data = ref<Group[]>([])
const allPermissions = ref<Permission[]>([])

const permissionOptions = computed(() =>
  allPermissions.value.map((p) => ({
    label: `${p.name} (${p.codename})`,
    value: p.id,
  }))
)

const form = ref({
  id: null as number | null,
  name: '',
  permissions: [] as number[],
})

const columns = [
  { title: 'ID', key: 'id', width: 80 },
  { title: '名称', key: 'name' },
  {
    title: '权限数',
    key: 'permissions',
    render: (row: Group) => `${row.permissions?.length ?? 0} 个权限`,
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render: (row: Group) => {
      const btns: any[] = []
      if (authStore.isSuperuser || authStore.permissions?.actions?.group?.includes('change')) {
        btns.push(h(NButton, { size: 'small', onClick: () => handleEdit(row) }, { default: () => '编辑' }))
      }
      if (authStore.isSuperuser || authStore.permissions?.actions?.group?.includes('delete')) {
        btns.push(h(NPopconfirm, { onPositiveClick: () => handleDelete(row.id) }, {
          trigger: () => h(NButton, { size: 'small', type: 'error' }, { default: () => '删除' }),
          default: () => '确定删除？',
        }))
      }
      if (btns.length === 0) return '-'
      return h(NSpace, { size: 'small' }, { default: () => btns })
    },
  },
]

const loadPermissions = async () => {
  try {
    const res = await getPermissions()
    allPermissions.value = res.data
  } catch {
    console.error('Failed to load permissions')
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const response = await getGroups()
    data.value = response.data.items
  } catch (error) {
    console.error('Failed to fetch groups:', error)
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  isEdit.value = false
  form.value = { id: null, name: '', permissions: [] }
  showModal.value = true
}

const handleEdit = (row: Group) => {
  isEdit.value = true
  form.value = {
    id: row.id,
    name: row.name,
    permissions: row.permissions ?? [],
  }
  showModal.value = true
}

const handleDelete = async (id: number) => {
  try {
    await deleteGroup(id)
    message.success('删除成功')
    loadData()
  } catch (error) {
    console.error('Failed to delete group:', error)
  }
}

const handleSubmit = async () => {
  if (!form.value.name) {
    message.warning('请输入用户组名称')
    return
  }

  submitting.value = true
  try {
    const payload = {
      name: form.value.name,
      permissions: form.value.permissions,
    }
    if (isEdit.value && form.value.id) {
      await updateGroup(form.value.id, payload)
      message.success('更新成功')
    } else {
      await createGroup(payload)
      message.success('创建成功')
    }
    showModal.value = false
    loadData()
  } catch (error) {
    console.error('Failed to submit:', error)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadData()
  loadPermissions()
})
</script>
