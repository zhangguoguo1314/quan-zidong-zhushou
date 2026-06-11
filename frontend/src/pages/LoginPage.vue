<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import api from '@/api'

const router = useRouter()
const authStore = useAuthStore()

const form = ref({
  email: '',
  password: ''
})
const loading = ref(false)

const handleLogin = async () => {
  if (!form.value.email || !form.value.password) {
    ElMessage.warning('Please fill in all fields')
    return
  }

  loading.value = true
  try {
    const response = await api.post('/api/auth/login', form.value)
    const { access_token } = response.data

    const userResponse = await api.get('/api/auth/me')
    authStore.setAuth(access_token, userResponse.data)

    ElMessage.success('Login successful')
    router.push('/')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || 'Login failed')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-container">
    <div class="login-card">
      <h1 class="title">Account Auto-Sign</h1>
      <p class="subtitle">Sign in to your account</p>

      <el-form :model="form" class="login-form">
        <el-form-item>
          <el-input
            v-model="form.email"
            placeholder="Email"
            type="email"
            size="large"
            prefix-icon="User"
          />
        </el-form-item>

        <el-form-item>
          <el-input
            v-model="form.password"
            placeholder="Password"
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
            Sign In
          </el-button>
        </el-form-item>
      </el-form>

      <div class="register-link">
        Don't have an account?
        <router-link to="/register">Register</router-link>
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
</style>
