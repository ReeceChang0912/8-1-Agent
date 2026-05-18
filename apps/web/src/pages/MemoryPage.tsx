import React, { useEffect, useState } from 'react'
import { Button, Card, Input, InputNumber, Modal, Select, Space, Table, Tag, message, Popconfirm, Statistic, Row, Col } from 'antd'
import { DeleteOutlined, EditOutlined, ReloadOutlined, SearchOutlined } from '@ant-design/icons'
import { memoryAPI } from '../services/api'

const typeOptions = [
  { label: '全部', value: 'all' },
  { label: '长期事实', value: 'long_term' },
  { label: '情景记忆', value: 'episodic' },
  { label: '摘要', value: 'summary' },
  { label: '短期', value: 'short_term' },
  { label: '工作记忆', value: 'working' },
]

const typeColorMap: Record<string, string> = {
  long_term: 'blue',
  episodic: 'purple',
  summary: 'gold',
  short_term: 'green',
  working: 'cyan',
}

const MemoryPage: React.FC = () => {
  const userId = localStorage.getItem('member_name') || ''
  const familyId = localStorage.getItem('family_id') || ''
  const [items, setItems] = useState<any[]>([])
  const [stats, setStats] = useState<any>({})
  const [query, setQuery] = useState('')
  const [memoryType, setMemoryType] = useState('all')
  const [loading, setLoading] = useState(false)
  const [editing, setEditing] = useState<any | null>(null)
  const [editContent, setEditContent] = useState('')
  const [editImportance, setEditImportance] = useState<number | null>(null)
  const [editTags, setEditTags] = useState('')

  const load = async () => {
    setLoading(true)
    try {
      const res = await memoryAPI.list({
        query,
        memory_type: memoryType,
        limit: 200,
        user_id: userId,
        family_id: familyId,
      })
      setItems(res.data.items || [])
      setStats(res.data.stats || {})
    } catch {
      message.error('加载记忆失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [memoryType])

  const remove = async (id: string) => {
    try {
      await memoryAPI.remove(id, { user_id: userId, family_id: familyId })
      message.success('已删除')
      load()
    } catch {
      message.error('删除失败')
    }
  }

  const openEdit = (row: any) => {
    setEditing(row)
    setEditContent(row.content || '')
    setEditImportance(Number(row.importance || 0.5))
    setEditTags((row.tags || []).join(','))
  }

  const saveEdit = async () => {
    if (!editing) return
    try {
      await memoryAPI.update(editing.id, {
        content: editContent,
        importance: editImportance ?? undefined,
        tags: editTags.split(',').map(t => t.trim()).filter(Boolean),
      }, { user_id: userId, family_id: familyId })
      message.success('已保存')
      setEditing(null)
      load()
    } catch {
      message.error('保存失败')
    }
  }

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={12} md={6}><Card><Statistic title="短期" value={stats.short_term_count || 0} /></Card></Col>
        <Col xs={12} md={6}><Card><Statistic title="长期/向量" value={stats.long_term_count || 0} /></Card></Col>
        <Col xs={12} md={6}><Card><Statistic title="摘要" value={stats.summary_count || 0} /></Card></Col>
        <Col xs={12} md={6}><Card><Statistic title="Chroma" value={stats.chroma_enabled ? '启用' : '降级'} /></Card></Col>
      </Row>

      <Card
        title="记忆管理"
        extra={
          <Space>
            <Input
              allowClear
              placeholder="搜索记忆"
              prefix={<SearchOutlined />}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onPressEnter={load}
              style={{ width: 220 }}
            />
            <Select value={memoryType} onChange={setMemoryType} options={typeOptions} style={{ width: 120 }} />
            <Button icon={<ReloadOutlined />} onClick={load}>刷新</Button>
          </Space>
        }
      >
        <Table
          rowKey="id"
          loading={loading}
          dataSource={items}
          pagination={{ pageSize: 12 }}
          columns={[
            {
              title: '类型',
              dataIndex: 'memory_type',
              width: 120,
              render: (value) => <Tag color={typeColorMap[value] || 'default'}>{value}</Tag>,
            },
            {
              title: '内容',
              dataIndex: 'content',
              render: (value, row) => (
                <div>
                  <div style={{ whiteSpace: 'pre-wrap' }}>{value}</div>
                  <div style={{ marginTop: 6 }}>
                    {(row.tags || []).map((tag: string) => <Tag key={tag} color="blue">{tag}</Tag>)}
                    {row.family_id && <Tag color="geekblue">家庭: {row.family_id}</Tag>}
                    {row.user_id && <Tag color="lime">成员: {row.user_id}</Tag>}
                  </div>
                </div>
              ),
            },
            {
              title: '重要性',
              dataIndex: 'importance',
              width: 90,
              render: (value) => Number(value || 0).toFixed(2),
            },
            {
              title: '时间',
              dataIndex: 'timestamp',
              width: 170,
              render: (value) => value ? new Date(value).toLocaleString('zh-CN') : '',
            },
            {
              title: '操作',
              width: 110,
              render: (_, row) => (
                <Space>
                  <Button type="text" icon={<EditOutlined />} onClick={() => openEdit(row)} />
                  <Popconfirm title="删除这条记忆？" onConfirm={() => remove(row.id)}>
                    <Button danger type="text" icon={<DeleteOutlined />} />
                  </Popconfirm>
                </Space>
              ),
            },
          ]}
        />
      </Card>

      <Modal
        title="编辑记忆"
        open={!!editing}
        onOk={saveEdit}
        onCancel={() => setEditing(null)}
        okText="保存"
        cancelText="取消"
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Input.TextArea rows={5} value={editContent} onChange={(e) => setEditContent(e.target.value)} />
          <InputNumber min={0} max={1} step={0.05} value={editImportance} onChange={setEditImportance} style={{ width: '100%' }} />
          <Input value={editTags} onChange={(e) => setEditTags(e.target.value)} placeholder="标签，用逗号分隔" />
        </Space>
      </Modal>
    </div>
  )
}

export default MemoryPage
