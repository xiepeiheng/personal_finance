<template>
  <div class="account-types">
    <n-h1>账户类型管理</n-h1>
    <n-card title="类型列表">
      <template #header-extra>
        <n-button
          v-if="canAdd"
          type="primary"
          @click="handleAdd"
        >新增类型</n-button>
      </template>

      <n-data-table
        :columns="columns"
        :data="data"
        :loading="loading"
        :pagination="false"
        size="small"
      />

      <n-modal v-model:show="showModal" preset="card" :title="isEdit ? '编辑类型' : '新增类型'" style="width: 420px">
        <n-form :model="form" label-placement="top">
          <n-form-item label="名称" required>
            <n-input v-model:value="form.name" placeholder="如：工资卡" />
          </n-form-item>
          <n-form-item label="标识" required>
            <n-input v-model:value="form.slug" placeholder="如：salary_card（英文/拼音，唯一）" />
          </n-form-item>
          <n-form-item label="排序">
            <n-input-number v-model:value="form.sort_order" :min="0" style="width: 100%" />
          </n-form-item>
        </n-form>
        <template #footer>
          <n-space justify="end">
            <n-button @click="showModal = false">取消</n-button>
            <n-button type="primary" @click="handleSubmit" :loading="submitting">确定</n-button>
          </n-space>
        </template>
      </n-modal>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted } from 'vue'
import {
  NCard, NH1, NButton, NDataTable, NModal, NForm, NFormItem,
  NInput, NInputNumber, NSpace, useMessage, NPopconfirm,
} from 'naive-ui'
import { getAccountTypes, createAccountType, updateAccountType, deleteAccountType } from '@/api/finance'
import { useAuthStore } from '@/stores/auth'
import type { AccountTypeItem } from '@/api/finance/type'

const authStore = useAuthStore()
const message = useMessage()
const loading = ref(false)
const submitting = ref(false)
const showModal = ref(false)
const isEdit = ref(false)
const data = ref<AccountTypeItem[]>([])

const canAdd = computed(() =>
  authStore.isSuperuser || authStore.permissions?.actions?.accounttype?.includes('add')
)
const canChange = (): boolean =>
  !!(authStore.isSuperuser || authStore.permissions?.actions?.accounttype?.includes('change'))
const canDelete = (): boolean =>
  !!(authStore.isSuperuser || authStore.permissions?.actions?.accounttype?.includes('delete'))

const columns = [
  { title: '名称', key: 'name' },
  { title: '标识', key: 'slug' },
  { title: '排序', key: 'sort_order', width: 80 },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render: (row: AccountTypeItem) => {
      const btns: any[] = []
      if (canChange()) {
        btns.push(h(NButton, { size: 'small', onClick: () => handleEdit(row) }, { default: () => '编辑' }))
      }
      if (canDelete()) {
        btns.push(h(NPopconfirm, { onPositiveClick: () => handleDelete(row.id) }, {
          trigger: () => h(NButton, { size: 'small', type: 'error' }, { default: () => '删除' }),
          default: () => '确定删除该类型？',
        }))
      }
      if (btns.length === 0) return '-'
      return h(NSpace, { size: 'small' }, { default: () => btns })
    },
  },
]

const form = ref({
  id: null as number | null,
  name: '',
  slug: '',
  sort_order: 0,
})

const loadData = async () => {
  loading.value = true
  try {
    const res = await getAccountTypes()
    data.value = res.data
  } catch {
    console.error('Failed to load account types')
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  isEdit.value = false
  form.value = { id: null, name: '', slug: '', sort_order: 0 }
  showModal.value = true
}

const handleEdit = (row: AccountTypeItem) => {
  isEdit.value = true
  form.value = { id: row.id, name: row.name, slug: row.slug, sort_order: row.sort_order }
  showModal.value = true
}

const handleDelete = async (id: number) => {
  try {
    await deleteAccountType(id)
    message.success('删除成功')
    loadData()
  } catch {
    console.error('Failed to delete account type')
  }
}

const handleSubmit = async () => {
  if (!form.value.name || !form.value.slug) {
    message.warning('名称和标识必填')
    return
  }
  submitting.value = true
  try {
    const payload = {
      name: form.value.name,
      slug: form.value.slug,
      sort_order: form.value.sort_order,
    }
    if (isEdit.value && form.value.id) {
      await updateAccountType(form.value.id, payload)
      message.success('更新成功')
    } else {
      await createAccountType(payload)
      message.success('创建成功')
    }
    showModal.value = false
    loadData()
  } catch {
    console.error('Failed to submit')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>
