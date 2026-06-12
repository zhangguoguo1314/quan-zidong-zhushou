<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const loading = ref(false)
const dialogVisible = ref(false)
const editingTask = ref<any>(null)
const searchKeyword = ref('')
const allSites = ref<any[]>([])
const allAccounts = ref<any[]>([])
const groupedTasks = ref<any[]>([])

const form = ref({
  account_id: null as number | null,
  cron: ''
})

const cronPresets = [
  { label: '每天 00:00', value: '0 0 * * *' },
  { label: '每天 08:00', value: '0 8 * * *' },
  { label: '每天 12:00', value: '0 12 * * *' },
  { label: '每天 18:00', value: '0 18 * * *' },
  { label: '每小时', value: '0 * * * *' },
  { label: '每周一 09:00', value: '0 9 * * 1' }
]

const fetchTasks = async () => {
  loading.value = true
  try {
    const [tasksRes, accountsRes, sitesRes] = await Promise.all([
      api.get('/api/tasks'),
      api.get('/api/accounts'),
      api.get('/api/sites')
    ])
    allAccounts.value = accountsRes.data
    allSites.value = sitesRes.data

    // 将任务按站点分组
    const accountMap: Record<number, any> = {}
    for (const acc of accountsRes.data) accountMap[acc.id] = acc
    const siteMap: Record<number, any> = {}
    for (const s of sitesRes.data) siteMap[s.id] = s

    const groups: Record<string, any> = {}
    for (const task of tasksRes.data) {
      const acc = accountMap[task.account_id]
      const site = acc ? siteMap[acc.site_id] : null
      if (!site) continue
      const key = String(site.id)
      if (!groups[key]) {
        groups[key] = {
          site_id: site.id,
          site_name: site.name,
          site_display_name: site.display_name || site.name,
          site_category: site.category || '其他',
          tasks: []
        }
      }
      groups[key].tasks.push({
        ...task,
        account_username: acc?.username,
        account_nickname: acc?.nickname
      })
    }
    groupedTasks.value = Object.values(groups)
  } catch (error: any) {
    ElMessage.error('获取任务列表失败')
  } finally {
    loading.value = false
  }
}

const filteredGroups = computed(() => {
  if (!searchKeyword.value.trim()) return groupedTasks.value
  const kw = searchKeyword.value.trim().toLowerCase()
  return groupedTasks.value
    .map((g: any) => ({
      ...g,
      tasks: g.tasks.filter((t: any) =>
        t.account_username?.toLowerCase().includes(kw) ||
        t.account_nickname?.toLowerCase().includes(kw) ||
        t.cron.toLowerCase().includes(kw)
      )
    }))
    .filter((g: any) => g.tasks.length > 0)
})

const totalTasks = computed(() => filteredGroups.value.reduce((s: number, g: any) => s + g.tasks.length, 0))

const openDialog = (task?: any) => {
  if (task) {
    editingTask.value = task
    form.value = { account_id: task.account_id, cron: task.cron }
  } else {
    editingTask.value = null
    form.value = { account_id: null, cron: '0 8 * * *' }
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!form.value.account_id || !form.value.cron) {
    ElMessage.warning('请填写必填字段')
    return
  }
  try {
    if (editingTask.value) {
      await api.put(`/api/tasks/${editingTask.value.id}`, form.value)
      ElMessage.success('任务更新成功')
    } else {
      await api.post('/api/tasks', form.value)
      ElMessage.success('任务创建成功')
    }
    dialogVisible.value = false
    fetchTasks()
  } catch (error: any) {
    ElMessage.error(editingTask.value ? '更新任务失败' : '创建任务失败')
  }
}

const handleDelete = async (task: any) => {
  try {
    await ElMessageBox.confirm('确定要删除这个任务吗？', '警告', {
      confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning'
    })
    await api.delete(`/api/tasks/${task.id}`)
    ElMessage.success('任务删除成功')
    fetchTasks()
  } catch (error: any) {
    if (error !== 'cancel') ElMessage.error('删除任务失败')
  }
}

const toggleTaskStatus = async (task: any) => {
  try {
    const newStatus = task.status === 'enabled' ? 'disabled' : 'enabled'
    await api.put(`/api/tasks/${task.id}`, { status: newStatus })
    ElMessage.success(`任务已${newStatus === 'enabled' ? '启用' : '禁用'}`)
    fetchTasks()
  } catch (error: any) {
    ElMessage.error('更新任务状态失败')
  }
}

const runTaskNow = async (task: any) => {
  try {
    await api.post(`/api/tasks/${task.id}/run`)
    ElMessage.success('任务已启动执行')
  } catch (error: any) {
    ElMessage.error('启动任务失败')
  }
}

