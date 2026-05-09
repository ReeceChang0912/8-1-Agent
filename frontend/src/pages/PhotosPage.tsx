import React, { useState, useEffect } from 'react'
import { Card, Upload, Button, Input, Form, message, Row, Col, Image, Empty, Tabs, Badge, Statistic, Progress } from 'antd'
import { UploadOutlined, PictureOutlined, SearchOutlined, RobotOutlined, FolderOutlined } from '@ant-design/icons'
import { photosAPI } from '../services/api'
import axios from 'axios'

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
}

const PhotosPage: React.FC = () => {
  const [photos, setPhotos] = useState<Photo[]>([])
  const [loading, setLoading] = useState(false)
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
      setPhotos(res.data.photos)
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
      const res = await photosAPI.upload(formData)
      message.success('照片上传成功')
      form.resetFields()
      loadPhotos()
    } catch (error) {
      message.error('上传失败')
    }
    
    return false
  }

  const handleSearch = () => {
    loadPhotos(searchQuery)
  }

  return (
    <div>
      <Tabs defaultActiveKey="upload">
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
                <Badge count={analysisStats.unannotated_photos} style={{ marginLeft: 8 }} />
              )}
            </span>
          }
          key="analyze"
        >
          <Row gutter={16}>
            <Col span={8}>
              <Card>
                <Statistic
                  title="总照片数"
                  value={analysisStats?.total_photos || 0}
                  prefix={<PictureOutlined />}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card>
                <Statistic
                  title="已标注"
                  value={analysisStats?.annotated_photos || 0}
                  valueStyle={{ color: '#3f8600' }}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card>
                <Statistic
                  title="待标注"
                  value={analysisStats?.unannotated_photos || 0}
                  valueStyle={{ color: '#cf1322' }}
                />
              </Card>
            </Col>
          </Row>

          <Card style={{ marginTop: 16 }}>
            <div style={{ marginBottom: 16 }}>
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
            >
              {analyzing ? '正在智能分析...' : '🤖 开始智能分析'}
            </Button>

            <div style={{ marginTop: 16, color: '#666', fontSize: 14 }}>
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
            <Row gutter={16}>
              {albums.map((album, index) => (
                <Col span={8} key={index}>
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

        <TabPane
          tab={
            <span>
              <PictureOutlined />
              照片浏览
            </span>
          }
          key="browse"
        >
          <Card
            title="照片库"
            extra={
              <Input.Search
                placeholder="搜索照片..."
                onSearch={handleSearch}
                style={{ width: 250 }}
                prefix={<SearchOutlined />}
              />
            }
          >
            {photos.length === 0 ? (
              <Empty description="暂无照片" />
            ) : (
              <Row gutter={[16, 16]}>
                {photos.map((photo) => (
                  <Col xs={24} sm={12} md={8} lg={6} key={photo.id}>
                    <Card
                      hoverable
                      cover={
                        <div style={{ height: 200, overflow: 'hidden' }}>
                          <Image
                            src={photo.oss_url || `/api/photos/${photo.filename}`}
                            alt={photo.description}
                            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                            fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
                          />
                        </div>
                      }
                    >
                      <Card.Meta
                        title={photo.description || '未命名照片'}
                        description={
                          <div style={{ fontSize: 12 }}>
                            {photo.people && photo.people.length > 0 && (
                              <div>👥 {photo.people.join(', ')}</div>
                            )}
                            {photo.location && <div>📍 {photo.location}</div>}
                            {photo.tags && photo.tags.length > 0 && (
                              <div style={{ marginTop: 4 }}>
                                {photo.tags.map(tag => (
                                  <span key={tag} style={{ marginRight: 4 }}>#{tag}</span>
                                ))}
                              </div>
                            )}
                          </div>
                        }
                      />
                    </Card>
                  </Col>
                ))}
              </Row>
            )}
          </Card>
        </TabPane>
      </Tabs>
    </div>
  )
}

export default PhotosPage
