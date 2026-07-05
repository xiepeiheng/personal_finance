<template>
  <div class="login-container">
    <n-card class="login-card" title="登录">
      <n-form ref="formRef" :model="formValue" :rules="rules">
        <n-form-item path="username" label="用户名">
          <n-input v-model:value="formValue.username" placeholder="请输入用户名" />
        </n-form-item>
        <n-form-item path="password" label="密码">
          <n-input
            v-model:value="formValue.password"
            type="password"
            placeholder="请输入密码"
            show-password-on="click"
            @keydown.enter="handleLogin"
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-button type="primary" block :loading="loading" @click="handleLogin">
          登录
        </n-button>
      </template>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NForm, NFormItem, NInput, NButton, useMessage } from 'naive-ui'
import type { FormInst } from 'naive-ui'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const message = useMessage()

const formRef = ref<FormInst | null>(null)
const loading = ref(false)
const formValue = ref({
  username: '',
  password: '',
})

const rules = {
  username: { required: true, message: '请输入用户名', trigger: 'blur' },
  password: { required: true, message: '请输入密码', trigger: 'blur' },
}

const handleLogin = async () => {
  if (!formRef.value) return

  formRef.value.validate(async (errors) => {
    if (errors) return

    loading.value = true
    try {
      console.log('[Login] Starting login...')
      await authStore.login(formValue.value.username, formValue.value.password)
      console.log('[Login] Login successful')
      router.push({ name: 'dashboard' })
    } catch (error: any) {
      console.error('[Login] Login failed:', error)
      message.error(error?.message || '登录失败')
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 400px;
}
</style>
