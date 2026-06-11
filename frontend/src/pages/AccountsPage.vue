<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAppStore } from '@/stores/app'
import api from '@/api'

const appStore = useAppStore()
const loading = ref(false)
const dialogVisible = ref(false)
const importDialogVisible = ref(false)
const editingAccount = ref<any>(null)

const form = ref({
  site_id: null as number | null,
  username: '',
  password: '',
  token: '',
  cookie: ''
})

const importFile = ref<any>(null)
const selectedSiteId = ref<number | null>(null)

const fetchAccounts = async () => {
  loading.value = true
  try {
    const [accountsRes, sitesRes] = await Promise.all([
      api.get('/api/accounts'),
      api.get('/api/sites')
    ])
    appStore.setAccounts(accountsRes.data)
    appStore.setSites(sitesRes.data)
  } catch (error: any) {
    ElMessage.error('Failed to fetch accounts')
  } finally {
    loading.value = false
  }
}

const openDialog = (account?: any) => {
  if (account) {
    editingAccount.value = account
    form.value = { ...account }
  } else {
    editingAccount.value = null
    form.value = { site_id: null, username: '', password: '', token: '', cookie: '' }
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!form.value.site_id || !form.value.username) {
    ElMessage.warning('Please fill in required fields')
    return
  }

  try {
    if (editingAccount.value) {
      await api.put(`/api/accounts/${editingAccount.value.id}`, form.value)
      ElMessage.success('Account updated successfully')
    } else {
      await api.post('/api/accounts', form.value)
      ElMessage.success('Account created successfully')
    }
    dialogVisible.value = false
    fetchAccounts()
  } catch (error: any) {
    ElMessage.error(editingAccount.value ? 'Failed to update account' : 'Failed to create account')
  }
}

const handleDelete = async (account: any) => {
  try {
    await ElMessageBox.confirm(
      `Are you sure you want to delete this account?`,
      'Warning',
      { confirmButtonText: 'Delete', cancelButtonText: 'Cancel', type: 'warning' }
    )
    await api.delete(`/api/accounts/${account.id}`)
    ElMessage.success('Account deleted successfully')
    fetchAccounts()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('Failed to delete account')
    }
  }
}

const handleImport = async () => {
  if (!selectedSiteId.value || !importFile.value) {
    ElMessage.warning('Please select a site and a CSV file')
    return
  }

  const formData = new FormData()
  formData.append('file', importFile.value)

  try {
    await api.post(`/api/accounts/import?site_id=${selectedSiteId.value}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    ElMessage.success('Accounts imported successfully')
    importDialogVisible.value = false
    fetchAccounts()
  } catch (error: any) {
    ElMessage.error('Failed to import accounts')
  }
}

const getSiteName = (siteId: number) => {
  const site = appStore.sites.find(s => s.id === siteId)
  return site?.name || 'Unknown'
}

onMounted(() => {
  fetchAccounts()
})
</script>

<template>
  <div class="dashboard">
    <aside class="sidebar">
      <div class="logo"><h2>Auto-Sign</h2></div>
      <nav class="nav-menu">
        <router-link to="/" class="nav-item">Dashboard</router-link>
        <router-link to="/sites" class="nav-item">Sites</router-link>
        <router-link to="/accounts" class="nav-item active">Accounts</router-link>
        <router-link to="/tasks" class="nav-item">Tasks</router-link>
        <router-link to="/logs" class="nav-item">Logs</router-link>
        <router-link to="/settings" class="nav-item">Settings</router-link>
      </nav>
    </aside>

    <main class="main-content">
      <header class="page-header">
        <h1>Accounts</h1>
        <div class="header-actions">
          <el-button @click="importDialogVisible = true">Import CSV</el-button>
          <el-button type="primary" @click="openDialog()">Add Account</el-button>
        </div>
      </header>

      <div class="content-card">
        <el-table :data="appStore.accounts" style="width: 100%" v-loading="loading">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="site_id" label="Site" width="150">
            <template #default="{ row }">{{ getSiteName(row.site_id) }}</template>
          </el-table-column>
          <el-table-column prop="username" label="Username" />
          <el-table-column prop="status" label="Status" width="120">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'info'">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="Created" width="180">
            <template #default="{ row }">{{ new Date(row.created_at).toLocaleDateString() }}</template>
          </el-table-column>
          <el-table-column label="Actions" width="180">
            <template #default="{ row }">
              <el-button link type="primary" @click="openDialog(row)">Edit</el-button>
              <el-button link type="danger" @click="handleDelete(row)">Delete</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <el-dialog v-model="dialogVisible" :title="editingAccount ? 'Edit Account' : 'Add Account'" width="500px">
        <el-form :model="form" label-width="100px">
          <el-form-item label="Site" required>
            <el-select v-model="form.site_id" placeholder="Select site" style="width: 100%">
              <el-option v-for="site in appStore.sites" :key="site.id" :label="site.name" :value="site.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="Username" required>
            <el-input v-model="form.username" placeholder="Username" />
          </el-form-item>
          <el-form-item label="Password">
            <el-input v-model="form.password" type="password" placeholder="Password" />
          </el-form-item>
          <el-form-item label="Token">
            <el-input v-model="form.token" placeholder="Token" />
          </el-form-item>
          <el-form-item label="Cookie">
            <el-input v-model="form.cookie" type="textarea" placeholder="Cookie" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="dialogVisible = false">Cancel</el-button>
          <el-button type="primary" @click="handleSubmit">Submit</el-button>
        </template>
      </el-dialog>

      <el-dialog v-model="importDialogVisible" title="Import Accounts from CSV" width="500px">
        <el-form label-width="100px">
          <el-form-item label="Site" required>
            <el-select v-model="selectedSiteId" placeholder="Select site" style="width: 100%">
              <el-option v-for="site in appStore.sites" :key="site.id" :label="site.name" :value="site.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="CSV File" required>
            <el-upload ref="uploadRef" :auto-upload="false" :limit="1" :on-change="(file: any) => importFile = file.raw">
              <el-button>Select File</el-button>
            </el-upload>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="importDialogVisible = false">Cancel</el-button>
          <el-button type="primary" @click="handleImport">Import</el-button>
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
.header-actions { display: flex; gap: 12px; }
.content-card { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06); }
</style>
