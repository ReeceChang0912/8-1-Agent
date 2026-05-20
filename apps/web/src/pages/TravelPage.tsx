import React, { useEffect, useMemo, useState } from 'react'
import { Card, Row, Col, Statistic, Tabs, List, Tag, Button, Modal, Form, Input, InputNumber, DatePicker, Space, Typography, message, Empty, Spin, Select } from 'antd'
import { CalendarOutlined, DollarOutlined, CheckCircleOutlined, PlusOutlined, DeleteOutlined, EditOutlined, EnvironmentOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { lifeModulesAPI, membersAPI } from '../services/api'

const { Text, Paragraph, Title } = Typography

const tabConfig = {
  itinerary: { recordType: 'itinerary', title: '行程计划', statuses: ['计划中', '已确认', '已完成'] },
  booking: { recordType: 'booking', title: '预订记录', statuses: ['待预订', '已预订', '已完成'] },
  budget: { recordType: 'budget', title: '旅行预算', statuses: ['预算中', '已支付', '已结算'] },
  packing: { recordType: 'packing', title: '打包清单', statuses: ['待准备', '已打包', '已带齐'] },
}

const TravelPage: React.FC = () => {
  const familyId = localStorage.getItem('family_id') || ''
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [tab, setTab] = useState<'itinerary' | 'booking' | 'budget' | 'packing'>('itinerary')
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<any>(null)
  const [items, setItems] = useState<any[]>([])
  const [stats, setStats] = useState<any>({})
  const [keyword, setKeyword] = useState('')
  const [members, setMembers] = useState<any[]>([])
  const [memberFilter, setMemberFilter] = useState('all')
  const [form] = Form.useForm()

  const load = async () => {
    setLoading(true)
    try {
      const [listRes, statsRes] = await Promise.all([
        lifeModulesAPI.travel.list(familyId),
        lifeModulesAPI.travel.stats(familyId),
      ])
      setItems(listRes.data.items || [])
      setStats(statsRes.data || {})
    } catch {
      message.error('加载旅行管理失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  useEffect(() => {
    membersAPI.getAll().then(res => setMembers(res.data.members || [])).catch(() => setMembers([]))
  }, [])

  const grouped = useMemo(() => ({
    itinerary: items.filter(item => item.record_type === 'itinerary'),
    booking: items.filter(item => item.record_type === 'booking'),
    budget: items.filter(item => item.record_type === 'budget'),
    packing: items.filter(item => item.record_type === 'packing'),
  }), [items])

  const filtered = useMemo(() => {
    const q = keyword.trim().toLowerCase()
    if (!q) return grouped
    const filterItems = (list: any[]) =>
      list.filter(item =>
        `${item.title || ''} ${item.destination || ''} ${item.companion || ''} ${item.provider || ''} ${item.status || ''} ${item.note || ''}`.toLowerCase().includes(q)
        && (memberFilter === 'all' || `${item.companion || ''}`.includes(memberFilter)),
      )
    return {
      itinerary: filterItems(grouped.itinerary),
      booking: filterItems(grouped.booking),
      budget: filterItems(grouped.budget),
      packing: filterItems(grouped.packing),
    }
  }, [grouped, keyword, memberFilter])

  const currentConfig = tabConfig[tab]

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    form.setFieldsValue({ record_type: currentConfig.recordType, status: currentConfig.statuses[0], amount: 0 })
    setOpen(true)
  }

  const editItem = (item: any) => {
    setEditing(item)
    const nextTab = item.record_type === 'booking' ? 'booking' : item.record_type === 'budget' ? 'budget' : item.record_type === 'packing' ? 'packing' : 'itinerary'
    setTab(nextTab)
    form.setFieldsValue({
      ...item,
      travel_date: item.travel_date ? dayjs(item.travel_date) : undefined,
      end_date: item.end_date ? dayjs(item.end_date) : undefined,
    })
    setOpen(true)
  }

  const save = async () => {
    const values = await form.validateFields()
    setSaving(true)
    try {
      const payload = {
        ...values,
        family_id: familyId,
        record_type: tabConfig[tab].recordType,
        travel_date: values.travel_date ? values.travel_date.format('YYYY-MM-DD') : '',
        end_date: values.end_date ? values.end_date.format('YYYY-MM-DD') : '',
      }
      if (editing?.id) await lifeModulesAPI.travel.update(editing.id, payload)
      else await lifeModulesAPI.travel.add(payload)
      message.success('已保存')
      setOpen(false)
      await load()
    } catch {
      message.error('保存失败')
    } finally {
      setSaving(false)
    }
  }

  const remove = async (id: number) => {
    await lifeModulesAPI.travel.remove(id, familyId)
    message.success('已删除')
    await load()
  }

  return (
    <div>
      <Card style={{ marginBottom: 16, borderRadius: 8 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} lg={8}>
            <Title level={4} style={{ margin: 0 }}>旅行管理</Title>
            <Paragraph style={{ marginTop: 8, marginBottom: 0 }}>
              行程、预算、预订和打包清单放在一起，出门前要做的事就能一次看清。
            </Paragraph>
          </Col>
          <Col xs={12} md={6} lg={4}><Statistic title="记录总数" value={stats.total_count || 0} prefix={<CalendarOutlined />} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="近期行程" value={stats.upcoming_count || 0} prefix={<CheckCircleOutlined />} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="预订记录" value={stats.booking_count || 0} prefix={<EnvironmentOutlined />} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="预算合计" value={stats.budget_total || 0} prefix={<DollarOutlined />} /></Col>
        </Row>
      </Card>

      <Card extra={<Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>新增{currentConfig.title}</Button>} style={{ borderRadius: 8 }}>
        <Space wrap style={{ marginBottom: 16 }}>
          <Input.Search
            allowClear
            placeholder="搜索标题、目的地、同行人、备注"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            style={{ width: 360 }}
          />
          <Select value={memberFilter} onChange={setMemberFilter} style={{ width: 180 }} options={[{ label: '全部成员', value: 'all' }, ...members.map(member => ({ label: member.name, value: member.name }))]} />
        </Space>
        {loading ? <Spin /> : (
          <Tabs activeKey={tab} onChange={(value) => setTab(value as typeof tab)} items={[
            {
              key: 'itinerary',
              label: '行程',
              children: filtered.itinerary.length ? (
                <List dataSource={[...filtered.itinerary].sort((a, b) => String(a.travel_date || '').localeCompare(String(b.travel_date || '')))} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => editItem(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta
                      avatar={<CalendarOutlined />}
                      title={<Space><Text strong>{item.title}</Text><Tag>{item.status}</Tag></Space>}
                      description={`${item.destination || '未填写目的地'} · ${item.companion || '未填写同行人'} · ${item.note || '未填写备注'}`}
                    />
                    <div style={{ textAlign: 'right' }}>
                      <Text type="secondary">{item.travel_date || '未设置出发日'}</Text>
                      <div><Text type="secondary">{item.end_date || '未设置返程日'}</Text></div>
                    </div>
                  </List.Item>
                )} />
              ) : <Empty description={keyword ? '没有匹配结果' : '暂无行程计划'} />,
            },
            {
              key: 'booking',
              label: '预订',
              children: filtered.booking.length ? (
                <List dataSource={filtered.booking} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => editItem(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta
                      avatar={<EnvironmentOutlined />}
                      title={<Space><Text strong>{item.title}</Text><Tag color="blue">{item.status}</Tag></Space>}
                      description={`${item.provider || '未填写商家'} · ${item.destination || '未填写目的地'} · ${item.note || '未填写备注'}`}
                    />
                    <Text strong>¥{Number(item.amount || 0).toLocaleString()}</Text>
                  </List.Item>
                )} />
              ) : <Empty description={keyword ? '没有匹配结果' : '暂无预订记录'} />,
            },
            {
              key: 'budget',
              label: '预算',
              children: filtered.budget.length ? (
                <List dataSource={filtered.budget} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => editItem(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta
                      avatar={<DollarOutlined />}
                      title={<Space><Text strong>{item.title}</Text><Tag>{item.status}</Tag></Space>}
                      description={`${item.destination || '未填写目的地'} · ${item.note || '未填写备注'}`}
                    />
                    <Text strong>¥{Number(item.amount || 0).toLocaleString()}</Text>
                  </List.Item>
                )} />
              ) : <Empty description={keyword ? '没有匹配结果' : '暂无预算记录'} />,
            },
            {
              key: 'packing',
              label: '打包',
              children: filtered.packing.length ? (
                <List dataSource={filtered.packing} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => editItem(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta
                      avatar={<CheckCircleOutlined />}
                      title={<Space><Text strong>{item.title}</Text><Tag color={item.status === '已带齐' ? 'green' : 'gold'}>{item.status}</Tag></Space>}
                      description={`${item.destination || '未填写目的地'} · ${item.companion || '未填写同行人'} · ${item.note || '未填写备注'}`}
                    />
                  </List.Item>
                )} />
              ) : <Empty description={keyword ? '没有匹配结果' : '暂无打包清单'} />,
            },
          ]} />
        )}
      </Card>

      <Modal title={`${editing ? '编辑' : '新增'}${currentConfig.title}`} open={open} onCancel={() => setOpen(false)} onOk={save} confirmLoading={saving} okText="保存" cancelText="取消" destroyOnHidden>
        <Form layout="vertical" form={form}>
          <Form.Item name="title" label="标题" rules={[{ required: true, message: '请输入标题' }]}><Input /></Form.Item>
          <Form.Item name="destination" label="目的地"><Input /></Form.Item>
          <Form.Item name="companion" label="同行人"><Input /></Form.Item>
          <Form.Item name="provider" label="预订平台/商家"><Input /></Form.Item>
          <Form.Item name="status" label="状态" rules={[{ required: true, message: '请选择状态' }]}>
            <Select options={currentConfig.statuses.map(value => ({ label: value, value }))} />
          </Form.Item>
          <Form.Item name="travel_date" label="出发日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="end_date" label="返程日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="amount" label="金额/预算"><InputNumber min={0} step={0.01} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="note" label="备注"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default TravelPage
