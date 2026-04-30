import React, { useState, useEffect, useRef } from 'react'
import { Card, Input, Button, List, Avatar, Space, message, Upload, Tag, Divider } from 'antd'
import { SendOutlined, UserOutlined, RobotOutlined, PaperClipOutlined, PictureOutlined, FileTextOutlined, ClockCircleOutlined, ShoppingCartOutlined, BookOutlined } from '@ant-design/icons'
import { chatAPI } from '../services/api'
import axios from 'axios'

const { TextArea } = Input

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [attachedFiles, setAttachedFiles] = useState<File[]>([])
  const [streamingMessage, setStreamingMessage] = useState('') // 流式消息
  const [isStreaming, setIsStreaming] = useState(false) // 是否正在流式输出
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<WebSocket | null>(null) // WebSocket连接

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingMessage])

  // 初始化WebSocket连接
  useEffect(() => {
    const userId = localStorage.getItem('member_name') || 'anonymous'
    const ws = new WebSocket(`ws://localhost:8000/api/chat/stream/${userId}`)
    
    ws.onopen = () => {
      console.log('WebSocket已连接')
    }
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.type === 'typing') {
        setIsStreaming(true)
        setStreamingMessage('')
      } else if (data.type === 'chunk') {
        // 逐字追加
        setStreamingMessage(prev => prev + data.data)
      } else if (data.type === 'complete') {
        // 完成,添加到消息列表
        const assistantMessage: Message = {
          role: 'assistant',
          content: data.data.full_response,
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, assistantMessage])
        setStreamingMessage('')
        setIsStreaming(false)
        setLoading(false)
      }
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket错误:', error)
      message.error('连接失败,使用HTTP模式')
      // 降级到HTTP模式
      setLoading(false)
      setIsStreaming(false)
    }
    
    wsRef.current = ws
    
    return () => {
      ws.close()
    }
  }, [])

  const handleSend = async () => {
    if (!inputValue.trim() && attachedFiles.length === 0) return

    // 构建消息内容
    let messageContent = inputValue
    
    // 如果有附件,先处理文件上传
    if (attachedFiles.length > 0) {
      for (const file of attachedFiles) {
        try {
          const formData = new FormData()
          formData.append('file', file)
          formData.append('description', inputValue || `上传的文件: ${file.name}`)
          
          // 判断是图片还是文档
          if (file.type.startsWith('image/')) {
            // 上传图片到照片记忆
            await axios.post('/api/photos/upload', formData)
            messageContent += `\n\n[已上传图片: ${file.name}]`
          } else {
            // 上传文档到知识库
            const text = await file.text()
            await axios.post('/api/knowledge/add', {
              title: file.name,
              content: text,
              category: 'general',
              tags: ['uploaded']
            })
            messageContent += `\n\n[已上传文档: ${file.name}]`
          }
        } catch (error) {
          console.error('上传失败:', error)
          message.error(`上传 ${file.name} 失败`)
        }
      }
      setAttachedFiles([]) // 清空附件
    }

    const userMessage: Message = {
      role: 'user',
      content: messageContent,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setLoading(true)

    // 使用WebSocket发送消息
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ message: messageContent }))
    } else {
      // 降级到HTTP模式
      try {
        const response = await chatAPI.sendMessage(messageContent)
        const assistantMessage: Message = {
          role: 'assistant',
          content: response.data.response,
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, assistantMessage])
      } catch (error) {
        message.error('发送消息失败')
      } finally {
        setLoading(false)
      }
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // 快捷指令
  const quickActions = [
    { icon: <ClockCircleOutlined />, label: '创建提醒', text: '提醒我明天下午3点开会' },
    { icon: <ShoppingCartOutlined />, label: '添加购物', text: '买牛奶和鸡蛋' },
    { icon: <BookOutlined />, label: '搜索知识', text: '查询高血压的注意事项' },
    { icon: <PictureOutlined />, label: '上传照片', action: 'upload' },
  ]

  const handleQuickAction = (action: any) => {
    if (action.action === 'upload') {
      // 触发文件上传
      document.getElementById('file-upload-input')?.click()
    } else {
      setInputValue(action.text)
    }
  }

  const handleFileChange = (info: any) => {
    const fileList = info.fileList.slice(-5) // 最多5个文件
    const files = fileList.map((f: any) => f.originFileObj).filter(Boolean)
    setAttachedFiles(files)
  }

  return (
    <div style={{ height: 'calc(100vh - 200px)', display: 'flex', flexDirection: 'column' }}>
      <Card 
        title="💬 智能对话" 
        style={{ flex: 1, display: 'flex', flexDirection: 'column' }}
        bodyStyle={{ flex: 1, overflowY: 'auto', padding: '24px' }}
      >
        <List
          dataSource={messages}
          renderItem={(msg) => (
            <div
              style={{
                display: 'flex',
                justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                marginBottom: 16,
              }}
            >
              <Space align="start">
                {msg.role === 'assistant' && (
                  <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#1890ff' }} />
                )}
                <Card
                  size="small"
                  style={{
                    maxWidth: 600,
                    background: msg.role === 'user' ? '#e6f7ff' : '#f5f5f5',
                  }}
                >
                  <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
                </Card>
                {msg.role === 'user' && (
                  <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#52c41a' }} />
                )}
              </Space>
            </div>
          )}
        />
        
        {/* 流式消息显示 */}
        {isStreaming && (
          <div style={{
            display: 'flex',
            justifyContent: 'flex-start',
            marginBottom: 16,
          }}>
            <Space align="start">
              <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#1890ff' }} />
              <Card
                size="small"
                style={{
                  maxWidth: 600,
                  background: '#f5f5f5',
                  border: '2px solid #1890ff',
                }}
              >
                <div style={{ whiteSpace: 'pre-wrap', minHeight: 24 }}>
                  {streamingMessage}
                  <span style={{
                    display: 'inline-block',
                    width: 2,
                    height: 16,
                    background: '#1890ff',
                    marginLeft: 2,
                    animation: 'blink 1s infinite'
                  }} />
                </div>
              </Card>
            </Space>
          </div>
        )}
        
        <style>{`
          @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
          }
        `}</style>
        
        <div ref={messagesEndRef} />
      </Card>

      <Card style={{ marginTop: 16 }}>
        {/* 快捷指令 */}
        <div style={{ marginBottom: 12 }}>
          <Space wrap>
            {quickActions.map((action, index) => (
              <Button
                key={index}
                size="small"
                icon={action.icon}
                onClick={() => handleQuickAction(action)}
              >
                {action.label}
              </Button>
            ))}
          </Space>
        </div>

        {/* 附件显示 */}
        {attachedFiles.length > 0 && (
          <div style={{ marginBottom: 12 }}>
            <Space wrap>
              {attachedFiles.map((file, index) => (
                <Tag
                  key={index}
                  color="blue"
                  closable
                  onClose={() => {
                    const newFiles = attachedFiles.filter((_, i) => i !== index)
                    setAttachedFiles(newFiles)
                  }}
                >
                  {file.type.startsWith('image/') ? <PictureOutlined /> : <FileTextOutlined />}
                  {' '}{file.name}
                </Tag>
              ))}
            </Space>
          </div>
        )}

        <Space.Compact style={{ width: '100%' }}>
          {/* 文件上传按钮 */}
          <Upload
            id="file-upload-input"
            multiple
            beforeUpload={() => false}
            onChange={handleFileChange}
            showUploadList={false}
            accept="image/*,.pdf,.doc,.docx,.txt,.md"
          >
            <Button icon={<PaperClipOutlined />} />
          </Upload>

          <TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="输入消息... (Enter 发送, Shift+Enter 换行)\n支持：创建提醒、添加购物、搜索知识、上传图片/文档"
            autoSize={{ minRows: 1, maxRows: 4 }}
            disabled={loading}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            loading={loading}
          >
            发送
          </Button>
        </Space.Compact>

        <div style={{ marginTop: 8, fontSize: 12, color: '#999' }}>
          💡 提示：直接说“提醒我...”、“买...”、“查询...”等，我会自动帮你操作
        </div>
      </Card>
    </div>
  )
}

export default ChatPage
