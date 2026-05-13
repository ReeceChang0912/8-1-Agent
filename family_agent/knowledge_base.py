"""
家庭知识库管理系统
"""

import json
import hashlib
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime
import chromadb
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


class KnowledgeBase:
    """家庭知识库"""
    
    CATEGORIES = {
        "health": "健康医疗",
        "finance": "理财规划",
        "relationship": "家庭关系",
        "education": "子女教育",
        "travel": "旅游攻略",
        "cooking": "烹饪食谱",
        "legal": "法律常识",
        "general": "通用知识"
    }
    
    def __init__(self, kb_dir: str = "data/knowledge_docs", db_dir: str = "data/knowledge_db"):
        self.kb_dir = Path(kb_dir)
        self.kb_dir.mkdir(parents=True, exist_ok=True)
        
        for cat in self.CATEGORIES.keys():
            (self.kb_dir / cat).mkdir(exist_ok=True)
        
        self.chroma_client = chromadb.PersistentClient(path=db_dir)
        
        try:
            self.collection = self.chroma_client.get_collection("family_knowledge")
        except:
            self.collection = self.chroma_client.create_collection(
                name="family_knowledge",
                metadata={"description": "家庭综合知识库"}
            )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
        )
        
        self.metadata_index_file = Path(db_dir) / "metadata_index.json"
        self.metadata_index: Dict[str, Dict] = {}
        self._load_metadata_index()
    
    def add_document(self, file_path: str, category: str = "general", 
                    tags: List[str] = None, description: str = "") -> str:
        """添加文档到知识库"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        if category not in self.CATEGORIES:
            category = "general"
        
        doc_id = f"doc_{hashlib.md5(str(path).encode()).hexdigest()[:12]}"
        
        # 加载文档
        try:
            if path.suffix.lower() == '.pdf':
                loader = PyPDFLoader(str(path))
            else:
                loader = TextLoader(str(path), encoding='utf-8')
            
            documents = loader.load()
        except Exception as e:
            raise ValueError(f"无法加载文档: {e}")
        
        # 分割文本
        texts = self.text_splitter.split_documents(documents)
        
        if not texts:
            raise ValueError("文档内容为空")
        
        now = datetime.now().isoformat()
        
        ids = []
        metadatas = []
        documents_content = []
        
        for i, text in enumerate(texts):
            chunk_id = f"{doc_id}_chunk_{i}"
            
            chunk_metadata = {
                "doc_id": doc_id,
                "title": path.stem,
                "source": str(path),
                "category": category,
                "file_type": path.suffix.lower(),
                "chunk_index": i,
                "total_chunks": len(texts),
                "upload_time": now,
                "tags": json.dumps(tags or []),
                "importance": 0.5
            }
            
            ids.append(chunk_id)
            metadatas.append(chunk_metadata)
            documents_content.append(text.page_content)
        
        self.collection.add(
            ids=ids,
            documents=documents_content,
            metadatas=metadatas
        )
        
        doc_metadata = {
            "doc_id": doc_id,
            "title": path.stem,
            "source": str(path),
            "category": category,
            "file_type": path.suffix.lower(),
            "upload_time": now,
            "update_time": now,
            "tags": tags or [],
            "description": description,
            "importance": 0.5,
            "chunk_count": len(texts)
        }
        
        self.metadata_index[doc_id] = doc_metadata
        self._save_metadata_index()
        
        return doc_id
    
    def add_text(self, text: str, title: str, category: str = "note", 
                tags: List[str] = None) -> str:
        """直接添加文本"""
        doc_id = f"text_{hashlib.md5(title.encode()).hexdigest()[:12]}"
        
        doc_metadata = {
            "doc_id": doc_id,
            "title": title,
            "source": "manual_input",
            "category": category,
            "file_type": ".txt",
            "upload_time": datetime.now().isoformat(),
            "update_time": datetime.now().isoformat(),
            "tags": tags or [],
            "description": "",
            "importance": 0.5,
            "chunk_count": 1
        }
        
        self.collection.add(
            ids=[doc_id],
            documents=[text],
            metadatas=[{**doc_metadata, "tags": json.dumps(tags or [])}]
        )
        
        self.metadata_index[doc_id] = doc_metadata
        self._save_metadata_index()
        
        return doc_id
    
    def search(self, query: str, category: str = None, n_results: int = 5) -> List[Dict]:
        """搜索知识库"""
        where_filter = {"category": category} if category else None
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter if where_filter else None
            )
            
            formatted_results = []
            if results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        "content": doc,
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i] if 'distances' in results else None
                    })
            
            return formatted_results
        except Exception as e:
            print(f"搜索失败: {e}")
            return []
    
    def list_documents(self, category: str = None, limit: int = 50) -> List[Dict]:
        """列出文档"""
        docs = list(self.metadata_index.values())
        
        if category:
            docs = [doc for doc in docs if doc.get('category') == category]
        
        docs.sort(key=lambda x: x.get('upload_time', ''), reverse=True)
        
        return docs[:limit]
    
    def get_document_detail(self, doc_id: str) -> Dict:
        """获取文档详情"""
        if doc_id not in self.metadata_index:
            return {}
        
        doc_metadata = self.metadata_index[doc_id].copy()
        
        # 从 ChromaDB 中获取文档内容
        try:
            results = self.collection.get(
                ids=[doc_id],
                include=['documents']
            )
            
            if results['documents'] and len(results['documents']) > 0:
                doc_metadata['content'] = results['documents'][0]
            else:
                doc_metadata['content'] = ''
        except Exception as e:
            print(f"获取文档内容失败: {e}")
            doc_metadata['content'] = ''
        
        return doc_metadata
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        stats = {
            "total_documents": len(self.metadata_index),
            "categories": {},
            "recent_uploads": []
        }
        
        for doc in self.metadata_index.values():
            cat = doc.get('category', 'unknown')
            if cat not in stats["categories"]:
                stats["categories"][cat] = 0
            stats["categories"][cat] += 1
        
        sorted_docs = sorted(
            self.metadata_index.values(),
            key=lambda x: x.get('upload_time', ''),
            reverse=True
        )
        stats["recent_uploads"] = sorted_docs[:5]
        
        return stats
    
    def _load_metadata_index(self):
        """加载元数据索引"""
        if self.metadata_index_file.exists():
            with open(self.metadata_index_file, 'r', encoding='utf-8') as f:
                self.metadata_index = json.load(f)
    
    def _save_metadata_index(self):
        """保存元数据索引"""
        self.metadata_index_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.metadata_index_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata_index, f, ensure_ascii=False, indent=2)
