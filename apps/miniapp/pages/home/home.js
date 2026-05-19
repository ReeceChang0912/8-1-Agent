const shortcuts = [
  { title: '主站', route: '/', desc: '打开 Web 总入口' },
  { title: '会话', route: '/chat', desc: '进入智能对话' },
  { title: '财务', route: '/finance', desc: '查看家庭收支' },
  { title: '模块', route: '/modules', desc: '管理备婚/住房/健康/保险/证件/车辆/健身' },
  { title: '备婚', route: '/modules/wedding', desc: '看婚礼筹备进度' },
  { title: '住房', route: '/modules/housing', desc: '看房租房贷和报修' },
  { title: '健康', route: '/modules/health', desc: '看体检和用药' },
  { title: '旅行', route: '/modules/travel', desc: '看行程预算和打包' },
  { title: '保险', route: '/modules/insurance', desc: '看保单和理赔' },
  { title: '证件', route: '/modules/documents', desc: '看证件到期提醒' },
  { title: '车辆', route: '/modules/vehicle', desc: '看保养和费用' },
  { title: '健身', route: '/modules/fitness', desc: '看训练和体重' },
]

const RECENT_KEY = 'family_management_recent_routes'

Page({
  data: {
    shortcuts,
    recentItems: [],
  },

  onLoad() {
    this.loadRecentItems()
  },

  loadRecentItems() {
    const recentItems = wx.getStorageSync(RECENT_KEY) || []
    this.setData({ recentItems: recentItems.slice(0, 4) })
  },

  recordRecentItem(route, title) {
    const recentItems = wx.getStorageSync(RECENT_KEY) || []
    const nextItems = [
      { route, title, ts: Date.now() },
      ...recentItems.filter((item) => item.route !== route),
    ].slice(0, 4)
    wx.setStorageSync(RECENT_KEY, nextItems)
    this.setData({ recentItems: nextItems })
  },

  goWebView(e) {
    const route = e.currentTarget.dataset.route || '/'
    const title = e.currentTarget.dataset.title || '家庭管理'
    this.recordRecentItem(route, title)
    wx.navigateTo({
      url: `/pages/webview/webview?route=${encodeURIComponent(route)}&title=${encodeURIComponent(title)}`,
    })
  },
})
