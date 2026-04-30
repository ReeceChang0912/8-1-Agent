import React, { useState, useEffect } from 'react'
import { Card, List, Button, Badge, Tag, Empty, Modal, message } from 'antd'
import { CheckCircleOutlined, ClockCircleOutlined, UserOutlined } from '@ant-design/icons'
import axios from 'axios'

interface Task {
  task_id: string
  from_member: string
  to_member: string
  content: string
  task_type: string
  priority: string
  status: string
  created_at: string
  completed_at?: string
  notes: string
}

interface TaskNotificationProps {
  memberName: string
  onTaskComplete?: () => void
}

const TaskNotification: React.FC<TaskNotificationProps> = ({ memberName, onTaskComplete }) => {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(false)
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    if (memberName) {
      loadTasks()
      loadUnreadCount()
    }
  }, [memberName])

  const loadTasks = async () => {
    try {
      const res = await axios.get('/api/tasks/my', {
        params: { member_name: memberName, status: 'pending' }
      })
      setTasks(res.data.tasks || [])
    } catch (error) {
      console.error('加载任务失败')
    }
  }

  const loadUnreadCount = async () => {
    try {
      const res = await axios.get('/api/tasks/unread-count', {
        params: { member_name: memberName }
      })
      setUnreadCount(res.data.count || 0)
    } catch (error) {
      console.error('加载未读数失败')
    }
  }

  const handleCompleteTask = async (taskId: string) => {
    try {
      await axios.post(`/api/tasks/${taskId}/complete`)
      message.success('✅ 任务已完成')
      
      // 重新加载
      loadTasks()
      loadUnreadCount()
      
      if (onTaskComplete) {
        onTaskComplete()
      }
    } catch (error) {
      message.error('操作失败')
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'red'
      case 'normal': return 'blue'
      case 'low': return 'green'
      default: return 'default'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'shopping': return '🛒'
      case 'reminder': return '⏰'
      case 'message': return '💬'
      default: return '📝'
    }
  }

  if (tasks.length === 0) {
    return null
  }

  return (
    <Card
      title={
        <span>
          <Badge count={unreadCount} overflowCount={99}>
            📋 我的任务
          </Badge>
        </span>
      }
      style={{ marginBottom: 16 }}
    >
      <List
        dataSource={tasks}
        renderItem={(task) => (
          <List.Item
            actions={[
              <Button
                type="primary"
                size="small"
                icon={<CheckCircleOutlined />}
                onClick={() => handleCompleteTask(task.task_id)}
              >
                完成
              </Button>
            ]}
          >
            <List.Item.Meta
              avatar={
                <div style={{ fontSize: 24 }}>
                  {getTypeIcon(task.task_type)}
                </div>
              }
              title={
                <div>
                  <strong>{task.content}</strong>
                  <Tag color={getPriorityColor(task.priority)} style={{ marginLeft: 8 }}>
                    {task.priority === 'high' ? '高优先级' : task.priority === 'normal' ? '普通' : '低优先级'}
                  </Tag>
                </div>
              }
              description={
                <div>
                  <div style={{ marginTop: 4 }}>
                    <UserOutlined /> 来自: <strong>{task.from_member}</strong>
                  </div>
                  {task.notes && (
                    <div style={{ marginTop: 4, color: '#666' }}>
                      📝 {task.notes}
                    </div>
                  )}
                  <div style={{ marginTop: 4, fontSize: 12, color: '#999' }}>
                    <ClockCircleOutlined /> {new Date(task.created_at).toLocaleString()}
                  </div>
                </div>
              }
            />
          </List.Item>
        )}
      />
    </Card>
  )
}

export default TaskNotification
