# D 盘安装完整指南

## 🎯 问题诊断

根据你的检查结果：
- ✅ Python 在 C 盘（无法移动）
- ✅ pip 在 C 盘（无法移动）
- ❌ 包还没安装
- ❌ 环境变量未设置

## 📋 解决方案（3步）

### ✅ 步骤 1：运行完整配置脚本

**双击运行** `complete_d_setup.bat`

这会：
1. 在 D 盘创建所有必要目录
2. 设置环境变量
3. **安装所有包到 D:\myAgent\python_packages**
4. 缓存保存到 D:\myAgent\.cache

⏱️ 这个过程可能需要 5-10 分钟，请耐心等待！

### ✅ 步骤 2：验证安装

**双击运行** `check_install.bat`

应该看到：
```
chromadb: D:\myAgent\python_packages\chromadb\...
streamlit: D:\myAgent\python_packages\streamlit\...
UV_CACHE_DIR=D:\myAgent\.cache
```

### ✅ 步骤 3：启动应用

**双击运行** `run.bat`

现在所有东西都在 D 盘了！

---

## 📂 D 盘目录结构

```
D:\myAgent\
├── .cache/              # 安装包缓存（~2GB）
│   └── pip/
├── python_packages/     # Python 包（~1GB）
│   ├── chromadb/
│   ├── streamlit/
│   ├── langchain/
│   └── ...
├── data/                # 应用数据
│   ├── members.json
│   ├── memory/
│   └── knowledge_db/
└── photos/              # 照片
```

---

## 💡 工作原理

虽然我们没法把 Python 本身移到 D 盘，但我们可以：

1. **包安装在 D 盘** - 使用 `--target` 参数
2. **缓存在 D 盘** - 设置 `PIP_CACHE_DIR`
3. **数据在 D 盘** - 代码自动检测并使用 D 盘

这样 C 盘只保留 Python 解释器（很小），大头都在 D 盘！

---

## ⚠️ 重要提示

### 每次启动都会自动设置

`run.bat` 和 `test.bat` 已经配置好，会自动：
- 设置 `PYTHONPATH=D:\myAgent\python_packages`
- 设置缓存目录到 D 盘

所以你只需要双击运行即可！

### 如果遇到问题

1. **确认 D 盘有足够空间**（至少 5GB）
2. **以管理员身份运行**脚本（如果需要）
3. **检查网络连接**（下载包需要）

---

## 🔍 验证清单

运行完 `complete_d_setup.bat` 后，检查：

- [ ] D:\myAgent\python_packages 文件夹存在
- [ ] D:\myAgent\.cache 文件夹存在
- [ ] D:\myAgent\data 文件夹存在
- [ ] 运行 `check_install.bat` 能看到包路径在 D 盘
- [ ] 运行 `test.bat` 测试通过
- [ ] 运行 `run.bat` 能启动 Web 界面

---

## 🚀 现在开始！

**双击运行** `complete_d_setup.bat` 

然后喝杯咖啡，等它安装完成 ☕

完成后就可以正常使用啦！🎉
