# 家庭智能管家 - 优化后的文件组织结构

## 📁 新的目录结构

```
E:\myAgent\
│
├── 📂 backend/                    # FastAPI 后端服务
│   ├── main.py                   # API 入口文件
│   ├── requirements.txt          # Python 依赖
│   └── README.md                 # 后端说明文档
│
├── 📂 frontend/                   # React 前端应用
│   ├── src/
│   │   ├── pages/                # 页面组件 (8个)
│   │   ├── services/             # API 服务层
│   │   ├── components/           # 可复用组件（待扩展）
│   │   ├── hooks/                # 自定义 Hooks（待扩展）
│   │   ├── utils/                # 工具函数（待扩展）
│   │   ├── App.tsx               # 主应用
│   │   └── main.tsx              # 入口文件
│   ├── public/                   # 静态资源
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── README.md                 # 前端说明文档
│
├── 📂 family_agent/               # 核心业务逻辑（Python包）
│   ├── __init__.py
│   ├── core.py                   # Agent 核心
│   ├── llm_adapter.py            # LLM 适配器
│   ├── role_manager.py           # 角色管理
│   ├── memory_manager.py         # 记忆管理
│   ├── knowledge_base.py         # 知识库
│   ├── emotion_engine.py         # 情感引擎
│   ├── tool_engine.py            # 工具引擎
│   ├── shopping_list.py          # 购物清单
│   ├── photo_memory.py           # 照片记忆
│   ├── wechat_integration.py     # 微信集成
│   ├── smart_home.py             # 智能家居
│   └── mcp_integration.py        # MCP协议
│
├── 📂 data/                       # 数据存储目录
│   ├── chroma_db/                # ChromaDB 向量数据库
│   ├── shopping_list.json        # 购物清单数据
│   ├── photo_index.json          # 照片索引
│   └── ...                       # 其他数据文件
│
├── 📂 photos/                     # 照片存储目录
│   └── (上传的照片文件)
│
├── 📂 docs/                       # 项目文档
│   ├── README.md                 # 项目总览 ⭐
│   ├── QUICKSTART.md             # 快速开始
│   ├── API_REFERENCE.md          # API 参考文档
│   ├── DEPLOYMENT.md             # 部署指南
│   ├── DEVELOPMENT.md            # 开发指南
│   ├── ARCHITECTURE.md           # 架构设计
│   ├── CHANGELOG.md              # 更新日志
│   └── CONTRIBUTING.md           # 贡献指南
│
├── 📂 scripts/                    # 脚本文件
│   ├── start.bat                 # Windows 启动脚本
│   ├── start.sh                  # Linux/Mac 启动脚本
│   ├── setup.py                  # 安装脚本
│   ├── backup.py                 # 备份脚本
│   └── migrate.py                # 数据迁移脚本
│
├── 📂 config/                     # 配置文件
│   ├── .env                      # 环境变量（不提交到Git）
│   ├── .env.example              # 环境变量示例
│   ├── settings.yaml             # 应用配置
│   └── logging.conf              # 日志配置
│
├── 📂 tests/                      # 测试文件
│   ├── test_api.py               # API 测试
│   ├── test_core.py              # 核心功能测试
│   ├── test_llm.py               # LLM 测试
│   └── conftest.py               # pytest 配置
│
├── 📂 .streamlit/                 # Streamlit 配置（保留兼容）
│   └── config.toml
│
├── 📂 .venv/                      # Python 虚拟环境
│
├── 📄 main.py                     # Streamlit 主程序（保留兼容）
├── 📄 pyproject.toml              # Poetry 项目配置
├── 📄 uv.lock                     # UV 锁定文件
├── 📄 Dockerfile                  # Docker 构建文件
├── 📄 docker-compose.yml          # Docker Compose 配置
├── 📄 .gitignore                  # Git 忽略规则
└── 📄 LICENSE                     # 开源许可证
```

---

## 🔄 迁移步骤

### 第 1 步：创建新目录

在 PowerShell 中执行：

```powershell
cd E:\myAgent

# 创建新目录
New-Item -ItemType Directory -Force -Path docs,scripts,config,tests

# 移动文档到 docs 目录
Move-Item -Path "*.md" -Destination docs\ -ErrorAction SilentlyContinue
Move-Item -Path "*.txt" -Destination docs\ -ErrorAction SilentlyContinue

# 移动配置文件到 config 目录
Move-Item -Path ".env*" -Destination config\ -Force
Copy-Item -Path ".streamlit\config.toml" -Destination config\streamlit.toml

# 创建启动脚本
```

### 第 2 步：整理文档

将相关文档合并或重命名：

**保留的核心文档：**
- `docs/README.md` - 项目总览（最重要）
- `docs/QUICKSTART.md` - 快速开始指南
- `docs/API_REFERENCE.md` - API 文档
- `docs/DEPLOYMENT.md` - 部署指南

