const { request } = require('../../utils/request')

function todayString() {
  const date = new Date()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${date.getFullYear()}-${month}-${day}`
}

function formatDate(value) {
  if (!value) return '-'
  const text = String(value)
  const match = text.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (!match) return text
  return `${match[2]}月${match[3]}日`
}

Page({
  data: {
    loading: true,
    submitting: false,
    reminders: [],
    upcomingReminders: [],
    pastReminders: [],
    recommendations: [],
    freeTimes: [],
    familyId: '',
    memberName: '',
    reminderDate: '',
    reminderEvent: '',
    upcomingCount: 0,
    pastCount: 0,
  },

  onLoad() {
    wx.setNavigationBarTitle({ title: '家庭日程' })
    const memberName = wx.getStorageSync('member_name') || ''
    const familyId = wx.getStorageSync('family_id') || ''
    if (!memberName || !familyId) {
      wx.redirectTo({ url: '/pages/auth/auth' })
      return
    }
    this.setData({ memberName, familyId, reminderDate: todayString() })
    this.refresh()
  },

  onShow() {
    if (this.data.familyId) {
      this.refresh()
    }
  },

  setField(e) {
    const { field } = e.currentTarget.dataset
    this.setData({ [field]: e.detail.value })
  },

  onDateChange(e) {
    this.setData({ reminderDate: e.detail.value })
  },

  refresh() {
    this.setData({ loading: true })
    Promise.all([this.loadReminders(), this.loadSuggestions()])
      .then(() => {})
      .catch(() => {})
      .then(() => this.setData({ loading: false }))
  },

  loadReminders() {
    return request({
      path: '/api/reminders',
      method: 'GET',
      data: { family_id: this.data.familyId },
    }).then((data) => {
      const today = todayString()
      const reminders = (data.reminders || [])
        .map((item) => ({
          ...item,
          date_text: formatDate(item.date),
          member_text: item.member || '全家',
          is_past: String(item.date || '') < today,
        }))
        .sort((a, b) => String(a.date || '').localeCompare(String(b.date || '')))
      const upcomingReminders = reminders.filter((item) => !item.is_past)
      const pastReminders = reminders.filter((item) => item.is_past).reverse()
      this.setData({
        reminders,
        upcomingReminders,
        pastReminders,
        upcomingCount: upcomingReminders.length,
        pastCount: pastReminders.length,
      })
    })
  },

  loadSuggestions() {
    const date = todayString()
    const memberName = this.data.memberName
    return Promise.all([
      request({
        path: `/api/recommendations/${encodeURIComponent(memberName)}`,
        method: 'GET',
        data: { date },
      }),
      request({
        path: `/api/free-times/${encodeURIComponent(memberName)}`,
        method: 'GET',
        data: { date },
      }),
    ]).then(([recommendationsRes, freeTimesRes]) => {
      this.setData({
        recommendations: (recommendationsRes.recommendations || []).slice(0, 3),
        freeTimes: (freeTimesRes.free_times || []).slice(0, 3),
      })
    })
  },

  addReminder() {
    const event = this.data.reminderEvent.trim()
    if (!this.data.reminderDate || !event) {
      wx.showToast({ title: '请选择日期并填写事项', icon: 'none' })
      return
    }
    this.setData({ submitting: true })
    request({
      path: '/api/reminders',
      method: 'POST',
      data: {
        date: this.data.reminderDate,
        event,
        member: this.data.memberName,
        family_id: this.data.familyId,
      },
    })
      .then((data) => {
        if (data && data.success) {
          wx.showToast({ title: '已添加提醒', icon: 'success' })
          this.setData({ reminderEvent: '' })
          this.refresh()
          return
        }
        wx.showToast({ title: (data && data.message) || '添加失败', icon: 'none' })
      })
      .catch(() => {})
      .then(() => this.setData({ submitting: false }))
  },

  removeReminder(e) {
    const reminderId = e.currentTarget.dataset.id
    if (!reminderId) return
    request({
      path: `/api/reminders/${encodeURIComponent(reminderId)}?family_id=${encodeURIComponent(this.data.familyId)}`,
      method: 'DELETE',
    })
      .then((data) => {
        if (data && data.success) {
          wx.showToast({ title: '已删除', icon: 'success' })
          this.refresh()
          return
        }
        wx.showToast({ title: '删除失败', icon: 'none' })
      })
      .catch(() => {})
  },

  openChatReminder() {
    wx.navigateTo({
      url: `/pages/webview/webview?route=${encodeURIComponent('/chat?prompt=/remind ')}&title=${encodeURIComponent('创建提醒')}`,
    })
  },
})
