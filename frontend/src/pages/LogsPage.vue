<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAppStore } from '@/stores/app'
import { useI18n } from '@/i18n'
import api from '@/api'

const appStore = useAppStore()
const { currentLang, setLang, t } = useI18n()
const loading = ref(false)

const filters = ref({
  status: '',
  task_id: null as number | null
})

const fetchLogs = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (filters.value.status) params.append('status', filters.value.status)
    if (filters.value.task_id) params.append('task_id', String(filters.value.task_id))

    const response = await api.get(`/api/logs?${params.toString()}`)
    appStore.setLogs(response.data)
  } catch (error: any) {
    ElMessage.error('获取日志失败')
  } finally {
    loading.value = false
  }
}

const handleDelete = async (log: any) => {
  try {
    await ElMessageBox.confirm('确定要删除这条日志吗？', '警告', {
      confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning'
    })
    await api.delete(`/api/logs/${log.id}`)
    ElMessage.success('日志删除成功')
    fetchLogs()
  } catch (error: any) {
    if (error !== 'cancel') ElMessage.error('删除日志失败')
  }
}

const handleDeleteAll = async () => {
  try {
    await ElMessageBox.confirm('确定要删除所有日志吗？', '警告', {
      confirmButtonText: '全部删除', cancelButtonText: '取消', type: 'warning'
    })
    await api.delete('/api/logs')
    ElMessage.success('所有日志已删除')
    fetchLogs()
  } catch (error: any) {
    if (error !== 'cancel') ElMessage.error('删除日志失败')
  }
}

const applyFilters = () => {
  fetchLogs()
}

const clearFilters = () => {
  filters.value = { status: '', task_id: null }
  fetchLogs()
}

onMounted(() => {
  fetchLogs()
})
</script>

<template>
  <div class="dashboard">
    <aside class="sidebar">
      <div class="logo"><h2>{{ t('app.title') }}</h2></div>
      <nav class="nav-menu">
        <router-link to="/" class="nav-item">{{ t('nav.dashboard') }}</router-link>
        <router-link to="/sites" class="nav-item">{{ t('nav.sites') }}</router-link>
        <router-link to="/accounts" class="nav-item">{{ t('nav.accounts') }}</router-link>
        <router-link to="/tasks" class="nav-item">{{ t('nav.tasks') }}</router-link>
        <router-link to="/logs" class="nav-item active">{{ t('nav.logs') }}</router-link>
        <router-link to="/settings" class="nav-item">{{ t('nav.settings') }}</router-link>
      </nav>
      <!-- 语言切换 -->
      <div class="lang-switch">
        <el-select v-model="currentLang" size="small" style="width: 100px" @change="(val: any) => setLang(val)">
          <el-option label="中文" value="zh" />
          <el-option label="English" value="en" />
          <el-option label="日本語" value="ja" />
        </el-select>
      </div>
    </aside>

    <main class="main-content">
      <header class="page-header">
        <h1>签到日志</h1>
        <el-button type="danger" @click="handleDeleteAll">全部删除</el-button>
      </header>

      <div class="filters-bar">
        <el-select v-model="filters.status" placeholder="按状态筛选" clearable @change="applyFilters" style="width: 150px">
          <el-option label="成功" value="success" />
          <el-option label="失败" value="failed" />
        </el-select>
        <el-button @click="clearFilters">清除筛选</el-button>
      </div>

      <div class="content-card">
        <el-table :data="appStore.logs" style="width: 100%" v-loading="loading">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="task_id" label="任务ID" width="100" />
          <el-table-column prop="status" label="状态" width="120">
            <template #default="{ row }">
              <el-tag :type="row.status === 'success' ? 'success' : 'danger'">{{ row.status === 'success' ? '成功' : '失败' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="result" label="结果" />
          <el-table-column prop="created_at" label="时间" width="180">
            <template #default="{ row }">{{ new Date(row.created_at).toLocaleString() }}</template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
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
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-header h1 { margin: 0; font-size: 28px; font-weight: 600; color: #1e3a5f; }
.filters-bar { display: flex; gap: 12px; margin-bottom: 16px; }
.content-card { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06); }
</style>
