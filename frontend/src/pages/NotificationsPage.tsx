import React, { useState, useEffect } from 'react'
import { Card, List, Badge, Button, Space, Tag, Empty, Typography, Spin, message as msgApi } from 'antd'
import { BellOutlined, CheckCircleOutlined, DeleteOutlined, RobotOutlined, CalendarOutlined, ShoppingOutlined, MessageOutlined } from '@ant-design/icons'
import api from '../services/api'

const { Title, Text } = Typography

interface Notification {
  id: string
  member_name: string
  title: string
  message: string
  type: string
  priority: string
  is_read: boolean
  created_at: string
  read_at?: string
}

const NotificationsPage: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'all' | 'unread'>('unread')

  const userId = localStorage.getItem('member_name') || 'anonymous'

  // 加载通知
  const loadNotifications = async (type: 'all' | 'unread' = 'unread') => {
    setLoading(true)
    try {
      if (type === 'unread') {
        const response = await api.get(`/api/notifications/unread/${userId}`)
        if (response.data.success) {
          setNotifications(response.data.notifications)
          setUnreadCount(response.data.unread_count)
        }
      } else {
        const response = await api.get(`/api/notifications/all/${userId}`)
        if (response.data.success) {
          setNotifications(response.data.notifications)
        }
      }
    } catch (error) {
      console.error('加载通知失败:', error)
      msgApi.error('加载通知失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadNotifications(activeTab)
    
    // 每30秒刷新一次未读数量
    const interval = setInterval(() => {
      api.get(`/api/notifications/unread-count/${userId}`).then(res => {
        if (res.data.success) {
          setUnreadCount(res.data.unread_count)
        }
      })
    }, 30000)
    
    return () => clearInterval(interval)
  }, [activeTab])

  // 标记为已读
  const handleMarkRead = async (notifId: string) => {
    try {
      await api.post(`/api/notifications/mark-read/${notifId}`)
      msgApi.success('已标记为已读')
      loadNotifications(activeTab)
    } catch (error) {
      msgApi.error('操作失败')
    }
  }

  // 标记所有为已读
  const handleMarkAllRead = async () => {
    try {
      await api.post(`/api/notifications/mark-all-read/${userId}`)
      msgApi.success('全部标记为已读')
      loadNotifications(activeTab)
    } catch (error) {
      msgApi.error('操作失败')
    }
  }

  // 删除通知
  const handleDelete = async (notifId: string) => {
    try {
      await api.delete(`/api/notifications/${notifId}`)
      msgApi.success('已删除')
      loadNotifications(activeTab)
    } catch (error) {
      msgApi.error('删除失败')
    }
  }

  // 获取优先级颜色
  const getPriorityColor = (priority: string) => {
    const colors: Record<string, string> = {
      urgent: 'red',
      high: 'orange',
      normal: 'blue',
      low: 'green'
    }
    return colors[priority] || 'default'
  }

  // 获取类型图标
  const getTypeIcon = (type: string) => {
    const icons: Record<string, React.ReactNode> = {
      task: <ShoppingOutlined />,
      reminder: <CalendarOutlined />,
      anniversary: <BellOutlined />,
      system: <RobotOutlined />,
      general: <MessageOutlined />
    }
    return icons[type] || <MessageOutlined />
  }

  // 格式化时间
  const formatTime = (timeStr: string) => {
    const date = new Date(timeStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    
    if (diff < 60000) return '刚刚'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
    return date.toLocaleDateString('zh-CN')
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 16 }}>
          <Title level={3} style={{ margin: 0 }}>
            <Badge count={unreadCount} offset={[-5, 5]}>
              <BellOutlined style={{ marginRight: 8 }} />
              消息通知
            </Badge>
          </Title>
          
          <Space>
            <Button 
              type={activeTab === 'unread' ? 'primary' : 'default'}
              onClick={() => setActiveTab('unread')}
            >
              未读 ({unreadCount})
            </Button>
            <Button 
              type={activeTab === 'all' ? 'primary' : 'default'}
              onClick={() => setActiveTab('all')}
            >
              全部
            </Button>
            {unreadCount > 0 && (
              <Button onClick={handleMarkAllRead}>
                <CheckCircleOutlined /> 全部已读
              </Button>
            )}
          </Space>
        </Space>

        <Spin spinning={loading}>
          {notifications.length === 0 ? (
            <Empty 
              description={activeTab === 'unread' ? '暂无未读消息' : '暂无消息'} 
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          ) : (
            <List
              dataSource={notifications}
              renderItem={(item) => (
                <List.Item
                  actions={[
                    !item.is_read && (
                      <Button 
                        size="small" 
                        type="link"
                        onClick={() => handleMarkRead(item.id)}
                      >
                        标记已读
                      </Button>
                    ),
                    <Button 
                      size="small" 
                      type="text" 
                      danger
                      icon={<DeleteOutlined />}
                      onClick={() => handleDelete(item.id)}
                    />
                  ]}
                  style={{
                    background: item.is_read ? '#fff' : '#f0f7ff',
                    borderLeft: `4px solid ${getPriorityColor(item.priority)}`,
                    marginBottom: 8,
                    padding: '12px 16px'
                  }}
                >
                  <List.Item.Meta
                    avatar={
                      <Badge dot={!item.is_read}>
                        <div style={{
                          width: 40,
                          height: 40,
                          borderRadius: '50%',
                          background: '#e6f4ff',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: 20
                        }}>
                          {getTypeIcon(item.type)}
                        </div>
                      </Badge>
                    }
                    title={
                      <Space>
                        <Text strong>{item.title}</Text>
                        <Tag color={getPriorityColor(item.priority)}>
                          {item.priority.toUpperCase()}
                        </Tag>
                      </Space>
                    }
                    description={
                      <div>
                        <Text>{item.message}</Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {formatTime(item.created_at)}
                        </Text>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          )}
        </Spin>
      </Card>
    </div>
  )
}

export default NotificationsPage
