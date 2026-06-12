<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from '@/i18n'
import api from '@/api'

const router = useRouter()
const authStore = useAuthStore()
const { currentLang, setLang, t } = useI18n()

const form = ref({
  email: '',
  password: ''
})
const loading = ref(false)

const handleLogin = async () => {
  if (!form.value.email || !form.value.password) {
    ElMessage.warning(t('login.fillAll') || '请填写所有字段')
    return
  }

  loading.value = true
  try {
    // 1. 登录获取 token
    const response = await api.post('/api/auth/login', form.value)
    const { access_token } = response.data

    // 2. 先存 token 到 localStorage，确保后续请求能带上
    localStorage.setItem('token', access_token)

    // 3. 获取用户信息（此时 localStorage 已有 token，拦截器会自动带上）
    const userResponse = await api.get('/api/auth/me')

    // 4. 设置 auth store
    authStore.setAuth(access_token, userResponse.data)

    ElMessage.success(t('common.success') || '登录成功')
    router.push('/')
  } catch (error: any) {
    // 清理可能残留的 token
    localStorage.removeItem('token')
    const detail = error.response?.data?.detail
    if (detail) {
      ElMessage.error(detail)
    } else {
      ElMessage.error(t('common.failed') || '登录失败')
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-container">
    <div class="login-card">
      <h1 class="title">{{ t('login.title') }}</h1>
      <p class="subtitle">{{ t('login.subtitle') }}</p>

      <el-form :model="form" class="login-form">
        <el-form-item>
          <el-input
            v-model="form.email"
            :placeholder="t('login.email')"
            type="email"
            size="large"
            prefix-icon="User"
          />
        </el-form-item>

        <el-form-item>
          <el-input
            v-model="form.password"
            :placeholder="t('login.password')"
            type="password"
            size="large"
            prefix-icon="Lock"
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleLogin"
            class="login-button"
          >
            {{ t('login.submit') }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="register-link">
        {{ t('login.noAccount') }}
        <router-link to="/register">{{ t('login.register') }}</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1e3a5f 0%, #0f1f3d 100%);
}

.login-card {
  width: 400px;
  padding: 40px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.title {
  font-size: 28px;
  font-weight: 700;
  color: #1e3a5f;
  text-align: center;
  margin: 0 0 8px;
}

.subtitle {
  font-size: 14px;
  color: #6b7280;
  text-align: center;
  margin: 0 0 32px;
}

.login-form {
  margin-bottom: 24px;
}

.login-button {
  width: 100%;
  height: 44px;
  font-size: 16px;
}

.register-link {
  text-align: center;
  font-size: 14px;
  color: #6b7280;
}

.register-link a {
  color: #3b82f6;
  text-decoration: none;
  font-weight: 500;
}

.register-link a:hover {
  text-decoration: underline;
}

@media (max-width: 768px) {
  .login-card {
    width: 90%;
    padding: 24px;
    margin: 12px;
  }
  .title {
    font-size: 22px;
  }
}
</style>
