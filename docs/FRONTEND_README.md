# 家庭智能管家 - 前后端分离架构

## 📁 项目结构

```
myAgent/
├── backend/              # FastAPI 后端
│   ├── main.py          # API 服务入口
│   └── requirements.txt # Python 依赖
├── frontend/            # React 前端
│   ├── src/
│   │   ├── pages/       # 页面组件
│   │   ├── services/    # API 服务
│   │   ├── App.tsx      # 主应用
│   │   └── main.tsx     # 入口文件
│   ├── package.json
│   └── vite.config.ts
└── data/                # 数据存储目录
```

---

## 🚀 快速启动

### 1. 启动后端（FastAPI）

```bash
cd E:\myAgent\backend

# 安装依赖
pip install fastapi uvicorn python-multipart pydantic

# 启动服务
python main.py
```

后端将运行在 `http://localhost:8000`

访问 API 文档：`http://localhost:8000/docs`

### 2. 启动前端（React + Vite）

```bash
cd E:\myAgent\frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将运行在 `http://localhost:3000`

---

## 📦 技术栈

### 后端
- **FastAPI** - 高性能 Python Web 框架
- **Pydantic** - 数据验证
- **Uvicorn** - ASGI 服务器
- **CORS** - 跨域支持

### 前端
- **React 18** - UI 框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Ant Design** - UI 组件库
- **Axios** - HTTP 客户端
- **React Router** - 路由管理

---

## 🔧 API 接口

### 对话接口
```typescript
POST /api/chat
{
  "message": "你好",
  "user_id": "optional"
}
```

### 成员管理
```typescript
GET  /api/members
POST /api/members
DELETE /api/members/{name}
```

### 购物清单
```typescript
GET  /api/shopping
POST /api/shopping
DELETE /api/shopping/{item_name}
POST /api/shopping/stats
```

### 照片记忆
```typescript
GET  /api/photos
POST /api/photos/upload (multipart/form-data)
```

### 智能家居
```typescript
POST /api/smarthome/command
GET  /api/smarthome/devices
```

### MCP协议
```typescript
GET  /api/mcp/tools
POST /api/mcp/call
```

---

## 📝 待完成的页面组件

以下页面需要创建（参考 ChatPage.tsx 的实现方式）：

### 1. MembersPage.tsx
```typescript
// 功能：
// - 显示家庭成员列表
// - 添加新成员表单
// - 删除成员按钮
// 使用 API: membersAPI.getAll(), membersAPI.add(), membersAPI.remove()
```

### 2. SchedulePage.tsx
```typescript
// 功能：
// - 显示日程列表
// - 添加提醒表单（日期选择器 + 事件输入）
// 使用 API: scheduleAPI.getAll(), scheduleAPI.add()
```

### 3. ShoppingPage.tsx
```typescript
// 功能：
// - 购物清单表格（复选框标记已购买）
// - 添加物品表单
// - 统计卡片（总数、已完成、完成率）
// 使用 API: shoppingAPI.getAll(), shoppingAPI.add(), shoppingAPI.remove(), shoppingAPI.getStats()
```

### 4. PhotosPage.tsx
```typescript
// 功能：
// - 照片网格展示
// - 上传照片表单（文件选择 + 描述输入）
// - 搜索功能
// 使用 API: photosAPI.getAll(), photosAPI.upload()
```

### 5. SmartHomePage.tsx
```typescript
// 功能：
// - 自然语言命令输入
// - 设备列表展示
// - 快速控制按钮
// 使用 API: smartHomeAPI.executeCommand(), smartHomeAPI.getDevices()
```

### 6. MCPPage.tsx
```typescript
// 功能：
// - 工具列表（可折叠面板）
// - 工具调用测试界面
// - 结果显示
// 使用 API: mcpAPI.listTools(), mcpAPI.callTool()
```

### 7. StatsPage.tsx
```typescript
// 功能：
// - 统计卡片（成员数、提醒数、记忆数等）
// - 图表展示（可选）
// 使用 API: statsAPI.getStats()
```

---

## 🎨 样式定制

编辑 `frontend/src/App.tsx` 中的主题配置：

```typescript
<ConfigProvider
  theme={{
    token: {
      colorPrimary: '#1890ff',
      borderRadius: 6,
    },
  }}
>
```

---

## 🌐 生产部署

### 构建前端

```bash
cd frontend
npm run build
```

生成的文件在 `frontend/dist/` 目录

### 部署选项

#### 方案一：Nginx 静态托管

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 方案二：Docker Compose

创建 `docker-compose.yml`:

```yaml
version: '3'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
  
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
```

---

## 🔍 开发提示

### 1. API 代理配置

已在 `vite.config.ts` 中配置：

```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true
  }
}
```

开发时前端请求 `/api/*` 会自动转发到后端。

### 2. TypeScript 类型定义

为每个 API 响应创建类型：

```typescript
interface Member {
  name: string
  role: string
  age: number
  // ...
}
```

### 3. 错误处理

在所有 API 调用中添加 try-catch：

```typescript
try {
  const response = await api.getData()
  setData(response.data)
} catch (error) {
  message.error('操作失败')
}
```

---

## 📊 优势对比

| 特性 | Streamlit (旧) | React + FastAPI (新) |
|------|---------------|---------------------|
| 性能 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 灵活性 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| SEO | ⭐ | ⭐⭐⭐⭐ |
| 移动端 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 学习曲线 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 部署复杂度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 可扩展性 | ⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🎯 下一步

1. ✅ 后端 API 已完成
2. ✅ 前端框架已搭建
3. ✅ 聊天页面已完成
4. ⏳ 创建其他页面组件（参考上面的模板）
5. ⏳ 添加路由和状态管理
6. ⏳ 优化性能和用户体验
7. ⏳ 编写单元测试
8. ⏳ 部署到生产环境

---

## 💡 小贴士

- 使用 Ant Design 的 ProComponents 可以快速创建复杂表单和表格
- 考虑添加 Redux 或 Zustand 进行全局状态管理
- 使用 React Query 或 SWR 进行数据缓存
- 添加 Loading 状态和骨架屏提升用户体验

---

**祝开发顺利！** 🚀
