const app = getApp()

Page({
  data: {
    webviewUrl: '',
  },

  onLoad(options) {
    const route = options.route ? decodeURIComponent(options.route) : app.globalData.defaultRoute
    const title = options.title ? decodeURIComponent(options.title) : ''
    const normalizedRoute = route.startsWith('/') ? route : `/${route}`
    const finalUrl = `${app.globalData.webviewUrl}${normalizedRoute}`

    this.setData({
      webviewUrl: finalUrl,
    })

    if (title) {
      wx.setNavigationBarTitle({ title })
    }
  },
})
