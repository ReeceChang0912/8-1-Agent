# 阿里云宝塔面板部署指南

> 适用场景：阿里云 ECS + 宝塔面板（Linux），部署 **FastAPI 后端** + **React 前端**

---

## 一、服务器准备

### 1.1 购买阿里云 ECS
- 推荐配置：2 核 4G（入门够用），系统选 **CentOS 7.9 / Ubuntu 22.04**
- 安全组放行端口：
  - `80`（HTTP）
  - `443`（HTTPS，如需）
  - `5432`（PostgreSQL，如果自建）
  - `8000`（后端调试用，部署后可不对外开放）

### 1.2 安装宝塔面板
```bash
# SSH 登录服务器后执行
CentOS: yum install -y wget && wget -O install.sh https://download.bt.cn/install/install_6.0.sh && bash install.sh
Ubuntu: wget -O install.sh https://download.bt.cn/install/install-ubuntu_6.0.sh && bash install.sh
```

安装完成后，访问显示的 URL 登录宝塔面板。

---

## 二、安装所需软件

进入宝塔面板 → **软件商店**，安装：

| 软件 | 版本 | 用途 |
|------|------|------|
| **Nginx** | 1.24+ | 反向代理前端和后端 |
| **PostgreSQL** | 16+ | 数据库 |
| **Python 项目管理器** | 2.0+ | 管理 Python 后端进程 |
| **Node.js** | 18+ | 构建前端 |
| **PM2** | 最新 | 可选，进程管理 |

---

## 三、配置 PostgreSQL 数据库

### 3.1 创建数据库
宝塔面板 → 数据库 → PostgreSQL → 添加数据库：
- **数据库名**: `agent`
- **用户名**: `family_agent`
- **密码**: 生成强密码（如 `Abc123Xyz!@#`）
- **访问权限**: 本地（localhost）

### 3.2 测试连接
```bash
# SSH 连接服务器后测试
psql -U family_agent -d agent -h localhost
# 输入密码后进入 psql 即成功
\q  # 退出
```

> **获取连接字符串**: `postgresql://family_agent:你的密码@localhost:5432/agent`

---

## 四、上传项目代码

### 4.1 通过宝塔面板上传
1. 宝塔 → **文件** → 进入 `/www/wwwroot/`
2. 创建目录：`family-agent`
3. 将本地项目压缩后上传解压，或用 `git clone`

### 4.2 或通过 Git 拉取
```bash
cd /www/wwwroot/
git clone https://github.com/你的仓库/family-agent.git
cd family-agent
```

### 4.3 配置环境变量
```bash
cd /www/wwwroot/family-agent
cp config/.env.example .env
# 编辑 .env 文件，填入实际配置
vim .env
```

`.env` 文件必须配置：
```ini
DATABASE_URL=postgresql://family_agent:你的密码@localhost:5432/agent
```

---

## 五、部署后端（FastAPI）

### 5.1 使用 Python 项目管理器（推荐）

宝塔 → **软件商店** → **Python 项目管理器** → **安装**

1. **添加项目**：
   - **项目名称**: `family-agent-backend`
   - **Python 版本**: 3.11
   - **项目路径**: `/www/wwwroot/family-agent/`
   - **启动文件**: `backend/main.py`
   - **框架**: FastAPI
   - **启动方式**: uvicorn
   - **监听端口**: `8000`

2. **安装依赖**：
   项目管理器会自动读取 `backend/requirements.txt` 安装

3. **环境变量**：
   在项目管理器的"环境变量"中添加：
   ```
   DATABASE_URL=postgresql://family_agent:密码@localhost:5432/agent
   ```

4. **启动项目**，检查运行状态和日志

### 5.2 使用 Supervisor 手动管理（替代方案）

```bash
# 安装 Supervisor
pip install supervisor

# 创建配置
cat > /etc/supervisor/conf.d/family-agent.conf << 'EOF'
[program:family-agent]
command=/www/wwwroot/family-agent/venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000 --workers 4
directory=/www/wwwroot/family-agent
user=root
autostart=true
autorestart=true
startsecs=5
startretries=3
stdout_logfile=/www/wwwroot/family-agent/logs/backend.log
stderr_logfile=/www/wwwroot/family-agent/logs/backend.err.log
environment=DATABASE_URL="postgresql://family_agent:密码@localhost:5432/agent"
EOF

# 创建日志目录
mkdir -p /www/wwwroot/family-agent/logs

# 重新加载并启动
supervisorctl reread
supervisorctl update
supervisorctl start family-agent
```

