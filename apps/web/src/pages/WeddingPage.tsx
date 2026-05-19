import React, { useEffect, useMemo, useState } from 'react'
import { Card, Row, Col, Statistic, Tabs, List, Tag, Button, Modal, Form, Input, InputNumber, DatePicker, Space, Progress, Typography, message, Empty, Spin, Select } from 'antd'
import { CalendarOutlined, CheckSquareOutlined, DollarOutlined, ShopOutlined, PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { lifeModulesAPI } from '../services/api'

const { Text, Paragraph, Title } = Typography

const tabStatusOptions: Record<string, { label: string; value: string }[]> = {
  timeline: [{ label: '待开始', value: 'todo' }, { label: '进行中', value: 'doing' }, { label: '已完成', value: 'done' }],
  budget: [{ label: '待付款', value: 'pending' }, { label: '部分支付', value: 'partial' }, { label: '已结清', value: 'paid' }],
  vendor: [{ label: '待联系', value: 'todo' }, { label: '已沟通', value: 'contacted' }, { label: '已签约', value: 'signed' }],
  todo: [{ label: '待处理', value: 'todo' }, { label: '进行中', value: 'doing' }, { label: '已完成', value: 'done' }],
}

const tabTitles: Record<string, string> = {
  timeline: '时间线',
  budget: '预算',
  vendor: '供应商',
  todo: '待办',
}

const WeddingPage: React.FC = () => {
  const familyId = localStorage.getItem('family_id') || ''
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [activeTab, setActiveTab] = useState('timeline')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<any>(null)
  const [items, setItems] = useState<any[]>([])
  const [stats, setStats] = useState<any>({ budget_total: 0, spent_total: 0, todo_count: 0 })
  const [keyword, setKeyword] = useState('')
  const [form] = Form.useForm()

  const load = async () => {
    setLoading(true)
    try {
      const [listRes, statsRes] = await Promise.all([
        lifeModulesAPI.wedding.list(familyId),
        lifeModulesAPI.wedding.stats(familyId),
      ])
      setItems(listRes.data.items || [])
      setStats(statsRes.data || {})
    } catch {
      message.error('加载备婚管理失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const grouped = useMemo(() => ({
    timeline: items.filter(item => item.item_type === 'timeline'),
    budget: items.filter(item => item.item_type === 'budget'),
    vendor: items.filter(item => item.item_type === 'vendor'),
    todo: items.filter(item => item.item_type === 'todo'),
  }), [items])

  const filtered = useMemo(() => {
    const q = keyword.trim().toLowerCase()
    if (!q) return grouped
    const filterItems = (list: any[]) =>
      list.filter(item =>
        `${item.title || ''} ${item.description || ''} ${item.owner || ''} ${item.status || ''}`.toLowerCase().includes(q),
      )
    return {
      timeline: filterItems(grouped.timeline),
      budget: filterItems(grouped.budget),
      vendor: filterItems(grouped.vendor),
      todo: filterItems(grouped.todo),
    }
  }, [grouped, keyword])

  const progress = stats.budget_total ? Math.min(100, Math.round(((stats.spent_total || 0) / stats.budget_total) * 100)) : 0

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    form.setFieldsValue({ item_type: activeTab, status: tabStatusOptions[activeTab]?.[0]?.value, planned_amount: 0, amount: 0 })
    setModalOpen(true)
  }

  const openEdit = (item: any) => {
    setEditing(item)
    setActiveTab(item.item_type)
    form.setFieldsValue({
      ...item,
      item_date: item.item_date ? dayjs(item.item_date) : undefined,
    })
    setModalOpen(true)
  }

  const save = async () => {
    const values = await form.validateFields()
    setSaving(true)
    try {
      const payload = {
        ...values,
        family_id: familyId,
        item_type: activeTab,
        item_date: values.item_date ? values.item_date.format('YYYY-MM-DD') : '',
      }
      if (editing?.id) await lifeModulesAPI.wedding.update(editing.id, payload)
      else await lifeModulesAPI.wedding.add(payload)
      message.success('已保存')
      setModalOpen(false)
      await load()
    } catch {
      message.error('保存失败')
    } finally {
      setSaving(false)
    }
  }

  const remove = async (id: number) => {
    await lifeModulesAPI.wedding.remove(id, familyId)
    message.success('已删除')
    await load()
  }

  const renderBudgetMeta = (item: any) => {
    const planned = Number(item.planned_amount || 0)
    const spent = Number(item.amount || 0)
    const rate = planned ? Math.min(100, Math.round((spent / planned) * 100)) : 0
    return (
      <div style={{ minWidth: 180 }}>
        <Text strong>¥{spent.toLocaleString()}</Text>
        <Text type="secondary"> / ¥{planned.toLocaleString()}</Text>
        <Progress percent={rate} size="small" style={{ marginTop: 8, marginBottom: 0 }} />
      </div>
    )
  }

  return (
    <div>
      <Card style={{ marginBottom: 16, borderRadius: 8 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} lg={8}>
            <Title level={4} style={{ margin: 0 }}>备婚管理</Title>
            <Paragraph style={{ marginTop: 8, marginBottom: 0 }}>
              把时间线、预算、供应商和待办收进一个工作面，信息会更稳，推进也更清楚。
            </Paragraph>
          </Col>
          <Col xs={12} md={6} lg={4}><Statistic title="预算总额" value={stats.budget_total || 0} prefix={<DollarOutlined />} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="已支付" value={stats.spent_total || 0} prefix={<DollarOutlined />} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="待办数量" value={stats.todo_count || 0} prefix={<CheckSquareOutlined />} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="预算进度" value={progress} suffix="%" prefix={<CalendarOutlined />} /></Col>
        </Row>
      </Card>

      <Card extra={<Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>新增{tabTitles[activeTab]}</Button>} style={{ borderRadius: 8 }}>
        <Input.Search
          allowClear
          placeholder="搜索备婚事项、供应商、备注"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          style={{ marginBottom: 16, maxWidth: 360 }}
        />
        {loading ? <Spin /> : (
          <Tabs activeKey={activeTab} onChange={setActiveTab} items={[
            {
              key: 'timeline',
              label: '时间线',
              children: filtered.timeline.length ? (
                <List dataSource={[...filtered.timeline].sort((a, b) => String(a.item_date || '').localeCompare(String(b.item_date || '')))} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => openEdit(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta avatar={<CalendarOutlined />} title={<Space><Text strong>{item.title}</Text><Tag>{item.status}</Tag></Space>} description={`${item.item_date || '未设置日期'} · ${item.owner || '未分配负责人'}`} />
                  </List.Item>
                )} />
              ) : <Empty description={keyword ? '没有匹配结果' : '暂无时间线'} />,
            },
            {
              key: 'budget',
              label: '预算',
              children: filtered.budget.length ? (
                <List dataSource={[...filtered.budget].sort((a, b) => Number(b.amount || 0) - Number(a.amount || 0))} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => openEdit(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta avatar={<DollarOutlined />} title={<Space><Text strong>{item.title}</Text><Tag color="blue">{item.status}</Tag></Space>} description={item.description || '未填写说明'} />
                    {renderBudgetMeta(item)}
                  </List.Item>
                )} />
              ) : <Empty description={keyword ? '没有匹配结果' : '暂无预算'} />,
            },
            {
              key: 'vendor',
              label: '供应商',
              children: filtered.vendor.length ? (
                <List dataSource={[...filtered.vendor].sort((a, b) => String(a.status || '').localeCompare(String(b.status || '')))} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => openEdit(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta avatar={<ShopOutlined />} title={<Space><Text strong>{item.title}</Text><Tag>{item.status}</Tag></Space>} description={`${item.owner || '未填写联系人'} · ${item.description || '未填写说明'}`} />
                  </List.Item>
                )} />
              ) : <Empty description={keyword ? '没有匹配结果' : '暂无供应商'} />,
            },
            {
              key: 'todo',
              label: '待办',
              children: filtered.todo.length ? (
                <List dataSource={[...filtered.todo].sort((a, b) => String(a.status || '').localeCompare(String(b.status || '')))} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => openEdit(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta avatar={<CheckSquareOutlined />} title={<Space><Text strong>{item.title}</Text><Tag color={item.status === 'done' ? 'green' : 'gold'}>{item.status}</Tag></Space>} description={`${item.item_date || '无截止时间'} · ${item.owner || '未分配负责人'}`} />
                  </List.Item>
                )} />
              ) : <Empty description={keyword ? '没有匹配结果' : '暂无待办'} />,
            },
          ]} />
        )}
      </Card>

      <Modal title={`${editing ? '编辑' : '新增'}${tabTitles[activeTab]}`} open={modalOpen} onCancel={() => setModalOpen(false)} onOk={save} confirmLoading={saving} okText="保存" cancelText="取消" destroyOnHidden>
        <Form layout="vertical" form={form}>
          <Form.Item name="title" label="标题" rules={[{ required: true, message: '请输入标题' }]}><Input /></Form.Item>
          <Form.Item name="owner" label={activeTab === 'vendor' ? '联系人/负责人' : '负责人'}><Input /></Form.Item>
          <Form.Item name="description" label={activeTab === 'budget' ? '说明' : '备注'}><Input.TextArea rows={3} /></Form.Item>
          {activeTab === 'budget' && (
            <>
              <Form.Item name="planned_amount" label="预算总额" rules={[{ required: true, message: '请输入预算总额' }]}><InputNumber min={0} style={{ width: '100%' }} /></Form.Item>
              <Form.Item name="amount" label="已支付"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item>
            </>
          )}
          {activeTab !== 'budget' && (
            <Form.Item name="amount" label="金额"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item>
          )}
          <Form.Item name="status" label="状态" rules={[{ required: true, message: '请选择状态' }]}>
            <Select options={tabStatusOptions[activeTab]} />
          </Form.Item>
          <Form.Item name="item_date" label={activeTab === 'todo' ? '截止日期' : '日期'}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default WeddingPage
