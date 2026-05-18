import React, { useState, useEffect } from 'react'
import { Card, Tabs, Form, Input, Button, Select, message, List, Tag, Space, Empty, Spin, Modal, Typography } from 'antd'
import { SearchOutlined, PlusOutlined, BookOutlined, FolderOutlined } from '@ant-design/icons'
import { knowledgeAPI } from '../services/api'

const { TabPane } = Tabs
const { TextArea } = Input
const { Title, Paragraph, Text } = Typography

const CATEGORIES = [
  { value: 'general', label: '📝 通用' },
  { value: 'health', label: '💊 健康' },
  { value: 'cooking', label: '🍳 烹饪' },
  { value: 'education', label: '📚 教育' },
  { value: 'finance', label: '💰 财务' },
  { value: 'travel', label: '✈️ 旅行' },
  { value: 'legal', label: '⚖️ 法律' },
  { value: 'relationship', label: '❤️ 关系' }
]

const KnowledgePage: React.FC = () => {
  const [searchForm] = Form.useForm()
  const [addForm] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [searchResults, setSearchResults] = useState<any[]>([])
  const [hasSearched, setHasSearched] = useState(false)
  const [documents, setDocuments] = useState<any[]>([])
  const [documentsLoading, setDocumentsLoading] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [currentDocument, setCurrentDocument] = useState<any>(null)
  const [detailLoading, setDetailLoading] = useState(false)

  // 加载所有文档
  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async (category?: string) => {
    setDocumentsLoading(true)
    try {
      const catParam = category === 'all' ? undefined : category
      const response = await knowledgeAPI.list(catParam, 100)
      setDocuments(response.data.documents || [])
    } catch (error) {
      console.error('加载文档失败:', error)
      message.error('加载文档失败')
    } finally {
      setDocumentsLoading(false)
    }
  }

  // 查看文档详情
  const handleViewDetail = async (docId: string) => {
    setDetailLoading(true)
    setDetailModalVisible(true)
    try {
      const response = await knowledgeAPI.getDetail(docId)
      setCurrentDocument(response.data.document)
    } catch (error) {
      console.error('获取文档详情失败:', error)
      message.error('获取文档详情失败')
      setDetailModalVisible(false)
    } finally {
      setDetailLoading(false)
    }
  }

  // 搜索知识库
  const handleSearch = async (values: any) => {
    if (!values.query) {
      message.warning('请输入搜索内容')
      return
    }

    setLoading(true)
    setHasSearched(true)
    try {
      const category = values.category === 'all' ? null : values.category
      const response = await knowledgeAPI.search(values.query, category || undefined, 10)
      
      setSearchResults(response.data.results || [])
      
      if (response.data.results?.length > 0) {
        message.success(`找到 ${response.data.results.length} 条相关知识`)
      } else {
        message.info('未找到相关知识')
      }
    } catch (error) {
      console.error('搜索失败:', error)
      message.error('搜索失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  // 添加文档
  const handleAdd = async (values: any) => {
    if (!values.title || !values.content) {
      message.warning('请填写标题和内容')
      return
    }

    setLoading(true)
    try {
      const response = await knowledgeAPI.add({
        title: values.title,
        content: values.content,
        category: values.category,
        tags: values.tags ? values.tags.split(',').map((t: string) => t.trim()).filter(Boolean) : []
      })
      
      message.success('✅ 文档添加成功')
      addForm.resetFields()
    } catch (error) {
      console.error('添加失败:', error)
      message.error('添加失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <Tabs defaultActiveKey="browse">
        <TabPane 
          tab={
            <span>
              <FolderOutlined />
              浏览知识
            </span>
          } 
          key="browse"
        >
          <Card>
            <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontSize: 16, fontWeight: 600 }}>
                📚 知识库文档列表
              </div>
              <Select
                value={selectedCategory}
                onChange={(value) => {
                  setSelectedCategory(value)
                  loadDocuments(value === 'all' ? undefined : value)
                }}
                style={{ width: 150 }}
              >
                <Select.Option value="all">全部分类</Select.Option>
                {CATEGORIES.map(cat => (
                  <Select.Option key={cat.value} value={cat.value}>
                    {cat.label}
                  </Select.Option>
                ))}
              </Select>
            </div>

            <Spin spinning={documentsLoading}>
              {documents.length > 0 ? (
                <List
                  itemLayout="vertical"
                  dataSource={documents}
                  renderItem={(doc: any) => (
                    <List.Item
                      key={doc.doc_id}
                      style={{
                        background: '#fafafa',
                        padding: 16,
                        borderRadius: 8,
                        marginBottom: 12,
                        cursor: 'pointer',
                        transition: 'all 0.3s'
                      }}
                      onClick={() => handleViewDetail(doc.doc_id)}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = '#f0f0f0'
                        e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)'
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = '#fafafa'
                        e.currentTarget.style.boxShadow = 'none'
                      }}
                    >
                      <List.Item.Meta
                        title={
                          <Space>
                            <BookOutlined />
                            <strong>{doc.title}</strong>
                            {doc.category && (
                              <Tag color="blue">
                                {CATEGORIES.find(c => c.value === doc.category)?.label || doc.category}
                              </Tag>
                            )}
                            <Tag color="green">{doc.file_type}</Tag>
                          </Space>
                        }
                        description={
                          <div style={{ marginTop: 8 }}>
                            {doc.description && <p style={{ margin: '0 0 8px 0' }}>{doc.description}</p>}
                            <Space size={[8, 8]} wrap>
                              <span style={{ fontSize: 12, color: '#999' }}>
                                📅 {new Date(doc.upload_time).toLocaleString('zh-CN')}
                              </span>
                              <span style={{ fontSize: 12, color: '#999' }}>
                                📄 {doc.chunk_count} 个段落
                              </span>
                              {doc.tags && doc.tags.length > 0 && (
                                <Space size={[0, 4]} wrap>
                                  {doc.tags.map((tag: string, i: number) => (
                                    <Tag key={i} color="purple">{tag}</Tag>
                                  ))}
                                </Space>
                              )}
                            </Space>
                          </div>
                        }
                      />
                    </List.Item>
                  )}
                />
              ) : (
                <Empty description="暂无文档，请添加知识" />
              )}
            </Spin>
          </Card>
        </TabPane>
        <TabPane 
          tab={
            <span>
              <SearchOutlined />
              搜索知识
            </span>
          } 
          key="search"
        >
          <Card>
            <Form
              form={searchForm}
              onFinish={handleSearch}
              layout="inline"
              className="knowledge-search-form"
              style={{ marginBottom: 24 }}
            >
              <Form.Item
                name="query"
                rules={[{ required: true, message: '请输入搜索内容' }]}
                style={{ flex: 1, minWidth: 250 }}
              >
                <Input
                  placeholder="输入你想查询的内容..."
                  prefix={<SearchOutlined />}
                  size="large"
                />
              </Form.Item>

              <Form.Item name="category" initialValue="all">
                <Select style={{ width: 150 }} size="large">
                  <Select.Option value="all">全部分类</Select.Option>
                  {CATEGORIES.map(cat => (
                    <Select.Option key={cat.value} value={cat.value}>
                      {cat.label}
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  icon={<SearchOutlined />}
                  loading={loading}
                  size="large"
                >
                  搜索
                </Button>
              </Form.Item>
            </Form>

            {hasSearched && (
              <div>
                {searchResults.length > 0 ? (
                  <List
                    itemLayout="vertical"
                    dataSource={searchResults}
                    renderItem={(item: any, index) => (
                      <List.Item
                        key={index}
                        style={{
                          background: '#fafafa',
                          padding: 16,
                          borderRadius: 8,
                          marginBottom: 12
                        }}
                      >
                        <List.Item.Meta
                          title={
                            <Space>
                              <BookOutlined />
                              <strong>结果 {index + 1}</strong>
                              {item.metadata?.title && (
                                <Tag color="blue">{item.metadata.title}</Tag>
                              )}
                              {item.metadata?.category && (
                                <Tag color="green">
                                  {CATEGORIES.find(c => c.value === item.metadata.category)?.label || item.metadata.category}
                                </Tag>
                              )}
                            </Space>
                          }
                          description={
                            <div style={{ marginTop: 8 }}>
                              <p style={{ margin: 0, lineHeight: 1.8 }}>{item.content}</p>
                              {item.metadata?.source && (
                                <div style={{ marginTop: 8, fontSize: 12, color: '#999' }}>
                                  📁 来源: {item.metadata.source}
                                </div>
                              )}
                              {item.metadata?.tags && item.metadata.tags.length > 0 && (
                                <div style={{ marginTop: 8 }}>
                                  <Space size={[0, 4]} wrap>
                                    {item.metadata.tags.map((tag: string, i: number) => (
                                      <Tag key={i} color="purple">{tag}</Tag>
                                    ))}
                                  </Space>
                                </div>
                              )}
                            </div>
                          }
                        />
                      </List.Item>
                    )}
                  />
                ) : (
                  <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
                    <SearchOutlined style={{ fontSize: 48 }} />
                    <p style={{ marginTop: 16 }}>暂无搜索结果</p>
                  </div>
                )}
              </div>
            )}

            {!hasSearched && (
              <div style={{ textAlign: 'center', padding: 60, color: '#999' }}>
                <SearchOutlined style={{ fontSize: 64 }} />
                <p style={{ marginTop: 16, fontSize: 16 }}>输入关键词开始搜索知识库</p>
              </div>
            )}
          </Card>
        </TabPane>

        <TabPane
          tab={
            <span>
              <PlusOutlined />
              添加文档
            </span>
          }
          key="add"
        >
          <Card>
            <Form
              form={addForm}
              onFinish={handleAdd}
              layout="vertical"
            >
              <Form.Item
                name="title"
                label="📝 标题"
                rules={[{ required: true, message: '请输入标题' }]}
              >
                <Input placeholder="输入文档标题" size="large" />
              </Form.Item>

              <Form.Item
                name="content"
                label="📄 内容"
                rules={[{ required: true, message: '请输入内容' }]}
              >
                <TextArea
                  rows={8}
                  placeholder="在此输入文档内容..."
                  style={{ fontSize: 14 }}
                />
              </Form.Item>

              <Form.Item
                name="category"
                label="📁 分类"
                initialValue="general"
              >
                <Select size="large">
                  {CATEGORIES.map(cat => (
                    <Select.Option key={cat.value} value={cat.value}>
                      {cat.label}
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item
                name="tags"
                label="🏷️ 标签（可选）"
                extra="多个标签用逗号分隔，例如：高血压,护理,健康"
              >
                <Input placeholder="用逗号分隔多个标签" />
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  icon={<PlusOutlined />}
                  loading={loading}
                  size="large"
                  block
                >
                  添加到知识库
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>
      </Tabs>

      {/* 文档详情弹窗 */}
      <Modal
        title={
          <Space>
            <BookOutlined />
            <span>{currentDocument?.title}</span>
          </Space>
        }
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={800}
        bodyStyle={{ maxHeight: '70vh', overflowY: 'auto' }}
      >
        <Spin spinning={detailLoading}>
          {currentDocument && (
            <div>
              <div style={{ marginBottom: 16 }}>
                <Space size={[8, 8]} wrap>
                  {currentDocument.category && (
                    <Tag color="blue">
                      {CATEGORIES.find(c => c.value === currentDocument.category)?.label || currentDocument.category}
                    </Tag>
                  )}
                  <Tag color="green">{currentDocument.file_type}</Tag>
                  <span style={{ fontSize: 12, color: '#999' }}>
                    📅 {new Date(currentDocument.upload_time).toLocaleString('zh-CN')}
                  </span>
                </Space>
              </div>

              {currentDocument.description && (
                <div style={{ marginBottom: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
                  <Text type="secondary">描述：</Text>
                  <Paragraph style={{ margin: '8px 0 0 0' }}>{currentDocument.description}</Paragraph>
                </div>
              )}

              {currentDocument.tags && currentDocument.tags.length > 0 && (
                <div style={{ marginBottom: 16 }}>
                  <Text strong>标签：</Text>
                  <Space size={[0, 4]} wrap style={{ marginLeft: 8 }}>
                    {currentDocument.tags.map((tag: string, i: number) => (
                      <Tag key={i} color="purple">{tag}</Tag>
                    ))}
                  </Space>
                </div>
              )}

              <div style={{ marginTop: 16 }}>
                <Title level={5}>📄 内容</Title>
                <Paragraph
                  style={{
                    whiteSpace: 'pre-wrap',
                    lineHeight: 1.8,
                    background: '#fafafa',
                    padding: 16,
                    borderRadius: 4,
                    maxHeight: '400px',
                    overflowY: 'auto'
                  }}
                >
                  {currentDocument.content || '暂无内容'}
                </Paragraph>
              </div>

              <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid #f0f0f0' }}>
                <Space size={[16, 8]} wrap>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    📊 {currentDocument.chunk_count} 个段落
                  </Text>
                  {currentDocument.source && currentDocument.source !== 'manual_input' && (
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      📁 来源: {currentDocument.source}
                    </Text>
                  )}
                </Space>
              </div>
            </div>
          )}
        </Spin>
      </Modal>
    </div>
  )
}

export default KnowledgePage
