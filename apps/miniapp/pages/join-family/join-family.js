const { request } = require('../../utils/request')

Page({
  data: {
    loading: false,
    inviteCode: '',
    joinFamilyId: '',
    joinMemberName: '',
  },

  onLoad(options) {
    wx.setNavigationBarTitle({ title: '加入家庭' })
    this.setData({
      inviteCode: options.invite ? decodeURIComponent(options.invite) : '',
      joinFamilyId: options.family_id ? decodeURIComponent(options.family_id) : '',
    })
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

  joinFamily() {
    const { joinFamilyId, joinMemberName, inviteCode } = this.data
    if (!joinMemberName || (!joinFamilyId && !inviteCode)) {
      wx.showToast({ title: '请填写家庭号和成员名', icon: 'none' })
      return
    }
    this.setData({ loading: true })
    request({
      path: '/api/auth/join-family',
      method: 'POST',
      data: {
        family_id: joinFamilyId,
        member_name: joinMemberName,
        invite_code: inviteCode || undefined,
      },
    })
      .then((data) => {
        if (data && data.success) {
          this.saveSession(data)
          wx.showToast({ title: '加入成功', icon: 'success' })
          this.goHome()
          return
        }
        wx.showToast({ title: (data && data.message) || '加入失败', icon: 'none' })
      })
      .catch(() => {})
      .then(() => this.setData({ loading: false }))
  },
})
