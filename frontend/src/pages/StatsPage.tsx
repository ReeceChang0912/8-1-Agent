import React, { useState, useEffect } from 'react'
import { Card, Statistic, Row, Col, Progress, Spin } from 'antd'
import { 
  TeamOutlined, 
  CalendarOutlined, 
  DatabaseOutlined,
  FileTextOutlined 
} from '@ant-design/icons'
import { statsAPI } from '../services/api'

const StatsPage: React.FC = () => {
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    setLoading(true)
    try {
      const res = await statsAPI.getStats()
      setStats(res.data)
    } catch (error) {
      console.error('加载统计失败')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 40 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!stats) {
    return <div>暂无数据</div>
  }

  return (
    <div>
      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <Statistic
              title="家庭成员"
              value={stats.members_count || 0}
              prefix={<TeamOutlined />}
              suffix="人"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="日程提醒"
              value={stats.reminders_count || 0}
              prefix={<CalendarOutlined />}
              suffix="个"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="记忆条数"
              value={stats.memory_stats?.total_memories || 0}
              prefix={<DatabaseOutlined />}
              suffix="条"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="知识文档"
              value={stats.kb_stats?.document_count || 0}
              prefix={<FileTextOutlined />}
              suffix="篇"
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="记忆类型分布">
            {stats.memory_stats?.by_type ? (
              Object.entries(stats.memory_stats.by_type).map(([type, count]: [string, any]) => (
                <div key={type} style={{ marginBottom: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span>{type}</span>
                    <span>{count} 条</span>
                  </div>
                  <Progress percent={Math.min(100, (count / stats.memory_stats.total_memories) * 100)} showInfo={false} />
                </div>
              ))
            ) : (
              <div style={{ textAlign: 'center', color: '#999' }}>暂无数据</div>
            )}
          </Card>
        </Col>

        <Col span={12}>
          <Card title="知识库统计">
            {stats.kb_stats ? (
              <>
                <div style={{ marginBottom: 16 }}>
                  <strong>总文档数：</strong>{stats.kb_stats.document_count || 0}
                </div>
                <div style={{ marginBottom: 16 }}>
                  <strong>总段落数：</strong>{stats.kb_stats.chunk_count || 0}
                </div>
                <div>
                  <strong>向量维度：</strong>{stats.kb_stats.embedding_dim || 0}
                </div>
              </>
            ) : (
              <div style={{ textAlign: 'center', color: '#999' }}>暂无数据</div>
            )}
          </Card>
        </Col>
      </Row>

      <Card title="系统信息" style={{ marginTop: 16 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Statistic title="LLM 提供商" value="DeepSeek" />
          </Col>
          <Col span={8}>
            <Statistic title="数据库" value="ChromaDB" />
          </Col>
          <Col span={8}>
            <Statistic title="版本" value="1.0.0" />
          </Col>
        </Row>
      </Card>
    </div>
  )
}

export default StatsPage
