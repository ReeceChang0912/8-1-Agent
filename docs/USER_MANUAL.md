# 🏡 家庭智能管家 - 完整使用手册

## 📖 目录

1. [快速开始](#快速开始)
2. [功能详解](#功能详解)
3. [LLM配置](#llm配置)
4. [高级功能](#高级功能)
5. [部署指南](#部署指南)
6. [常见问题](#常见问题)

---

## 🚀 快速开始

### 3分钟上手

```bash
# 1. 安装依赖
uv sync

# 2. 运行测试（可选）
python test_agent.py

# 3. 启动应用
streamlit run main.py

# 4. 浏览器访问
http://localhost:8501
```

或者双击 `run.bat` 一键启动！

---

## 💡 功能详解

### 1. 智能对话 💬

**基本用法**：
- 在聊天框输入消息
- 系统自动识别情绪并回应
- 支持上下文记忆

**示例对话**：
```
用户: 你好！
助手: 你好！很高兴为你服务。

用户: 我今天有点担心孩子的学习
助手: [检测到焦虑情绪] 别太担心，事情总会解决的...

用户: 帮我设置一个生日提醒
助手: 好的，请告诉我具体日期和详情。
```

**技巧**：
- 左侧可选择当前用户身份
- 不同身份有不同的交互风格
- 系统会记住对话历史

---

### 2. 家庭成员管理 👨‍👩‍👧‍👦

**添加成员**：
1. 点击"👨‍👩‍👧‍👦 家庭成员"
2. 填写信息：
   - 姓名、角色、年龄
   - 家庭方（小家庭/男方/女方）
   - 交互风格
   - 权限等级
3. 点击"添加成员"

**交互风格说明**：
- **平等交流**：适合夫妻之间
- **童趣模式**：对孩子使用，语言简单有趣
- **长辈模式**：对老人使用，尊敬耐心
- **正式模式**：正式场合使用

**权限等级**：
- **管理员**：完全控制（建议夫妻）
- **普通成员**：可添加日程等
- **访客**：只读权限
- **儿童**：受限访问

---

### 3. 日程管理 📅

**设置提醒**：
1. 点击"📅 日程管理"
2. 输入事件标题
3. 选择日期和时间
4. 点击"设置提醒"

**查看提醒**：
- 切换到"查看提醒"标签
- 显示所有 upcoming 事件

**应用场景**：
- 生日提醒
- 纪念日提醒
- 用药提醒
- 会议提醒
- 探亲计划

---

### 4. 知识库管理 📚

**添加知识**：
1. 点击"📚 知识库"
2. 选择"添加文档"标签
3. 输入：
   - 标题
   - 内容（支持长文本）
   - 分类（健康/理财/教育等）
4. 点击"添加到知识库"

**搜索知识**：
1. 切换到"搜索知识"标签
2. 输入问题
3. 选择分类（可选）
4. 点击"搜索"

**支持的分类**：
- health：健康医疗
- finance：理财规划
- relationship：家庭关系
- education：子女教育
- travel：旅游攻略
- cooking：烹饪食谱
- legal：法律常识
- general：通用知识

**示例**：
```
添加：高血压护理指南
搜索：高血压要注意什么？
结果：[从知识库检索相关信息]
```

---

### 5. 统计信息 📊

查看系统状态：
- 家庭成员数量
- 记忆条数
- 知识文档数
- 各类统计图表

---

## 🔧 LLM配置

### 选择LLM提供商

编辑 `.env` 文件：

```env
# Mock模式（默认，无需配置）
LLM_PROVIDER=mock

# OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key

# 通义千问
LLM_PROVIDER=qwen
QWEN_API_KEY=your-key

# Ollama（本地）
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5
```

详细说明见：[LLM_CONFIG.md](LLM_CONFIG.md)

---

## 🌟 高级功能

### 购物清单 🛒

**Python API使用**：

```python
from family_agent.core import FamilyAgentCore

agent = FamilyAgentCore()

# 添加购物项
agent.shopping_list.add_item(
    name="大米",
    quantity="5",
    unit="kg",
    category="food",
    added_by="妈妈"
)

# 查看清单
items = agent.shopping_list.get_items(purchased=False)
for item in items:
    print(f"- {item.name}: {item.quantity}{item.unit}")

# 标记已购买
agent.shopping_list.mark_purchased("大米")

# 获取摘要
summary = agent.shopping_list.get_shopping_summary()
print(f"完成率: {summary['completion_rate']:.0%}")
```

---

### 照片记忆 📸

**Python API使用**：

```python
# 添加照片
photo_id = agent.photo_memory.add_photo(
    file_path="photos/family.jpg",
    description="全家福",
    tags=["家庭", "聚会"],
    people=["爸爸", "妈妈", "小明"],
    event="春节聚会",
    location="老家"
)

# 搜索照片
photos = agent.photo_memory.search_photos(
    query="春节",
    person="奶奶"
)

# 查看去年的今天
today = datetime.now()
memories = agent.photo_memory.get_memories_on_date(
    month=today.month,
    day=today.day
)

# 生成回忆故事
story = agent.photo_memory.generate_memory_story(
    photo_ids=[p.photo_id for p in memories]
)
print(story)
```

---

### 情感识别 ❤️

**自动情绪检测**：

```python
# 检测情绪
result = agent.emotion_engine.detect_emotion("我今天好生气！")
print(f"情绪: {result['primary_emotion'].value}")
print(f"置信度: {result['confidence']:.2f}")

# 生成安抚回应
comfort = agent.emotion_engine.generate_comfort_response(
    emotion=result['primary_emotion'],
    context="工作压力大"
)
print(comfort)

# 沟通建议
advice = agent.emotion_engine.suggest_communication_strategy(
    emotion=result['primary_emotion'],
    relationship="婆婆",
    situation="批评我带孩子的方式"
)
print(advice)
```

---

## 🐳 部署指南

### Docker部署（推荐）

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

详细部署指南见：[DEPLOYMENT.md](DEPLOYMENT.md)

---

### 本地运行

```bash
# 安装依赖
uv sync

# 启动
streamlit run main.py

# 访问
http://localhost:8501
```

---

## ❓ 常见问题

### Q1: 如何重置所有数据？

A: 删除 `data` 文件夹，重启应用即可。

```bash
# Windows
rmdir /s /q data

# Linux/Mac
rm -rf data
```

---

### Q2: 可以用手机访问吗？

A: 可以！确保手机和电脑在同一WiFi，访问：
```
http://电脑IP:8501
```

查看电脑IP：
```bash
# Windows
ipconfig

# Linux/Mac
ifconfig
```

---

### Q3: 如何备份数据？

A: 直接复制 `data` 和 `photos` 文件夹。

```bash
# 备份
cp -r data photos backup_20260430/

# 恢复
cp -r backup_20260430/* .
```

---

### Q4: LLM调用失败怎么办？

A: 系统会自动降级到Mock模式，不影响基本功能。

检查配置：
```bash
# 查看环境变量
cat .env

# 测试API
python -c "from family_agent.llm_adapter import get_llm; llm = get_llm(); print(llm.chat([{'role': 'user', 'content': '你好'}]))"
```

---

### Q5: 如何添加更多工具？

A: 在 `tool_engine.py` 中注册新工具：

```python
self.register_tool(FamilyTool(
    name="my_new_tool",
    description="工具描述",
    func=self._my_function,
    parameters={...}
))
```

---

### Q6: 性能优化建议？

A: 
1. 定期清理旧记忆
2. 限制知识库文档大小
3. 使用SSD存储
4. 增加内存

```python
# 清理记忆
agent.memory_manager.forget_unimportant_memories(threshold=0.2)
```

---

### Q7: 支持哪些文件格式？

A: 
- 知识库：TXT, PDF
- 照片：JPG, PNG, GIF
- 未来会支持：DOCX, MD, CSV

---

### Q8: 如何贡献代码？

A: 
1. Fork 项目
2. 创建特性分支
3. 提交变更
4. 创建 Pull Request

详见：CONTRIBUTING.md（待创建）

---

## 📚 相关文档

- [README.md](README.md) - 项目概述
- [QUICKSTART.md](QUICKSTART.md) - 快速入门
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - 技术总结
- [LLM_CONFIG.md](LLM_CONFIG.md) - LLM配置
- [DEPLOYMENT.md](DEPLOYMENT.md) - 部署指南
- [CHECKLIST.md](CHECKLIST.md) - 开发清单

---

## 🎯 下一步

1. ✅ 完成快速开始
2. ✅ 体验所有功能
3. ✅ 配置LLM提升质量
4. ✅ 部署到服务器
5. ✅ 邀请家人使用
6. ⏳ 反馈建议和改进

---

## 💕 温馨提示

- 定期备份重要数据
- 保护隐私，不要分享敏感信息
- 享受科技带来的便利
- 记得多与家人真实互动哦！

---

**祝使用愉快！** 🏡✨

有问题随时反馈，我们会持续改进。
