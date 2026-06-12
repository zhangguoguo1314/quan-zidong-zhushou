<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from '@/i18n'
import api from '@/api'

const { currentLang, setLang, t } = useI18n()
const loading = ref(false)
const dialogVisible = ref(false)
const editingSite = ref<any>(null)
const testDialogVisible = ref(false)
const testResult = ref<{ success: boolean; message: string } | null>(null)
const testing = ref(false)
const presets = ref<any[]>([])
const selectedPreset = ref('')
const activeCategory = ref('全部')
const searchKeyword = ref('')

// ============= 分类管理相关状态 =============
const categoriesLoading = ref(false)
const categories = ref<any[]>([])
const categoryDialogVisible = ref(false)
const editingCategory = ref<any>(null)
const categoryForm = ref({
  name: '',
  display_name: '',
  description: '',
  icon: '',
  color: '#1e3a5f',
  sort_order: 0,
  is_public: true,
})

// ============= AI 配置生成器相关状态 =============
const probeForm = ref({
  url: '',
  username: '',
  password: '',
})
const probing = ref(false)
const probeResult = ref<any>(null)
const probeError = ref('')

const handleProbe = async () => {
  if (!probeForm.value.url.trim()) {
    ElMessage.warning('请输入网站地址')
    return
  }
  probing.value = true
  probeResult.value = null
  probeError.value = ''
  try {
    const payload: any = { url: probeForm.value.url.trim() }
    if (probeForm.value.username.trim()) payload.username = probeForm.value.username.trim()
    if (probeForm.value.password.trim()) payload.password = probeForm.value.password.trim()
    const response = await api.post('/api/config-generator/probe', payload)
    probeResult.value = response.data
    if (response.data.success) {
      ElMessage.success('探测完成')
    } else {
      probeError.value = response.data.error || '探测失败'
      ElMessage.warning('探测未发现可用接口')
    }
  } catch (_error: any) {
    probeError.value = '探测请求失败，请检查网站地址是否正确'
    ElMessage.error('探测请求失败')
  } finally {
    probing.value = false
  }
}

const copyProbeConfig = () => {
  if (!probeResult.value?.api_config) return
  navigator.clipboard
    .writeText(JSON.stringify(probeResult.value.api_config, null, 2))
    .then(() => ElMessage.success('已复制 api_config 到剪贴板'))
    .catch(() => ElMessage.warning('复制失败'))
}

const copyProbeCurl = () => {
  if (!probeResult.value?.curl_command) return
  navigator.clipboard
    .writeText(probeResult.value.curl_command)
    .then(() => ElMessage.success('已复制 curl 命令到剪贴板'))
    .catch(() => ElMessage.warning('复制失败'))
}

const importProbeAsSite = () => {
  if (!probeResult.value?.api_config) return
  const cfg = probeResult.value.api_config
  editingSite.value = null
  form.value = {
    name: '',
    display_name: '',
    category: '其他',
    type: 'custom-api',
    url: probeForm.value.url.trim(),
    api_config: { ...defaultApiConfig, ...cfg },
  }
  // 尝试从 URL 提取站点名称
  try {
    const u = new URL(probeForm.value.url.trim())
    form.value.name = u.hostname
    form.value.display_name = u.hostname
  } catch {
    form.value.name = '探测站点'
  }
  selectedPreset.value = ''
  dialogVisible.value = true
  ElMessage.info('已自动填充站点创建表单，请补充信息后提交')
}

// ============= 按分类分组的站点列表 =============
const groupedSites = ref<any[]>([])
const useGroupedView = ref(true)
const allSites = ref<any[]>([])

const form = ref({
  name: '',
  display_name: '',
  category: '其他',
  type: '',
  url: '',
  api_config: null as any,
})

const testForm = ref({
  username: '',
  password: '',
})

const siteTypes = [
  { label: '自定义API签到（推荐）', value: 'custom-api' },
  { label: '哈基米API站', value: 'gemai' },
  { label: '辉哥boy公益站', value: 'lizhiyu' },
  { label: 'OpenRouter', value: 'openrouter' },
  { label: '论坛类(Playwright)', value: 'forum' },
  { label: '其他(Playwright)', value: 'custom' },
]

const defaultApiConfig = {
  login_url: '',
  login_method: 'POST',
  login_body_template: '{"username": "{{username}}", "password": "{{password}}"}',
  login_content_type: 'application/json',
  login_extra_headers: {},
  token_path: 'token',
  signin_url: '',
  signin_method: 'POST',
  signin_body: '{}',
  signin_content_type: 'application/json',
  signin_extra_headers: {},
  auth_header_template: 'Bearer {{token}}',
  auth_header_name: 'Authorization',
  success_field: '',
  message_field: '',
  force_login: false,
  login_only: false,
  verify_ssl: true,
  extra_headers: {},
}

