const { request } = require('../../utils/request')
const { isPlaceholderUrl } = require('../../config/index')

function normalize(value) {
  return String(value || '').trim()
}

function formatDate(value) {
  if (!value) return '未记录日期'
  const text = String(value)
  const match = text.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (!match) return text.slice(0, 10) || '未记录日期'
  return `${match[1]}年${match[2]}月${match[3]}日`
}

function formatShortDate(value) {
  if (!value) return '未记录'
  const text = String(value)
  const match = text.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (!match) return text.slice(0, 10) || '未记录'
  return `${match[2]}.${match[3]}`
}

function getBaseUrl() {
  const app = getApp()
  return String((app.globalData && app.globalData.apiBaseUrl) || '').replace(/\/+$/, '')
}

function buildPhotoUrl(photo) {
  if (photo.oss_url) return photo.oss_url
  if (!photo.filename) return ''
  return `${getBaseUrl()}/api/photos/${encodeURIComponent(photo.filename)}`
}

function asList(value) {
  return Array.isArray(value) ? value.filter(Boolean) : []
}

function buildPhotoCard(photo) {
  const tags = asList(photo.tags)
  const people = asList(photo.people)
  const chips = [
    ...people.map((item) => `人物 ${item}`),
    ...tags.map((item) => `#${item}`),
    normalize(photo.event),
    normalize(photo.location),
  ].filter(Boolean).slice(0, 5)

  return {
    ...photo,
    image_url: buildPhotoUrl(photo),
    title_text: normalize(photo.description) || normalize(photo.event) || normalize(photo.filename) || '家庭照片',
    date_text: formatDate(photo.upload_date),
    short_date_text: formatShortDate(photo.upload_date),
    location_text: normalize(photo.location) || '未记录地点',
    people_text: people.length ? people.join('、') : '未识别人物',
    tags_text: tags.length ? tags.join('、') : '待补充标签',
    mood_text: normalize(photo.mood) || '未标注',
    chips,
  }
}

function buildAlbumCard(album) {
  return {
    ...album,
    type_text: album.type === 'person' ? '人物相册' : album.type === 'event' ? '事件相册' : '时间相册',
    count_text: `${Number(album.photo_count || 0)} 张`,
  }
}

function buildStatsCards(stats, totalFromList) {
  const total = Number(stats.total_photos || totalFromList || 0)
  const annotated = Number(stats.annotated_photos || 0)
  const unannotated = Number(stats.unannotated_photos || 0)
  const rate = Number(stats.annotation_rate || 0)
  return [
    { key: 'total', label: '照片总数', value: String(total) },
    { key: 'annotated', label: '已标注', value: String(annotated) },
    { key: 'todo', label: '待分析', value: String(unannotated) },
    { key: 'rate', label: '标注率', value: `${rate}%` },
  ]
}

function buildUploadPayload(pageData) {
  return {
    description: normalize(pageData.uploadDescription),
    tags: normalize(pageData.uploadTags),
    people: normalize(pageData.uploadPeople),
    location: normalize(pageData.uploadLocation),
  }
}

