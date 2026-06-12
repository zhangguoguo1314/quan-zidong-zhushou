<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from '@/i18n'
import api from '@/api'

const { currentLang, setLang, t } = useI18n()
const loading = ref(false)
const dialogVisible = ref(false)
const editingAccount = ref<any>(null)
const importDialogVisible = ref(false)
const activeCategory = ref('全部')
const searchKeyword = ref('')
const allSites = ref<any[]>([])
const groupedAccounts = ref<any[]>([])

const form = ref({
  site_id: null as number | null,
  username: '',
  nickname: '',
  password: '',
  token: '',
  cookie: ''
})

const importFile = ref<any>(null)
const importSiteId = ref<number | null>(null)

const fetchAccounts = async () => {
  loading.value = true
  try {
    const [accountsRes, sitesRes] = await Promise.all([
      api.get('/api/accounts/grouped' + (searchKeyword.value.trim() ? `?search=${encodeURIComponent(searchKeyword.value.trim())}` : '')),
      api.get('/api/sites')
    ])
    groupedAccounts.value = accountsRes.data.groups || []
    allSites.value = sitesRes.data
  } catch (error: any) {
    ElMessage.error('获取账号列表失败')
  } finally {
    loading.value = false
  }
}

// 根据分类过滤
const filteredGroups = computed(() => {
  if (!activeCategory.value || activeCategory.value === '全部') {
    return groupedAccounts.value
  }
  return groupedAccounts.value.filter((g: any) => g.site_category === activeCategory.value)
})

const totalAccounts = computed(() => {
  return filteredGroups.value.reduce((sum: number, g: any) => sum + g.accounts.length, 0)
})

const openDialog = (account?: any) => {
  if (account) {
    editingAccount.value = account
    form.value = {
      site_id: account.site_id || null,
      username: account.username,
      nickname: account.nickname || '',
      password: account.password || '',
      token: account.token || '',
      cookie: account.cookie || ''
    }
  } else {
    editingAccount.value = null
    form.value = { site_id: null, username: '', nickname: '', password: '', token: '', cookie: '' }
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!form.value.site_id || !form.value.username) {
    ElMessage.warning('请填写必填字段')
    return
  }
  const payload = { ...form.value }
  if (!payload.nickname) delete payload.nickname
  try {
    if (editingAccount.value) {
      await api.put(`/api/accounts/${editingAccount.value.id}`, payload)
      ElMessage.success('账号更新成功')
    } else {
      await api.post('/api/accounts', payload)
      ElMessage.success('账号创建成功')
    }
    dialogVisible.value = false
    fetchAccounts()
  } catch (error: any) {
    ElMessage.error(editingAccount.value ? '更新账号失败' : '创建账号失败')
  }
}

const handleDelete = async (account: any, group: any) => {
  try {
    const name = account.nickname || account.username
    await ElMessageBox.confirm(`确定要删除账号 "${name}" 吗？`, '警告', {
      confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning'
    })
    await api.delete(`/api/accounts/${account.id}`)
    ElMessage.success('账号删除成功')
    fetchAccounts()
  } catch (error: any) {
    if (error !== 'cancel') ElMessage.error('删除账号失败')
  }
}

const openImportDialog = () => {
  importFile.value = null
  importSiteId.value = allSites.value[0]?.id || null
  importDialogVisible.value = true
}

