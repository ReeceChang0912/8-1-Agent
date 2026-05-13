import React, { useState, useEffect } from 'react'
import { Card, Row, Col, Spin, Typography, Tag, List, Space, Statistic, Divider, Empty, Alert } from 'antd'
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
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [weather, setWeather] = useState<WeatherData | null>(null)
  const [aiNews, setAiNews] = useState<NewsItem[]>([])
  const [internetNews, setInternetNews] = useState<NewsItem[]>([])
  const [investmentNews, setInvestmentNews] = useState<NewsItem[]>([])
  const [briefing, setBriefing] = useState<BriefingData | null>(null)
  const [holidays, setHolidays] = useState<HolidayItem[]>([])

  useEffect(() => {
    fetchAll()
    const timer = setInterval(fetchAll, 60000)
    return () => clearInterval(timer)
  }, [])

  const fetchAll = async () => {
    setLoading(true)
    setError(null)
    try {
      const [weatherRes, aiRes, internetRes, investRes, briefingRes, holidayRes] = await Promise.allSettled([
        axios.get('/api/workbench/weather', { params: { city: '昆明' } }),
        axios.get('/api/workbench/news', { params: { category: 'ai', limit: 6 } }),
        axios.get('/api/workbench/news', { params: { category: 'internet', limit: 6 } }),
        axios.get('/api/workbench/news', { params: { category: 'investment', limit: 5 } }),
        axios.get('/api/workbench/briefing'),
        axios.get('/api/workbench/holidays'),
      ])

      if (weatherRes.status === 'fulfilled') setWeather(weatherRes.value.data.data)
      if (aiRes.status === 'fulfilled') setAiNews(aiRes.value.data.items)
      if (internetRes.status === 'fulfilled') setInternetNews(internetRes.value.data.items)
      if (investRes.status === 'fulfilled') setInvestmentNews(investRes.value.data.items)
      if (briefingRes.status === 'fulfilled') setBriefing(briefingRes.value.data.data)
      if (holidayRes.status === 'fulfilled') setHolidays(holidayRes.value.data.items)
    } catch {
      setError('部分数据加载失败')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 0' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16, color: '#999' }}>加载工作台数据...</div>
      </div>
    )
  }

  if (error) {
    return <Alert type="warning" message={error} banner closable />
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
      {/* 我的任务 */}
      <TaskNotification memberName={localStorage.getItem('member_name') || ''} />

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
