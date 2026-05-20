const app = getApp()
const { isPlaceholderUrl } = require('../../config/index')

function appendQuery(url, params) {
  const query = Object.keys(params)
    .filter((key) => params[key])
    .map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
    .join('&')

  if (!query) return url
  return `${url}${url.includes('?') ? '&' : '?'}${query}`
}

Page({
  data: {
    webviewUrl: '',
    configError: '',
  },

  onLoad(options) {
    if (!app.globalData.webviewUrl || isPlaceholderUrl(app.globalData.webviewUrl)) {
      this.setData({ configError: 'Web 域名未配置，请更新 config/index.js' })
      wx.setNavigationBarTitle({ title: '配置未完成' })
      return
    }

    const route = options.route ? decodeURIComponent(options.route) : app.globalData.defaultRoute
    const title = options.title ? decodeURIComponent(options.title) : ''
    const normalizedRoute = route.startsWith('/') ? route : `/${route}`
    const finalUrl = appendQuery(`${app.globalData.webviewUrl}${normalizedRoute}`, {
      session_id: wx.getStorageSync('session_id'),
      family_id: wx.getStorageSync('family_id'),
      member_name: wx.getStorageSync('member_name'),
      family_name: wx.getStorageSync('family_name'),
    })

    this.setData({
      webviewUrl: finalUrl,
    })

    if (title) {
      wx.setNavigationBarTitle({ title })
    }
  },
})
