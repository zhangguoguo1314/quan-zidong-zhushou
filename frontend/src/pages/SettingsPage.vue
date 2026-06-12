<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const loading = ref(false)
const emailLoading = ref(false)
const testEmailLoading = ref(false)
const wechatLoading = ref(false)
const testWechatLoading = ref(false)
const userInfo = ref<any>(null)

const settingsForm = ref({
  email_enabled: false,
  notify_on_success: false,
  notify_on_failure: true,
  smtp_host: '',
  smtp_port: 465,
  smtp_user: '',
  smtp_password: '',
  email_from: '',
  email_to: '',
  // 企业微信
  wechat_bot_enabled: false,
  wechat_bot_webhook: '',
  wechat_bot_notify_on_success: false,
  wechat_bot_notify_on_failure: true
})

const passwordForm = ref({
  current_password: '',
  new_password: '',
  confirm_password: ''
})

const fetchUser = async () => {
  try {
    const response = await api.get('/api/auth/me')
    userInfo.value = response.data
  } catch (e) {
    console.error(e)
  }
}

const fetchSettings = async () => {
  try {
    const response = await api.get('/api/settings')
    if (response.data) {
      const d = response.data
      settingsForm.value = {
        email_enabled: d.email_enabled || false,
        notify_on_success: d.notify_on_success || false,
        notify_on_failure: d.notify_on_failure !== false,
        smtp_host: d.smtp_host || '',
        smtp_port: d.smtp_port || 465,
        smtp_user: d.smtp_user || '',
        smtp_password: d.smtp_password || '',
        email_from: d.email_from || '',
        email_to: d.email_to || d.email || '',
        wechat_bot_enabled: d.wechat_bot_enabled || false,
        wechat_bot_webhook: d.wechat_bot_webhook || '',
        wechat_bot_notify_on_success: d.wechat_bot_notify_on_success || false,
        wechat_bot_notify_on_failure: d.wechat_bot_notify_on_failure !== false
      }
    }
  } catch (e) {
    console.error(e)
  }
}

const saveEmailSettings = async () => {
  if (settingsForm.value.email_enabled && (!settingsForm.value.smtp_host || !settingsForm.value.smtp_user || !settingsForm.value.smtp_password)) {
    ElMessage.warning('开启邮件通知需要填写 SMTP 主机、用户名和密码')
    return
  }
  emailLoading.value = true
  try {
    await api.put('/api/settings/email', {
      email_enabled: settingsForm.value.email_enabled,
      notify_on_success: settingsForm.value.notify_on_success,
      notify_on_failure: settingsForm.value.notify_on_failure,
      smtp_host: settingsForm.value.smtp_host,
      smtp_port: settingsForm.value.smtp_port,
      smtp_user: settingsForm.value.smtp_user,
      smtp_password: settingsForm.value.smtp_password,
      email_from: settingsForm.value.email_from
    })
    ElMessage.success('邮件设置保存成功')
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    emailLoading.value = false
  }
}

const testEmail = async () => {
  if (!settingsForm.value.smtp_host) {
    ElMessage.warning('请先填写 SMTP 配置')
    return
  }
  testEmailLoading.value = true
  try {
    const response = await api.post('/api/settings/test-email', {
      smtp_host: settingsForm.value.smtp_host,
      smtp_port: settingsForm.value.smtp_port,
      smtp_user: settingsForm.value.smtp_user,
      smtp_password: settingsForm.value.smtp_password,
      email_from: settingsForm.value.email_from
    })
    if (response.data.success) {
      ElMessage.success('测试邮件发送成功')
    } else {
      ElMessage.error('测试邮件发送失败')
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '测试邮件发送失败')
  } finally {
    testEmailLoading.value = false
  }
}

// ========== 企业微信机器人 ==========
const saveWechatSettings = async () => {
  if (settingsForm.value.wechat_bot_enabled && !settingsForm.value.wechat_bot_webhook) {
    ElMessage.warning('开启企业微信通知需要填写 webhook 地址')
    return
  }
  wechatLoading.value = true
  try {
    await api.put('/api/settings/wechat-bot', {
      wechat_bot_enabled: settingsForm.value.wechat_bot_enabled,
      wechat_bot_webhook: settingsForm.value.wechat_bot_webhook,
      wechat_bot_notify_on_success: settingsForm.value.wechat_bot_notify_on_success,
      wechat_bot_notify_on_failure: settingsForm.value.wechat_bot_notify_on_failure
    })
    ElMessage.success('企业微信设置保存成功')
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    wechatLoading.value = false
  }
}

