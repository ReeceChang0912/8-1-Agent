# DeepSeek LLM 配置指南

## 🎯 概述

DeepSeek 是一个高性能的大语言模型，现已集成到家庭智能管家中。

---

## 📋 配置步骤

### 1. 获取 API Key

访问 [DeepSeek 官网](https://platform.deepseek.com/) 注册并获取 API Key。

### 2. 设置环境变量

创建或编辑 `.env` 文件（在项目根目录）：

```bash
# LLM 提供商选择
LLM_PROVIDER=deepseek

# DeepSeek 配置
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
```

### 3. 安装依赖

DeepSeek 使用 OpenAI 兼容接口，所以只需要 `openai` 库（已安装）。

---

## ⚙️ 配置选项

### 环境变量说明

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `LLM_PROVIDER` | LLM 提供商 | `mock` |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | 必需 |
| `DEEPSEEK_BASE_URL` | API 基础 URL | `https://api.deepseek.com/v1` |
| `DEEPSEEK_MODEL` | 模型名称 | `deepseek-chat` |

### 可用模型

- `deepseek-chat` - 通用对话模型（推荐）
- `deepseek-coder` - 代码专用模型
- `deepseek-reasoner` - 推理增强模型

---

## 🚀 使用方法

### 方法一：环境变量配置

在 `.env` 文件中设置：

```bash
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxx
```

然后重启应用即可。

### 方法二：代码中指定

```python
from family_agent.llm_adapter import get_llm

# 使用 DeepSeek
llm = get_llm(provider="deepseek")
```

---

## 💰 费用说明

DeepSeek 提供免费的 API 额度，具体请参考官方定价页面。

---

## 🔍 验证配置

运行测试脚本验证配置是否正确：

```python
from family_agent.llm_adapter import get_llm

llm = get_llm(provider="deepseek")

response = llm.generate_response(
    system_prompt="你是一个助手",
    user_message="你好"
)

print(response)
```

如果看到正常回复，说明配置成功！

---

## ❓ 常见问题

### Q: 如何切换到其他 LLM？

A: 修改 `.env` 文件中的 `LLM_PROVIDER`：
- `openai` - OpenAI GPT
- `qwen` - 通义千问
- `deepseek` - DeepSeek
- `ollama` - 本地模型
- `mock` - 模拟模式

### Q: DeepSeek 和 OpenAI 有什么区别？

A: DeepSeek 使用 OpenAI 兼容的 API 接口，所以代码实现类似，但价格和性能可能不同。

### Q: API 调用失败怎么办？

A: 检查：
1. API Key 是否正确
2. 网络连接是否正常
3. 账户余额是否充足
4. 查看控制台错误信息

---

## 📞 技术支持

如有问题，请访问：
- DeepSeek 官方文档：https://platform.deepseek.com/docs
- 项目 Issues：提交问题反馈

---

**配置完成后，享受 DeepSeek 的强大能力吧！** 🚀
