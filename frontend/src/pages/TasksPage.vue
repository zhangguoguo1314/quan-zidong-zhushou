<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAppStore } from '@/stores/app'
import api from '@/api'

const appStore = useAppStore()
const loading = ref(false)
const dialogVisible = ref(false)
const editingTask = ref<any>(null)

const form = ref({
  account_id: null as number | null,
  cron: ''
})

const cronPresets = [
  { label: 'Every hour', value: '0 * * * *' },
  { label: 'Every day at 8am', value: '0 8 * * *' },
  { label: 'Every day at 12pm', value: '0 12 * * *' },
  { label: 'Every day at 6pm', value: '0 18 * * *' },
  { label: 'Every Monday', value: '0 0 * * 1' }
]

const fetchTasks = async () => {
  loading.value = true
  try {
    const [tasksRes, accountsRes] = await Promise.all([
      api.get('/api/tasks'),
      api.get('/api/accounts')
    ])
    appStore.setTasks(tasksRes.data)
    appStore.setAccounts(accountsRes.data)
  } catch (error: any) {
    ElMessage.error('Failed to fetch tasks')
  } finally {
    loading.value = false
  }
}

const openDialog = (task?: any) => {
  if (task) {
    editingTask.value = task
    form.value = { ...task }
  } else {
    editingTask.value = null
    form.value = { account_id: null, cron: '' }
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!form.value.account_id || !form.value.cron) {
    ElMessage.warning('Please fill in required fields')
    return
  }

  try {
    if (editingTask.value) {
      await api.put(`/api/tasks/${editingTask.value.id}`, form.value)
      ElMessage.success('Task updated successfully')
    } else {
      await api.post('/api/tasks', form.value)
      ElMessage.success('Task created successfully')
    }
    dialogVisible.value = false
    fetchTasks()
  } catch (error: any) {
    ElMessage.error(editingTask.value ? 'Failed to update task' : 'Failed to create task')
  }
}

const handleDelete = async (task: any) => {
  try {
    await ElMessageBox.confirm('Are you sure you want to delete this task?', 'Warning', {
      confirmButtonText: 'Delete', cancelButtonText: 'Cancel', type: 'warning'
    })
    await api.delete(`/api/tasks/${task.id}`)
    ElMessage.success('Task deleted successfully')
    fetchTasks()
  } catch (error: any) {
    if (error !== 'cancel') ElMessage.error('Failed to delete task')
  }
}

const toggleTaskStatus = async (task: any) => {
  try {
    const newStatus = task.status === 'enabled' ? 'disabled' : 'enabled'
    await api.put(`/api/tasks/${task.id}`, { status: newStatus })
    ElMessage.success(`Task ${newStatus === 'enabled' ? 'enabled' : 'disabled'}`)
    fetchTasks()
  } catch (error: any) {
    ElMessage.error('Failed to update task status')
  }
}

const runTaskNow = async (task: any) => {
  try {
    await api.post(`/api/tasks/${task.id}/run`)
    ElMessage.success('Task execution started')
  } catch (error: any) {
    ElMessage.error('Failed to run task')
  }
}

const getAccountUsername = (accountId: number) => {
  const account = appStore.accounts.find(a => a.id === accountId)
  return account?.username || 'Unknown'
}

onMounted(() => {
  fetchTasks()
})
</script>

<template>
  <div class="dashboard">
    <aside class="sidebar">
      <div class="logo"><h2>Auto-Sign</h2></div>
      <nav class="nav-menu">
        <router-link to="/" class="nav-item">Dashboard</router-link>
        <router-link to="/sites" class="nav-item">Sites</router-link>
        <router-link to="/accounts" class="nav-item">Accounts</router-link>
        <router-link to="/tasks" class="nav-item active">Tasks</router-link>
        <router-link to="/logs" class="nav-item">Logs</router-link>
        <router-link to="/settings" class="nav-item">Settings</router-link>
      </nav>
    </aside>

    <main class="main-content">
      <header class="page-header">
        <h1>Tasks</h1>
        <el-button type="primary" @click="openDialog()">Add Task</el-button>
      </header>

      <div class="content-card">
        <el-table :data="appStore.tasks" style="width: 100%" v-loading="loading">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="account_id" label="Account" width="150">
            <template #default="{ row }">{{ getAccountUsername(row.account_id) }}</template>
          </el-table-column>
          <el-table-column prop="cron" label="Cron" />
          <el-table-column prop="last_run" label="Last Run" width="180">
            <template #default="{ row }">{{ row.last_run ? new Date(row.last_run).toLocaleString() : 'Never' }}</template>
          </el-table-column>
          <el-table-column prop="status" label="Status" width="120">
            <template #default="{ row }">
              <el-tag :type="row.status === 'enabled' ? 'success' : 'info'">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="Actions" width="280">
            <template #default="{ row }">
              <el-button link type="primary" @click="openDialog(row)">Edit</el-button>
              <el-button link @click="toggleTaskStatus(row)">{{ row.status === 'enabled' ? 'Disable' : 'Enable' }}</el-button>
              <el-button link type="warning" @click="runTaskNow(row)">Run Now</el-button>
              <el-button link type="danger" @click="handleDelete(row)">Delete</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <el-dialog v-model="dialogVisible" :title="editingTask ? 'Edit Task' : 'Add Task'" width="500px">
        <el-form :model="form" label-width="100px">
          <el-form-item label="Account" required>
            <el-select v-model="form.account_id" placeholder="Select account" style="width: 100%">
              <el-option v-for="account in appStore.accounts" :key="account.id" :label="account.username" :value="account.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="Cron Expression" required>
            <el-input v-model="form.cron" placeholder="* * * * *" />
          </el-form-item>
          <el-form-item label="Presets">
            <el-select placeholder="Select preset" @change="(val: string) => form.cron = val" style="width: 100%">
              <el-option v-for="preset in cronPresets" :key="preset.value" :label="preset.label" :value="preset.value" />
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="dialogVisible = false">Cancel</el-button>
          <el-button type="primary" @click="handleSubmit">Submit</el-button>
        </template>
      </el-dialog>
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
.content-card { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06); }
</style>
