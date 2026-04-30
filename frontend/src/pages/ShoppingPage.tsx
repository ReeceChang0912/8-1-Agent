import React, { useState, useEffect } from 'react'
import { Card, Table, Button, Form, Input, Select, Tag, Space, message, Statistic, Row, Col } from 'antd'
import { PlusOutlined, ShoppingCartOutlined, CheckOutlined } from '@ant-design/icons'
import { shoppingAPI } from '../services/api'

const ShoppingPage: React.FC = () => {
  const [items, setItems] = useState([])
  const [stats, setStats] = useState<any>({})
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    loadItems()
    loadStats()
  }, [])

  const loadItems = async () => {
    setLoading(true)
    try {
      const res = await shoppingAPI.getAll()
      setItems(res.data.items)
    } catch (error) {
      message.error('加载购物清单失败')
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const res = await shoppingAPI.getStats()
      setStats(res.data)
    } catch (error) {
      console.error('加载统计失败')
    }
  }

  const handleAdd = async (values: any) => {
    try {
      await shoppingAPI.add(values)
      message.success('物品添加成功')
      form.resetFields()
      loadItems()
      loadStats()
    } catch (error) {
      message.error('添加失败')
    }
  }

  const handleDelete = async (name: string) => {
    try {
      await shoppingAPI.remove(name)
      message.success('物品已删除')
      loadItems()
      loadStats()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const columns = [
    {
      title: '物品名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 100,
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 120,
      render: (cat: string) => <Tag color="blue">{cat}</Tag>,
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 100,
      render: (p: string) => (
        <Tag color={p === 'high' ? 'red' : p === 'normal' ? 'orange' : 'default'}>
          {p === 'high' ? '高' : p === 'normal' ? '中' : '低'}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'purchased',
      key: 'purchased',
      width: 100,
      render: (p: boolean) => (
        p ? <Tag icon={<CheckOutlined />} color="success">已购买</Tag> : <Tag color="default">待购买</Tag>
      ),
    },
    {
      title: '备注',
      dataIndex: 'notes',
      key: 'notes',
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: any, record: any) => (
        <Button danger size="small" onClick={() => handleDelete(record.name)}>
          删除
        </Button>
      ),
    },
  ]

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总物品数"
              value={stats.total_items || 0}
              prefix={<ShoppingCartOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已购买"
              value={stats.purchased || 0}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="待购买"
              value={stats.unpurchased || 0}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="完成率"
              value={(stats.completion_rate || 0) * 100}
              precision={1}
              suffix="%"
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>

      <Card
        title="添加物品"
        style={{ marginBottom: 16 }}
      >
        <Form form={form} onFinish={handleAdd} layout="inline">
          <Form.Item
            name="name"
            rules={[{ required: true, message: '请输入物品名称' }]}
          >
            <Input placeholder="物品名称" style={{ width: 200 }} />
          </Form.Item>

          <Form.Item name="quantity" initialValue="1">
            <Input placeholder="数量" style={{ width: 100 }} />
          </Form.Item>

          <Form.Item name="category" initialValue="general">
            <Select style={{ width: 120 }}>
              <Select.Option value="general">一般</Select.Option>
              <Select.Option value="food">食品</Select.Option>
              <Select.Option value="daily">日用品</Select.Option>
              <Select.Option value="electronics">电子产品</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item name="priority" initialValue="normal">
            <Select style={{ width: 100 }}>
              <Select.Option value="high">高</Select.Option>
              <Select.Option value="normal">中</Select.Option>
              <Select.Option value="low">低</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" icon={<PlusOutlined />}>
              添加
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="购物清单">
        <Table
          dataSource={items}
          columns={columns}
          rowKey="name"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  )
}

export default ShoppingPage
