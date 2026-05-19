import React, { useEffect, useMemo, useState } from 'react'
import { Card, Row, Col, Statistic, Tabs, List, Tag, Button, Modal, Form, Input, InputNumber, DatePicker, Space, Typography, message, Empty, Spin, Select } from 'antd'
import { CarOutlined, ToolOutlined, DollarOutlined, CalendarOutlined, PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { lifeModulesAPI } from '../services/api'

const { Text, Paragraph, Title } = Typography

const tabConfig = {
  vehicles: { recordType: 'vehicle', title: '车辆档案', statuses: ['正常', '待年检', '待续保'] },
  services: { recordType: 'service', title: '保养记录', statuses: ['待执行', '已完成'] },
  expenses: { recordType: 'expense', title: '费用记录', statuses: ['燃油', '停车', '维修', '保险', '其他'] },
}

const VehiclePage: React.FC = () => {
  const familyId = localStorage.getItem('family_id') || ''
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [tab, setTab] = useState<'vehicles' | 'services' | 'expenses'>('vehicles')
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
        lifeModulesAPI.vehicle.list(familyId),
        lifeModulesAPI.vehicle.stats(familyId),
      ])
      setItems(listRes.data.items || [])
      setStats(statsRes.data || {})
    } catch {
      message.error('加载车辆管理失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const grouped = useMemo(() => ({
    vehicles: items.filter(item => item.record_type === 'vehicle'),
    services: items.filter(item => item.record_type === 'service'),
    expenses: items.filter(item => item.record_type === 'expense'),
  }), [items])

  const filtered = useMemo(() => {
    const q = keyword.trim().toLowerCase()
    if (!q) return grouped
    const filterItems = (list: any[]) =>
      list.filter(item =>
        `${item.title || ''} ${item.plate || ''} ${item.model || ''} ${item.status || ''} ${item.note || ''}`.toLowerCase().includes(q),
      )
    return {
      vehicles: filterItems(grouped.vehicles),
      services: filterItems(grouped.services),
      expenses: filterItems(grouped.expenses),
    }
  }, [grouped, keyword])

  const currentConfig = tabConfig[tab]

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    form.setFieldsValue({ record_type: currentConfig.recordType, status: currentConfig.statuses[0], amount: 0, mileage: 0 })
    setOpen(true)
  }

  const editItem = (item: any) => {
    setEditing(item)
    const nextTab = item.record_type === 'service' ? 'services' : item.record_type === 'expense' ? 'expenses' : 'vehicles'
    setTab(nextTab)
    form.setFieldsValue({ ...item, record_date: item.record_date ? dayjs(item.record_date) : undefined })
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
        record_date: values.record_date ? values.record_date.format('YYYY-MM-DD') : '',
      }
      if (editing?.id) await lifeModulesAPI.vehicle.update(editing.id, payload)
      else await lifeModulesAPI.vehicle.add(payload)
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
    await lifeModulesAPI.vehicle.remove(id, familyId)
    message.success('已删除')
    await load()
  }

  return (
    <div>
      <Card style={{ marginBottom: 16, borderRadius: 8 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} lg={8}>
            <Title level={4} style={{ margin: 0 }}>车辆管理</Title>
            <Paragraph style={{ marginTop: 8, marginBottom: 0 }}>
              车辆档案、保养和费用都收在一起，后面接年检和违章也不会乱。
            </Paragraph>
          </Col>
          <Col xs={12} md={6} lg={4}><Statistic title="车辆数量" value={stats.vehicle_count || 0} prefix={<CarOutlined />} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="保养记录" value={stats.service_count || 0} prefix={<ToolOutlined />} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="费用合计" value={stats.expense_total || 0} prefix={<DollarOutlined />} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="总记录数" value={stats.record_count || 0} prefix={<CalendarOutlined />} /></Col>
        </Row>
      </Card>

      <Card extra={<Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>新增{currentConfig.title}</Button>} style={{ borderRadius: 8 }}>
        <Input.Search
          allowClear
          placeholder="搜索车牌、车型、备注"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          style={{ marginBottom: 16, maxWidth: 320 }}
        />
        {loading ? <Spin /> : (
          <Tabs activeKey={tab} onChange={(value) => setTab(value as typeof tab)} items={[
            {
              key: 'vehicles',
              label: '车辆档案',
              children: filtered.vehicles.length ? (
                <List dataSource={[...filtered.vehicles].sort((a, b) => String(a.status || '').localeCompare(String(b.status || '')))} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => editItem(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta avatar={<CarOutlined />} title={<Space><Text strong>{item.title}</Text><Tag>{item.status}</Tag></Space>} description={`${item.plate || '未填写车牌'} · ${item.model || '未填写车型'} · 里程 ${Number(item.mileage || 0).toLocaleString()} km`} />
                  </List.Item>
                )} />
              ) : <Empty description={keyword ? '没有匹配结果' : '暂无车辆档案'} />,
            },
            {
              key: 'services',
              label: '保养记录',
              children: filtered.services.length ? (
                <List dataSource={[...filtered.services].sort((a, b) => String(b.record_date || '').localeCompare(String(a.record_date || '')))} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => editItem(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta avatar={<ToolOutlined />} title={<Space><Text strong>{item.title}</Text><Tag color="green">{item.status}</Tag></Space>} description={`${item.record_date || '未设置日期'} · ${Number(item.mileage || 0).toLocaleString()} km · ${item.note || '未填写说明'}`} />
                    <Text strong>¥{Number(item.amount || 0).toLocaleString()}</Text>
                  </List.Item>
                )} />
              ) : <Empty description={keyword ? '没有匹配结果' : '暂无保养记录'} />,
            },
            {
              key: 'expenses',
              label: '费用记录',
              children: filtered.expenses.length ? (
                <List dataSource={[...filtered.expenses].sort((a, b) => Number(b.amount || 0) - Number(a.amount || 0))} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => editItem(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta avatar={<DollarOutlined />} title={<Space><Text strong>{item.title}</Text><Tag>{item.status || '其他'}</Tag></Space>} description={`${item.record_date || '未设置日期'} · ${item.note || '未填写说明'}`} />
                    <Text strong>¥{Number(item.amount || 0).toLocaleString()}</Text>
                  </List.Item>
                )} />
              ) : <Empty description={keyword ? '没有匹配结果' : '暂无费用记录'} />,
            },
          ]} />
        )}
      </Card>

      <Modal title={`${editing ? '编辑' : '新增'}${currentConfig.title}`} open={open} onCancel={() => setOpen(false)} onOk={save} confirmLoading={saving} okText="保存" cancelText="取消" destroyOnHidden>
        <Form layout="vertical" form={form}>
          <Form.Item name="title" label="标题" rules={[{ required: true, message: '请输入标题' }]}><Input /></Form.Item>
          {tab === 'vehicles' && (
            <>
              <Form.Item name="plate" label="车牌号"><Input /></Form.Item>
              <Form.Item name="model" label="车型"><Input /></Form.Item>
            </>
          )}
          <Form.Item name="mileage" label="里程"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="amount" label={tab === 'vehicles' ? '相关金额' : '金额'}><InputNumber min={0} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="status" label="状态/分类" rules={[{ required: true, message: '请选择状态或分类' }]}>
            <Select options={currentConfig.statuses.map(value => ({ label: value, value }))} />
          </Form.Item>
          <Form.Item name="record_date" label="日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="note" label="备注"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default VehiclePage