const testWechatBot = async () => {
  if (!settingsForm.value.wechat_bot_webhook) {
    ElMessage.warning('请先填写 webhook 地址')
    return
  }
  testWechatLoading.value = true
  try {
    const response = await api.post('/api/settings/test-wechat-bot', {
      webhook_url: settingsForm.value.wechat_bot_webhook
    })
    if (response.data.success) {
      ElMessage.success('测试消息已发送，请查看企业微信群')
    } else {
      ElMessage.error('发送失败')
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '测试消息发送失败')
  } finally {
    testWechatLoading.value = false
  }
}

const changePassword = async () => {
  if (!passwordForm.value.current_password) {
    ElMessage.warning('请输入当前密码')
    return
  }
  if (passwordForm.value.new_password.length < 6) {
    ElMessage.warning('新密码至少 6 位')
    return
  }
  if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  loading.value = true
  try {
    await api.post('/api/settings/change-password', {
      old_password: passwordForm.value.current_password,
      new_password: passwordForm.value.new_password
    })
    ElMessage.success('密码修改成功')
    passwordForm.value = { current_password: '', new_password: '', confirm_password: '' }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '密码修改失败')
  } finally {
    loading.value = false
  }
}

const logout = () => {
  localStorage.removeItem('token')
  window.location.href = '/login'
}