Page({
  data: {
    loading: true,
    uploading: false,
    analyzing: false,
    photos: [],
    albums: [],
    stats: {
      total_photos: 0,
      annotated_photos: 0,
      unannotated_photos: 0,
      annotation_rate: 0,
    },
    statCards: buildStatsCards({}, 0),
    searchKeyword: '',
    resultCountText: '0',
    noPhotos: false,
    albumCountText: '0',
    noAlbums: false,
    memberName: '',
    familyId: '',
    uploadDescription: '',
    uploadTags: '',
    uploadPeople: '',
    uploadLocation: '',
    chatPrompts: [
      { title: '搜索回忆', prompt: '/photo 搜索 去年生日', desc: '按人物、标签、描述找照片' },
      { title: '生成相册', prompt: '/photo albums', desc: '让 Chat 整理照片主题' },
      { title: '回忆故事', prompt: '/photo story 家庭旅行', desc: '把照片串成故事' },
    ],
  },

  onLoad() {
    wx.setNavigationBarTitle({ title: '照片记忆' })
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
      this.loadPhotos(this.data.searchKeyword),
      this.loadStats(),
      this.loadAlbums(),
    ])
      .then(([photoData, stats, albums]) => {
        const photos = (photoData.photos || []).map(buildPhotoCard)
        const albumCards = (albums || []).map(buildAlbumCard)
        this.setData({
          photos,
          stats,
          albums: albumCards,
          statCards: buildStatsCards(stats, photoData.total || photos.length),
          resultCountText: String(photoData.total || photos.length),
          noPhotos: photos.length === 0,
          albumCountText: String(albumCards.length),
          noAlbums: albumCards.length === 0,
        })
      })
      .catch(() => {})
      .then(() => this.setData({ loading: false }))
  },

  loadPhotos(query) {
    return request({
      path: '/api/photos',
      method: 'GET',
      data: normalize(query) ? { query: normalize(query) } : {},
    })
      .then((data) => ({
        photos: data.photos || [],
        total: Number(data.total || 0),
      }))
      .catch(() => ({ photos: [], total: 0 }))
  },

  loadStats() {
    return request({
      path: '/api/photos/analysis-stats',
      method: 'GET',
    })
      .then((data) => ({
        total_photos: Number(data.total_photos || 0),
        annotated_photos: Number(data.annotated_photos || 0),
        unannotated_photos: Number(data.unannotated_photos || 0),
        annotation_rate: Number(data.annotation_rate || 0),
        last_analysis: data.last_analysis || '',
      }))
      .catch(() => ({
        total_photos: 0,
        annotated_photos: 0,
        unannotated_photos: 0,
        annotation_rate: 0,
      }))
  },

  loadAlbums() {
    return request({
      path: '/api/photos/albums',
      method: 'GET',
    })
      .then((data) => data.albums || [])
      .catch(() => [])
  },

  setSearch(e) {
    this.setData({ searchKeyword: e.detail.value })
  },

  submitSearch() {
    this.refresh()
  },

  clearSearch() {
    this.setData({ searchKeyword: '' }, () => this.refresh())
  },

  chooseAndUpload() {
    wx.chooseMedia({
      count: 9,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const files = res.tempFiles || []
        if (!files.length) return
        this.uploadQueue(files.map((item) => item.tempFilePath))
      },
    })
  },

  uploadQueue(paths) {
    const baseUrl = getBaseUrl()
    if (!baseUrl || isPlaceholderUrl(baseUrl)) {
      wx.showToast({ title: 'API 域名未配置', icon: 'none' })
      return
    }
    this.setData({ uploading: true })
    let successCount = 0
    const formData = buildUploadPayload(this.data)
    const run = paths.reduce((promise, filePath) => promise.then(() => this.uploadOne(filePath, formData).then(() => {
      successCount += 1
    })), Promise.resolve())

    run
      .then(() => {
        wx.showToast({ title: `已上传 ${successCount} 张`, icon: 'success' })
        this.clearUploadForm(false)
        this.refresh()
      })
      .catch(() => {
        wx.showToast({ title: `已上传 ${successCount} 张，部分失败`, icon: 'none' })
        this.clearUploadForm(false)
        this.refresh()
      })
      .then(() => this.setData({ uploading: false }))
  },

  uploadOne(filePath, formData) {
    return new Promise((resolve, reject) => {
      wx.uploadFile({
        url: `${getBaseUrl()}/api/photos/upload`,
        filePath,
        name: 'file',
        formData,
        success: (res) => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(res)
            return
          }
          reject(new Error(`上传失败 ${res.statusCode}`))
        },
        fail: reject,
      })
    })
  },

  setUploadField(e) {
    const { field } = e.currentTarget.dataset
    this.setData({ [field]: e.detail.value })
  },

  clearUploadForm(showToast = true) {
    this.setData({
      uploadDescription: '',
      uploadTags: '',
      uploadPeople: '',
      uploadLocation: '',
    })
    if (showToast) {
      wx.showToast({ title: '已清空', icon: 'none' })
    }
  },

  analyzePhotos() {
    this.setData({ analyzing: true })
    request({
      path: '/api/photos/analyze?batch_size=20',
      method: 'POST',
    })
      .then((data) => {
        const processed = Number(data.success || data.processed || 0)
        wx.showToast({ title: processed ? `已分析 ${processed} 张` : '暂无待分析照片', icon: 'none' })
        this.refresh()
      })
      .catch(() => {})
      .then(() => this.setData({ analyzing: false }))
  },

  previewPhoto(e) {
    const url = e.currentTarget.dataset.url
    if (!url) return
    const urls = this.data.photos.map((item) => item.image_url).filter(Boolean)
    wx.previewImage({
      current: url,
      urls: urls.length ? urls : [url],
    })
  },

  openChatPrompt(e) {
    const prompt = e.currentTarget.dataset.prompt || '/photo'
    const title = e.currentTarget.dataset.title || '照片记忆'
    const route = `/chat?prompt=${encodeURIComponent(prompt)}`
    wx.navigateTo({
      url: `/pages/webview/webview?route=${encodeURIComponent(route)}&title=${encodeURIComponent(title)}`,
    })
  },
})
