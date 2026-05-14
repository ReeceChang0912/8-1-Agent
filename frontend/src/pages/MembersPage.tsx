import React, { useState, useEffect } from 'react'
import { Card, Table, Button, Form, Input, InputNumber, Select, Modal, message, Popconfirm, Alert, Space } from 'antd'
import { PlusOutlined, DeleteOutlined, EditOutlined, UserAddOutlined, HomeOutlined, CopyOutlined } from '@ant-design/icons'
import { membersAPI } from '../services/api'
import axios from 'axios'

const MembersPage: React.FC = () => {
  const [members, setMembers] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [editingMember, setEditingMember] = useState<any>(null)
  const [familyInfo, setFamilyInfo] = useState<any>(null)
  const [form] = Form.useForm()
  const [editForm] = Form.useForm()

  useEffect(() => {
    loadMembers()
    loadFamilyInfo()
  }, [])

  const loadMembers = async () => {
    setLoading(true)
    try {
      const res = await membersAPI.getAll()
      setMembers(res.data.members)
    } catch (error) {
      message.error('加载成员失败')
    } finally {
      setLoading(false)
    }
  }

  const loadFamilyInfo = async () => {
    const familyId = localStorage.getItem('family_id')
    if (familyId) {
      try {
        const res = await axios.get('/api/auth/family-members', {
          params: { family_id: familyId }
        })
        const familyName = localStorage.getItem('family_name')
        setFamilyInfo({
          family_id: familyId,
          family_name: familyName,
          members: res.data.members || []
        })
      } catch (error) {
        console.error('加载家庭信息失败')
      }
    }
  }

  const copyFamilyId = () => {
    if (familyInfo?.family_id) {
      navigator.clipboard.writeText(familyInfo.family_id)
      message.success('✅ 家庭号已复制到剪贴板')
    }
  }

  const handleAdd = async (values: any) => {
    try {
      await membersAPI.add(values)
      message.success('成员添加成功')
      setModalVisible(false)
      form.resetFields()
      loadMembers()
    } catch (error) {
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
      await axios.put(`/api/members/${editingMember.name}`, values)
      message.success('成员已更新')
      setEditModalVisible(false)
      setEditingMember(null)
      loadMembers()
    } catch (error) {
      message.error('更新失败')
    }
  }

  const handleDelete = async (name: string) => {
    try {
      await membersAPI.remove(name)
      message.success('成员已删除')
      loadMembers()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const columns = [
    {
      title: '姓名',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
    },
    {
      title: '年龄',
      dataIndex: 'age',
      key: 'age',
    },
    {
      title: '交互风格',
      dataIndex: 'interaction_style',
      key: 'interaction_style',
    },
    {
      title: '权限',
      dataIndex: 'permission',
      key: 'permission',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space>
          <Button icon={<EditOutlined />} size="small" onClick={() => handleEditClick(record)}>
            编辑
          </Button>
          <Popconfirm
            title="确定删除该成员？"
            onConfirm={() => handleDelete(record.name)}
            okText="确定"
            cancelText="取消"
          >
            <Button danger icon={<DeleteOutlined />} size="small">
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      {/* 家庭号显示 */}
      {familyInfo && (
        <Alert
          className="family-info-alert"
          message={
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
              <span>
                <HomeOutlined style={{ marginRight: 8 }} />
                <strong>{familyInfo.family_name}</strong> | 家庭号: <strong style={{ fontSize: 18, color: '#1890ff' }}>{familyInfo.family_id}</strong>
              </span>
              <Button
                size="small"
                icon={<CopyOutlined />}
                onClick={copyFamilyId}
              >
                复制家庭号
              </Button>
            </div>
          }
          type="info"
          showIcon={false}
          style={{ marginBottom: 16 }}
        />
      )}

      <Card
        title="家庭成员管理"
        extra={
          <Button
            type="primary"
            icon={<UserAddOutlined />}
            onClick={() => setModalVisible(true)}
          >
            添加成员
          </Button>
        }
      >
        <Table
          dataSource={members}
          columns={columns}
          rowKey="name"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title="添加家庭成员"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
      >
        <Form form={form} onFinish={handleAdd} layout="vertical">
          <Form.Item
            name="name"
            label="姓名"
            rules={[{ required: true, message: '请输入姓名' }]}
          >
            <Input placeholder="例如：张三" />
          </Form.Item>

          <Form.Item
            name="role"
            label="角色"
            rules={[{ required: true, message: '请输入角色' }]}
          >
            <Input placeholder="例如：父亲、母亲、孩子" />
          </Form.Item>

          <Form.Item
            name="age"
            label="年龄"
            rules={[{ required: true, message: '请输入年龄' }]}
          >
            <InputNumber min={1} max={150} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="interaction_style"
            label="交互风格"
            initialValue="peer"
          >
            <Select>
              <Select.Option value="peer">平等</Select.Option>
              <Select.Option value="child">对孩子</Select.Option>
              <Select.Option value="elder">对长辈</Select.Option>
              <Select.Option value="formal">正式</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="permission"
            label="权限级别"
            initialValue="member"
          >
            <Select>
              <Select.Option value="admin">管理员</Select.Option>
              <Select.Option value="member">成员</Select.Option>
              <Select.Option value="guest">访客</Select.Option>
              <Select.Option value="child">儿童</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              添加
            </Button>
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑成员弹窗 */}
      <Modal
        title="编辑家庭成员"
        open={editModalVisible}
        onCancel={() => { setEditModalVisible(false); setEditingMember(null) }}
        footer={null}
      >
        <Form form={editForm} onFinish={handleEditOk} layout="vertical" initialValues={editingMember}>
          <Form.Item name="name" label="姓名">
            <Input disabled />
          </Form.Item>
          <Form.Item name="role" label="角色" rules={[{ required: true, message: '请输入角色' }]}>
            <Input placeholder="例如：父亲、母亲、孩子" />
          </Form.Item>
          <Form.Item name="age" label="年龄" rules={[{ required: true, message: '请输入年龄' }]}>
            <InputNumber min={1} max={150} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="interaction_style" label="交互风格">
            <Select>
              <Select.Option value="peer">平等</Select.Option>
              <Select.Option value="child">对孩子</Select.Option>
              <Select.Option value="elder">对长辈</Select.Option>
              <Select.Option value="formal">正式</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="permission" label="权限级别">
            <Select>
              <Select.Option value="admin">管理员</Select.Option>
              <Select.Option value="member">成员</Select.Option>
              <Select.Option value="guest">访客</Select.Option>
              <Select.Option value="child">儿童</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              保存修改
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default MembersPage
