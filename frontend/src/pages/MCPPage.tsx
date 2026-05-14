import React, { useState, useEffect } from 'react'
import { Card, Select, Form, Button, Input, message, List } from 'antd'
import { ApiOutlined, PlayCircleOutlined } from '@ant-design/icons'
import { mcpAPI } from '../services/api'

const MCPPage: React.FC = () => {
  const [tools, setTools] = useState<any[]>([])
  const [selectedTool, setSelectedTool] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    loadTools()
  }, [])

  const loadTools = async () => {
    try {
      const res = await mcpAPI.listTools()
      setTools(res.data.tools)
    } catch (error) {
      message.error('加载工具列表失败')
    }
  }

  const handleCall = async (values: any) => {
    if (!selectedTool) {
      message.warning('请选择一个工具')
      return
    }

    setLoading(true)
    try {
      const res = await mcpAPI.callTool(selectedTool, values)
      setResult(res.data)
      if (res.data.success) {
        message.success('调用成功')
      } else {
        message.error(res.data.error || '调用失败')
      }
    } catch (error) {
      message.error('调用失败')
    } finally {
      setLoading(false)
    }
  }

  const renderToolParams = () => {
    const tool = tools.find((t: any) => t.name === selectedTool)
    if (!tool) return null

    const params = tool.parameters?.properties || {}
    
    return Object.entries(params).map(([key, value]: [string, any]) => {
      if (value.enum) {
        return (
          <Form.Item
            key={key}
            name={key}
            label={key}
            rules={[{ required: tool.parameters.required?.includes(key) }]}
          >
            <Select placeholder={`选择${key}`}>
              {value.enum.map((opt: string) => (
                <Select.Option key={opt} value={opt}>{opt}</Select.Option>
              ))}
            </Select>
          </Form.Item>
        )
      }

      return (
        <Form.Item
          key={key}
          name={key}
          label={key}
          rules={[{ required: tool.parameters.required?.includes(key) }]}
        >
          <Input placeholder={value.description || `输入${key}`} />
        </Form.Item>
      )
    })
  }

  return (
    <div className="mcp-container" style={{ display: 'flex', gap: 16 }}>
      <Card title="🔧 可用工具" style={{ width: 400 }}>
        <List
          dataSource={tools}
          renderItem={(tool: any) => (
            <List.Item
              onClick={() => setSelectedTool(tool.name)}
              style={{
                cursor: 'pointer',
                background: selectedTool === tool.name ? '#e6f7ff' : 'transparent',
                padding: 12,
                borderRadius: 4,
              }}
            >
              <List.Item.Meta
                title={<strong>{tool.name}</strong>}
                description={tool.description}
              />
            </List.Item>
          )}
        />
      </Card>

      <Card title="🧪 工具测试" style={{ flex: 1 }}>
        {selectedTool ? (
          <>
            <div style={{ marginBottom: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
              <strong>当前工具：</strong>{selectedTool}
            </div>

            <Form form={form} onFinish={handleCall} layout="vertical">
              {renderToolParams()}

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  icon={<PlayCircleOutlined />}
                  loading={loading}
                  block
                >
                  调用工具
                </Button>
              </Form.Item>
            </Form>

            {result && (
              <Card title="执行结果" size="small" style={{ marginTop: 16 }}>
                <pre style={{ 
                  background: '#f5f5f5', 
                  padding: 12, 
                  borderRadius: 4,
                  overflow: 'auto',
                  maxHeight: 300
                }}>
                  {JSON.stringify(result, null, 2)}
                </pre>
              </Card>
            )}
          </>
        ) : (
          <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
            <ApiOutlined style={{ fontSize: 48 }} />
            <p style={{ marginTop: 16 }}>请从左侧选择一个工具进行测试</p>
          </div>
        )}
      </Card>
    </div>
  )
}

export default MCPPage
