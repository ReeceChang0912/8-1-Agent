# D 盘配置指南

## 📌 为什么使用 D 盘？

- ✅ 避免占用 C 盘空间
- ✅ 数据与系统分离，更安全
- ✅ 方便备份和迁移

---

## 🚀 快速配置（3步）

### 步骤 1：运行配置脚本

双击运行 `setup_d_drive.bat`

这会：
- 在 D 盘创建必要的目录
- 设置环境变量

### 步骤 2：安装依赖

双击运行 `install.bat`

### 步骤 3：启动应用

双击运行 `run.bat`

---

## 📂 D 盘目录结构

```
D:\myAgent\
├── .cache/          # UV 缓存（下载的包）
├── data/            # 应用数据
│   ├── members.json
│   ├── memory/
│   ├── knowledge_db/
│   └── shopping_list.json
└── photos/          # 照片存储
```

---

## 🔧 手动配置（可选）

如果自动脚本不起作用，可以手动设置：

### 1. 创建目录

```bash
mkdir D:\myAgent
mkdir D:\myAgent\.cache
mkdir D:\myAgent\data
mkdir D:\myAgent\photos
```

### 2. 设置环境变量

**Windows 10/11**：
1. 右键"此电脑" → 属性
2. 高级系统设置 → 环境变量
3. 新建系统变量：
   - 变量名：`UV_CACHE_DIR`
   - 变量值：`D:\myAgent\.cache`

### 3. 验证配置

```bash
echo %UV_CACHE_DIR%
```

应该输出：`D:\myAgent\.cache`

---

## ⚙️ 自定义数据位置

如果你想把数据放在其他位置，可以：

### 方法一：修改代码

编辑 `family_agent/core.py`：

```python
def __init__(self, data_dir: str = None):
    if data_dir is None:
        data_dir = "你的路径/data"  # 修改这里
```

### 方法二：创建时指定

```python
from family_agent.core import FamilyAgentCore

# 指定自定义数据目录
agent = FamilyAgentCore(data_dir="X:/your/path/data")
```

---

## 🔄 从 C 盘迁移到 D 盘

如果之前已经在 C 盘有数据：

### 1. 停止应用

确保应用没有运行。

### 2. 复制数据

```bash
# 复制整个 data 文件夹
xcopy E:\myAgent\data D:\myAgent\data /E /I /H
```

### 3. 复制照片

```bash
xcopy E:\myAgent\photos D:\myAgent\photos /E /I /H
```

### 4. 验证

启动应用，检查数据是否正常。

### 5. 删除旧数据（可选）

确认一切正常后，可以删除 E 盘的旧数据。

---

## ❓ 常见问题

### Q: D 盘空间不够怎么办？

A: 可以选择其他盘符，修改配置即可。

### Q: 可以同时使用 C 盘和 D 盘吗？

A: 可以，代码会自动检测 D 盘是否存在。

### Q: 如何查看数据存在哪里？

A: 启动应用后，查看控制台输出，会显示数据目录路径。

### Q: 卸载后 D 盘数据还在吗？

A: 是的，需要手动删除 D:\myAgent 文件夹。

---

## 💡 最佳实践

1. **定期备份 D 盘数据**
   ```bash
   xcopy D:\myAgent\data X:\backup\family-agent /E /I
   ```

2. **监控磁盘空间**
   - 保持至少 10GB 可用空间

3. **清理缓存**
   ```bash
   # 定期清理 UV 缓存
   rmdir /s /q D:\myAgent\.cache
   ```

---

## 🎯 完成检查

- [ ] 运行 setup_d_drive.bat
- [ ] D:\myAgent 目录已创建
- [ ] 环境变量已设置
- [ ] 运行 install.bat 安装依赖
- [ ] 运行 test.bat 测试通过
- [ ] 运行 run.bat 启动成功

---

**配置完成后，所有数据都会存储在 D 盘！** 💾
