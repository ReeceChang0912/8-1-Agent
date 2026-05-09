FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY backend/requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 创建数据目录
RUN mkdir -p data/memory data/knowledge_docs photos

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK CMD curl --fail http://localhost:8000/health || exit 1

# 启动命令（使用 uvicorn 运行 FastAPI）
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
