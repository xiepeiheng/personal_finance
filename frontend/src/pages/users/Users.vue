<template>
  <div class="users">
    <n-h1>用户管理</n-h1>
    <n-card title="用户列表">
      <template #header-extra>
        <n-button v-if="authStore.isSuperuser || authStore.permissions?.actions?.user?.includes('add')" type="primary" @click="handleAdd">新增用户</n-button>
      </template>
      <n-data-table :columns="columns" :data="data" :loading="loading" :pagination="false" />
    </n-card>

    <n-modal v-model:show="showModal" preset="card" :title="isEdit ? '编辑用户' : '新增用户'" style="width: 480px">
      <n-form :model="form" label-placement="top">
        <n-form-item label="用户名" required>
          <n-input v-model:value="form.username" placeholder="请输入用户名" />
        </n-form-item>
        <n-form-item label="邮箱">
          <n-input v-model:value="form.email" placeholder="请输入邮箱" />
        </n-form-item>
        <n-form-item v-if="!isEdit" label="密码" required>
          <n-input v-model:value="form.password" type="password" placeholder="请输入密码" show-password-on="click" />
        </n-form-item>
        <n-form-item label="用户组">
          <n-select
            v-model:value="form.groups"
            :options="groupOptions"
            multiple
            placeholder="选择用户组（可选）"
            clearable
          />
        </n-form-item>
        <n-form-item v-if="isEdit" label="重置密码">
          <n-input
            v-model:value="newPassword"
            type="password"
            placeholder="留空则不修改密码"
            show-password-on="click"
          />
          <template #extra>
            如用户忘记密码，在此输入新密码后点击"更新密码"按钮
          </template>
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showModal = false">取消</n-button>
          <n-button v-if="isEdit && newPassword" type="warning" @click="handleResetPassword" :loading="resetting">更新密码</n-button>
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
import { getUsers, createUser, updateUser, deleteUser, setUserPassword, getGroups } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import type { User } from '@/api/types'
import type { Group } from '@/api/auth/type'

const authStore = useAuthStore()
const message = useMessage()
const loading = ref(false)
const submitting = ref(false)
const resetting = ref(false)
const showModal = ref(false)
const isEdit = ref(false)
const data = ref<User[]>([])
const allGroups = ref<Group[]>([])

const groupOptions = computed(() =>
  allGroups.value.map((g) => ({ label: g.name, value: g.id }))
)

const form = ref({
  id: null as number | null,
  username: '',
  email: '',
  password: '',
  groups: [] as number[],
})

const newPassword = ref('')

const columns = [
  { title: 'ID', key: 'id', width: 80 },
  { title: '用户名', key: 'username' },
  { title: '邮箱', key: 'email' },
  {
    title: '超级管理员',
    key: 'is_superuser',
    width: 100,
    render: (row: User) => row.is_superuser ? '是' : '否',
  },
  {
    title: '用户组',
    key: 'groups',
    render: (row: User) => row.groups?.map(([, name]) => name).join(', ') || '-',
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render: (row: User) => {
      const btns: any[] = []
      if (authStore.isSuperuser || authStore.permissions?.actions?.user?.includes('change')) {
        btns.push(h(NButton, { size: 'small', onClick: () => handleEdit(row) }, { default: () => '编辑' }))
      }
      if (authStore.isSuperuser || authStore.permissions?.actions?.user?.includes('delete')) {
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

const loadGroups = async () => {
  try {
    const res = await getGroups()
    allGroups.value = res.data.items
  } catch {
    console.error('Failed to load groups')
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const response = await getUsers()
    data.value = response.data.items
  } catch (error) {
    console.error('Failed to fetch users:', error)
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  isEdit.value = false
  newPassword.value = ''
  form.value = { id: null, username: '', email: '', password: '', groups: [] }
  showModal.value = true
}

const handleEdit = (row: User) => {
  isEdit.value = true
  newPassword.value = ''
  form.value = {
    id: row.id,
    username: row.username,
    email: row.email,
    password: '',
    groups: row.groups?.map(([id]) => id) || [],
  }
  showModal.value = true
}

const handleDelete = async (id: number) => {
  try {
    await deleteUser(id)
    message.success('删除成功')
    loadData()
  } catch (error) {
    console.error('Failed to delete user:', error)
  }
}

const handleResetPassword = async () => {
  if (!newPassword.value || newPassword.value.length < 8) {
    message.warning('密码长度至少8位')
    return
  }
  if (!form.value.id) return
  resetting.value = true
  try {
    await setUserPassword(form.value.id, newPassword.value)
    message.success('密码已更新')
    newPassword.value = ''
  } catch (error) {
    console.error('Failed to reset password:', error)
  } finally {
    resetting.value = false
  }
}

const handleSubmit = async () => {
  if (!form.value.username) {
    message.warning('请输入用户名')
    return
  }
  if (!isEdit.value && !form.value.password) {
    message.warning('请输入密码')
    return
  }

  submitting.value = true
  try {
    if (isEdit.value && form.value.id) {
      await updateUser(form.value.id, {
        username: form.value.username,
        email: form.value.email,
        groups: form.value.groups,
      })
      message.success('更新成功')
    } else {
      await createUser({
        username: form.value.username,
        email: form.value.email,
        password: form.value.password,
        groups: form.value.groups,
      })
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
  loadGroups()
})
</script>
