import React, { useEffect, useMemo, useState } from 'react'
import { Card, Table, Button, Form, Input, InputNumber, Select, Tag, Space, message, Statistic, Row, Col, Modal, Tabs, Typography, Switch } from 'antd'
import { PlusOutlined, ShoppingCartOutlined, CheckOutlined, EditOutlined, ReloadOutlined, StarOutlined, InboxOutlined } from '@ant-design/icons'
import { membersAPI, shoppingAPI } from '../services/api'

const { Title, Paragraph, Text } = Typography

const categoryOptions = [
  { label: '食品食材', value: 'food' },
  { label: '日用品', value: 'daily' },
  { label: '医药保健', value: 'health' },
  { label: '家居用品', value: 'home' },
  { label: '电子产品', value: 'electronics' },
  { label: '服装鞋帽', value: 'clothing' },
  { label: '其他', value: 'other' },
]

const ShoppingPage: React.FC = () => {
  const familyId = localStorage.getItem('family_id') || ''
  const [items, setItems] = useState<any[]>([])
  const [stats, setStats] = useState<any>({})
  const [loading, setLoading] = useState(false)
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [editingItem, setEditingItem] = useState<any>(null)
  const [activeTab, setActiveTab] = useState('pending')
  const [keyword, setKeyword] = useState('')
  const [members, setMembers] = useState<any[]>([])
  const [memberFilter, setMemberFilter] = useState('all')
  const [form] = Form.useForm()
  const [editForm] = Form.useForm()

  useEffect(() => {
    loadItems()
    loadStats()
    loadMembers()
  }, [])

  const loadMembers = async () => {
    try {
      const res = await membersAPI.getAll()
      setMembers(res.data.members || [])
    } catch {
      setMembers([])
    }
  }

  const loadItems = async () => {
    setLoading(true)
    try {
      const res = await shoppingAPI.getAll(familyId)
      setItems(res.data.items || [])
    } catch {
      message.error('加载采购中心失败')
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const res = await shoppingAPI.getStats(familyId)
      setStats(res.data || {})
    } catch {
      message.error('加载采购统计失败')
    }
  }

  const refresh = async () => {
    await Promise.all([loadItems(), loadStats()])
  }

  const handleAdd = async (values: any) => {
    try {
      await shoppingAPI.add(values, familyId)
      message.success('采购项添加成功')
      form.resetFields()
      form.setFieldsValue({ quantity: '1', unit: '件', priority: 'normal', category: 'daily', current_stock: 0, target_stock: 0, restock_threshold: 0, is_favorite: false })
      await refresh()
    } catch {
      message.error('添加失败')
    }
  }

  const handleTogglePurchased = async (item: any) => {
    try {
      await shoppingAPI.toggle(item.id, familyId)
      message.success(item.purchased ? '已恢复为待采购' : '已标记为已采购')
      await refresh()
    } catch {
      message.error('操作失败')
    }
  }

  const handleQuickRestock = async (item: any) => {
    try {
      await shoppingAPI.update(item.id, {
        ...item,
        current_stock: Number(item.target_stock || item.current_stock || 0),
      }, familyId)
      message.success('已补齐库存')
      await refresh()
    } catch {
      message.error('补货失败')
    }
  }

  const handleEditClick = (record: any) => {
    setEditingItem(record)
    editForm.setFieldsValue({
      ...record,
      is_favorite: Boolean(record.is_favorite),
      current_stock: Number(record.current_stock || 0),
      target_stock: Number(record.target_stock || 0),
      restock_threshold: Number(record.restock_threshold || 0),
    })
    setEditModalVisible(true)
  }

  const handleEditOk = async (values: any) => {
    if (!editingItem) return
    try {
      await shoppingAPI.update(editingItem.id, values, familyId)
      message.success('已更新')
      setEditModalVisible(false)
      setEditingItem(null)
      await refresh()
    } catch {
      message.error('更新失败')
    }
  }

  const handleDelete = async (name: string) => {
    try {
      await shoppingAPI.remove(name, familyId)
      message.success('采购项已删除')
      await refresh()
    } catch {
      message.error('删除失败')
    }
  }

  const filteredItems = useMemo(() => {
    const q = keyword.trim().toLowerCase()
    return items.filter(item => {
      const matchesKeyword = !q || `${item.name || ''} ${item.category || ''} ${item.notes || ''}`.toLowerCase().includes(q)
      const matchesMember = memberFilter === 'all' || (item.added_by || '') === memberFilter
      const isRestock = Number(item.current_stock || 0) <= Number(item.restock_threshold || 0)
      if (activeTab === 'pending') return !item.purchased && matchesKeyword && matchesMember
      if (activeTab === 'restock') return isRestock && matchesKeyword && matchesMember
      if (activeTab === 'favorites') return Boolean(item.is_favorite) && matchesKeyword && matchesMember
      if (activeTab === 'purchased') return item.purchased && matchesKeyword && matchesMember
      return matchesKeyword && matchesMember
    })
  }, [activeTab, items, keyword, memberFilter])

  const columns = [
    {
      title: '物品',
      dataIndex: 'name',
      key: 'name',
      render: (_: any, record: any) => (
        <Space direction="vertical" size={0}>
          <Space>
            <Text strong>{record.name}</Text>
            {record.is_favorite ? <Tag color="gold" icon={<StarOutlined />}>常买</Tag> : null}
            <Tag color="blue">{record.category}</Tag>
          </Space>
            <Text type="secondary">{record.added_by || '未分配成员'} · {record.notes || '未填写备注'}</Text>
        </Space>
      ),
    },
    {
      title: '采购量',
      key: 'quantity',
      width: 110,
      render: (_: any, record: any) => `${record.quantity || '1'} ${record.unit || '件'}`,
    },
    {
      title: '库存',
      key: 'stock',
      width: 170,
      render: (_: any, record: any) => {
        const currentStock = Number(record.current_stock || 0)
        const threshold = Number(record.restock_threshold || 0)
        const target = Number(record.target_stock || 0)
        const low = currentStock <= threshold
        return (
          <Space direction="vertical" size={0}>
            <Text type={low ? 'danger' : undefined}>{currentStock} / {target || '-'} {record.unit || '件'}</Text>
            <Text type="secondary">阈值 {threshold}</Text>
          </Space>
        )
      },
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 100,
      render: (priority: string) => (
        <Tag color={priority === 'high' ? 'red' : priority === 'normal' ? 'orange' : 'default'}>
          {priority === 'high' ? '高' : priority === 'normal' ? '中' : '低'}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'purchased',
      key: 'purchased',
      width: 120,
      render: (purchased: boolean, record: any) => (
        <Button type="link" size="small" onClick={() => handleTogglePurchased(record)}>
          {purchased ? <Tag icon={<CheckOutlined />} color="success">已采购</Tag> : <Tag color="default">待采购</Tag>}
        </Button>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 220,
      render: (_: any, record: any) => (
        <Space>
          <Button icon={<EditOutlined />} size="small" onClick={() => handleEditClick(record)}>编辑</Button>
          <Button icon={<ReloadOutlined />} size="small" onClick={() => handleQuickRestock(record)}>补货</Button>
          <Button danger size="small" onClick={() => handleDelete(record.name)}>删除</Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Card style={{ marginBottom: 16, borderRadius: 8 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} lg={8}>
            <Title level={4} style={{ margin: 0 }}>采购中心</Title>
            <Paragraph style={{ marginTop: 8, marginBottom: 0 }}>
              购物清单、常买品、库存和补货提醒放到一页里，家庭采购会顺很多。
            </Paragraph>
          </Col>
          <Col xs={12} md={6} lg={4}><Statistic title="采购项" value={stats.total_items || 0} prefix={<ShoppingCartOutlined />} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="待采购" value={stats.unpurchased || 0} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="需补货" value={stats.restock_needed || 0} prefix={<InboxOutlined />} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="常买品" value={stats.favorites || 0} prefix={<StarOutlined />} /></Col>
        </Row>
      </Card>

      <Card style={{ marginBottom: 16, borderRadius: 8 }}>
        <Form form={form} layout="vertical" onFinish={handleAdd} initialValues={{ quantity: '1', unit: '件', priority: 'normal', category: 'daily', current_stock: 0, target_stock: 0, restock_threshold: 0, is_favorite: false }}>
          <Row gutter={16}>
            <Col xs={24} md={8}><Form.Item name="name" label="物品名称" rules={[{ required: true, message: '请输入物品名称' }]}><Input placeholder="例如：抽纸" /></Form.Item></Col>
            <Col xs={12} md={4}><Form.Item name="quantity" label="采购量"><Input /></Form.Item></Col>
            <Col xs={12} md={4}><Form.Item name="unit" label="单位"><Input /></Form.Item></Col>
            <Col xs={12} md={4}><Form.Item name="category" label="分类"><Select options={categoryOptions} /></Form.Item></Col>
            <Col xs={12} md={4}><Form.Item name="priority" label="优先级"><Select options={[{ label: '低', value: 'low' }, { label: '中', value: 'normal' }, { label: '高', value: 'high' }]} /></Form.Item></Col>
            <Col xs={12} md={4}><Form.Item name="added_by" label="负责人"><Select allowClear options={members.map(member => ({ label: member.name, value: member.name }))} /></Form.Item></Col>
            <Col xs={12} md={4}><Form.Item name="current_stock" label="当前库存"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item></Col>
            <Col xs={12} md={4}><Form.Item name="target_stock" label="目标库存"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item></Col>
            <Col xs={12} md={4}><Form.Item name="restock_threshold" label="补货阈值"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item></Col>
            <Col xs={24} md={8}><Form.Item name="notes" label="备注"><Input placeholder="品牌、规格、渠道" /></Form.Item></Col>
            <Col xs={12} md={4}><Form.Item name="is_favorite" label="常买品" valuePropName="checked"><Switch /></Form.Item></Col>
            <Col xs={12} md={4} style={{ display: 'flex', alignItems: 'end' }}><Button type="primary" htmlType="submit" icon={<PlusOutlined />}>新增采购项</Button></Col>
          </Row>
        </Form>
      </Card>

      <Card style={{ borderRadius: 8 }}>
        <Tabs activeKey={activeTab} onChange={setActiveTab} items={[
          { key: 'pending', label: '待采购' },
          { key: 'restock', label: '需补货' },
          { key: 'favorites', label: '常买品' },
          { key: 'purchased', label: '已采购' },
          { key: 'all', label: '全部' },
        ]} />
        <Space wrap style={{ marginBottom: 16 }}>
          <Input.Search allowClear placeholder="搜索物品、分类、备注" value={keyword} onChange={(e) => setKeyword(e.target.value)} style={{ width: 360 }} />
          <Select value={memberFilter} onChange={setMemberFilter} style={{ width: 180 }} options={[{ label: '全部成员', value: 'all' }, ...members.map(member => ({ label: member.name, value: member.name }))]} />
        </Space>
        <Table rowKey="id" loading={loading} dataSource={filteredItems} columns={columns} pagination={{ pageSize: 8 }} />
      </Card>

      <Modal title="编辑采购项" open={editModalVisible} onCancel={() => setEditModalVisible(false)} onOk={() => editForm.submit()} okText="保存" cancelText="取消" destroyOnHidden>
        <Form form={editForm} layout="vertical" onFinish={handleEditOk}>
          <Form.Item name="name" label="物品名称" rules={[{ required: true, message: '请输入物品名称' }]}><Input /></Form.Item>
          <Form.Item name="quantity" label="采购量"><Input /></Form.Item>
          <Form.Item name="unit" label="单位"><Input /></Form.Item>
          <Form.Item name="category" label="分类"><Select options={categoryOptions} /></Form.Item>
          <Form.Item name="priority" label="优先级"><Select options={[{ label: '低', value: 'low' }, { label: '中', value: 'normal' }, { label: '高', value: 'high' }]} /></Form.Item>
          <Form.Item name="added_by" label="负责人"><Select allowClear options={members.map(member => ({ label: member.name, value: member.name }))} /></Form.Item>
          <Form.Item name="current_stock" label="当前库存"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="target_stock" label="目标库存"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="restock_threshold" label="补货阈值"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="notes" label="备注"><Input.TextArea rows={3} /></Form.Item>
          <Form.Item name="is_favorite" label="常买品" valuePropName="checked"><Switch /></Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default ShoppingPage
