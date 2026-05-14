import React, { useState, useEffect, useCallback } from 'react'
import {
  Card, Table, Button, Form, Input, InputNumber, Select, Tag, Space,
  message, Statistic, Row, Col, Modal, DatePicker, Empty, Typography,
} from 'antd'
import {
  PlusOutlined, EditOutlined, DeleteOutlined, ArrowUpOutlined,
  ArrowDownOutlined, WalletOutlined, DollarOutlined,
} from '@ant-design/icons'
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from 'recharts'
import { financeAPI } from '../services/api'
import dayjs from 'dayjs'

const { Text } = Typography

const INCOME_COLOR = '#52c41a'
const EXPENSE_COLOR = '#f5222d'
const PIE_COLORS = ['#f5222d', '#fa8c16', '#fadb14', '#52c41a', '#1890ff', '#722ed1', '#eb2f96', '#13c2c2', '#fa541c', '#2f54eb']

const FinancePage: React.FC = () => {
  const [summary, setSummary] = useState<any>(null)
  const [transactions, setTransactions] = useState<any[]>([])
  const [trendData, setTrendData] = useState<any[]>([])
  const [categories, setCategories] = useState<{ income: string[]; expense: string[] }>({
    income: [], expense: [],
  })
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingRecord, setEditingRecord] = useState<any>(null)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 })
  const [filters, setFilters] = useState({
    year: dayjs().year(),
    month: dayjs().month() + 1,
    transaction_type: undefined as string | undefined,
    category: undefined as string | undefined,
  })
  const [form] = Form.useForm()

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [summaryRes, txRes] = await Promise.all([
        financeAPI.getSummary(filters.year, filters.month),
        financeAPI.getTransactions({
          ...filters,
          page: pagination.current,
          page_size: pagination.pageSize,
        }),
      ])
      setSummary(summaryRes.data)
      setTransactions(txRes.data.items)
      setPagination(prev => ({ ...prev, total: txRes.data.total }))
    } catch {
      message.error('加载数据失败')
    } finally {
      setLoading(false)
    }
  }, [filters, pagination.current, pagination.pageSize])

  useEffect(() => {
    loadData()
  }, [filters.year, filters.month, filters.transaction_type, filters.category])