onMounted(() => {
  fetchUser()
  fetchSettings()
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
        <router-link to="/tasks" class="nav-item">任务管理</router-link>
        <router-link to="/logs" class="nav-item">签到日志</router-link>
        <router-link to="/settings" class="nav-item active">设置</router-link>
      </nav>
    </aside>

    <main class="main-content">
      <header class="page-header">
        <h1>设置</h1>
        <el-button @click="logout">退出登录</el-button>
      </header>

      <!-- 用户信息 -->
      <div class="content-card">
        <h2 class="card-title">个人信息</h2>
        <div class="user-info-row">
          <span class="label">用户名:</span>
          <span class="value">{{ userInfo?.username || userInfo?.email }}</span>
        </div>
        <div class="user-info-row">
          <span class="label">邮箱:</span>
          <span class="value">{{ userInfo?.email || '未设置' }}</span>
        </div>
      </div>

      <!-- 修改密码 -->
      <div class="content-card">
        <h2 class="card-title">修改密码</h2>
        <el-form :model="passwordForm" label-width="120px" style="max-width: 500px">
          <el-form-item label="当前密码">
            <el-input v-model="passwordForm.current_password" type="password" show-password />
          </el-form-item>
          <el-form-item label="新密码">
            <el-input v-model="passwordForm.new_password" type="password" show-password />
          </el-form-item>
          <el-form-item label="确认新密码">
            <el-input v-model="passwordForm.confirm_password" type="password" show-password />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="loading" @click="changePassword">保存密码</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 邮件通知设置 -->
      <div class="content-card">
        <h2 class="card-title">邮件通知</h2>

        <el-alert v-if="!settingsForm.email_enabled" type="info" :closable="false" show-icon style="margin-bottom: 16px">
          <template #title>邮件通知当前已关闭，开启后将在签到失败时收到邮件提醒</template>
        </el-alert>

        <el-form :model="settingsForm" label-width="150px" style="max-width: 680px">
          <el-form-item label="开启邮件通知">
            <el-switch v-model="settingsForm.email_enabled" />
          </el-form-item>

          <el-form-item label="通知时机">
            <el-checkbox v-model="settingsForm.notify_on_success">签到成功时通知</el-checkbox>
            <el-checkbox v-model="settingsForm.notify_on_failure">签到失败时通知</el-checkbox>
          </el-form-item>

          <el-divider content-position="left">SMTP 配置</el-divider>

          <el-form-item label="SMTP 主机">
            <el-input v-model="settingsForm.smtp_host" placeholder="smtp.gmail.com 或 smtp.qq.com" />
          </el-form-item>
          <el-form-item label="SMTP 端口">
            <el-input v-model.number="settingsForm.smtp_port" placeholder="465 或 587" style="width: 200px" />
            <div class="hint" style="margin-left: 10px">QQ邮箱: 465, Gmail: 465, 网易: 465</div>
          </el-form-item>
          <el-form-item label="SMTP 用户名">
            <el-input v-model="settingsForm.smtp_user" placeholder="your-email@example.com" />
          </el-form-item>
          <el-form-item label="SMTP 密码/授权码">
            <el-input v-model="settingsForm.smtp_password" type="password" show-password placeholder="QQ邮箱需使用授权码" />
          </el-form-item>
          <el-form-item label="发件人显示">
            <el-input v-model="settingsForm.email_from" placeholder="your-email@example.com" />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" :loading="emailLoading" @click="saveEmailSettings">保存邮件设置</el-button>
            <el-button :loading="testEmailLoading" @click="testEmail">发送测试邮件</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 企业微信机器人通知 -->
      <div class="content-card">
        <h2 class="card-title">企业微信机器人通知</h2>

        <el-alert type="info" :closable="false" show-icon style="margin-bottom: 16px">
          <template #title>在企业微信群中添加机器人，获取 webhook 地址填入下方即可</template>
        </el-alert>

        <el-form :model="settingsForm" label-width="150px" style="max-width: 680px">
          <el-form-item label="开启机器人通知">
            <el-switch v-model="settingsForm.wechat_bot_enabled" />
          </el-form-item>

          <el-form-item label="通知时机">
            <el-checkbox v-model="settingsForm.wechat_bot_notify_on_success">签到成功时通知</el-checkbox>
            <el-checkbox v-model="settingsForm.wechat_bot_notify_on_failure">签到失败时通知</el-checkbox>
          </el-form-item>

          <el-form-item label="Webhook 地址">
            <el-input
              v-model="settingsForm.wechat_bot_webhook"
              type="textarea"
              :rows="2"
              placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxxxxx"
            />
            <div class="hint" style="margin-top: 4px">
              获取方式：企业微信群 → 群设置 → 添加群机器人 → 复制 webhook 地址
            </div>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" :loading="wechatLoading" @click="saveWechatSettings">保存机器人设置</el-button>
            <el-button :loading="testWechatLoading" @click="testWechatBot">发送测试消息</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 关于系统 -->
      <div class="content-card">
        <h2 class="card-title">关于系统</h2>
        <div class="info-grid">
          <div class="info-item">
            <div class="info-label">功能支持</div>
            <div class="info-value">
              <div>• 自定义 API 站点签到</div>
              <div>• JSON 配置导入/导出</div>
              <div>• 定时自动签到（Cron 表达式）</div>
              <div>• 邮件通知提醒</div>
              <div>• 企业微信机器人通知</div>
              <div>• 多站点、多账号管理</div>
            </div>
          </div>
          <div class="info-item">
            <div class="info-label">Cron 表达式说明</div>
            <div class="info-value">
              <div>格式: <code>分 时 日 月 星期</code></div>
              <div>每天 8:00 → <code>0 8 * * *</code></div>
              <div>每小时 → <code>0 * * * *</code></div>
              <div>每 5 分钟 → <code>*/5 * * * *</code></div>
              <div>每周一 9:00 → <code>0 9 * * 1</code></div>
            </div>
          </div>
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
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h1 { margin: 0; font-size: 28px; font-weight: 600; color: #1e3a5f; }
.content-card { background: white; border-radius: 12px; padding: 24px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06); }
.card-title { margin: 0 0 16px 0; font-size: 18px; color: #1e3a5f; padding-bottom: 8px; border-bottom: 1px solid #eee; }
.user-info-row { display: flex; padding: 8px 0; }
.label { color: #909399; min-width: 100px; }
.value { color: #303133; font-weight: 500; }
.hint { font-size: 12px; color: #909399; }
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.info-item { background: #f5f7fa; padding: 16px; border-radius: 8px; }
.info-label { font-weight: 600; color: #1e3a5f; margin-bottom: 8px; font-size: 14px; }
.info-value { font-size: 13px; color: #606266; line-height: 1.8; }
code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 12px; font-family: monospace; }
</style>
