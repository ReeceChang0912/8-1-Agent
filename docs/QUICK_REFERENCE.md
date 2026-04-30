# 🏡 家庭智能管家 - 快速参考卡

## 🚀 一键启动

```bash
# Windows
双击 run.bat

# 或命令行
uv sync
streamlit run main.py
```

访问：http://localhost:8501

---

## 📂 项目结构

```
myAgent/
├── family_agent/          # 核心代码
│   ├── core.py           # Agent引擎
│   ├── role_manager.py   # 角色管理
│   ├── memory_manager.py # 记忆系统
│   ├── knowledge_base.py # 知识库
│   ├── emotion_engine.py # 情感识别
│   ├── llm_adapter.py    # LLM适配
│   ├── shopping_list.py  # 购物清单
│   └── photo_memory.py   # 照片记忆
├── main.py               # Web界面
├── test_agent.py         # 测试脚本
└── data/                 # 数据存储
```

---

## 💡 核心功能速查

### 1️⃣ 添加家庭成员
```python
from family_agent.role_manager import FamilyMember, InteractionStyle

member = FamilyMember(
    name="爸爸",
    role="父亲",
    age=45,
    side="core",
    interaction_style=InteractionStyle.PEER
)
agent.add_member(member)
```

### 2️⃣ 智能对话
```python
response = agent.chat("你好！", user_id="爸爸")
```

### 3️⃣ 添加知识
```python
agent.knowledge_base.add_text(
    text="高血压患者应该...",
    title="高血压护理",
    category="health"
)
```

### 4️⃣ 搜索知识
```python
results = agent.knowledge_base.search("高血压", category="health")
```

### 5️⃣ 购物清单
```python
agent.shopping_list.add_item(
    name="大米",
    quantity="5",
    unit="kg",
    added_by="妈妈"
)
```

### 6️⃣ 照片记忆
```python
agent.photo_memory.add_photo(
    file_path="photos/family.jpg",
    description="全家福",
    people=["爸爸", "妈妈"],
    event="春节"
)
```

---

## 🔧 LLM配置

编辑 `.env` 文件：

```env
# Mock模式（默认）
LLM_PROVIDER=mock

# OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxx

# 通义千问
LLM_PROVIDER=qwen
QWEN_API_KEY=xxx

# Ollama本地
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5
```

---

## 🐳 Docker部署

```bash
# 构建
docker-compose build

# 启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

---

## 📊 常用命令

```bash
# 安装依赖
uv sync

# 运行测试
python test_agent.py
# 或双击 test.bat

# 启动Web
streamlit run main.py
# 或双击 run.bat

# 查看帮助
python -c "from family_agent.core import FamilyAgentCore; help(FamilyAgentCore)"
```

---

## 📖 文档导航

| 需求 | 查看文档 |
|------|----------|
| 新手入门 | QUICKSTART.md |
| 功能详解 | USER_MANUAL.md |
| LLM配置 | LLM_CONFIG.md |
| 部署指南 | DEPLOYMENT.md |
| 技术细节 | PROJECT_SUMMARY.md |
| 开发清单 | CHECKLIST.md |

---

## ❓ 常见问题

**Q: 如何重置数据？**
A: 删除 `data` 文件夹

**Q: 手机能访问吗？**
A: 可以，访问 http://电脑IP:8501

**Q: 如何备份？**
A: 复制 `data` 和 `photos` 文件夹

**Q: LLM失败怎么办？**
A: 自动降级到Mock模式，不影响使用

---

## 🎯 下一步

1. ✅ 体验所有功能
2. ✅ 配置LLM提升质量
3. ✅ 添加家庭成员
4. ✅ 邀请家人使用
5. ⏳ 反馈建议

---

## 📞 获取帮助

- 查看 USER_MANUAL.md
- 查阅 DEPLOYMENT.md
- 提交 GitHub Issue

---

**祝使用愉快！** 🏡💕
