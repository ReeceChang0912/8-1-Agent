# 从 C 盘迁移到 D 盘完整指南

## 🎯 目标

删除 C 盘的所有安装，将所有数据和应用迁移到 D 盘。

---

## 📋 迁移步骤（4步）

### ✅ 步骤 1：清理 C 盘安装

**双击运行** `clean_c_drive.bat`

这会：
- 卸载 C 盘的 Python 包
- 清理 pip 缓存
- 清理 UV 缓存
- 释放 C 盘空间

### ✅ 步骤 2：配置 D 盘

**双击运行** `setup_d_drive.bat`

这会：
- 在 D 盘创建目录结构
- 设置环境变量

### ✅ 步骤 3：安装到 D 盘

**双击运行** `install.bat`

这会：
- 安装所有依赖到 D 盘
- 使用 D 盘缓存

### ✅ 步骤 4：启动应用

**双击运行** `run.bat`

---

## 🗑️ 手动清理（可选）

如果自动脚本不起作用，可以手动清理：

### 1. 卸载 Python 包

打开命令行，执行：

```bash
pip uninstall -y chromadb sentence-transformers langchain langchain-community langchain-chroma streamlit streamlit-chat pyttsx3 SpeechRecognition Pillow requests schedule python-dotenv pydantic openai dashscope
```

### 2. 清理缓存

```bash
# 清理 pip 缓存
pip cache purge

# 删除 UV 缓存
rmdir /s /q %USERPROFILE%\AppData\Local\uv

# 删除 pip 缓存
rmdir /s /q %USERPROFILE%\AppData\Local\pip\Cache
```

### 3. 删除虚拟环境（如果有）

```bash
# 如果在项目目录有 .venv
rmdir /s /q E:\myAgent\.venv
```

---

## 📂 D 盘目录结构

完成后，D 盘会有：

```
D:\myAgent\
├── .cache/              # Python 包缓存
│   ├── pip/
│   └── uv/
├── data/                # 应用数据
│   ├── members.json
│   ├── memory/
│   │   ├── short_term.json
│   │   ├── working.json
│   │   └── chroma_db/
│   ├── knowledge_docs/
│   ├── knowledge_db/
│   ├── shopping_list.json
│   └── photo_index.json
└── photos/              # 照片存储
```

---

## 💾 估算空间占用

| 项目 | 大小 |
|------|------|
| Python 包 | ~2-3 GB |
| 向量数据库 | ~100-500 MB |
| 照片存储 | 取决于数量 |
| 其他数据 | ~50-100 MB |
| **总计** | **~3-4 GB** |

---

## ⚠️ 注意事项

### 1. 备份重要数据

如果 C 盘已有数据，先备份：

```bash
xcopy E:\myAgent\data C:\backup\data /E /I
```

### 2. 确认 D 盘空间

确保 D 盘至少有 **5 GB** 可用空间。

### 3. 管理员权限

某些操作可能需要管理员权限。

---

## 🔍 验证迁移

### 检查 C 盘是否清理干净

```bash
# 查看 pip 安装的包
pip list

# 应该只看到基础包，没有我们的依赖
```

### 检查 D 盘配置

```bash
# 查看环境变量
echo %UV_CACHE_DIR%

# 应该输出: D:\myAgent\.cache
```

### 测试应用

```bash
python test_agent.py
```

---

## ❓ 常见问题

### Q: 清理后无法运行怎么办？

A: 重新运行 `install.bat` 安装依赖。

### Q: D 盘空间不够怎么办？

A: 可以选择其他盘符，修改配置脚本即可。

### Q: 能否保留 C 盘的某些包？

A: 可以，手动卸载不需要的包即可。

### Q: 迁移后之前的数据还在吗？

A: 代码会自动检测并使用 D 盘数据。如果 D 盘没有数据，会创建新的。

---

## 🚀 快速开始

最简单的方式：

1. **双击** `clean_c_drive.bat` - 清理 C 盘
2. **双击** `setup_d_drive.bat` - 配置 D 盘
3. **双击** `install.bat` - 安装依赖
4. **双击** `run.bat` - 启动应用

完成！🎉

---

## 📞 需要帮助？

如果遇到问题：
1. 查看控制台错误信息
2. 检查 D 盘是否有写入权限
3. 确认 Python 已正确安装
4. 查看详细文档

---

**准备好了吗？开始清理吧！** 🧹
