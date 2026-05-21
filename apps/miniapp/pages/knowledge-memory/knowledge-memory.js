const { request } = require('../../utils/request')

const CATEGORY_OPTIONS = [
  { label: '全部分类', value: 'all' },
  { label: '通用', value: 'general' },
  { label: '健康', value: 'health' },
  { label: '烹饪', value: 'cooking' },
  { label: '教育', value: 'education' },
  { label: '财务', value: 'finance' },
  { label: '旅行', value: 'travel' },
  { label: '法律', value: 'legal' },
  { label: '关系', value: 'relationship' },
]

const MEMORY_TYPES = [
  { label: '全部', value: 'all' },
  { label: '长期事实', value: 'long_term' },
  { label: '情景记忆', value: 'episodic' },
  { label: '摘要', value: 'summary' },
  { label: '短期', value: 'short_term' },
  { label: '工作记忆', value: 'working' },
]

function normalize(value) {
  return String(value || '').trim()
}

function parseTags(value) {
  return normalize(value)
    .replace(/，/g, ',')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function parseMaybeList(value) {
  if (Array.isArray(value)) return value.filter(Boolean)
  if (!value) return []
  if (typeof value === 'string') {
    try {
      const parsed = JSON.parse(value)
      if (Array.isArray(parsed)) return parsed.filter(Boolean)
    } catch (err) {}
    return value
      .replace(/，/g, ',')
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean)
  }
  return []
}

function formatDate(value) {
  if (!value) return '未记录'
  const text = String(value)
  const match = text.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (!match) return text.slice(0, 10) || '未记录'
  return `${match[1]}年${match[2]}月${match[3]}日`
}

function truncate(value, maxLength) {
  const text = normalize(value)
  if (text.length <= maxLength) return text
  return `${text.slice(0, maxLength)}...`
}

function findOptionIndex(options, value) {
  const index = options.findIndex((item) => item.value === value)
  return index >= 0 ? index : 0
}

function getCategoryLabel(value) {
  const option = CATEGORY_OPTIONS.find((item) => item.value === value)
  return option ? option.label : normalize(value) || '未分类'
}

function getMemoryTypeLabel(value) {
  const option = MEMORY_TYPES.find((item) => item.value === value)
  return option ? option.label : normalize(value) || '未知类型'
}

function buildDocumentCard(doc) {
  const tags = Array.isArray(doc.tags) ? doc.tags : []
  return {
    ...doc,
    id: doc.doc_id,
    title_text: normalize(doc.title) || '未命名知识',
    category_text: getCategoryLabel(doc.category),
    file_type_text: normalize(doc.file_type) || '.txt',
    date_text: formatDate(doc.upload_time),
    chunk_text: `${Number(doc.chunk_count || 0)} 段`,
    description_text: normalize(doc.description) || '未填写描述',
    tags,
    tags_text: tags.length ? tags.join('、') : '暂无标签',
  }
}

function buildSearchResultCard(item, index) {
  const metadata = item.metadata || {}
  const tags = parseMaybeList(metadata.tags)
  return {
    id: `${metadata.doc_id || 'result'}_${index}`,
    title_text: normalize(metadata.title) || `搜索结果 ${index + 1}`,
    category_text: getCategoryLabel(metadata.category),
    content_text: truncate(item.content, 220),
    source_text: normalize(metadata.source) || '知识库',
    tags,
    tags_text: tags.length ? tags.join('、') : '暂无标签',
  }
}

function buildMemoryCard(item) {
  const tags = Array.isArray(item.tags) ? item.tags : []
  const importance = Number(item.importance || 0)
  return {
    ...item,
    title_text: getMemoryTypeLabel(item.memory_type),
    content_text: normalize(item.content) || '空记忆',
    date_text: formatDate(item.timestamp),
    importance_text: importance.toFixed(2),
    tags,
    tags_text: tags.length ? tags.join('、') : '暂无标签',
    source_text: normalize(item.source) || '系统',
  }
}

function buildStatsCards(knowledgeTotal, memoryStats) {
  return [
    { key: 'docs', label: '知识文档', value: String(knowledgeTotal || 0) },
    { key: 'long', label: '长期记忆', value: String(memoryStats.long_term_count || 0) },
    { key: 'short', label: '短期记忆', value: String(memoryStats.short_term_count || 0) },
    { key: 'summary', label: '会话摘要', value: String(memoryStats.summary_count || 0) },
  ]
}

