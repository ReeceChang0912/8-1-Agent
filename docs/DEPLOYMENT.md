# 家庭智能管家 - 部署指南

## 📦 部署方案选择

### 方案对比

| 方案 | 难度 | 成本 | 适用场景 |
|------|------|------|----------|
| 本地运行 | ⭐ | 免费 | 个人测试、开发 |
| Docker部署 | ⭐⭐ | 免费 | 家庭服务器、长期使用 |
| 云服务器 | ⭐⭐⭐ | ¥50-200/月 | 远程访问、多地点使用 |
| NAS部署 | ⭐⭐ | 硬件成本 | 已有NAS设备 |

---

## 🖥️ 方案一：本地运行（最简单）

### 适用场景
- 首次体验
- 开发测试
- 单机使用

### 步骤

1. **安装Python 3.13+**
   ```bash
   # 检查Python版本
   python --version
   ```

2. **安装uv包管理器**
   ```bash
   # Windows (PowerShell)
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **安装依赖**
   ```bash
   cd E:\myAgent
   uv sync
   ```

4. **启动应用**
   ```bash
   streamlit run main.py
   ```

5. **访问**
   浏览器打开：http://localhost:8501

### 优点
✅ 最简单，无需配置  
✅ 完全免费  
✅ 数据本地存储

### 缺点
❌ 只能在本机访问  
❌ 需要手动启动  
❌ 关闭电脑后不可用

---

## 🐳 方案二：Docker部署（推荐）

### 适用场景
- 家庭服务器
- 7x24小时运行
- 局域网内多设备访问

### 前置要求
- 安装Docker Desktop：https://www.docker.com/products/docker-desktop

### 步骤

1. **准备环境文件**
   ```bash
   # 复制示例配置
   cp .env.example .env
   
   # 编辑配置（可选）
   # 添加LLM API Key等
   ```

2. **构建镜像**
   ```bash
   docker-compose build
   ```

3. **启动服务**
   ```bash
   docker-compose up -d
   ```

4. **查看日志**
   ```bash
   docker-compose logs -f
   ```

5. **访问**
   - 本机：http://localhost:8501
   - 局域网：http://你的IP:8501

6. **管理命令**
   ```bash
   # 停止服务
   docker-compose down
   
   # 重启服务
   docker-compose restart
   
   # 更新服务
   docker-compose pull
   docker-compose up -d --build
   
   # 查看状态
   docker-compose ps
   ```

### 数据备份
```bash
# 备份数据目录
tar -czf family-agent-backup-$(date +%Y%m%d).tar.gz data/ photos/

# 恢复数据
tar -xzf family-agent-backup-20260430.tar.gz
```

### 优点
✅ 环境隔离，干净  
✅ 易于部署和更新  
✅ 自动重启  
✅ 资源限制可控

### 缺点
❌ 需要学习Docker  
❌ 初次配置稍复杂

---

## ☁️ 方案三：云服务器部署

### 适用场景
- 需要远程访问
- 家庭成员分布多地
- 有公网IP需求

### 推荐服务商
- 阿里云 ECS：https://www.aliyun.com
- 腾讯云 CVM：https://cloud.tencent.com
- 华为云：https://www.huaweicloud.com

### 配置建议
- CPU：2核
- 内存：4GB
- 硬盘：50GB SSD
- 带宽：5Mbps
- 系统：Ubuntu 22.04 LTS

### 步骤

1. **购买服务器**
   - 选择上述配置
   - 记录公网IP

2. **连接服务器**
   ```bash
   ssh root@你的服务器IP
   ```

3. **安装Docker**
   ```bash
   # Ubuntu
   curl -fsSL https://get.docker.com | bash
   sudo systemctl enable docker
   sudo systemctl start docker
   
   # 安装docker-compose
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

4. **上传代码**
   ```bash
   # 方法1：Git克隆
   git clone <你的仓库地址>
   cd myAgent
   
   # 方法2：SCP上传
   scp -r myAgent root@服务器IP:/root/
   ```

5. **配置环境变量**
   ```bash
   nano .env
   # 填写LLM API Key等配置
   ```

6. **启动服务**
   ```bash
   docker-compose up -d
   ```

7. **配置防火墙**
   ```bash
   # 开放8501端口
   sudo ufw allow 8501/tcp
   sudo ufw reload
   ```

8. **访问**
   http://服务器公网IP:8501

### 安全加固

1. **修改默认端口**
   ```yaml
   # docker-compose.yml
   ports:
     - "自定义端口:8501"
   ```

