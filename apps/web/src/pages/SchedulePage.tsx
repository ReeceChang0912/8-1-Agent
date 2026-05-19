import React, { useState, useEffect, useMemo } from 'react'
import { Card, List, Button, Form, Input, DatePicker, message, Empty, Row, Col, Space, Tag, Divider } from 'antd'
import { PlusOutlined, CalendarOutlined, DeleteOutlined, SearchOutlined, ThunderboltOutlined, ClockCircleOutlined } from '@ant-design/icons'
import { scheduleAPI } from '../services/api'
import dayjs from 'dayjs'
import { useNavigate } from 'react-router-dom'

const SchedulePage: React.FC = () => {
  const familyId = localStorage.getItem('family_id') || ''
  const memberName = localStorage.getItem('member_name') || ''
  const navigate = useNavigate()
  const [reminders, setReminders] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [keyword, setKeyword] = useState('')
  const [recommendations, setRecommendations] = useState<any[]>([])
  const [freeTimes, setFreeTimes] = useState<any[]>([])
  const [form] = Form.useForm()

  useEffect(() => {
    loadReminders()
    loadSuggestions()
  }, [])

  const loadReminders = async () => {
    setLoading(true)
    try {
      const res = await scheduleAPI.getAll(familyId)
      setReminders((res.data.reminders || []).sort((a: any, b: any) => String(a.date || '').localeCompare(String(b.date || ''))))
    } catch (error) {
      message.error('加载日程失败')
    } finally {
      setLoading(false)
    }
  }

  const loadSuggestions = async () => {
    if (!memberName) return
    try {
      const today = dayjs().format('YYYY-MM-DD')
      const [recommendationRes, freeTimesRes] = await Promise.all([
        scheduleAPI.getRecommendations(memberName, today),
        scheduleAPI.getFreeTimes(memberName, today),
      ])
      setRecommendations(recommendationRes.data.recommendations || [])
      setFreeTimes(freeTimesRes.data.free_times || [])
    } catch {
      setRecommendations([])
      setFreeTimes([])
    }
  }

  const handleAdd = async (values: any) => {
    try {
      const dateStr = values.date.format('YYYY-MM-DD')
      await scheduleAPI.add(dateStr, values.event, familyId, memberName)
      message.success('提醒添加成功')
      form.resetFields()
      loadReminders()
    } catch (error) {
      message.error('添加失败')
    }
  }

  const filteredReminders = useMemo(() => {
    const q = keyword.trim().toLowerCase()
    if (!q) return reminders
    return reminders.filter((item) =>
      `${item.date || ''} ${item.event || ''} ${item.member || ''}`.toLowerCase().includes(q),
    )
  }, [keyword, reminders])

  const groupedReminders = useMemo(() => {
    const now = dayjs()
    const upcoming = filteredReminders.filter((item) => dayjs(item.date).isAfter(now.subtract(1, 'day')))
    const past = filteredReminders.filter((item) => !dayjs(item.date).isAfter(now.subtract(1, 'day')))
    return { upcoming, past }
  }, [filteredReminders])

  const removeReminder = async (id: number) => {
    try {
      await scheduleAPI.remove(id, familyId)
      message.success('提醒已删除')
      await loadReminders()
    } catch {
      message.error('删除失败')
    }
  }

  return (
    <div>
      <Card style={{ marginBottom: 16, borderRadius: 8 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} lg={12}>
            <Space>
              <CalendarOutlined style={{ color: '#1677ff', fontSize: 22 }} />
              <div>
                <div style={{ fontSize: 18, fontWeight: 700 }}>家庭日程</div>
                <div style={{ color: '#667085' }}>生日、纪念日、接送安排、重要提醒，都放在一处看。</div>
              </div>
            </Space>
          </Col>
          <Col xs={12} md={6}><Tag color="blue">本月提醒 {filteredReminders.length}</Tag></Col>
          <Col xs={12} md={6}><Button icon={<ThunderboltOutlined />} onClick={() => navigate('/modules')}>打开模块中心</Button></Col>
        </Row>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} md={10} lg={8}>
          <Card title="添加提醒">
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

          <Card title="智能建议" style={{ marginTop: 16, borderRadius: 8 }} extra={<ClockCircleOutlined />}>
            <Space direction="vertical" size={12} style={{ width: '100%' }}>
              <div>
                <div style={{ fontWeight: 600, marginBottom: 6 }}>推荐安排</div>
                {recommendations.length ? (
                  recommendations.slice(0, 3).map((item: any, idx: number) => (
                    <div key={idx} style={{ color: '#667085', fontSize: 12, marginBottom: 6 }}>
                      {item.title || item.event || item.suggestion}
                    </div>
                  ))
                ) : (
                  <div style={{ color: '#667085', fontSize: 12 }}>暂无推荐</div>
                )}
              </div>
              <Divider style={{ margin: '4px 0' }} />
              <div>
                <div style={{ fontWeight: 600, marginBottom: 6 }}>空闲时段</div>
                {freeTimes.length ? (
                  freeTimes.slice(0, 4).map((item: any, idx: number) => (
                    <div key={idx} style={{ color: '#667085', fontSize: 12, marginBottom: 6 }}>
                      {item.start_time || item.start || '-'} - {item.end_time || item.end || '-'}
                    </div>
                  ))
                ) : (
                  <div style={{ color: '#667085', fontSize: 12 }}>暂无空闲时段建议</div>
                )}
              </div>
            </Space>
          </Card>
        </Col>

        <Col xs={24} md={14} lg={16}>
          <Card title="日程列表" extra={<CalendarOutlined />}>
            <Input.Search
              allowClear
              prefix={<SearchOutlined />}
              placeholder="搜索日期、事件、成员"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              style={{ marginBottom: 16, maxWidth: 320 }}
            />
            {filteredReminders.length === 0 ? (
              <Empty description={keyword ? '没有匹配的日程' : '暂无日程安排'} />
            ) : (
              <Space direction="vertical" size={16} style={{ width: '100%' }}>
                <Card size="small" style={{ borderRadius: 8 }}>
                  <Space direction="vertical" size={8} style={{ width: '100%' }}>
                    <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                      <strong>最近将到来</strong>
                      <Tag color="green">{groupedReminders.upcoming.length}</Tag>
                    </Space>
                    <List
                      dataSource={groupedReminders.upcoming.slice(0, 5)}
                      loading={loading}
                      renderItem={(item: any) => (
                        <List.Item actions={[
                          <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => removeReminder(item.id)}>删除</Button>,
                        ]}>
                          <List.Item.Meta
                            title={<span>📅 {dayjs(item.date).format('YYYY年MM月DD日')} {item.event}</span>}
                            description={item.member ? `负责人：${item.member}` : '未指定负责人'}
                          />
                        </List.Item>
                      )}
                    />
                  </Space>
                </Card>
                <Card size="small" style={{ borderRadius: 8 }}>
                  <Space direction="vertical" size={8} style={{ width: '100%' }}>
                    <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                      <strong>历史与已过</strong>
                      <Tag>{groupedReminders.past.length}</Tag>
                    </Space>
                    <List
                      dataSource={groupedReminders.past}
                      renderItem={(item: any) => (
                        <List.Item actions={[
                          <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => removeReminder(item.id)}>删除</Button>,
                        ]}>
                          <List.Item.Meta
                            title={<span>📌 {dayjs(item.date).format('YYYY年MM月DD日')} {item.event}</span>}
                            description={item.member ? `负责人：${item.member}` : '未指定负责人'}
                          />
                        </List.Item>
                      )}
                    />
                  </Space>
                </Card>
              </Space>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default SchedulePage
