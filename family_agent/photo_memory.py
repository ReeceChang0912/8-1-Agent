"""
照片记忆管理模块
支持照片标注、自然语言搜索、回忆生成
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
import hashlib


@dataclass
class PhotoMemory:
    """照片记忆"""
    photo_id: str
    filename: str
    upload_date: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    people: List[str] = field(default_factory=list)
    event: str = ""
    location: str = ""
    mood: str = ""  # happy/sad/neutral/etc.
    metadata: Dict = field(default_factory=dict)
    oss_url: str = ""  # 阿里云 OSS 访问地址

    def to_dict(self) -> Dict:
        return {
            "id": self.photo_id,
            "photo_id": self.photo_id,
            "filename": self.filename,
            "upload_date": self.upload_date,
            "description": self.description,
            "tags": self.tags,
            "people": self.people,
            "event": self.event,
            "location": self.location,
            "mood": self.mood,
            "metadata": self.metadata,
            "oss_url": self.oss_url
        }

    @staticmethod
    def from_dict(data: Dict) -> 'PhotoMemory':
        clean = {k: v for k, v in data.items() if k in {
            'photo_id', 'filename', 'upload_date', 'description',
            'tags', 'people', 'event', 'location', 'mood', 'metadata', 'oss_url'
        }}
        if 'photo_id' not in clean and 'id' in data:
            clean['photo_id'] = data['id']
        return PhotoMemory(**clean)


class PhotoMemoryManager:
    """
    照片记忆管理器
    
    功能：
    1. 照片上传和存储
    2. 自动标注（描述、人物、事件）
    3. 自然语言搜索
    4. 回忆生成（"去年的今天"）
    5. 相册分类
    """
    
    def __init__(self, photo_dir: str = "photos", index_file: str = "data/photo_index.json"):
        self.photo_dir = Path(photo_dir)
        self.photo_dir.mkdir(parents=True, exist_ok=True)
        
        self.index_file = Path(index_file)
        self.photos: Dict[str, PhotoMemory] = {}
        
        self._load_index()
    
    def add_photo(
        self,
        file_path: str,
        description: str = "",
        tags: List[str] = None,
        people: List[str] = None,
        event: str = "",
        location: str = "",
        mood: str = "",
        oss_url: str = ""
    ) -> str:
        """
        添加照片

        Args:
            file_path: 照片文件路径
            description: 描述
            tags: 标签列表
            people: 照片中的人物
            event: 相关事件
            location: 拍摄地点
            mood: 情绪氛围
            oss_url: 阿里云 OSS 访问地址

        Returns:
            照片ID
        """

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 生成照片ID
        photo_id = f"photo_{hashlib.md5(str(path).encode()).hexdigest()[:12]}"

        # 复制文件到照片目录（本地始终保留一份）
        dest_path = self.photo_dir / f"{photo_id}{path.suffix}"
        import shutil
        shutil.copy2(file_path, dest_path)

        # 创建照片记录
        photo = PhotoMemory(
            photo_id=photo_id,
            filename=dest_path.name,
            upload_date=datetime.now().isoformat(),
            description=description,
            tags=tags or [],
            people=people or [],
            event=event,
            location=location,
            mood=mood,
            oss_url=oss_url
        )

        self.photos[photo_id] = photo
        self._save_index()

        return photo_id
    
    def search_photos(
        self,
        query: str = None,
        tag: str = None,
        person: str = None,
        event: str = None,
        date_range: tuple = None,
        limit: int = 20
    ) -> List[PhotoMemory]:
        """
        搜索照片
        
        Args:
            query: 文本搜索（描述、标签）
            tag: 标签过滤
            person: 人物过滤
            event: 事件过滤
            date_range: 日期范围 (start, end)
            limit: 返回数量限制
        
        Returns:
            匹配的照片列表
        """
        
        results = list(self.photos.values())
        
        # 文本搜索
        if query:
            query_lower = query.lower()
            filtered = []
            for photo in results:
                # 搜索描述
                if query_lower in photo.description.lower():
                    filtered.append(photo)
                    continue
                
                # 搜索标签
                if any(query_lower in tag.lower() for tag in photo.tags):
                    filtered.append(photo)
                    continue
                
                # 搜索人物
                if any(query_lower in person.lower() for person in photo.people):
                    filtered.append(photo)
                    continue
            
            results = filtered
        
        # 标签过滤
        if tag:
            results = [p for p in results if tag in p.tags]
        
        # 人物过滤
        if person:
            results = [p for p in results if person in p.people]
        
        # 事件过滤
        if event:
            results = [p for p in results if event.lower() in p.event.lower()]
        
        # 日期范围过滤
        if date_range:
            start, end = date_range
            results = [
                p for p in results
                if start <= p.upload_date[:10] <= end
            ]
        
        # 按上传日期排序（最新的在前）
        results.sort(key=lambda x: x.upload_date, reverse=True)
        
        return results[:limit]
    
    def get_photos_by_person(self, person_name: str, limit: int = 20) -> List[PhotoMemory]:
        """获取特定人物的照片"""
        return self.search_photos(person=person_name, limit=limit)
    
    def get_photos_by_event(self, event_name: str, limit: int = 20) -> List[PhotoMemory]:
        """获取特定事件的照片"""
        return self.search_photos(event=event_name, limit=limit)
    
    def get_photos_by_tag(self, tag: str, limit: int = 20) -> List[PhotoMemory]:
        """获取特定标签的照片"""
        return self.search_photos(tag=tag, limit=limit)
    
    def get_memories_on_date(self, month: int, day: int) -> List[PhotoMemory]:
        """
        获取历史上今天（某月某日）的照片
        
        用于"去年的今天"功能
        """
        results = []
        
        for photo in self.photos.values():
            try:
                upload_date = datetime.fromisoformat(photo.upload_date)
                if upload_date.month == month and upload_date.day == day:
                    results.append(photo)
            except:
                pass
        
        # 按年份排序
        results.sort(key=lambda x: x.upload_date)
        
        return results
    
    def generate_memory_story(self, photo_ids: List[str]) -> str:
        """
        根据照片生成回忆故事
        
        Args:
            photo_ids: 照片ID列表
        
        Returns:
            回忆故事文本
        """
        
        photos = [self.photos[pid] for pid in photo_ids if pid in self.photos]
        
        if not photos:
            return "没有找到相关照片。"
        
        # 简单的故事生成
        story_parts = []
        
        # 提取共同的事件
        events = set(p.event for p in photos if p.event)
        people = set()
        for p in photos:
            people.update(p.people)
        
        if events:
            story_parts.append(f"回忆起{', '.join(events)}的美好时光...")
        
        if people:
            story_parts.append(f"和{', '.join(people)}一起")
        
        # 时间跨度
        dates = [p.upload_date[:10] for p in photos]
        if len(dates) > 1:
            story_parts.append(f"从{min(dates)}到{max(dates)}")
        
        story_parts.append(f"共有{len(photos)}张珍贵照片")
        
        story = "。".join(story_parts) + "。"
        
        return story
    
    def get_statistics(self) -> Dict:
        """获取照片统计信息"""
        total_photos = len(self.photos)
        
        # 按人物统计
        people_count = {}
        for photo in self.photos.values():
            for person in photo.people:
                if person not in people_count:
                    people_count[person] = 0
                people_count[person] += 1
        
        # 按标签统计
        tags_count = {}
        for photo in self.photos.values():
            for tag in photo.tags:
                if tag not in tags_count:
                    tags_count[tag] = 0
                tags_count[tag] += 1
        
        # 按事件统计
        events_count = {}
        for photo in self.photos.values():
            if photo.event:
                if photo.event not in events_count:
                    events_count[photo.event] = 0
                events_count[photo.event] += 1
        
        return {
            "total_photos": total_photos,
            "by_person": dict(sorted(people_count.items(), key=lambda x: x[1], reverse=True)[:10]),
            "by_tag": dict(sorted(tags_count.items(), key=lambda x: x[1], reverse=True)[:10]),
            "by_event": dict(sorted(events_count.items(), key=lambda x: x[1], reverse=True)[:10])
        }
    
    def delete_photo(self, photo_id: str) -> bool:
        """删除照片"""
        if photo_id not in self.photos:
            return False
        
        photo = self.photos[photo_id]
        
        # 删除文件
        photo_path = self.photo_dir / photo.filename
        if photo_path.exists():
            photo_path.unlink()
        
        # 删除索引
        del self.photos[photo_id]
        self._save_index()
        
        return True
    
    def _load_index(self):
        """加载照片索引"""
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.photos = {k: PhotoMemory.from_dict(v) for k, v in data.items()}
    
    def _save_index(self):
        """保存照片索引"""
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(
                {k: v.to_dict() for k, v in self.photos.items()},
                f, ensure_ascii=False, indent=2
            )