### 5.3 验证后端
```bash
curl http://127.0.0.1:8000/health
# 返回: {"status":"ok","service":"family-agent-api"}
curl http://127.0.0.1:8000/
# 返回: {"message":"家庭智能管家 API 运行中","version":"2.0.0",...}
```

---

## 六、部署前端（React）

### 6.1 安装依赖并构建
```bash
cd /www/wwwroot/family-agent/frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 构建产物在 frontend/dist/
```

### 6.2 预览构建结果
```bash
# 检查 dist 目录
ls -la dist/
# 应有 index.html 和 assets/ 目录
```

---

## 七、配置 Nginx 反向代理

### 7.1 创建网站

宝塔 → **网站** → **添加站点**：
- **域名**: 你的域名 或 服务器公网 IP
- **根目录**: `/www/wwwroot/family-agent/frontend/dist`
- **PHP**: 纯静态
- **提交创建**

### 7.2 修改 Nginx 配置

在网站设置 → **配置文件** 中，替换为以下内容：

```nginx
server {
    listen 80;
    server_name 你的域名或IP;
    
    # 前端静态文件
    root /www/wwwroot/family-agent/frontend/dist;
    index index.html;
    
    # 开启 gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    # 后端 API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持（聊天功能用）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }
    
    # 静态资源缓存
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # 前端路由（SPA 支持）
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # 访问日志
    access_log /www/wwwroot/family-agent/logs/nginx_access.log;
    error_log /www/wwwroot/family-agent/logs/nginx_error.log;
}
```

### 7.3 重载 Nginx
```bash
nginx -t          # 测试配置
nginx -s reload   # 重载配置
```

---

## 八、配置 HTTPS（可选但推荐）

宝塔面板 → **网站** → **SSL** → **Let's Encrypt** → 申请免费证书

---

## 九、启动顺序与验证

### 9.1 完整启动顺序
1. PostgreSQL 数据库已运行
2. 后端（FastAPI）进程已启动
3. Nginx 已配置并重载
4. 前端已构建到 dist 目录

### 9.2 验证步骤
```bash
# 1. 验证数据库
psql -U family_agent -d agent -h localhost -c "SELECT 1"

# 2. 验证后端
curl http://127.0.0.1:8000/health

# 3. 验证前端+Nginx
curl http://你的域名或IP/
# 应返回 index.html 内容

# 4. 验证 API 代理
curl http://你的域名或IP/api/health
# 应返回 {"status":"ok","service":"family-agent-api"}
```

### 9.3 浏览器访问
- 用浏览器打开 `http://你的域名或IP/`
- 应该看到家庭智能管家的登录页面
- 功能包括：工作台、智能对话、成员管理、购物清单等

---

## 十、常用维护命令

```bash
# 查看后端日志（Python 项目管理器）
# 在宝塔面板的 Python 项目管理器中查看运行日志

# 或 Supervisor 日志
tail -f /www/wwwroot/family-agent/logs/backend.log

# 查看 Nginx 日志
tail -f /www/wwwroot/family-agent/logs/nginx_access.log
tail -f /www/wwwroot/family-agent/logs/nginx_error.log

# 重启后端
supervisorctl restart family-agent

# 重启 Nginx
nginx -s reload

# 更新前端
cd /www/wwwroot/family-agent/frontend
git pull
npm install
npm run build
```

---

## 十一、问题排查

### 后端无法启动
```bash
# 检查 Python 版本
python3 --version  # 需要 >= 3.10

# 手动启动测试
cd /www/wwwroot/family-agent
source venv/bin/activate
DATABASE_URL="postgresql://..." python -c "from backend.main import app; print('OK')"

# 查看详细错误
supervisorctl tail family-agent stderr
```

### 数据库连接失败
```bash
# 检查 PostgreSQL 是否运行
systemctl status postgresql

# 测试连接
psql -U family_agent -d agent -h localhost

# 检查 pg_hba.conf 认证方式
cat /www/server/pgsql/data/pg_hba.conf | grep local
```

### 前端接口 502
- 检查后端是否运行: `curl http://127.0.0.1:8000/health`
- 检查 Nginx 配置中的 `proxy_pass` 地址是否正确
- 查看 Nginx 错误日志

### WebSocket 连接失败
- 确认 Nginx 配置中包含 WebSocket 升级头
- 检查宝塔安全组是否放行了相关端口
