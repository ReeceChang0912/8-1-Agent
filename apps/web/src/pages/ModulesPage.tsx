import React, { useEffect, useMemo, useState } from 'react'
import { Card, Col, Row, Tag, Typography, Space, Button, Empty, Statistic, message, Input, Segmented } from 'antd'
import { AppstoreOutlined, CheckCircleOutlined, ClockCircleOutlined, ArrowRightOutlined, WalletOutlined, HeartOutlined, CarOutlined, SafetyCertificateOutlined, CalendarOutlined, HomeOutlined } from '@ant-design/icons'
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
  housing: <HomeOutlined />,
  documents: <SafetyCertificateOutlined />,
  schedule: <CalendarOutlined />,
  chores: <AppstoreOutlined />,
  shopping: <WalletOutlined />,
  health: <HeartOutlined />,
  travel: <CalendarOutlined />,
}

const ModulesPage: React.FC = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [modules, setModules] = useState<any[]>([])
  const [stats, setStats] = useState({ ready_count: 0, planned_count: 0 })
  const [keyword, setKeyword] = useState('')
  const [category, setCategory] = useState<'all' | 'core' | 'life'>('all')

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
    const order = ['finance', 'wedding', 'housing', 'health', 'travel', 'chores', 'insurance', 'documents', 'vehicle', 'fitness']
    return order.map(id => modules.find(item => item.id === id)).filter(Boolean)
  }, [modules])

  const roadmap = useMemo(() => modules.filter(item => item.status !== 'ready'), [modules])

  const filteredModules = useMemo(() => {
    const q = keyword.trim().toLowerCase()
    return modules.filter((module) => {
      const matchesCategory = category === 'all' || module.category === category
      const matchesKeyword = !q || `${module.title || ''} ${module.description || ''} ${module.owner || ''}`.toLowerCase().includes(q)
      return matchesCategory && matchesKeyword
    })
  }, [category, keyword, modules])

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
              这里是整套家庭管理系统的入口。财务已经在跑，备婚、住房、健康、旅行、家务、保险、车辆、健身也已经进入可用状态，后面还可以继续往同一平台里加更多模块。
            </Paragraph>
          </Col>
          <Col xs={12} md={6} lg={3}><Statistic title="已上线" value={stats.ready_count} /></Col>
          <Col xs={12} md={6} lg={3}><Statistic title="规划中" value={stats.planned_count} /></Col>
          <Col xs={12} md={6} lg={3}><Statistic title="生活模块" value={modules.filter(item => item.category === 'life').length} /></Col>
          <Col xs={12} md={6} lg={3}><Statistic title="核心模块" value={modules.filter(item => item.category === 'core').length} /></Col>
        </Row>
      </Card>

      <Card style={{ marginBottom: 16, borderRadius: 8 }}>
        <Space direction="vertical" size={12} style={{ width: '100%' }}>
          <Space wrap style={{ width: '100%', justifyContent: 'space-between' }}>
            <Input.Search
              allowClear
              placeholder="搜索模块"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              style={{ maxWidth: 320 }}
            />
            <Segmented
              value={category}
              onChange={(value) => setCategory(value as typeof category)}
              options={[
                { label: '全部', value: 'all' },
                { label: '核心', value: 'core' },
                { label: '生活', value: 'life' },
              ]}
            />
          </Space>
          <Space wrap>
            <Button size="small" onClick={() => navigate('/finance')}>财务</Button>
            <Button size="small" onClick={() => navigate('/modules/wedding')}>备婚</Button>
            <Button size="small" onClick={() => navigate('/modules/housing')}>住房</Button>
            <Button size="small" onClick={() => navigate('/modules/health')}>健康</Button>
            <Button size="small" onClick={() => navigate('/modules/travel')}>旅行</Button>
            <Button size="small" onClick={() => navigate('/modules/chores')}>家务</Button>
            <Button size="small" onClick={() => navigate('/modules/insurance')}>保险</Button>
            <Button size="small" onClick={() => navigate('/modules/documents')}>证件</Button>
            <Button size="small" onClick={() => navigate('/modules/vehicle')}>车辆</Button>
            <Button size="small" onClick={() => navigate('/modules/fitness')}>健身</Button>
          </Space>
        </Space>
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

      <Card style={{ marginBottom: 16, borderRadius: 8 }} bodyStyle={{ paddingBottom: 8 }}>
        <Title level={4} style={{ marginTop: 0 }}>家庭管理路线图</Title>
        <Paragraph style={{ marginTop: 0, marginBottom: 16, maxWidth: 880 }}>
          先把你真正会长期用的东西铺出来。已上线的是主干，下面这些是下一步很自然会长出来的家庭管理能力。
        </Paragraph>
        <Row gutter={[16, 16]}>
          {roadmap.map((module: any) => {
            const meta = statusMeta[module.status] || statusMeta.planned
            return (
              <Col xs={24} md={12} xl={8} key={module.id}>
                <Card size="small" style={{ borderRadius: 8, height: '100%' }}>
                  <Space align="start" style={{ marginBottom: 12 }}>
                    <div style={{ width: 36, height: 36, borderRadius: 10, background: '#f5f7fb', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      {iconMap[module.id] || <AppstoreOutlined />}
                    </div>
                    <div>
                      <Space wrap>
                        <Text strong>{module.title}</Text>
                        <Tag color={meta.color} icon={meta.icon}>{meta.label}</Tag>
                      </Space>
                      <div style={{ marginTop: 4, color: '#667085' }}>{module.description}</div>
                    </div>
                  </Space>
                  <Space wrap>
                    <Tag>{module.category}</Tag>
                    <Tag>Owner: {module.owner}</Tag>
                    {module.web_route ? <Tag color="blue">Web 可直达</Tag> : <Tag>待规划页面</Tag>}
                  </Space>
                </Card>
              </Col>
            )
          })}
        </Row>
      </Card>

      <Row gutter={[16, 16]}>
        {filteredModules.map(module => {
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
        {!loading && filteredModules.length === 0 && (
          <Col span={24}>
            <Empty description={keyword || category !== 'all' ? '没有匹配的模块' : '暂无模块'} />
          </Col>
        )}
      </Row>
    </div>
  )
}

export default ModulesPage
