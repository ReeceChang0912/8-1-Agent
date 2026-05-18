const app = getApp()

Page({
  data: {
    loading: true,
    modules: [],
    readyCount: 0,
    plannedCount: 0,
  },

  onLoad() {
    this.loadModules()
  },

  loadModules() {
    const baseUrl = app.globalData.apiBaseUrl
    wx.request({
      url: `${baseUrl}/api/modules`,
      method: 'GET',
      success: (res) => {
        this.setData({
          modules: res.data.items || [],
          readyCount: res.data.ready_count || 0,
          plannedCount: res.data.planned_count || 0,
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
      const route = encodeURIComponent(module.web_route)
      wx.navigateTo({ url: `/pages/webview/webview?route=${route}&title=${encodeURIComponent(module.title || '')}` })
      return
    }
    wx.showToast({ title: '模块还在规划中', icon: 'none' })
  },
})
