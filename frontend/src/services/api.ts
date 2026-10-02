import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || ''

export const api = axios.create({ baseURL: API_BASE })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('access_token')
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export async function login(email: string, password: string) {
  const params = new URLSearchParams()
  params.append('username', email)
  params.append('password', password)
  const res = await api.post('/auth/login', params.toString(), {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return res.data
}

export async function register(email: string, password: string, role: string) {
  return api.post('/auth/register', { email, password, role })
}

export async function getMe() {
  return api.get('/auth/me')
}
