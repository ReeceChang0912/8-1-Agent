const { request } = require('../../utils/request')

const CHORE_TYPES = [
  {
    key: 'task',
    label: '家务',
    recordType: 'task',
    statuses: ['待处理', '进行中', '已完成'],
    doneStatus: '已完成',
    hint: '日常分配、完成确认、家庭协作',
  },
  {
    key: 'rotation',
    label: '轮值',
    recordType: 'rotation',
    statuses: ['待轮值', '本周执行', '已完成'],
    doneStatus: '已完成',
    hint: '值日安排、轮值提醒、周期执行',
  },
  {
    key: 'supply',
    label: '补货',
    recordType: 'supply',
    statuses: ['待补货', '采购中', '已补货'],
    doneStatus: '已补货',
    hint: '缺什么、谁买、是否补上',
  },
  {
    key: 'checklist',
    label: '检查',
    recordType: 'checklist',
    statuses: ['待检查', '检查中', '已打卡'],
    doneStatus: '已打卡',
    hint: '巡检、打卡、归档确认',
  },
]

function todayString() {
  const date = new Date()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${date.getFullYear()}-${month}-${day}`
}

function formatDate(value) {
  if (!value) return '未设日期'
  const text = String(value)
  const match = text.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (!match) return text
  return `${match[2]}月${match[3]}日`
}

function normalize(value) {
  return String(value || '').trim()
}

function getTypeConfig(typeKey) {
  return CHORE_TYPES.find((item) => item.key === typeKey) || CHORE_TYPES[0]
}

function buildTabs(items) {
  return CHORE_TYPES.map((item) => ({
    ...item,
    count: items.filter((record) => record.record_type === item.recordType).length,
  }))
}

function buildMemberFilters(members) {
  return [
    { label: '全部', value: 'all' },
    ...members.map((member) => ({ label: member.name, value: member.name })),
  ]
}

function buildChoreCard(item) {
  const config = getTypeConfig(item.record_type)
  const status = normalize(item.status) || config.statuses[0]
  const done = status === config.doneStatus
  const dueDate = normalize(item.due_date)
  const overdue = !!dueDate && !done && dueDate < todayString()
  return {
    ...item,
    type_key: config.key,
    type_label: config.label,
    status_text: status,
    status_class: done ? 'done' : overdue ? 'overdue' : 'active',
    is_done: done,
    is_overdue: overdue,
    assignee_text: normalize(item.assignee) || '未分配',
    frequency_text: normalize(item.frequency) || '未设频率',
    due_text: formatDate(dueDate),
    note_text: normalize(item.note) || '未填写备注',
    points_text: `${Number(item.points || 0)} 分`,
  }
}

function filterChores(items, tabKey, keyword, memberFilter) {
  const q = normalize(keyword).toLowerCase()
  const config = getTypeConfig(tabKey)
  const filtered = items.filter((item) => {
    if ((item.record_type || '') !== config.recordType) return false
    if (memberFilter !== 'all' && normalize(item.assignee) !== memberFilter) return false
    if (!q) return true
    const haystack = [
      item.title,
      item.assignee,
      item.frequency,
      item.status,
      item.note,
      item.due_date,
    ]
      .map((value) => normalize(value).toLowerCase())
      .join(' ')
    return haystack.includes(q)
  })

  return filtered
    .map(buildChoreCard)
    .sort((a, b) => {
      const aRank = a.is_done ? 2 : a.is_overdue ? 0 : 1
      const bRank = b.is_done ? 2 : b.is_overdue ? 0 : 1
      if (aRank !== bRank) return aRank - bRank
      return normalize(a.due_date).localeCompare(normalize(b.due_date)) || Number(b.id || 0) - Number(a.id || 0)
    })
}

function getMemberIndex(members, name) {
  return members.findIndex((item) => item.name === name)
}

Page({
  data: {
    loading: true,
    saving: false,
    chores: [],
    visibleChores: [],
    tabs: CHORE_TYPES.map((item) => ({ ...item, count: 0 })),
    stats: {
      total_count: 0,
      task_count: 0,
      rotation_count: 0,
      supply_count: 0,
      checklist_count: 0,
      done_count: 0,
      overdue_count: 0,
      points_total: 0,
    },
    currentTab: 'task',
    searchKeyword: '',
    memberFilter: 'all',
    members: [],
    memberFilters: [{ label: '全部', value: 'all' }],
    memberCount: 0,
    familyId: '',
    memberName: '',
    chatPrompts: [
      { title: '家务概览', prompt: '/chores summary', desc: '查看家务整体进度' },
      { title: '家务列表', prompt: '/chores list', desc: '按记录展开明细' },
      { title: '新增家务', prompt: '/chores add 周末大扫除', desc: '一句话创建新记录' },
    ],
    formType: 'task',
    formTypeLabel: '家务',
    formRecordType: 'task',
    formHint: '日常分配、完成确认、家庭协作',
    formStatusOptions: ['待处理', '进行中', '已完成'],
    formDoneStatus: '已完成',
    editingId: '',
    title: '',
    assigneeName: '',
    assigneeIndex: 0,
    frequency: '',
    dueDate: todayString(),
    status: '待处理',
    statusIndex: 0,
    points: '0',
    note: '',
  },

  onLoad() {
    wx.setNavigationBarTitle({ title: '家务分工' })
    const memberName = wx.getStorageSync('member_name') || ''
    const familyId = wx.getStorageSync('family_id') || ''
    if (!memberName || !familyId) {
      wx.redirectTo({ url: '/pages/auth/auth' })
      return
    }
    this.setData({
      memberName,
      familyId,
      assigneeName: memberName,
    })
    this.refresh()
  },

  onShow() {
    if (this.data.familyId) {
      this.refresh()
    }
  },

  refresh() {
    this.setData({ loading: true })
    Promise.all([this.loadChores(), this.loadStats(), this.loadMembers()])
      .then(([chores, stats, members]) => {
        const nextTabs = buildTabs(chores)
        const nextMemberFilters = buildMemberFilters(members)
        const nextVisibleChores = filterChores(
          chores,
          this.data.currentTab,
          this.data.searchKeyword,
          this.data.memberFilter,
        )
        const nextAssigneeName = this.data.assigneeName || this.data.memberName || (members[0] && members[0].name) || ''
        const nextAssigneeIndex = nextAssigneeName ? getMemberIndex(members, nextAssigneeName) : 0
        this.setData({
          chores,
          stats,
          members,
          memberCount: members.length,
          memberFilters: nextMemberFilters,
          tabs: nextTabs,
          visibleChores: nextVisibleChores,
          assigneeName: nextAssigneeName,
          assigneeIndex: nextAssigneeIndex >= 0 ? nextAssigneeIndex : 0,
        })
      })
      .catch(() => {})
      .then(() => {
        this.setData({ loading: false })
      })
  },

  loadChores() {
    return request({
      path: '/api/modules/chores',
      method: 'GET',
      data: { family_id: this.data.familyId },
    })
      .then((data) => (data && data.items) || [])
      .catch(() => [])
  },

  loadStats() {
    return request({
      path: '/api/modules/chores/stats',
      method: 'GET',
      data: { family_id: this.data.familyId },
    })
      .then((data) => ({
        total_count: data.total_count || 0,
        task_count: data.task_count || 0,
        rotation_count: data.rotation_count || 0,
        supply_count: data.supply_count || 0,
        checklist_count: data.checklist_count || 0,
        done_count: data.done_count || 0,
        overdue_count: data.overdue_count || 0,
        points_total: Number(data.points_total || 0),
      }))
      .catch(() => ({
        total_count: 0,
        task_count: 0,
        rotation_count: 0,
        supply_count: 0,
        checklist_count: 0,
        done_count: 0,
        overdue_count: 0,
        points_total: 0,
      }))
  },

  loadMembers() {
    return request({
      path: '/api/members',
      method: 'GET',
    })
      .then((data) => (data && data.members) || [])
      .catch(() => [])
  },

  setField(e) {
    const { field } = e.currentTarget.dataset
    const value = e.detail.value
    this.setData({ [field]: value })
  },

  setSearch(e) {
    const searchKeyword = e.detail.value
    this.setData({ searchKeyword })
    this.applyFilters({ searchKeyword })
  },

  clearSearch() {
    this.setData({ searchKeyword: '' })
    this.applyFilters({ searchKeyword: '' })
  },

  setMemberFilter(e) {
    const { value } = e.currentTarget.dataset
    const memberFilter = value || 'all'
    this.setData({ memberFilter })
    this.applyFilters({ memberFilter })
  },

  switchTab(e) {
    const { key } = e.currentTarget.dataset
    if (!key || key === this.data.currentTab) return
    this.setData({ currentTab: key })
    this.applyFilters({ currentTab: key })
  },

  applyFilters(nextState = {}) {
    const currentTab = nextState.currentTab || this.data.currentTab
    const searchKeyword = Object.prototype.hasOwnProperty.call(nextState, 'searchKeyword')
      ? nextState.searchKeyword
      : this.data.searchKeyword
    const memberFilter = Object.prototype.hasOwnProperty.call(nextState, 'memberFilter')
      ? nextState.memberFilter
      : this.data.memberFilter
    const visibleChores = filterChores(this.data.chores, currentTab, searchKeyword, memberFilter)
    const tabs = buildTabs(this.data.chores)
    this.setData({
      ...nextState,
      visibleChores,
      tabs,
    })
  },

  syncFormType(typeKey, statusValue) {
    const config = getTypeConfig(typeKey)
    const nextStatus = config.statuses.includes(statusValue) ? statusValue : config.statuses[0]
    this.setData({
      formType: config.key,
      formTypeLabel: config.label,
      formRecordType: config.recordType,
      formHint: config.hint,
      formStatusOptions: config.statuses,
      formDoneStatus: config.doneStatus,
      status: nextStatus,
      statusIndex: Math.max(config.statuses.indexOf(nextStatus), 0),
    })
  },

  syncAssigneePicker(nextAssigneeName) {
    const assigneeName = nextAssigneeName !== undefined ? nextAssigneeName : this.data.assigneeName
    const assigneeIndex = getMemberIndex(this.data.members, assigneeName)
    this.setData({
      assigneeName,
      assigneeIndex: assigneeIndex >= 0 ? assigneeIndex : 0,
    })
  },

  openCreate() {
    const defaultAssignee = this.data.memberName || (this.data.members[0] && this.data.members[0].name) || ''
    this.syncFormType(this.data.currentTab)
    this.setData({
      editingId: '',
      title: '',
      assigneeName: defaultAssignee,
      frequency: '',
      dueDate: todayString(),
      points: '0',
      note: '',
    }, () => {
      this.syncAssigneePicker(defaultAssignee)
    })
  },

  editItem(e) {
    const itemId = e.currentTarget.dataset.id
    const item = this.data.chores.find((record) => String(record.id) === String(itemId))
    if (!item) return
    this.syncFormType(item.record_type, item.status)
    const assigneeName = normalize(item.assignee)
    const points = item.points === undefined || item.points === null ? 0 : item.points
    this.setData({
      editingId: item.id,
      title: item.title || '',
      assigneeName,
      frequency: item.frequency || '',
      dueDate: item.due_date || todayString(),
      points: String(points),
      note: item.note || '',
    }, () => {
      this.syncAssigneePicker(assigneeName)
    })
  },

  resetForm() {
    const defaultAssignee = this.data.memberName || (this.data.members[0] && this.data.members[0].name) || ''
    this.syncFormType(this.data.currentTab)
    this.setData({
      editingId: '',
      title: '',
      assigneeName: defaultAssignee,
      frequency: '',
      dueDate: todayString(),
      points: '0',
      note: '',
    }, () => {
      this.syncAssigneePicker(defaultAssignee)
    })
  },

  changeAssignee(e) {
    const index = Number(e.detail.value)
    const assigneeName = this.data.members[index] ? this.data.members[index].name : ''
    this.setData({
      assigneeIndex: index,
      assigneeName,
    })
  },

  changeStatus(e) {
    const index = Number(e.detail.value)
    const status = this.data.formStatusOptions[index] || this.data.formStatusOptions[0]
    this.setData({
      statusIndex: index,
      status,
    })
  },

  changeDueDate(e) {
    this.setData({ dueDate: e.detail.value })
  },

  saveItem() {
    const title = normalize(this.data.title)
    if (!title) {
      wx.showToast({ title: '请输入标题', icon: 'none' })
      return
    }
    this.setData({ saving: true })
    const payload = {
      record_type: this.data.formRecordType,
      title,
      assignee: normalize(this.data.assigneeName),
      frequency: normalize(this.data.frequency),
      due_date: normalize(this.data.dueDate),
      points: Number(this.data.points || 0),
      status: normalize(this.data.status) || this.data.formStatusOptions[0],
      note: normalize(this.data.note),
      family_id: this.data.familyId,
    }
    const action = this.data.editingId
      ? request({
          path: `/api/modules/chores/${encodeURIComponent(this.data.editingId)}`,
          method: 'PUT',
          data: payload,
        })
      : request({
          path: '/api/modules/chores',
          method: 'POST',
          data: payload,
        })

    action
      .then((data) => {
        if (data && data.success) {
          wx.showToast({ title: this.data.editingId ? '已更新' : '已添加', icon: 'success' })
          this.resetForm()
          this.refresh()
          return
        }
        wx.showToast({ title: (data && data.message) || '保存失败', icon: 'none' })
      })
      .catch(() => {})
      .then(() => {
        this.setData({ saving: false })
      })
  },

  toggleDone(e) {
    const itemId = e.currentTarget.dataset.id
    const item = this.data.chores.find((record) => String(record.id) === String(itemId))
    if (!item) return
    const config = getTypeConfig(item.record_type)
    const status = normalize(item.status) === config.doneStatus ? config.statuses[0] : config.doneStatus
    request({
      path: `/api/modules/chores/${encodeURIComponent(item.id)}`,
      method: 'PUT',
      data: {
        record_type: config.recordType,
        title: item.title || '',
        assignee: item.assignee || '',
        frequency: item.frequency || '',
        due_date: item.due_date || '',
        points: Number(item.points || 0),
        status,
        note: item.note || '',
        family_id: this.data.familyId,
      },
    })
      .then((data) => {
        if (data && data.success) {
          wx.showToast({ title: '已更新', icon: 'success' })
          this.refresh()
          return
        }
        wx.showToast({ title: '操作失败', icon: 'none' })
      })
      .catch(() => {})
  },

  removeItem(e) {
    const itemId = e.currentTarget.dataset.id
    if (!itemId) return
    wx.showModal({
      title: '删除家务',
      content: '确认删除这条家务记录？',
      confirmText: '删除',
      success: (res) => {
        if (!res.confirm) return
        request({
          path: `/api/modules/chores/${encodeURIComponent(itemId)}?family_id=${encodeURIComponent(this.data.familyId)}`,
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
    })
  },

  openChatPrompt(e) {
    const prompt = e.currentTarget.dataset.prompt || '/chores summary'
    const title = e.currentTarget.dataset.title || '家务分工'
    const route = `/chat?prompt=${encodeURIComponent(prompt)}`
    wx.navigateTo({
      url: `/pages/webview/webview?route=${encodeURIComponent(route)}&title=${encodeURIComponent(title)}`,
    })
  },

  openChatSummary() {
    this.openChatPrompt({
      currentTarget: {
        dataset: {
          prompt: '/chores summary',
          title: '家务概览',
        },
      },
    })
  },

  openChatCreate() {
    this.openChatPrompt({
      currentTarget: {
        dataset: {
          prompt: '/chores add 周末大扫除',
          title: '新增家务',
        },
      },
    })
  },
})
