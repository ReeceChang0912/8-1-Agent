import React, { useState, useEffect } from 'react'
import { Card, Switch, Tag, Button, Input, Form, message, Collapse, Badge, Tooltip, Row, Col, Select, Empty } from 'antd'
import { 
  ToolOutlined, 
  CheckCircleOutlined, 
  CloseCircleOutlined,
  SettingOutlined,
  ThunderboltOutlined,
  ApiOutlined,
  RobotOutlined
} from '@ant-design/icons'
import axios from 'axios'

const { Panel } = Collapse
const { Option } = Select

interface Skill {
  id: string
  name: string
  description: string
  category: string
  enabled: boolean
  icon: string
  config?: Record<string, any>
  usage_count: number
  last_used?: string
}

const SkillsPage: React.FC = () => {
  const [skills, setSkills] = useState<Skill[]>([])
  const [loading, setLoading] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')

  // 模拟技能数据(实际应该从后端API获取)
  const defaultSkills: Skill[] = [
    {
      id: 'blog-page-generator',
      name: '博客页面生成器',
      description: '创建和优化博客索引或列表页面结构,支持SEO优化',
      category: 'content',
      enabled: false,
      icon: '📝',
      usage_count: 0
    },
    {
      id: 'frontend-design',
      name: '前端设计专家',
      description: '创建高质量的前端界面,避免通用AI美学,生成精美的UI设计',
      category: 'development',
      enabled: true,
      icon: '🎨',
      usage_count: 12
    },
    {
      id: 'seo-content-writer',
      name: 'SEO内容写作',
      description: '撰写SEO优化的博客文章、落地页,包含关键词集成和标题优化',
      category: 'content',
      enabled: false,
      icon: '✍️',
      usage_count: 5
    },
    {
      id: 'web-design-guidelines',
      name: 'Web设计指南审查',
      description: '审查UI代码是否符合Web界面指南,检查可访问性和设计',
      category: 'review',
      enabled: true,
      icon: '✅',
      usage_count: 8
    },
    {
      id: 'git-commit',
      name: 'Git提交助手',
      description: '执行git commit,自动生成符合规范的提交消息,智能暂存文件',
      category: 'development',
      enabled: true,
      icon: '💾',
      usage_count: 23
    },
    {
      id: 'github',
      name: 'GitHub营销',
      description: '使用GitHub进行SEO、开源营销、README优化和精选列表管理',
      category: 'marketing',
      enabled: false,
      icon: '🐙',
      usage_count: 3
    },
    {
      id: 'documentation-writer',
      name: '文档编写专家',
      description: '基于Diátaxis框架创建高质量的技术文档',
      category: 'content',
      enabled: true,
      icon: '📚',
      usage_count: 15
    },
    {
      id: 'supabase',
      name: 'Supabase集成',
      description: '与Supabase交互,包括数据库、认证、边缘函数等所有产品',
      category: 'integration',
      enabled: false,
      icon: '⚡',
      usage_count: 0
    },
    {
      id: 'notion-api',
      name: 'Notion API集成',
      description: '与Notion API交互,管理页面、数据库、块和评论',
      category: 'integration',
      enabled: false,
      icon: '📋',
      usage_count: 0
    },
    {
      id: 'write-blog',
      name: '博客文章生成',
      description: '生成完整的SEO优化博客文章,包含关键词研究和片段目标',
      category: 'content',
      enabled: true,
      icon: '📰',
      usage_count: 18
    }
  ]

  useEffect(() => {
    loadSkills()
  }, [])

  const loadSkills = async () => {
    setLoading(true)
    try {
      // 尝试从后端加载,如果失败则使用默认数据
      const res = await axios.get('/api/skills')
      setSkills(res.data.skills || defaultSkills)
    } catch (error) {
      console.log('使用默认技能数据')
      setSkills(defaultSkills)
    } finally {
      setLoading(false)
    }
  }

  const toggleSkill = async (skillId: string, enabled: boolean) => {
    try {
      await axios.post(`/api/skills/${skillId}/toggle`, { enabled })
      
      setSkills(skills.map(skill => 
        skill.id === skillId ? { ...skill, enabled } : skill
      ))
      
      message.success(enabled ? '✅ 技能已启用' : '⏸️ 技能已禁用')
    } catch (error) {
      // 如果后端API不存在,仅更新本地状态
      setSkills(skills.map(skill => 
        skill.id === skillId ? { ...skill, enabled } : skill
      ))
      message.info('技能状态已更新(本地模式)')
    }
  }

  const getCategories = () => {
    const categories = new Set(skills.map(s => s.category))
    return ['all', ...Array.from(categories)]
  }

  const getCategoryName = (category: string) => {
    const names: Record<string, string> = {
      all: '全部',
      content: '📝 内容创作',
      development: '💻 开发工具',
      review: '✅ 代码审查',
      marketing: '📢 营销推广',
      integration: '🔌 平台集成'
    }
    return names[category] || category
  }

  const filteredSkills = skills.filter(skill => {
    const matchesSearch = skill.name.toLowerCase().includes(searchText.toLowerCase()) ||
                         skill.description.toLowerCase().includes(searchText.toLowerCase())
    const matchesCategory = selectedCategory === 'all' || skill.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  const stats = {
    total: skills.length,
    enabled: skills.filter(s => s.enabled).length,
    disabled: skills.filter(s => !s.enabled).length,
    totalUsage: skills.reduce((sum, s) => sum + s.usage_count, 0)
  }

  return (
    <div>
      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={12} md={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 24, fontWeight: 'bold', color: '#1890ff' }}>
                {stats.total}
              </div>
              <div style={{ color: '#666', marginTop: 8 }}>总技能数</div>
            </div>
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 24, fontWeight: 'bold', color: '#52c41a' }}>
                {stats.enabled}
              </div>
              <div style={{ color: '#666', marginTop: 8 }}>已启用</div>
            </div>
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 24, fontWeight: 'bold', color: '#f5222d' }}>
                {stats.disabled}
              </div>
              <div style={{ color: '#666', marginTop: 8 }}>已禁用</div>
            </div>
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 24, fontWeight: 'bold', color: '#722ed1' }}>
                {stats.totalUsage}
              </div>
              <div style={{ color: '#666', marginTop: 8 }}>总使用次数</div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 搜索和筛选 */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={16}>
            <Input.Search
              placeholder="搜索技能名称或描述..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onSearch={setSearchText}
              allowClear
              size="large"
            />
          </Col>
          <Col xs={24} sm={8}>
            <Select
              placeholder="选择分类"
              value={selectedCategory}
              onChange={setSelectedCategory}
              size="large"
              style={{ width: '100%' }}
            >
              {getCategories().map(cat => (
                <Option key={cat} value={cat}>
                  {getCategoryName(cat)}
                </Option>
              ))}
            </Select>
          </Col>
        </Row>
      </Card>

      {/* 技能列表 */}
      <Collapse defaultActiveKey={['enabled', 'disabled']}>
        <Panel 
          header={
            <span>
              <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
              已启用的技能 ({stats.enabled})
            </span>
          } 
          key="enabled"
        >
          <Row gutter={[16, 16]}>
            {filteredSkills.filter(s => s.enabled).map(skill => (
              <Col xs={24} sm={12} lg={8} key={skill.id}>
                <Card
                  hoverable
                  actions={[
                    <Tooltip title="配置">
                      <Button type="text" icon={<SettingOutlined />} />
                    </Tooltip>,
                    <Tooltip title="禁用">
                      <Switch 
                        checked={skill.enabled} 
                        onChange={(checked) => toggleSkill(skill.id, checked)}
                        checkedChildren="启用"
                        unCheckedChildren="禁用"
                      />
                    </Tooltip>
                  ]}
                >
                  <Card.Meta
                    avatar={<div style={{ fontSize: 32 }}>{skill.icon}</div>}
                    title={
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span>{skill.name}</span>
                        <Badge count={skill.usage_count} showZero style={{ backgroundColor: '#52c41a' }} />
                      </div>
                    }
                    description={
                      <div>
                        <p style={{ margin: '8px 0', color: '#666' }}>{skill.description}</p>
                        <Tag color="blue">{getCategoryName(skill.category)}</Tag>
                        {skill.last_used && (
                          <div style={{ marginTop: 8, fontSize: 12, color: '#999' }}>
                            最后使用: {new Date(skill.last_used).toLocaleDateString()}
                          </div>
                        )}
                      </div>
                    }
                  />
                </Card>
              </Col>
            ))}
            {filteredSkills.filter(s => s.enabled).length === 0 && (
              <Col span={24}>
                <Empty description="暂无已启用的技能" />
              </Col>
            )}
          </Row>
        </Panel>

        <Panel 
          header={
            <span>
              <CloseCircleOutlined style={{ color: '#f5222d', marginRight: 8 }} />
              已禁用的技能 ({stats.disabled})
            </span>
          } 
          key="disabled"
        >
          <Row gutter={[16, 16]}>
            {filteredSkills.filter(s => !s.enabled).map(skill => (
              <Col xs={24} sm={12} lg={8} key={skill.id}>
                <Card
                  hoverable
                  actions={[
                    <Tooltip title="配置">
                      <Button type="text" icon={<SettingOutlined />} disabled />
                    </Tooltip>,
                    <Tooltip title="启用">
                      <Switch 
                        checked={skill.enabled} 
                        onChange={(checked) => toggleSkill(skill.id, checked)}
                        checkedChildren="启用"
                        unCheckedChildren="禁用"
                      />
                    </Tooltip>
                  ]}
                >
                  <Card.Meta
                    avatar={<div style={{ fontSize: 32, opacity: 0.5 }}>{skill.icon}</div>}
                    title={
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span style={{ opacity: 0.5 }}>{skill.name}</span>
                        <Badge count={skill.usage_count} showZero style={{ backgroundColor: '#d9d9d9' }} />
                      </div>
                    }
                    description={
                      <div>
                        <p style={{ margin: '8px 0', color: '#999' }}>{skill.description}</p>
                        <Tag>{getCategoryName(skill.category)}</Tag>
                      </div>
                    }
                  />
                </Card>
              </Col>
            ))}
            {filteredSkills.filter(s => !s.enabled).length === 0 && (
              <Col span={24}>
                <Empty description="暂无已禁用的技能" />
              </Col>
            )}
          </Row>
        </Panel>
      </Collapse>

      {/* 使用说明 */}
      <Card title="💡 使用说明" style={{ marginTop: 16 }}>
        <div style={{ lineHeight: 2 }}>
          <p><strong>什么是技能(Skills)?</strong></p>
          <p>技能是预定义的专业能力模块,可以增强AI助手的特定领域功能。每个技能都专注于解决特定类型的问题。</p>
          
          <p><strong>如何使用?</strong></p>
          <ul>
            <li>🟢 <strong>启用技能</strong>: 打开开关即可激活该技能,AI会在相关场景中自动使用</li>
            <li>⚙️ <strong>配置技能</strong>: 点击设置图标可以自定义技能的参数和行为</li>
            <li>📊 <strong>查看统计</strong>: 每个技能显示使用次数,帮助你了解哪些技能最常用</li>
            <li>🔍 <strong>搜索筛选</strong>: 使用搜索框和分类筛选快速找到需要的技能</li>
          </ul>

          <p><strong>技能分类:</strong></p>
          <ul>
            <li>📝 <strong>内容创作</strong>: 博客写作、SEO优化、文档生成等</li>
            <li>💻 <strong>开发工具</strong>: Git操作、前端设计、代码生成等</li>
            <li>✅ <strong>代码审查</strong>: 设计指南检查、最佳实践审核等</li>
            <li>📢 <strong>营销推广</strong>: GitHub营销、社交媒体管理等</li>
            <li>🔌 <strong>平台集成</strong>: Notion、Supabase等第三方服务集成</li>
          </ul>
        </div>
      </Card>
    </div>
  )
}

export default SkillsPage
