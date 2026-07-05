<template>
  <div class="settings">
    <n-h1>设置</n-h1>

    <n-card title="个人信息">
      <n-descriptions label-placement="left" :column="1">
        <n-descriptions-item label="用户名">{{ authStore.username }}</n-descriptions-item>
        <n-descriptions-item label="用户ID">{{ authStore.userId }}</n-descriptions-item>
        <n-descriptions-item label="管理员">
          {{ authStore.isSuperuser ? '是' : '否' }}
        </n-descriptions-item>
      </n-descriptions>
    </n-card>

    <n-card title="修改密码" style="margin-top: 16px;">
      <n-form label-placement="left" label-width="100" style="max-width: 400px;">
        <n-form-item label="当前密码">
          <n-input
            v-model:value="pwForm.old_password"
            type="password"
            placeholder="输入当前密码"
            show-password-on="click"
          />
        </n-form-item>
        <n-form-item label="新密码">
          <n-input
            v-model:value="pwForm.new_password"
            type="password"
            placeholder="至少 8 位"
            show-password-on="click"
          />
        </n-form-item>
        <n-form-item>
          <n-button type="primary" @click="handleChangePassword" :loading="pwLoading">更新密码</n-button>
        </n-form-item>
      </n-form>
    </n-card>

    <n-card title="数据维护" style="margin-top: 16px;">
      <n-space align="center">
        <n-button @click="handleRecalculate" :loading="recalculating" type="warning">
          校准分类与账本金额
        </n-button>
        <span style="font-size: 13px; color: #888;">
          重新统计所有分类的实际金额和账本余额，用于修复信号异常导致的数据偏差
        </span>
      </n-space>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { NH1, NCard, NDescriptions, NDescriptionsItem, NButton, NSpace, NForm, NFormItem, NInput, useMessage } from 'naive-ui'
import { useAuthStore } from '@/stores/auth'
import { changePassword } from '@/api/auth'
import { recalculateAll } from '@/api/finance'

const authStore = useAuthStore()
const message = useMessage()
const recalculating = ref(false)
const pwLoading = ref(false)

const pwForm = reactive({
  old_password: '',
  new_password: '',
})

const handleRecalculate = async () => {
  recalculating.value = true
  try {
    const res = await recalculateAll()
    message.success(`校准完成：${res.data.categories} 个分类、${res.data.ledgers} 个账本已更新`)
  } catch {
    message.error('校准失败')
  } finally {
    recalculating.value = false
  }
}

const handleChangePassword = async () => {
  if (!pwForm.old_password) {
    message.warning('请输入当前密码')
    return
  }
  if (!pwForm.new_password || pwForm.new_password.length < 8) {
    message.warning('新密码长度至少 8 位')
    return
  }
  pwLoading.value = true
  try {
    await changePassword({ old_password: pwForm.old_password, new_password: pwForm.new_password })
    message.success('密码已更新')
    pwForm.old_password = ''
    pwForm.new_password = ''
  } catch {
    message.error('密码更新失败')
  } finally {
    pwLoading.value = false
  }
}
</script>
