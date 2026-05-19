import React, { useEffect, useMemo, useState } from 'react'
import { Card, Row, Col, Statistic, Tabs, List, Tag, Button, Modal, Form, Input, InputNumber, DatePicker, Space, Typography, message, Empty, Spin, Select } from 'antd'
import { HeartOutlined, MedicineBoxOutlined, CalendarOutlined, PlusOutlined, DeleteOutlined, EditOutlined, FileTextOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { lifeModulesAPI } from '../services/api'

const { Text, Paragraph, Title } = Typography

const tabConfig = {
  exam: { recordType: 'exam', title: '体检报告', statuses: ['正常', '异常', '需复查'] },
  medication: { recordType: 'medication', title: '用药记录', statuses: ['在用', '调整中', '已停用'] },
  followup: { recordType: 'followup', title: '复诊安排', statuses: ['待就诊', '已预约', '已完成'] },
  chronic: { recordType: 'chronic', title: '慢病跟踪', statuses: ['稳定', '观察中', '需关注'] },
}

const HealthPage: React.FC = () => {
  const familyId = localStorage.getItem('family_id') || ''
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [tab, setTab] = useState<'exam' | 'medication' | 'followup' | 'chronic'>('exam')
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
        lifeModulesAPI.health.list(familyId),
        lifeModulesAPI.health.stats(familyId),
      ])
      setItems(listRes.data.items || [])
      setStats(statsRes.data || {})
    } catch {
      message.error('加载健康管理失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const grouped = useMemo(() => ({
    exam: items.filter(item => item.record_type === 'exam'),
    medication: items.filter(item => item.record_type === 'medication'),
    followup: items.filter(item => item.record_type === 'followup'),
    chronic: items.filter(item => item.record_type === 'chronic'),
  }), [items])

  const filtered = useMemo(() => {
    const q = keyword.trim().toLowerCase()
    if (!q) return grouped
    const filterItems = (list: any[]) =>
      list.filter(item =>
        `${item.title || ''} ${item.provider || ''} ${item.dosage || ''} ${item.frequency || ''} ${item.status || ''} ${item.note || ''}`.toLowerCase().includes(q),
      )
    return {
      exam: filterItems(grouped.exam),
      medication: filterItems(grouped.medication),
      followup: filterItems(grouped.followup),
      chronic: filterItems(grouped.chronic),
    }
  }, [grouped, keyword])

  const currentConfig = tabConfig[tab]

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    form.setFieldsValue({ record_type: currentConfig.recordType, status: currentConfig.statuses[0], weight: 0, bp_systolic: 0, bp_diastolic: 0 })
    setOpen(true)
  }

  const editItem = (item: any) => {
    setEditing(item)
    const nextTab = item.record_type === 'medication' ? 'medication' : item.record_type === 'followup' ? 'followup' : item.record_type === 'chronic' ? 'chronic' : 'exam'
    setTab(nextTab)
    form.setFieldsValue({
      ...item,
      record_date: item.record_date ? dayjs(item.record_date) : undefined,
      next_visit: item.next_visit ? dayjs(item.next_visit) : undefined,
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
        record_date: values.record_date ? values.record_date.format('YYYY-MM-DD') : '',
        next_visit: values.next_visit ? values.next_visit.format('YYYY-MM-DD') : '',
      }
      if (editing?.id) await lifeModulesAPI.health.update(editing.id, payload)
      else await lifeModulesAPI.health.add(payload)
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
    await lifeModulesAPI.health.remove(id, familyId)
    message.success('已删除')
    await load()
  }

  return (
    <div>
      <Card style={{ marginBottom: 16, borderRadius: 8 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} lg={8}>
            <Title level={4} style={{ margin: 0 }}>健康管理</Title>
            <Paragraph style={{ marginTop: 8, marginBottom: 0 }}>
              体检、用药、复诊和慢病跟踪都放在同一块，健康信息会更连贯。
            </Paragraph>
          </Col>
          <Col xs={12} md={6} lg={4}><Statistic title="记录总数" value={stats.total_count || 0} prefix={<HeartOutlined />} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="体检异常" value={stats.abnormal_count || 0} prefix={<FileTextOutlined />} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="待复诊" value={stats.due_soon_count || 0} prefix={<CalendarOutlined />} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="已逾期" value={stats.overdue_count || 0} prefix={<MedicineBoxOutlined />} /></Col>
        </Row>
      </Card>

      <Card extra={<Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>新增{currentConfig.title}</Button>} style={{ borderRadius: 8 }}>
        <Input.Search
          allowClear
          placeholder="搜索标题、机构、剂量、备注"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          style={{ marginBottom: 16, maxWidth: 360 }}
        />
        {loading ? <Spin /> : (
          <Tabs activeKey={tab} onChange={(value) => setTab(value as typeof tab)} items={[
            {
              key: 'exam',
              label: '体检',
              children: filtered.exam.length ? (
                <List dataSource={[...filtered.exam].sort((a, b) => String(b.record_date || '').localeCompare(String(a.record_date || '')))} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => editItem(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta
                      avatar={<FileTextOutlined />}
                      title={<Space><Text strong>{item.title}</Text><Tag>{item.status}</Tag></Space>}
                      description={`${item.record_date || '未设置日期'} · ${item.provider || '未填写机构'} · ${item.note || '未填写备注'}`}
                    />
                    <div style={{ textAlign: 'right' }}>
                      <Text type="secondary">血压 {Number(item.bp_systolic || 0)}/{Number(item.bp_diastolic || 0)}</Text>
                    </div>
                  </List.Item>
                )} />
              ) : <Empty description={keyword ? '没有匹配结果' : '暂无体检记录'} />,
            },
            {
              key: 'medication',
              label: '用药',
              children: filtered.medication.length ? (
                <List dataSource={[...filtered.medication].sort((a, b) => String(b.record_date || '').localeCompare(String(a.record_date || '')))} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => editItem(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta
                      avatar={<MedicineBoxOutlined />}
                      title={<Space><Text strong>{item.title}</Text><Tag color="blue">{item.status}</Tag></Space>}
                      description={`${item.dosage || '未填写剂量'} · ${item.frequency || '未填写频次'} · ${item.note || '未填写备注'}`}
                    />
                    <Text type="secondary">{item.record_date || '未设置日期'}</Text>
                  </List.Item>
                )} />
              ) : <Empty description={keyword ? '没有匹配结果' : '暂无用药记录'} />,
            },
            {
              key: 'followup',
              label: '复诊',
              children: filtered.followup.length ? (
                <List dataSource={[...filtered.followup].sort((a, b) => String(a.next_visit || '').localeCompare(String(b.next_visit || '')))} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => editItem(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta
                      avatar={<CalendarOutlined />}
                      title={<Space><Text strong>{item.title}</Text><Tag>{item.status}</Tag></Space>}
                      description={`${item.provider || '未填写医院'} · 下次复诊 ${item.next_visit || '未设置'} · ${item.note || '未填写备注'}`}
                    />
                  </List.Item>
                )} />
              ) : <Empty description={keyword ? '没有匹配结果' : '暂无复诊安排'} />,
            },
            {
              key: 'chronic',
              label: '慢病',
              children: filtered.chronic.length ? (
                <List dataSource={filtered.chronic} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => editItem(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta
                      avatar={<HeartOutlined />}
                      title={<Space><Text strong>{item.title}</Text><Tag color={item.status === '稳定' ? 'green' : 'gold'}>{item.status}</Tag></Space>}
                      description={`${item.provider || '未填写医生'} · ${item.note || '未填写备注'}`}
                    />
                  </List.Item>
                )} />
              ) : <Empty description={keyword ? '没有匹配结果' : '暂无慢病跟踪'} />,
            },
          ]} />
        )}
      </Card>

      <Modal title={`${editing ? '编辑' : '新增'}${currentConfig.title}`} open={open} onCancel={() => setOpen(false)} onOk={save} confirmLoading={saving} okText="保存" cancelText="取消" destroyOnHidden>
        <Form layout="vertical" form={form}>
          <Form.Item name="title" label="标题" rules={[{ required: true, message: '请输入标题' }]}><Input /></Form.Item>
          <Form.Item name="provider" label="医院/机构"><Input /></Form.Item>
          <Form.Item name="status" label="状态" rules={[{ required: true, message: '请选择状态' }]}>
            <Select options={currentConfig.statuses.map(value => ({ label: value, value }))} />
          </Form.Item>
          <Form.Item name="record_date" label="记录日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="next_visit" label="下次复诊/提醒日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          {tab === 'exam' && (
            <>
              <Form.Item name="bp_systolic" label="收缩压"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item>
              <Form.Item name="bp_diastolic" label="舒张压"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item>
            </>
          )}
          {tab === 'medication' && (
            <>
              <Form.Item name="dosage" label="剂量"><Input /></Form.Item>
              <Form.Item name="frequency" label="频次"><Input /></Form.Item>
            </>
          )}
          {tab === 'chronic' && (
            <Form.Item name="weight" label="体重(kg)"><InputNumber min={0} step={0.1} style={{ width: '100%' }} /></Form.Item>
          )}
          <Form.Item name="note" label="备注"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default HealthPage
