import React, { useState, useEffect } from 'react'
import { Button, Card, Row, Col, Spin, Typography, Tag, List, Space, Statistic, Divider, Empty, Alert } from 'antd'
import {
  EnvironmentOutlined,
  ThunderboltOutlined,
  RiseOutlined,
  CalendarOutlined,
  GiftOutlined,
  BulbOutlined,
  SoundOutlined,
  GlobalOutlined,
  SafetyOutlined,
} from '@ant-design/icons'
import axios from 'axios'
import dayjs from 'dayjs'
import TaskNotification from '../components/TaskNotification'
import { membersAPI } from '../services/api'

const { Title, Text, Paragraph } = Typography

interface WeatherData {
  current: { temp: string; humidity: string; wind: string; desc: string; icon: string }
  forecast: Array<{ date: string; temp_high: string; temp_low: string; desc: string; icon: string }>
}

interface NewsItem {
  title: string
  url: string
  summary: string
  source?: string
  time: string
}

interface BriefingData {
  date: string
  weekday: string
  greeting: string
  headlines: Array<{ title: string; source: string }>
  market_snapshots: Array<{ title: string; source: string }>
  inspiration: { quote: string; author: string }
}

interface HolidayItem {
  name: string
  date: string
  days_until: number
  duration: number
  type: string
}

