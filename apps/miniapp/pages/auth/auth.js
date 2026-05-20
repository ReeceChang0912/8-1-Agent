const { request } = require('../../utils/request')

Page({
  data: {
    loading: false,
    familyId: '',
    memberName: '',
    familyName: '',
    loginFamilyId: '',
    loginMemberName: '',
    wechatCode: '',
    phoneCode: '',
  },

  onLoad(options) {
    const inviteCode = options.invite ? decodeURIComponent(options.invite) : ''
    const familyId = options.family_id ? decodeURIComponent(options.family_id) : ''
    wx.setNavigationBarTitle({ title: '家庭登录' })
    if (inviteCode) {
      wx.redirectTo({
        url: `/pages/join-family/join-family?invite=${encodeURIComponent(inviteCode)}&family_id=${encodeURIComponent(familyId)}`,
      })
      return
    }
    this.refreshWechatCode()
  },

  refreshWechatCode() {
    return new Promise((resolve) => {
      wx.login({
        success: (res) => {
          const code = res.code || ''
          if (code) this.setData({ wechatCode: code })
          resolve(code)
        },
        fail: () => resolve(''),
      })
    })
  },

  setField(e) {
    const { field } = e.currentTarget.dataset
    this.setData({ [field]: e.detail.value })
  },

  openJoinFamily() {
    wx.navigateTo({ url: '/pages/join-family/join-family' })
  },

  openCreateFamily() {
    wx.navigateTo({ url: '/pages/create-family/create-family' })
  },

  saveSession(sessionInfo) {
    wx.setStorageSync('session_id', sessionInfo.session_id)
    wx.setStorageSync('family_id', sessionInfo.family_id)
    wx.setStorageSync('member_name', sessionInfo.member_name)
    wx.setStorageSync('family_name', sessionInfo.family_name)
    if (sessionInfo.phone_number) wx.setStorageSync('phone_number', sessionInfo.phone_number)
    if (sessionInfo.wechat_openid) wx.setStorageSync('wechat_openid', sessionInfo.wechat_openid)
    this.setData({
      familyId: sessionInfo.family_id,
      memberName: sessionInfo.member_name,
      familyName: sessionInfo.family_name,
    })
  },

  goHome() {
    wx.redirectTo({ url: '/pages/home/home' })
  },

  handleAuthResult(data, successTitle, fallbackTitle) {
    if (data && data.success) {
      this.saveSession(data)
      wx.showToast({ title: successTitle, icon: 'success' })
      this.goHome()
      return
    }
    wx.showToast({ title: (data && data.message) || fallbackTitle, icon: 'none' })
  },

  loginWithWechat() {
    const { loginFamilyId, loginMemberName } = this.data
    if (!loginFamilyId || !loginMemberName) {
      wx.showToast({ title: '请先填写家庭号和成员名', icon: 'none' })
      return
    }
    this.setData({ loading: true })
    this.refreshWechatCode()
      .then((wechatCode) => request({
        path: '/api/auth/wechat-login',
        method: 'POST',
        data: {
          code: wechatCode,
          family_id: loginFamilyId,
          member_name: loginMemberName,
        },
      }))
      .then((data) => this.handleAuthResult(data, '微信登录成功', '微信登录失败'))
      .catch(() => {})
      .then(() => this.setData({ loading: false }))
  },

  onGetPhoneNumber(e) {
    const code = (e.detail && e.detail.code) || ''
    if (!code) {
      wx.showToast({ title: '未获取到手机号授权', icon: 'none' })
      return
    }
    const { loginFamilyId, loginMemberName } = this.data
    if (!loginFamilyId) {
      wx.showToast({ title: '请先填写家庭号', icon: 'none' })
      return
    }
    this.setData({ loading: true, phoneCode: code })
    const path = loginMemberName ? '/api/auth/phone-bind-login' : '/api/auth/phone-login'
    this.refreshWechatCode()
      .then((wechatCode) => request({
        path,
        method: 'POST',
        data: {
          code,
          family_id: loginFamilyId,
          member_name: loginMemberName,
          wechat_code: wechatCode,
        },
      }))
      .then((data) => {
        if (data && data.need_bind) {
          wx.showToast({ title: '请填成员名后再授权绑定', icon: 'none' })
          return
        }
        this.handleAuthResult(
          data,
          loginMemberName ? '手机号已绑定' : '手机号登录成功',
          '手机号登录失败',
        )
      })
      .catch(() => {})
      .then(() => {
        this.setData({ loading: false })
        this.refreshWechatCode()
      })
  },

  login() {
    const { loginFamilyId, loginMemberName } = this.data
    if (!loginFamilyId || !loginMemberName) {
      wx.showToast({ title: '请填写家庭号和成员名', icon: 'none' })
      return
    }
    this.setData({ loading: true })
    request({
      path: '/api/auth/login',
      method: 'POST',
      data: { family_id: loginFamilyId, member_name: loginMemberName },
    })
      .then((data) => this.handleAuthResult(data, '登录成功', '登录失败'))
      .catch(() => {})
      .then(() => this.setData({ loading: false }))
  },

})
