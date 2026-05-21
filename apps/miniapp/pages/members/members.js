const { request } = require('../../utils/request')

function normalize(value) {
  return String(value || '').trim()
}

function getOptionIndex(options, value) {
  const index = options.indexOf(value)
  return index >= 0 ? index : 0
}

function buildInvitationUrl(familyId, code) {
  if (!familyId || !code) return ''
  return `/pages/join-family/join-family?invite=${encodeURIComponent(code)}&family_id=${encodeURIComponent(familyId)}`
}

Page({
  data: {
    loading: true,
    saving: false,
    inviteLoading: false,
    members: [],
    topMembers: [],
    summary: {
      member_count: 0,
      active_member_count: 0,
      shopping_items: 0,
      chore_items: 0,
      travel_items: 0,
      top_member: '',
    },
    familyId: '',
    familyName: '',
    memberName: '',
    familyMembers: [],
    inviteCode: '',
    inviteUrl: '',
    addVisible: false,
    editVisible: false,
    editingName: '',
    addName: '',
    addRole: '',
    addAge: '',
    addSide: 'core',
    addStyle: 'peer',
    addPermission: 'member',
    addSideIndex: 0,
    addStyleIndex: 0,
    addPermissionIndex: 1,
    addSideOptions: ['core', 'extended', 'guest'],
    addStyleOptions: ['peer', 'child', 'elder', 'formal'],
    addPermissionOptions: ['admin', 'member', 'guest', 'child'],
    editRole: '',
    editAge: '',
    editSide: 'core',
    editStyle: 'peer',
    editPermission: 'member',
    editSideIndex: 0,
    editStyleIndex: 0,
    editPermissionIndex: 0,
    editSideOptions: ['core', 'extended', 'guest'],
    editStyleOptions: ['peer', 'child', 'elder', 'formal'],
    editPermissionOptions: ['admin', 'member', 'guest', 'child'],
  },

  onLoad() {
    wx.setNavigationBarTitle({ title: '家庭成员' })
    const memberName = wx.getStorageSync('member_name') || ''
    const familyId = wx.getStorageSync('family_id') || ''
    const familyName = wx.getStorageSync('family_name') || ''
    if (!memberName || !familyId) {
      wx.redirectTo({ url: '/pages/auth/auth' })
      return
    }
    this.setData({ memberName, familyId, familyName })
    this.refresh()
  },

  onShow() {
    if (this.data.familyId) {
      this.refresh()
    }
  },

  refresh() {
    this.setData({ loading: true })
    Promise.all([this.loadMembers(), this.loadStats(), this.loadFamilyInfo()])
      .then(([membersRes, statsRes, familyRes]) => {
        const members = (membersRes && membersRes.members) || []
        const memberStats = (statsRes && statsRes.summary) || {}
        const topMembers = ((statsRes && statsRes.members) || []).slice(0, 4)
        const familyMembers = (familyRes && familyRes.members) || []
        this.setData({
          members,
          summary: {
            member_count: memberStats.member_count || members.length,
            active_member_count: memberStats.active_member_count || 0,
            shopping_items: memberStats.shopping_items || 0,
            chore_items: memberStats.chore_items || 0,
            travel_items: memberStats.travel_items || 0,
            top_member: memberStats.top_member || '',
          },
          topMembers,
          familyMembers,
          familyName: (familyRes && familyRes.family_name) || this.data.familyName,
        })
      })
      .catch(() => {})
      .then(() => this.setData({ loading: false }))
  },

  loadMembers() {
    return request({
      path: '/api/members',
      method: 'GET',
    }).catch(() => ({ members: [] }))
  },

  loadStats() {
    return request({
      path: '/api/members/stats',
      method: 'GET',
      data: { family_id: this.data.familyId },
    }).catch(() => ({ summary: {}, members: [] }))
  },

  loadFamilyInfo() {
    return request({
      path: '/api/auth/family-members',
      method: 'GET',
      data: { family_id: this.data.familyId },
    }).catch(() => ({ family_id: this.data.familyId, family_name: this.data.familyName, members: [] }))
  },

  setField(e) {
    const { field } = e.currentTarget.dataset
    this.setData({ [field]: e.detail.value })
  },

  openChatFamily() {
    const route = `/chat?prompt=${encodeURIComponent('/members summary')}`
    wx.navigateTo({
      url: `/pages/webview/webview?route=${encodeURIComponent(route)}&title=${encodeURIComponent('家庭成员')}`,
    })
  },

  copyFamilyId() {
    if (!this.data.familyId) return
    wx.setClipboardData({
      data: this.data.familyId,
      success: () => wx.showToast({ title: '已复制家庭号', icon: 'success' }),
    })
  },

  createInvite() {
    if (!this.data.familyId) return
    this.setData({ inviteLoading: true })
    request({
      path: `/api/members/invite/create?family_id=${encodeURIComponent(this.data.familyId)}&creator=${encodeURIComponent(this.data.memberName)}`,
      method: 'POST',
    })
      .then((data) => {
        const code = data.code || data.invite_code || ''
        const inviteUrl = buildInvitationUrl(this.data.familyId, code)
        this.setData({
          inviteCode: code,
          inviteUrl,
        })
        if (inviteUrl) {
          wx.setClipboardData({
            data: inviteUrl,
            success: () => wx.showToast({ title: '邀请已复制', icon: 'success' }),
          })
        }
      })
      .catch(() => {
        wx.showToast({ title: '生成邀请失败', icon: 'none' })
      })
      .then(() => this.setData({ inviteLoading: false }))
  },

  openAdd() {
    this.setData({
      addVisible: true,
      addName: '',
      addRole: '',
      addAge: '',
      addSide: 'core',
      addSideIndex: 0,
      addStyle: 'peer',
      addStyleIndex: 0,
      addPermission: 'member',
      addPermissionIndex: 1,
    })
  },

  closeAdd() {
    this.setData({ addVisible: false })
  },

  changeAddSide(e) {
    const index = Number(e.detail.value)
    this.setData({
      addSideIndex: index,
      addSide: this.data.addSideOptions[index] || this.data.addSide,
    })
  },

  changeAddStyle(e) {
    const index = Number(e.detail.value)
    this.setData({
      addStyleIndex: index,
      addStyle: this.data.addStyleOptions[index] || this.data.addStyle,
    })
  },

  changeAddPermission(e) {
    const index = Number(e.detail.value)
    this.setData({
      addPermissionIndex: index,
      addPermission: this.data.addPermissionOptions[index] || this.data.addPermission,
    })
  },

  openEdit(e) {
    const name = e.currentTarget.dataset.name
    const member = this.data.members.find((item) => item.name === name)
    if (!member) return
    this.setData({
      editVisible: true,
      editingName: member.name,
      editRole: member.role || '',
      editAge: String(member.age || ''),
      editSide: member.side || 'core',
      editSideIndex: getOptionIndex(this.data.editSideOptions, member.side || 'core'),
      editStyle: member.interaction_style || 'peer',
      editStyleIndex: getOptionIndex(this.data.editStyleOptions, member.interaction_style || 'peer'),
      editPermission: member.permission || 'member',
      editPermissionIndex: getOptionIndex(this.data.editPermissionOptions, member.permission || 'member'),
    })
  },

  closeEdit() {
    this.setData({ editVisible: false, editingName: '' })
  },

  changeEditSide(e) {
    const index = Number(e.detail.value)
    this.setData({
      editSideIndex: index,
      editSide: this.data.editSideOptions[index] || this.data.editSide,
    })
  },

  changeEditStyle(e) {
    const index = Number(e.detail.value)
    this.setData({
      editStyleIndex: index,
      editStyle: this.data.editStyleOptions[index] || this.data.editStyle,
    })
  },

  changeEditPermission(e) {
    const index = Number(e.detail.value)
    this.setData({
      editPermissionIndex: index,
      editPermission: this.data.editPermissionOptions[index] || this.data.editPermission,
    })
  },

  saveAdd() {
    const name = normalize(this.data.addName)
    const role = normalize(this.data.addRole)
    const age = Number(this.data.addAge || 0)
    if (!name || !role || !age) {
      wx.showToast({ title: '请填写姓名、角色和年龄', icon: 'none' })
      return
    }
    this.setData({ saving: true })
    request({
      path: `/api/members?session_id=${encodeURIComponent(wx.getStorageSync('session_id') || '')}`,
      method: 'POST',
      data: {
        name,
        role,
        age,
        side: this.data.addSide,
        interaction_style: this.data.addStyle,
        permission: this.data.addPermission,
        preferences: [],
      },
    })
      .then((data) => {
        if (data && data.success) {
          wx.showToast({ title: '成员已添加', icon: 'success' })
          this.closeAdd()
          this.refresh()
          return
        }
        wx.showToast({ title: (data && data.message) || '添加失败', icon: 'none' })
      })
      .catch(() => {})
      .then(() => this.setData({ saving: false }))
  },

  saveEdit() {
    const name = this.data.editingName
    const role = normalize(this.data.editRole)
    const age = Number(this.data.editAge || 0)
    if (!name || !role || !age) {
      wx.showToast({ title: '请填写角色和年龄', icon: 'none' })
      return
    }
    this.setData({ saving: true })
    request({
      path: `/api/members/${encodeURIComponent(name)}`,
      method: 'PUT',
      data: {
        name,
        role,
        age,
        side: this.data.editSide,
        interaction_style: this.data.editStyle,
        permission: this.data.editPermission,
      },
    })
      .then((data) => {
        if (data && data.success) {
          wx.showToast({ title: '成员已更新', icon: 'success' })
          this.closeEdit()
          this.refresh()
          return
        }
        wx.showToast({ title: (data && data.message) || '更新失败', icon: 'none' })
      })
      .catch(() => {})
      .then(() => this.setData({ saving: false }))
  },

  deleteMember(e) {
    const name = e.currentTarget.dataset.name
    if (!name) return
    wx.showModal({
      title: '删除成员',
      content: `确定删除 ${name} 吗？`,
      confirmText: '删除',
      success: (res) => {
        if (!res.confirm) return
        request({
          path: `/api/members/${encodeURIComponent(name)}`,
          method: 'DELETE',
        })
          .then((data) => {
            if (data && data.success) {
              wx.showToast({ title: '成员已删除', icon: 'success' })
              this.refresh()
              return
            }
            wx.showToast({ title: '删除失败', icon: 'none' })
          })
          .catch(() => {})
      },
    })
  },
})
