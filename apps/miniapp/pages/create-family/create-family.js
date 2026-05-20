const { request } = require('../../utils/request')

Page({
  data: {
    loading: false,
    createFamilyName: '',
    createAdminName: '',
  },

  onLoad() {
    wx.setNavigationBarTitle({ title: '创建家庭' })
  },

  setField(e) {
    const { field } = e.currentTarget.dataset
    this.setData({ [field]: e.detail.value })
  },

  saveSession(sessionInfo) {
    wx.setStorageSync('session_id', sessionInfo.session_id)
    wx.setStorageSync('family_id', sessionInfo.family_id)
    wx.setStorageSync('member_name', sessionInfo.member_name)
    wx.setStorageSync('family_name', sessionInfo.family_name)
  },

  goHome() {
    wx.redirectTo({ url: '/pages/home/home' })
  },

  createFamily() {
    const { createFamilyName, createAdminName } = this.data
    if (!createFamilyName || !createAdminName) {
      wx.showToast({ title: '请填写家庭名称和管理员名', icon: 'none' })
      return
    }
    this.setData({ loading: true })
    request({
      path: '/api/auth/create-family',
      method: 'POST',
      data: { family_name: createFamilyName, admin_name: createAdminName },
    })
      .then((data) => {
        if (data && data.success) {
          this.saveSession(data)
          wx.showToast({ title: '家庭已创建', icon: 'success' })
          this.goHome()
          return
        }
        wx.showToast({ title: (data && data.message) || '创建失败', icon: 'none' })
      })
      .catch(() => {})
      .then(() => this.setData({ loading: false }))
  },
})
