import { ref } from 'vue'

export type Lang = 'zh' | 'en' | 'ja'

const messages: Record<Lang, Record<string, string>> = {
  zh: {
    // 侧边栏
    'nav.dashboard': '仪表盘',
    'nav.sites': '网站管理',
    'nav.accounts': '账号管理',
    'nav.tasks': '任务管理',
    'nav.logs': '签到日志',
    'nav.settings': '设置',
    'app.title': '全自动签到助手',
    // 登录
    'login.title': 'Account Auto-Sign',
    'login.subtitle': 'Sign in to your account',
    'login.email': '邮箱',
    'login.password': '密码',
    'login.submit': '登录',
    'login.register': '注册',
    'login.noAccount': '没有账号？',
    // 仪表盘
    'dashboard.title': '仪表盘',
    'dashboard.sites': '管理站点',
    'dashboard.accounts': '管理账号',
    'dashboard.tasks': '定时任务',
    'dashboard.successRate': '成功率',
    'dashboard.recentLogs': '最近签到记录',
    // 设置
    'settings.title': '设置',
    'settings.personalInfo': '个人信息',
    'settings.changePassword': '修改密码',
    'settings.emailNotify': '邮件通知',
    'settings.wechatNotify': '企业微信机器人通知',
    'settings.msgTemplate': '消息模板',
    'settings.statusReport': '定时状态报告',
    'settings.about': '关于系统',
    'settings.logout': '退出登录',
    // 通用
    'common.save': '保存',
    'common.cancel': '取消',
    'common.delete': '删除',
    'common.edit': '编辑',
    'common.add': '添加',
    'common.search': '搜索',
    'common.loading': '加载中...',
    'common.success': '操作成功',
    'common.failed': '操作失败',
  },
  en: {
    'nav.dashboard': 'Dashboard',
    'nav.sites': 'Sites',
    'nav.accounts': 'Accounts',
    'nav.tasks': 'Tasks',
    'nav.logs': 'Sign-in Logs',
    'nav.settings': 'Settings',
    'app.title': 'Auto Sign-in Assistant',
    'login.title': 'Account Auto-Sign',
    'login.subtitle': 'Sign in to your account',
    'login.email': 'Email',
    'login.password': 'Password',
    'login.submit': 'Sign In',
    'login.register': 'Register',
    'login.noAccount': "Don't have an account?",
    'dashboard.title': 'Dashboard',
    'dashboard.sites': 'Sites',
    'dashboard.accounts': 'Accounts',
    'dashboard.tasks': 'Tasks',
    'dashboard.successRate': 'Success Rate',
    'dashboard.recentLogs': 'Recent Sign-in Logs',
    'settings.title': 'Settings',
    'settings.personalInfo': 'Personal Info',
    'settings.changePassword': 'Change Password',
    'settings.emailNotify': 'Email Notification',
    'settings.wechatNotify': 'WeChat Bot Notification',
    'settings.msgTemplate': 'Message Templates',
    'settings.statusReport': 'Scheduled Status Report',
    'settings.about': 'About',
    'settings.logout': 'Logout',
    'common.save': 'Save',
    'common.cancel': 'Cancel',
    'common.delete': 'Delete',
    'common.edit': 'Edit',
    'common.add': 'Add',
    'common.search': 'Search',
    'common.loading': 'Loading...',
    'common.success': 'Success',
    'common.failed': 'Failed',
  },
  ja: {
    'nav.dashboard': 'ダッシュボード',
    'nav.sites': 'サイト管理',
    'nav.accounts': 'アカウント管理',
    'nav.tasks': 'タスク管理',
    'nav.logs': 'サインイン履歴',
    'nav.settings': '設定',
    'app.title': '自動サインインアシスタント',
    'login.title': 'Account Auto-Sign',
    'login.subtitle': 'アカウントにサインイン',
    'login.email': 'メールアドレス',
    'login.password': 'パスワード',
    'login.submit': 'ログイン',
    'login.register': '登録',
    'login.noAccount': 'アカウントをお持ちでないですか？',
    'dashboard.title': 'ダッシュボード',
    'dashboard.sites': 'サイト',
    'dashboard.accounts': 'アカウント',
    'dashboard.tasks': 'タスク',
    'dashboard.successRate': '成功率',
    'dashboard.recentLogs': '最近のサインイン履歴',
    'settings.title': '設定',
    'settings.personalInfo': '個人情報',
    'settings.changePassword': 'パスワード変更',
    'settings.emailNotify': 'メール通知',
    'settings.wechatNotify': 'WeChatボット通知',
    'settings.msgTemplate': 'メッセージテンプレート',
    'settings.statusReport': '定期ステータスレポート',
    'settings.about': 'について',
    'settings.logout': 'ログアウト',
    'common.save': '保存',
    'common.cancel': 'キャンセル',
    'common.delete': '削除',
    'common.edit': '編集',
    'common.add': '追加',
    'common.search': '検索',
    'common.loading': '読み込み中...',
    'common.success': '成功',
    'common.failed': '失敗',
  }
}

const currentLang = ref<Lang>((localStorage.getItem('lang') as Lang) || 'zh')

const setLang = (lang: Lang) => {
  currentLang.value = lang
  localStorage.setItem('lang', lang)
}

const t = (key: string): string => {
  return messages[currentLang.value]?.[key] || messages.zh[key] || key
}

export const useI18n = () => {
  return { currentLang, setLang, t, messages }
}

export type { Lang }
