<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import { useI18n } from '@/i18n'
import api from '@/api'

const router = useRouter()
const authStore = useAuthStore()
const appStore = useAppStore()
const { currentLang, setLang, t } = useI18n()

const loading = ref(false)

const stats = ref({
  sites: 0,
  accounts: 0,
  tasks: 0,
  successRate: 0
})

const recentLogs = ref<any[]>([])

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

const fetchDashboardData = async () => {
  loading.value = true
  try {
    const [sitesRes, accountsRes, tasksRes, logsRes] = await Promise.all([
      api.get('/api/sites'),
      api.get('/api/accounts'),
      api.get('/api/tasks'),
      api.get('/api/logs?limit=5')
    ])

    appStore.setSites(sitesRes.data)
    appStore.setAccounts(accountsRes.data)
    appStore.setTasks(tasksRes.data)
    appStore.setLogs(logsRes.data)

    stats.value = {
      sites: sitesRes.data.length,
      accounts: accountsRes.data.length,
      tasks: tasksRes.data.length,
      successRate: calculateSuccessRate(logsRes.data)
    }

    recentLogs.value = logsRes.data
  } catch (error: any) {
    ElMessage.error('Failed to fetch dashboard data')
  } finally {
    loading.value = false
  }
}

const calculateSuccessRate = (logs: any[]) => {
  if (logs.length === 0) return 0
  const successCount = logs.filter(log => log.status === 'success').length
  return Math.round((successCount / logs.length) * 100)
}

onMounted(() => {
  fetchDashboardData()
})
</script>

<template>
  <div class="dashboard">
    <aside class="sidebar">
      <div class="logo">
        <h2>{{ t('app.title') }}</h2>
      </div>
      <nav class="nav-menu">
        <router-link to="/" class="nav-item active">
          <span>{{ t('nav.dashboard') }}</span>
        </router-link>
        <router-link to="/sites" class="nav-item">
          <span>{{ t('nav.sites') }}</span>
        </router-link>
        <router-link to="/accounts" class="nav-item">
          <span>{{ t('nav.accounts') }}</span>
        </router-link>
        <router-link to="/tasks" class="nav-item">
          <span>{{ t('nav.tasks') }}</span>
        </router-link>
        <router-link to="/logs" class="nav-item">
          <span>{{ t('nav.logs') }}</span>
        </router-link>
        <router-link to="/settings" class="nav-item">
          <span>{{ t('nav.settings') }}</span>
        </router-link>
      </nav>
      <!-- 语言切换 -->
      <div class="lang-switch">
        <el-select v-model="currentLang" size="small" style="width: 100px" @change="(val: any) => setLang(val)">
          <el-option label="中文" value="zh" />
          <el-option label="English" value="en" />
          <el-option label="日本語" value="ja" />
        </el-select>
      </div>
      <div class="user-info">
        <span>{{ authStore.user?.email }}</span>
        <el-button link @click="handleLogout">Logout</el-button>
      </div>
    </aside>

    <main class="main-content">
      <header class="page-header">
        <h1>{{ t('dashboard.title') }}</h1>
      </header>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon sites">🌐</div>
          <div class="stat-info">
            <span class="stat-value">{{ stats.sites }}</span>
            <span class="stat-label">Sites</span>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon accounts">👤</div>
          <div class="stat-info">
            <span class="stat-value">{{ stats.accounts }}</span>
            <span class="stat-label">Accounts</span>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon tasks">⚡</div>
          <div class="stat-info">
            <span class="stat-value">{{ stats.tasks }}</span>
            <span class="stat-label">Tasks</span>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon rate">📈</div>
          <div class="stat-info">
            <span class="stat-value">{{ stats.successRate }}%</span>
            <span class="stat-label">Success Rate</span>
          </div>
        </div>
      </div>

      <div class="recent-section">
        <h2>Recent Logs</h2>
        <el-table :data="recentLogs" style="width: 100%" v-loading="loading">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="task_id" label="Task ID" width="100" />
          <el-table-column prop="status" label="Status" width="120">
            <template #default="{ row }">
              <el-tag :type="row.status === 'success' ? 'success' : 'danger'">
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="result" label="Result" />
          <el-table-column prop="created_at" label="Time" width="180">
            <template #default="{ row }">
              {{ new Date(row.created_at).toLocaleString() }}
            </template>
          </el-table-column>
        </el-table>
      </div>
    </main>
  </div>
</template>

<style scoped>
.dashboard {
  display: flex;
  min-height: 100vh;
  background: #f5f7fa;
}

.sidebar {
  width: 240px;
  background: #1e3a5f;
  color: white;
  display: flex;
  flex-direction: column;
}

.logo {
  padding: 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.nav-menu {
  flex: 1;
  padding: 16px 0;
}

.nav-item {
  display: block;
  padding: 12px 24px;
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  transition: all 0.2s;
}

.nav-item:hover,
.nav-item.active {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.user-info {
  padding: 16px 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 14px;
}

.user-info span {
  display: block;
  margin-bottom: 8px;
  opacity: 0.8;
}

.main-content {
  flex: 1;
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  color: #1e3a5f;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-bottom: 32px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.stat-icon {
  font-size: 36px;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1e3a5f;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
}

.recent-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.recent-section h2 {
  margin: 0 0 16px;
  font-size: 18px;
  font-weight: 600;
  color: #1e3a5f;
}
</style>
