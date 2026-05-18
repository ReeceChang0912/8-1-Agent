import React, { useEffect, useMemo, useState } from 'react'
import { Card, Row, Col, Statistic, Tabs, List, Tag, Button, Modal, Form, Input, InputNumber, DatePicker, Space, Typography, message, Empty, Spin, Select } from 'antd'
import { HeartOutlined, FireOutlined, TrophyOutlined, PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { lifeModulesAPI } from '../services/api'

const { Text, Paragraph, Title } = Typography

const tabConfig = {
  workouts: { recordType: 'workout', title: '训练记录', statuses: ['低强度', '中等', '高强度'] },
  metrics: { recordType: 'metric', title: '身体数据', statuses: ['晨起', '训练后', '晚间'] },
  meals: { recordType: 'meal', title: '饮食记录', statuses: ['早餐', '午餐', '晚餐', '加餐'] },
}

const FitnessPage: React.FC = () => {
  const familyId = localStorage.getItem('family_id') || ''
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [tab, setTab] = useState<'workouts' | 'metrics' | 'meals'>('workouts')
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<any>(null)
  const [items, setItems] = useState<any[]>([])
  const [stats, setStats] = useState<any>({})
  const [form] = Form.useForm()

  const load = async () => {
    setLoading(true)
    try {
      const [listRes, statsRes] = await Promise.all([
        lifeModulesAPI.fitness.list(familyId),
        lifeModulesAPI.fitness.stats(familyId),
      ])
      setItems(listRes.data.items || [])
      setStats(statsRes.data || {})
    } catch {
      message.error('加载健身管理失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const grouped = useMemo(() => ({
    workouts: items.filter(item => item.record_type === 'workout'),
    metrics: items.filter(item => item.record_type === 'metric'),
    meals: items.filter(item => item.record_type === 'meal'),
  }), [items])

  const currentConfig = tabConfig[tab]

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    form.setFieldsValue({ record_type: currentConfig.recordType, status: currentConfig.statuses[0], duration: 0, calories: 0, protein: 0 })
    setOpen(true)
  }

  const editItem = (item: any) => {
    setEditing(item)
    const nextTab = item.record_type === 'metric' ? 'metrics' : item.record_type === 'meal' ? 'meals' : 'workouts'
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
      if (editing?.id) await lifeModulesAPI.fitness.update(editing.id, payload)
      else await lifeModulesAPI.fitness.add(payload)
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
    await lifeModulesAPI.fitness.remove(id, familyId)
    message.success('已删除')
    await load()
  }

  return (
    <div>
      <Card style={{ marginBottom: 16, borderRadius: 8 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} lg={8}>
            <Title level={4} style={{ margin: 0 }}>健身管理</Title>
            <Paragraph style={{ marginTop: 8, marginBottom: 0 }}>
              训练、体重和饮食放在同一块面板里，周节奏和变化会更容易看出来。
            </Paragraph>
          </Col>
          <Col xs={12} md={6} lg={4}><Statistic title="训练次数" value={stats.workout_count || 0} prefix={<FireOutlined />} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="身体记录" value={stats.metric_count || 0} prefix={<HeartOutlined />} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="平均体重" value={stats.avg_weight || 0} suffix="kg" prefix={<HeartOutlined />} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="蛋白摄入" value={stats.protein_today || 0} suffix="g" prefix={<TrophyOutlined />} /></Col>
        </Row>
      </Card>

      <Card extra={<Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>新增{currentConfig.title}</Button>} style={{ borderRadius: 8 }}>
        {loading ? <Spin /> : (
          <Tabs activeKey={tab} onChange={(value) => setTab(value as typeof tab)} items={[
            {
              key: 'workouts',
              label: '训练',
              children: grouped.workouts.length ? (
                <List dataSource={grouped.workouts} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => editItem(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta avatar={<FireOutlined />} title={<Space><Text strong>{item.title}</Text><Tag>{item.status}</Tag></Space>} description={`${item.record_date || '未设置日期'} · ${Number(item.duration || 0)} 分钟`} />
                    <Text strong>{Number(item.calories || 0)} kcal</Text>
                  </List.Item>
                )} />
              ) : <Empty description="暂无训练记录" />,
            },
            {
              key: 'metrics',
              label: '身体数据',
              children: grouped.metrics.length ? (
                <List dataSource={grouped.metrics} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => editItem(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta avatar={<HeartOutlined />} title={<Space><Text strong>{item.record_date || '未设置日期'}</Text><Tag>{item.status}</Tag></Space>} description={`体重 ${Number(item.weight || 0)} kg · 体脂 ${Number(item.body_fat || 0)}% · 腰围 ${Number(item.waist || 0)} cm`} />
                  </List.Item>
                )} />
              ) : <Empty description="暂无身体数据" />,
            },
            {
              key: 'meals',
              label: '饮食',
              children: grouped.meals.length ? (
                <List dataSource={grouped.meals} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => editItem(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta avatar={<TrophyOutlined />} title={<Space><Text strong>{item.title}</Text><Tag>{item.status}</Tag></Space>} description={`${item.record_date || '未设置日期'} · 蛋白质 ${Number(item.protein || 0)} g · ${item.note || '未填写备注'}`} />
                    <Text strong>{Number(item.calories || 0)} kcal</Text>
                  </List.Item>
                )} />
              ) : <Empty description="暂无饮食记录" />,
            },
          ]} />
        )}
      </Card>

      <Modal title={`${editing ? '编辑' : '新增'}${currentConfig.title}`} open={open} onCancel={() => setOpen(false)} onOk={save} confirmLoading={saving} okText="保存" cancelText="取消" destroyOnHidden>
        <Form layout="vertical" form={form}>
          <Form.Item name="title" label="标题" rules={[{ required: true, message: '请输入标题' }]}><Input /></Form.Item>
          <Form.Item name="status" label={tab === 'meals' ? '餐次' : tab === 'metrics' ? '记录场景' : '训练强度'} rules={[{ required: true, message: '请选择状态' }]}>
            <Select options={currentConfig.statuses.map(value => ({ label: value, value }))} />
          </Form.Item>
          <Form.Item name="record_date" label="日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          {tab === 'workouts' && (
            <>
              <Form.Item name="duration" label="时长(分钟)"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item>
              <Form.Item name="calories" label="消耗(kcal)"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item>
            </>
          )}
          {tab === 'metrics' && (
            <>
              <Form.Item name="weight" label="体重(kg)"><InputNumber min={0} step={0.1} style={{ width: '100%' }} /></Form.Item>
              <Form.Item name="body_fat" label="体脂率(%)"><InputNumber min={0} step={0.1} style={{ width: '100%' }} /></Form.Item>
              <Form.Item name="waist" label="腰围(cm)"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item>
            </>
          )}
          {tab === 'meals' && (
            <>
              <Form.Item name="calories" label="热量(kcal)"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item>
              <Form.Item name="protein" label="蛋白质(g)"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item>
            </>
          )}
          <Form.Item name="note" label="备注"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default FitnessPage