useEffect(() => {
    financeAPI.getCategories().then(res => setCategories(res.data))
    financeAPI.getTrend(6).then(res => setTrendData(res.data))
  }, [])

  // 30秒自动刷新
  useEffect(() => {
    const timer = setInterval(() => {
      loadData()
      financeAPI.getTrend(6).then(res => setTrendData(res.data))
    }, 30000)
    return () => clearInterval(timer)
  }, [])

  const handleFilterChange = (key: string, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }))
    setPagination(prev => ({ ...prev, current: 1 }))
  }

  const openAddModal = () => {
    setEditingRecord(null)
    form.resetFields()
    form.setFieldsValue({
      transaction_date: dayjs(),
      transaction_type: 'expense',
      created_by: '',
    })
    setModalVisible(true)
  }

  const openEditModal = (record: any) => {
    setEditingRecord(record)
    form.setFieldsValue({
      amount: record.amount,
      transaction_type: record.transaction_type,
      category: record.category,
      description: record.description,
      transaction_date: dayjs(record.transaction_date),
      created_by: record.created_by,
    })
    setModalVisible(true)
  }

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields()
      const data = {
        ...values,
        amount: parseFloat(values.amount),
        transaction_date: values.transaction_date.format('YYYY-MM-DD'),
      }

      if (editingRecord) {
        await financeAPI.update(editingRecord.id, data)
        message.success('更新成功')
      } else {
        await financeAPI.add(data)
        message.success('添加成功')
      }

      setModalVisible(false)
      loadData()
    } catch (err: any) {
      if (err?.errorFields) return
      message.error('操作失败')
    }
  }

  const handleDelete = (record: any) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除这条 ${record.transaction_type === 'income' ? '收入' : '支出'} 记录吗？`,
      okText: '删除',
      cancelText: '取消',
      okButtonProps: { danger: true },
      onOk: async () => {
        try {
          await financeAPI.remove(record.id)
          message.success('删除成功')
          if (transactions.length === 1 && pagination.current > 1) {
            setPagination(prev => ({ ...prev, current: prev.current - 1 }))
          } else {
            loadData()
          }
        } catch {
          message.error('删除失败')
        }
      },
    })
  }

  const handleTableChange = (pag: any) => {
    setPagination(prev => ({ ...prev, current: pag.current, pageSize: pag.pageSize }))
  }

  const expensePercent = summary && summary.total_income > 0
    ? Math.round((summary.total_expense / summary.total_income) * 100)
    : 0

  // pie data for expense breakdown
  const expensePieData = (summary?.expense_breakdown || []).map((d: any) => ({
    name: d.category,
    value: d.total,
    count: d.count,
  }))

  // bar data sorted ascending
  const barData = [...trendData].sort((a, b) => a.year - b.year || a.month_num - b.month_num)

  // format currency for tooltips
  const formatYuan = (v: any) => {
    const n = typeof v === 'number' ? v : parseFloat(v)
    return isNaN(n) ? '¥0.00' : `¥${n.toLocaleString('zh-CN', { minimumFractionDigits: 2 })}`
  }

  const columns = [
    {
      title: '日期',
      dataIndex: 'transaction_date',
      key: 'date',
      width: 100,
      render: (v: string) => dayjs(v).format('MM-DD'),
    },
    {
      title: '类型',
      dataIndex: 'transaction_type',
      key: 'type',
      width: 70,
      render: (v: string) => (
        <Tag color={v === 'income' ? 'green' : 'red'}>{v === 'income' ? '收入' : '支出'}</Tag>
      ),
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 90,
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 120,
      align: 'right' as const,
      render: (v: number, record: any) => (
        <Text style={{
          color: record.transaction_type === 'income' ? INCOME_COLOR : EXPENSE_COLOR,
          fontWeight: 600,
          fontSize: 15,
        }}>
          {record.transaction_type === 'income' ? '+' : '-'}¥{v.toFixed(2)}
        </Text>
      ),
      sorter: (a: any, b: any) => a.amount - b.amount,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'desc',
      ellipsis: true,
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: any) => (
        <Space>
          <Button type="link" size="small" icon={<EditOutlined />}
            onClick={() => openEditModal(record)}>编辑</Button>
          <Button type="link" size="small" danger icon={<DeleteOutlined />}
            onClick={() => handleDelete(record)}>删除</Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      {/* ===== 大盘统计卡片 ===== */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={12} sm={6}>
          <Card hoverable styles={{ body: { padding: '20px 24px' } }}>
            <Statistic
              title="本月收入"
              value={summary?.total_income || 0}
              precision={2}
              prefix={<ArrowUpOutlined />}
              valueStyle={{ color: INCOME_COLOR, fontSize: 26 }}
              suffix={<span style={{ fontSize: 14, color: '#999' }}>元</span>}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card hoverable styles={{ body: { padding: '20px 24px' } }}>
            <Statistic
              title="本月支出"
              value={summary?.total_expense || 0}
              precision={2}
              prefix={<ArrowDownOutlined />}
              valueStyle={{ color: EXPENSE_COLOR, fontSize: 26 }}
              suffix={<span style={{ fontSize: 14, color: '#999' }}>元</span>}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card hoverable styles={{ body: { padding: '20px 24px' } }}>
            <Statistic
              title="本月结余"
              value={summary?.balance || 0}
              precision={2}
              prefix={<WalletOutlined />}
              valueStyle={{
                color: (summary?.balance || 0) >= 0 ? '#1890ff' : EXPENSE_COLOR,
                fontSize: 26,
              }}
              suffix={<span style={{ fontSize: 14, color: '#999' }}>元</span>}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card hoverable styles={{ body: { padding: '20px 24px' } }}>
            <Statistic
              title="支出占收入比"
              value={expensePercent}
              prefix={<DollarOutlined />}
              suffix={<span style={{ fontSize: 14, color: '#999' }}>%</span>}
              valueStyle={{
                color: expensePercent > 80 ? EXPENSE_COLOR : INCOME_COLOR,
                fontSize: 26,
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* ===== 图表行 ===== */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        {/* 支出分类饼图 */}
        <Col xs={24} lg={12}>
          <Card title="支出分类构成" size="small">
            {expensePieData.length > 0 ? (
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <ResponsiveContainer width="60%" height={260}>
                  <PieChart>
                    <Pie
                      data={expensePieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={55}
                      outerRadius={100}
                      paddingAngle={3}
                      dataKey="value"
                    >
                      {expensePieData.map((_: any, i: number) => (
                        <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(v: any) => formatYuan(v)} />
                  </PieChart>
                </ResponsiveContainer>
                <div style={{ width: '40%' }}>
                  {expensePieData.map((d: any, i: number) => (
                    <div key={d.name} style={{
                      display: 'flex', alignItems: 'center', gap: 8,
                      marginBottom: 8, fontSize: 13,
                    }}>
                      <span style={{
                        width: 10, height: 10, borderRadius: '50%',
                        background: PIE_COLORS[i % PIE_COLORS.length],
                        display: 'inline-block', flexShrink: 0,
                      }} />
                      <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {d.name}
                      </span>
                      <span style={{ fontWeight: 500, color: EXPENSE_COLOR }}>
                        ¥{d.value.toFixed(2)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Empty description="暂无支出数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />
              </div>
            )}
          </Card>
        </Col>

        {/* 月度趋势柱状图 */}
        <Col xs={24} lg={12}>
          <Card title="月度收支趋势" size="small">
            {barData.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={barData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis
                    dataKey="month"
                    tick={{ fontSize: 12 }}
                    axisLine={{ stroke: '#e8e8e8' }}
                  />
                  <YAxis
                    tick={{ fontSize: 12 }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(v: number) => v >= 10000 ? `${(v / 10000).toFixed(1)}万` : `${v}`}
                  />
                  <Tooltip formatter={(v: any) => formatYuan(v)} />
                  <Legend
                    formatter={(value: string) => value === 'income' ? '收入' : '支出'}
                  />
                  <Bar dataKey="income" name="income" fill={INCOME_COLOR}
                    radius={[4, 4, 0, 0]} maxBarSize={36} />
                  <Bar dataKey="expense" name="expense" fill={EXPENSE_COLOR}
                    radius={[4, 4, 0, 0]} maxBarSize={36} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Empty description="暂无趋势数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* ===== 交易列表 ===== */}
      <Card
        title="交易记录"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={openAddModal}>
            新增记录
          </Button>
        }
        style={{ marginBottom: 16 }}
      >
        <Row gutter={[12, 12]} className="finance-filters" style={{ marginBottom: 16 }}>
          <Col>
            <DatePicker
              picker="month"
              value={dayjs(`${filters.year}-${filters.month}`)}
              onChange={d => {
                if (d) {
                  handleFilterChange('year', d.year())
                  handleFilterChange('month', d.month() + 1)
                }
              }}
              allowClear={false}
            />
          </Col>
          <Col>
            <Select
              allowClear placeholder="全部类型" style={{ width: 120 }}
              value={filters.transaction_type}
              onChange={v => handleFilterChange('transaction_type', v)}
            >
              <Select.Option value="income">收入</Select.Option>
              <Select.Option value="expense">支出</Select.Option>
            </Select>
          </Col>
          <Col>
            <Select
              allowClear placeholder="全部分类" style={{ width: 130 }}
              value={filters.category}
              onChange={v => handleFilterChange('category', v)}
              disabled={!filters.transaction_type}
            >
              {(filters.transaction_type === 'income' ? categories.income : categories.expense).map(c => (
                <Select.Option key={c} value={c}>{c}</Select.Option>
              ))}
            </Select>
          </Col>
          <Col>
            <Button onClick={loadData}>刷新</Button>
          </Col>
        </Row>

        <Table
          columns={columns}
          dataSource={transactions}
          rowKey="id"
          loading={loading}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            showTotal: (t) => `共 ${t} 条`,
          }}
          onChange={handleTableChange}
          locale={{ emptyText: <Empty description="暂无交易记录" image={Empty.PRESENTED_IMAGE_SIMPLE} /> }}
          scroll={{ x: 580 }}
        />
      </Card>

      {/* ===== 新增/编辑弹窗 ===== */}
      <Modal
        title={editingRecord ? '编辑记录' : '新增记录'}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={() => setModalVisible(false)}
        okText="确定"
        cancelText="取消"
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item name="transaction_type" label="类型" rules={[{ required: true, message: '请选择类型' }]}>
            <Select onChange={() => form.setFieldValue('category', undefined)}>
              <Select.Option value="income">收入</Select.Option>
              <Select.Option value="expense">支出</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="category" label="分类" rules={[{ required: true, message: '请选择分类' }]}>
            <Select placeholder="请选择分类">
              {form.getFieldValue('transaction_type') === 'income'
                ? categories.income.map(c => (
                  <Select.Option key={c} value={c}>{c}</Select.Option>
                ))
                : categories.expense.map(c => (
                  <Select.Option key={c} value={c}>{c}</Select.Option>
                ))
              }
            </Select>
          </Form.Item>
          <Form.Item name="amount" label="金额" rules={[
            { required: true, message: '请输入金额' },
            { type: 'number', min: 0.01, message: '金额必须大于0' },
          ]}>
            <InputNumber style={{ width: '100%' }} prefix="¥" precision={2} placeholder="0.00" />
          </Form.Item>
          <Form.Item name="transaction_date" label="日期" rules={[{ required: true, message: '请选择日期' }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} placeholder="可选" />
          </Form.Item>
          <Form.Item name="created_by" label="记录人">
            <Input placeholder="可选" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default FinancePage
