const { request } = require('../../utils/request')
const RECENT_KEY = 'family_management_recent_routes'

const CATEGORY_LABELS = {
  core: '高频协作',
  life: '生活模块',
  memory: '家庭记忆',
  ai: 'AI 能力',
  integration: '系统联动',
  system: '系统能力',
}

const CATEGORY_NOTES = {
  core: '每天都会用到的家庭协作入口',
  life: '围绕居家、出行、健康和资产的长期管理',
  memory: '沉淀资料、照片和家庭知识',
  ai: '让助手能力可被管理和复用',
  integration: '连接外部设备和工具协议',
  system: '小程序与 Web 的通用入口',
}

const CATEGORY_ORDER = ['core', 'life', 'memory', 'ai', 'integration', 'system']

const ACCENTS = {
  core: 'teal',
  life: 'amber',
  memory: 'cyan',
  ai: 'violet',
  integration: 'green',
  system: 'blue',
}

const MODULE_COMMANDS = {
  workbench: '/stats',
  chat: '/help',
  members: '/members',
  tasks: '/tasks list',
  schedule: '/remind 明天晚上7点家庭会议',
  shopping: '/shopping summary',
  photos: '/photo',
  knowledge: '/knowledge 家庭资料',
  memory: '/memory 车辆保养',
  skills: '/skills',
  smarthome: '/smarthome 打开客厅灯',
  mcp: '/mcp',
  stats: '/stats',
  notifications: '/notifications',
  finance: '/finance summary',
  modules: '/modules',
  wedding: '/wedding summary',
  insurance: '/insurance list',
  vehicle: '/vehicle summary',
  fitness: '/fitness summary',
  documents: '/documents list',
  housing: '/housing summary',
  health: '/health summary',
  travel: '/travel summary',
  chores: '/chores summary',
}

function decorateModule(item) {
  const category = item.category || 'system'
  return {
    ...item,
    category_label: CATEGORY_LABELS[category] || category,
    category_note: CATEGORY_NOTES[category] || '家庭管理模块',
    accent: ACCENTS[category] || 'slate',
    status_text: item.status === 'ready' ? '已上线' : '规划中',
    route_label: item.web_route || '规划中',
    ai_prompt: MODULE_COMMANDS[item.id] || '/modules',
  }
}

function groupModules(modules) {
  const grouped = modules.reduce((acc, item) => {
    const category = item.category || 'system'
    if (!acc[category]) {
      acc[category] = {
        category,
        title: CATEGORY_LABELS[category] || category,
        note: CATEGORY_NOTES[category] || '家庭管理模块',
        items: [],
      }
    }
    acc[category].items.push(item)
    return acc
  }, {})

  return Object.keys(grouped)
    .sort((a, b) => {
      const ai = CATEGORY_ORDER.indexOf(a)
      const bi = CATEGORY_ORDER.indexOf(b)
      return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi)
    })
    .map((key) => grouped[key])
}

Page({
  data: {
    loading: true,
    modules: [],
    readyCount: 0,
    plannedCount: 0,
    moduleGroups: [],
    heroModules: [],
    readyModules: [],
    plannedModules: [],
  },

  onLoad() {
    wx.setNavigationBarTitle({ title: '模块中心' })
    const memberName = wx.getStorageSync('member_name') || ''
    const familyId = wx.getStorageSync('family_id') || ''
    if (!memberName || !familyId) {
      wx.redirectTo({ url: '/pages/auth/auth' })
      return
    }
    this.loadModules()
  },

  openWeb(route, title) {
    const recentItems = wx.getStorageSync(RECENT_KEY) || []
    const nextItems = [
      { route, title, ts: Date.now() },
      ...recentItems.filter((item) => item.route !== route),
    ].slice(0, 4)
    wx.setStorageSync(RECENT_KEY, nextItems)
    wx.navigateTo({
      url: `/pages/webview/webview?route=${encodeURIComponent(route)}&title=${encodeURIComponent(title)}`,
    })
  },

  openHome() {
    wx.redirectTo({ url: '/pages/home/home' })
  },

  loadModules() {
    request({
      path: '/api/modules',
      method: 'GET',
    })
      .then((data) => {
        const modules = (data.items || []).map(decorateModule)
        const readyModules = modules.filter((item) => item.status === 'ready')
        const plannedModules = modules.filter((item) => item.status !== 'ready')
        this.setData({
          modules,
          readyCount: data.ready_count || 0,
          plannedCount: data.planned_count || 0,
          readyModules,
          plannedModules,
          heroModules: readyModules.slice(0, 3),
          moduleGroups: groupModules(readyModules),
        })
      })
      .catch(() => {})
      .then(() => {
        this.setData({ loading: false })
        const homeHistory = wx.getStorageSync('family_management_recent_routes') || []
        if (homeHistory.length === 0) {
          wx.setStorageSync('family_management_recent_routes', [
            { route: '/modules', title: '模块中心', ts: Date.now() },
          ])
        }
      })
  },

  openModule(e) {
    const module = e.currentTarget.dataset.module
    if (!module) return
    if (module.id === 'tasks') {
      wx.navigateTo({ url: '/pages/tasks/tasks' })
      return
    }
    if (module.id === 'shopping') {
      wx.navigateTo({ url: '/pages/shopping/shopping' })
      return
    }
    if (module.status === 'ready' && module.web_route) {
      this.openWeb(module.web_route, module.title || '')
      return
    }
    wx.showToast({ title: '模块还在规划中', icon: 'none' })
  },

  openChatCommand(e) {
    const prompt = e.currentTarget.dataset.prompt || '/modules'
    const title = e.currentTarget.dataset.title || '智能对话'
    this.openWeb(`/chat?prompt=${encodeURIComponent(prompt)}`, `${title} Chat`)
  },
})
