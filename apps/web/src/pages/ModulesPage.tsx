import React, { useEffect, useMemo, useState } from 'react'
import { Card, Col, Row, Tag, Typography, Space, Button, Empty, Statistic, message } from 'antd'
import { AppstoreOutlined, CheckCircleOutlined, ClockCircleOutlined, ArrowRightOutlined, WalletOutlined, HeartOutlined, CarOutlined, SafetyCertificateOutlined, CalendarOutlined } from '@ant-design/icons'
import { modulesAPI } from '../services/api'
import { useNavigate } from 'react-router-dom'

const { Title, Paragraph, Text } = Typography

const statusMeta: Record<string, { color: string; label: string; icon: React.ReactNode }> = {
  ready: { color: 'green', label: '已上线', icon: <CheckCircleOutlined /> },
  planned: { color: 'gold', label: '规划中', icon: <ClockCircleOutlined /> },
}

const iconMap: Record<string, React.ReactNode> = {
  finance: <WalletOutlined />,
  wedding: <CalendarOutlined />,
  insurance: <SafetyCertificateOutlined />,
  vehicle: <CarOutlined />,
  fitness: <HeartOutlined />,
}

const ModulesPage: React.FC = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [modules, setModules] = useState<any[]>([])
  const [stats, setStats] = useState({ ready_count: 0, planned_count: 0 })

  useEffect(() => {
    load()
  }, [])

  const load = async () => {
    setLoading(true)
    try {
      const res = await modulesAPI.list()
      setModules(res.data.items || [])
      setStats({
        ready_count: res.data.ready_count || 0,
        planned_count: res.data.planned_count || 0,
      })
    } finally {
      setLoading(false)
    }
  }

  const recommended = useMemo(() => {
    const order = ['finance', 'wedding', 'insurance', 'vehicle', 'fitness']
    return order.map(id => modules.find(item => item.id === id)).filter(Boolean)
  }, [modules])

  const openModule = (module: any) => {
    if (module.web_route) {
      navigate(module.web_route)
    } else {
      message.info('这个模块暂时没有页面入口')
    }
  }

  return (
    <div style={{ padding: 0 }}>
      <Card style={{ marginBottom: 16, borderRadius: 8 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} lg={12}>
            <Space>
              <AppstoreOutlined style={{ color: '#1677ff', fontSize: 22 }} />
              <Title level={3} style={{ margin: 0 }}>家庭模块中心</Title>
            </Space>
            <Paragraph style={{ marginTop: 8, marginBottom: 0, maxWidth: 760 }}>
              这里是整套家庭管理系统的入口。财务已经在跑，备婚、保险、车辆、健身也已经进入可用状态，后面还可以继续往同一平台里加更多模块。
            </Paragraph>
          </Col>
          <Col xs={12} md={6} lg={3}><Statistic title="已上线" value={stats.ready_count} /></Col>
          <Col xs={12} md={6} lg={3}><Statistic title="规划中" value={stats.planned_count} /></Col>
          <Col xs={12} md={6} lg={3}><Statistic title="生活模块" value={modules.filter(item => item.category === 'life').length} /></Col>
          <Col xs={12} md={6} lg={3}><Statistic title="核心模块" value={modules.filter(item => item.category === 'core').length} /></Col>
        </Row>
      </Card>

      <Card style={{ marginBottom: 16, borderRadius: 8 }} bodyStyle={{ paddingBottom: 8 }}>
        <Title level={4} style={{ marginTop: 0 }}>推荐先用</Title>
        <Row gutter={[16, 16]}>
          {recommended.map((module: any) => {
            const meta = statusMeta[module.status] || statusMeta.planned
            return (
              <Col xs={24} md={12} xl={8} key={module.id}>
                <Card hoverable style={{ borderRadius: 8, height: '100%' }} bodyStyle={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                  <Space align="start" style={{ marginBottom: 12 }}>
                    <div style={{ width: 42, height: 42, borderRadius: 12, background: '#f3f6fb', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, color: '#1677ff' }}>
                      {iconMap[module.id] || <AppstoreOutlined />}
                    </div>
                    <div>
                      <Title level={5} style={{ margin: 0 }}>{module.title}</Title>
                      <Space style={{ marginTop: 6 }}>
                        <Tag color={meta.color} icon={meta.icon}>{meta.label}</Tag>
                        <Tag>{module.category}</Tag>
                      </Space>
                    </div>
                  </Space>
                  <Paragraph style={{ color: '#4b5563', flex: 1, marginBottom: 12 }}>{module.description}</Paragraph>
                  <Button type="primary" icon={<ArrowRightOutlined />} onClick={() => openModule(module)}>
                    进入模块
                  </Button>
                </Card>
              </Col>
            )
          })}
        </Row>
      </Card>

      <Row gutter={[16, 16]}>
        {modules.map(module => {
          const meta = statusMeta[module.status] || statusMeta.planned
          return (
            <Col xs={24} md={12} xl={8} key={module.id}>
              <Card hoverable style={{ height: '100%', borderRadius: 8 }} bodyStyle={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                <Space align="start" style={{ marginBottom: 12 }}>
                  <div style={{ width: 40, height: 40, borderRadius: 12, background: '#f5f7fb', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, color: '#1677ff' }}>
                    {iconMap[module.id] || <AppstoreOutlined />}
                  </div>
                  <div>
                    <Title level={4} style={{ margin: 0 }}>{module.title}</Title>
                    <Space style={{ marginTop: 8 }}>
                      <Tag color={meta.color} icon={meta.icon}>{meta.label}</Tag>
                      <Tag>{module.category}</Tag>
                    </Space>
                  </div>
                </Space>
                <Paragraph style={{ color: '#4b5563', flex: 1 }}>{module.description}</Paragraph>
                <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                  <Text type="secondary">Owner: {module.owner}</Text>
                  <Button type="link" icon={<ArrowRightOutlined />} onClick={() => openModule(module)}>
                    {module.status === 'ready' ? '打开' : '查看规划'}
                  </Button>
                </Space>
              </Card>
            </Col>
          )
        })}
        {!loading && modules.length === 0 && (
          <Col span={24}>
            <Empty description="暂无模块" />
          </Col>
        )}
      </Row>
    </div>
  )
}

export default ModulesPage
