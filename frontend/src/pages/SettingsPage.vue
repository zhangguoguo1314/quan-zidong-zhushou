<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import api from '@/api'

const authStore = useAuthStore()

const emailSettings = ref({
  smtp_host: '',
  smtp_port: 587,
  smtp_user: '',
  smtp_password: '',
  email_from: ''
})

const loading = ref(false)

const saveEmailSettings = async () => {
  loading.value = true
  try {
    await api.put('/api/settings/email', emailSettings.value)
    ElMessage.success('Email settings saved successfully')
  } catch (error: any) {
    ElMessage.error('Failed to save email settings')
  } finally {
    loading.value = false
  }
}

const testEmailConnection = async () => {
  if (!emailSettings.value.smtp_host || !emailSettings.value.smtp_user) {
    ElMessage.warning('Please fill in all required fields')
    return
  }

  loading.value = true
  try {
    await api.post('/api/settings/test-email', emailSettings.value)
    ElMessage.success('Test email sent successfully')
  } catch (error: any) {
    ElMessage.error('Failed to send test email')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="dashboard">
    <aside class="sidebar">
      <div class="logo"><h2>Auto-Sign</h2></div>
      <nav class="nav-menu">
        <router-link to="/" class="nav-item">Dashboard</router-link>
        <router-link to="/sites" class="nav-item">Sites</router-link>
        <router-link to="/accounts" class="nav-item">Accounts</router-link>
        <router-link to="/tasks" class="nav-item">Tasks</router-link>
        <router-link to="/logs" class="nav-item">Logs</router-link>
        <router-link to="/settings" class="nav-item active">Settings</router-link>
      </nav>
    </aside>

    <main class="main-content">
      <header class="page-header">
        <h1>Settings</h1>
      </header>

      <div class="settings-section">
        <h2>Email Notifications</h2>
        <div class="settings-card">
          <el-form :model="emailSettings" label-width="140px">
            <el-form-item label="SMTP Host">
              <el-input v-model="emailSettings.smtp_host" placeholder="smtp.gmail.com" />
            </el-form-item>
            <el-form-item label="SMTP Port">
              <el-input-number v-model="emailSettings.smtp_port" :min="1" :max="65535" />
            </el-form-item>
            <el-form-item label="SMTP Username">
              <el-input v-model="emailSettings.smtp_user" placeholder="your@email.com" />
            </el-form-item>
            <el-form-item label="SMTP Password">
              <el-input v-model="emailSettings.smtp_password" type="password" placeholder="Password" />
            </el-form-item>
            <el-form-item label="From Email">
              <el-input v-model="emailSettings.email_from" placeholder="noreply@example.com" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="loading" @click="saveEmailSettings">Save Settings</el-button>
              <el-button @click="testEmailConnection">Test Connection</el-button>
            </el-form-item>
          </el-form>
        </div>
      </div>

      <div class="settings-section">
        <h2>Account</h2>
        <div class="settings-card">
          <p><strong>Email:</strong> {{ authStore.user?.email }}</p>
          <p><strong>Status:</strong> {{ authStore.user?.is_active ? 'Active' : 'Inactive' }}</p>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.dashboard { display: flex; min-height: 100vh; background: #f5f7fa; }
.sidebar { width: 240px; background: #1e3a5f; color: white; display: flex; flex-direction: column; }
.logo { padding: 24px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }
.logo h2 { margin: 0; font-size: 20px; font-weight: 600; }
.nav-menu { flex: 1; padding: 16px 0; }
.nav-item { display: block; padding: 12px 24px; color: rgba(255, 255, 255, 0.7); text-decoration: none; transition: all 0.2s; }
.nav-item:hover, .nav-item.active { background: rgba(255, 255, 255, 0.1); color: white; }
.main-content { flex: 1; padding: 24px; }
.page-header { margin-bottom: 24px; }
.page-header h1 { margin: 0; font-size: 28px; font-weight: 600; color: #1e3a5f; }
.settings-section { margin-bottom: 32px; }
.settings-section h2 { font-size: 18px; font-weight: 600; color: #1e3a5f; margin: 0 0 16px; }
.settings-card { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06); }
</style>
