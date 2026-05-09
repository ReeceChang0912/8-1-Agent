# 底层技术修复 + Phase 4 剩余任务 - 设计文档

**日期**: 2026-05-07
**项目**: Family Smart Agent (家庭智能管家)
**版本**: v3.0.0
**状态**: 待审批

---

## 1. 概述

本设计文档覆盖两个主要工作：
1. **底层技术修复** - 修复阻塞性和安全隐患问题
2. **Phase 4剩余任务** - 完成第四阶段规划的5个未完成任务

### 范围

| 模块 | 任务 | 优先级 | 估计工作量 |
|------|------|--------|------------|
| 照片模块 | 修复SmartPhotoAnalyzer + 完善照片记忆 | P0 | 2h |
| 购物模块 | 智能购物建议 + 高级功能 | P0 | 3h |
| 日程模块 | 智能日程推荐 | P1 | 3h |
| 交互模块 | 语音交互集成 | P1 | 4h |
| 管理模块 | 数据导入导出 + 邀请链接 + bug修复 | P2 | 3h |

---

## 2. 底层技术修复

### 2.1 SmartPhotoAnalyzer调用不存在方法修复

**问题**: `smart_photo_analyzer.py` 调用 `LLMAdapter` 上不存在的方法。

**修复方案**:
1. 检查 `LLMAdapter` 现有方法签名
2. 在 `LLMAdapter` 中添分析方法（如 `analyze_image_description`）
3. 或者在 `SmartPhotoAnalyzer` 中改用已存在的方法
4. 确保照片分析功能能正常工作

**文件影响**:
- `family_agent/llm_adapter.py` - 添加图片分析方法
- `family_agent/smart_photo_analyzer.py` - 修复调用

### 2.2 硬编码D:/myAgent路径清理

**问题**: 代码中有4处硬编码 `D:/myAgent` 路径。

**修复方案**:
```python
# 替换前
if os.path.exists("D:/myAgent/data"):
    data_dir = "D:/myAgent/data"

# 替换后
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
data_dir = BASE_DIR / "data"
```

**文件影响**:
- `family_agent/core.py` (lines 36-37)
- `family_agent/role_manager.py` (lines 122-123)
- `pyproject.toml` (line 9 - cache-dir)

### 2.3 LLM API密钥泄露处理

**问题**: API密钥可能已提交到git历史中。

**修复方案**:
1. 检查 `config/.env` 是否有密钥
2. 确保 `.gitignore` 包含 `config/.env`
3. 使用 `git-filter-repo` 或 BFG 清理git历史（如需要）
4. 更新文档，说明如何配置 `.env`

**文件影响**:
- `config/.env.example` - 确保有模板
- `.gitignore` - 确认规则

### 2.4 双认证系统合并

**问题**: `family_auth.py` 和 `auth_manager.py` 两个认证系统共存。

**修复方案**:
1. 分析两套系统的功能差异
2. 保留 `family_auth.py`（功能更完整）
3. 将 `auth_manager.py` 的功能合并进来
4. 更新所有引用指向统一认证系统
5. 删除冗余文件

**文件影响**:
- `family_agent/family_auth.py` - 合并目标
- `family_agent/auth_manager.py` - 被合并后删除
- 所有引用 `auth_manager` 的文件

---

## 3. Module 1: 照片模块

### 3.1 修复SmartPhotoAnalyzer

**目标**: 让照片分析功能可用。

**设计**:
1. 在 `LLMAdapter` 中添加 `analyze_image` 方法
2. 支持图片描述生成、标签提取、人物识别
3. 如果LLM不支持图片，使用本地规则降级

**API设计**:
```python
class LLMAdapter:
    def analyze_image(self, image_path: str, prompt: str) -> dict:
        """
        分析图片
        返回: {"description": str, "tags": list, "people": list, "mood": str}
        """
```

### 3.2 完善照片记忆功能

**目标**: 实现Phase 3中的照片记忆功能。

**功能点**:
1. 照片上传API（已在backend/routers/photos.py）
2. 自动分析（调用SmartPhotoAnalyzer）
3. 自然语言搜索（已在photo_memory.py，需对接LLM）
4. "去年的今天"回忆生成（已有基础，需完善）

**新增API**:
- `POST /api/photos/upload` - 上传并分析
- `GET /api/photos/memories` - 获取回忆照片
- `GET /api/photos/search?q=xxx` - 自然语言搜索

---

## 4. Module 2: 购物模块

### 4.1 智能购物建议

**目标**: 基于历史消费数据，提供智能购物建议。

**设计**:
1. 分析历史购物记录，识别消耗频率
2. 预测哪些商品即将用完
3. 自动生成补货提醒

**实现**:
```python
class SmartShoppingAdvisor:
    def analyze_consumption_patterns(self) -> dict:
        """分析消费模式"""

    def predict_reorder_items(self) -> list:
        """预测需要补货的商品"""

    def generate_shopping_suggestions(self, member: str) -> list:
        """生成购物建议"""
```

**数据库表**（如需要）:
- `shopping_history` - 购物历史记录
- `consumption_patterns` - 消费模式缓存

### 4.2 购物清单高级功能

**目标**: 实现合并、去重、采购路线优化。

**功能点**:
1. **智能合并** - 已部分实现（_find_similar_item），需完善
2. **去重增强** - 基于语义相似度（可用LLM）
3. **采购路线** - 已基本实现，需对接真实超市布局

**改进点**:
- `shopping_list.py` 的 `_find_similar_item` 使用LLM做语义匹配
- 添加 `merge_shopping_list` 方法合并多个清单
- 采购路线支持自定义超市布局