const handleImport = async () => {
  if (!importSiteId.value || !importFile.value) {
    ElMessage.warning('请选择网站和CSV文件')
    return
  }
  const fd = new FormData()
  fd.append('file', importFile.value)
  try {
    await api.post(`/api/accounts/import?site_id=${importSiteId.value}`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    ElMessage.success('账号导入成功')
    importDialogVisible.value = false
    fetchAccounts()
  } catch (error: any) {
    ElMessage.error('导入账号失败')
  }
}

const handleExportAll = async () => {
  try {
    const res = await api.get('/api/accounts/export/csv', { responseType: 'blob' })
    const url = URL.createObjectURL(new Blob([res.data], { type: 'text/csv;charset=utf-8;' }))
    const a = document.createElement('a')
    a.href = url
    a.download = `accounts-${Date.now()}.csv`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) { ElMessage.error('导出失败') }
}

const handleExportSite = async (siteId: number) => {
  try {
    const res = await api.get(`/api/accounts/export/csv?site_id=${siteId}`, { responseType: 'blob' })
    const url = URL.createObjectURL(new Blob([res.data], { type: 'text/csv;charset=utf-8;' }))
    const a = document.createElement('a')
    a.href = url
    a.download = `accounts-site-${siteId}.csv`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) { ElMessage.error('导出失败') }
}

const getSiteDisplayName = (siteId: number) => {
  const site = allSites.value.find((s: any) => s.id === siteId)
  return site?.display_name || site?.name || '未知站点'
}

onMounted(() => {
  fetchAccounts()
})
</script>

<template>
  <div class="dashboard">
    <aside class="sidebar">
      <div class="logo"><h2>{{ t('app.title') }}</h2></div>
      <nav class="nav-menu">
        <router-link to="/" class="nav-item">{{ t('nav.dashboard') }}</router-link>
        <router-link to="/sites" class="nav-item">{{ t('nav.sites') }}</router-link>
        <router-link to="/accounts" class="nav-item active">{{ t('nav.accounts') }}</router-link>
        <router-link to="/tasks" class="nav-item">{{ t('nav.tasks') }}</router-link>
        <router-link to="/logs" class="nav-item">{{ t('nav.logs') }}</router-link>
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
        <h1>账号管理 <span class="subtitle">(共 {{ totalAccounts }} 个)</span></h1>
        <div class="header-actions">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索账号/昵称..."
            clearable
            style="width: 200px"
            @keyup.enter="fetchAccounts"
          />
          <el-button @click="openImportDialog">导入CSV</el-button>
          <el-button @click="handleExportAll">导出CSV</el-button>
          <el-button type="primary" @click="openDialog()">添加账号</el-button>
        </div>
      </header>

      <div class="content-area" v-loading="loading">
        <div v-if="filteredGroups.length === 0" class="empty-state">
          <div class="empty-icon">📭</div>
          <div class="empty-text">暂无账号，点击右上角"添加账号"或"导入CSV"开始</div>
        </div>

        <!-- 按站点分组显示账号 -->
        <div v-for="group in filteredGroups" :key="group.site_id" class="site-group">
          <div class="site-group-header">
            <div class="site-group-title">
              <span class="site-name">{{ group.site_display_name }}</span>
              <el-tag size="small" type="info">{{ group.site_category }}</el-tag>
              <span class="account-count">{{ group.accounts.length }} 个账号</span>
            </div>
            <div class="site-group-actions">
              <el-button size="small" link @click="handleExportSite(group.site_id)">导出本组</el-button>
            </div>
          </div>

          <div class="site-group-body">
            <el-table :data="group.accounts" style="width: 100%">
              <el-table-column prop="id" label="ID" width="70" />
              <el-table-column label="账号" min-width="180">
                <template #default="{ row }">
                  <div class="account-name-cell">
                    <div class="account-name-main">{{ row.username }}</div>
                    <div class="account-name-nick" v-if="row.nickname">昵称: {{ row.nickname }}</div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag size="small" :type="row.status === 'active' ? 'success' : 'info'">
                    {{ row.status === 'active' ? '启用' : '禁用' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="创建时间" width="160">
                <template #default="{ row }">{{ new Date(row.created_at).toLocaleDateString('zh-CN') }}</template>
              </el-table-column>
              <el-table-column label="操作" width="180">
                <template #default="{ row }">
                  <el-button link type="primary" @click="openDialog({ ...row, site_id: group.site_id })">编辑</el-button>
                  <el-button link type="danger" @click="handleDelete(row, group)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>

      <!-- 添加/编辑 账号 -->
      <el-dialog v-model="dialogVisible" :title="editingAccount ? '编辑账号' : '添加账号'" width="520px">
        <el-form :model="form" label-width="110px">
          <el-form-item label="所属网站" required>
            <el-select v-model="form.site_id" placeholder="选择网站" style="width: 100%">
              <el-option v-for="site in allSites" :key="site.id"
                :label="(site.display_name || site.name) + ' (' + site.name + ')'" :value="site.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="用户名" required>
            <el-input v-model="form.username" placeholder="登录用户名/邮箱" />
          </el-form-item>
          <el-form-item label="昵称">
            <el-input v-model="form.nickname" placeholder="便于管理的备注名（可选）" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="form.password" type="password" show-password placeholder="登录密码" />
          </el-form-item>
          <el-form-item label="Token">
            <el-input v-model="form.token" placeholder="预先获取的 token（可选）" />
          </el-form-item>
          <el-form-item label="Cookie">
            <el-input v-model="form.cookie" type="textarea" :rows="2" placeholder="预先获取的 cookie（可选）" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit">提交</el-button>
        </template>
      </el-dialog>

      <!-- 导入对话框 -->
      <el-dialog v-model="importDialogVisible" title="从CSV导入账号" width="520px">
        <el-form label-width="110px">
          <el-form-item label="目标网站" required>
            <el-select v-model="importSiteId" placeholder="选择网站" style="width: 100%">
              <el-option v-for="site in allSites" :key="site.id"
                :label="(site.display_name || site.name)" :value="site.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="CSV文件" required>
            <el-upload :auto-upload="false" :limit="1" :on-change="(file: any) => importFile = file.raw" accept=".csv">
              <el-button>选择文件</el-button>
            </el-upload>
            <div class="hint" style="margin-top: 8px">
              CSV 格式: username, nickname, password, token, cookie<br />
              第一行为表头，之后每行一个账号
            </div>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="importDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleImport">导入</el-button>
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
.subtitle { font-size: 16px; font-weight: 400; color: #909399; margin-left: 8px; }
.header-actions { display: flex; gap: 12px; align-items: center; }
.content-area { display: flex; flex-direction: column; gap: 20px; }
.site-group { background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06); }
.site-group-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; background: linear-gradient(135deg, #1e3a5f, #2d4a6f); color: white; }
.site-group-title { display: flex; align-items: center; gap: 12px; }
.site-name { font-size: 16px; font-weight: 600; }
.site-group .el-tag { color: #303133 !important; }
.account-count { font-size: 13px; opacity: 0.85; }
.site-group-body { padding: 0 0 8px; }
.site-group-header .el-button { color: rgba(255, 255, 255, 0.9) !important; }
.site-group-header .el-button:hover { color: white !important; }
.account-name-cell { display: flex; flex-direction: column; }
.account-name-main { font-weight: 500; color: #303133; }
.account-name-nick { font-size: 12px; color: #909399; margin-top: 2px; }
.hint { font-size: 12px; color: #909399; line-height: 1.6; }
.empty-state { text-align: center; padding: 80px 20px; background: white; border-radius: 12px; }
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.empty-text { color: #909399; font-size: 14px; }
</style>