2. **添加HTTPS**
   ```bash
   # 使用Let's Encrypt免费证书
   sudo apt install certbot
   sudo certbot certonly --standalone -d 你的域名
   ```

3. **设置密码保护**
   - 在Streamlit中添加认证
   - 或使用Nginx反向代理+Basic Auth

### 成本估算
- 阿里云：约 ¥100-200/月
- 腾讯云：约 ¥80-150/月
- 学生优惠：约 ¥10-30/月

### 优点
✅ 随时随地访问  
✅ 不受本地网络限制  
✅ 专业运维

### 缺点
❌ 需要付费  
❌ 需要域名备案（国内）  
❌ 数据安全需注意

---

## 💾 方案四：NAS部署

### 适用场景
- 已有NAS设备
- 家庭数据中心
- 大容量存储需求

### 支持的NAS
- 群晖 (Synology)
- 威联通 (QNAP)
- 极空间
- Unraid

### 以群晖为例

1. **安装Docker套件**
   - 打开套件中心
   - 搜索并安装"Docker"

2. **上传项目文件**
   - 通过File Station上传myAgent文件夹

3. **创建容器**
   ```bash
   # SSH连接到NAS
   ssh admin@nas-ip
   
   # 进入项目目录
   cd /volume1/myAgent
   
   # 构建并运行
   docker-compose up -d
   ```

4. **配置端口转发**
   - 控制面板 > 外部访问 > 路由器配置
   - 转发8501端口

5. **访问**
   http://NAS-IP:8501

### 优点
✅ 利用现有设备  
✅ 大容量存储  
✅ 与其他家庭服务集成

### 缺点
❌ 需要NAS硬件  
❌ 性能受NAS限制

---

## 🔧 高级配置

### 1. 反向代理（Nginx）

```nginx
server {
    listen 80;
    server_name family.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 2. 自动备份脚本

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/family-agent"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据
tar -czf $BACKUP_DIR/data_$DATE.tar.gz ./data
tar -czf $BACKUP_DIR/photos_$DATE.tar.gz ./photos

# 保留最近7天的备份
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "备份完成: $DATE"
```

设置定时任务：
```bash
# 每天凌晨2点备份
0 2 * * * /path/to/backup.sh
```

### 3. 监控和告警

使用Prometheus + Grafana监控：
- CPU使用率
- 内存使用
- 磁盘空间
- 服务状态

---

## 🚨 故障排查

### 问题1：无法访问Web界面

**检查清单**：
```bash
# 1. 检查服务是否运行
docker-compose ps

# 2. 查看日志
docker-compose logs

# 3. 检查端口占用
netstat -tulpn | grep 8501

# 4. 检查防火墙
sudo ufw status
```

### 问题2：数据丢失

**解决方案**：
```bash
# 检查卷挂载
docker inspect family-agent | grep Mounts

# 确保数据目录权限正确
chmod -R 755 data/ photos/
```

### 问题3：内存不足

**优化方案**：
```yaml
# docker-compose.yml
services:
  family-agent:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 512M
```

---

## 📊 性能优化

### 1. 数据库优化
- 定期清理旧记忆
- 压缩向量数据库
- 使用SSD存储

### 2. 缓存策略
- Redis缓存常用查询
- CDN加速静态资源
- 浏览器缓存

### 3. 资源限制
```yaml
# 限制CPU和内存
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 2G
```

---

## 🔐 安全建议

1. **定期更新**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

2. **强密码**
   - 使用密码管理器
   - 启用双因素认证

3. **网络隔离**
   - 使用VLAN隔离IoT设备
   - 限制外网访问

4. **数据加密**
   - HTTPS传输
   - 敏感数据加密存储

5. **审计日志**
   ```bash
   # 查看访问日志
   docker-compose logs | grep "access"
   ```

---

## 📞 技术支持

遇到问题？

1. 查看日志：`docker-compose logs -f`
2. 查阅文档：README.md
3. 提交Issue：GitHub Issues
4. 社区讨论：Discussions

---

## ✅ 部署检查清单

- [ ] 选择部署方案
- [ ] 准备服务器/环境
- [ ] 安装依赖（Docker/Python）
- [ ] 配置环境变量
- [ ] 启动服务
- [ ] 测试访问
- [ ] 配置备份
- [ ] 设置监控
- [ ] 安全加固
- [ ] 文档记录

---

**祝部署顺利！** 🎉

如有问题，欢迎反馈。
