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
  password: '',
  confirmPassword: ''
})
const loading = ref(false)

const handleRegister = async () => {
  if (!form.value.email || !form.value.password || !form.value.confirmPassword) {
    ElMessage.warning('Please fill in all fields')
    return
  }

  if (form.value.password !== form.value.confirmPassword) {
    ElMessage.warning('Passwords do not match')
    return
  }

  if (form.value.password.length < 6) {
    ElMessage.warning('Password must be at least 6 characters')
    return
  }

  loading.value = true
  try {
    await api.post('/api/auth/register', {
      email: form.value.email,
      password: form.value.password
    })

    ElMessage.success('Registration successful. Please sign in.')

    const loginResponse = await api.post('/api/auth/login', {
      email: form.value.email,
      password: form.value.password
    })

    const { access_token } = loginResponse.data
    const userResponse = await api.get('/api/auth/me')
    authStore.setAuth(access_token, userResponse.data)

    router.push('/')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || 'Registration failed')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="register-container">
    <div class="register-card">
      <h1 class="title">{{ t('login.register') }}</h1>
      <p class="subtitle">{{ t('login.subtitle') }}</p>

      <el-form :model="form" class="register-form">
        <el-form-item>
          <el-input
            v-model="form.email"
            :placeholder="t('login.email')"
            type="email"
            size="large"
            prefix-icon="Message"
          />
        </el-form-item>

        <el-form-item>
          <el-input
            v-model="form.password"
            :placeholder="t('login.password')"
            type="password"
            size="large"
            prefix-icon="Lock"
          />
        </el-form-item>

        <el-form-item>
          <el-input
            v-model="form.confirmPassword"
            :placeholder="t('login.password')"
            type="password"
            size="large"
            prefix-icon="Lock"
            @keyup.enter="handleRegister"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleRegister"
            class="register-button"
          >
            {{ t('login.register') }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-link">
        Already have an account?
        <router-link to="/login">Sign in</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1e3a5f 0%, #0f1f3d 100%);
}

.register-card {
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

.register-form {
  margin-bottom: 24px;
}

.register-button {
  width: 100%;
  height: 44px;
  font-size: 16px;
}

.login-link {
  text-align: center;
  font-size: 14px;
  color: #6b7280;
}

.login-link a {
  color: #3b82f6;
  text-decoration: none;
  font-weight: 500;
}

.login-link a:hover {
  text-decoration: underline;
}
</style>
