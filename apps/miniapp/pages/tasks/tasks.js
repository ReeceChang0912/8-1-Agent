const { request } = require('../../utils/request')

Page({
  data: {
    loading: true,
    tasks: [],
    memberName: '',
    familyId: '',
    pendingCount: 0,
    completedCount: 0,
  },

  onLoad() {
    wx.setNavigationBarTitle({ title: '家庭任务' })
    const memberName = wx.getStorageSync('member_name') || ''
    const familyId = wx.getStorageSync('family_id') || ''
    if (!memberName || !familyId) {
      wx.redirectTo({ url: '/pages/auth/auth' })
      return
    }
    this.setData({ memberName, familyId })
    this.loadTasks()
  },

  onShow() {
    if (this.data.memberName && this.data.familyId) {
      this.loadTasks()
    }
  },

  loadTasks() {
    const { memberName, familyId } = this.data
    this.setData({ loading: true })
    request({
      path: '/api/tasks/my',
      method: 'GET',
      data: {
        member_name: memberName,
        status: 'all',
        family_id: familyId,
      },
    })
      .then((data) => {
        const tasks = (data.tasks || []).map((item) => ({
          ...item,
          status_text: item.status === 'completed' ? '已完成' : item.status === 'cancelled' ? '已取消' : '待完成',
          priority_text: item.priority === 'high' ? '重要' : item.priority === 'low' ? '低优先' : '普通',
        }))
        this.setData({
          tasks,
          pendingCount: tasks.filter((item) => item.status === 'pending').length,
          completedCount: tasks.filter((item) => item.status === 'completed').length,
        })
      })
      .catch(() => {})
      .then(() => this.setData({ loading: false }))
  },

  completeTask(e) {
    const taskId = e.currentTarget.dataset.taskid
    if (!taskId) return
    request({
      path: `/api/tasks/${encodeURIComponent(taskId)}/complete`,
      method: 'POST',
      data: {
        family_id: this.data.familyId,
      },
    })
      .then((data) => {
        if (data && data.success) {
          wx.showToast({ title: '已完成', icon: 'success' })
          this.loadTasks()
          return
        }
        wx.showToast({ title: (data && data.message) || '操作失败', icon: 'none' })
      })
      .catch(() => {})
  },

  openChatAssign() {
    wx.navigateTo({
      url: `/pages/webview/webview?route=${encodeURIComponent('/chat?prompt=/tasks ')}&title=${encodeURIComponent('分配任务')}`,
    })
  },

  openChatList() {
    wx.navigateTo({
      url: `/pages/webview/webview?route=${encodeURIComponent('/chat?prompt=/tasks list')}&title=${encodeURIComponent('我的任务')}`,
    })
  },
})