**可以删除的冗余文档：**
- `CHECKLIST.md` → 合并到 README
- `FINAL_REPORT.md` → 归档或删除
- `PROJECT_SUMMARY.md` → 合并到 README
- `QUICK_REFERENCE.md` → 合并到 QUICKSTART
- `USER_MANUAL.md` → 合并到 README
- `VENV_GUIDE.md` → 合并到 DEVELOPMENT
- `D_DRIVE_INSTALL.md` → 合并到 DEPLOYMENT
- `D_DRIVE_SETUP.md` → 合并到 DEPLOYMENT
- `MIGRATION_GUIDE.md` → 归档
- `LLM_CONFIG.md` → 合并到 API_REFERENCE
- `DEEPSEEK_CONFIG.md` → 合并到 API_REFERENCE
- `FRONTEND_README.md` → 移动到 frontend/README.md
- `REACT_FASTAPI_GUIDE.md` → 合并到 DEVELOPMENT
- `README_FULLSTACK.md` → 替换为新的 README.md
- `SERVER_DEPLOY.md` → 合并到 DEPLOYMENT

### 第 3 步：创建启动脚本

创建 `scripts/start.bat`：

```batch
@echo off
echo ========================================
echo   家庭智能管家 - 启动服务
echo ========================================
echo.

echo [1/2] 启动后端服务...
start "Backend" cmd /k "cd backend && ..\.venv\Scripts\python.exe main.py"

timeout /t 3 /nobreak >nul

echo [2/2] 启动前端服务...
start "Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo   服务已启动！
echo   前端: http://localhost:3000
echo   后端: http://localhost:8000
echo   API文档: http://localhost:8000/docs
echo ========================================
pause
```

### 第 4 步：更新 .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
*.egg-info/
dist/
.venv/
venv/
ENV/

# Node
node_modules/
frontend/dist/
frontend/build/
*.log

# Data
data/
photos/
*.pkl

# Environment
config/.env
.env.local

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

---

## 📝 新的 README.md 内容

创建根目录的 `docs/README.md`：

```markdown
# 🏡 家庭智能管家 (Family Smart Agent)

> 基于 React + FastAPI + DeepSeek 的现代化家庭AI助手系统

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2-blue.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ 特性

- 🤖 **智能对话** - 基于 DeepSeek LLM 的自然语言交互
- 👨‍👩‍👧‍👦 **家庭成员管理** - 多用户角色和权限系统
- 📅 **日程管理** - 智能提醒和事件管理
- 🛒 **购物清单** - 物品追踪和统计分析
- 📸 **照片记忆** - 照片上传、标签和搜索
- 🏠 **智能家居** - Home Assistant 集成
- 💬 **微信集成** - 微信机器人支持
- 🔌 **MCP协议** - 标准化工具调用接口

---

## 🚀 快速开始

### 前置要求

- Python 3.13+
- Node.js 18+
- npm 或 yarn

### 安装

```bash
# 克隆项目
git clone <repository-url>
cd myAgent

# 安装后端依赖
cd backend
pip install -r requirements.txt

# 安装前端依赖
cd ../frontend
npm install

# 配置环境变量
cp ../config/.env.example ../config/.env
# 编辑 .env 文件，填入你的 DeepSeek API Key
```

### 启动

```bash
# 方式一：使用启动脚本（Windows）
..\scripts\start.bat

# 方式二：手动启动
# 终端1 - 后端
cd backend
python main.py

# 终端2 - 前端
cd frontend
npm run dev
```

访问：
- 前端界面：http://localhost:3000
- API 文档：http://localhost:8000/docs

---

## 📚 文档

- [快速开始](QUICKSTART.md)
- [API 参考](API_REFERENCE.md)
- [部署指南](DEPLOYMENT.md)
- [开发指南](DEVELOPMENT.md)
- [架构设计](ARCHITECTURE.md)

---

## 🛠️ 技术栈

**后端：**
- FastAPI - Web 框架
- Uvicorn - ASGI 服务器
- ChromaDB - 向量数据库
- DeepSeek - LLM

**前端：**
- React 18 - UI 框架
- TypeScript - 类型安全
- Ant Design - UI 组件库
- Vite - 构建工具

---

## 📄 许可证

MIT License

---

## 🙏 致谢

感谢以下开源项目：
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://reactjs.org/)
- [Ant Design](https://ant.design/)
- [DeepSeek](https://platform.deepseek.com/)
```

---

## ✅ 优化后的优势

1. **清晰的职责分离**
   - backend/ - 后端代码
   - frontend/ - 前端代码
   - family_agent/ - 核心业务逻辑
   - docs/ - 所有文档
   - scripts/ - 所有脚本
   - config/ - 所有配置

2. **易于维护**
   - 相关文件集中管理
   - 文档统一存放
   - 脚本统一管理

3. **专业的项目结构**
   - 符合行业标准
   - 便于团队协作
   - 易于 CI/CD 集成

4. **更好的可扩展性**
   - tests/ - 测试文件独立
   - components/ - 可复用组件
   - hooks/ - 自定义 Hooks
   - utils/ - 工具函数

---

## 🎯 下一步行动

请在 PowerShell 中执行以下命令完成迁移：

```powershell
# 1. 创建新目录
cd E:\myAgent
New-Item -ItemType Directory -Force -Path docs,scripts,config,tests

# 2. 移动文档
Move-Item -Path "*.md" -Destination docs\
Move-Item -Path "*.txt" -Destination docs\

# 3. 移动配置文件
Move-Item -Path ".env*" -Destination config\ -Force

# 4. 复制重要文档到根目录
Copy-Item -Path "docs\README_FULLSTACK.md" -Destination "README.md" -Force

# 5. 创建启动脚本
# （手动创建 scripts\start.bat，内容见上文）
```

完成后，项目结构将更加清晰和专业！🎉
