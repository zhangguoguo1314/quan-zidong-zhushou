import axios from 'axios'
import router from '@/router'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 30000,
})

apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 标记是否正在处理 401 跳转，防止多个并发 401 重复触发
let isRedirecting = false

apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      if (!isRedirecting) {
        isRedirecting = true
        // 用 router.push 替代 window.location.href，避免页面硬刷新
        router.push({ name: 'Login' }).finally(() => {
          isRedirecting = false
        })
      }
      // 返回一个已 reject 的 promise，但不再让错误冒泡到页面组件
      return new Promise(() => {})
    }
    return Promise.reject(error)
  }
)

// ============= 分类管理 API =============
const categories = {
  list: () => apiClient.get('/sites/categories'),
  create: (data: any) => apiClient.post('/sites/categories', data),
  update: (id: number | string, data: any) => apiClient.put(`/sites/categories/${id}`, data),
  delete: (id: number | string) => apiClient.delete(`/sites/categories/${id}`),
}

// ============= 分组站点 API =============
const sitesGrouped = {
  list: () => apiClient.get('/sites/grouped'),
}

// 兼容之前的 api.get / api.post 用法
const api: any = Object.assign(
  {
    get: (url: string, ...args: any[]) => apiClient.get(url, ...args),
    post: (url: string, ...args: any[]) => apiClient.post(url, ...args),
    put: (url: string, ...args: any[]) => apiClient.put(url, ...args),
    delete: (url: string, ...args: any[]) => apiClient.delete(url, ...args),
    patch: (url: string, ...args: any[]) => apiClient.patch(url, ...args),
  },
  {
    apiClient,
    getSitesCategories: () => apiClient.get('/sites/categories'),
    createSiteCategory: (data: any) => apiClient.post('/sites/categories', data),
    updateSiteCategory: (id: number | string, data: any) => apiClient.put(`/sites/categories/${id}`, data),
    deleteSiteCategory: (id: number | string) => apiClient.delete(`/sites/categories/${id}`),
    getSitesGrouped: () => apiClient.get('/sites/grouped'),
    categories,
    sitesGrouped,
  }
)

export default api
