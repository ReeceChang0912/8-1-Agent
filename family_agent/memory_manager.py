"""
家庭记忆管理系统
支持短期记忆、长期记忆、工作记忆和情景记忆
"""

import json
import datetime
import hashlib
import os
import re
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import chromadb


class MemoryType(Enum):
    """记忆类型"""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    WORKING = "working"
    EPISODIC = "episodic"
    SUMMARY = "summary"


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
        self.compress_after = 36
        self.keep_recent_after_compress = 18
        self.conversation_summaries: List[Memory] = []
        
        # 工作记忆
        self.working_memory: Dict[str, any] = {}
        
        # 长期记忆（优先向量数据库；不可用时降级为 JSON 检索）
        self.chroma_client = None
        self.long_term_collection = None
        self.long_term_fallback: List[Memory] = []
        self.chroma_path = Path(os.getenv("CHROMA_DB_DIR", str(self.data_dir / "chroma_db")))
        try:
            self._ensure_directory_writable(self.chroma_path)
            self.chroma_client = chromadb.PersistentClient(path=str(self.chroma_path))
            try:
                self.long_term_collection = self.chroma_client.get_collection("family_long_term_memory")
            except Exception:
                self.long_term_collection = self.chroma_client.create_collection(
                    name="family_long_term_memory",
                    metadata={"description": "家庭长期记忆"}
                )
        except Exception as e:
            print(
                f"长期记忆向量库不可用，使用 JSON 降级存储: {e}. "
                f"请确认 CHROMA_DB_DIR 或 {self.chroma_path} 对运行进程可写。"
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
        metadata = metadata or {}
        
        memory = Memory(
            content=content,
            memory_type=memory_type,
            timestamp=datetime.datetime.now().isoformat(),
            source=source,
            importance=importance,
            tags=tags or [],
            related_members=related_members or [],
            metadata=metadata
        )
        
        if memory_type == MemoryType.SHORT_TERM:
            self.short_term_memory.append(memory)
            if len(self.short_term_memory) > self.max_short_term:
                self.short_term_memory = self.short_term_memory[-self.max_short_term:]
            self._maybe_compress_short_term()
        
        elif memory_type == MemoryType.LONG_TERM:
            memory_id = self._stable_memory_id("mem", content, metadata)
            memory.id = memory_id
            
            if self.long_term_collection:
                try:
                    self.long_term_collection.upsert(
                        documents=[content],
                        metadatas=[self._chroma_metadata(memory)],
                        ids=[memory_id]
                    )
                except AttributeError:
                    self.long_term_collection.add(
                        documents=[content],
                        metadatas=[self._chroma_metadata(memory)],
                        ids=[memory_id]
                    )
            else:
                self._upsert_fallback_memory(memory)
        
        elif memory_type == MemoryType.WORKING:
            key = metadata.get("key", "default")
            self.working_memory[key] = memory
        
        elif memory_type == MemoryType.EPISODIC:
            memory_id = self._stable_memory_id("epi", content, metadata)
            memory.id = memory_id
            
            if self.long_term_collection:
                try:
                    self.long_term_collection.upsert(
                        documents=[content],
                        metadatas=[self._chroma_metadata(memory, {"type": "episodic"})],
                        ids=[memory_id]
                    )
                except AttributeError:
                    self.long_term_collection.add(
                        documents=[content],
                        metadatas=[self._chroma_metadata(memory, {"type": "episodic"})],
                        ids=[memory_id]
                    )
            else:
                self._upsert_fallback_memory(memory)

        elif memory_type == MemoryType.SUMMARY:
            memory_id = self._stable_memory_id("sum", content, metadata)
            memory.id = memory_id
            self._upsert_summary(memory)
        
        self._save_memories()
        
        return memory.id if memory.id else "saved"
    
    def retrieve_memories(self, 
                         query: str,
                         memory_types: List[MemoryType] = None,
                         n_results: int = 5,
                         min_importance: float = 0.0,
                         user_id: str = None,
                         family_id: str = None) -> List[Dict]:
        """检索相关记忆"""
        
        if memory_types is None:
            memory_types = [MemoryType.LONG_TERM, MemoryType.EPISODIC]
        
        results = []
        
        if self.long_term_collection and (
            MemoryType.LONG_TERM in memory_types
            or MemoryType.EPISODIC in memory_types
            or MemoryType.SUMMARY in memory_types
        ):
            try:
                vector_results = self.long_term_collection.query(
                    query_texts=[query],
                    n_results=n_results * 2
                )
                
                for i, doc in enumerate(vector_results['documents'][0]):
                    meta = vector_results['metadatas'][0][i]
                    
                    if meta.get('importance', 0) < min_importance:
                        continue
                    if not self._memory_matches_scope(meta, user_id=user_id, family_id=family_id):
                        continue
                    
                    results.append({
                        "content": doc,
                        "metadata": meta,
                        "distance": vector_results['distances'][0][i] if vector_results.get('distances') else None
                    })
            except Exception as e:
                print(f"检索失败: {e}")
        elif (
            MemoryType.LONG_TERM in memory_types
            or MemoryType.EPISODIC in memory_types
            or MemoryType.SUMMARY in memory_types
        ):
            results.extend(self._search_fallback_memories(
                query, memory_types, min_importance, user_id=user_id, family_id=family_id
            ))
            if MemoryType.SUMMARY in memory_types:
                results.extend(self._search_summaries(query, min_importance, user_id=user_id, family_id=family_id))
        
        if MemoryType.SHORT_TERM in memory_types:
            for mem in reversed(self.short_term_memory[-20:]):
                if query.lower() in mem.content.lower() and self._memory_matches_scope(
                    mem.to_dict(), user_id=user_id, family_id=family_id
                ):
                    results.append({
                        "content": mem.content,
                        "metadata": mem.to_dict(),
                        "distance": 0.0
                    })
        
        results.sort(key=lambda x: x.get('distance', 1.0) or 1.0)
        
        return results[:n_results]
    
    def get_conversation_context(self, n_turns: int = 10, user_id: str = None, family_id: str = None) -> str:
        """获取对话上下文"""
        recent_memories = [
            memory for memory in self.short_term_memory
            if self._memory_matches_scope(memory.to_dict(), user_id=user_id, family_id=family_id)
        ][-n_turns:]
        
        context = "\n".join([
            f"[{m.timestamp}] {m.content}"
            for m in recent_memories
        ])
        
        return context

    def get_summary_context(self, query: str = "", limit: int = 3,
                            user_id: str = None, family_id: str = None) -> str:
        """Return recent and query-relevant compressed conversation summaries."""
        all_summaries = [
            memory for memory in self.conversation_summaries
            if self._memory_matches_scope(memory.to_dict(), user_id=user_id, family_id=family_id)
        ]
        summaries = list(reversed(all_summaries[-limit:]))
        if query:
            query_chars = set(query.lower())
            relevant = self._search_summaries(query, min_importance=0.0, user_id=user_id, family_id=family_id)
            for item in relevant:
                memory = item.get("memory")
                if memory and memory not in summaries:
                    summaries.append(memory)
            summaries.sort(
                key=lambda m: (
                    -m.importance,
                    -len(set(m.content.lower()) & query_chars),
                    m.timestamp,
                )
            )
        return "\n".join(f"- {memory.content}" for memory in summaries[:limit])

    def remember_conversation_turn(
        self,
        user_message: str,
        assistant_response: str = "",
        user_id: str = None,
        family_id: str = None,
        emotion: str = None,
    ) -> List[str]:
        """Persist a chat turn and promote durable user facts to long-term memory."""
        metadata = {
            "user_id": user_id or "",
            "family_id": family_id or "",
            "emotion": emotion or "",
            "role": "user" if user_message else "assistant",
        }
        if user_message:
            self.add_memory(
                content=f"[User:{user_id or 'unknown'}] {user_message}",
                memory_type=MemoryType.SHORT_TERM,
                source="chat",
                tags=["conversation", family_id or "global", user_id or "anonymous"],
                related_members=[user_id] if user_id else [],
                metadata=metadata,
            )

        if assistant_response:
            self.add_memory(
                content=f"[Assistant] {assistant_response}",
                memory_type=MemoryType.SHORT_TERM,
                source="chat",
                tags=["conversation", family_id or "global", user_id or "anonymous"],
                related_members=[user_id] if user_id else [],
                metadata={**metadata, "role": "assistant"},
            )

        promoted = []
        for fact in self.extract_memorable_facts(user_message):
            fact_type = self.classify_fact(fact)
            memory_id = self.add_memory(
                content=fact,
                memory_type=MemoryType.LONG_TERM,
                source="chat_fact",
                importance=self.score_importance(fact, fact_type),
                tags=["profile", "auto_extracted", fact_type, family_id or "global", user_id or "anonymous"],
                related_members=[user_id] if user_id else [],
                metadata={
                    "user_id": user_id or "",
                    "family_id": family_id or "",
                    "origin": "chat",
                    "fact_type": fact_type,
                },
            )
            promoted.append(memory_id)
        self._maybe_record_episode(user_message, assistant_response, user_id, family_id, emotion)
        return promoted

    def extract_memorable_facts(self, text: str) -> List[str]:
        """Extract simple durable preferences and personal facts from a message."""
        cleaned = text.strip()
        if len(cleaned) < 4 or len(cleaned) > 220:
            return []

        patterns = [
            r"(我(?:叫|是)[^，。；;.!！?？\n]{1,30})",
            r"(我(?:喜欢|爱吃|爱喝|偏好|习惯|讨厌|不喜欢|不能吃|对[^，。；;.!！?？\n]{1,24}过敏)[^，。；;.!！?？\n]{0,80})",
            r"(我家(?:住在|在|有)[^，。；;.!！?？\n]{1,80})",
            r"((?:爸爸|妈妈|孩子|宝宝|奶奶|爷爷|外婆|外公|老婆|老公)[^，。；;.!！?？\n]{0,20}(?:喜欢|讨厌|不能吃|过敏|需要|生日|血压|血糖|身体)[^，。；;.!！?？\n]{0,80})",
            r"([^，。；;.!！?？\n]{1,40}(?:生日|纪念日|过敏|忌口|慢性病|用药)[^，。；;.!！?？\n]{0,80})",
        ]

        facts = []
        for pattern in patterns:
            for match in re.finditer(pattern, cleaned):
                for fact in self._split_fact_candidates(match.group(1)):
                    if fact and fact not in facts:
                        facts.append(fact)
        return facts[:3]

    def classify_fact(self, fact: str) -> str:
        """Classify a durable fact for later filtering and editing."""
        if any(word in fact for word in ["过敏", "不能吃", "忌口", "慢性病", "用药", "血压", "血糖", "身体"]):
            return "health"
        if any(word in fact for word in ["生日", "纪念日"]):
            return "date"
        if any(word in fact for word in ["喜欢", "爱吃", "爱喝", "偏好", "讨厌", "不喜欢", "习惯"]):
            return "preference"
        if any(word in fact for word in ["住在", "地址", "我家"]):
            return "home"
        if fact.startswith("我叫") or fact.startswith("我是"):
            return "identity"
        return "profile"

    def score_importance(self, fact: str, fact_type: str = "") -> float:
        """Score memory importance so critical facts survive context pruning."""
        scores = {
            "health": 0.95,
            "date": 0.9,
            "identity": 0.88,
            "home": 0.84,
            "preference": 0.78,
            "profile": 0.7,
        }
        score = scores.get(fact_type, 0.7)
        if any(word in fact for word in ["紧急", "重要", "必须", "一定"]):
            score = min(1.0, score + 0.08)
        return score

    def build_chat_context(
        self,
        query: str,
        user_id: str = None,
        family_id: str = None,
        recent_turns: int = 8,
        relevant_limit: int = 5,
        max_chars: int = 6000,
    ) -> str:
        """Build compact context from summaries, retrieval, working memory, and recent turns."""
        parts = []

        summary_context = self.get_summary_context(query=query, limit=3, user_id=user_id, family_id=family_id)
        if summary_context:
            parts.append(f"压缩会话摘要:\n{summary_context}")

        relevant_memories = self.retrieve_memories(
            query=query,
            memory_types=[MemoryType.LONG_TERM, MemoryType.EPISODIC, MemoryType.SUMMARY, MemoryType.SHORT_TERM],
            n_results=relevant_limit,
            min_importance=0.2,
            user_id=user_id,
            family_id=family_id,
        )
        if relevant_memories:
            seen = set()
            lines = []
            for memory in relevant_memories:
                content = memory["content"]
                if content in seen:
                    continue
                seen.add(content)
                lines.append(f"- {content}")
            if lines:
                parts.append("相关长期记忆:\n" + "\n".join(lines))

        if self.working_memory:
            working_lines = [
                f"- {key}: {memory.content}"
                for key, memory in self.working_memory.items()
                if self._memory_matches_scope(memory.to_dict(), user_id=user_id, family_id=family_id)
            ]
            parts.append("当前工作记忆:\n" + "\n".join(working_lines[:8]))

        recent_context = self.get_conversation_context(recent_turns, user_id=user_id, family_id=family_id)
        if recent_context:
            parts.append(f"最近对话:\n{recent_context}")

        return self._fit_context(parts, max_chars=max_chars)
    
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
            "summary_count": len(self.conversation_summaries),
            "long_term_count": (
                len(self.long_term_collection.get()['ids'])
                if self.long_term_collection
                else len(self.long_term_fallback)
            ),
            "working_memory_keys": list(self.working_memory.keys()),
            "chroma_enabled": bool(self.long_term_collection),
            "chroma_path": str(self.chroma_path),
        }

    def list_memories(self, query: str = "", memory_type: str = "all", limit: int = 100,
                      user_id: str = None, family_id: str = None) -> List[Dict]:
        """List manageable memories for UI review."""
        items: List[Memory] = []
        if memory_type in ("all", MemoryType.SHORT_TERM.value):
            items.extend(self.short_term_memory)
        if memory_type in ("all", MemoryType.WORKING.value):
            items.extend(self.working_memory.values())
        if memory_type in ("all", MemoryType.SUMMARY.value):
            items.extend(self.conversation_summaries)
        if memory_type in ("all", MemoryType.LONG_TERM.value, MemoryType.EPISODIC.value):
            items.extend(self.long_term_fallback)

        query_lower = query.lower().strip()
        result = []
        seen = set()
        for memory in items:
            if not self._memory_matches_scope(memory.to_dict(), user_id=user_id, family_id=family_id):
                continue
            if query_lower and query_lower not in memory.content.lower():
                continue
            key = memory.id or f"{memory.memory_type.value}:{memory.timestamp}:{memory.content[:24]}"
            if key in seen:
                continue
            seen.add(key)
            data = memory.to_dict()
            data["id"] = key
            result.append(data)

        result.sort(key=lambda item: item.get("timestamp", ""), reverse=True)
        if self.long_term_collection and memory_type in (
            "all",
            MemoryType.LONG_TERM.value,
            MemoryType.EPISODIC.value,
            MemoryType.SUMMARY.value,
        ):
            result.extend(self._list_chroma_memories(
                query=query,
                memory_type=memory_type,
                limit=limit,
                user_id=user_id,
                family_id=family_id,
            ))
            deduped = {}
            for item in result:
                deduped[item["id"]] = item
            result = list(deduped.values())
            result.sort(key=lambda item: item.get("timestamp", ""), reverse=True)
        return result[:limit]

    def update_memory(self, memory_id: str, content: str, importance: float = None,
                      tags: List[str] = None, user_id: str = None, family_id: str = None) -> bool:
        """Update memory content/metadata."""
        updated = False
        stores = [
            self.short_term_memory,
            self.long_term_fallback,
            self.conversation_summaries,
            list(self.working_memory.values()),
        ]
        for store in stores:
            for memory in store:
                if (memory.id or "") == memory_id:
                    if not self._memory_matches_scope(memory.to_dict(), user_id=user_id, family_id=family_id):
                        continue
                    memory.content = content
                    if importance is not None:
                        memory.importance = importance
                    if tags is not None:
                        memory.tags = tags
                    updated = True

        if self.long_term_collection and memory_id:
            try:
                got = self.long_term_collection.get(ids=[memory_id], include=["documents", "metadatas"])
                if got.get("ids"):
                    meta = got["metadatas"][0] or {}
                    if not self._memory_matches_scope(meta, user_id=user_id, family_id=family_id):
                        return updated
                    meta["importance"] = importance if importance is not None else meta.get("importance", 0.5)
                    if tags is not None:
                        meta["tags"] = tags
                    self.long_term_collection.upsert(
                        ids=[memory_id],
                        documents=[content],
                        metadatas=[meta],
                    )
                    updated = True
            except Exception:
                pass
        if updated:
            self._save_memories()
        return updated

    def delete_memory(self, memory_id: str, user_id: str = None, family_id: str = None) -> bool:
        """Delete a memory from local stores and Chroma when possible."""
        before = (
            len(self.short_term_memory)
            + len(self.long_term_fallback)
            + len(self.conversation_summaries)
            + len(self.working_memory)
        )
        self.short_term_memory = [
            m for m in self.short_term_memory
            if (m.id or "") != memory_id or not self._memory_matches_scope(m.to_dict(), user_id=user_id, family_id=family_id)
        ]
        self.long_term_fallback = [
            m for m in self.long_term_fallback
            if (m.id or "") != memory_id or not self._memory_matches_scope(m.to_dict(), user_id=user_id, family_id=family_id)
        ]
        self.conversation_summaries = [
            m for m in self.conversation_summaries
            if (m.id or "") != memory_id or not self._memory_matches_scope(m.to_dict(), user_id=user_id, family_id=family_id)
        ]
        self.working_memory = {
            key: memory for key, memory in self.working_memory.items()
            if (memory.id or key) != memory_id
            or not self._memory_matches_scope(memory.to_dict(), user_id=user_id, family_id=family_id)
        }
        if self.long_term_collection and memory_id:
            try:
                got = self.long_term_collection.get(ids=[memory_id], include=["metadatas"])
                meta = (got.get("metadatas") or [{}])[0] if got.get("ids") else {}
                if self._memory_matches_scope(meta or {}, user_id=user_id, family_id=family_id):
                    self.long_term_collection.delete(ids=[memory_id])
            except Exception:
                pass
        self._save_memories()
        after = (
            len(self.short_term_memory)
            + len(self.long_term_fallback)
            + len(self.conversation_summaries)
            + len(self.working_memory)
        )
        return after < before

    def _list_chroma_memories(self, query: str = "", memory_type: str = "all", limit: int = 100,
                              user_id: str = None, family_id: str = None) -> List[Dict]:
        try:
            data = self.long_term_collection.get(include=["documents", "metadatas"], limit=limit * 3)
        except Exception:
            return []
        rows = []
        query_lower = query.lower().strip()
        ids = data.get("ids", [])
        docs = data.get("documents", [])
        metas = data.get("metadatas", [])
        for idx, memory_id in enumerate(ids):
            content = docs[idx] if idx < len(docs) else ""
            meta = metas[idx] if idx < len(metas) and metas[idx] else {}
            item_type = meta.get("memory_type", MemoryType.LONG_TERM.value)
            if memory_type != "all" and item_type != memory_type and meta.get("type") != memory_type:
                continue
            if not self._memory_matches_scope(meta, user_id=user_id, family_id=family_id):
                continue
            if query_lower and query_lower not in content.lower():
                continue
            rows.append({
                "id": memory_id,
                "content": content,
                "memory_type": item_type,
                "timestamp": meta.get("timestamp", ""),
                "source": meta.get("source", ""),
                "importance": meta.get("importance", 0.5),
                "tags": meta.get("tags", []),
                "related_members": meta.get("related_members", []),
                "metadata": meta,
            })
        return rows[:limit]
    
    def _save_memories(self):
        """保存记忆到磁盘"""
        try:
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

            if not self.long_term_collection:
                long_term_file = self.data_dir / "long_term.json"
                with open(long_term_file, 'w', encoding='utf-8') as f:
                    json.dump([m.to_dict() for m in self.long_term_fallback],
                             f, ensure_ascii=False, indent=2)

            summaries_file = self.data_dir / "summaries.json"
            with open(summaries_file, 'w', encoding='utf-8') as f:
                json.dump([m.to_dict() for m in self.conversation_summaries],
                         f, ensure_ascii=False, indent=2)
        except OSError as e:
            print(f"记忆落盘失败，继续使用进程内记忆: {e}")
    
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
                for key, item in data.items():
                    item['memory_type'] = MemoryType(item['memory_type'])
                    self.working_memory[key] = Memory(**item)

        long_term_file = self.data_dir / "long_term.json"
        if long_term_file.exists():
            with open(long_term_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    item['memory_type'] = MemoryType(item['memory_type'])
                    self.long_term_fallback.append(Memory(**item))

        summaries_file = self.data_dir / "summaries.json"
        if summaries_file.exists():
            with open(summaries_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    item['memory_type'] = MemoryType(item['memory_type'])
                    self.conversation_summaries.append(Memory(**item))

    def _stable_memory_id(self, prefix: str, content: str, metadata: Dict = None) -> str:
        raw = json.dumps(
            {"content": content.strip(), "metadata": metadata or {}},
            ensure_ascii=False,
            sort_keys=True,
        )
        digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
        return f"{prefix}_{digest}"

    def _chroma_metadata(self, memory: Memory, extra: Dict = None) -> Dict:
        data = memory.to_dict()
        nested_metadata = data.pop("metadata", {}) or {}
        data["user_id"] = nested_metadata.get("user_id", data.get("user_id", ""))
        data["family_id"] = nested_metadata.get("family_id", data.get("family_id", ""))
        data["metadata_json"] = json.dumps(nested_metadata, ensure_ascii=False, sort_keys=True)
        if extra:
            data.update(extra)
        return data

    def _maybe_compress_short_term(self):
        if len(self.short_term_memory) <= self.compress_after:
            return
        candidate_count = len(self.short_term_memory) - self.keep_recent_after_compress
        if candidate_count <= 0:
            return
        candidates = self.short_term_memory[:candidate_count]
        first_scope = self._memory_scope_key(candidates[0])
        chunk = []
        for memory in candidates:
            if self._memory_scope_key(memory) != first_scope:
                break
            chunk.append(memory)
        if len(chunk) < 2:
            return
        summary = self._summarize_memory_chunk(chunk)
        if summary:
            first_ts = chunk[0].timestamp
            last_ts = chunk[-1].timestamp
            family_id = self._metadata_family_id(chunk[0].to_dict())
            user_id = self._metadata_user_id(chunk[0].to_dict())
            self.add_memory(
                content=summary,
                memory_type=MemoryType.SUMMARY,
                source="compression",
                importance=0.76,
                tags=["conversation_summary", family_id or "global", user_id or "anonymous"],
                related_members=[user_id] if user_id else [],
                metadata={
                    "from": first_ts,
                    "to": last_ts,
                    "count": len(chunk),
                    "family_id": family_id,
                    "user_id": user_id,
                },
            )
        self.short_term_memory = self.short_term_memory[len(chunk):]

    def _summarize_memory_chunk(self, memories: List[Memory]) -> str:
        facts = []
        tasks = []
        emotions = []
        topics = []
        for memory in memories:
            content = re.sub(r"^\[(User:[^\]]+|Assistant)\]\s*", "", memory.content).strip()
            if not content:
                continue
            for fact in self.extract_memorable_facts(content):
                if fact not in facts:
                    facts.append(fact)
            if any(word in content for word in ["提醒", "安排", "日程", "任务", "购物", "买", "待办"]):
                tasks.append(content[:80])
            emotion = memory.metadata.get("emotion") if isinstance(memory.metadata, dict) else ""
            if emotion and emotion not in emotions:
                emotions.append(emotion)
            topic = self._extract_topic(content)
            if topic and topic not in topics:
                topics.append(topic)

        lines = []
        if topics:
            lines.append("讨论主题: " + "、".join(topics[:6]))
        if facts:
            lines.append("沉淀事实: " + "；".join(facts[:6]))
        if tasks:
            lines.append("未必完成的事项: " + "；".join(tasks[:4]))
        if emotions:
            lines.append("情绪线索: " + "、".join(emotions[:4]))
        if not lines:
            compact = "；".join(
                re.sub(r"^\[(User:[^\]]+|Assistant)\]\s*", "", m.content).strip()[:60]
                for m in memories[-6:]
                if m.content.strip()
            )
            lines.append("近期片段: " + compact)
        return " | ".join(lines)

    def _maybe_record_episode(
        self,
        user_message: str,
        assistant_response: str,
        user_id: str = None,
        family_id: str = None,
        emotion: str = None,
    ):
        text = f"{user_message}\n{assistant_response}".strip()
        if not text:
            return
        episode_keywords = ["生日", "纪念日", "医院", "旅行", "聚会", "吵架", "搬家", "考试", "重要", "第一次"]
        if emotion in {"anger", "sadness", "anxiety"} or any(word in text for word in episode_keywords):
            self.add_memory(
                content=text[:500],
                memory_type=MemoryType.EPISODIC,
                source="chat_episode",
                importance=0.72 if emotion not in {"anger", "sadness", "anxiety"} else 0.86,
                tags=["episode", family_id or "global", user_id or "anonymous"],
                related_members=[user_id] if user_id else [],
                metadata={"user_id": user_id or "", "family_id": family_id or "", "emotion": emotion or ""},
            )

    def _extract_topic(self, text: str) -> str:
        keywords = ["购物", "日程", "健康", "照片", "财务", "任务", "知识库", "智能家居", "家庭成员", "孩子", "父母"]
        for keyword in keywords:
            if keyword in text:
                return keyword
        cleaned = re.sub(r"[，。！？,.!?\\s]+", " ", text).strip()
        return cleaned[:18] if 4 <= len(cleaned) <= 80 else ""

    def _upsert_summary(self, memory: Memory):
        self.conversation_summaries = [
            existing for existing in self.conversation_summaries
            if existing.id != memory.id
        ]
        self.conversation_summaries.append(memory)
        if self.long_term_collection:
            try:
                self.long_term_collection.upsert(
                    documents=[memory.content],
                    metadatas=[self._chroma_metadata(memory, {"type": "summary"})],
                    ids=[memory.id],
                )
            except Exception as e:
                print(f"摘要写入 Chroma 失败，保留本地摘要: {e}")

    def _search_summaries(self, query: str, min_importance: float,
                          user_id: str = None, family_id: str = None) -> List[Dict]:
        if not query:
            return [
                {"content": memory.content, "metadata": memory.to_dict(), "distance": 0.5, "memory": memory}
                for memory in reversed(self.conversation_summaries)
                if memory.importance >= min_importance
                and self._memory_matches_scope(memory.to_dict(), user_id=user_id, family_id=family_id)
            ]
        query_chars = set(query.lower())
        matches = []
        for memory in self.conversation_summaries:
            if memory.importance < min_importance:
                continue
            if not self._memory_matches_scope(memory.to_dict(), user_id=user_id, family_id=family_id):
                continue
            overlap = len(query_chars & set(memory.content.lower()))
            if overlap >= 2:
                matches.append({
                    "content": memory.content,
                    "metadata": memory.to_dict(),
                    "distance": 1.0 / (overlap + 1),
                    "memory": memory,
                })
        matches.sort(key=lambda item: item["distance"])
        return matches

    def _fit_context(self, parts: List[str], max_chars: int) -> str:
        selected = []
        used = 0
        for part in parts:
            if not part:
                continue
            remaining = max_chars - used
            if remaining <= 0:
                break
            if len(part) > remaining:
                selected.append(part[: max(0, remaining - 20)] + "\n...[已压缩截断]")
                break
            selected.append(part)
            used += len(part) + 2
        return "\n\n".join(selected)

    def _ensure_directory_writable(self, path: Path):
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_probe"
        try:
            probe.write_text("ok", encoding="utf-8")
        finally:
            try:
                probe.unlink(missing_ok=True)
            except OSError:
                pass

    def _upsert_fallback_memory(self, memory: Memory):
        self.long_term_fallback = [
            existing for existing in self.long_term_fallback
            if existing.id != memory.id
        ]
        self.long_term_fallback.append(memory)

    def _memory_scope_key(self, memory: Memory) -> tuple:
        data = memory.to_dict()
        return (
            self._metadata_family_id(data),
            self._metadata_user_id(data),
        )

    def _search_fallback_memories(
        self,
        query: str,
        memory_types: List[MemoryType],
        min_importance: float,
        user_id: str = None,
        family_id: str = None,
    ) -> List[Dict]:
        query_text = query.lower()
        query_chars = set(query_text)
        matches = []
        for memory in self.long_term_fallback:
            if memory.memory_type not in memory_types or memory.importance < min_importance:
                continue
            if not self._memory_matches_scope(memory.to_dict(), user_id=user_id, family_id=family_id):
                continue
            content = memory.content.lower()
            overlap = len(query_chars & set(content))
            if query_text in content or overlap >= 2:
                distance = 1.0 / (overlap + 1)
                matches.append({
                    "content": memory.content,
                    "metadata": memory.to_dict(),
                    "distance": distance,
                })
        matches.sort(key=lambda x: x["distance"])
        return matches

    def _split_fact_candidates(self, text: str) -> List[str]:
        candidates = []
        for part in re.split(r"[，。；;.!！?？\n]+", text):
            fact = part.strip(" ，。；;.!！?？")
            if 4 <= len(fact) <= 90:
                candidates.append(fact)
        return candidates

    def _memory_matches_scope(self, metadata: Dict, user_id: str = None, family_id: str = None) -> bool:
        if family_id:
            memory_family_id = self._metadata_family_id(metadata)
            if memory_family_id != family_id:
                return False
        return self._memory_matches_user(metadata, user_id)

    def _memory_matches_user(self, metadata: Dict, user_id: str = None) -> bool:
        if not user_id:
            return True
        memory_user_id = self._metadata_user_id(metadata)
        related_members = metadata.get("related_members") or []
        tags = metadata.get("tags") or []
        return (
            not memory_user_id
            or memory_user_id == user_id
            or user_id in related_members
            or user_id in tags
        )

    def _metadata_family_id(self, metadata: Dict) -> str:
        if not isinstance(metadata, dict):
            return ""
        if metadata.get("family_id"):
            return str(metadata["family_id"])
        nested = metadata.get("metadata")
        if isinstance(nested, dict) and nested.get("family_id"):
            return str(nested["family_id"])
        metadata_json = metadata.get("metadata_json")
        if metadata_json:
            try:
                parsed = json.loads(metadata_json)
                if isinstance(parsed, dict) and parsed.get("family_id"):
                    return str(parsed["family_id"])
            except (TypeError, ValueError):
                return ""
        return ""

    def _metadata_user_id(self, metadata: Dict) -> str:
        if not isinstance(metadata, dict):
            return ""
        if metadata.get("user_id"):
            return str(metadata["user_id"])
        nested = metadata.get("metadata")
        if isinstance(nested, dict) and nested.get("user_id"):
            return str(nested["user_id"])
        metadata_json = metadata.get("metadata_json")
        if metadata_json:
            try:
                parsed = json.loads(metadata_json)
                if isinstance(parsed, dict) and parsed.get("user_id"):
                    return str(parsed["user_id"])
            except (TypeError, ValueError):
                return ""
        return ""
