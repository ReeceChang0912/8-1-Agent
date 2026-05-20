import React, { useEffect, useMemo, useState } from 'react'
import { Card, Row, Col, Statistic, Tabs, List, Tag, Button, Modal, Form, Input, InputNumber, DatePicker, Space, Typography, message, Empty, Spin, Select } from 'antd'
import { CheckSquareOutlined, SyncOutlined, ShoppingCartOutlined, FileDoneOutlined, PlusOutlined, DeleteOutlined, EditOutlined, ClockCircleOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { lifeModulesAPI, membersAPI } from '../services/api'

const { Text, Paragraph, Title } = Typography

const tabConfig = {
  task: { recordType: 'task', title: '家务任务', statuses: ['待处理', '进行中', '已完成'] },
  rotation: { recordType: 'rotation', title: '轮值安排', statuses: ['待轮值', '本周执行', '已完成'] },
  supply: { recordType: 'supply', title: '补货事项', statuses: ['待补货', '采购中', '已补货'] },
  checklist: { recordType: 'checklist', title: '检查清单', statuses: ['待检查', '检查中', '已打卡'] },
}

const ChoresPage: React.FC = () => {
  const familyId = localStorage.getItem('family_id') || ''
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [tab, setTab] = useState<'task' | 'rotation' | 'supply' | 'checklist'>('task')
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
        lifeModulesAPI.chores.list(familyId),
        lifeModulesAPI.chores.stats(familyId),
      ])
      setItems(listRes.data.items || [])
      setStats(statsRes.data || {})
    } catch {
      message.error('加载家务分工失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  useEffect(() => {
    membersAPI.getAll().then(res => setMembers(res.data.members || [])).catch(() => setMembers([]))
  }, [])

  const grouped = useMemo(() => ({
    task: items.filter(item => item.record_type === 'task'),
    rotation: items.filter(item => item.record_type === 'rotation'),
    supply: items.filter(item => item.record_type === 'supply'),
    checklist: items.filter(item => item.record_type === 'checklist'),
  }), [items])

  const filtered = useMemo(() => {
    const q = keyword.trim().toLowerCase()
    if (!q) return grouped
    const filterItems = (list: any[]) =>
      list.filter(item =>
        `${item.title || ''} ${item.assignee || ''} ${item.frequency || ''} ${item.status || ''} ${item.note || ''}`.toLowerCase().includes(q)
        && (memberFilter === 'all' || (item.assignee || '') === memberFilter),
      )
    return {
      task: filterItems(grouped.task),
      rotation: filterItems(grouped.rotation),
      supply: filterItems(grouped.supply),
      checklist: filterItems(grouped.checklist),
    }
  }, [grouped, keyword, memberFilter])

  const currentConfig = tabConfig[tab]

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    form.setFieldsValue({ record_type: currentConfig.recordType, status: currentConfig.statuses[0], points: 0 })
    setOpen(true)
  }

  const editItem = (item: any) => {
    setEditing(item)
    const nextTab = item.record_type === 'rotation' ? 'rotation' : item.record_type === 'supply' ? 'supply' : item.record_type === 'checklist' ? 'checklist' : 'task'
    setTab(nextTab)
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
      if (editing?.id) await lifeModulesAPI.chores.update(editing.id, payload)
      else await lifeModulesAPI.chores.add(payload)
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
    await lifeModulesAPI.chores.remove(id, familyId)
    message.success('已删除')
    await load()
  }

  const tabIcon = {
    task: <CheckSquareOutlined />,
    rotation: <SyncOutlined />,
    supply: <ShoppingCartOutlined />,
    checklist: <FileDoneOutlined />,
  }

  return (
    <div>
      <Card style={{ marginBottom: 16, borderRadius: 8 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} lg={8}>
            <Title level={4} style={{ margin: 0 }}>家务分工</Title>
            <Paragraph style={{ marginTop: 8, marginBottom: 0 }}>
              家务任务、轮值、补货和巡检都放在一起，家庭协作会顺手很多。
            </Paragraph>
          </Col>
          <Col xs={12} md={6} lg={4}><Statistic title="记录总数" value={stats.total_count || 0} prefix={<CheckSquareOutlined />} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="已完成" value={stats.done_count || 0} prefix={<FileDoneOutlined />} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="已逾期" value={stats.overdue_count || 0} prefix={<ClockCircleOutlined />} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="积分合计" value={stats.points_total || 0} prefix={<SyncOutlined />} /></Col>
        </Row>
      </Card>

      <Card extra={<Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>新增{currentConfig.title}</Button>} style={{ borderRadius: 8 }}>
        <Space wrap style={{ marginBottom: 16 }}>
          <Input.Search
            allowClear
            placeholder="搜索任务、负责人、频率、备注"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            style={{ width: 360 }}
          />
          <Select value={memberFilter} onChange={setMemberFilter} style={{ width: 180 }} options={[{ label: '全部成员', value: 'all' }, ...members.map(member => ({ label: member.name, value: member.name }))]} />
        </Space>
        {loading ? <Spin /> : (
          <Tabs activeKey={tab} onChange={(value) => setTab(value as typeof tab)} items={[
            {
              key: 'task',
              label: '家务',
              children: filtered.task.length ? (
                <List dataSource={filtered.task} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => editItem(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta
                      avatar={tabIcon.task}
                      title={<Space><Text strong>{item.title}</Text><Tag>{item.status}</Tag></Space>}
                      description={`${item.assignee || '未分配'} · ${item.frequency || '未设频率'} · ${item.note || '未填写备注'}`}
                    />
                    <Text strong>{Number(item.points || 0)} 分</Text>
                  </List.Item>
                )} />
              ) : <Empty description={keyword ? '没有匹配结果' : '暂无家务任务'} />,
            },
            {
              key: 'rotation',
              label: '轮值',
              children: filtered.rotation.length ? (
                <List dataSource={filtered.rotation} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => editItem(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta
                      avatar={tabIcon.rotation}
                      title={<Space><Text strong>{item.title}</Text><Tag color="blue">{item.status}</Tag></Space>}
                      description={`${item.assignee || '未分配'} · ${item.frequency || '未设轮值频率'} · ${item.note || '未填写备注'}`}
                    />
                    <Text type="secondary">{item.due_date || '未设置日期'}</Text>
                  </List.Item>
                )} />
              ) : <Empty description={keyword ? '没有匹配结果' : '暂无轮值安排'} />,
            },
            {
              key: 'supply',
              label: '补货',
              children: filtered.supply.length ? (
                <List dataSource={filtered.supply} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => editItem(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta
                      avatar={tabIcon.supply}
                      title={<Space><Text strong>{item.title}</Text><Tag>{item.status}</Tag></Space>}
                      description={`${item.assignee || '未分配'} · ${item.due_date || '未设置补货日'} · ${item.note || '未填写备注'}`}
                    />
                  </List.Item>
                )} />
              ) : <Empty description={keyword ? '没有匹配结果' : '暂无补货事项'} />,
            },
            {
              key: 'checklist',
              label: '检查',
              children: filtered.checklist.length ? (
                <List dataSource={filtered.checklist} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => editItem(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta
                      avatar={tabIcon.checklist}
                      title={<Space><Text strong>{item.title}</Text><Tag color={item.status === '已打卡' ? 'green' : 'gold'}>{item.status}</Tag></Space>}
                      description={`${item.assignee || '未分配'} · ${item.frequency || '未设周期'} · ${item.note || '未填写备注'}`}
                    />
                  </List.Item>
                )} />
              ) : <Empty description={keyword ? '没有匹配结果' : '暂无检查清单'} />,
            },
          ]} />
        )}
      </Card>

      <Modal title={`${editing ? '编辑' : '新增'}${currentConfig.title}`} open={open} onCancel={() => setOpen(false)} onOk={save} confirmLoading={saving} okText="保存" cancelText="取消" destroyOnHidden>
        <Form layout="vertical" form={form}>
          <Form.Item name="title" label="标题" rules={[{ required: true, message: '请输入标题' }]}><Input /></Form.Item>
          <Form.Item name="assignee" label="负责人"><Select allowClear options={members.map(member => ({ label: member.name, value: member.name }))} /></Form.Item>
          <Form.Item name="frequency" label="频率/周期"><Input /></Form.Item>
          <Form.Item name="status" label="状态" rules={[{ required: true, message: '请选择状态' }]}>
            <Select options={currentConfig.statuses.map(value => ({ label: value, value }))} />
          </Form.Item>
          <Form.Item name="due_date" label="到期/执行日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="points" label="积分"><InputNumber min={0} step={1} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="note" label="备注"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default ChoresPage
