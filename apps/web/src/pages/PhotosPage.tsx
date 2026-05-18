import React, { useState, useEffect } from 'react'
import { Card, Upload, Button, Input, Form, message, Row, Col, Image, Empty, Tabs, Badge, Statistic, Progress, Space, Tooltip, Spin } from 'antd'
import { UploadOutlined, PictureOutlined, LoadingOutlined, RobotOutlined, FolderOutlined } from '@ant-design/icons'
import { photosAPI } from '../services/api'
import axios from 'axios'
import '../styles/PhotosPage.css'

const { TextArea } = Input
const { TabPane } = Tabs

interface Photo {
  id: string
  filename: string
  upload_date: string
  description: string
  tags: string[]
  people: string[]
  location: string
  oss_url?: string
}

const PhotosPage: React.FC = () => {
  const [photos, setPhotos] = useState<Photo[]>([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [form] = Form.useForm()
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisStats, setAnalysisStats] = useState<any>(null)
  const [albums, setAlbums] = useState<any[]>([])

  useEffect(() => {
    loadPhotos()
    loadAnalysisStats()
    loadAlbums()
  }, [])

  const loadPhotos = async (query?: string) => {
    setLoading(true)
    try {
      const res = await photosAPI.getAll(query)
      setPhotos(res.data.photos || [])
    } catch (error) {
      message.error('加载照片失败')
    } finally {
      setLoading(false)
    }
  }

  // 智能分析照片
  const handleSmartAnalyze = async () => {
    setAnalyzing(true)
    try {
      const res = await axios.post('/api/photos/analyze', null, {
        params: { batch_size: 20 }
      })

      if (res.data.success > 0) {
        message.success(`✅ 成功分析 ${res.data.success} 张照片`)
        loadPhotos()
        loadAnalysisStats()
      } else {
        message.info('所有照片已标注')
      }
    } catch (error) {
      console.error('分析失败:', error)
      message.error('分析失败，请稍后重试')
    } finally {
      setAnalyzing(false)
    }
  }

  // 加载分析统计
  const loadAnalysisStats = async () => {
    try {
      const res = await axios.get('/api/photos/analysis-stats')
      setAnalysisStats(res.data)
    } catch (error) {
      console.error('加载统计失败')
    }
  }

  // 加载自动相册
  const loadAlbums = async () => {
    try {
      const res = await axios.get('/api/photos/albums')
      setAlbums(res.data.albums || [])
    } catch (error) {
      console.error('加载相册失败')
    }
  }

  const handleUpload = async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)

    const values = form.getFieldsValue()
    formData.append('description', values.description || '')
    formData.append('tags', values.tags || '')
    formData.append('people', values.people || '')
    formData.append('location', values.location || '')

    try {
      await photosAPI.upload(formData)
      message.success('照片上传成功')
      form.resetFields()
      loadPhotos()
    } catch (error) {
      message.error('上传失败')
    }

    return false
  }

  const handleSearch = (query?: string) => {
    loadPhotos(query || searchQuery)
  }

  return (
    <div className="photos-page-container">
      <Tabs defaultActiveKey="browse" className="photos-tabs">
        <TabPane
          tab={
            <span>
              <PictureOutlined />
              照片墙
            </span>
          }
          key="browse"
        >
          {/* 顶部操作栏 */}
          <div className="photos-header">
            <div className="photos-title">
              <PictureOutlined style={{ marginRight: 10 }} />
              照片墙
            </div>
            <Space className="photos-actions">
              <Input.Search
                placeholder="搜索照片..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onSearch={handleSearch}
                className="photos-search"
                allowClear
              />
              <Upload
                showUploadList={false}
                action="/api/photos/upload"
                multiple
                accept="image/*"
                beforeUpload={() => { setUploading(true); return true }}
                onChange={({ file }) => {
                  if (file.status === 'done' || file.status === 'error') {
                    setUploading(false)
                  }
                  if (file.status === 'done') {
                    if (file.response?.success) {
                      message.success(`已上传 ${file.name}`)
                      loadPhotos()
                    }
                  }
                  if (file.status === 'error') {
                    message.error(`${file.name} 上传失败`)
                  }
                }}
              >
                <Tooltip title="支持多选">
                  <Button type="primary" icon={uploading ? <LoadingOutlined /> : <UploadOutlined />} size="large" loading={uploading} className="photos-upload-btn">
                    上传照片
                  </Button>
                </Tooltip>
              </Upload>
            </Space>
          </div>

          {/* 照片墙 */}
          <Spin spinning={loading}>
          {photos.length === 0 ? (
            <div className="photos-empty">
              <Empty description="暂无照片，点击右上角上传">
                <Upload
                  showUploadList={false}
                  action="/api/photos/upload"
                  accept="image/*"
                  beforeUpload={() => { setUploading(true); return true }}
                  onChange={({ file }) => {
                    if (file.status === 'done' || file.status === 'error') {
                      setUploading(false)
                    }
                    if (file.status === 'done' && file.response?.success) {
                      message.success('照片上传成功')
                      loadPhotos()
                    }
                  }}
                >
                  <Button type="primary" icon={<UploadOutlined />}>
                    上传第一张照片
                  </Button>
                </Upload>
              </Empty>
            </div>
          ) : (
            <Row gutter={[16, 16]} className="photos-grid">
              {photos.map((photo) => (
                <Col xs={24} sm={12} md={8} lg={6} xl={6} key={photo.id}>
                  <div
                    className="photo-item"
                    onMouseEnter={(e) => {
                      e.currentTarget.classList.add('photo-hover')
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.classList.remove('photo-hover')
                    }}
                  >
                    <Image
                      src={photo.oss_url || `/api/photos/${photo.filename}`}
                      alt={photo.description}
                      className="photo-image"
                      fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
                      preview={{ mask: (photo.description || photo.location) ? (
                        <div className="photo-mask">
                          {photo.description && <div className="photo-mask-desc">{photo.description}</div>}
                          {photo.location && <div className="photo-mask-loc">📍 {photo.location}</div>}
                        </div>
                      ) : true }}
                    />
                  </div>
                </Col>
              ))}
            </Row>
          )}
          </Spin>
        </TabPane>

        <TabPane
          tab={
            <span>
              <UploadOutlined />
              上传照片
            </span>
          }
          key="upload"
        >
          <Card>
            <Form form={form} layout="vertical">
              <Form.Item name="description" label="描述">
                <TextArea rows={3} placeholder="描述这张照片..." />
              </Form.Item>

              <Form.Item name="tags" label="标签">
                <Input placeholder="用逗号分隔，例如：生日,聚会,家庭" />
              </Form.Item>

              <Form.Item name="people" label="人物">
                <Input placeholder="照片中的人物" />
              </Form.Item>

              <Form.Item name="location" label="地点">
                <Input placeholder="拍摄地点" />
              </Form.Item>

              <Form.Item>
                <Upload
                  showUploadList={false}
                  customRequest={({ file }) => handleUpload(file as File)}
                  accept="image/*"
                >
                  <Button icon={<UploadOutlined />} type="primary" size="large">
                    选择照片上传
                  </Button>
                </Upload>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>

        <TabPane
          tab={
            <span>
              <RobotOutlined />
              智能分析
              {analysisStats?.unannotated_photos > 0 && (
                <Badge count={analysisStats.unannotated_photos} className="analyze-badge" />
              )}
            </span>
          }
          key="analyze"
        >
          <Row gutter={16} className="stats-row">
            <Col xs={24} sm={8} className="stats-col">
              <Card>
                <Statistic
                  title="总照片数"
                  value={analysisStats?.total_photos || 0}
                  prefix={<PictureOutlined />}
                />
              </Card>
            </Col>
            <Col xs={24} sm={8} className="stats-col">
              <Card>
                <Statistic
                  title="已标注"
                  value={analysisStats?.annotated_photos || 0}
                  valueStyle={{ color: '#3f8600' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={8} className="stats-col">
              <Card>
                <Statistic
                  title="待标注"
                  value={analysisStats?.unannotated_photos || 0}
                  valueStyle={{ color: '#cf1322' }}
                />
              </Card>
            </Col>
          </Row>

          <Card className="analyze-card">
            <div className="progress-wrapper">
              <Progress
                percent={analysisStats?.annotation_rate || 0}
                format={(percent) => `${percent}% 已标注`}
              />
            </div>

            <Button
              type="primary"
              icon={<RobotOutlined />}
              onClick={handleSmartAnalyze}
              loading={analyzing}
              block
              size="large"
              className="analyze-btn"
            >
              {analyzing ? '正在智能分析...' : '🤖 开始智能分析'}
            </Button>

            <div className="analyze-tips">
              <p>✨ 智能分析功能可以：</p>
              <ul>
                <li>自动生成照片描述</li>
                <li>识别照片中的人物</li>
                <li>添加相关标签</li>
                <li>推测拍摄场景和情绪</li>
              </ul>
            </div>
          </Card>
        </TabPane>

        <TabPane
          tab={
            <span>
              <FolderOutlined />
              自动相册
            </span>
          }
          key="albums"
        >
          {albums.length > 0 ? (
            <Row gutter={16} className="albums-row">
              {albums.map((album, index) => (
                <Col xs={24} sm={12} md={8} key={index} className="album-col">
                  <Card
                    hoverable
                    cover={
                      <div style={{ height: 200, background: '#f0f0f0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <PictureOutlined style={{ fontSize: 48, color: '#999' }} />
                      </div>
                    }
                  >
                    <Card.Meta
                      title={album.name}
                      description={`${album.photo_count} 张照片`}
                    />
                  </Card>
                </Col>
              ))}
            </Row>
          ) : (
            <Empty description="暂无自动相册，请先上传更多照片" />
          )}
        </TabPane>
      </Tabs>
    </div>
  )
}

export default PhotosPage