import React, { useState, useEffect } from 'react'
import { Layout, Menu, theme, Avatar, Dropdown, message, Badge, Drawer, Button } from 'antd'
import { MenuOutlined } from '@ant-design/icons'
import {
  MessageOutlined,
  TeamOutlined,
  CalendarOutlined,
  ShoppingCartOutlined,
  PictureOutlined,
  HomeOutlined,
  ApiOutlined,
  BarChartOutlined,
  BookOutlined,
  ThunderboltOutlined,
  UserOutlined,
  LogoutOutlined,
  BellOutlined,
  AppstoreOutlined,
  WalletOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'
import WorkbenchPage from './pages/WorkbenchPage'
import ChatPage from './pages/ChatPage'
import MembersPage from './pages/MembersPage'
import SchedulePage from './pages/SchedulePage'
import ShoppingPage from './pages/ShoppingPage'
import PhotosPage from './pages/PhotosPage'
import SmartHomePage from './pages/SmartHomePage'
import KnowledgePage from './pages/KnowledgePage'
import SkillsPage from './pages/SkillsPage'
import MCPPage from './pages/MCPPage'
import StatsPage from './pages/StatsPage'
import NotificationsPage from './pages/NotificationsPage'
import FinancePage from './pages/FinancePage'
import LoginPage from './pages/LoginPage'
import axios from 'axios'

const { Header, Sider, Content } = Layout

const PAGE_ROUTES: Record<string, string> = {
  myWorkbench: '/',
  chat: '/chat',
  members: '/members',
  schedule: '/schedule',
  shopping: '/shopping',
  photos: '/photos',
  knowledge: '/knowledge',
  skills: '/skills',
  smarthome: '/smarthome',
  mcp: '/mcp',
  stats: '/stats',
  notifications: '/notifications',
  finance: '/finance',
}

const ROUTE_TO_KEY: Record<string, string> = {}
for (const [key, path] of Object.entries(PAGE_ROUTES)) {
  ROUTE_TO_KEY[path] = key
}

const App: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const selectedKey = ROUTE_TO_KEY[location.pathname] || 'myWorkbench'
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [userInfo, setUserInfo] = useState<any>(null)
  const [unreadCount, setUnreadCount] = useState(0)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const {
    token: { colorBgContainer },
  } = theme.useToken()

  // 检查登录状态
  useEffect(() => {
    checkLoginStatus()
  }, [])

  // 获取未读通知数量
  useEffect(() => {
    if (isLoggedIn && userInfo?.member_name) {
      const fetchUnreadCount = async () => {
        try {
          const response = await axios.get(`/api/notifications/unread-count/${userInfo.member_name}`)
          if (response.data.success) {
            setUnreadCount(response.data.unread_count)
          }
        } catch (error) {
          console.error('获取未读通知失败:', error)
        }
      }
      
      fetchUnreadCount()
      const interval = setInterval(fetchUnreadCount, 30000) // 每30秒刷新
      return () => clearInterval(interval)
    }
  }, [isLoggedIn, userInfo])

  const checkLoginStatus = async () => {
    const sessionId = localStorage.getItem('session_id')
    if (sessionId) {
      try {
        const response = await axios.get('/api/auth/verify', {
          params: { session_id: sessionId }
        })
        
        if (response.data.valid) {
          setIsLoggedIn(true)
          setUserInfo(response.data)
        } else {
          // 会话无效，清除本地存储
          localStorage.clear()
          setIsLoggedIn(false)
        }
      } catch (error) {
        console.error('验证会话失败')
        localStorage.clear()
        setIsLoggedIn(false)
      }
    }
  }

  const handleLoginSuccess = (sessionInfo: any) => {
    setIsLoggedIn(true)
    setUserInfo(sessionInfo)
    message.success(`欢迎加入 ${sessionInfo.family_name}!`)
  }

  const handleLogout = async () => {
    const sessionId = localStorage.getItem('session_id')
    if (sessionId) {
      try {
        await axios.post('/api/auth/logout', null, {
          params: { session_id: sessionId }
        })
      } catch (error) {
        console.error('登出失败')
      }
    }
    
    localStorage.clear()
    setIsLoggedIn(false)
    setUserInfo(null)
    message.success('已退出登录')
  }

  const menuItems = [
    { key: 'myWorkbench', icon: <AppstoreOutlined />, label: '我的工作台' },
    { key: 'chat', icon: <MessageOutlined />, label: '智能对话' },
    { key: 'members', icon: <TeamOutlined />, label: '家庭成员' },
    { key: 'schedule', icon: <CalendarOutlined />, label: '日程管理' },
    { key: 'shopping', icon: <ShoppingCartOutlined />, label: '购物清单' },
    { key: 'photos', icon: <PictureOutlined />, label: '照片记忆' },
    { key: 'knowledge', icon: <BookOutlined />, label: '知识库' },
    { key: 'skills', icon: <ThunderboltOutlined />, label: '技能中心' },
    { key: 'smarthome', icon: <HomeOutlined />, label: '智能家居' },
    { key: 'mcp', icon: <ApiOutlined />, label: 'MCP协议' },
    { key: 'finance', icon: <WalletOutlined />, label: '家庭财务' },
    { key: 'stats', icon: <BarChartOutlined />, label: '统计信息' },
    { 
      key: 'notifications', 
      icon: (
        <Badge count={unreadCount} offset={[5, -5]}>
          <BellOutlined />
        </Badge>
      ), 
      label: '消息通知' 
    },
  ]

  const renderContent = () => {
    switch (selectedKey) {
      case 'myWorkbench':
        return <WorkbenchPage />
      case 'chat':
        return <ChatPage />
      case 'members':
        return <MembersPage />
      case 'schedule':
        return <SchedulePage />
      case 'shopping':
        return <ShoppingPage />
      case 'photos':
        return <PhotosPage />
      case 'knowledge':
        return <KnowledgePage />
      case 'skills':
        return <SkillsPage />
      case 'smarthome':
        return <SmartHomePage />
      case 'mcp':
        return <MCPPage />
      case 'stats':
        return <StatsPage />
      case 'finance':
        return <FinancePage />
      case 'notifications':
        return <NotificationsPage />
      default:
        return <ChatPage />
    }
  }

  // 如果未登录，显示登录页面
  if (!isLoggedIn) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />
  }

  const logoutMenuItems = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout
    }
  ]

  return (
    <Layout style={{ height: '100vh', overflow: 'hidden' }}>
      <Sider width={200} theme="dark" breakpoint="lg" collapsedWidth={0}
        style={{ height: '100vh', position: 'sticky', top: 0, left: 0, overflow: 'hidden' }}>
        <div style={{
          height: 64,
          margin: 16,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontSize: 18,
          fontWeight: 'bold',
          flexShrink: 0
        }}>
          🏡 家庭管家
        </div>
        <div style={{ overflowY: 'auto', maxHeight: 'calc(100vh - 96px)', scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
        <style>{`
          .ant-layout-sider::-webkit-scrollbar { display: none; }
          .mobile-menu-btn { display: none !important; }
          @media (max-width: 992px) {
            .mobile-menu-btn { display: inline-flex !important; }
            .ant-layout-sider { display: none !important; }
            .ant-layout-header { padding: 0 12px !important; }
            .ant-layout-content { margin: 12px 8px !important; padding: 12px !important; }
          }
        `}</style>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => {
            const path = PAGE_ROUTES[key] || '/'
            navigate(path)
          }}
        />
        </div>
      </Sider>
      <Layout style={{ height: '100vh', overflow: 'hidden' }}>
        <Header style={{
          padding: '0 24px',
          background: colorBgContainer,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Button className="mobile-menu-btn" type="text" icon={<MenuOutlined />}
              onClick={() => setMobileMenuOpen(true)} style={{ fontSize: 18 }} />
            <div style={{ fontSize: 20, fontWeight: 'bold' }}>
              {menuItems.find(item => item.key === selectedKey)?.label}
            </div>
          </div>
          
          {/* 用户信息 */}
          <Dropdown 
            menu={{ items: logoutMenuItems }} 
            placement="bottomRight"
            dropdownRender={(menu) => (
              <div>
                {/* 用户信息头部 */}
                <div style={{ 
                  padding: '16px 20px', 
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  borderRadius: '12px 12px 0 0',
                  color: 'white'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                    <Avatar 
                      size={48} 
                      icon={<UserOutlined />} 
                      style={{ 
                        backgroundColor: 'rgba(255,255,255,0.2)',
                        border: '2px solid rgba(255,255,255,0.4)',
                        fontSize: 20,
                        backdropFilter: 'blur(10px)'
                      }} 
                    />
                    <div>
                      <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 2 }}>
                        {userInfo?.member_name}
                      </div>
                      <div style={{ fontSize: 13, opacity: 0.9 }}>
                        {userInfo?.family_name}
                      </div>
                    </div>
                  </div>
                  <div style={{ 
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 8,
                    background: 'rgba(255,255,255,0.15)',
                    padding: '6px 12px',
                    borderRadius: 8,
                    fontSize: 13,
                    backdropFilter: 'blur(10px)'
                  }}>
                    <span style={{ opacity: 0.9 }}>家庭号:</span>
                    <span style={{ 
                      fontFamily: 'monospace', 
                      fontWeight: 700, 
                      fontSize: 15,
                      letterSpacing: 2,
                      background: 'rgba(255,255,255,0.2)',
                      padding: '2px 8px',
                      borderRadius: 4
                    }}>
                      {userInfo?.family_id}
                    </span>
                  </div>
                </div>
                {/* 菜单内容 */}
                {menu}
              </div>
            )}
          >
            <div 
              style={{ 
                cursor: 'pointer', 
                padding: '8px 16px', 
                borderRadius: 12,
                transition: 'all 0.3s',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                boxShadow: '0 4px 12px rgba(102, 126, 234, 0.3)',
                border: 'none'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)'
                e.currentTarget.style.boxShadow = '0 6px 16px rgba(102, 126, 234, 0.4)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)'
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.3)'
              }}
            >
              <Avatar 
                size={36} 
                icon={<UserOutlined />} 
                style={{ 
                  backgroundColor: 'rgba(255,255,255,0.2)',
                  border: '2px solid rgba(255,255,255,0.4)',
                  backdropFilter: 'blur(10px)'
                }} 
              />
              <div style={{ lineHeight: 1.2, color: 'white' }}>
                <div style={{ fontSize: 14, fontWeight: 600 }}>
                  {userInfo?.member_name}
                </div>
                <div style={{ fontSize: 12, opacity: 0.9 }}>
                  {userInfo?.family_name}
                </div>
              </div>
            </div>
          </Dropdown>
        </Header>
        <Content style={{ margin: '24px 16px', padding: 24, background: colorBgContainer, overflow: 'auto', height: 'calc(100vh - 64px)' }}>
          {renderContent()}
        </Content>
      </Layout>
      <Drawer title="🏡 家庭管家" placement="left" width={240}
        open={mobileMenuOpen} onClose={() => setMobileMenuOpen(false)}
        styles={{ body: { padding: 0 } }}>
        <Menu
          theme="light"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => {
            const path = PAGE_ROUTES[key] || '/'
            navigate(path)
            setMobileMenuOpen(false)
          }}
        />
      </Drawer>
    </Layout>
  )
}

export default App