---

## 5. Module 3: 日程模块 - 智能日程推荐

**目标**: 基于历史行为分析，智能推荐日程安排。

**设计**:
```python
class SmartScheduleRecommender:
    def __init__(self, db_manager):
        self.db = db_manager

    def analyze_historical_patterns(self, member: str) -> dict:
        """分析历史日程模式"""

    def recommend_schedule(self, member: str, date: str) -> list:
        """推荐日程安排"""

    def predict_free_time(self, member: str, date: str) -> list:
        """预测空闲时段"""
```

**机器学习模型**（可选）:
- 使用简单的统计模型（无需复杂ML库）
- 基于时间规律、频率、优先级

**新增API**:
- `GET /api/schedule/recommendations?member=xxx&date=yyyy-mm-dd`
- `GET /api/schedule/free-times?member=xxx&date=yyyy-mm-dd`

---

## 6. Module 4: 交互模块 - 语音交互集成

**目标**: 支持语音输入和输出。

### 6.1 前端语音识别

**技术方案**: Web Speech API（浏览器原生支持）

**实现**:
```typescript
// frontend/src/hooks/useSpeechRecognition.ts
export function useSpeechRecognition() {
    const [isListening, setIsListening] = useState(false);
    const [transcript, setTranscript] = useState('');

    const startListening = () => {
        const recognition = new webkitSpeechRecognition();
        recognition.onresult = (event) => {
            setTranscript(event.results[0][0].transcript);
        };
        recognition.start();
    };

    return { isListening, transcript, startListening };
}
```

### 6.2 后端TTS合成

**技术方案**: 使用Edge-TTS或pyttsx3（离线）

**实现**:
```python
# family_agent/voice_engine.py
class VoiceEngine:
    def text_to_speech(self, text: str, output_path: str):
        """文字转语音"""
```

**新增API**:
- `POST /api/voice/recognize` - 语音识别（可选，前端可做）
- `POST /api/voice/tts` - 文字转语音

---

## 7. Module 5: 管理模块

### 7.1 数据导入导出

**目标**: 支持JSON/CSV格式的数据备份和迁移。

**设计**:
```python
class DataMigrationManager:
    def export_all(self, format: str = 'json') -> str:
        """导出所有数据"""

    def import_all(self, file_path: str, format: str = 'json'):
        """导入数据"""

    def backup_to_file(self, backup_path: str):
        """备份到文件"""

    def restore_from_file(self, backup_path: str):
        """从文件恢复"""
```

**支持的数据类型**:
- 家庭成员
- 购物清单
- 日程提醒
- 聊天历史
- 任务管理

### 7.2 邀请链接生成

**目标**: 用短链接/二维码替代家庭号。

**设计**:
1. 生成唯一的邀请码
2. 创建邀请记录（包含过期时间）
3. 生成二维码（使用qrcode库）
4. 通过链接/二维码加入家庭

**新增API**:
- `POST /api/family/invite` - 创建邀请
- `GET /api/family/invite/{code}` - 验证邀请
- `POST /api/family/join-by-invite` - 通过邀请加入

### 7.3 其他bug修复

**清单**:
1. `memory_manager.py` 的 `load` 函数不完整实现 - 检查并修复
2. `emotion_engine.py` 使用基础关键词匹配 - 可升级为LLM增强
3. 前端API调用使用不一致的URL模式 - 已修复（第一阶段优化）
4. 重复的启动脚本（`run.bat`、`run_fullstack.bat`）- 统一为一个
5. 照片服务端点缺失 - 已修复（第一阶段优化）

---

## 8. 数据流图

```
用户请求
  ↓
前端UI (React/Streamlit)
  ↓ HTTP/WebSocket
后端API (FastAPI routers)
  ↓
Family Agent核心模块
  ├─ LLM Adapter (AI对话)
  ├─ Photo Analyzer (图片分析)
  ├─ Smart Shopping (购物建议)
  ├─ Schedule Recommender (日程推荐)
  ├─ Voice Engine (语音交互)
  └─ Data Migration (数据迁移)
  ↓
数据库 (SQLite) / 文件系统
```

---

## 9. 测试策略

### 单元测试
- 每个新模块至少3个测试用例
- 覆盖正常流程、边界情况、错误处理

### 集成测试
- API端点测试（使用httpx.AsyncClient）
- 模块间交互测试

### 手动测试
- 语音交互功能（需要真实麦克风）
- 移动端适配（已在第二阶段完成）

---

## 10. 实施顺序

**Week 1: 底层修复**
- Day 1-2: 修复SmartPhotoAnalyzer + 清理硬编码路径
- Day 3: 处理API密钥泄露 + 合并双认证系统

**Week 2: Phase 4功能**
- Day 1-2: 智能购物建议 + 购物高级功能
- Day 3: 智能日程推荐

**Week 3: 交互和管理**
- Day 1-2: 语音交互集成
- Day 3: 数据导入导出 + 邀请链接

---

## 11. 成功指标

| 指标 | 目标值 |
|------|--------|
| 修复的bug数量 | 5+ |
| 新增功能点 | 7个 |
| 测试覆盖率 | >80% |
| API端点增加 | 10+ |
| 代码质量 | 无硬编码、无重复认证 |

---

**设计完成度**: 100%
**下一步**: 用户审批后，调用 writing-plans skill 生成实施计划

---

*文档生成时间: 2026-05-07*
*作者: Claude (brainstorming skill)*
