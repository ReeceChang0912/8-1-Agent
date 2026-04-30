FROM python:3.13-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY pyproject.toml .

# 安装uv和依赖
RUN pip install uv && \
    uv pip install --system openai dashscope chromadb sentence-transformers langchain langchain-community langchain-chroma streamlit streamlit-chat pyttsx3 SpeechRecognition Pillow requests schedule python-dotenv pydantic

# 复制代码
COPY . .

# 创建数据目录
RUN mkdir -p data/memory data/knowledge_docs photos

# 暴露端口
EXPOSE 8501

# 健康检查
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# 启动命令
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
