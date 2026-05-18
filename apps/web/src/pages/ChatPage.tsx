import React, { useState, useEffect, useRef } from 'react'
import { Card, Input, Button, List, Avatar, Space, message, Upload, Tag, Empty, Modal, Tooltip, Typography, Divider } from 'antd'
import { SendOutlined, UserOutlined, RobotOutlined, PaperClipOutlined, PictureOutlined, FileTextOutlined, ClockCircleOutlined, ShoppingCartOutlined, BookOutlined, PlusOutlined, DeleteOutlined, EditOutlined, MessageOutlined } from '@ant-design/icons'
import { chatAPI, lifeModulesAPI, financeAPI } from '../services/api'
import axios from 'axios'
import { useSpeechRecognition } from '../hooks/useSpeechRecognition'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import rehypeHighlight from 'rehype-highlight'

const { TextArea } = Input
const { Text } = Typography

const getChatWebSocketUrl = (userId: string) => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const apiPath = `/api/chat/stream/${encodeURIComponent(userId)}`
  return `${protocol}//${window.location.host}${apiPath}`
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  images?: { url: string; name: string }[]
}

interface ChatSession {
  session_id: string
  title: string
  updated_at?: string
  created_at?: string
  message_count?: number
  last_message?: string
}

const ChatPage: React.FC = () => {
  const userId = localStorage.getItem('member_name') || 'anonymous'
  const familyId = localStorage.getItem('family_id') || ''
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [activeSessionId, setActiveSessionId] = useState<string>('')
  const [sessionsLoading, setSessionsLoading] = useState(false)
  const [renamingSession, setRenamingSession] = useState<ChatSession | null>(null)
  const [renameTitle, setRenameTitle] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [attachedFiles, setAttachedFiles] = useState<File[]>([])
  const [streamingMessage, setStreamingMessage] = useState('') // 流式消息
  
  // Voice recognition
  const { transcript } = useSpeechRecognition();
  const [isStreaming, setIsStreaming] = useState(false) // 是否正在流式输出
  const [connectionMode, setConnectionMode] = useState<'websocket' | 'http'>('http') // 连接模式
  const [showCommands, setShowCommands] = useState(false)
  const [commandFilter, setCommandFilter] = useState('')
  const [moduleSummary, setModuleSummary] = useState<any>({
    wedding: null,
    insurance: null,
    vehicle: null,
    fitness: null,
    finance: null,
  })
  const inputRef = useRef<any>(null)

  const commands = [
    { cmd: '/shopping', desc: '添加购物清单', icon: '🛒', example: '/shopping 牛奶和鸡蛋' },
    { cmd: '/remind', desc: '创建日程提醒', icon: '📅', example: '/remind 明天下午3点开会' },
    { cmd: '/knowledge', desc: '搜索知识库', icon: '📚', example: '/knowledge 高血压注意事项' },
    { cmd: '/wedding', desc: '查看备婚摘要/列表', icon: '💍', example: '/wedding summary' },
    { cmd: '/insurance', desc: '查看保险摘要/列表', icon: '🛡️', example: '/insurance list' },
    { cmd: '/vehicle', desc: '查看车辆摘要/列表', icon: '🚗', example: '/vehicle summary' },
    { cmd: '/fitness', desc: '查看健身摘要/列表', icon: '🏋️', example: '/fitness list' },
    { cmd: '/finance', desc: '查看本月财务摘要', icon: '💰', example: '/finance summary' },
    { cmd: '/memory', desc: '搜索记忆', icon: '🧠', example: '/memory 车辆保养' },
    { cmd: '/photo', desc: '上传照片', icon: '📸', example: '/photo' },
    { cmd: '/help', desc: '查看所有指令', icon: '📋', example: '/help' },
  ]

  const filteredCommands = commands.filter(c =>
    c.cmd.includes(commandFilter.toLowerCase())
  )
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<WebSocket | null>(null) // WebSocket连接
  const activeSessionRef = useRef<string>('')

  const scrollToBottom = () => {
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }, 50)
  }

  // Auto-fill input with voice transcript
  useEffect(() => {
    if (transcript) {
      setInputValue(transcript);
    }
  }, [transcript]);

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingMessage])

  useEffect(() => {
    activeSessionRef.current = activeSessionId
  }, [activeSessionId])

  useEffect(() => {
    loadSessions()
    loadModuleSummary()
  }, [])

  const loadModuleSummary = async () => {
    try {
      const now = new Date()
      const [wedding, insurance, vehicle, fitness, finance] = await Promise.all([
        lifeModulesAPI.wedding.stats(familyId),
        lifeModulesAPI.insurance.stats(familyId),
        lifeModulesAPI.vehicle.stats(familyId),
        lifeModulesAPI.fitness.stats(familyId),
        financeAPI.getSummary(now.getFullYear(), now.getMonth() + 1),
      ])
      setModuleSummary({
        wedding: wedding.data,
        insurance: insurance.data,
        vehicle: vehicle.data,
        fitness: fitness.data,
        finance: finance.data,
      })
    } catch (error) {
      console.warn('加载聊天上下文摘要失败', error)
    }
  }

  useEffect(() => {
    if (activeSessionId) {
      loadSessionHistory(activeSessionId)
    } else {
      setMessages([])
    }
  }, [activeSessionId])

  const loadSessions = async () => {
    setSessionsLoading(true)
    try {
      const res = await chatAPI.listSessions(userId, 50, familyId)
      const list = res.data.sessions || []
      setSessions(list)
      if (!activeSessionRef.current && list.length > 0) {
        setActiveSessionId(list[0].session_id)
      } else if (activeSessionRef.current && !list.some((item: ChatSession) => item.session_id === activeSessionRef.current)) {
        setActiveSessionId(list[0]?.session_id || '')
      }
    } catch (error) {
      console.error('加载会话列表失败:', error)
    } finally {
      setSessionsLoading(false)
    }
  }

  const loadSessionHistory = async (sessionId: string) => {
    try {
      const res = await chatAPI.getHistory(userId, sessionId, 200, familyId)
      const history = (res.data.history || []).map((item: any) => ({
        role: item.role,
        content: item.content,
        timestamp: item.timestamp ? new Date(item.timestamp) : new Date(),
      }))
      setMessages(history)
      setStreamingMessage('')
      setIsStreaming(false)
      setLoading(false)
    } catch (error) {
      message.error('加载会话历史失败')
    }
  }

  const handleNewSession = async () => {
    try {
      const res = await chatAPI.createSession(userId, '新对话', familyId)
      const session = res.data.session
      setSessions(prev => [session, ...prev])
      setActiveSessionId(session.session_id)
      setMessages([])
      setInputValue('')
    } catch (error) {
      message.error('创建会话失败')
    }
  }

  const refreshSessionsSoon = () => {
    setTimeout(loadSessions, 300)
  }

  const handleSelectSession = (sessionId: string) => {
    if (sessionId === activeSessionId || loading) return
    setActiveSessionId(sessionId)
    setInputValue('')
    setAttachedFiles([])
  }

  const openRenameModal = (session: ChatSession) => {
    setRenamingSession(session)
    setRenameTitle(session.title || '新对话')
  }

  const handleRenameSession = async () => {
    if (!renamingSession) return
    const title = renameTitle.trim() || '新对话'
    try {
      await chatAPI.updateSession(userId, renamingSession.session_id, title, familyId)
      setSessions(prev => prev.map(item =>
        item.session_id === renamingSession.session_id ? { ...item, title } : item
      ))
      setRenamingSession(null)
      setRenameTitle('')
    } catch (error) {
      message.error('重命名会话失败')
    }
  }

  const handleArchiveSession = (session: ChatSession) => {
    Modal.confirm({
      title: '删除这个会话？',
      content: session.title || '新对话',
      okText: '删除',
      okButtonProps: { danger: true },
      cancelText: '取消',
      onOk: async () => {
        try {
          await chatAPI.archiveSession(userId, session.session_id, familyId)
          setSessions(prev => prev.filter(item => item.session_id !== session.session_id))
          if (activeSessionId === session.session_id) {
            const nextSession = sessions.find(item => item.session_id !== session.session_id)
            setActiveSessionId(nextSession?.session_id || '')
            if (!nextSession) setMessages([])
          }
        } catch (error) {
          message.error('删除会话失败')
        }
      },
    })
  }

  const formatSessionTime = (value?: string) => {
    if (!value) return ''
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return ''
    return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
  }

  const currentSession = sessions.find(item => item.session_id === activeSessionId)

  // 初始化WebSocket连接(可选,失败时自动降级到HTTP)
  // Auto-fill input with voice transcript
  useEffect(() => {
    if (transcript) {
      setInputValue(transcript);
    }
  }, [transcript]);

  useEffect(() => {
    const userId = localStorage.getItem('member_name') || 'anonymous'
    
    try {
      const ws = new WebSocket(getChatWebSocketUrl(userId))
      
      ws.onopen = () => {
        console.log('✅ WebSocket已连接 - 启用流式聊天')
        setConnectionMode('websocket')
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
          const fullResponse = data.data.full_response
          const completedSessionId = data.data.session_id
          if (completedSessionId && !activeSessionRef.current) {
            setActiveSessionId(completedSessionId)
            activeSessionRef.current = completedSessionId
          }
          const assistantMessage: Message = {
            role: 'assistant',
            content: fullResponse,
            timestamp: new Date(),
          }
          setMessages(prev => [...prev, assistantMessage])
          // 检测日程创建成功
        if (fullResponse.includes('已添加到日程安排')) {
          message.success('📅 已添加到日程管理，快去查看吧！')
        }
        if (/已新增|已添加到购物清单|财务概览|备婚概览|保险概览|车辆概览|健身概览/.test(fullResponse)) {
          loadModuleSummary()
        }
        setStreamingMessage('')
        setIsStreaming(false)
        setLoading(false)
          refreshSessionsSoon()
        }
      }
      
      ws.onerror = () => {
        console.warn('⚠️ WebSocket连接失败,使用HTTP模式')
        // 静默降级,不显示错误提示
        setLoading(false)
        setIsStreaming(false)
      }
      
      wsRef.current = ws
      
      return () => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.close()
        }
      }
    } catch (error) {
      console.warn('⚠️ WebSocket初始化失败,使用HTTP模式')
    }
  }, [])

  // 共享的 Markdown 渲染组件
  const markdownComponents = {
    p: ({node, ...props}: any) => <p style={{ margin: '8px 0', lineHeight: 1.6 }} {...props} />,
    h1: ({node, ...props}: any) => <h1 style={{ margin: '12px 0 8px', fontSize: '1.5em', fontWeight: 600 }} {...props} />,
    h2: ({node, ...props}: any) => <h2 style={{ margin: '10px 0 6px', fontSize: '1.3em', fontWeight: 600 }} {...props} />,
    h3: ({node, ...props}: any) => <h3 style={{ margin: '8px 0 4px', fontSize: '1.1em', fontWeight: 600 }} {...props} />,
    ul: ({node, ...props}: any) => <ul style={{ margin: '8px 0', paddingLeft: '24px' }} {...props} />,
    ol: ({node, ...props}: any) => <ol style={{ margin: '8px 0', paddingLeft: '24px' }} {...props} />,
    li: ({node, ...props}: any) => <li style={{ margin: '4px 0', lineHeight: 1.6 }} {...props} />,
    code: ({node, inline, ...props}: any) =>
      inline ? (
        <code style={{ background: '#f0f0f0', padding: '2px 6px', borderRadius: 4, fontSize: '0.9em' }} {...props} />
      ) : (
        <pre style={{ background: '#1e1e1e', color: '#d4d4d4', padding: '16px', borderRadius: 8, overflow: 'auto', margin: '8px 0', fontSize: '0.9em', lineHeight: 1.5 }}>
          <code {...props} />
        </pre>
      ),
    blockquote: ({node, ...props}: any) => (
      <blockquote style={{ borderLeft: '4px solid #1890ff', paddingLeft: '16px', margin: '8px 0', color: '#666', background: '#f9f9f9', padding: '8px 16px', borderRadius: '0 8px 8px 0' }} {...props} />
    ),
    table: ({node, ...props}: any) => (
      <div style={{ overflow: 'auto', margin: '8px 0' }}>
        <table style={{ borderCollapse: 'collapse', width: '100%' }} {...props} />
      </div>
    ),
    th: ({node, ...props}: any) => <th style={{ border: '1px solid #d9d9d9', padding: '8px 12px', background: '#fafafa', fontWeight: 600 }} {...props} />,
    td: ({node, ...props}: any) => <td style={{ border: '1px solid #d9d9d9', padding: '8px 12px' }} {...props} />,
    a: ({node, ...props}: any) => <a style={{ color: '#1890ff', textDecoration: 'none' }} {...props} />,
    strong: ({node, ...props}: any) => <strong style={{ fontWeight: 600 }} {...props} />,
    img: ({node, ...props}: any) => (
      <img {...props} style={{ maxWidth: '100%', borderRadius: 8, margin: '8px 0', cursor: 'pointer' }}
        onClick={() => window.open(props.src, '_blank')} />
    ),
  }

  const handleSend = async () => {
    if (!inputValue.trim() && attachedFiles.length === 0) return
    let sessionId = activeSessionId
    if (!sessionId) {
      try {
        const res = await chatAPI.createSession(userId, inputValue.trim().slice(0, 28) || '新对话', familyId)
        const session = res.data.session
        sessionId = session.session_id
        setSessions(prev => [session, ...prev])
        setActiveSessionId(sessionId)
        activeSessionRef.current = sessionId
      } catch (error) {
        message.error('创建会话失败')
        return
      }
    }

    // 构建消息内容
    let messageContent = inputValue
    const imageUrls: { url: string; name: string }[] = []

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
            const uploadRes = await axios.post('/api/photos/upload', formData)
            const imgUrl = uploadRes.data.oss_url || `/api/photos/${file.name}`
            imageUrls.push({ url: imgUrl, name: file.name })
            messageContent += `\n\n![${file.name}](${imgUrl})`
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
      images: imageUrls.length > 0 ? imageUrls : undefined,
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setLoading(true)

    // 使用WebSocket发送消息
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ message: messageContent, session_id: sessionId, family_id: familyId }))
    } else {
      // 降级到HTTP模式
      try {
        const response = await chatAPI.sendMessage(messageContent, userId, sessionId, familyId)
        const respText = response.data.response
        const assistantMessage: Message = {
          role: 'assistant',
          content: respText,
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, assistantMessage])
        // 检测日程创建成功
        if (respText.includes('已添加到日程安排')) {
          message.success('📅 已添加到日程管理，快去查看吧！')
        }
        if (/已新增|已添加到购物清单|财务概览|备婚概览|保险概览|车辆概览|健身概览/.test(respText)) {
          loadModuleSummary()
        }
        refreshSessionsSoon()
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
      if (showCommands && filteredCommands.length === 1) {
        setInputValue(filteredCommands[0].cmd + ' ')
        setShowCommands(false)
        return
      }
      setShowCommands(false)
      handleSend()
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value
    setInputValue(val)
    if (val === '/') {
      setShowCommands(true)
      setCommandFilter('')
    } else if (val.startsWith('/') && !val.includes(' ')) {
      setShowCommands(true)
      setCommandFilter(val.slice(1))
    } else {
      setShowCommands(false)
    }
  }

  // 快捷指令
  const quickActions = [
    { icon: <ClockCircleOutlined />, label: '创建提醒', text: '/remind 明天下午3点开会' },
    { icon: <ShoppingCartOutlined />, label: '添加购物', text: '/shopping 牛奶和鸡蛋' },
    { icon: <BookOutlined />, label: '搜索知识', text: '/knowledge 高血压注意事项' },
    { icon: <MessageOutlined />, label: '看备婚', text: '/wedding summary' },
    { icon: <MessageOutlined />, label: '看保险', text: '/insurance summary' },
    { icon: <MessageOutlined />, label: '看车辆', text: '/vehicle summary' },
    { icon: <MessageOutlined />, label: '看健身', text: '/fitness summary' },
    { icon: <PictureOutlined />, label: '上传照片', action: 'upload' },
  ]

  const handleQuickAction = (action: any) => {
    if (action.action === 'upload') {
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

  // 判断消息是否为确认提示
  const isConfirmMessage = (msg: Message) =>
    msg.role === 'assistant' && msg.content.includes('请确认是否执行')

  // 获取最后一个确认消息的索引
  const lastConfirmIndex = messages.map((m, i) => isConfirmMessage(m) ? i : -1).filter(i => i >= 0).pop() ?? -1

  // 发送确认或取消
  const handleConfirmAction = async (confirmed: boolean) => {
    const text = confirmed ? '是' : '不'
    const userMessage: Message = {
      role: 'user', content: text, timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMessage])
    setLoading(true)
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ message: text, session_id: activeSessionId, family_id: familyId }))
    } else {
      try {
        const response = await chatAPI.sendMessage(text, userId, activeSessionId, familyId)
        setMessages(prev => [...prev, {
          role: 'assistant', content: response.data.response, timestamp: new Date(),
        }])
        refreshSessionsSoon()
      } catch (error) {
        message.error('操作失败')
      } finally {
        setLoading(false)
      }
    }
  }

  return (
    <div className="chat-page-container" style={{ height: 'calc(100vh - 200px)', display: 'flex', gap: 16, minHeight: 520 }}>
      <style>{`
        .chat-page-container { height: calc(100vh - 200px); }
        .chat-session-sidebar {
          width: 280px;
          flex: 0 0 280px;
          display: flex;
          flex-direction: column;
        }
        .chat-main-panel {
          flex: 1;
          min-width: 0;
          display: flex;
          flex-direction: column;
        }
        .chat-context-sidebar {
          width: 300px;
          flex: 0 0 300px;
          display: flex;
          flex-direction: column;
        }
        .session-card {
          border: 1px solid transparent;
          border-radius: 8px;
          cursor: pointer;
          transition: background 0.16s ease, border-color 0.16s ease, transform 0.16s ease;
        }
        .session-card:hover { background: #f6f8fb; border-color: #e6edf5; }
        .session-card.active { background: #eef6ff; border-color: #91caff; }
        .session-actions { opacity: 0; transition: opacity 0.16s ease; }
        .session-card:hover .session-actions, .session-card.active .session-actions { opacity: 1; }
        .message-bubble { transition: all 0.2s ease; }
        .message-bubble:hover { transform: translateY(-1px); }
        .user-bubble pre,
        .user-bubble code { color: #333 !important; }
        @media (max-width: 992px) {
          .chat-page-container { height: auto !important; flex-direction: column; }
          .chat-session-sidebar { width: 100%; flex-basis: auto; max-height: 280px; }
          .chat-context-sidebar { width: 100%; flex-basis: auto; }
          .chat-main-panel { min-height: 620px; }
          .message-bubble { max-width: 85vw !important; }
        }
      `}</style>
      <Card
        className="chat-session-sidebar"
        title={<Space><MessageOutlined /><span>会话</span></Space>}
        extra={
          <Tooltip title="新建会话">
            <Button type="primary" size="small" icon={<PlusOutlined />} onClick={handleNewSession} />
          </Tooltip>
        }
        bodyStyle={{ flex: 1, overflow: 'auto', padding: 10 }}
      >
        {sessions.length === 0 && !sessionsLoading ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="还没有会话"
          >
            <Button type="primary" icon={<PlusOutlined />} onClick={handleNewSession}>
              新建会话
            </Button>
          </Empty>
        ) : (
          <List
            loading={sessionsLoading}
            dataSource={sessions}
            split={false}
            renderItem={(session) => (
              <div
                className={`session-card ${session.session_id === activeSessionId ? 'active' : ''}`}
                onClick={() => handleSelectSession(session.session_id)}
                style={{ padding: '10px 10px 9px', marginBottom: 6 }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                  <MessageOutlined style={{ color: session.session_id === activeSessionId ? '#1677ff' : '#8c8c8c', marginTop: 3 }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <div style={{ flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontWeight: 600, color: '#1f2937' }}>
                        {session.title || '新对话'}
                      </div>
                      <div className="session-actions" onClick={(event) => event.stopPropagation()} style={{ display: 'flex', gap: 2 }}>
                        <Tooltip title="重命名">
                          <Button size="small" type="text" icon={<EditOutlined />} onClick={() => openRenameModal(session)} />
                        </Tooltip>
                        <Tooltip title="删除">
                          <Button size="small" type="text" danger icon={<DeleteOutlined />} onClick={() => handleArchiveSession(session)} />
                        </Tooltip>
                      </div>
                    </div>
                    <div style={{ marginTop: 4, color: '#667085', fontSize: 12, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {session.last_message || '暂无消息'}
                    </div>
                    <div style={{ marginTop: 6, display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: '#98a2b3', fontSize: 11 }}>
                      <span>{session.message_count || 0} 条消息</span>
                      <span>{formatSessionTime(session.updated_at || session.created_at)}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          />
        )}
      </Card>

      <div className="chat-main-panel">
      <Card 
        title={
          <Space>
            <span>{currentSession?.title || '新对话'}</span>
            <Tag color={connectionMode === 'websocket' ? 'green' : 'orange'}>
              {connectionMode === 'websocket' ? '🚀 流式模式' : '⚡ HTTP模式'}
            </Tag>
          </Space>
        }
        style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}
        bodyStyle={{ flex: 1, overflowY: 'auto', padding: '24px' }}
      >
        {messages.length === 0 && !isStreaming ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="开始一个新对话"
            style={{ marginTop: 80 }}
          />
        ) : (
          <List
            dataSource={messages}
            split={false}
            renderItem={(msg) => (
            <div
              style={{
                display: 'flex',
                justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                marginBottom: 16,
                animation: 'fadeInUp 0.3s ease',
              }}
            >
              <Space align="start" size={8}>
                {msg.role === 'assistant' && (
                  <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#1890ff', flexShrink: 0 }} />
                )}
                <Card
                  size="small"
                  className={`message-bubble ${msg.role === 'user' ? 'user-bubble' : 'assistant-bubble'}`}
                  style={{
                    maxWidth: 600,
                    background: msg.role === 'user' ? 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)' : '#f5f5f5',
                    padding: '12px 16px',
                    borderRadius: msg.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                    boxShadow: msg.role === 'user' ? '0 2px 8px rgba(24,144,255,0.2)' : '0 1px 4px rgba(0,0,0,0.06)',
                    border: 'none',
                  }}
                >
                  {/* 图片展示 */}
                  {msg.images && msg.images.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: msg.content ? 8 : 0 }}>
                      {msg.images.map((img, i) => (
                        <div key={i} style={{
                          borderRadius: 8, overflow: 'hidden',
                          border: msg.role === 'user' ? '2px solid rgba(255,255,255,0.3)' : '1px solid #e8e8e8',
                          maxWidth: 240,
                        }}>
                          <img src={img.url} alt={img.name}
                            style={{ width: '100%', height: 'auto', display: 'block', cursor: 'pointer' }}
                            onClick={() => window.open(img.url, '_blank')}
                          />
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="markdown-content" style={{ color: msg.role === 'user' ? '#fff' : '#333', lineHeight: 1.6 }}>
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      rehypePlugins={[rehypeRaw, rehypeHighlight]}
                      components={markdownComponents}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                  <div style={{ fontSize: 11, color: msg.role === 'user' ? 'rgba(255,255,255,0.6)' : '#bbb', marginTop: 4, textAlign: 'right' }}>
                    {new Date(msg.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
                  </div>
                  {/* 确认按钮 */}
                  {msg.role === 'assistant' && msg.content.includes('请确认是否执行') && !loading && (
                    <div style={{ marginTop: 10, display: 'flex', gap: 8, justifyContent: 'center' }}>
                      <Button size="small" type="primary" style={{ borderRadius: 6, minWidth: 70 }}
                        onClick={() => handleConfirmAction(true)}>
                        ✓ 确认
                      </Button>
                      <Button size="small" style={{ borderRadius: 6, minWidth: 70 }}
                        onClick={() => handleConfirmAction(false)}>
                        ✕ 取消
                      </Button>
                    </div>
                  )}
                </Card>
                {msg.role === 'user' && (
                  <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#52c41a', flexShrink: 0 }} />
                )}
              </Space>
            </div>
            )}
          />
        )}
        
        {/* 流式消息显示 */}
        {isStreaming && (
          <div style={{
            display: 'flex',
            justifyContent: 'flex-start',
            marginBottom: 16,
            animation: 'fadeInUp 0.3s ease',
          }}>
            <Space align="start">
              <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#1890ff' }} />
              <Card
                size="small"
                className="streaming-card"
                style={{
                  maxWidth: 600,
                  background: 'linear-gradient(135deg, #f0f5ff 0%, #e6f7ff 100%)',
                  border: '1px solid #91d5ff',
                  borderRadius: 12,
                  boxShadow: '0 2px 8px rgba(24,144,255,0.1)',
                }}
              >
                {streamingMessage ? (
                  <div className="markdown-content" style={{ minHeight: 24, lineHeight: 1.6 }}>
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      rehypePlugins={[rehypeRaw, rehypeHighlight]}
                      components={markdownComponents}
                    >
                      {streamingMessage}
                    </ReactMarkdown>
                    <span className="streaming-cursor" />
                  </div>
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, minHeight: 24 }}>
                    <span className="typing-dot" style={{ animationDelay: '0s' }} />
                    <span className="typing-dot" style={{ animationDelay: '0.15s' }} />
                    <span className="typing-dot" style={{ animationDelay: '0.3s' }} />
                    <span style={{ fontSize: 13, color: '#666', marginLeft: 4 }}>思考中...</span>
                  </div>
                )}
              </Card>
            </Space>
          </div>
        )}

        <style>{`
          @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
          }
          @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
          }
          @keyframes typingDot {
            0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
            40% { transform: scale(1); opacity: 1; }
          }
          .streaming-card { transition: all 0.2s; }
          .streaming-cursor {
            display: inline-block;
            width: 2px;
            height: 1em;
            background: #1890ff;
            margin-left: 2px;
            vertical-align: text-bottom;
            animation: blink 0.8s infinite;
          }
          .typing-dot {
            display: inline-block;
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #1890ff;
            animation: typingDot 1.2s infinite;
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

        {/* 输入区域 */}
        <div className="chat-input-area">
          {/* 附件标签 */}
          {attachedFiles.length > 0 && (
            <div style={{ marginBottom: 8 }}>
              <Space wrap>
                {attachedFiles.map((file, index) => (
                  <Tag key={index} color="blue" closable
                    onClose={() => setAttachedFiles(prev => prev.filter((_, i) => i !== index))}>
                    {file.type.startsWith('image/') ? <PictureOutlined /> : <FileTextOutlined />} {file.name}
                  </Tag>
                ))}
              </Space>
            </div>
          )}
          <Upload
            id="file-upload-input"
            multiple
            beforeUpload={() => false}
            onChange={handleFileChange}
            showUploadList={false}
            accept="image/*,.pdf,.doc,.docx,.txt,.md"
          >
            <Button size="small" icon={<PaperClipOutlined />} type="text" style={{ marginBottom: 4 }}>
              附件
            </Button>
          </Upload>
          <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
            <div style={{ flex: 1, position: 'relative' }}>
              {/* 指令选择浮层 */}
              {showCommands && (
                <div style={{
                  position: 'absolute', bottom: '100%', left: 0, right: 0, zIndex: 100,
                  marginBottom: 4, background: '#fff', borderRadius: 8,
                  boxShadow: '0 4px 16px rgba(0,0,0,0.12)', overflow: 'hidden',
                  maxHeight: 240, overflowY: 'auto',
                }}>
                  <div style={{ padding: '8px 12px', fontSize: 12, color: '#999', borderBottom: '1px solid #f0f0f0' }}>
                    输入指令快速操作
                  </div>
                  {filteredCommands.map(cmd => (
                    <div key={cmd.cmd} onClick={() => {
                      setInputValue(cmd.cmd + ' ')
                      setShowCommands(false)
                      inputRef.current?.focus()
                    }} style={{
                      padding: '10px 12px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 10,
                      borderBottom: '1px solid #f5f5f5', transition: 'background 0.15s',
                    }}
                      onMouseEnter={e => e.currentTarget.style.background = '#f0f5ff'}
                      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                    >
                      <span style={{ fontSize: 18 }}>{cmd.icon}</span>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 600, color: '#1890ff', fontSize: 14 }}>
                          {cmd.cmd}
                        </div>
                        <div style={{ fontSize: 12, color: '#666' }}>{cmd.desc}</div>
                      </div>
                      <div style={{ fontSize: 11, color: '#bbb' }}>{cmd.example}</div>
                    </div>
                  ))}
                </div>
              )}
              <TextArea
                ref={inputRef}
                value={inputValue}
                onChange={handleInputChange}
                onKeyPress={handleKeyPress}
                placeholder="输入消息... / 可输 / 查看指令"
                autoSize={{ minRows: 1, maxRows: 4 }}
                disabled={loading}
                style={{ flex: 1, borderRadius: 8 }}
              />
            </div>
            <Button
              type="primary"
              icon={loading ? undefined : <SendOutlined />}
              onClick={handleSend}
              loading={loading}
              size="large"
              style={{ height: 40, minWidth: 80, borderRadius: 8 }}
            >
              {loading ? '' : '发送'}
            </Button>
          </div>
        </div>

        <div style={{ marginTop: 8, fontSize: 12, color: '#999' }}>
          💡 输入 <span style={{ color: '#1890ff', fontWeight: 600 }}>/</span> 使用指令快速操作；现在也能在对话里直接查看备婚、保险、车辆、健身和财务摘要
        </div>
      </Card>
      </div>

      <Card
        className="chat-context-sidebar"
        title={<Space><MessageOutlined /><span>家庭上下文</span></Space>}
        extra={<Button size="small" type="text" onClick={loadModuleSummary}>刷新</Button>}
        bodyStyle={{ padding: 12, overflow: 'auto' }}
      >
        <Space direction="vertical" size={12} style={{ width: '100%' }}>
          <Card size="small" style={{ borderRadius: 8 }}>
            <Space style={{ width: '100%', justifyContent: 'space-between' }}>
              <Text strong>备婚</Text>
              <Button size="small" type="link" onClick={() => setInputValue('/wedding summary')}>查看</Button>
            </Space>
            <div style={{ marginTop: 8, fontSize: 12, color: '#667085' }}>
              待办 {moduleSummary.wedding?.todo_count || 0} · 预算 ¥{Number(moduleSummary.wedding?.budget_total || 0).toLocaleString()}
            </div>
          </Card>

          <Card size="small" style={{ borderRadius: 8 }}>
            <Space style={{ width: '100%', justifyContent: 'space-between' }}>
              <Text strong>保险</Text>
              <Button size="small" type="link" onClick={() => setInputValue('/insurance summary')}>查看</Button>
            </Space>
            <div style={{ marginTop: 8, fontSize: 12, color: '#667085' }}>
              保单 {moduleSummary.insurance?.policy_count || 0} · 理赔 {moduleSummary.insurance?.claim_count || 0}
            </div>
          </Card>

          <Card size="small" style={{ borderRadius: 8 }}>
            <Space style={{ width: '100%', justifyContent: 'space-between' }}>
              <Text strong>车辆</Text>
              <Button size="small" type="link" onClick={() => setInputValue('/vehicle summary')}>查看</Button>
            </Space>
            <div style={{ marginTop: 8, fontSize: 12, color: '#667085' }}>
              档案 {moduleSummary.vehicle?.vehicle_count || 0} · 费用 ¥{Number(moduleSummary.vehicle?.expense_total || 0).toLocaleString()}
            </div>
          </Card>

          <Card size="small" style={{ borderRadius: 8 }}>
            <Space style={{ width: '100%', justifyContent: 'space-between' }}>
              <Text strong>健身</Text>
              <Button size="small" type="link" onClick={() => setInputValue('/fitness summary')}>查看</Button>
            </Space>
            <div style={{ marginTop: 8, fontSize: 12, color: '#667085' }}>
              训练 {moduleSummary.fitness?.workout_count || 0} · 体重 {moduleSummary.fitness?.avg_weight || 0}kg
            </div>
          </Card>

          <Card size="small" style={{ borderRadius: 8 }}>
            <Space style={{ width: '100%', justifyContent: 'space-between' }}>
              <Text strong>财务</Text>
              <Button size="small" type="link" onClick={() => setInputValue('/finance summary')}>查看</Button>
            </Space>
            <div style={{ marginTop: 8, fontSize: 12, color: '#667085' }}>
              收入 ¥{Number(moduleSummary.finance?.total_income || 0).toLocaleString()} · 支出 ¥{Number(moduleSummary.finance?.total_expense || 0).toLocaleString()}
            </div>
          </Card>

          <Divider style={{ margin: '4px 0' }} />

          <Card size="small" style={{ borderRadius: 8 }}>
            <Text strong>顺手可发</Text>
            <Space direction="vertical" size={6} style={{ width: '100%', marginTop: 8 }}>
              <Button block onClick={() => setInputValue('帮我加一个车险续保提醒')}>加车险续保提醒</Button>
              <Button block onClick={() => setInputValue('帮我记一条今晚力量训练 45分钟 320kcal')}>记训练</Button>
              <Button block onClick={() => setInputValue('看看这个月财务情况')}>看本月财务</Button>
            </Space>
          </Card>
        </Space>
      </Card>

      <Modal
        title="重命名会话"
        open={!!renamingSession}
        onOk={handleRenameSession}
        onCancel={() => {
          setRenamingSession(null)
          setRenameTitle('')
        }}
        okText="保存"
        cancelText="取消"
      >
        <Input
          value={renameTitle}
          onChange={(event) => setRenameTitle(event.target.value)}
          maxLength={80}
          placeholder="输入会话标题"
          onPressEnter={handleRenameSession}
        />
      </Modal>
    </div>
  )
}

export default ChatPage
