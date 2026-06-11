import { defineStore } from 'pinia'
import { ref } from 'vue'

interface Site {
  id: number
  name: string
  type: string
  url: string
  created_at: string
}

interface Account {
  id: number
  site_id: number
  user_id: number
  username: string
  password?: string
  token?: string
  cookie?: string
  status: string
  created_at: string
}

interface Task {
  id: number
  account_id: number
  cron: string
  last_run?: string
  status: string
  created_at: string
}

interface Log {
  id: number
  task_id: number
  result?: string
  status: string
  created_at: string
}

export const useAppStore = defineStore('app', () => {
  const sites = ref<Site[]>([])
  const accounts = ref<Account[]>([])
  const tasks = ref<Task[]>([])
  const logs = ref<Log[]>([])

  const setSites = (data: Site[]) => { sites.value = data }
  const setAccounts = (data: Account[]) => { accounts.value = data }
  const setTasks = (data: Task[]) => { tasks.value = data }
  const setLogs = (data: Log[]) => { logs.value = data }

  const addSite = (site: Site) => { sites.value.push(site) }
  const updateSite = (site: Site) => {
    const index = sites.value.findIndex(s => s.id === site.id)
    if (index !== -1) sites.value[index] = site
  }
  const removeSite = (id: number) => {
    sites.value = sites.value.filter(s => s.id !== id)
  }

  const addAccount = (account: Account) => { accounts.value.push(account) }
  const updateAccount = (account: Account) => {
    const index = accounts.value.findIndex(a => a.id === account.id)
    if (index !== -1) accounts.value[index] = account
  }
  const removeAccount = (id: number) => {
    accounts.value = accounts.value.filter(a => a.id !== id)
  }

  const addTask = (task: Task) => { tasks.value.push(task) }
  const updateTask = (task: Task) => {
    const index = tasks.value.findIndex(t => t.id === task.id)
    if (index !== -1) tasks.value[index] = task
  }
  const removeTask = (id: number) => {
    tasks.value = tasks.value.filter(t => t.id !== id)
  }

  const addLog = (log: Log) => { logs.value.unshift(log) }

  return {
    sites,
    accounts,
    tasks,
    logs,
    setSites,
    setAccounts,
    setTasks,
    setLogs,
    addSite,
    updateSite,
    removeSite,
    addAccount,
    updateAccount,
    removeAccount,
    addTask,
    updateTask,
    removeTask,
    addLog
  }
})