// 计算：下拉分类选项（来自 categories API，加上"其他"）
const categoryOptions = computed(() => {
  const fromApi = categories.value.map((c: any) => ({
    label: (c.display_name || c.name || ''),
    value: c.name || c.display_name,
  }))
  const hasOther = fromApi.some((opt: any) => opt.value === '其他')
  if (!hasOther) fromApi.push({ label: '其他', value: '其他' })
  return fromApi
})

// 过滤：根据 activeCategory 和 searchKeyword 过滤（分组视图）
const filteredGroups = computed(() => {
  const kw = searchKeyword.value.trim().toLowerCase()
  let groups = groupedSites.value

  if (activeCategory.value && activeCategory.value !== '全部') {
    groups = groups.filter((g: any) => (g.category_name || g.name) === activeCategory.value)
  }

  if (kw) {
    groups = groups
      .map((g: any) => ({
        ...g,
        sites: (g.sites || []).filter((s: any) =>
          (s.name || '').toLowerCase().includes(kw) ||
          (s.display_name || '').toLowerCase().includes(kw)
        ),
      }))
      .filter((g: any) => g.sites.length > 0)
  }

  return groups
})

// 过滤：扁平列表（兼容旧视图）
const filteredSites = computed(() => {
  let list = allSites.value
  if (activeCategory.value && activeCategory.value !== '全部') {
    list = list.filter((s: any) => (s.category || '其他') === activeCategory.value)
  }
  if (searchKeyword.value.trim()) {
    const kw = searchKeyword.value.trim().toLowerCase()
    list = list.filter((s: any) =>
      (s.name || '').toLowerCase().includes(kw) ||
      (s.display_name || '').toLowerCase().includes(kw)
    )
  }
  return list
})

// 分类标签（基于分类管理数据）
const categoryTabStats = computed(() => {
  const stats: Record<string, number> = {}
  stats['全部'] = allSites.value.length
  for (const s of allSites.value) {
    const cat = s.category || '其他'
    stats[cat] = (stats[cat] || 0) + 1
  }
  return stats
})

// 分类选项名称列表（用于 tab）
const categoryTabNames = computed(() => {
  const names = categoryOptions.value.map((c: any) => c.value)
  // 去重 + 保持顺序
  return Array.from(new Set(names))
})

// ============= 数据加载 =============
const fetchSites = async () => {
  loading.value = true
  try {
    const response = await api.get('/api/sites')
    allSites.value = response.data
  } catch (_error) {
    ElMessage.error('获取网站列表失败')
  } finally {
    loading.value = false
  }
}

const fetchSitesGrouped = async () => {
  try {
    const response = await api.getSitesGrouped()
    groupedSites.value = response.data?.groups || response.data || []
    // 若分组数据里没有 sites 但有扁平数据，则回退到扁平展示
    if (!Array.isArray(groupedSites.value) || groupedSites.value.length === 0) {
      useGroupedView.value = false
    }
  } catch (_error) {
    useGroupedView.value = false
  }
}

const fetchCategories = async () => {
  categoriesLoading.value = true
  try {
    const response = await api.getSitesCategories()
    if (Array.isArray(response.data)) {
      categories.value = response.data
    } else if (response.data && Array.isArray(response.data.categories)) {
      categories.value = response.data.categories
    } else if (response.data && Array.isArray(response.data.items)) {
      categories.value = response.data.items
    }
  } catch (_error) {
    // 分类 API 失败时保持空数组（但仍会 fallback 到 siteCategories）
  } finally {
    categoriesLoading.value = false
  }
}

const fetchPresets = async () => {
  try {
    const response = await api.get('/api/sites/presets')
    const presetData = response.data.presets || {}
    presets.value = Object.entries(presetData).map(([key, val]: [string, any]) => ({
      key,
      name: val.name,
      description: val.description,
      type: val.type,
      api_config: val.api_config,
      display_name: val.display_name || val.name,
      category: val.category || '其他',
    }))
  } catch (_error) {
    // 预设列表加载失败时不阻塞
  }
}

const applyPreset = (key: string) => {
  const preset = presets.value.find((p: any) => p.key === key)
  if (preset) {
    form.value.name = preset.name
    form.value.display_name = preset.display_name || preset.name
    form.value.category = preset.category || '其他'
    form.value.type = preset.type
    form.value.api_config = JSON.parse(JSON.stringify(preset.api_config))
    if (preset.api_config?.login_url) {
      try {
        const u = new URL(preset.api_config.login_url)
        form.value.url = `${u.protocol}//${u.host}`
      } catch {
        form.value.url = preset.api_config.login_url
      }
    }
    ElMessage.success(`已应用预设: ${preset.name}`)
  }
}

