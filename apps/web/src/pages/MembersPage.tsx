import React, { useEffect, useMemo, useState } from 'react'
import { Alert, Button, Card, Col, Form, Input, InputNumber, Modal, Popconfirm, Row, Select, Space, Statistic, Table, Tag, message } from 'antd'
import { CopyOutlined, DeleteOutlined, EditOutlined, FireOutlined, HomeOutlined, LinkOutlined, ShoppingOutlined, TeamOutlined, UserAddOutlined, CheckSquareOutlined } from '@ant-design/icons'
import axios from 'axios'
import { membersAPI } from '../services/api'

const MembersPage: React.FC = () => {
  const familyId = localStorage.getItem('family_id') || ''
  const [members, setMembers] = useState<any[]>([])
  const [memberStats, setMemberStats] = useState<any>({ summary: {}, members: [] })
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [editingMember, setEditingMember] = useState<any>(null)
  const [familyInfo, setFamilyInfo] = useState<any>(null)
  const [inviteLoading, setInviteLoading] = useState(false)
  const [inviteData, setInviteData] = useState<any>(null)
  const [form] = Form.useForm()
  const [editForm] = Form.useForm()

  useEffect(() => {
    loadAll()
    loadFamilyInfo()
  }, [])

  const loadAll = async () => {
    setLoading(true)
    try {
      const [membersRes, statsRes] = await Promise.all([
        membersAPI.getAll(),
        membersAPI.getStats(familyId),
      ])
      setMembers(membersRes.data.members || [])
      setMemberStats(statsRes.data || { summary: {}, members: [] })
    } catch {
      message.error('加载成员信息失败')
    } finally {
      setLoading(false)
    }
  }

  const loadFamilyInfo = async () => {
    if (!familyId) return
    try {
      const res = await axios.get('/api/auth/family-members', { params: { family_id: familyId } })
      setFamilyInfo({
        family_id: familyId,
        family_name: localStorage.getItem('family_name'),
        members: res.data.members || [],
      })
    } catch {
      setFamilyInfo({ family_id: familyId, family_name: localStorage.getItem('family_name'), members: [] })
    }
  }

  const copyFamilyId = () => {
    if (familyInfo?.family_id) {
      navigator.clipboard.writeText(familyInfo.family_id)
      message.success('家庭号已复制')
    }
  }

  const createInvite = async () => {
    if (!familyId) return
    setInviteLoading(true)
    try {
      const creator = localStorage.getItem('member_name') || ''
      const res = await membersAPI.createInvite(familyId, creator)
      setInviteData(res.data)
      const joinUrl = `${window.location.origin}/?invite=${encodeURIComponent(res.data.code)}&family_id=${encodeURIComponent(familyId)}`
      await navigator.clipboard.writeText(joinUrl)
      message.success('邀请链接已复制')
    } catch {
      message.error('生成邀请失败')
    } finally {
      setInviteLoading(false)
    }
  }

  const handleAdd = async (values: any) => {
    try {
      await membersAPI.add(values)
      message.success('成员添加成功')
      setModalVisible(false)
      form.resetFields()
      await loadAll()
    } catch {
      message.error('添加失败')
    }
  }

  const handleEditClick = (record: any) => {
    setEditingMember(record)
    editForm.setFieldsValue(record)
    setEditModalVisible(true)
  }

  const handleEditOk = async (values: any) => {
    if (!editingMember) return
    try {
      await membersAPI.update(editingMember.name, values)
      message.success('成员已更新')
      setEditModalVisible(false)
      setEditingMember(null)
      await loadAll()
    } catch {
      message.error('更新失败')
    }
  }

  const handleDelete = async (name: string) => {
    try {
      await membersAPI.remove(name)
      message.success('成员已删除')
      await loadAll()
    } catch {
      message.error('删除失败')
    }
  }

  const topMembers = useMemo(() => (memberStats.members || []).slice(0, 4), [memberStats.members])

  const columns = [
    { title: '姓名', dataIndex: 'name', key: 'name' },
    { title: '角色', dataIndex: 'role', key: 'role' },
    { title: '年龄', dataIndex: 'age', key: 'age', width: 90 },
    { title: '交互风格', dataIndex: 'interaction_style', key: 'interaction_style' },
    { title: '权限', dataIndex: 'permission', key: 'permission' },
    {
      title: '标签',
      key: 'tags',
      render: (_: any, record: any) => (
        <Space wrap>
          {record.side ? <Tag>{record.side}</Tag> : null}
          {record.permission ? <Tag color={record.permission === 'admin' ? 'red' : 'blue'}>{record.permission}</Tag> : null}
        </Space>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEditClick(record)}>编辑</Button>
          <Popconfirm title="确定删除该成员？" onConfirm={() => handleDelete(record.name)} okText="确定" cancelText="取消">
            <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      {familyInfo && (
        <Alert
          type="info"
          showIcon={false}
          message={
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
              <span><HomeOutlined style={{ marginRight: 8 }} /><strong>{familyInfo.family_name}</strong> | 家庭号: <strong style={{ color: '#1890ff' }}>{familyInfo.family_id}</strong></span>
              <Space wrap>
                <Button size="small" icon={<CopyOutlined />} onClick={copyFamilyId}>复制家庭号</Button>
                <Button size="small" icon={<LinkOutlined />} loading={inviteLoading} onClick={createInvite}>生成邀请</Button>
              </Space>
            </div>
          }
        />
      )}

      {inviteData && (
        <Alert
          type="success"
          message="邀请链接已生成"
          description={
            <div style={{ wordBreak: 'break-all' }}>
              {`${window.location.origin}/?invite=${encodeURIComponent(inviteData.code)}&family_id=${encodeURIComponent(familyId)}`}
            </div>
          }
          closable
          onClose={() => setInviteData(null)}
        />
      )}

      <Card>
        <Row gutter={[16, 16]}>
          <Col xs={12} md={6}><Statistic title="成员总数" value={memberStats.summary?.member_count || members.length} prefix={<TeamOutlined />} /></Col>
          <Col xs={12} md={6}><Statistic title="活跃成员" value={memberStats.summary?.active_member_count || 0} prefix={<FireOutlined />} /></Col>
          <Col xs={12} md={6}><Statistic title="购物联动" value={memberStats.summary?.shopping_items || 0} prefix={<ShoppingOutlined />} /></Col>
          <Col xs={12} md={6}><Statistic title="家务联动" value={memberStats.summary?.chore_items || 0} prefix={<CheckSquareOutlined />} /></Col>
        </Row>
      </Card>

      <Row gutter={[16, 16]}>
        {topMembers.map((item: any) => (
          <Col xs={24} md={12} lg={6} key={item.name}>
            <Card size="small">
              <Space direction="vertical" size={6} style={{ width: '100%' }}>
                <Space><strong>{item.name}</strong><Tag color="blue">{item.role}</Tag></Space>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>购物 {item.shopping?.added || 0}</span><span>家务 {item.chores?.assigned || 0}</span></div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>出行 {item.travel?.participations || 0}</span><span>任务 {item.tasks?.received || 0}</span></div>
              </Space>
            </Card>
          </Col>
        ))}
      </Row>

      <Card title="家庭成员管理" extra={<Button type="primary" icon={<UserAddOutlined />} onClick={() => setModalVisible(true)}>添加成员</Button>}>
        <Table dataSource={members} columns={columns as any} rowKey="name" loading={loading} pagination={{ pageSize: 10 }} />
      </Card>

      <Modal title="添加家庭成员" open={modalVisible} onCancel={() => setModalVisible(false)} footer={null} destroyOnHidden>
        <Form form={form} onFinish={handleAdd} layout="vertical" initialValues={{ interaction_style: 'peer', permission: 'member', side: 'core' }}>
          <Form.Item name="name" label="姓名" rules={[{ required: true, message: '请输入姓名' }]}><Input placeholder="例如：张三" /></Form.Item>
          <Form.Item name="role" label="角色" rules={[{ required: true, message: '请输入角色' }]}><Input placeholder="例如：父亲、母亲、孩子" /></Form.Item>
          <Form.Item name="age" label="年龄" rules={[{ required: true, message: '请输入年龄' }]}><InputNumber min={1} max={150} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="side" label="分组">
            <Select options={[{ label: '核心家庭', value: 'core' }, { label: '扩展家庭', value: 'extended' }, { label: '访客', value: 'guest' }]} />
          </Form.Item>
          <Form.Item name="interaction_style" label="交互风格">
            <Select options={[{ label: '平等', value: 'peer' }, { label: '对孩子', value: 'child' }, { label: '对长辈', value: 'elder' }, { label: '正式', value: 'formal' }]} />
          </Form.Item>
          <Form.Item name="permission" label="权限级别">
            <Select options={[{ label: '管理员', value: 'admin' }, { label: '成员', value: 'member' }, { label: '访客', value: 'guest' }, { label: '儿童', value: 'child' }]} />
          </Form.Item>
          <Form.Item><Button type="primary" htmlType="submit" block>添加</Button></Form.Item>
        </Form>
      </Modal>

      <Modal title="编辑家庭成员" open={editModalVisible} onCancel={() => { setEditModalVisible(false); setEditingMember(null) }} footer={null} destroyOnHidden>
        <Form form={editForm} onFinish={handleEditOk} layout="vertical">
          <Form.Item name="name" label="姓名"><Input disabled /></Form.Item>
          <Form.Item name="role" label="角色" rules={[{ required: true, message: '请输入角色' }]}><Input /></Form.Item>
          <Form.Item name="age" label="年龄" rules={[{ required: true, message: '请输入年龄' }]}><InputNumber min={1} max={150} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="side" label="分组">
            <Select options={[{ label: '核心家庭', value: 'core' }, { label: '扩展家庭', value: 'extended' }, { label: '访客', value: 'guest' }]} />
          </Form.Item>
          <Form.Item name="interaction_style" label="交互风格">
            <Select options={[{ label: '平等', value: 'peer' }, { label: '对孩子', value: 'child' }, { label: '对长辈', value: 'elder' }, { label: '正式', value: 'formal' }]} />
          </Form.Item>
          <Form.Item name="permission" label="权限级别">
            <Select options={[{ label: '管理员', value: 'admin' }, { label: '成员', value: 'member' }, { label: '访客', value: 'guest' }, { label: '儿童', value: 'child' }]} />
          </Form.Item>
          <Form.Item><Button type="primary" htmlType="submit" block>保存修改</Button></Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default MembersPage
