import React, { useEffect, useMemo, useState } from 'react'
import { Card, Row, Col, Statistic, Tabs, List, Tag, Button, Modal, Form, Input, InputNumber, DatePicker, Space, Typography, message, Empty, Spin, Select } from 'antd'
import { SafetyCertificateOutlined, BellOutlined, FileProtectOutlined, PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { lifeModulesAPI } from '../services/api'

const { Text, Paragraph, Title } = Typography

const tabConfig = {
  policies: { recordType: 'policy', title: '保单', statuses: ['有效', '待续保', '已失效'] },
  reminders: { recordType: 'reminder', title: '提醒', statuses: ['待处理', '已安排', '已完成'] },
  claims: { recordType: 'claim', title: '理赔', statuses: ['准备中', '处理中', '已结案'] },
}

const InsurancePage: React.FC = () => {
  const familyId = localStorage.getItem('family_id') || ''
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [tab, setTab] = useState<'policies' | 'reminders' | 'claims'>('policies')
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
        lifeModulesAPI.insurance.list(familyId),
        lifeModulesAPI.insurance.stats(familyId),
      ])
      setItems(listRes.data.items || [])
      setStats(statsRes.data || {})
    } catch {
      message.error('加载保险管理失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const grouped = useMemo(() => ({
    policies: items.filter(item => (item.record_type || 'policy') === 'policy'),
    reminders: items.filter(item => item.record_type === 'reminder'),
    claims: items.filter(item => item.record_type === 'claim'),
  }), [items])

  const filtered = useMemo(() => {
    const q = keyword.trim().toLowerCase()
    if (!q) return grouped
    const filterItems = (list: any[]) =>
      list.filter(item =>
        `${item.name || ''} ${item.title || ''} ${item.company || ''} ${item.holder || ''} ${item.coverage || ''} ${item.note || ''}`.toLowerCase().includes(q),
      )
    return {
      policies: filterItems(grouped.policies),
      reminders: filterItems(grouped.reminders),
      claims: filterItems(grouped.claims),
    }
  }, [grouped, keyword])

  const currentConfig = tabConfig[tab]

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    form.setFieldsValue({ record_type: currentConfig.recordType, status: currentConfig.statuses[0], premium: 0, amount: 0 })
    setOpen(true)
  }

  const editItem = (item: any) => {
    setEditing(item)
    const nextTab = item.record_type === 'claim' ? 'claims' : item.record_type === 'reminder' ? 'reminders' : 'policies'
    setTab(nextTab)
    form.setFieldsValue({ ...item, renew_date: item.renew_date ? dayjs(item.renew_date) : undefined })
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
        renew_date: values.renew_date ? values.renew_date.format('YYYY-MM-DD') : '',
      }
      if (editing?.id) await lifeModulesAPI.insurance.update(editing.id, payload)
      else await lifeModulesAPI.insurance.add(payload)
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
    await lifeModulesAPI.insurance.remove(id, familyId)
    message.success('已删除')
    await load()
  }

  return (
    <div>
      <Card style={{ marginBottom: 16, borderRadius: 8 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} lg={8}>
            <Title level={4} style={{ margin: 0 }}>保险管理</Title>
            <Paragraph style={{ marginTop: 8, marginBottom: 0 }}>
              保单、续保提醒、理赔推进放在同一个工作面，家庭保障会更清楚。
            </Paragraph>
          </Col>
          <Col xs={12} md={6} lg={4}><Statistic title="保单数" value={stats.policy_count || 0} prefix={<FileProtectOutlined />} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="待关注到期" value={stats.expiring_count || 0} prefix={<BellOutlined />} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="年保费" value={stats.annual_premium || 0} prefix={<SafetyCertificateOutlined />} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="理赔金额" value={stats.claim_amount || 0} prefix={<BellOutlined />} /></Col>
        </Row>
      </Card>

      <Card extra={<Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>新增{currentConfig.title}</Button>} style={{ borderRadius: 8 }}>
        <Input.Search
          allowClear
          placeholder="搜索保单、公司、持有人、备注"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          style={{ marginBottom: 16, maxWidth: 360 }}
        />
        {loading ? <Spin /> : (
          <Tabs activeKey={tab} onChange={(value) => setTab(value as typeof tab)} items={[
            {
              key: 'policies',
              label: '保单',
              children: filtered.policies.length ? (
                <List dataSource={[...filtered.policies].sort((a, b) => String(a.renew_date || '').localeCompare(String(b.renew_date || '')))} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => editItem(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta avatar={<FileProtectOutlined />} title={<Space><Text strong>{item.name}</Text><Tag color="green">{item.status}</Tag></Space>} description={`${item.holder || '未填写持有人'} · ${item.company || '未填写保险公司'} · ${item.coverage || '未填写保障范围'}`} />
                    <div style={{ textAlign: 'right' }}>
                      <Text strong>¥{Number(item.premium || 0).toLocaleString()}</Text>
                      <div><Text type="secondary">续保 {item.renew_date || '未设置'}</Text></div>
                    </div>
                  </List.Item>
                )} />
              ) : <Empty description={keyword ? '没有匹配结果' : '暂无保单'} />,
            },
            {
              key: 'reminders',
              label: '提醒',
              children: filtered.reminders.length ? (
                <List dataSource={[...filtered.reminders].sort((a, b) => String(a.renew_date || '').localeCompare(String(b.renew_date || '')))} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => editItem(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta avatar={<BellOutlined />} title={<Space><Text strong>{item.title || item.name}</Text><Tag>{item.status}</Tag></Space>} description={item.note || '未填写说明'} />
                    <Text type="secondary">{item.renew_date || '未设置日期'}</Text>
                  </List.Item>
                )} />
              ) : <Empty description={keyword ? '没有匹配结果' : '暂无提醒'} />,
            },
            {
              key: 'claims',
              label: '理赔',
              children: filtered.claims.length ? (
                <List dataSource={[...filtered.claims].sort((a, b) => Number(b.amount || 0) - Number(a.amount || 0))} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => editItem(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta avatar={<SafetyCertificateOutlined />} title={<Space><Text strong>{item.title || item.name}</Text><Tag>{item.status}</Tag></Space>} description={`${item.name || '未关联保单'} · ${item.note || '未填写说明'}`} />
                    <div style={{ textAlign: 'right' }}>
                      <Text strong>¥{Number(item.amount || 0).toLocaleString()}</Text>
                      <div><Text type="secondary">{item.renew_date || '未设置日期'}</Text></div>
                    </div>
                  </List.Item>
                )} />
              ) : <Empty description={keyword ? '没有匹配结果' : '暂无理赔记录'} />,
            },
          ]} />
        )}
      </Card>

      <Modal title={`${editing ? '编辑' : '新增'}${currentConfig.title}`} open={open} onCancel={() => setOpen(false)} onOk={save} confirmLoading={saving} okText="保存" cancelText="取消" destroyOnHidden>
        <Form layout="vertical" form={form}>
          <Form.Item name="name" label={tab === 'policies' ? '保单名称' : tab === 'claims' ? '关联保单' : '提醒名称'} rules={[{ required: true, message: '请填写名称' }]}><Input /></Form.Item>
          <Form.Item name="title" label="标题"><Input /></Form.Item>
          {tab === 'policies' && (
            <>
              <Form.Item name="holder" label="持有人"><Input /></Form.Item>
              <Form.Item name="company" label="保险公司"><Input /></Form.Item>
              <Form.Item name="coverage" label="保障范围"><Input /></Form.Item>
              <Form.Item name="premium" label="年保费"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item>
            </>
          )}
          {tab === 'claims' && (
            <Form.Item name="amount" label="理赔金额"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item>
          )}
          <Form.Item name="status" label="状态" rules={[{ required: true, message: '请选择状态' }]}>
            <Select options={currentConfig.statuses.map(value => ({ label: value, value }))} />
          </Form.Item>
          <Form.Item name="renew_date" label={tab === 'policies' ? '续保日期' : '日期'}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="note" label="备注"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default InsurancePage
