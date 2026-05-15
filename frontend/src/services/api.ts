import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 聊天相关
export const chatAPI = {
  sendMessage: (message: string, userId?: string, sessionId?: string) =>
    api.post('/chat', { message, user_id: userId, session_id: sessionId }),
  listSessions: (userId: string, limit: number = 50) =>
    api.get(`/chat/sessions/${userId}`, { params: { limit } }),
  createSession: (userId: string, title?: string) =>
    api.post('/chat/sessions', { user_id: userId, title }),
  updateSession: (userId: string, sessionId: string, title: string) =>
    api.put(`/chat/sessions/${userId}/${sessionId}`, { title }),
  archiveSession: (userId: string, sessionId: string) =>
    api.delete(`/chat/sessions/${userId}/${sessionId}`),
  getHistory: (userId: string, sessionId: string, limit: number = 100) =>
    api.get(`/chat/history/${userId}`, { params: { session_id: sessionId, limit } }),
}

// 成员管理
export const membersAPI = {
  getAll: () => api.get('/members'),
  add: (data: any) => {
    const sessionId = localStorage.getItem('session_id')
    return api.post('/members', data, {
      params: sessionId ? { session_id: sessionId } : {}
    })
  },
  remove: (name: string) => api.delete(`/members/${name}`),
}

// 日程管理
export const scheduleAPI = {
  getAll: () => api.get('/reminders'),
  add: (date: string, event: string) => api.post('/reminders', { date, event }),
}

// 购物清单
export const shoppingAPI = {
  getAll: () => api.get('/shopping'),
  add: (data: any) => api.post('/shopping', data),
  remove: (name: string) => api.delete(`/shopping/${name}`),
  getStats: () => api.get('/shopping/stats'),
}

// 照片记忆
export const photosAPI = {
  getAll: (query?: string) => api.get('/photos', { params: { query } }),
  upload: (formData: FormData) => 
    api.post('/photos/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
}

// 智能家居
export const smartHomeAPI = {
  executeCommand: (command: string) => api.post('/smarthome/command', { command }),
  getDevices: (type?: string) => api.get('/smarthome/devices', { params: { device_type: type } }),
}

// MCP协议
export const mcpAPI = {
  listTools: () => api.get('/mcp/tools'),
  callTool: (toolName: string, args: any) => api.post('/mcp/call', { tool_name: toolName, arguments: args }),
}

// 统计信息
export const statsAPI = {
  getStats: () => api.get('/stats'),
}

// 知识库
export const knowledgeAPI = {
  search: (query: string, category?: string, limit?: number) => 
    api.get('/knowledge/search', { params: { query, category, limit } }),
  add: (data: { title: string; content: string; category?: string; tags?: string[] }) => 
    api.post('/knowledge/add', data),
  list: (category?: string, limit?: number) => 
    api.get('/knowledge/list', { params: { category, limit } }),
  categories: () => api.get('/knowledge/categories'),
  getDetail: (docId: string) => 
    api.get(`/knowledge/detail/${docId}`),
}

// 记忆管理
export const memoryAPI = {
  list: (params?: { query?: string; memory_type?: string; limit?: number }) =>
    api.get('/memory', { params }),
  stats: () => api.get('/memory/stats'),
  update: (id: string, data: { content: string; importance?: number; tags?: string[] }) =>
    api.put(`/memory/${id}`, data),
  remove: (id: string) => api.delete(`/memory/${id}`),
}

// 家庭财务
export const financeAPI = {
  getSummary: (year: number, month: number) =>
    api.get('/finance/summary', { params: { year, month } }),
  getTransactions: (params: {
    year: number; month: number;
    transaction_type?: string; category?: string;
    page?: number; page_size?: number;
  }) => api.get('/finance/transactions', { params }),
  add: (data: any) => api.post('/finance/transactions', data),
  update: (id: number, data: any) => api.put(`/finance/transactions/${id}`, data),
  remove: (id: number) => api.delete(`/finance/transactions/${id}`),
  getCategories: () => api.get('/finance/categories'),
  getTrend: (months: number = 6) => api.get('/finance/trend', { params: { months } }),
}

export default api
