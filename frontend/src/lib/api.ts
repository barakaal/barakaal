import axios from 'axios'
import Cookies from 'js-cookie'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = Cookies.get('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      Cookies.remove('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', new URLSearchParams({ username: email, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }),
  me: () => api.get('/auth/me'),
}

// Dashboard
export const dashboardApi = {
  getCEOStats: () => api.get('/dashboard/ceo'),
}

// Agents
export const agentsApi = {
  list: (params?: Record<string, unknown>) => api.get('/agents/', { params }),
  get: (id: number) => api.get(`/agents/${id}`),
  create: (data: Record<string, unknown>) => api.post('/agents/', data),
  update: (id: number, data: Record<string, unknown>) => api.put(`/agents/${id}`, data),
  runTask: (id: number, task: Record<string, unknown>) => api.post(`/agents/${id}/run-task`, task),
  getTasks: (id: number) => api.get(`/agents/${id}/tasks`),
  getDecisions: (id: number) => api.get(`/agents/${id}/decisions`),
  allTasks: (params?: Record<string, unknown>) => api.get('/agents/tasks/', { params }),
  allDecisions: (params?: Record<string, unknown>) => api.get('/agents/decisions/', { params }),
}

// Products
export const productsApi = {
  list: (params?: Record<string, unknown>) => api.get('/products/', { params }),
  get: (id: number) => api.get(`/products/${id}`),
  create: (data: Record<string, unknown>) => api.post('/products/', data),
  update: (id: number, data: Record<string, unknown>) => api.put(`/products/${id}`, data),
  score: (id: number) => api.post(`/products/${id}/score`),
  importCSV: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post('/products/import-csv', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
}

// Suppliers
export const suppliersApi = {
  list: (params?: Record<string, unknown>) => api.get('/suppliers/', { params }),
  get: (id: number) => api.get(`/suppliers/${id}`),
  create: (data: Record<string, unknown>) => api.post('/suppliers/', data),
}

// Orders
export const ordersApi = {
  list: (params?: Record<string, unknown>) => api.get('/orders/', { params }),
  get: (id: number) => api.get(`/orders/${id}`),
  updateStatus: (id: number, data: Record<string, unknown>) => api.put(`/orders/${id}/status`, data),
}

// Approvals
export const approvalsApi = {
  list: (params?: Record<string, unknown>) => api.get('/approvals/', { params }),
  get: (id: number) => api.get(`/approvals/${id}`),
  review: (id: number, data: { status: string; review_notes?: string }) =>
    api.post(`/approvals/${id}/review`, data),
  stats: () => api.get('/approvals/stats'),
}

// Finance
export const financeApi = {
  reports: () => api.get('/finance/reports/'),
  summary: () => api.get('/finance/summary'),
}

// Audit
export const auditApi = {
  list: (params?: Record<string, unknown>) => api.get('/audit/', { params }),
}

// Departments
export const departmentsApi = {
  list: () => api.get('/departments/'),
}

// Reports
export const reportsApi = {
  weekly: () => api.get('/reports/weekly'),
  agentActivity: () => api.get('/reports/agents/activity'),
  triggerWeekly: () => api.post('/reports/weekly/trigger'),
}

// Connectors
export const connectorsApi = {
  list: () => api.get('/connectors/'),
  test: (id: number) => api.post(`/connectors/${id}/test`),
  sync: (id: number) => api.post(`/connectors/${id}/sync`),
}
