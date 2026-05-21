const { request } = require('../../utils/request')

function todayParts() {
  const now = new Date()
  return {
    year: now.getFullYear(),
    month: now.getMonth() + 1,
    date: `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`,
  }
}

function normalize(value) {
  return String(value || '').trim()
}

function formatYuan(value) {
  const num = Number(value || 0)
  return `¥${num.toFixed(2)}`
}

function buildMonthLabel(year, month) {
  return `${year}年${String(month).padStart(2, '0')}月`
}

function buildMonthValue(year, month) {
  return `${year}-${String(month).padStart(2, '0')}`
}

function getTypeLabel(value) {
  if (value === 'income') return '收入'
  if (value === 'expense') return '支出'
  return '全部类型'
}

function getTypeIndex(value) {
  if (value === 'income') return 1
  if (value === 'expense') return 2
  return 0
}

function getFormTypeLabel(value) {
  return value === 'income' ? '收入' : '支出'
}

const today = todayParts()

Page({
  data: {
    loading: true,
    saving: false,
    summary: {
      total_income: 0,
      total_expense: 0,
      balance: 0,
      total_income_text: '¥0.00',
      total_expense_text: '¥0.00',
      balance_text: '¥0.00',
      income_breakdown: [],
      expense_breakdown: [],
    },
    transactions: { items: [], total: 0, page: 1, page_size: 12 },
    transactionCountText: '0',
    hasTransactions: false,
    noTransactions: false,
    categories: { income: [], expense: [] },
    trend: [],
    filters: {
      year: today.year,
      month: today.month,
      transaction_type: '',
      category: '',
    },
    pagination: {
      current: 1,
      pageSize: 12,
      total: 0,
    },
    familyId: '',
    memberName: '',
    monthLabel: buildMonthLabel(today.year, today.month),
    monthValue: buildMonthValue(today.year, today.month),
    filterTypeIndex: 0,
    filterTypeLabel: '全部类型',
    filterCategoryIndex: 0,
    filterCategoryLabel: '全部分类',
    pagerText: '1 / 1',
    prevPage: 1,
    nextPage: 1,
    prevDisabled: true,
    nextDisabled: true,
    transactionTypeOptions: [
      { label: '全部', value: '' },
      { label: '收入', value: 'income' },
      { label: '支出', value: 'expense' },
    ],
    filterCategoryOptions: [{ label: '全部分类', value: '' }],
    formCategoryOptions: [{ label: '请选择分类', value: '' }],
    chartItems: [],
    chartLabel: '暂无趋势',
    chatPrompts: [
      { title: '记一笔支出', prompt: '/finance 支出 68 餐饮 今晚吃饭', desc: '一句话记账' },
      { title: '看本月汇总', prompt: '/finance summary', desc: '查看月度统计' },
      { title: '查财务趋势', prompt: '/finance trend', desc: '看近几个月变化' },
    ],
    formVisible: false,
    editingId: '',
    formTitle: '新增记录',
    formResetText: '清空',
    formAmount: '',
    formType: 'expense',
    formTypeLabel: '支出',
    formCategory: '',
    formCategoryLabel: '请选择分类',
    formDescription: '',
    formDate: today.date,
    formCreatedBy: '',
    formTypeIndex: 1,
    formCategoryIndex: 0,
    formTypeChoices: ['income', 'expense'],
    formTypeLabels: ['收入', '支出'],
    formDateLabel: today.date,
  },

  onLoad() {
    wx.setNavigationBarTitle({ title: '家庭财务' })
    const memberName = wx.getStorageSync('member_name') || ''
    const familyId = wx.getStorageSync('family_id') || ''
    if (!memberName || !familyId) {
      wx.redirectTo({ url: '/pages/auth/auth' })
      return
    }
    this.setData({
      memberName,
      familyId,
      formCreatedBy: memberName,
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
    Promise.all([
      this.loadSummary(),
      this.loadTransactions(),
      this.loadCategories(),
      this.loadTrend(),
    ])
      .then(([summary, transactions, categories, trend]) => {
        const filterCategoryOptions = this.buildFilterCategoryOptions(categories, this.data.filters.transaction_type)
        const filterCategoryIndex = this.findOptionIndex(filterCategoryOptions, this.data.filters.category)
        const selectedCategory = filterCategoryOptions[filterCategoryIndex] || filterCategoryOptions[0]
        const chartItems = this.buildChartItems(trend)
        const pager = this.buildPager(transactions.total || 0, this.data.pagination.current, this.data.pagination.pageSize)
        const formCategoryState = this.buildFormCategoryState(categories, this.data.formType, this.data.formCategory)
        const transactionItems = transactions.items || []

        this.setData({
          summary,
          transactions: {
            ...transactions,
            items: transactionItems,
          },
          transactionCountText: String(transactionItems.length),
          hasTransactions: transactionItems.length > 0,
          noTransactions: transactionItems.length === 0,
          categories,
          trend,
          filters: {
            ...this.data.filters,
            category: selectedCategory.value,
          },
          filterCategoryOptions,
          filterCategoryIndex,
          filterCategoryLabel: selectedCategory.label,
          formCategoryOptions: formCategoryState.options,
          formCategoryIndex: formCategoryState.index,
          formCategory: formCategoryState.value,
          formCategoryLabel: formCategoryState.label,
          chartItems,
          chartLabel: chartItems.length ? chartItems[0].month_text : '暂无趋势',
          monthLabel: buildMonthLabel(this.data.filters.year, this.data.filters.month),
          monthValue: buildMonthValue(this.data.filters.year, this.data.filters.month),
          filterTypeIndex: getTypeIndex(this.data.filters.transaction_type),
          filterTypeLabel: getTypeLabel(this.data.filters.transaction_type),
          pagerText: pager.text,
          prevPage: pager.prevPage,
          nextPage: pager.nextPage,
          prevDisabled: pager.prevDisabled,
          nextDisabled: pager.nextDisabled,
          pagination: {
            ...this.data.pagination,
            current: pager.current,
            total: transactions.total || 0,
            pageSize: transactions.page_size || this.data.pagination.pageSize,
          },
        })
      })
      .catch(() => {})
      .then(() => this.setData({ loading: false }))
  },

  loadSummary() {
    return request({
      path: '/api/finance/summary',
      method: 'GET',
      data: {
        year: this.data.filters.year,
        month: this.data.filters.month,
      },
    }).then((data) => ({
      total_income: Number(data.total_income || 0),
      total_expense: Number(data.total_expense || 0),
      balance: Number(data.balance || 0),
      total_income_text: formatYuan(data.total_income || 0),
      total_expense_text: formatYuan(data.total_expense || 0),
      balance_text: formatYuan(data.balance || 0),
      income_breakdown: data.income_breakdown || [],
      expense_breakdown: data.expense_breakdown || [],
    })).catch(() => ({
      total_income: 0,
      total_expense: 0,
      balance: 0,
      total_income_text: '¥0.00',
      total_expense_text: '¥0.00',
      balance_text: '¥0.00',
      income_breakdown: [],
      expense_breakdown: [],
    }))
  },

  loadTransactions() {
    return request({
      path: '/api/finance/transactions',
      method: 'GET',
      data: {
        year: this.data.filters.year,
        month: this.data.filters.month,
        transaction_type: this.data.filters.transaction_type || undefined,
        category: this.data.filters.category || undefined,
        page: this.data.pagination.current,
        page_size: this.data.pagination.pageSize,
      },
    }).then((data) => ({
      items: (data.items || []).map((item) => ({
        ...item,
        amount_text: formatYuan(item.amount),
        sign_text: item.transaction_type === 'income' ? '+' : '-',
        type_text: item.transaction_type === 'income' ? '收入' : '支出',
        date_text: String(item.transaction_date || '').slice(5, 10) || '00-00',
        creator_text: normalize(item.created_by) || '未记录',
        description_text: normalize(item.description) || '无描述',
      })),
      total: Number(data.total || 0),
      page: Number(data.page || this.data.pagination.current),
      page_size: Number(data.page_size || this.data.pagination.pageSize),
    })).catch(() => ({
      items: [],
      total: 0,
      page: this.data.pagination.current,
      page_size: this.data.pagination.pageSize,
    }))
  },

  loadCategories() {
    return request({
      path: '/api/finance/categories',
      method: 'GET',
    }).then((data) => ({
      income: data.income || [],
      expense: data.expense || [],
    })).catch(() => ({ income: [], expense: [] }))
  },

  loadTrend() {
    return request({
      path: '/api/finance/trend',
      method: 'GET',
      data: { months: 6 },
    }).then((data) => data || []).catch(() => [])
  },

  buildFilterCategoryOptions(categories, transactionType) {
    const income = categories.income || []
    const expense = categories.expense || []
    const list = transactionType === 'income'
      ? income
      : transactionType === 'expense'
        ? expense
        : income.concat(expense)
    const uniqueList = list.filter((item, index) => list.indexOf(item) === index)
    return [{ label: '全部分类', value: '' }].concat(uniqueList.map((item) => ({ label: item, value: item })))
  },

  buildFormCategoryOptions(categories, transactionType) {
    const list = transactionType === 'income' ? categories.income || [] : categories.expense || []
    return [{ label: '请选择分类', value: '' }].concat(list.map((item) => ({ label: item, value: item })))
  },

  buildFormCategoryState(categories, transactionType, category) {
    const options = this.buildFormCategoryOptions(categories, transactionType)
    const index = this.findOptionIndex(options, category)
    const option = options[index] || options[0]
    return {
      options,
      index,
      value: option.value,
      label: option.label,
    }
  },

  buildChartItems(trend) {
    return (trend || []).map((item) => ({
      ...item,
      month_text: `${String(item.month_num || '').padStart(2, '0')}月`,
      income_text: formatYuan(item.income || 0),
      expense_text: formatYuan(item.expense || 0),
    }))
  },

  findOptionIndex(options, value) {
    const index = options.findIndex((item) => item.value === value)
    return index >= 0 ? index : 0
  },

  buildPager(total, current, pageSize) {
    const totalPages = Math.max(1, Math.ceil(Number(total || 0) / Number(pageSize || 1)))
    const page = Math.min(Math.max(1, Number(current || 1)), totalPages)
    return {
      current: page,
      text: `${page} / ${totalPages}`,
      prevPage: Math.max(1, page - 1),
      nextPage: Math.min(totalPages, page + 1),
      prevDisabled: page <= 1,
      nextDisabled: page >= totalPages,
    }
  },

  setField(e) {
    const { field } = e.currentTarget.dataset
    this.setData({ [field]: e.detail.value })
  },

  changeMonth(e) {
    const value = e.detail.value || ''
    const parts = value.split('-')
    if (parts.length !== 2) return
    const year = Number(parts[0])
    const month = Number(parts[1])
    this.setData({
      filters: {
        ...this.data.filters,
        year,
        month,
      },
      pagination: {
        ...this.data.pagination,
        current: 1,
      },
      monthLabel: buildMonthLabel(year, month),
      monthValue: buildMonthValue(year, month),
    }, () => this.refresh())
  },

  changeTransactionType(e) {
    const index = Number(e.detail.value || 0)
    const option = this.data.transactionTypeOptions[index] || this.data.transactionTypeOptions[0]
    const value = option.value
    const filterCategoryOptions = this.buildFilterCategoryOptions(this.data.categories, value)
    this.setData({
      filters: {
        ...this.data.filters,
        transaction_type: value,
        category: '',
      },
      filterTypeIndex: index,
      filterTypeLabel: getTypeLabel(value),
      filterCategoryOptions,
      filterCategoryIndex: 0,
      filterCategoryLabel: '全部分类',
      pagination: {
        ...this.data.pagination,
        current: 1,
      },
    }, () => this.refresh())
  },

  changeCategory(e) {
    const index = Number(e.detail.value || 0)
    const option = this.data.filterCategoryOptions[index] || this.data.filterCategoryOptions[0]
    this.setData({
      filters: {
        ...this.data.filters,
        category: option.value,
      },
      filterCategoryIndex: index,
      filterCategoryLabel: option.label,
      pagination: {
        ...this.data.pagination,
        current: 1,
      },
    }, () => this.refresh())
  },

  changePage(e) {
    const page = Number(e.currentTarget.dataset.page || 1)
    if (page === this.data.pagination.current) return
    this.setData({
      pagination: {
        ...this.data.pagination,
        current: page,
      },
    }, () => this.refresh())
  },

  openChatFinance() {
    const route = `/chat?prompt=${encodeURIComponent('/finance summary')}`
    wx.navigateTo({
      url: `/pages/webview/webview?route=${encodeURIComponent(route)}&title=${encodeURIComponent('家庭财务')}`,
    })
  },

  openQuickAdd() {
    const formCategoryState = this.buildFormCategoryState(this.data.categories, 'expense', '')
    this.setData({
      formVisible: true,
      editingId: '',
      formTitle: '新增记录',
      formResetText: '清空',
      formAmount: '',
      formType: 'expense',
      formTypeLabel: '支出',
      formCategory: '',
      formCategoryOptions: formCategoryState.options,
      formCategoryIndex: formCategoryState.index,
      formCategoryLabel: formCategoryState.label,
      formDescription: '',
      formDate: todayParts().date,
      formCreatedBy: this.data.memberName,
      formTypeIndex: 1,
      formDateLabel: todayParts().date,
    })
  },

  closeForm() {
    this.setData({ formVisible: false, editingId: '' })
  },

  openEdit(e) {
    const id = e.currentTarget.dataset.id
    const tx = this.data.transactions.items.find((item) => String(item.id) === String(id))
    if (!tx) return
    const type = tx.transaction_type || 'expense'
    const typeIndex = type === 'income' ? 0 : 1
    const formCategoryState = this.buildFormCategoryState(this.data.categories, type, tx.category || '')
    this.setData({
      formVisible: true,
      editingId: tx.id,
      formTitle: '编辑记录',
      formResetText: '重置',
      formAmount: String(tx.amount || ''),
      formType: type,
      formTypeLabel: getFormTypeLabel(type),
      formCategory: formCategoryState.value,
      formCategoryOptions: formCategoryState.options,
      formCategoryIndex: formCategoryState.index,
      formCategoryLabel: formCategoryState.label,
      formDescription: tx.description || '',
      formDate: tx.transaction_date || todayParts().date,
      formCreatedBy: tx.created_by || this.data.memberName,
      formTypeIndex: typeIndex,
      formDateLabel: tx.transaction_date || todayParts().date,
    })
  },

  changeFormType(e) {
    const index = Number(e.detail.value)
    const type = this.data.formTypeChoices[index] || 'expense'
    const formCategoryState = this.buildFormCategoryState(this.data.categories, type, '')
    this.setData({
      formTypeIndex: index,
      formType: type,
      formTypeLabel: getFormTypeLabel(type),
      formCategory: formCategoryState.value,
      formCategoryOptions: formCategoryState.options,
      formCategoryIndex: formCategoryState.index,
      formCategoryLabel: formCategoryState.label,
    })
  },

  changeFormCategory(e) {
    const index = Number(e.detail.value)
    const option = this.data.formCategoryOptions[index] || this.data.formCategoryOptions[0]
    this.setData({
      formCategoryIndex: index,
      formCategory: option.value,
      formCategoryLabel: option.label,
    })
  },

  changeFormDate(e) {
    this.setData({
      formDate: e.detail.value,
      formDateLabel: e.detail.value,
    })
  },

  saveTransaction() {
    const amount = Number(this.data.formAmount || 0)
    const category = normalize(this.data.formCategory)
    const description = normalize(this.data.formDescription)
    if (!amount || amount <= 0) {
      wx.showToast({ title: '请输入金额', icon: 'none' })
      return
    }
    if (!category) {
      wx.showToast({ title: '请选择分类', icon: 'none' })
      return
    }
    this.setData({ saving: true })
    const payload = {
      amount,
      transaction_type: this.data.formType,
      category,
      description,
      transaction_date: this.data.formDate,
      created_by: normalize(this.data.formCreatedBy) || this.data.memberName,
    }
    const action = this.data.editingId
      ? request({
          path: `/api/finance/transactions/${encodeURIComponent(this.data.editingId)}`,
          method: 'PUT',
          data: payload,
        })
      : request({
          path: '/api/finance/transactions',
          method: 'POST',
          data: payload,
        })
    action
      .then((data) => {
        if (data && data.success) {
          wx.showToast({ title: this.data.editingId ? '已更新' : '已添加', icon: 'success' })
          this.closeForm()
          this.refresh()
          return
        }
        wx.showToast({ title: (data && data.message) || '保存失败', icon: 'none' })
      })
      .catch(() => {})
      .then(() => this.setData({ saving: false }))
  },

  deleteTransaction(e) {
    const id = e.currentTarget.dataset.id
    if (!id) return
    wx.showModal({
      title: '删除记录',
      content: '确认删除这条财务记录？',
      confirmText: '删除',
      success: (res) => {
        if (!res.confirm) return
        request({
          path: `/api/finance/transactions/${encodeURIComponent(id)}`,
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
})
