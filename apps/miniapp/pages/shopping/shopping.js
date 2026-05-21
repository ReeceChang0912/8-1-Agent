const { request } = require('../../utils/request')

const CATEGORY_LABELS = {
  food: '食品食材',
  daily: '日用品',
  health: '医药保健',
  home: '家居用品',
  electronics: '电子产品',
  clothing: '服装鞋帽',
  other: '其他',
  general: '其他',
}

Page({
  data: {
    loading: true,
    submitting: false,
    items: [],
    pendingItems: [],
    purchasedItems: [],
    restockItems: [],
    familyId: '',
    memberName: '',
    itemName: '',
    itemQuantity: '1',
    stats: {
      total_items: 0,
      unpurchased: 0,
      purchased: 0,
      restock_needed: 0,
    },
  },

  onLoad() {
    wx.setNavigationBarTitle({ title: '购物清单' })
    const memberName = wx.getStorageSync('member_name') || ''
    const familyId = wx.getStorageSync('family_id') || ''
    if (!memberName || !familyId) {
      wx.redirectTo({ url: '/pages/auth/auth' })
      return
    }
    this.setData({ memberName, familyId })
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

  refresh() {
    this.setData({ loading: true })
    Promise.all([this.loadItems(), this.loadStats()])
      .then(() => {})
      .catch(() => {})
      .then(() => this.setData({ loading: false }))
  },

  loadItems() {
    return request({
      path: '/api/shopping',
      method: 'GET',
      data: { family_id: this.data.familyId },
    }).then((data) => {
      const items = (data.items || []).map((item) => {
        const currentStock = Number(item.current_stock || 0)
        const threshold = Number(item.restock_threshold || 0)
        const purchased = item.purchased || item.status === 'purchased'
        return {
          ...item,
          purchased,
          category_text: CATEGORY_LABELS[item.category] || item.category || '其他',
          quantity_text: `${item.quantity || '1'} ${item.unit || '件'}`,
          priority_text: item.priority === 'high' ? '重要' : item.priority === 'low' ? '低优先' : '普通',
          added_by_text: item.added_by || '未记录',
          is_restock: !purchased && currentStock <= threshold && threshold > 0,
        }
      })
      this.setData({
        items,
        pendingItems: items.filter((item) => !item.purchased),
        purchasedItems: items.filter((item) => item.purchased),
        restockItems: items.filter((item) => item.is_restock),
      })
    })
  },

  loadStats() {
    return request({
      path: '/api/shopping/stats',
      method: 'GET',
      data: { family_id: this.data.familyId },
    }).then((data) => {
      this.setData({
        stats: {
          total_items: data.total_items || 0,
          unpurchased: data.unpurchased || 0,
          purchased: data.purchased || 0,
          restock_needed: data.restock_needed || 0,
        },
      })
    })
  },

  addItem() {
    const name = this.data.itemName.trim()
    if (!name) {
      wx.showToast({ title: '请输入物品名称', icon: 'none' })
      return
    }
    this.setData({ submitting: true })
    request({
      path: '/api/shopping',
      method: 'POST',
      data: {
        name,
        quantity: this.data.itemQuantity || '1',
        unit: '件',
        category: 'daily',
        priority: 'normal',
        notes: '',
        added_by: this.data.memberName,
        family_id: this.data.familyId,
      },
    })
      .then((data) => {
        if (data && data.success) {
          wx.showToast({ title: '已加入清单', icon: 'success' })
          this.setData({ itemName: '', itemQuantity: '1' })
          this.refresh()
          return
        }
        wx.showToast({ title: (data && data.message) || '添加失败', icon: 'none' })
      })
      .catch(() => {})
      .then(() => this.setData({ submitting: false }))
  },

  toggleItem(e) {
    const itemId = e.currentTarget.dataset.itemid
    if (!itemId) return
    request({
      path: `/api/shopping/${encodeURIComponent(itemId)}/toggle?family_id=${encodeURIComponent(this.data.familyId)}`,
      method: 'POST',
    })
      .then((data) => {
        if (data && data.success) {
          this.refresh()
          return
        }
        wx.showToast({ title: '操作失败', icon: 'none' })
      })
      .catch(() => {})
  },

  openChatAdd() {
    wx.navigateTo({
      url: `/pages/webview/webview?route=${encodeURIComponent('/chat?prompt=/shopping ')}&title=${encodeURIComponent('添加采购')}`,
    })
  },
})
