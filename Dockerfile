# ===== 第一阶段：构建前端 =====
FROM node:20-alpine AS web-builder

WORKDIR /repo/apps/web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci
COPY apps/web/ ./
RUN npm run build

# ===== 第二阶段：后端运行环境 =====
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc curl \
    && rm -rf /var/lib/apt/lists/*

# 复制后端依赖
COPY apps/backend/requirements.txt ./apps/backend/requirements.txt
RUN pip install --no-cache-dir -r ./apps/backend/requirements.txt

# 复制代码
COPY . .

# 从前端构建产物目录复制到 apps/web/dist
COPY --from=web-builder /repo/apps/web/dist ./apps/web/dist

# 创建数据目录
RUN mkdir -p data/photos_frontend photos

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK CMD curl --fail http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "backend.main:app", "--app-dir", "apps", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
