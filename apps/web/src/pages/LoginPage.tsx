import React, { useEffect, useMemo, useState } from 'react'
import { Card, Input, Button, Form, message, Tabs, Divider, Typography } from 'antd'
import { UserOutlined, HomeOutlined, LoginOutlined, PlusOutlined } from '@ant-design/icons'
import axios from 'axios'
import { useSearchParams } from 'react-router-dom'

const { Title, Text } = Typography
const { TabPane } = Tabs

interface LoginPageProps {
  onLoginSuccess?: (sessionInfo: any) => void
}

const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('login')
  const [searchParams] = useSearchParams()
  const inviteCode = searchParams.get('invite')
  const inviteFamilyId = searchParams.get('family_id') || ''
  const [joinForm] = Form.useForm()

  useEffect(() => {
    if (inviteCode) {
      setActiveTab('join')
      joinForm.setFieldsValue({ invite_code: inviteCode, family_id: inviteFamilyId })
    }
  }, [inviteCode, inviteFamilyId, joinForm])

  // 登录表单
  const handleLogin = async (values: any) => {
    setLoading(true)
    try {
      const response = await axios.post('/api/auth/login', {
        family_id: values.family_id,
        member_name: values.member_name
      })

      if (response.data.success) {
        message.success(`✅ 欢迎回来, ${values.member_name}!`)
        
        // 保存会话信息到 localStorage
        localStorage.setItem('session_id', response.data.session_id)
        localStorage.setItem('family_id', response.data.family_id)
        localStorage.setItem('member_name', response.data.member_name)
        localStorage.setItem('family_name', response.data.family_name)
        
        if (onLoginSuccess) {
          onLoginSuccess(response.data)
        }
      } else {
        message.error(response.data.message || '登录失败')
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '登录失败,请检查家庭号和姓名')
    } finally {
      setLoading(false)
    }
  }

  // 创建家庭表单
  const handleCreateFamily = async (values: any) => {
    setLoading(true)
    try {
      const response = await axios.post('/api/auth/create-family', {
        family_name: values.family_name,
        admin_name: values.admin_name
      })

      if (response.data.success) {
        message.success(response.data.message)
        
        // 自动登录
        const loginResponse = await axios.post('/api/auth/login', {
          family_id: response.data.family_id,
          member_name: values.admin_name
        })

        if (loginResponse.data.success) {
          localStorage.setItem('session_id', loginResponse.data.session_id)
          localStorage.setItem('family_id', loginResponse.data.family_id)
          localStorage.setItem('member_name', loginResponse.data.member_name)
          localStorage.setItem('family_name', loginResponse.data.family_name)
          
          if (onLoginSuccess) {
            onLoginSuccess(loginResponse.data)
          }
        }
      } else {
        message.error(response.data.message || '创建失败')
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '创建家庭失败')
    } finally {
      setLoading(false)
    }
  }

  // 加入家庭表单
  const handleJoinFamily = async (values: any) => {
    setLoading(true)
    try {
      const response = await axios.post('/api/auth/join-family', {
        family_id: values.family_id,
        member_name: values.member_name,
        invite_code: values.invite_code || inviteCode || undefined,
      })

      if (response.data.success) {
        message.success(response.data.message)
        
        // 自动登录
        const loginResponse = await axios.post('/api/auth/login', {
          family_id: values.family_id,
          member_name: values.member_name
        })

        if (loginResponse.data.success) {
          localStorage.setItem('session_id', loginResponse.data.session_id)
          localStorage.setItem('family_id', loginResponse.data.family_id)
          localStorage.setItem('member_name', loginResponse.data.member_name)
          localStorage.setItem('family_name', loginResponse.data.family_name)
          
          if (onLoginSuccess) {
            onLoginSuccess(loginResponse.data)
          }
        }
      } else {
        message.error(response.data.message || '加入失败')
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '加入家庭失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      padding: 16,
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      <Card
        style={{
          width: '100%',
          maxWidth: 450,
          boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
          borderRadius: 16,
          margin: '0 auto'
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Title level={2} style={{ margin: 0, fontSize: 24 }}>
            🏡 家庭智能管家
          </Title>
          <Text type="secondary">温馨陪伴每一天</Text>
        </div>

        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          {/* 登录 */}
          <TabPane 
            tab={
              <span>
                <LoginOutlined />
                登录
              </span>
            } 
            key="login"
          >
            <Form onFinish={handleLogin} layout="vertical">
              <Form.Item
                name="family_id"
                label="家庭号"
                rules={[{ required: true, message: '请输入家庭号' }]}
              >
                <Input 
                  prefix={<HomeOutlined />} 
                  placeholder="请输入6位家庭号"
                  maxLength={6}
                  size="large"
                />
              </Form.Item>

              <Form.Item
                name="member_name"
                label="成员姓名"
                rules={[{ required: true, message: '请输入姓名' }]}
              >
                <Input 
                  prefix={<UserOutlined />} 
                  placeholder="例如: 妈妈、爸爸"
                  size="large"
                />
              </Form.Item>

              <Form.Item>
                <Button 
                  type="primary" 
                  htmlType="submit" 
                  loading={loading}
                  block
                  size="large"
                >
                  登录
                </Button>
              </Form.Item>
            </Form>
          </TabPane>

          {/* 创建家庭 */}
          <TabPane 
            tab={
              <span>
                <PlusOutlined />
                创建家庭
              </span>
            } 
            key="create"
          >
            <Form onFinish={handleCreateFamily} layout="vertical">
              <Form.Item
                name="family_name"
                label="家庭名称"
                rules={[{ required: true, message: '请输入家庭名称' }]}
              >
                <Input 
                  prefix={<HomeOutlined />} 
                  placeholder="例如: 幸福小家"
                  size="large"
                />
              </Form.Item>

              <Form.Item
                name="admin_name"
                label="管理员姓名"
                rules={[{ required: true, message: '请输入管理员姓名' }]}
              >
                <Input 
                  prefix={<UserOutlined />} 
                  placeholder="例如: 我"
                  size="large"
                />
              </Form.Item>

              <Form.Item>
                <Button 
                  type="primary" 
                  htmlType="submit" 
                  loading={loading}
                  block
                  size="large"
                >
                  创建家庭
                </Button>
              </Form.Item>

              <Divider />
              
              <div style={{ textAlign: 'center', color: '#666' }}>
                <Text type="secondary">
                  创建后您将获得一个6位家庭号<br/>
                  分享给家人,他们就可以加入了
                </Text>
              </div>
            </Form>
          </TabPane>

          {/* 加入家庭 */}
          <TabPane 
            tab={
              <span>
                <LoginOutlined />
                加入家庭
              </span>
            } 
            key="join"
          >
            <Form form={joinForm} onFinish={handleJoinFamily} layout="vertical">
              <Form.Item
                name="family_id"
                label="家庭号"
                rules={[{ required: !inviteCode, message: '请输入家庭号' }]}
              >
                <Input 
                  prefix={<HomeOutlined />} 
                  placeholder="请输入家人分享的家庭号"
                  maxLength={6}
                  size="large"
                  disabled={!!inviteCode}
                />
              </Form.Item>

              <Form.Item
                name="invite_code"
                label="邀请码"
                rules={[{ required: !!inviteCode, message: '请输入邀请码' }]}
              >
                <Input
                  placeholder="扫码/链接加入时可自动带入"
                  size="large"
                  disabled={!!inviteCode}
                />
              </Form.Item>

              <Form.Item
                name="member_name"
                label="您的姓名"
                rules={[{ required: true, message: '请输入您的姓名' }]}
              >
                <Input 
                  prefix={<UserOutlined />} 
                  placeholder="例如: 妈妈、爸爸"
                  size="large"
                />
              </Form.Item>

              <Form.Item>
                <Button 
                  type="primary" 
                  htmlType="submit" 
                  loading={loading}
                  block
                  size="large"
                >
                  加入家庭
                </Button>
              </Form.Item>

              <Divider />
              
              <div style={{ textAlign: 'center', color: '#666' }}>
                <Text type="secondary">
                  需要家人先创建家庭并分享家庭号给您
                </Text>
              </div>
            </Form>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  )
}

export default LoginPage
