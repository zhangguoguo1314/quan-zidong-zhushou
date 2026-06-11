<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAppStore } from '@/stores/app'
import api from '@/api'

const appStore = useAppStore()
const loading = ref(false)
const dialogVisible = ref(false)
const editingSite = ref<any>(null)

const form = ref({
  name: '',
  type: '',
  url: ''
})

const siteTypes = [
  { label: 'OpenRouter', value: 'openrouter' },
  { label: 'Forum', value: 'forum' },
  { label: 'Custom', value: 'custom' }
]

const fetchSites = async () => {
  loading.value = true
  try {
    const response = await api.get('/api/sites')
    appStore.setSites(response.data)
  } catch (error: any) {
    ElMessage.error('Failed to fetch sites')
  } finally {
    loading.value = false
  }
}

const openDialog = (site?: any) => {
  if (site) {
    editingSite.value = site
    form.value = { ...site }
  } else {
    editingSite.value = null
    form.value = { name: '', type: '', url: '' }
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!form.value.name || !form.value.type) {
    ElMessage.warning('Please fill in required fields')
    return
  }

  try {
    if (editingSite.value) {
      await api.put(`/api/sites/${editingSite.value.id}`, form.value)
      ElMessage.success('Site updated successfully')
    } else {
      await api.post('/api/sites', form.value)
      ElMessage.success('Site created successfully')
    }
    dialogVisible.value = false
    fetchSites()
  } catch (error: any) {
    ElMessage.error(editingSite.value ? 'Failed to update site' : 'Failed to create site')
  }
}

const handleDelete = async (site: any) => {
  try {
    await ElMessageBox.confirm(
      `Are you sure you want to delete "${site.name}"? This will also delete all associated accounts and tasks.`,
      'Warning',
      { confirmButtonText: 'Delete', cancelButtonText: 'Cancel', type: 'warning' }
    )
    await api.delete(`/api/sites/${site.id}`)
    ElMessage.success('Site deleted successfully')
    fetchSites()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('Failed to delete site')
    }
  }
}

onMounted(() => {
  fetchSites()
})
</script>

<template>
  <div class="dashboard">
    <aside class="sidebar">
      <div class="logo">
        <h2>Auto-Sign</h2>
      </div>
      <nav class="nav-menu">
        <router-link to="/" class="nav-item">Dashboard</router-link>
        <router-link to="/sites" class="nav-item active">Sites</router-link>
        <router-link to="/accounts" class="nav-item">Accounts</router-link>
        <router-link to="/tasks" class="nav-item">Tasks</router-link>
        <router-link to="/logs" class="nav-item">Logs</router-link>
        <router-link to="/settings" class="nav-item">Settings</router-link>
      </nav>
    </aside>

    <main class="main-content">
      <header class="page-header">
        <h1>Sites</h1>
        <el-button type="primary" @click="openDialog()">Add Site</el-button>
      </header>

      <div class="content-card">
        <el-table :data="appStore.sites" style="width: 100%" v-loading="loading">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="name" label="Name" />
          <el-table-column prop="type" label="Type" width="150">
            <template #default="{ row }">
              <el-tag>{{ row.type }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="url" label="URL" />
          <el-table-column prop="created_at" label="Created" width="180">
            <template #default="{ row }">
              {{ new Date(row.created_at).toLocaleDateString() }}
            </template>
          </el-table-column>
          <el-table-column label="Actions" width="180">
            <template #default="{ row }">
              <el-button link type="primary" @click="openDialog(row)">Edit</el-button>
              <el-button link type="danger" @click="handleDelete(row)">Delete</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <el-dialog v-model="dialogVisible" :title="editingSite ? 'Edit Site' : 'Add Site'" width="500px">
        <el-form :model="form" label-width="100px">
          <el-form-item label="Name" required>
            <el-input v-model="form.name" placeholder="Site name" />
          </el-form-item>
          <el-form-item label="Type" required>
            <el-select v-model="form.type" placeholder="Select type" style="width: 100%">
              <el-option v-for="item in siteTypes" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="URL">
            <el-input v-model="form.url" placeholder="https://example.com" />
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
