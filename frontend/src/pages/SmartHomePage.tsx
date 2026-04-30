import React, { useState } from 'react'
import { Card, Input, Button, List, Tabs, message } from 'antd'
import { SendOutlined, HomeOutlined } from '@ant-design/icons'
import { smartHomeAPI } from '../services/api'

const SmartHomePage: React.FC = () => {
  const [command, setCommand] = useState('')
  const [loading, setLoading] = useState(false)
  const [devices, setDevices] = useState([])
  const [result, setResult] = useState('')

  const handleCommand = async () => {
    if (!command.trim()) return
    
    setLoading(true)
    try {
      const res = await smartHomeAPI.executeCommand(command)
      setResult(res.data.result)
      if (res.data.result.includes('✅')) {
        message.success(res.data.result)
      } else {
        message.info(res.data.result)
      }
      setCommand('')
    } catch (error) {
      message.error('命令执行失败')
    } finally {
      setLoading(false)
    }
  }

  const loadDevices = async (type?: string) => {
    try {
      const res = await smartHomeAPI.getDevices(type)
      setDevices(res.data.devices)
    } catch (error) {
      message.error('获取设备失败')
    }
  }

  const quickActions = [
    { name: '💡 打开所有灯', command: '打开所有灯' },
    { name: '🌙 关闭所有灯', command: '关闭所有灯' },
    { name: '❄️ 舒适模式', command: '设置温度25度' },
    { name: '🎬 电影模式', command: '开启电影模式' },
  ]

  return (
    <div>
      <Card title="🏠 智能家居控制" style={{ marginBottom: 16 }}>
        <Input.Search
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          onSearch={handleCommand}
          placeholder="输入语音命令，例如：打开客厅灯、设置温度25度"
          enterButton={<SendOutlined />}
          size="large"
          loading={loading}
        />
        
        {result && (
          <div style={{ marginTop: 16, padding: 12, background: '#f0f2f5', borderRadius: 4 }}>
            <strong>执行结果：</strong>{result}
          </div>
        )}
      </Card>

      <Card title="快速操作" style={{ marginBottom: 16 }}>
        <List
          grid={{ gutter: 16, column: 4 }}
          dataSource={quickActions}
          renderItem={(action) => (
            <List.Item>
              <Button
                block
                onClick={() => {
                  setCommand(action.command)
                  handleCommand()
                }}
              >
                {action.name}
              </Button>
            </List.Item>
          )}
        />
      </Card>

      <Card
        title="设备列表"
        extra={
          <Button onClick={() => loadDevices()}>刷新</Button>
        }
      >
        <Tabs
          items={[
            {
              key: 'all',
              label: '全部设备',
              children: (
                <List
                  dataSource={devices}
                  renderItem={(device: any) => (
                    <List.Item>
                      <List.Item.Meta
                        title={device.entity_id}
                        description={`状态: ${device.state}`}
                      />
                    </List.Item>
                  )}
                />
              ),
            },
            {
              key: 'light',
              label: '灯光',
              children: (
                <Button onClick={() => loadDevices('light')}>加载灯光设备</Button>
              ),
            },
            {
              key: 'climate',
              label: '温控',
              children: (
                <Button onClick={() => loadDevices('climate')}>加载温控设备</Button>
              ),
            },
          ]}
        />
      </Card>

      <Card title="配置说明">
        <div style={{ lineHeight: 1.8 }}>
          <p><strong>使用前需要配置：</strong></p>
          <ol>
            <li>安装 Home Assistant</li>
            <li>在 HA 中创建 Long-lived Access Token</li>
            <li>在后端配置 HA URL 和 Token</li>
          </ol>
          <p><strong>支持的命令示例：</strong></p>
          <ul>
            <li>打开客厅灯</li>
            <li>关闭所有灯</li>
            <li>设置温度25度</li>
            <li>打开空调</li>
          </ul>
        </div>
      </Card>
    </div>
  )
}

export default SmartHomePage
