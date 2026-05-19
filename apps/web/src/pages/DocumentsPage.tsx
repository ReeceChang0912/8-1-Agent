import React, { useEffect, useMemo, useState } from 'react'
import { Card, Row, Col, Statistic, Tabs, List, Tag, Button, Modal, Form, Input, InputNumber, DatePicker, Space, Typography, message, Empty, Spin, Select } from 'antd'
import { IdcardOutlined, AlertOutlined, ClockCircleOutlined, PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { lifeModulesAPI } from '../services/api'

const { Text, Paragraph, Title } = Typography

const tabConfig = {
  identity: { docType: 'identity', title: '身份证件', statuses: ['有效', '临近到期', '已失效'] },
  asset: { docType: 'asset', title: '资产证照', statuses: ['有效', '需整理', '已归档'] },
  travel: { docType: 'travel', title: '出行证件', statuses: ['有效', '待更新', '已失效'] },
}

const docLabels: Record<string, string> = {
  identity: '身份证件',
  passport: '出入境证件',
  driver: '驾驶证',
  asset: '资产证照',
  travel: '出行证件',
  other: '其他',
}

const DocumentsPage: React.FC = () => {
  const familyId = localStorage.getItem('family_id') || ''
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [tab, setTab] = useState<'identity' | 'asset' | 'travel'>('identity')
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
        lifeModulesAPI.documents.list(familyId),
        lifeModulesAPI.documents.stats(familyId),
      ])
      setItems(listRes.data.items || [])
      setStats(statsRes.data || {})
    } catch {
      message.error('加载证件管理失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const grouped = useMemo(() => ({
    identity: items.filter(item => ['identity', 'passport', 'driver'].includes(item.doc_type || 'identity')),
    asset: items.filter(item => item.doc_type === 'asset'),
    travel: items.filter(item => item.doc_type === 'travel'),
  }), [items])

  const filtered = useMemo(() => {
    const q = keyword.trim().toLowerCase()
    if (!q) return grouped
    const filterItems = (list: any[]) =>
      list.filter(item =>
        `${item.doc_type || ''} ${item.title || ''} ${item.holder || ''} ${item.number || ''} ${item.issuer || ''} ${item.note || ''}`.toLowerCase().includes(q),
      )
    return {
      identity: filterItems(grouped.identity),
      asset: filterItems(grouped.asset),
      travel: filterItems(grouped.travel),
    }
  }, [grouped, keyword])

  const currentConfig = tabConfig[tab]

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    form.setFieldsValue({ doc_type: currentConfig.docType, status: currentConfig.statuses[0], reminder_days: 30 })
    setOpen(true)
  }

  const editItem = (item: any) => {
    setEditing(item)
    const nextTab = item.doc_type === 'asset' ? 'asset' : item.doc_type === 'travel' ? 'travel' : 'identity'
    setTab(nextTab)
    form.setFieldsValue({
      ...item,
      issue_date: item.issue_date ? dayjs(item.issue_date) : undefined,
      expiry_date: item.expiry_date ? dayjs(item.expiry_date) : undefined,
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
        doc_type: tabConfig[tab].docType,
        issue_date: values.issue_date ? values.issue_date.format('YYYY-MM-DD') : '',
        expiry_date: values.expiry_date ? values.expiry_date.format('YYYY-MM-DD') : '',
      }
      if (editing?.id) await lifeModulesAPI.documents.update(editing.id, payload)
      else await lifeModulesAPI.documents.add(payload)
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
    await lifeModulesAPI.documents.remove(id, familyId)
    message.success('已删除')
    await load()
  }

  const expiredCount = stats.expired_count || 0
  const expiringSoonCount = stats.expiring_soon_count || 0

  return (
    <div>
      <Card style={{ marginBottom: 16, borderRadius: 8 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} lg={8}>
            <Title level={4} style={{ margin: 0 }}>证件管理</Title>
            <Paragraph style={{ marginTop: 8, marginBottom: 0 }}>
              身份、出行、资产相关证件集中管理，快到期时可以提前提醒。
            </Paragraph>
          </Col>
          <Col xs={12} md={6} lg={4}><Statistic title="证件总数" value={stats.total_count || 0} prefix={<IdcardOutlined />} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="临近到期" value={expiringSoonCount} prefix={<ClockCircleOutlined />} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="已失效" value={expiredCount} prefix={<AlertOutlined />} /></Col>
          <Col xs={12} md={6} lg={4}><Statistic title="有效中" value={stats.active_count || 0} prefix={<IdcardOutlined />} /></Col>
        </Row>
      </Card>

      <Card extra={<Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>新增{currentConfig.title}</Button>} style={{ borderRadius: 8 }}>
        <Input.Search
          allowClear
          placeholder="搜索证件、持有人、号码、备注"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          style={{ marginBottom: 16, maxWidth: 360 }}
        />
        {loading ? <Spin /> : (
          <Tabs activeKey={tab} onChange={(value) => setTab(value as typeof tab)} items={[
            {
              key: 'identity',
              label: '身份',
              children: filtered.identity.length ? (
                <List dataSource={[...filtered.identity].sort((a, b) => String(a.expiry_date || '').localeCompare(String(b.expiry_date || '')))} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => editItem(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta
                      avatar={<IdcardOutlined />}
                      title={<Space><Text strong>{item.title}</Text><Tag>{item.status}</Tag><Tag>{docLabels[item.doc_type] || item.doc_type}</Tag></Space>}
                      description={`${item.holder || '未填写持有人'} · ${item.number || '未填写号码'} · ${item.issuer || '未填写签发机构'}`}
                    />
                    <div style={{ textAlign: 'right' }}>
                      <Text type="secondary">签发 {item.issue_date || '未设置'}</Text>
                      <div><Text type="secondary">到期 {item.expiry_date || '未设置'}</Text></div>
                    </div>
                  </List.Item>
                )} />
              ) : <Empty description={keyword ? '没有匹配结果' : '暂无身份相关证件'} />,
            },
            {
              key: 'asset',
              label: '资产',
              children: filtered.asset.length ? (
                <List dataSource={filtered.asset} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => editItem(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta
                      avatar={<IdcardOutlined />}
                      title={<Space><Text strong>{item.title}</Text><Tag color="blue">{item.status}</Tag></Space>}
                      description={item.note || '未填写说明'}
                    />
                    <Text type="secondary">{item.expiry_date || '未设置到期'}</Text>
                  </List.Item>
                )} />
              ) : <Empty description={keyword ? '没有匹配结果' : '暂无资产证照'} />,
            },
            {
              key: 'travel',
              label: '出行',
              children: filtered.travel.length ? (
                <List dataSource={filtered.travel} renderItem={(item) => (
                  <List.Item actions={[
                    <Button key="e" type="link" icon={<EditOutlined />} onClick={() => editItem(item)}>编辑</Button>,
                    <Button key="d" type="link" danger icon={<DeleteOutlined />} onClick={() => remove(item.id)}>删除</Button>,
                  ]}>
                    <List.Item.Meta
                      avatar={<ClockCircleOutlined />}
                      title={<Space><Text strong>{item.title}</Text><Tag color="green">{item.status}</Tag></Space>}
                      description={`${item.holder || '未填写持有人'} · ${item.number || '未填写号码'} · ${item.note || '未填写备注'}`}
                    />
                    <Text type="secondary">提醒 {Number(item.reminder_days || 30)} 天前</Text>
                  </List.Item>
                )} />
              ) : <Empty description={keyword ? '没有匹配结果' : '暂无出行证件'} />,
            },
          ]} />
        )}
      </Card>

      <Modal title={`${editing ? '编辑' : '新增'}${currentConfig.title}`} open={open} onCancel={() => setOpen(false)} onOk={save} confirmLoading={saving} okText="保存" cancelText="取消" destroyOnHidden>
        <Form layout="vertical" form={form}>
          <Form.Item name="title" label="证件名称" rules={[{ required: true, message: '请输入证件名称' }]}><Input /></Form.Item>
          <Form.Item name="holder" label="持有人"><Input /></Form.Item>
          <Form.Item name="number" label="证件号码"><Input /></Form.Item>
          <Form.Item name="issuer" label="签发机构"><Input /></Form.Item>
          <Form.Item name="doc_type" label="证件类型" rules={[{ required: true, message: '请选择证件类型' }]}>
            <Select options={Object.entries(docLabels).map(([value, label]) => ({ value, label }))} />
          </Form.Item>
          <Form.Item name="status" label="状态" rules={[{ required: true, message: '请选择状态' }]}>
            <Select options={currentConfig.statuses.map(value => ({ label: value, value }))} />
          </Form.Item>
          <Form.Item name="issue_date" label="签发日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="expiry_date" label="到期日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="reminder_days" label="提前提醒天数"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="note" label="备注"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default DocumentsPage
