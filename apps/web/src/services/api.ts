import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 聊天相关
export const chatAPI = {
  sendMessage: (message: string, userId?: string, sessionId?: string, familyId?: string) =>
    api.post('/chat', { message, user_id: userId, session_id: sessionId, family_id: familyId }),
  listSessions: (userId: string, limit: number = 50, familyId?: string) =>
    api.get(`/chat/sessions/${userId}`, { params: { limit, family_id: familyId } }),
  createSession: (userId: string, title?: string, familyId?: string) =>
    api.post('/chat/sessions', { user_id: userId, title, family_id: familyId }),
  updateSession: (userId: string, sessionId: string, title: string, familyId?: string) =>
    api.put(`/chat/sessions/${userId}/${sessionId}`, { title }, { params: { family_id: familyId } }),
  archiveSession: (userId: string, sessionId: string, familyId?: string) =>
    api.delete(`/chat/sessions/${userId}/${sessionId}`, { params: { family_id: familyId } }),
  getHistory: (userId: string, sessionId: string, limit: number = 100, familyId?: string) =>
    api.get(`/chat/history/${userId}`, { params: { session_id: sessionId, limit, family_id: familyId } }),
  getContext: (userId: string, familyId?: string) =>
    api.get(`/chat/context/${userId}`, { params: { family_id: familyId } }),
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
  getAll: (familyId?: string) => api.get('/reminders', { params: { family_id: familyId } }),
  add: (date: string, event: string, familyId?: string, member?: string) =>
    api.post('/reminders', { date, event, family_id: familyId, member }),
  remove: (id: number, familyId?: string) => api.delete(`/reminders/${id}`, { params: { family_id: familyId } }),
  getRecommendations: (memberName: string, date?: string) =>
    api.get(`/recommendations/${memberName}`, { params: { date } }),
  getFreeTimes: (memberName: string, date?: string) =>
    api.get(`/free-times/${memberName}`, { params: { date } }),
}

// 购物清单
export const shoppingAPI = {
  getAll: (familyId?: string) => api.get('/shopping', { params: { family_id: familyId } }),
  add: (data: any, familyId?: string) => api.post('/shopping', { ...data, family_id: familyId }),
  update: (id: number, data: any, familyId?: string) =>
    api.put(`/shopping/${id}`, data, { params: { family_id: familyId } }),
  toggle: (id: number, familyId?: string) =>
    api.post(`/shopping/${id}/toggle`, null, { params: { family_id: familyId } }),
  remove: (name: string, familyId?: string) => api.delete(`/shopping/${name}`, { params: { family_id: familyId } }),
  getStats: (familyId?: string) => api.get('/shopping/stats', { params: { family_id: familyId } }),
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

// 平台模块
export const modulesAPI = {
  list: () => api.get('/modules'),
}

export const lifeModulesAPI = {
  wedding: {
    list: (familyId?: string) => api.get('/modules/wedding', { params: { family_id: familyId } }),
    stats: (familyId?: string) => api.get('/modules/wedding/stats', { params: { family_id: familyId } }),
    add: (data: any) => api.post('/modules/wedding', data),
    update: (id: number, data: any) => api.put(`/modules/wedding/${id}`, data),
    remove: (id: number, familyId?: string) => api.delete(`/modules/wedding/${id}`, { params: { family_id: familyId } }),
  },
  insurance: {
    list: (familyId?: string) => api.get('/modules/insurance', { params: { family_id: familyId } }),
    stats: (familyId?: string) => api.get('/modules/insurance/stats', { params: { family_id: familyId } }),
    add: (data: any) => api.post('/modules/insurance', data),
    update: (id: number, data: any) => api.put(`/modules/insurance/${id}`, data),
    remove: (id: number, familyId?: string) => api.delete(`/modules/insurance/${id}`, { params: { family_id: familyId } }),
  },
  vehicle: {
    list: (familyId?: string) => api.get('/modules/vehicle', { params: { family_id: familyId } }),
    stats: (familyId?: string) => api.get('/modules/vehicle/stats', { params: { family_id: familyId } }),
    add: (data: any) => api.post('/modules/vehicle', data),
    update: (id: number, data: any) => api.put(`/modules/vehicle/${id}`, data),
    remove: (id: number, familyId?: string) => api.delete(`/modules/vehicle/${id}`, { params: { family_id: familyId } }),
  },
  fitness: {
    list: (familyId?: string) => api.get('/modules/fitness', { params: { family_id: familyId } }),
    stats: (familyId?: string) => api.get('/modules/fitness/stats', { params: { family_id: familyId } }),
    add: (data: any) => api.post('/modules/fitness', data),
    update: (id: number, data: any) => api.put(`/modules/fitness/${id}`, data),
    remove: (id: number, familyId?: string) => api.delete(`/modules/fitness/${id}`, { params: { family_id: familyId } }),
  },
  documents: {
    list: (familyId?: string) => api.get('/modules/documents', { params: { family_id: familyId } }),
    stats: (familyId?: string) => api.get('/modules/documents/stats', { params: { family_id: familyId } }),
    add: (data: any) => api.post('/modules/documents', data),
    update: (id: number, data: any) => api.put(`/modules/documents/${id}`, data),
    remove: (id: number, familyId?: string) => api.delete(`/modules/documents/${id}`, { params: { family_id: familyId } }),
  },
  housing: {
    list: (familyId?: string) => api.get('/modules/housing', { params: { family_id: familyId } }),
    stats: (familyId?: string) => api.get('/modules/housing/stats', { params: { family_id: familyId } }),
    add: (data: any) => api.post('/modules/housing', data),
    update: (id: number, data: any) => api.put(`/modules/housing/${id}`, data),
    remove: (id: number, familyId?: string) => api.delete(`/modules/housing/${id}`, { params: { family_id: familyId } }),
  },
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
  list: (params?: { query?: string; memory_type?: string; limit?: number; user_id?: string; family_id?: string }) =>
    api.get('/memory', { params }),
  stats: () => api.get('/memory/stats'),
  update: (id: string, data: { content: string; importance?: number; tags?: string[] }, params?: { user_id?: string; family_id?: string }) =>
    api.put(`/memory/${id}`, data, { params }),
  remove: (id: string, params?: { user_id?: string; family_id?: string }) =>
    api.delete(`/memory/${id}`, { params }),
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
