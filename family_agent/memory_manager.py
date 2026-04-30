"""
家庭记忆管理系统
支持短期记忆、长期记忆、工作记忆和情景记忆
"""

import json
import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import chromadb
from chromadb.config import Settings


class MemoryType(Enum):
    """记忆类型"""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    WORKING = "working"
    EPISODIC = "episodic"


@dataclass
class Memory:
    """记忆单元"""
    content: str
    memory_type: MemoryType
    timestamp: str
    source: str = ""
    importance: float = 0.5
    tags: List[str] = field(default_factory=list)
    related_members: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    id: str = ""
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            "memory_type": self.memory_type.value
        }


class FamilyMemoryManager:
    """家庭记忆管理器"""
    
    def __init__(self, data_dir: str = "data/memory"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 短期记忆
        self.short_term_memory: List[Memory] = []
        self.max_short_term = 50
        
        # 工作记忆
        self.working_memory: Dict[str, any] = {}
        
        # 长期记忆（向量数据库）
        self.chroma_client = chromadb.PersistentClient(path=str(self.data_dir / "chroma_db"))
        
        try:
            self.long_term_collection = self.chroma_client.get_collection("family_long_term_memory")
        except:
            self.long_term_collection = self.chroma_client.create_collection(
                name="family_long_term_memory",
                metadata={"description": "家庭长期记忆"}
            )
        
        self._load_memories()
    
    def add_memory(self, 
                   content: str,
                   memory_type: MemoryType,
                   source: str = "chat",
                   importance: float = 0.5,
                   tags: List[str] = None,
                   related_members: List[str] = None,
                   metadata: Dict = None) -> str:
        """添加记忆"""
        
        memory = Memory(
            content=content,
            memory_type=memory_type,
            timestamp=datetime.datetime.now().isoformat(),
            source=source,
            importance=importance,
            tags=tags or [],
            related_members=related_members or [],
            metadata=metadata or {}
        )
        
        if memory_type == MemoryType.SHORT_TERM:
            self.short_term_memory.append(memory)
            if len(self.short_term_memory) > self.max_short_term:
                self.short_term_memory = self.short_term_memory[-self.max_short_term:]
        
        elif memory_type == MemoryType.LONG_TERM:
            memory_id = f"mem_{len(self.long_term_collection.get()['ids'])}"
            memory.id = memory_id
            
            self.long_term_collection.add(
                documents=[content],
                metadatas=[memory.to_dict()],
                ids=[memory_id]
            )
        
        elif memory_type == MemoryType.WORKING:
            key = metadata.get("key", "default")
            self.working_memory[key] = memory
        
        elif memory_type == MemoryType.EPISODIC:
            memory_id = f"epi_{len(self.long_term_collection.get()['ids'])}"
            memory.id = memory_id
            
            self.long_term_collection.add(
                documents=[content],
                metadatas=[{**memory.to_dict(), "type": "episodic"}],
                ids=[memory_id]
            )
        
        self._save_memories()
        
        return memory.id if memory.id else "saved"
    
    def retrieve_memories(self, 
                         query: str,
                         memory_types: List[MemoryType] = None,
                         n_results: int = 5,
                         min_importance: float = 0.0) -> List[Dict]:
        """检索相关记忆"""
        
        if memory_types is None:
            memory_types = [MemoryType.LONG_TERM, MemoryType.EPISODIC]
        
        results = []
        
        if MemoryType.LONG_TERM in memory_types or MemoryType.EPISODIC in memory_types:
            try:
                vector_results = self.long_term_collection.query(
                    query_texts=[query],
                    n_results=n_results * 2
                )
                
                for i, doc in enumerate(vector_results['documents'][0]):
                    meta = vector_results['metadatas'][0][i]
                    
                    if meta.get('importance', 0) < min_importance:
                        continue
                    
                    results.append({
                        "content": doc,
                        "metadata": meta,
                        "distance": vector_results['distances'][0][i] if 'distances' in results else None
                    })
            except Exception as e:
                print(f"检索失败: {e}")
        
        if MemoryType.SHORT_TERM in memory_types:
            for mem in reversed(self.short_term_memory[-20:]):
                if query.lower() in mem.content.lower():
                    results.append({
                        "content": mem.content,
                        "metadata": mem.to_dict(),
                        "distance": 0.0
                    })
        
        results.sort(key=lambda x: x.get('distance', 1.0) or 1.0)
        
        return results[:n_results]
    
    def get_conversation_context(self, n_turns: int = 10) -> str:
        """获取对话上下文"""
        recent_memories = self.short_term_memory[-n_turns:]
        
        context = "\n".join([
            f"[{m.timestamp}] {m.content}"
            for m in recent_memories
        ])
        
        return context
    
    def update_working_memory(self, key: str, value: any):
        """更新工作记忆"""
        self.add_memory(
            content=str(value),
            memory_type=MemoryType.WORKING,
            metadata={"key": key}
        )
    
    def get_working_memory(self, key: str) -> Optional[str]:
        """获取工作记忆"""
        if key in self.working_memory:
            return self.working_memory[key].content
        return None
    
    def get_memory_stats(self) -> Dict:
        """获取记忆统计信息"""
        return {
            "short_term_count": len(self.short_term_memory),
            "long_term_count": len(self.long_term_collection.get()['ids']),
            "working_memory_keys": list(self.working_memory.keys())
        }
    
    def _save_memories(self):
        """保存记忆到磁盘"""
        short_term_file = self.data_dir / "short_term.json"
        with open(short_term_file, 'w', encoding='utf-8') as f:
            json.dump([m.to_dict() for m in self.short_term_memory], 
                     f, ensure_ascii=False, indent=2)
        
        working_file = self.data_dir / "working.json"
        with open(working_file, 'w', encoding='utf-8') as f:
            json.dump(
                {k: v.to_dict() for k, v in self.working_memory.items()},
                f, ensure_ascii=False, indent=2
            )
    
    def _load_memories(self):
        """从磁盘加载记忆"""
        short_term_file = self.data_dir / "short_term.json"
        if short_term_file.exists():
            with open(short_term_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    item['memory_type'] = MemoryType(item['memory_type'])
                    self.short_term_memory.append(Memory(**item))
        
        working_file = self.data_dir / "working.json"
        if working_file.exists():
            with open(working_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 简化处理
