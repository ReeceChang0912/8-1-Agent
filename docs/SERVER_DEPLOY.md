# 家庭智能管家 - 服务器部署指南

## 📋 目录

1. [快速部署（推荐）](#快速部署推荐)
2. [Linux 服务器部署](#linux-服务器部署)
3. [Docker 部署](#docker-部署)
4. [云服务器部署](#云服务器部署)
5. [安全配置](#安全配置)
6. [性能优化](#性能优化)

---

## 🚀 快速部署（推荐）

### 方案一：使用 systemd 服务（Linux）

#### 1. 上传代码到服务器

```bash
# 在本地打包
cd E:\myAgent
tar -czf family-agent.tar.gz ./*

# 上传到服务器
scp family-agent.tar.gz user@your-server:/opt/

# 在服务器上解压
ssh user@your-server
cd /opt
tar -xzf family-agent.tar.gz
mv family-agent myagent
cd myagent
```

#### 2. 安装依赖

```bash
# 安装 Python 3.13+
sudo apt update
sudo apt install python3.13 python3.13-venv python3.13-dev

# 创建虚拟环境
python3.13 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install streamlit chromadb sentence-transformers langchain langchain-community langchain-chroma pyttsx3 SpeechRecognition Pillow requests schedule python-dotenv pydantic openai dashscope
```

#### 3. 配置环境变量

```bash
# 编辑 .env 文件
nano .env

# 填入你的配置
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-api-key
```

#### 4. 创建 systemd 服务

```bash
sudo nano /etc/systemd/system/family-agent.service
```

粘贴以下内容：

```ini
[Unit]
Description=Family Smart Agent
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/myagent
Environment="PATH=/opt/myagent/.venv/bin"
ExecStart=/opt/myagent/.venv/bin/streamlit run main.py --server.address=0.0.0.0 --server.port=8501
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 5. 启动服务

```bash
# 重载 systemd
sudo systemctl daemon-reload

# 启用开机自启
sudo systemctl enable family-agent

# 启动服务
sudo systemctl start family-agent

# 查看状态
sudo systemctl status family-agent

# 查看日志
sudo journalctl -u family-agent -f
```

#### 6. 配置防火墙

```bash
# 开放 8501 端口
sudo ufw allow 8501/tcp
sudo ufw reload
```

现在访问 `http://your-server-ip:8501` 即可！

---

## 🐧 Linux 服务器部署

### 完整步骤

```bash
# 1. 更新系统
sudo apt update && sudo apt upgrade -y

# 2. 安装必要软件
sudo apt install -y python3.13 python3.13-venv git nginx certbot

# 3. 克隆代码
cd /opt
git clone https://github.com/your-username/family-agent.git
cd family-agent

# 4. 设置虚拟环境
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 5. 配置环境变量
cp .env.example .env
nano .env  # 编辑配置

# 6. 创建数据目录
mkdir -p data photos
chown -R www-data:www-data data photos

# 7. 配置 Nginx（反向代理）
sudo nano /etc/nginx/sites-available/family-agent
```

Nginx 配置：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/family-agent /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 8. 配置 HTTPS（Let's Encrypt）
sudo certbot --nginx -d your-domain.com

# 9. 启动应用
sudo systemctl start family-agent
```

---

## 🐳 Docker 部署

### 方法一：使用现有 Dockerfile

项目已包含 `Dockerfile` 和 `docker-compose.yml`。

```bash
# 1. 构建镜像
docker build -t family-agent .

# 2. 运行容器
docker run -d \
  --name family-agent \
  -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/photos:/app/photos \
  -e LLM_PROVIDER=deepseek \
  -e DEEPSEEK_API_KEY=sk-your-key \
  --restart unless-stopped \
  family-agent
```

### 方法二：使用 Docker Compose（推荐）

```bash
# 1. 编辑 docker-compose.yml
nano docker-compose.yml

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 停止服务
docker-compose down
```

---

## ☁️ 云服务器部署

### 阿里云 ECS

```bash
# 1. 购买 ECS 实例（推荐配置）
# - CPU: 2核
# - 内存: 4GB
# - 系统: Ubuntu 22.04
# - 带宽: 5Mbps

# 2. 安全组配置
# 开放端口: 80, 443, 8501

# 3. 连接服务器
ssh root@your-ecs-ip

# 4. 按照 Linux 部署步骤操作
```

### 腾讯云 CVM

类似阿里云，注意配置安全组规则。

### AWS EC2

```bash
# 1. 启动 EC2 实例
# AMI: Ubuntu Server 22.04 LTS
# Type: t3.medium

# 2. 配置安全组
# Inbound rules: HTTP (80), HTTPS (443), Custom TCP (8501)

# 3. 部署应用
# 同 Linux 部署步骤
```

---

## 🔒 安全配置

### 1. 添加身份验证

创建 `.streamlit/secrets.toml`：

```toml
[general]
password = "your_secure_password"
```

或在 `main.py` 中添加：

```python
import streamlit as st

# 简单的密码保护
def check_password():
    def password_entered():
        if st.session_state["password"] == "your_password":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "Password",
            type="password",
            on_change=password_entered,
            key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "Password",
            type="password",
            on_change=password_entered,
            key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        return True

if check_password():
    # 你的应用代码
    main()
```

### 2. 配置 HTTPS

```bash
# 使用 Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加：0 0 1 * * certbot renew --quiet
```

### 3. 防火墙配置

```bash
# 启用 UFW
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw allow 8501/tcp
```

### 4. 定期备份

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/family-agent"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份数据
tar -czf $BACKUP_DIR/data_$DATE.tar.gz /opt/myagent/data
tar -czf $BACKUP_DIR/photos_$DATE.tar.gz /opt/myagent/photos

# 保留最近7天的备份
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

设置定时任务：

```bash
crontab -e
# 每天凌晨2点备份
0 2 * * * /opt/myagent/backup.sh
```

---

## ⚡ 性能优化

### 1. 使用 Gunicorn

```bash
# 安装 gunicorn
pip install gunicorn

# 创建启动脚本
cat > run_gunicorn.sh << EOF
#!/bin/bash
gunicorn -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8501 \
  --workers 4 \
  --timeout 120 \
  main:app
EOF

chmod +x run_gunicorn.sh
```

### 2. 启用缓存

在 `.streamlit/config.toml` 中：

```toml
[server]
maxUploadSize = 50
enableStaticServing = true

[browser]
gatherUsageStats = false
```

### 3. 数据库优化

```bash
# 定期清理 ChromaDB
# 添加定时任务清理旧数据
```

### 4. 监控

```bash
# 安装监控工具
sudo apt install htop iotop nethogs

# 查看资源使用
htop

# 监控网络
nethogs
```

---

## 📊 监控和维护

### 查看日志

```bash
# systemd 日志
sudo journalctl -u family-agent -f

# Docker 日志
docker logs -f family-agent

# Nginx 日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 重启服务

```bash
# systemd
sudo systemctl restart family-agent

# Docker
docker restart family-agent
```

### 更新应用

```bash
# 1. 拉取最新代码
cd /opt/myagent
git pull

# 2. 安装新依赖
source .venv/bin/activate
pip install -r requirements.txt

# 3. 重启服务
sudo systemctl restart family-agent
```

---

## ❓ 常见问题

### Q: 端口被占用怎么办？

A: 修改端口
```bash
# 修改 .streamlit/config.toml
[server]
port = 8502

# 或运行时指定
streamlit run main.py --server.port=8502
```

### Q: 内存不足怎么办？

A: 增加 swap 空间
```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Q: 如何查看实时日志？

A: 
```bash
# systemd
sudo journalctl -u family-agent -f --since "10 minutes ago"

# Docker
docker logs -f --tail 100 family-agent
```

---

## 🎯 推荐部署方案

| 场景 | 推荐方案 | 难度 | 成本 |
|------|---------|------|------|
| 个人使用 | systemd + Nginx | ⭐⭐ | 低 |
| 小团队 | Docker Compose | ⭐⭐⭐ | 中 |
| 生产环境 | K8s + CI/CD | ⭐⭐⭐⭐⭐ | 高 |
| 测试环境 | 直接运行 | ⭐ | 最低 |

**对于大多数用户，推荐使用 systemd + Nginx 方案！**

---

## 📞 需要帮助？

如有部署问题，请检查：
1. 服务器防火墙设置
2. 端口是否正确开放
3. 依赖是否完整安装
4. 环境变量是否正确配置
5. 查看日志文件定位错误

祝部署顺利！🎉
