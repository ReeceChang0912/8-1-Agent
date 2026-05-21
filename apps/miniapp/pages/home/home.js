const { request } = require('../../utils/request')

const featureGroups = [
  {
    title: '高频协作',
    note: '聊天、任务、日程、购物、家务',
    items: [
      { title: '智能对话', route: '/chat', desc: '一句话操作所有模块', accent: 'teal' },
      { title: '家庭成员', route: '/members', desc: '邀请、角色和分工', accent: 'blue' },
      { title: '家庭任务', route: '__native_tasks__', desc: '谁负责、谁完成', accent: 'red' },
      { title: '日程管理', route: '/schedule', desc: '提醒、空闲时间、推荐', accent: 'amber' },
      { title: '购物清单', route: '__native_shopping__', desc: '库存、常买、补货', accent: 'green' },
      { title: '家务分工', route: '/modules/chores', desc: '轮值、打卡、积分', accent: 'slate' },
      { title: '消息通知', route: '/notifications', desc: '任务和提醒通知', accent: 'blue' },
    ],
  },
  {
    title: '家庭记忆',
    note: '资料、照片、知识沉淀',
    items: [
      { title: '照片记忆', route: '/photos', desc: '上传、识别和检索', accent: 'pink' },
      { title: '知识库', route: '/knowledge', desc: '家庭资料和问答', accent: 'violet' },
      { title: '记忆管理', route: '/memory', desc: '偏好、事实、归档', accent: 'cyan' },
      { title: '证件管理', route: '/modules/documents', desc: '证件到期提醒', accent: 'amber' },
      { title: '健康管理', route: '/modules/health', desc: '体检、用药、复诊', accent: 'green' },
      { title: '保险管理', route: '/modules/insurance', desc: '保单、理赔、续保', accent: 'blue' },
    ],
  },
  {
    title: '生活模块',
    note: '新婚、车辆、住房、财务、旅行',
    items: [
      { title: '家庭财务', route: '/finance', desc: '收支、预算、趋势', accent: 'green' },
      { title: '备婚管理', route: '/modules/wedding', desc: '预算、供应商、待办', accent: 'pink' },
      { title: '车辆管理', route: '/modules/vehicle', desc: '保养、车险、费用', accent: 'slate' },
      { title: '健身管理', route: '/modules/fitness', desc: '训练、体重、饮食', accent: 'red' },
      { title: '住房管理', route: '/modules/housing', desc: '房租、物业、报修', accent: 'teal' },
      { title: '旅行管理', route: '/modules/travel', desc: '行程、预订、打包', accent: 'blue' },
    ],
  },
  {
    title: '系统能力',
    note: 'Web 同步能力',
    items: [
      { title: '工作台', route: '/', desc: '天气、新闻和家庭概览', accent: 'teal' },
      { title: '模块中心', route: '/modules', desc: '查看全部路线图', accent: 'blue' },
      { title: '技能中心', route: '/skills', desc: 'AI 专业技能', accent: 'violet' },
      { title: '智能家居', route: '/smarthome', desc: 'Home Assistant 控制', accent: 'green' },
      { title: 'MCP 协议', route: '/mcp', desc: '标准化工具调用', accent: 'slate' },
      { title: '统计信息', route: '/stats', desc: '家庭数据总览', accent: 'amber' },
    ],
  },
]

const aiActions = [
  { title: '分配任务', prompt: '/tasks 张三 买牛奶', desc: '指定谁负责' },
  { title: '加日程', prompt: '/remind 明天晚上7点家庭会议', desc: '一句话创建提醒' },
  { title: '加采购', prompt: '/shopping 牛奶和鸡蛋', desc: '同步购物清单' },
  { title: '记支出', prompt: '今天买菜花了 68', desc: '自动归类财务' },
  { title: '看家务', prompt: '/chores summary', desc: '查看分工进度' },
  { title: '查记忆', prompt: '/memory 车辆保养', desc: '检索家庭资料' },
  { title: '控家居', prompt: '/smarthome 打开客厅灯', desc: '自然语言控制' },
  { title: '全模块', prompt: '/modules', desc: '查看 Web 全功能' },
]

const RECENT_ROUTE_KEY = 'family_management_recent_routes'
const RECENT_CHAT_KEY = 'family_management_recent_chats'

