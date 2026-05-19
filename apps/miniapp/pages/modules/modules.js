const app = getApp()

Page({
  data: {
    loading: true,
    modules: [],
    readyCount: 0,
    plannedCount: 0,
    readyModules: [],
    plannedModules: [],
  },

  onLoad() {
    wx.setNavigationBarTitle({ title: '模块中心' })
    this.loadModules()
  },

  openWeb(route, title) {
    wx.navigateTo({
      url: `/pages/webview/webview?route=${encodeURIComponent(route)}&title=${encodeURIComponent(title)}`,
    })
  },

  openHome() {
    this.openWeb('/', '家庭管理')
  },

  loadModules() {
    const baseUrl = app.globalData.apiBaseUrl
    wx.request({
      url: `${baseUrl}/api/modules`,
      method: 'GET',
      success: (res) => {
        const modules = res.data.items || []
        this.setData({
          modules,
          readyCount: res.data.ready_count || 0,
          plannedCount: res.data.planned_count || 0,
          readyModules: modules.filter((item) => item.status === 'ready'),
          plannedModules: modules.filter((item) => item.status !== 'ready'),
        })
      },
      fail: () => {
        wx.showToast({ title: '模块加载失败', icon: 'none' })
      },
      complete: () => {
        this.setData({ loading: false })
      },
    })
  },

  openModule(e) {
    const module = e.currentTarget.dataset.module
    if (!module) return
    if (module.status === 'ready' && module.web_route) {
      this.openWeb(module.web_route, module.title || '')
      return
    }
    wx.showToast({ title: '模块还在规划中', icon: 'none' })
  },
})
