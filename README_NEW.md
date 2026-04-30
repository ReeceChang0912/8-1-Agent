# 🏡 家庭智能管家 (Family Smart Agent)

> 基于 React + FastAPI + DeepSeek 的现代化家庭AI助手系统

## ✨ 核心功能

- 🤖 **智能对话** - DeepSeek LLM 驱动的自然语言交互
- 👨‍👩‍👧‍👦 **家庭成员管理** - 多用户角色和权限系统
- 📅 **日程管理** - 智能提醒和事件管理
- 🛒 **购物清单** - 物品追踪和统计分析
- 📸 **照片记忆** - 照片上传、标签和搜索
- 🏠 **智能家居** - Home Assistant 集成
- 💬 **微信集成** - 微信机器人支持
- 🔌 **MCP协议** - 标准化工具调用接口

## 🚀 快速开始

### 1️⃣ 一键启动（推荐）

双击运行 `scripts\start.bat`

### 2️⃣ 手动启动

**终端 1 - 后端：**
```bash
cd backend
..\..venv\Scripts\python.exe main.py
```

**终端 2 - 前端：**
```bash
cd frontend
npm install  # 首次运行需要
npm run dev
```

### 3️⃣ 访问应用

- 🌐 前端界面：http://localhost:3000
- 🔧 后端 API：http://localhost:8000
- 📖 API文档：http://localhost:8000/docs

## 📋 前置要求

- ✅ Python 3.13+
- ✅ Node.js 18+
- ✅ DeepSeek API Key（在 `config/.env` 中配置）

## 📚 详细文档

查看 `docs/` 目录获取更多文档：

- [快速开始指南](docs/QUICKSTART.md)
- [API 参考文档](docs/API_REFERENCE.md)
- [部署指南](docs/DEPLOYMENT.md)
- [开发指南](docs/DEVELOPMENT.md)

## 🛠️ 技术栈

**后端：** FastAPI + Uvicorn + ChromaDB + DeepSeek  
**前端：** React 18 + TypeScript + Ant Design + Vite

## 📄 许可证

MIT License

---

**享受你的智能家庭助手！** 🎉
