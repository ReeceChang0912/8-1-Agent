const { isPlaceholderUrl } = require('../config/index')

function buildUrl(path) {
  const app = getApp()
  const baseUrl = app.globalData.apiBaseUrl || ''
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${baseUrl}${normalizedPath}`
}

function request(options) {
  const app = getApp()
  const baseUrl = app.globalData.apiBaseUrl || ''

  if (!baseUrl || isPlaceholderUrl(baseUrl)) {
    const message = 'API 域名未配置'
    console.warn('[miniapp config] apiBaseUrl is missing or still a placeholder. Update apps/miniapp/config/index.js.', {
      env: app.globalData.env,
      apiBaseUrl: baseUrl,
    })
    wx.showToast({ title: message, icon: 'none' })
    return Promise.reject(new Error('API 域名未配置：请更新 apps/miniapp/config/index.js'))
  }

  return new Promise((resolve, reject) => {
    wx.request({
      ...options,
      url: options.url || buildUrl(options.path),
      header: {
        'content-type': 'application/json',
        ...(options.header || {}),
      },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data || {})
          return
        }
        const message = (res.data && (res.data.message || res.data.detail)) || `请求失败 ${res.statusCode}`
        wx.showToast({ title: message, icon: 'none' })
        reject(new Error(message))
      },
      fail: (err) => {
        const message = err && err.errMsg ? err.errMsg : '网络请求失败'
        wx.showToast({ title: message, icon: 'none' })
        reject(err)
      },
      complete: options.complete,
    })
  })
}

module.exports = {
  request,
}