Page({
  data: {
    loading: true,
    saving: false,
    activeTab: 'knowledge',
    activeTabLabel: '知识库',
    familyId: '',
    memberName: '',
    statCards: buildStatsCards(0, {}),
    chatPrompts: [
      { title: '查家庭资料', prompt: '/knowledge 家庭资料', desc: '从知识库找答案' },
      { title: '查家庭记忆', prompt: '/memory 车辆保养', desc: '检索长期记忆' },
      { title: '沉淀资料', prompt: '/knowledge add 宝宝过敏史', desc: '让 Chat 帮你归档' },
    ],
    categoryOptions: CATEGORY_OPTIONS,
    categoryIndex: 0,
    categoryLabel: '全部分类',
    selectedCategory: 'all',
    knowledgeQuery: '',
    documents: [],
    searchResults: [],
    hasKnowledgeSearch: false,
    documentCountText: '0',
    searchCountText: '0',
    noDocuments: false,
    noSearchResults: false,
    formTitle: '',
    formContent: '',
    formTags: '',
    formCategoryIndex: 1,
    formCategory: 'general',
    formCategoryLabel: '通用',
    detailVisible: false,
    detailLoading: false,
    detailTitle: '',
    detailMeta: '',
    detailContent: '',
    detailTagsText: '',
    memoryTypes: MEMORY_TYPES,
    memoryTypeIndex: 0,
    memoryTypeLabel: '全部',
    memoryType: 'all',
    memoryQuery: '',
    memories: [],
    memoryCountText: '0',
    noMemories: false,
    memoryStats: {},
    editingMemoryId: '',
    editMemoryVisible: false,
    editContent: '',
    editImportance: '0.50',
    editTags: '',
  },

  onLoad() {
    wx.setNavigationBarTitle({ title: '家庭记忆' })
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
    if (this.data.familyId) this.refresh()
  },

  refresh() {
    this.setData({ loading: true })
    Promise.all([
      this.loadDocuments(),
      this.loadMemories(),
    ])
      .then(([documentData, memoryData]) => {
        const documents = (documentData.documents || []).map(buildDocumentCard)
        const memories = (memoryData.items || []).map(buildMemoryCard)
        const stats = memoryData.stats || {}
        this.setData({
          documents,
          memories,
          memoryStats: stats,
          documentCountText: String(documentData.total || documents.length),
          memoryCountText: String(memories.length),
          noDocuments: documents.length === 0,
          noMemories: memories.length === 0,
          statCards: buildStatsCards(documentData.total || documents.length, stats),
        })
      })
      .catch(() => {})
      .then(() => this.setData({ loading: false }))
  },

  loadDocuments() {
    const category = this.data.selectedCategory === 'all' ? '' : this.data.selectedCategory
    const params = { limit: 100 }
    if (category) {
      params.category = category
    }
    return request({
      path: '/api/knowledge/list',
      method: 'GET',
      data: params,
    }).then((data) => ({
      documents: data.documents || [],
      total: Number(data.total || 0),
    })).catch(() => ({ documents: [], total: 0 }))
  },

  loadMemories() {
    return request({
      path: '/api/memory',
      method: 'GET',
      data: {
        query: normalize(this.data.memoryQuery),
        memory_type: this.data.memoryType,
        limit: 200,
        user_id: this.data.memberName,
        family_id: this.data.familyId,
      },
    }).then((data) => ({
      items: data.items || [],
      stats: data.stats || {},
    })).catch(() => ({ items: [], stats: {} }))
  },

  switchTab(e) {
    const tab = e.currentTarget.dataset.tab || 'knowledge'
    this.setData({
      activeTab: tab,
      activeTabLabel: tab === 'knowledge' ? '知识库' : 'AI 记忆',
    })
  },

  changeCategory(e) {
    const index = Number(e.detail.value || 0)
    const option = this.data.categoryOptions[index] || this.data.categoryOptions[0]
    this.setData({
      categoryIndex: index,
      selectedCategory: option.value,
      categoryLabel: option.label,
    }, () => this.refresh())
  },

  changeFormCategory(e) {
    const index = Number(e.detail.value || 0)
    const option = this.data.categoryOptions[index] || this.data.categoryOptions[1]
    this.setData({
      formCategoryIndex: index,
      formCategory: option.value === 'all' ? 'general' : option.value,
      formCategoryLabel: option.value === 'all' ? '通用' : option.label,
    })
  },

  setField(e) {
    const { field } = e.currentTarget.dataset
    this.setData({ [field]: e.detail.value })
  },

  searchKnowledge() {
    const query = normalize(this.data.knowledgeQuery)
    if (!query) {
      wx.showToast({ title: '请输入搜索内容', icon: 'none' })
      return
    }
    this.setData({ loading: true, hasKnowledgeSearch: true })
    request({
      path: '/api/knowledge/search',
      method: 'GET',
      data: {
        query,
        ...(this.data.selectedCategory === 'all' ? {} : { category: this.data.selectedCategory }),
        limit: 10,
      },
    })
      .then((data) => {
        const searchResults = (data.results || []).map(buildSearchResultCard)
        this.setData({
          searchResults,
          searchCountText: String(searchResults.length),
          noSearchResults: searchResults.length === 0,
        })
      })
      .catch(() => {})
      .then(() => this.setData({ loading: false }))
  },

  clearKnowledgeSearch() {
    this.setData({
      knowledgeQuery: '',
      searchResults: [],
      hasKnowledgeSearch: false,
      searchCountText: '0',
      noSearchResults: false,
    })
  },

  addKnowledge() {
    const title = normalize(this.data.formTitle)
    const content = normalize(this.data.formContent)
    if (!title || !content) {
      wx.showToast({ title: '请填写标题和内容', icon: 'none' })
      return
    }
    this.setData({ saving: true })
    request({
      path: '/api/knowledge/add',
      method: 'POST',
      data: {
        title,
        content,
        category: this.data.formCategory,
        tags: parseTags(this.data.formTags),
      },
    })
      .then((data) => {
        if (data && data.success) {
          wx.showToast({ title: '已添加', icon: 'success' })
          this.setData({
            formTitle: '',
            formContent: '',
            formTags: '',
            formCategoryIndex: 1,
            formCategory: 'general',
            formCategoryLabel: '通用',
          })
          this.refresh()
          return
        }
        wx.showToast({ title: '添加失败', icon: 'none' })
      })
      .catch(() => {})
      .then(() => this.setData({ saving: false }))
  },

  openDocumentDetail(e) {
    const docId = e.currentTarget.dataset.id
    if (!docId) return
    this.setData({ detailVisible: true, detailLoading: true })
    request({
      path: `/api/knowledge/detail/${encodeURIComponent(docId)}`,
      method: 'GET',
    })
      .then((data) => {
        const doc = data.document || {}
        const tags = Array.isArray(doc.tags) ? doc.tags : []
        this.setData({
          detailTitle: normalize(doc.title) || '知识详情',
          detailMeta: `${getCategoryLabel(doc.category)} · ${formatDate(doc.upload_time)} · ${Number(doc.chunk_count || 0)} 段`,
          detailContent: normalize(doc.content) || '暂无内容',
          detailTagsText: tags.length ? tags.join('、') : '暂无标签',
        })
      })
      .catch(() => {
        this.setData({
          detailTitle: '知识详情',
          detailMeta: '',
          detailContent: '加载失败',
          detailTagsText: '',
        })
      })
      .then(() => this.setData({ detailLoading: false }))
  },

  closeDetail() {
    this.setData({ detailVisible: false })
  },

  changeMemoryType(e) {
    const index = Number(e.detail.value || 0)
    const option = this.data.memoryTypes[index] || this.data.memoryTypes[0]
    this.setData({
      memoryTypeIndex: index,
      memoryType: option.value,
      memoryTypeLabel: option.label,
    }, () => this.refresh())
  },

  searchMemory() {
    this.refresh()
  },

  clearMemorySearch() {
    this.setData({ memoryQuery: '' }, () => this.refresh())
  },

  openEditMemory(e) {
    const id = e.currentTarget.dataset.id
    const memory = this.data.memories.find((item) => item.id === id)
    if (!memory) return
    this.setData({
      editMemoryVisible: true,
      editingMemoryId: id,
      editContent: memory.content || memory.content_text || '',
      editImportance: String(Number(memory.importance || 0.5).toFixed(2)),
      editTags: (memory.tags || []).join(','),
    })
  },

  closeEditMemory() {
    this.setData({ editMemoryVisible: false, editingMemoryId: '' })
  },

  saveMemory() {
    const id = this.data.editingMemoryId
    const content = normalize(this.data.editContent)
    if (!id || !content) {
      wx.showToast({ title: '请填写记忆内容', icon: 'none' })
      return
    }
    this.setData({ saving: true })
    request({
      path: `/api/memory/${encodeURIComponent(id)}?user_id=${encodeURIComponent(this.data.memberName)}&family_id=${encodeURIComponent(this.data.familyId)}`,
      method: 'PUT',
      data: {
        content,
        importance: Number(this.data.editImportance || 0.5),
        tags: parseTags(this.data.editTags),
      },
    })
      .then((data) => {
        if (data && data.success) {
          wx.showToast({ title: '已保存', icon: 'success' })
          this.closeEditMemory()
          this.refresh()
          return
        }
        wx.showToast({ title: '保存失败', icon: 'none' })
      })
      .catch(() => {})
      .then(() => this.setData({ saving: false }))
  },

  deleteMemory(e) {
    const id = e.currentTarget.dataset.id
    if (!id) return
    wx.showModal({
      title: '删除记忆',
      content: '确认删除这条 AI 记忆？',
      confirmText: '删除',
      success: (res) => {
        if (!res.confirm) return
        request({
          path: `/api/memory/${encodeURIComponent(id)}?user_id=${encodeURIComponent(this.data.memberName)}&family_id=${encodeURIComponent(this.data.familyId)}`,
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
    const prompt = e.currentTarget.dataset.prompt || '/memory'
    const title = e.currentTarget.dataset.title || '家庭记忆'
    const route = `/chat?prompt=${encodeURIComponent(prompt)}`
    wx.navigateTo({
      url: `/pages/webview/webview?route=${encodeURIComponent(route)}&title=${encodeURIComponent(title)}`,
    })
  },
})