// ============= 站点 CRUD =============
const openDialog = (site?: any) => {
  if (site) {
    editingSite.value = site
    form.value = {
      name: site.name,
      display_name: site.display_name || '',
      category: site.category || '其他',
      type: site.type,
      url: site.url || '',
      api_config: site.api_config ? JSON.parse(JSON.stringify(site.api_config)) : { ...defaultApiConfig },
    }
  } else {
    editingSite.value = null
    form.value = { name: '', display_name: '', category: '其他', type: '', url: '', api_config: { ...defaultApiConfig } }
  }
  selectedPreset.value = ''
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!form.value.name || !form.value.type) {
    ElMessage.warning('请填写必填字段')
    return
  }
  if (form.value.type === 'custom-api') {
    const cfg = form.value.api_config
    if (!cfg || (!cfg.login_url && !cfg.signin_url)) {
      ElMessage.warning('请至少填写登录地址或签到地址')
      return
    }
  }

  const payload: any = {
    name: form.value.name,
    display_name: form.value.display_name,
    category: form.value.category,
    type: form.value.type,
    url: form.value.url,
  }
  if (form.value.type === 'custom-api' && form.value.api_config) {
    payload.api_config = form.value.api_config
  }

  try {
    if (editingSite.value) {
      await api.put(`/api/sites/${editingSite.value.id}`, payload)
      ElMessage.success('网站更新成功')
    } else {
      await api.post('/api/sites', payload)
      ElMessage.success('网站创建成功')
    }
    dialogVisible.value = false
    await Promise.all([fetchSites(), fetchSitesGrouped()])
  } catch (_error) {
    ElMessage.error(editingSite.value ? '更新网站失败' : '创建网站失败')
  }
}

