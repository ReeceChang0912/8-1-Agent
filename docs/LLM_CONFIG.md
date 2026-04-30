# LLM 配置指南

## 📌 支持的LLM提供商

### 1. OpenAI (GPT-4/GPT-3.5)

**优点**：质量最高，生态完善  
**缺点**：需要付费，国内访问可能不稳定

**配置步骤**：

1. 注册OpenAI账号：https://platform.openai.com
2. 获取API Key
3. 在 `.env` 文件中添加：

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-api-key-here
```

**费用**：约 $0.002/1K tokens（GPT-3.5）


### 2. 阿里云通义千问 (Qwen)

**优点**：中文优化好，价格实惠，国内稳定  
**缺点**：需要实名认证

**配置步骤**：

1. 注册阿里云账号：https://dashscope.aliyun.com
2. 开通DashScope服务
3. 获取API Key
4. 在 `.env` 文件中添加：

```env
LLM_PROVIDER=qwen
QWEN_API_KEY=your-api-key-here
```

**费用**：约 ¥0.008/1K tokens（qwen-turbo）


### 3. Ollama (本地模型)

**优点**：完全免费，隐私最好，离线可用  
**缺点**：需要本地GPU，模型质量略低

**配置步骤**：

1. 安装Ollama：https://ollama.ai
2. 下载模型：
   ```bash
   ollama pull qwen2.5
   # 或
   ollama pull llama3.2
   ```
3. 启动Ollama服务
4. 在 `.env` 文件中添加：

```env
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5
```

**费用**：免费（需要硬件）


### 4. Mock模式（默认）

**优点**：无需配置，立即可用  
**缺点**：回复简单，基于规则

**配置**：

```env
LLM_PROVIDER=mock
```

不需要任何API Key。


## 🎯 推荐配置

### 开发测试阶段
```env
LLM_PROVIDER=mock
```

### 生产环境（国内）
```env
LLM_PROVIDER=qwen
QWEN_API_KEY=your-key
```

### 生产环境（国际）
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key
```

### 隐私优先
```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5
```


## 🔧 切换LLM提供商

修改 `.env` 文件中的 `LLM_PROVIDER` 即可，无需修改代码。

系统会自动检测并切换到对应的LLM。


## 💡 使用建议

1. **先用Mock模式**测试基本功能
2. **再集成真实LLM**提升对话质量
3. **根据预算选择**合适的提供商
4. **考虑隐私需求**决定是否用本地模型


## ⚠️ 注意事项

- API Key不要提交到Git仓库
- 定期检查API使用情况避免超额
- 建议设置使用限额
- 保留Mock模式作为降级方案


## 📊 性能对比

| 提供商 | 响应速度 | 对话质量 | 成本 | 隐私 |
|--------|---------|---------|------|------|
| GPT-4 | 快 | ⭐⭐⭐⭐⭐ | 高 | 中 |
| GPT-3.5 | 很快 | ⭐⭐⭐⭐ | 中 | 中 |
| Qwen | 快 | ⭐⭐⭐⭐ | 低 | 中 |
| Ollama | 中 | ⭐⭐⭐ | 免费 | 高 |
| Mock | 很快 | ⭐⭐ | 免费 | 高 |


## 🚀 快速开始

1. 复制 `.env.example` 为 `.env`
2. 选择LLM提供商并填写API Key
3. 重启应用即可生效

就这么简单！