const WorkbenchPage: React.FC = () => {
  const [initialLoading, setInitialLoading] = useState(true)
  const [weather, setWeather] = useState<WeatherData | null>(null)
  const [aiNews, setAiNews] = useState<NewsItem[]>([])
  const [internetNews, setInternetNews] = useState<NewsItem[]>([])
  const [investmentNews, setInvestmentNews] = useState<NewsItem[]>([])
  const [briefing, setBriefing] = useState<BriefingData | null>(null)
  const [holidays, setHolidays] = useState<HolidayItem[]>([])
  const [memberDigest, setMemberDigest] = useState<any>({ summary: {}, members: [] })
  const [showOnboarding] = useState(() => !localStorage.getItem('family_onboarding_dismissed'))

  useEffect(() => {
    fetchAll()
    const timer = setInterval(fetchAll, 60000)
    return () => clearInterval(timer)
  }, [])

  const fetchAll = async () => {
    // 逐个发起请求，每个接口独立更新状态
    // 先加载完成的区块先显示，不再互相等待
    const fetchWeather = axios.get('/api/workbench/weather', { params: { city: '昆明' } })
      .then(res => setWeather(res.data.data))
      .catch(() => {})

    const fetchAiNews = axios.get('/api/workbench/news', { params: { category: 'ai', limit: 6 } })
      .then(res => setAiNews(res.data.items))
      .catch(() => {})

    const fetchInternetNews = axios.get('/api/workbench/news', { params: { category: 'internet', limit: 6 } })
      .then(res => setInternetNews(res.data.items))
      .catch(() => {})

    const fetchInvestNews = axios.get('/api/workbench/news', { params: { category: 'investment', limit: 5 } })
      .then(res => setInvestmentNews(res.data.items))
      .catch(() => {})

    const fetchBriefing = axios.get('/api/workbench/briefing')
      .then(res => setBriefing(res.data.data))
      .catch(() => {})

    const fetchHolidays = axios.get('/api/workbench/holidays')
      .then(res => setHolidays(res.data.items))
      .catch(() => {})

    membersAPI.getStats(localStorage.getItem('family_id') || '')
      .then(res => setMemberDigest(res.data || { summary: {}, members: [] }))
      .catch(() => {})

    // 等全部完成才移除初始加载状态
    await Promise.allSettled([fetchWeather, fetchAiNews, fetchInternetNews, fetchInvestNews, fetchBriefing, fetchHolidays])
    setInitialLoading(false)
  }

  const dismissOnboarding = () => {
    localStorage.setItem('family_onboarding_dismissed', '1')
    window.location.reload()
  }

  // 首次加载显示骨架屏
  if (initialLoading && !weather && aiNews.length === 0) {
    return (
      <div style={{ padding: 0 }}>
        <TaskNotification memberName={localStorage.getItem('member_name') || ''} />
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={12}>
            <Card style={{ borderRadius: 12 }}>
              <Spin>
                <div style={{ height: 180 }} />
              </Spin>
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card style={{ borderRadius: 12 }}>
              <Spin>
                <div style={{ height: 180 }} />
              </Spin>
            </Card>
          </Col>
        </Row>
      </div>
    )
  }

  const WeatherIcon = ({ code }: { code: string }) => {
    const iconMap: Record<string, string> = {
      '113': '☀️', '116': '⛅', '119': '☁️', '122': '☁️',
      '143': '🌫️', '176': '🌦️', '179': '🌨️', '182': '🌧️',
      '185': '🌧️', '200': '⛈️', '227': '🌨️', '230': '🌨️',
      '248': '🌫️', '260': '🌫️', '263': '🌦️', '266': '🌦️',
      '281': '🌧️', '284': '🌧️', '293': '🌦️', '296': '🌦️',
      '299': '🌧️', '302': '🌧️', '305': '🌧️', '308': '🌧️',
      '311': '🌧️', '314': '🌧️', '317': '🌧️', '320': '🌨️',
      '323': '🌨️', '326': '🌨️', '329': '🌨️', '332': '🌨️',
      '335': '🌨️', '338': '🌨️', '350': '🧊', '353': '🌦️',
      '356': '🌧️', '359': '🌧️', '362': '🌧️', '365': '🌧️',
      '368': '🌨️', '371': '🌨️', '374': '🌧️', '377': '🌧️',
      '386': '⛈️', '389': '⛈️', '392': '⛈️', '395': '🌨️',
    }
    return <span style={{ fontSize: 40 }}>{iconMap[code] || '☀️'}</span>
  }

  const renderNewsList = (items: NewsItem[], icon: React.ReactNode, color: string) => (
    <List
      dataSource={items}
      renderItem={(item, idx) => (
        <List.Item
          style={{ cursor: 'pointer', padding: '10px 0' }}
        >
          <a href={item.url && item.url !== '#' ? item.url : undefined} target="_blank" rel="noopener noreferrer" style={{ display: 'flex', width: '100%', textDecoration: 'none', color: 'inherit' }}>
          <List.Item.Meta
            avatar={
              <div style={{
                width: 24, height: 24, borderRadius: 12,
                background: color, color: '#fff',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 12, fontWeight: 'bold', flexShrink: 0, marginTop: 2
              }}>
                {idx + 1}
              </div>
            }
            title={
              <Text strong style={{ fontSize: 14 }}>{item.title}</Text>
            }
            description={
              <div>
                <Paragraph ellipsis={{ rows: 2 }} style={{ margin: 0, fontSize: 13, color: '#666' }}>
                  {item.summary}
                </Paragraph>
                <Space size={12} style={{ marginTop: 4 }}>
                  {item.source && <Text type="secondary" style={{ fontSize: 12 }}>{item.source}</Text>}
                  {item.time && (
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {dayjs(item.time).format('HH:mm')}
                    </Text>
                  )}
                </Space>
              </div>
            }
          />
          </a>
        </List.Item>
      )}
    />
  )

  return (
    <div style={{ padding: 0 }}>
      {showOnboarding && (
        <Card style={{ marginBottom: 20, borderRadius: 12, border: '1px solid #dbeafe', background: '#f8fbff' }}>
          <Row gutter={[16, 16]} align="middle">
            <Col xs={24} lg={12}>
              <Space direction="vertical" size={6}>
                <Text type="secondary">新手上手</Text>
                <Title level={4} style={{ margin: 0 }}>先把家里的人、事、钱接进来</Title>
                <Paragraph style={{ marginBottom: 0, color: '#475569' }}>
                  先建家庭或邀请家人，再把会话、购物、家务和财务一起串起来，系统才会真正开始帮你省心。
                </Paragraph>
              </Space>
            </Col>
            <Col xs={24} lg={12}>
              <Row gutter={12}>
                <Col xs={24} md={8}>
                  <Card size="small" style={{ borderRadius: 8, height: '100%' }}>
                    <Text strong>1. 建家庭</Text>
                    <div style={{ marginTop: 6, color: '#64748b' }}>创建家庭号，先把主账号立住。</div>
                  </Card>
                </Col>
                <Col xs={24} md={8}>
                  <Card size="small" style={{ borderRadius: 8, height: '100%' }}>
                    <Text strong>2. 拉家人</Text>
                    <div style={{ marginTop: 6, color: '#64748b' }}>生成邀请链接，直接分享给家里人。</div>
                  </Card>
                </Col>
                <Col xs={24} md={8}>
                  <Card size="small" style={{ borderRadius: 8, height: '100%' }}>
                    <Text strong>3. 先聊一件事</Text>
                    <div style={{ marginTop: 6, color: '#64748b' }}>从购物、家务、备婚、财务里挑一个开始。</div>
                  </Card>
                </Col>
              </Row>
              <Space style={{ marginTop: 12 }}>
                <Button type="primary" onClick={() => window.location.assign('/members')}>去邀请家人</Button>
                <Button onClick={dismissOnboarding}>我知道了</Button>
              </Space>
            </Col>
          </Row>
        </Card>
      )}

      {/* 我的任务 */}
      <TaskNotification memberName={localStorage.getItem('member_name') || ''} />
      <Card style={{ marginBottom: 20, borderRadius: 12 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} md={8}>
            <Space direction="vertical" size={4}>
              <Text type="secondary">家庭成员总览</Text>
              <Title level={4} style={{ margin: 0 }}>{memberDigest.summary?.member_count || 0} 人在协同</Title>
            </Space>
          </Col>
          <Col xs={12} md={4}><Statistic title="活跃成员" value={memberDigest.summary?.active_member_count || 0} /></Col>
          <Col xs={12} md={4}><Statistic title="购物联动" value={memberDigest.summary?.shopping_items || 0} /></Col>
          <Col xs={12} md={4}><Statistic title="家务联动" value={memberDigest.summary?.chore_items || 0} /></Col>
          <Col xs={24} md={4}>
            <Space direction="vertical" size={0}>
              <Text type="secondary">当前最活跃</Text>
              <Text strong>{memberDigest.summary?.top_member || '暂无'}</Text>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 八点一刻 - 每日简报 */}
      {briefing && (
        <Card
          style={{
            marginBottom: 20,
            borderRadius: 16,
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: '#fff',
            border: 'none',
          }}
          bodyStyle={{ padding: '28px 32px' }}
        >
          <Row align="middle" gutter={24}>
            <Col xs={24} md={14}>
              <Space direction="vertical" size={8}>
                <Space>
                  <SoundOutlined style={{ fontSize: 24 }} />
                  <Title level={3} style={{ color: '#fff', margin: 0 }}>八点一刻</Title>
                </Space>
                <Text style={{ color: 'rgba(255,255,255,0.9)', fontSize: 16 }}>
                  {briefing.greeting}
                </Text>
                <div style={{ marginTop: 8 }}>
                  <Text style={{ color: 'rgba(255,255,255,0.8)', fontWeight: 600, fontSize: 13 }}>
                    📰 今日要闻
                  </Text>
                  {briefing.headlines.map((h, i) => (
                    <div key={i} style={{ color: 'rgba(255,255,255,0.9)', fontSize: 13, marginTop: 4 }}>
                      · {h.title}
                    </div>
                  ))}
                </div>
                <div style={{ marginTop: 8 }}>
                  <Text style={{ color: 'rgba(255,255,255,0.8)', fontWeight: 600, fontSize: 13 }}>
                    💹 市场速览
                  </Text>
                  {briefing.market_snapshots.map((m, i) => (
                    <div key={i} style={{ color: 'rgba(255,255,255,0.9)', fontSize: 13, marginTop: 4 }}>
                      · {m.title}
                    </div>
                  ))}
                </div>
              </Space>
            </Col>
            <Col xs={24} md={10} style={{ textAlign: 'right' }}>
              <div style={{ opacity: 0.2, fontSize: 120, lineHeight: 1, userSelect: 'none' }}>
                <SoundOutlined />
              </div>
            </Col>
          </Row>
        </Card>
      )}

      {/* 天气与节假日 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 20 }}>
        {/* 天气 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <EnvironmentOutlined style={{ color: '#667eea' }} />
                <span>天气 · 昆明</span>
              </Space>
            }
            style={{ borderRadius: 12, height: '100%' }}
          >
            {weather ? (
              <Row align="middle">
                <Col span={8} style={{ textAlign: 'center' }}>
                  <WeatherIcon code={weather.current.icon} />
                  <Title level={2} style={{ margin: '4px 0', fontSize: 36 }}>
                    {weather.current.temp}°
                  </Title>
                  <Text type="secondary">{weather.current.desc}</Text>
                </Col>
                <Col span={16}>
                  <Row gutter={[8, 8]}>
                    {weather.forecast.slice(0, 4).map((day, i) => (
                      <Col span={6} key={i} style={{ textAlign: 'center' }}>
                        <Text type="secondary" style={{ fontSize: 12, display: 'block' }}>
                          {dayjs(day.date).format('dd日')}
                        </Text>
                        <WeatherIcon code={day.icon} />
                        <div style={{ fontSize: 12, marginTop: 2 }}>
                          <Text>{day.temp_high}°</Text>
                          <Text type="secondary">/{day.temp_low}°</Text>
                        </div>
                      </Col>
                    ))}
                  </Row>
                  <Divider style={{ margin: '8px 0' }} />
                  <Space size={16}>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      湿度: {weather.current.humidity}%
                    </Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      风力: {weather.current.wind}km/h
                    </Text>
                  </Space>
                </Col>
              </Row>
            ) : (
              <Empty description="天气数据不可用" />
            )}
          </Card>
        </Col>

        {/* 临近节日 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <GiftOutlined style={{ color: '#f5222d' }} />
                <span>临近节日</span>
              </Space>
            }
            style={{ borderRadius: 12, height: '100%' }}
          >
            {holidays.length > 0 ? (
              <List
                dataSource={holidays}
                renderItem={(item) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={
                        <div style={{
                          width: 48, height: 48, borderRadius: 12,
                          background: item.days_until === 0 ? '#f5222d' : item.days_until <= 7 ? '#fa8c16' : '#52c41a',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          color: '#fff', fontWeight: 'bold', fontSize: 16,
                        }}>
                          {item.days_until === 0 ? '今' : `${item.days_until}`}
                        </div>
                      }
                      title={
                        <Space>
                          <Text strong>{item.name}</Text>
                          <Tag color={item.days_until === 0 ? 'red' : item.days_until <= 7 ? 'orange' : 'green'}>
                            {item.days_until === 0 ? '今天' : `还有 ${item.days_until} 天`}
                          </Tag>
                          <Text type="secondary" style={{ fontSize: 12 }}>放假 {item.duration} 天</Text>
                        </Space>
                      }
                      description={
                        <Text type="secondary">
                          {dayjs(item.date).format('YYYY年M月D日')}
                        </Text>
                      }
                    />
                  </List.Item>
                )}
              />
            ) : (
              <Empty description="暂无节假日数据" />
            )}
          </Card>
        </Col>
      </Row>

      {/* 新闻区域 */}
      <Row gutter={[16, 16]}>
        {/* AI 新闻 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <ThunderboltOutlined style={{ color: '#722ed1' }} />
                <span>AI 新闻</span>
              </Space>
            }
            extra={<a onClick={fetchAll} style={{ fontSize: 13 }}>刷新</a>}
            style={{ borderRadius: 12 }}
          >
            {aiNews.length > 0 ? renderNewsList(aiNews, <ThunderboltOutlined />, '#722ed1') : <Empty description="暂无数据" />}
          </Card>
        </Col>

        {/* 互联网新闻 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <GlobalOutlined style={{ color: '#1890ff' }} />
                <span>互联网新闻</span>
              </Space>
            }
            extra={<a onClick={fetchAll} style={{ fontSize: 13 }}>刷新</a>}
            style={{ borderRadius: 12 }}
          >
            {internetNews.length > 0 ? renderNewsList(internetNews, <GlobalOutlined />, '#1890ff') : <Empty description="暂无数据" />}
          </Card>
        </Col>

        {/* 投资新闻 */}
        <Col xs={24}>
          <Card
            title={
              <Space>
                <RiseOutlined style={{ color: '#52c41a' }} />
                <span>投资新闻</span>
              </Space>
            }
            extra={<a onClick={fetchAll} style={{ fontSize: 13 }}>刷新</a>}
            style={{ borderRadius: 12 }}
          >
            {investmentNews.length > 0 ? renderNewsList(investmentNews, <RiseOutlined />, '#52c41a') : <Empty description="暂无数据" />}
          </Card>
        </Col>
      </Row>
      <div style={{ textAlign: 'center', color: '#999', fontSize: 12, marginTop: 16 }}>
        部署测试 v2.0 — 自动部署管道已就绪 🚀
      </div>
    </div>
  )
}

export default WorkbenchPage