const handleDelete = async (site: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 "${site.name}" 吗？这将同时删除所有关联的账号和任务。`,
      '警告',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    await api.delete(`/api/sites/${site.id}`)
    ElMessage.success('网站删除成功')
    await Promise.all([fetchSites(), fetchSitesGrouped()])
  } catch (error: any) {
    if (error !== 'cancel') ElMessage.error('删除网站失败')
  }
}

// ============= 测试 =============
const openTestDialog = (site: any) => {
  editingSite.value = site
  testForm.value = { username: '', password: '' }
  testResult.value = null
  testDialogVisible.value = true
}

const runTest = async () => {
  if (!testForm.value.username || !testForm.value.password) {
    ElMessage.warning('请输入测试用的用户名和密码')
    return
  }
  testing.value = true
  testResult.value = null
  try {
    const response = await api.post('/api/sites/test', {
      site_type: editingSite.value.type,
      api_config: editingSite.value.api_config,
      username: testForm.value.username,
      password: testForm.value.password,
    })
    testResult.value = response.data
    if (response.data.success) {
      ElMessage.success('测试成功')
    } else {
      ElMessage.warning('测试失败')
    }
  } catch (_error) {
    ElMessage.error('测试请求失败')
  } finally {
    testing.value = false
  }
}

const getTypeLabel = (type: string) => {
  const t = siteTypes.find((s: any) => s.value === type)
  return t ? t.label : type
}

const getDisplayName = (site: any) => {
  return site.display_name || site.name
}

// ============= 导出/导入 JSON =============
const handleExportAll = async () => {
  try {
    const response = await api.get('/api/sites/export/all')
    const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `sites-config-${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (_error) {
    ElMessage.error('导出失败')
  }
}

const jsonImportVisible = ref(false)
const jsonImportText = ref('')

const openJsonImport = () => {
  jsonImportText.value = ''
  jsonImportVisible.value = true
}

const handleJsonImport = async () => {
  if (!jsonImportText.value.trim()) {
    ElMessage.warning('请粘贴 JSON 配置内容')
    return
  }
  try {
    const parsed = JSON.parse(jsonImportText.value)
    let sitesToImport: any[] = []
    if (Array.isArray(parsed)) {
      sitesToImport = parsed
    } else if (parsed.sites && Array.isArray(parsed.sites)) {
      sitesToImport = parsed.sites
    } else if (parsed.name || parsed.api_config) {
      sitesToImport = [parsed]
    } else {
      ElMessage.warning('JSON 格式不正确，请确保包含站点配置信息（name/type/api_config 等）')
      return
    }

    if (sitesToImport.length === 1) {
      const payload = {
        name: sitesToImport[0].name || '导入的站点',
        display_name: sitesToImport[0].display_name || '',
        category: sitesToImport[0].category || '其他',
        type: sitesToImport[0].type || 'custom-api',
        url: sitesToImport[0].url || '',
        api_config: sitesToImport[0].api_config,
      }
      await api.post('/api/sites', payload)
      ElMessage.success('站点导入成功')
    } else {
      await api.post('/api/sites/bulk', {
        sites: sitesToImport.map((s: any) => ({
          name: s.name || '导入的站点',
          display_name: s.display_name || '',
          category: s.category || '其他',
          type: s.type || 'custom-api',
          url: s.url || '',
          api_config: s.api_config,
        })),
      })
      ElMessage.success(`成功导入 ${sitesToImport.length} 个站点`)
    }
    jsonImportVisible.value = false
    await Promise.all([fetchSites(), fetchSitesGrouped()])
  } catch (_e) {
    ElMessage.error('导入失败：JSON 解析错误或 API 异常')
  }
}

const copySiteConfig = (site: any) => {
  const config = {
    name: site.name,
    display_name: site.display_name || '',
    category: site.category || '其他',
    type: site.type,
    url: site.url || '',
    api_config: site.api_config,
  }
  navigator.clipboard
    .writeText(JSON.stringify(config, null, 2))
    .then(() => ElMessage.success('已复制 JSON 配置到剪贴板'))
    .catch(() => ElMessage.warning('复制失败，可手动复制'))
}

// ============= 分类管理 CRUD =============
const openCategoryDialog = (cat?: any) => {
  if (cat) {
    editingCategory.value = cat
    categoryForm.value = {
      name: cat.name || '',
      display_name: cat.display_name || '',
      description: cat.description || '',
      icon: cat.icon || '',
      color: cat.color || '#1e3a5f',
      sort_order: cat.sort_order ?? cat.sort_order ?? 0,
      is_public: cat.is_public !== false,
    }
  } else {
    editingCategory.value = null
    const maxOrder = categories.value.reduce((m: number, c: any) => Math.max(m, c.sort_order || 0), 0)
    categoryForm.value = {
      name: '',
      display_name: '',
      description: '',
      icon: '📁',
      color: '#1e3a5f',
      sort_order: maxOrder + 1,
      is_public: true,
    }
  }
  categoryDialogVisible.value = true
}

const handleCategorySubmit = async () => {
  if (!categoryForm.value.name) {
    ElMessage.warning('请填写分类名称')
    return
  }
  const payload = { ...categoryForm.value }
  try {
    if (editingCategory.value) {
      await api.updateSiteCategory(editingCategory.value.id || editingCategory.value.name, payload)
      ElMessage.success('分类更新成功')
    } else {
      await api.createSiteCategory(payload)
      ElMessage.success('分类创建成功')
    }
    categoryDialogVisible.value = false
    await fetchCategories()
  } catch (_error) {
    ElMessage.error(editingCategory.value ? '更新分类失败' : '创建分类失败')
  }
}

const handleCategoryDelete = async (cat: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除分类 "${cat.display_name || cat.name}" 吗？已使用此分类的站点将保留分类名。`,
      '警告',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    await api.deleteSiteCategory(cat.id || cat.name)
    ElMessage.success('分类删除成功')
    await fetchCategories()
  } catch (error: any) {
    if (error !== 'cancel') ElMessage.error('删除分类失败')
  }
}

// 分类列表（按排序字段）
const sortedCategories = computed(() => {
  return [...categories.value].sort(
    (a: any, b: any) => (a.sort_order || 0) - (b.sort_order || 0)
  )
})

onMounted(async () => {
  await Promise.all([fetchSites(), fetchPresets(), fetchCategories()])
  await fetchSitesGrouped()
})
</script>

<template>
  <div class="dashboard">
    <aside class="sidebar">
      <div class="logo"><h2>{{ t('app.title') }}</h2></div>
      <nav class="nav-menu">
        <router-link to="/" class="nav-item">{{ t('nav.dashboard') }}</router-link>
        <router-link to="/sites" class="nav-item active">{{ t('nav.sites') }}</router-link>
        <router-link to="/accounts" class="nav-item">{{ t('nav.accounts') }}</router-link>
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
        <h1>网站管理</h1>
        <div class="header-actions">
          <el-input v-model="searchKeyword" placeholder="搜索站点..." clearable style="width: 180px" />
          <el-button @click="openJsonImport">粘贴JSON导入</el-button>
          <el-button @click="handleExportAll">导出全部</el-button>
          <el-button type="primary" @click="openDialog()">添加网站</el-button>
        </div>
      </header>

      <!-- AI 智能配置生成器 -->
      <div class="content-card" style="margin-bottom: 16px">
        <div class="card-title-row">
          <h2 class="card-title">AI 智能配置生成器</h2>
        </div>
        <div class="probe-form">
          <el-form :inline="false" label-width="100px">
            <el-form-item label="网站地址" required>
              <el-input v-model="probeForm.url" placeholder="https://example.com" style="width: 100%" />
            </el-form-item>
            <el-form-item label="测试账号">
              <el-input v-model="probeForm.username" placeholder="选填，用于登录探测" style="width: 100%" />
            </el-form-item>
            <el-form-item label="测试密码">
              <el-input v-model="probeForm.password" type="password" show-password placeholder="选填，用于登录探测" style="width: 100%" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="probing" @click="handleProbe">开始探测</el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 探测成功结果 -->
        <div v-if="probeResult && probeResult.success" class="probe-result-section">
          <el-alert type="success" title="探测成功" :closable="false" show-icon style="margin-bottom: 16px" />

          <div v-if="probeResult.login_url || probeResult.signin_url" style="margin-bottom: 16px">
            <div v-if="probeResult.login_url" style="margin-bottom: 8px">
              <span class="hint">登录 URL：</span>
              <code>{{ probeResult.login_url }}</code>
            </div>
            <div v-if="probeResult.signin_url">
              <span class="hint">签到 URL：</span>
              <code>{{ probeResult.signin_url }}</code>
            </div>
          </div>

          <div v-if="probeResult.api_config" style="margin-bottom: 16px">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px">
              <span style="font-weight: 600; color: #303133">生成的 api_config</span>
              <el-button size="small" @click="copyProbeConfig">复制</el-button>
            </div>
            <pre class="probe-code-block">{{ JSON.stringify(probeResult.api_config, null, 2) }}</pre>
          </div>

          <div v-if="probeResult.curl_command" style="margin-bottom: 16px">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px">
              <span style="font-weight: 600; color: #303133">curl 测试命令</span>
              <el-button size="small" @click="copyProbeCurl">复制</el-button>
            </div>
            <pre class="probe-code-block">{{ probeResult.curl_command }}</pre>
          </div>

          <el-button type="success" @click="importProbeAsSite">一键导入为站点</el-button>
        </div>

        <!-- 探测失败结果 -->
        <div v-if="probeResult && !probeResult.success" class="probe-result-section">
          <el-alert type="warning" title="探测未发现可用接口" :closable="false" show-icon style="margin-bottom: 16px">
            <template #default>
              <div>{{ probeError || probeResult.error || '未能自动探测到登录和签到接口' }}</div>
            </template>
          </el-alert>

          <div v-if="probeResult.probed_endpoints && probeResult.probed_endpoints.length > 0">
            <div style="font-weight: 600; color: #303133; margin-bottom: 8px">已探测的端点：</div>
            <el-table :data="probeResult.probed_endpoints" size="small" style="width: 100%">
              <el-table-column prop="url" label="端点" min-width="300" show-overflow-tooltip />
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag size="small" :type="row.status === 200 ? 'success' : row.status ? 'warning' : 'info'">
                    {{ row.status || '无响应' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="content_type" label="类型" width="150" show-overflow-tooltip />
            </el-table>
          </div>
        </div>

        <!-- 探测错误 -->
        <div v-if="probeError && !probeResult" class="probe-result-section">
          <el-alert type="error" :title="probeError" :closable="false" show-icon />
        </div>
      </div>

      <!-- 分类管理卡片 -->
      <div class="content-card" v-loading="categoriesLoading" style="margin-bottom: 16px">
        <div class="card-title-row">
          <h2 class="card-title">分类管理</h2>
          <el-button type="primary" size="small" @click="openCategoryDialog()">+ 添加分类</el-button>
        </div>

        <div v-if="sortedCategories.length === 0" class="empty-state" style="padding: 24px 0">
          <div class="empty-text">暂无分类，点击右上角"添加分类"开始管理你的站点分类</div>
        </div>

        <el-table v-else :data="sortedCategories" style="width: 100%" size="default">
          <el-table-column width="64" label="图标">
            <template #default="{ row }">
              <span class="category-icon" :style="{ color: row.color || '#1e3a5f' }">{{ row.icon || '📁' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="名称" min-width="140">
            <template #default="{ row }">
              <b>{{ row.display_name || row.name }}</b>
              <span class="hint" v-if="row.display_name && row.display_name !== row.name"> ({{ row.name }})</span>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip>
            <template #default="{ row }">
              <span v-if="row.description">{{ row.description }}</span>
              <span v-else class="hint">—</span>
            </template>
          </el-table-column>
          <el-table-column width="80" label="颜色">
            <template #default="{ row }">
              <span class="color-chip" :style="{ background: row.color || '#1e3a5f' }"></span>
            </template>
          </el-table-column>
          <el-table-column prop="sort_order" label="排序" width="80" />
          <el-table-column label="公开" width="80">
            <template #default="{ row }">
              <el-tag size="small" :type="row.is_public !== false ? 'success' : 'info'">
                {{ row.is_public !== false ? '公开' : '私密' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180">
            <template #default="{ row }">
              <el-button link type="primary" @click="openCategoryDialog(row)">编辑</el-button>
              <el-button link type="danger" @click="handleCategoryDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 分类标签（过滤） -->
      <div class="category-tabs">
        <div class="tab" :class="{ active: activeCategory === '全部' }" @click="activeCategory = '全部'">
          全部 ({{ categoryTabStats['全部'] || 0 }})
        </div>
        <div
          v-for="catName in categoryTabNames"
          :key="catName"
          class="tab"
          :class="{ active: activeCategory === catName }"
          @click="activeCategory = catName"
        >
          {{ catName }} ({{ categoryTabStats[catName] || 0 }})
        </div>
      </div>

      <!-- 站点列表：按分类分组视图 -->
      <div class="content-card" v-if="useGroupedView && filteredGroups.length > 0" v-loading="loading">
        <div v-for="group in filteredGroups" :key="group.category_name || group.name" class="site-group-inline">
          <div class="site-group-header-inline">
            <span class="category-icon-inline">{{ group.icon || '📁' }}</span>
            <span class="category-name-inline" :style="{ color: group.color || '#1e3a5f' }">
              {{ group.display_name || group.category_name || group.name }}
            </span>
            <span class="category-count-inline">{{ (group.sites || []).length }} 个站点</span>
          </div>
          <el-table :data="group.sites" style="width: 100%" size="default">
            <el-table-column label="名称" min-width="200">
              <template #default="{ row }">
                <div class="site-name-cell">
                  <div class="site-name-main">{{ getDisplayName(row) }}</div>
                  <div class="site-name-sub" v-if="row.display_name && row.display_name !== row.name">
                    真实名称: {{ row.name }}
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="type" label="类型" width="160">
              <template #default="{ row }">
                <el-tag :type="['gemai', 'custom-api', 'lizhiyu'].includes(row.type) ? 'success' : 'info'">
                  {{ getTypeLabel(row.type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="url" label="网址" min-width="160" show-overflow-tooltip />
            <el-table-column prop="created_at" label="创建时间" width="170">
              <template #default="{ row }">{{ new Date(row.created_at).toLocaleDateString('zh-CN') }}</template>
            </el-table-column>
            <el-table-column label="操作" width="280">
              <template #default="{ row }">
                <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
                <el-button v-if="row.api_config || row.type === 'gemai'" link type="success" @click="openTestDialog(row)">
                  测试
                </el-button>
                <el-button link type="warning" @click="copySiteConfig(row)">复制JSON</el-button>
                <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <!-- 站点列表：回退到扁平视图（当分组 API 失败或数据为空时） -->
      <div class="content-card" v-else-if="!useGroupedView || filteredSites.length > 0" v-loading="loading">
        <el-table :data="filteredSites" style="width: 100%">
          <el-table-column prop="category" label="分类" width="110">
            <template #default="{ row }">
              <el-tag size="small" type="info">{{ row.category || '其他' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="名称" min-width="200">
            <template #default="{ row }">
              <div class="site-name-cell">
                <div class="site-name-main">{{ getDisplayName(row) }}</div>
                <div class="site-name-sub" v-if="row.display_name && row.display_name !== row.name">
                  真实名称: {{ row.name }}
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="type" label="类型" width="160">
            <template #default="{ row }">
              <el-tag :type="['gemai', 'custom-api', 'lizhiyu'].includes(row.type) ? 'success' : 'info'">
                {{ getTypeLabel(row.type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="url" label="网址" min-width="160" show-overflow-tooltip />
          <el-table-column prop="created_at" label="创建时间" width="170">
            <template #default="{ row }">{{ new Date(row.created_at).toLocaleDateString('zh-CN') }}</template>
          </el-table-column>
          <el-table-column label="操作" width="280">
            <template #default="{ row }">
              <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
              <el-button v-if="row.api_config || row.type === 'gemai'" link type="success" @click="openTestDialog(row)">
                测试
              </el-button>
              <el-button link type="warning" @click="copySiteConfig(row)">复制JSON</el-button>
              <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 空状态 -->
      <div class="content-card" v-else>
        <div class="empty-state">
          <div class="empty-icon">📭</div>
          <div class="empty-text">暂无站点，点击右上角"添加网站"或"粘贴JSON导入"开始</div>
        </div>
      </div>

      <!-- 添加/编辑网站 -->
      <el-dialog v-model="dialogVisible" :title="editingSite ? '编辑网站' : '添加网站'" width="720px">
        <el-form :model="form" label-width="130px">
          <el-form-item label="显示名称">
            <el-input v-model="form.display_name" placeholder="用于管理页面显示（可选）" />
          </el-form-item>
          <el-form-item label="站点名称" required>
            <el-input v-model="form.name" placeholder="站点原始名称（如: 哈基米API站）" />
          </el-form-item>
          <el-form-item label="分类" required>
            <el-select
              v-model="form.category"
              placeholder="选择或输入分类"
              filterable
              allow-create
              default-first-option
              style="width: 100%"
            >
              <el-option
                v-for="opt in categoryOptions"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>
            <div class="hint" style="margin-left: 10px">可直接输入自定义分类名</div>
          </el-form-item>
          <el-form-item label="站点类型" required>
            <el-select v-model="form.type" placeholder="选择类型" style="width: 100%">
              <el-option v-for="item in siteTypes" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="官网网址">
            <el-input v-model="form.url" placeholder="https://example.com" />
          </el-form-item>

          <!-- 预设模板（仅 custom-api 时显示） -->
          <el-form-item v-if="form.type === 'custom-api'" label="预设模板">
            <el-select
              v-model="selectedPreset"
              placeholder="选择预设一键导入"
              style="width: 100%"
              @change="applyPreset"
            >
              <el-option v-for="p in presets" :key="p.key" :label="p.name + ' - ' + p.description" :value="p.key" />
            </el-select>
            <div class="hint" style="margin-top: 4px">选择预设后自动填充以下配置项</div>
          </el-form-item>

          <!-- API 配置表单 -->
          <template v-if="form.type === 'custom-api'">
            <el-divider content-position="left">登录配置</el-divider>
            <el-form-item label="登录地址">
              <el-input v-model="form.api_config.login_url" placeholder="https://api.example.com/v1/login" />
            </el-form-item>
            <el-form-item label="请求方法">
              <el-select v-model="form.api_config.login_method" style="width: 160px">
                <el-option label="POST" value="POST" />
                <el-option label="GET" value="GET" />
                <el-option label="PUT" value="PUT" />
              </el-select>
            </el-form-item>
            <el-form-item label="请求体模板">
              <el-input
                v-model="form.api_config.login_body_template"
                type="textarea"
                :rows="3"
                placeholder='{"username": "{{username}}", "password": "{{password}}"}'
              />
              <div class="hint" style="margin-left: 10px">
                使用 <code v-text="'{{username}}'"></code> 和 <code v-text="'{{password}}'"></code> 作为占位符
              </div>
            </el-form-item>
            <el-form-item label="Content-Type">
              <el-input v-model="form.api_config.login_content_type" placeholder="application/json" style="width: 260px" />
            </el-form-item>

            <el-divider content-position="left">认证配置</el-divider>
            <el-form-item label="Token路径">
              <el-input v-model="form.api_config.token_path" placeholder="token 或 data.id" style="width: 260px" />
              <div class="hint" style="margin-left: 10px">从登录响应提取 token 的字段路径，支持嵌套（如 data.id）</div>
            </el-form-item>
            <el-form-item label="认证Header名">
              <el-input
                v-model="form.api_config.auth_header_name"
                placeholder="Authorization 或 New-Api-User"
                style="width: 260px"
              />
            </el-form-item>
            <el-form-item label="Header模板">
              <el-input v-model="form.api_config.auth_header_template" placeholder='Bearer {{token}}' />
            </el-form-item>

            <el-divider content-position="left">签到配置</el-divider>
            <el-form-item label="签到地址">
              <el-input v-model="form.api_config.signin_url" placeholder="https://api.example.com/v1/signin" />
            </el-form-item>
            <el-form-item label="请求方法">
              <el-select v-model="form.api_config.signin_method" style="width: 160px">
                <el-option label="POST" value="POST" />
                <el-option label="GET" value="GET" />
                <el-option label="PUT" value="PUT" />
              </el-select>
            </el-form-item>
            <el-form-item label="请求体">
              <el-input v-model="form.api_config.signin_body" type="textarea" :rows="2" placeholder="{}" />
            </el-form-item>
            <el-form-item label="Content-Type">
              <el-input v-model="form.api_config.signin_content_type" placeholder="application/json" style="width: 260px" />
            </el-form-item>
            <el-form-item label="成功字段">
              <el-input
                v-model="form.api_config.success_field"
                placeholder="success（留空表示不检查）"
                style="width: 260px"
              />
            </el-form-item>
            <el-form-item label="消息字段">
              <el-input
                v-model="form.api_config.message_field"
                placeholder="message（从响应提取提示）"
                style="width: 260px"
              />
            </el-form-item>
            <el-form-item label="高级选项">
              <el-checkbox v-model="form.api_config.force_login">
                强制登录（即使账号已有 token 也登录）
              </el-checkbox>
              &nbsp;&nbsp;
              <el-checkbox v-model="form.api_config.login_only">登录即签到（仅执行登录步骤）</el-checkbox>
            </el-form-item>
          </template>

          <el-alert
            v-if="['gemai', 'lizhiyu'].includes(form.type)"
            type="success"
            :closable="false"
            show-icon
            style="margin-top: 8px"
          >
            <template #title>✓ 内置类型，后端已有对应的签到逻辑，直接保存即可使用</template>
          </el-alert>
        </el-form>
        <template #footer>
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit">提交</el-button>
        </template>
      </el-dialog>

      <!-- 分类管理对话框 -->
      <el-dialog v-model="categoryDialogVisible" :title="editingCategory ? '编辑分类' : '添加分类'" width="560px">
        <el-form :model="categoryForm" label-width="110px">
          <el-form-item label="分类名称" required>
            <el-input v-model="categoryForm.name" placeholder="如 API服务、公益站点（唯一标识）" />
          </el-form-item>
          <el-form-item label="显示名">
            <el-input v-model="categoryForm.display_name" placeholder="用于卡片/分组标题展示（可选）" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="categoryForm.description" type="textarea" :rows="2" placeholder="此分类的用途说明（可选）" />
          </el-form-item>
          <el-form-item label="图标">
            <el-input v-model="categoryForm.icon" placeholder="📁 或其他 emoji" maxlength="4" style="width: 200px" />
            <span class="hint" style="margin-left: 10px">单个 emoji 字符</span>
          </el-form-item>
          <el-form-item label="颜色">
            <el-color-picker v-model="categoryForm.color" show-alpha />
            <span class="hint" style="margin-left: 10px">分组标题/图标颜色</span>
          </el-form-item>
          <el-form-item label="排序">
            <el-input-number v-model="categoryForm.sort_order" :min="0" :step="1" />
            <span class="hint" style="margin-left: 10px">数值越小越靠前</span>
          </el-form-item>
          <el-form-item label="是否公开">
            <el-switch v-model="categoryForm.is_public" active-text="公开" inactive-text="私密" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="categoryDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleCategorySubmit">保存</el-button>
        </template>
      </el-dialog>

      <!-- 测试对话框 -->
      <el-dialog v-model="testDialogVisible" title="测试签到" width="500px">
        <el-form :model="testForm" label-width="100px">
          <el-form-item label="用户名" required>
            <el-input v-model="testForm.username" placeholder="登录用的用户名/邮箱" />
          </el-form-item>
          <el-form-item label="密码" required>
            <el-input v-model="testForm.password" type="password" show-password placeholder="登录用的密码" />
          </el-form-item>
        </el-form>

        <div v-if="testResult" class="test-result">
          <el-alert
            :type="testResult.success ? 'success' : 'error'"
            :title="testResult.success ? '测试成功' : '测试失败'"
            :closable="false"
            show-icon
          >
            <template #default><div class="result-msg">{{ testResult.message }}</div></template>
          </el-alert>
        </div>

        <template #footer>
          <el-button @click="testDialogVisible = false">关闭</el-button>
          <el-button type="primary" :loading="testing" @click="runTest">执行测试</el-button>
        </template>
      </el-dialog>

      <!-- JSON 粘贴导入 -->
      <el-dialog v-model="jsonImportVisible" title="粘贴 JSON 配置导入站点" width="680px">
        <div style="margin-bottom: 12px">
          <div class="hint">粘贴完整 JSON 配置（包含 name/type/api_config 等字段），支持: </div>
          <div class="hint">1) 单个站点: <code>{ "name": "xxx", "type": "custom-api", "api_config": {...} }</code></div>
          <div class="hint">2) 多个站点: <code>[ { ... }, { ... } ]</code></div>
          <div class="hint">3) 导出格式: <code>{ "sites": [ ... ] }</code></div>
        </div>
        <el-input
          v-model="jsonImportText"
          type="textarea"
          :rows="18"
          placeholder='粘贴 JSON 配置...&#10;例如:&#10;{&#10;  "name": "示例站点",&#10;  "type": "custom-api",&#10;  "api_config": {&#10;    "login_url": "https://...",&#10;    "signin_url": "https://...",&#10;    ...&#10;  }&#10;}'
        />
        <template #footer>
          <el-button @click="jsonImportVisible = false">取消</el-button>
          <el-button type="primary" @click="handleJsonImport">导入</el-button>
        </template>
      </el-dialog>
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
.main-content {
  flex: 1;
  padding: 24px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  color: #1e3a5f;
}
.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}
.category-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}
.tab {
  padding: 8px 16px;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #606266;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  transition: all 0.2s;
}
.tab:hover {
  color: #1e3a5f;
}
.tab.active {
  background: #1e3a5f;
  color: white;
}
.content-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  margin-bottom: 16px;
}
.card-title {
  margin: 0;
  font-size: 18px;
  color: #1e3a5f;
  font-weight: 600;
}
.card-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
}
.hint {
  font-size: 12px;
  color: #909399;
}
.test-result {
  margin-bottom: 16px;
}
.result-msg {
  margin-top: 6px;
  font-size: 13px;
  word-break: break-all;
}
code {
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 12px;
  font-family: monospace;
}
.site-name-cell {
  display: flex;
  flex-direction: column;
}
.site-name-main {
  font-weight: 600;
  color: #303133;
}
.site-name-sub {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}
.empty-state {
  text-align: center;
  padding: 40px 20px;
}
.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}
.empty-text {
  color: #909399;
  font-size: 14px;
}

/* 分类卡片图标/颜色 */
.category-icon {
  font-size: 20px;
  display: inline-block;
  line-height: 1;
}
.color-chip {
  display: inline-block;
  width: 20px;
  height: 20px;
  border-radius: 4px;
  vertical-align: middle;
  border: 1px solid #ddd;
}

/* 按分类分组的站点标题行 */
.site-group-inline {
  margin-bottom: 16px;
}
.site-group-inline:last-child {
  margin-bottom: 0;
}
.site-group-header-inline {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: linear-gradient(90deg, #f0f5fb, #ffffff);
  border-left: 4px solid #1e3a5f;
  border-radius: 6px;
  margin-bottom: 8px;
}
.category-icon-inline {
  font-size: 18px;
  line-height: 1;
}
.category-name-inline {
  font-weight: 600;
  font-size: 15px;
}
.category-count-inline {
  color: #909399;
  font-size: 13px;
  margin-left: auto;
}

/* AI 配置生成器 */
.probe-form {
  margin-bottom: 8px;
}
.probe-result-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #eee;
}
.probe-code-block {
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 16px;
  max-height: 400px;
  overflow: auto;
  font-size: 13px;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
}
</style>
