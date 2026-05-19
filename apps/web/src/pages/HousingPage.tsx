import React, { useEffect, useMemo, useState } from 'react'
import { Card, Row, Col, Statistic, Tabs, List, Tag, Button, Modal, Form, Input, InputNumber, DatePicker, Space, Typography, message, Empty, Spin, Select } from 'antd'
import { HomeOutlined, DollarOutlined, ToolOutlined, CalendarOutlined, PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { lifeModulesAPI } from '../services/api'

const { Text, Paragraph, Title } = Typography

const tabConfig = {
  property: { recordType: 'property', title: '房屋档案', statuses: ['自有', '租赁', '按揭'] },
  rent: { recordType: 'rent', title: '房租缴纳', statuses: ['待缴', '已缴', '已逾期'] },
  utility: { recordType: 'utility', title: '水电物业', statuses: ['待缴', '已缴', '已逾期'] },
  repair: { recordType: 'repair', title: '维修报修', statuses: ['待处理', '处理中', '已完成'] },
}

const HousingPage: React.FC = () => {
  const familyId = localStorage.getItem('family_id') || ''
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [tab, setTab] = useState<'property' | 'rent' | 'utility' | 'repair'>('property')
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<any>(null)
  const [items, setItems] = useState<any[]>([])
  const [stats, setStats] = useState<any>({})
  const [keyword, setKeyword] = useState('')
  const [form] = Form.useForm()

  const load = async () => {
    setLoading(true)
    try {
      const [listRes, statsRes] = await Promise.all([
        lifeModulesAPI.housing.list(familyId),
        lifeModulesAPI.housing.stats(familyId),
      ])
      setItems(listRes.data.items || [])
      setStats(statsRes.data || {})
    } catch {
      message.error('加载住房管理失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const grouped = useMemo(() => ({
    property: items.filter(item => item.record_type === 'property'),
    rent: items.filter(item => item.record_type === 'rent'),
    utility: items.filter(item => item.record_type === 'utility'),
    repair: items.filter(item => item.record_type === 'repair'),
  }), [items])

  const filtered = useMemo(() => {
    const q = keyword.trim().toLowerCase()
    if (!q) return grouped
    const filterItems = (list: any[]) =>
      list.filter(item =>
        `${item.title || ''} ${item.location || ''} ${item.owner || ''} ${item.status || ''} ${item.note || ''}`.toLowerCase().includes(q),
      )
    return {
      property: filterItems(grouped.property),
      rent: filterItems(grouped.rent),
      utility: filterItems(grouped.utility),
      repair: filterItems(grouped.repair),
    }
  }, [grouped, keyword])

  const currentConfig = tabConfig[tab]

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    form.setFieldsValue({ record_type: currentConfig.recordType, status: currentConfig.statuses[0], amount: 0 })
    setOpen(true)
  }

  const editItem = (item: any) => {
    setEditing(item)
    setTab(item.record_type === 'rent' ? 'rent' : item.record_type === 'utility' ? 'utility' : item.record_type === 'repair' ? 'repair' : 'property')
    form.setFieldsValue({
      ...item,
      due_date: item.due_date ? dayjs(item.due_date) : undefined,
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
        due_date: values.due_date ? values.due_date.format('YYYY-MM-DD') : '',
      }
      if (editing?.id) await lifeModulesAPI.housing.update(editing.id, payload)
      else await lifeModulesAPI.housing.add(payload)
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
    await lifeModulesAPI.housing.remove(id, familyId)
    message.success('已删除')
    await load()
  }

  return (
    <div>
      <Card style={{ marginBottom: 16, borderRadius: 8 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} lg={8}>
            <Title level={4} style={{ margin: 0 }}>住房管理</Title>
            <Paragraph style={{ marginTop: 8, marginBottom: 0 }}>
              房贷、房租、水电物业和维修报修放到一起，住处相关的账和提醒就不散了。
            </Paragraph>
          </Col>
          <Col xs={12} md={6} lg={4}><Statistic title="记录总数" value={stats.total_count || 0} prefix={<HomeOutlined />} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="临近到期" value={stats.due_soon_count || 0} prefix={<CalendarOutlined />} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="逾期" value={stats.overdue_count || 0} prefix={<ToolOutlined />} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="合计金额" value={stats.total_amount || 0} prefix={<DollarOutlined />} /></Col>
        </Row>
      </Card>

      <Card extra={<Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>新增{currentConfig.title}</Button>} style={{ borderRadius: 8 }}>
        <Input.Search
          allowClear
          placeholder="搜索标题、地点、负责人、备注"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          style={{ marginBottom: 16, maxWidth: 360 }}
        />
        {loading ? <Spin /> : (
          <Tabs activeKey={tab} onChange={(value) => setTab(value as typeof tab)} items={[
            {
              key: 'property',
              label: '房屋档案',
              children: filtered.property.length ? (
                <List dataSource={filtered.property} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => editItem(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta
                      avatar={<HomeOutlined />}
                      title={<Space><Text strong>{item.title}</Text><Tag>{item.status}</Tag></Space>}
                      description={`${item.location || '未填写地址'} · ${item.owner || '未填写负责人'}`}
                    />
                    <Text strong>¥{Number(item.amount || 0).toLocaleString()}</Text>
                  </List.Item>
                )} />
              ) : <Empty description={keyword ? '没有匹配结果' : '暂无房屋档案'} />,
            },
            {
              key: 'rent',
              label: '房租',
              children: filtered.rent.length ? (
                <List dataSource={[...filtered.rent].sort((a, b) => String(a.due_date || '').localeCompare(String(b.due_date || '')))} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => editItem(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta
                      avatar={<DollarOutlined />}
                      title={<Space><Text strong>{item.title}</Text><Tag color="blue">{item.status}</Tag></Space>}
                      description={`${item.due_date || '未设置日期'} · ${item.location || '未填写地址'} · ${item.note || '未填写备注'}`}
                    />
                    <Text strong>¥{Number(item.amount || 0).toLocaleString()}</Text>
                  </List.Item>
                )} />
              ) : <Empty description={keyword ? '没有匹配结果' : '暂无房租记录'} />,
            },
            {
              key: 'utility',
              label: '水电物业',
              children: filtered.utility.length ? (
                <List dataSource={[...filtered.utility].sort((a, b) => String(a.due_date || '').localeCompare(String(b.due_date || '')))} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => editItem(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta
                      avatar={<CalendarOutlined />}
                      title={<Space><Text strong>{item.title}</Text><Tag>{item.status}</Tag></Space>}
                      description={`${item.due_date || '未设置日期'} · ${item.location || '未填写地点'} · ${item.note || '未填写备注'}`}
                    />
                    <Text strong>¥{Number(item.amount || 0).toLocaleString()}</Text>
                  </List.Item>
                )} />
              ) : <Empty description={keyword ? '没有匹配结果' : '暂无水电物业记录'} />,
            },
            {
              key: 'repair',
              label: '维修报修',
              children: filtered.repair.length ? (
                <List dataSource={[...filtered.repair].sort((a, b) => String(b.updated_at || '').localeCompare(String(a.updated_at || '')))} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => editItem(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta
                      avatar={<ToolOutlined />}
                      title={<Space><Text strong>{item.title}</Text><Tag color={item.status === '已完成' ? 'green' : 'gold'}>{item.status}</Tag></Space>}
                      description={`${item.location || '未填写地点'} · ${item.note || '未填写报修说明'}`}
                    />
                    <Text type="secondary">{item.due_date || '未设置日期'}</Text>
                  </List.Item>
                )} />
              ) : <Empty description={keyword ? '没有匹配结果' : '暂无维修报修'} />,
            },
          ]} />
        )}
      </Card>

      <Modal title={`${editing ? '编辑' : '新增'}${currentConfig.title}`} open={open} onCancel={() => setOpen(false)} onOk={save} confirmLoading={saving} okText="保存" cancelText="取消" destroyOnHidden>
        <Form layout="vertical" form={form}>
          <Form.Item name="title" label="标题" rules={[{ required: true, message: '请输入标题' }]}><Input /></Form.Item>
          <Form.Item name="location" label="地点/地址"><Input /></Form.Item>
          <Form.Item name="owner" label="负责人/业主"><Input /></Form.Item>
          <Form.Item name="amount" label="金额"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="status" label="状态" rules={[{ required: true, message: '请选择状态' }]}>
            <Select options={currentConfig.statuses.map(value => ({ label: value, value }))} />
          </Form.Item>
          <Form.Item name="due_date" label="到期/日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="note" label="备注"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default HousingPage
