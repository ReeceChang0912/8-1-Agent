import React, { useState, useEffect } from 'react'
import { Card, List, Button, Form, Input, DatePicker, message, Empty } from 'antd'
import { PlusOutlined, CalendarOutlined } from '@ant-design/icons'
import { scheduleAPI } from '../services/api'
import dayjs from 'dayjs'

const SchedulePage: React.FC = () => {
  const [reminders, setReminders] = useState([])
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    loadReminders()
  }, [])

  const loadReminders = async () => {
    setLoading(true)
    try {
      const res = await scheduleAPI.getAll()
      setReminders(res.data.reminders)
    } catch (error) {
      message.error('加载日程失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = async (values: any) => {
    try {
      const dateStr = values.date.format('YYYY-MM-DD')
      await scheduleAPI.add(dateStr, values.event)
      message.success('提醒添加成功')
      form.resetFields()
      loadReminders()
    } catch (error) {
      message.error('添加失败')
    }
  }

  return (
    <div style={{ display: 'flex', gap: 16 }}>
      <Card title="添加提醒" style={{ width: 400 }}>
        <Form form={form} onFinish={handleAdd} layout="vertical">
          <Form.Item
            name="date"
            label="日期"
            rules={[{ required: true, message: '请选择日期' }]}
          >
            <DatePicker style={{ width: '100%' }} placeholder="选择日期" />
          </Form.Item>

          <Form.Item
            name="event"
            label="事件"
            rules={[{ required: true, message: '请输入事件内容' }]}
          >
            <Input.TextArea
              rows={4}
              placeholder="例如：下午3点开会、晚上7点家庭聚餐"
            />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" icon={<PlusOutlined />} block>
              添加提醒
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card
        title="日程列表"
        style={{ flex: 1 }}
        extra={<CalendarOutlined />}
      >
        {reminders.length === 0 ? (
          <Empty description="暂无日程安排" />
        ) : (
          <List
            dataSource={reminders}
            loading={loading}
            renderItem={(item: any) => (
              <List.Item>
                <List.Item.Meta
                  title={
                    <span style={{ fontSize: 16 }}>
                      📅 {dayjs(item.date).format('YYYY年MM月DD日')}
                    </span>
                  }
                  description={
                    <div style={{ marginTop: 8, fontSize: 14 }}>
                      {item.event}
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </Card>
    </div>
  )
}

export default SchedulePage