Page({
  data: {
    featureGroups,
    aiActions,
    recentItems: [],
    recentChats: [],
    memberName: '',
    familyId: '',
    familyName: '',
    loadingChats: false,
    featureCount: featureGroups.reduce((sum, group) => sum + group.items.length, 0),
  },

  onLoad() {
    const memberName = wx.getStorageSync('member_name') || ''
    const familyId = wx.getStorageSync('family_id') || ''
    const familyName = wx.getStorageSync('family_name') || ''
    this.setData({ memberName, familyId, familyName })
    if (!memberName || !familyId) {
      wx.redirectTo({ url: '/pages/auth/auth' })
      return
    }
    this.loadRecentItems()
    this.loadRecentChats()
  },

  onShow() {
    this.loadRecentItems()
    this.loadRecentChats()
  },

  loadRecentItems() {
    const recentItems = wx.getStorageSync(RECENT_ROUTE_KEY) || []
    this.setData({ recentItems: recentItems.slice(0, 4) })
  },

  loadRecentChats() {
    const memberName = this.data.memberName
    const familyId = this.data.familyId
    if (!memberName) {
      const cachedChats = wx.getStorageSync(RECENT_CHAT_KEY) || []
      this.setData({ recentChats: cachedChats.slice(0, 4) })
      return
    }

    this.setData({ loadingChats: true })
    request({
      path: `/api/chat/sessions/${encodeURIComponent(memberName)}`,
      method: 'GET',
      data: {
        limit: 4,
        family_id: familyId,
      },
    })
      .then((data) => {
        const sessions = (data && data.sessions) || []
        const nextChats = sessions.slice(0, 4).map((item) => ({
          session_id: item.session_id,
          title: item.title || '新对话',
          last_message: item.last_message || '暂无消息',
          updated_at: item.updated_at || item.created_at || '',
          message_count: item.message_count || 0,
        }))
        wx.setStorageSync(RECENT_CHAT_KEY, nextChats)
        this.setData({ recentChats: nextChats })
      })
      .catch(() => {
        const cachedChats = wx.getStorageSync(RECENT_CHAT_KEY) || []
        this.setData({ recentChats: cachedChats.slice(0, 4) })
      })
      .then(() => {
        this.setData({ loadingChats: false })
      })
  },

  recordRecentItem(route, title) {
    const recentItems = wx.getStorageSync(RECENT_ROUTE_KEY) || []
    const nextItems = [
      { route, title, ts: Date.now() },
      ...recentItems.filter((item) => item.route !== route),
    ].slice(0, 4)
    wx.setStorageSync(RECENT_ROUTE_KEY, nextItems)
    this.setData({ recentItems: nextItems })
  },

  recordRecentChat(sessionId, title) {
    const recentChats = wx.getStorageSync(RECENT_CHAT_KEY) || []
    const nextChats = [
      { sessionId, title, ts: Date.now() },
      ...recentChats.filter((item) => item.sessionId !== sessionId),
    ].slice(0, 4)
    wx.setStorageSync(RECENT_CHAT_KEY, nextChats)
    return nextChats
  },

  openWeb(route, title) {
    this.recordRecentItem(route, title)
    wx.navigateTo({
      url: `/pages/webview/webview?route=${encodeURIComponent(route)}&title=${encodeURIComponent(title)}`,
    })
  },

  openChatWithPrompt(prompt, title) {
    const route = `/chat?prompt=${encodeURIComponent(prompt)}`
    this.recordRecentItem('/chat', title || '智能对话')
    wx.navigateTo({
      url: `/pages/webview/webview?route=${encodeURIComponent(route)}&title=${encodeURIComponent(title || '智能对话')}`,
    })
  },

  openChatSession(e) {
    const sessionId = e.currentTarget.dataset.sessionid
    const title = e.currentTarget.dataset.title || '智能对话'
    if (!sessionId) return
    this.recordRecentChat(sessionId, title)
    this.recordRecentItem('/chat', '智能对话')
    wx.navigateTo({
      url: `/pages/webview/webview?route=${encodeURIComponent(`/chat?session=${sessionId}`)}&title=${encodeURIComponent(title)}`,
    })
  },

  startNewChat() {
    this.openWeb('/chat', '智能对话')
  },

  goWebView(e) {
    const route = e.currentTarget.dataset.route || '/'
    const title = e.currentTarget.dataset.title || '家庭管理'
    if (route === '__native_tasks__') {
      wx.navigateTo({ url: '/pages/tasks/tasks' })
      return
    }
    if (route === '__native_shopping__') {
      wx.navigateTo({ url: '/pages/shopping/shopping' })
      return
    }
    this.openWeb(route, title)
  },

  goAiAction(e) {
    const prompt = e.currentTarget.dataset.prompt || ''
    const title = e.currentTarget.dataset.title || '智能对话'
    if (!prompt) return
    this.openChatWithPrompt(prompt, title)
  },
})
