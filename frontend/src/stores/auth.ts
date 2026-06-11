import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface User {
  id: number
  email: string
  is_active: boolean
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<User | null>(null)

  const setAuth = (newToken: string, newUser: User) => {
    localStorage.setItem('token', newToken)
    token.value = newToken
    user.value = newUser
  }

  const logout = () => {
    localStorage.removeItem('token')
    token.value = null
    user.value = null
  }

  const isAuthenticated = computed(() => !!token.value)

  return {
    token,
    user,
    setAuth,
    logout,
    isAuthenticated
  }
})
