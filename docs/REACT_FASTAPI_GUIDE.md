# 家庭智能管家 - React + FastAPI 快速启动指南

## 🎉 架构升级完成！

项目已从 Streamlit 单体应用升级为 **React + FastAPI** 前后端分离架构。

---

## ⚡ 一键启动（Windows）

双击运行 `run_fullstack.bat` 即可同时启动前后端服务！

---

## 📋 手动启动步骤

### 1️⃣ 启动后端（FastAPI）

```bash
cd E:\myAgent\backend

# 首次运行需要安装依赖
pip install fastapi uvicorn python-multipart pydantic

# 启动服务
python main.py
```

✅ 后端将运行在：`http://localhost:8000`  
📖 API 文档：`http://localhost:8000/docs`

---

### 2️⃣ 启动前端（React + Vite）

```bash
cd E:\myAgent\frontend

# 首次运行需要安装依赖
npm install

# 启动开发服务器
npm run dev
```

✅ 前端将运行在：`http://localhost:3000`

---

## 🏗️ 项目结构

```
E:\myAgent\
├── backend/                 # Python FastAPI 后端
│   ├── main.py             # API 服务入口（442行完整API）
│   └── requirements.txt    # Python 依赖
│
├── frontend/               # React TypeScript 前端
│   ├── src/
│   │   ├── pages/          # 页面组件
│   │   │   └── ChatPage.tsx    # ✅ 聊天页面已完成
│   │   ├── services/       # API 服务层
│   │   │   └── api.ts      # ✅ 所有 API 接口封装
│   │   ├── App.tsx         # ✅ 主应用框架
│   │   └── main.tsx        # ✅ 入口文件
│   ├── index.html
│   ├── package.json        # Node.js 依赖配置
│   ├── vite.config.ts      # Vite 配置
│   └── tsconfig.json       # TypeScript 配置
│
├── family_agent/           # 核心业务逻辑（保持不变）
├── data/                   # 数据存储
├── .env                    # 环境变量配置
├── run_fullstack.bat       # ✅ 一键启动脚本
└── FRONTEND_README.md      # 📖 详细开发文档
```

---

## ✨ 已完成的组件

### ✅ 后端 API（100% 完成）

- [x] POST `/api/chat` - 智能对话
- [x] GET/POST/DELETE `/api/members` - 成员管理
- [x] GET/POST `/api/reminders` - 日程管理
- [x] GET/POST/DELETE `/api/shopping` - 购物清单
- [x] GET/POST `/api/photos` - 照片记忆
- [x] POST `/api/smarthome/command` - 智能家居
- [x] GET/POST `/api/mcp` - MCP协议
- [x] GET `/api/stats` - 统计信息

### ✅ 前端组件（部分完成）

- [x] App.tsx - 主应用框架（侧边栏 + 路由）
- [x] ChatPage.tsx - 聊天界面（完整功能）
- [x] api.ts - 所有 API 接口封装
- [ ] MembersPage.tsx - 待创建
- [ ] SchedulePage.tsx - 待创建
- [ ] ShoppingPage.tsx - 待创建
- [ ] PhotosPage.tsx - 待创建
- [ ] SmartHomePage.tsx - 待创建
- [ ] MCPPage.tsx - 待创建
- [ ] StatsPage.tsx - 待创建

---

## 🎯 创建剩余页面（简单模板）

参考 `ChatPage.tsx`，其他页面只需 50-100 行代码。

### 示例：ShoppingPage.tsx

