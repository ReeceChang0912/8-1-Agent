import React, { useState } from 'react'
import { Card, Tabs, Form, Input, Button, Select, message, List, Tag, Space } from 'antd'
import { SearchOutlined, PlusOutlined, BookOutlined } from '@ant-design/icons'
import axios from 'axios'

const { TabPane } = Tabs
const { TextArea } = Input

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
      const response = await axios.get('/api/knowledge/search', {
        params: {
          query: values.query,
          category: category,
          n_results: 10
        }
      })
      
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
      const response = await axios.post('/api/knowledge/add', {
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
      <Tabs defaultActiveKey="search">
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
              style={{ marginBottom: 24 }}
            >
              <Form.Item
                name="query"
                rules={[{ required: true, message: '请输入搜索内容' }]}
                style={{ flex: 1, minWidth: 300 }}
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
    </div>
  )
}

export default KnowledgePage