// 按账号分组的下拉选项
const selectableAccounts = computed(() => {
  const siteMap: Record<number, any> = {}
  for (const s of allSites.value) siteMap[s.id] = s
  return allAccounts.value.map((acc: any) => {
    const site = siteMap[acc.site_id]
    return {
      id: acc.id,
      label: `${site?.display_name || site?.name || '未知'} - ${acc.username}${acc.nickname ? ' (' + acc.nickname + ')' : ''}`,
      value: acc.id
    }
  })
})

onMounted(() => {
  fetchTasks()
})
</script>

<template>
  <div class="dashboard">
    <aside class="sidebar">
      <div class="logo"><h2>全自动助手</h2></div>
      <nav class="nav-menu">
        <router-link to="/" class="nav-item">仪表盘</router-link>
        <router-link to="/sites" class="nav-item">网站管理</router-link>
        <router-link to="/accounts" class="nav-item">账号管理</router-link>
        <router-link to="/tasks" class="nav-item active">任务管理</router-link>
        <router-link to="/logs" class="nav-item">签到日志</router-link>
        <router-link to="/settings" class="nav-item">设置</router-link>
      </nav>
    </aside>

    <main class="main-content">
      <header class="page-header">
        <h1>任务管理 <span class="subtitle">(共 {{ totalTasks }} 个)</span></h1>
        <div class="header-actions">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索账号/定时表达式..."
            clearable
            style="width: 240px"
          />
          <el-button type="primary" @click="openDialog()">添加任务</el-button>
        </div>
      </header>

      <div class="content-area" v-loading="loading">
        <div v-if="filteredGroups.length === 0" class="empty-state">
          <div class="empty-icon">⏰</div>
          <div class="empty-text">暂无定时任务，先到"账号管理"添加账号，再点击右上角"添加任务"</div>
        </div>

        <div v-for="group in filteredGroups" :key="group.site_id" class="site-group">
          <div class="site-group-header">
            <div class="site-group-title">
              <span class="site-name">{{ group.site_display_name }}</span>
              <el-tag size="small" type="info">{{ group.site_category }}</el-tag>
              <span class="count">{{ group.tasks.length }} 个任务</span>
            </div>
          </div>

          <div class="site-group-body">
            <el-table :data="group.tasks" style="width: 100%">
              <el-table-column prop="id" label="ID" width="70" />
              <el-table-column label="账号" min-width="180">
                <template #default="{ row }">
                  <div class="account-cell">
                    <span class="account-name">{{ row.account_username }}</span>
                    <span v-if="row.account_nickname" class="account-nick">({{ row.account_nickname }})</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="cron" label="定时表达式" min-width="140">
                <template #default="{ row }"><code class="cron-code">{{ row.cron }}</code></template>
              </el-table-column>
              <el-table-column prop="last_run" label="上次执行" width="160">
                <template #default="{ row }">{{ row.last_run ? new Date(row.last_run).toLocaleString('zh-CN') : '从未执行' }}</template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag size="small" :type="row.status === 'enabled' ? 'success' : 'info'">
                    {{ row.status === 'enabled' ? '启用' : '禁用' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="260">
                <template #default="{ row }">
                  <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
                  <el-button link @click="toggleTaskStatus(row)">{{ row.status === 'enabled' ? '禁用' : '启用' }}</el-button>
                  <el-button link type="warning" @click="runTaskNow(row)">立即执行</el-button>
                  <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>

      <el-dialog v-model="dialogVisible" :title="editingTask ? '编辑任务' : '添加任务'" width="520px">
        <el-form :model="form" label-width="110px">
          <el-form-item label="账号" required>
            <el-select v-model="form.account_id" placeholder="选择账号" style="width: 100%" filterable>
              <el-option v-for="opt in selectableAccounts" :key="opt.id" :label="opt.label" :value="opt.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="Cron 表达式" required>
            <el-input v-model="form.cron" placeholder="0 8 * * *" />
            <div class="hint" style="margin-top: 8px">格式: 分钟 小时 日 月 星期（如 0 8 * * * 表示每天早上8点）</div>
          </el-form-item>
          <el-form-item label="预设选择">
            <el-select placeholder="选择一个预设" @change="(val: string) => form.cron = val" style="width: 100%" :model-value="''">
              <el-option v-for="preset in cronPresets" :key="preset.value" :label="preset.label" :value="preset.value" />
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit">提交</el-button>
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
.count { font-size: 13px; opacity: 0.85; }
.site-group-body { padding: 0 0 8px; }
.account-cell { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.account-name { font-weight: 500; color: #303133; }
.account-nick { font-size: 12px; color: #909399; }
.cron-code { font-family: 'Courier New', monospace; font-size: 13px; background: #f0f0f0; padding: 2px 8px; border-radius: 4px; color: #1e3a5f; }
.hint { font-size: 12px; color: #909399; }
.empty-state { text-align: center; padding: 80px 20px; background: white; border-radius: 12px; }
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.empty-text { color: #909399; font-size: 14px; }
</style>