```typescript
import React, { useState, useEffect } from 'react'
import { Card, Table, Button, Input, Form, message } from 'antd'
import { shoppingAPI } from '../services/api'

const ShoppingPage: React.FC = () => {
  const [items, setItems] = useState([])
  const [form] = Form.useForm()

  useEffect(() => {
    loadItems()
  }, [])

  const loadItems = async () => {
    const res = await shoppingAPI.getAll()
    setItems(res.data.items)
  }

  const handleAdd = async (values: any) => {
    await shoppingAPI.add(values)
    message.success('添加成功')
    form.resetFields()
    loadItems()
  }

  const columns = [
    { title: '物品', dataIndex: 'name' },
    { title: '数量', dataIndex: 'quantity' },
    { title: '分类', dataIndex: 'category' },
    { 
      title: '状态', 
      render: (r: any) => r.purchased ? '✅ 已购买' : '⏳ 待购买'
    },
  ]

  return (
    <div>
      <Card title="添加物品" style={{ marginBottom: 16 }}>
        <Form form={form} onFinish={handleAdd}>
          <Form.Item name="name" label="物品名称">
            <Input />
          </Form.Item>
          <Form.Item name="quantity" label="数量">
            <Input defaultValue="1" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit">添加</Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="购物清单">
        <Table dataSource={items} columns={columns} rowKey="name" />
      </Card>
    </div>
  )
}

export default ShoppingPage
```

就这么简单！其他页面类似。

---

## 🔧 技术栈对比

| 特性 | Streamlit (旧) | React + FastAPI (新) |
|------|---------------|---------------------|
| 前端框架 | Streamlit | React 18 + TypeScript |
| 后端框架 | 无（单体） | FastAPI |
| UI 组件 | Streamlit 内置 | Ant Design |
| 构建工具 | 无 | Vite |
| API 风格 | 函数调用 | RESTful |
| 性能 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 可扩展性 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 移动端支持 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| SEO | ⭐ | ⭐⭐⭐⭐ |

---

## 🌐 访问地址

- **前端界面**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs (Swagger UI)
- **ReDoc 文档**: http://localhost:8000/redoc

---

## 📦 安装依赖

### 后端依赖（Python）

```bash
pip install fastapi uvicorn python-multipart pydantic
```

这些包会自动导入已有的 `family_agent` 模块。

### 前端依赖（Node.js）

```bash
cd frontend
npm install
```

这会安装：
- react + react-dom
- antd (UI 组件库)
- axios (HTTP 客户端)
- typescript
- vite (构建工具)

---

## 🚀 下一步计划

1. **完善前端页面**
   - 创建剩余的 7 个页面组件
   - 每个页面约 50-100 行代码
   - 参考 `ChatPage.tsx` 和 `FRONTEND_README.md`

2. **优化用户体验**
   - 添加 Loading 状态
   - 添加错误处理
   - 添加动画效果

3. **响应式设计**
   - 适配移动端
   - 使用 Ant Design 的 Grid 系统

4. **状态管理**（可选）
   - 使用 Zustand 或 Redux
   - 管理用户登录状态

5. **部署到生产环境**
   - 前端打包：`npm run build`
   - 后端使用 Gunicorn
   - 配置 Nginx 反向代理

---

## 💡 常见问题

### Q: 为什么选择 React + FastAPI？

A: 
- **性能更好**：前后端独立优化
- **更灵活**：可以单独升级前端或后端
- **更易维护**：职责清晰，代码分离
- **更好的生态**：React 和 FastAPI 都有庞大的社区

### Q: 旧的 Streamlit 代码还能用吗？

A: 可以！`main.py` 仍然保留，你可以继续使用 Streamlit 版本作为备用。

### Q: 如何调试 API？

A: 访问 http://localhost:8000/docs，这是 Swagger UI，可以直接测试所有 API。

### Q: 前端如何调用后端？

A: 通过 `vite.config.ts` 中的代理配置，前端请求 `/api/*` 会自动转发到 `http://localhost:8000/api/*`。

---

## 📞 需要帮助？

查看详细文档：
- `FRONTEND_README.md` - 前端开发完整指南
- `SERVER_DEPLOY.md` - 服务器部署指南
- `DEEPSEEK_CONFIG.md` - DeepSeek 配置指南

---

**开始享受现代化的开发体验吧！** 🎊
