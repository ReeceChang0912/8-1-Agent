"""
智能照片分析器
使用 AI 自动生成照片描述、标签和人物识别
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path

from .photo_memory import PhotoMemoryManager
from .llm_adapter import LLMAdapter


class SmartPhotoAnalyzer:
    """
    智能照片分析器
    
    功能：
    1. 定期扫描未标注的照片
    2. 使用多模态 AI 分析照片内容
    3. 自动生成描述、标签、人物识别
    4. 智能分类和情绪识别
    5. 批量处理和历史照片挖掘
    """
    
    def __init__(self, photo_manager: PhotoMemoryManager, llm_adapter: LLMAdapter = None):
        self.photo_manager = photo_manager
        self.llm_adapter = llm_adapter
        self.analysis_log_file = Path("data/photo_analysis_log.json")
        self._load_analysis_log()
    
    def analyze_unannotated_photos(self, batch_size: int = 10) -> Dict:
        """
        分析未标注的照片
        
        Args:
            batch_size: 每批处理的照片数量
        
        Returns:
            处理结果统计
        """
        
        # 获取所有照片
        all_photos = list(self.photo_manager.photos.values())
        
        # 筛选出缺少描述或标签的照片
        unannotated = [
            p for p in all_photos 
            if not p.description or len(p.tags) == 0
        ]
        
        if not unannotated:
            return {"status": "completed", "message": "所有照片已标注", "processed": 0}
        
        # 限制批次大小
        to_process = unannotated[:batch_size]
        
        results = {
            "total_found": len(unannotated),
            "processing": len(to_process),
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        for photo in to_process:
            try:
                analysis = self._analyze_single_photo(photo)
                
                if analysis:
                    # 更新照片信息
                    photo.description = analysis.get('description', photo.description)
                    photo.tags = analysis.get('tags', photo.tags)
                    photo.people = analysis.get('people', photo.people)
                    photo.event = analysis.get('event', photo.event)
                    photo.location = analysis.get('location', photo.location)
                    photo.mood = analysis.get('mood', photo.mood)
                    
                    # 保存更新
                    self.photo_manager._save_index()
                    
                    results["success"] += 1
                    results["details"].append({
                        "photo_id": photo.photo_id,
                        "status": "success",
                        "analysis": analysis
                    })
                    
                    # 记录分析日志
                    self._log_analysis(photo.photo_id, analysis)
                else:
                    results["failed"] += 1
                    
            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "photo_id": photo.photo_id,
                    "status": "failed",
                    "error": str(e)
                })
        
        return results
    
    def _analyze_single_photo(self, photo: 'PhotoMemory') -> Optional[Dict]:
        """
        分析单张照片
        
        如果有 LLM 适配器且支持视觉,使用 AI 分析
        否则使用基于元数据的启发式分析
        """
        
        if self.llm_adapter and hasattr(self.llm_adapter, 'analyze_image'):
            # 使用多模态 AI 分析
            return self._analyze_with_ai(photo)
        else:
            # 使用启发式分析
            return self._analyze_heuristic(photo)
    
    def _analyze_with_ai(self, photo: 'PhotoMemory') -> Optional[Dict]:
        """使用 AI 分析照片"""
        
        try:
            # 构建照片路径
            photo_path = self.photo_manager.photo_dir / photo.filename
            
            if not photo_path.exists():
                return None
            
            # 调用 AI 分析
            prompt = f"""
请分析这张家庭照片,提供以下信息(用JSON格式返回):
{{
    "description": "详细描述照片内容,包括人物、场景、活动(50-100字)",
    "tags": ["标签1", "标签2", "标签3"], // 3-5个关键词标签
    "people": ["人物1", "人物2"], // 推测的人物角色,如"爸爸","妈妈","孩子"
    "event": "事件类型,如生日聚会/家庭聚餐/旅行/日常",
    "location": "拍摄地点,如家中/公园/餐厅/户外",
    "mood": "情绪氛围,如happy/sad/neutral/excited/calm"
}}

要求:
1. 描述要温馨、自然,体现家庭温情
2. 标签要具体,便于搜索
3. 人物角色要根据年龄、性别推测
4. 如果无法确定某些字段,留空字符串或空数组
"""
            
            # 这里假设 LLMAdapter 有 analyze_image 方法
            # 实际实现需要根据具体的 LLM API 调整
            result = self.llm_adapter.analyze_image(str(photo_path), prompt)
            
            # 解析 JSON 结果
            if isinstance(result, str):
                import re
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            
            return result if isinstance(result, dict) else None
            
        except Exception as e:
            print(f"AI 分析失败: {e}")
            return None
    
    def _analyze_heuristic(self, photo: 'PhotoMemory') -> Dict:
        """
        启发式分析(基于文件名、日期等元数据)
        
        当没有多模态 AI 时使用
        """
        
        analysis = {
            "description": "",
            "tags": [],
            "people": [],
            "event": "",
            "location": "",
            "mood": "neutral"
        }
        
        # 基于上传日期推测
        try:
            upload_date = datetime.fromisoformat(photo.upload_date)
            
            # 周末可能是家庭活动
            if upload_date.weekday() >= 5:
                analysis["tags"].append("周末")
                analysis["mood"] = "happy"
            
            # 节假日检测
            month = upload_date.month
            day = upload_date.day
            
            if month == 1 and day == 1:
                analysis["event"] = "元旦"
                analysis["tags"].extend(["节日", "新年"])
            elif month == 2 and day == 14:
                analysis["event"] = "情人节"
                analysis["tags"].extend(["节日", "浪漫"])
            elif month == 10 and day == 1:
                analysis["event"] = "国庆节"
                analysis["tags"].extend(["节日", "假期"])
            elif month == 12 and day == 25:
                analysis["event"] = "圣诞节"
                analysis["tags"].extend(["节日", "庆祝"])
            
            # 生成基础描述
            date_str = upload_date.strftime("%Y年%m月%d日")
            weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][upload_date.weekday()]
            analysis["description"] = f"{date_str}({weekday})的家庭照片"
            
        except:
            pass
        
        # 基于已有信息补充
        if photo.location:
            analysis["location"] = photo.location
            analysis["tags"].append("外出" if photo.location != "家" else "居家")
        
        if photo.event:
            analysis["event"] = photo.event
        
        # 去重标签
        analysis["tags"] = list(set(analysis["tags"]))
        
        return analysis
    
    def smart_categorize_photos(self) -> Dict:
        """
        智能分类照片
        
        Returns:
            分类结果
        """
        
        categories = {
            "人物合影": [],
            "风景照": [],
            "美食": [],
            "节日庆典": [],
            "日常生活": [],
            "旅行": [],
            "其他": []
        }
        
        for photo in self.photo_manager.photos.values():
            # 基于标签和描述分类
            tags_lower = [t.lower() for t in photo.tags]
            desc_lower = photo.description.lower()
            
            if any(kw in tags_lower or kw in desc_lower for kw in ["全家福", "合影", "家人"]):
                categories["人物合影"].append(photo.photo_id)
            elif any(kw in tags_lower or kw in desc_lower for kw in ["风景", "自然", "山水"]):
                categories["风景照"].append(photo.photo_id)
            elif any(kw in tags_lower or kw in desc_lower for kw in ["美食", "吃饭", "聚餐"]):
                categories["美食"].append(photo.photo_id)
            elif any(kw in tags_lower or kw in desc_lower for kw in ["生日", "节日", "庆典"]):
                categories["节日庆典"].append(photo.photo_id)
            elif any(kw in tags_lower or kw in desc_lower for kw in ["旅行", "旅游", "度假"]):
                categories["旅行"].append(photo.photo_id)
            else:
                categories["日常生活"].append(photo.photo_id)
        
        return categories
    
    def generate_auto_albums(self) -> List[Dict]:
        """
        自动生成相册
        
        Returns:
            相册列表
        """
        
        albums = []
        
        # 按人物生成相册
        people_photos = {}
        for photo in self.photo_manager.photos.values():
            for person in photo.people:
                if person not in people_photos:
                    people_photos[person] = []
                people_photos[person].append(photo.photo_id)
        
        for person, photo_ids in people_photos.items():
            if len(photo_ids) >= 3:  # 至少3张照片才生成相册
                albums.append({
                    "name": f"{person}的专属相册",
                    "type": "person",
                    "photo_count": len(photo_ids),
                    "photo_ids": photo_ids,
                    "cover_photo": photo_ids[0]
                })
        
        # 按事件生成相册
        event_photos = {}
        for photo in self.photo_manager.photos.values():
            if photo.event:
                if photo.event not in event_photos:
                    event_photos[photo.event] = []
                event_photos[photo.event].append(photo.photo_id)
        
        for event, photo_ids in event_photos.items():
            if len(photo_ids) >= 2:
                albums.append({
                    "name": f"{event}相册",
                    "type": "event",
                    "photo_count": len(photo_ids),
                    "photo_ids": photo_ids,
                    "cover_photo": photo_ids[0]
                })
        
        # 按时间生成年度相册
        year_photos = {}
        for photo in self.photo_manager.photos.values():
            try:
                year = photo.upload_date[:4]
                if year not in year_photos:
                    year_photos[year] = []
                year_photos[year].append(photo.photo_id)
            except:
                pass
        
        for year, photo_ids in year_photos.items():
            if len(photo_ids) >= 5:
                albums.append({
                    "name": f"{year}年回忆",
                    "type": "time",
                    "photo_count": len(photo_ids),
                    "photo_ids": photo_ids,
                    "cover_photo": photo_ids[0]
                })
        
        return albums
    
    def schedule_periodic_analysis(self, interval_hours: int = 24):
        """
        设置定期分析任务
        
        Args:
            interval_hours: 分析间隔(小时)
        """
        
        import schedule
        import time
        
        def job():
            print(f"[{datetime.now()}] 开始定期照片分析...")
            result = self.analyze_unannotated_photos(batch_size=20)
            print(f"分析完成: {result}")
        
        # 设置定时任务
        schedule.every(interval_hours).hours.do(job)
        
        print(f"已设置每 {interval_hours} 小时执行一次照片分析")
        
        # 在后台运行
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    def _load_analysis_log(self):
        """加载分析日志"""
        if self.analysis_log_file.exists():
            with open(self.analysis_log_file, 'r', encoding='utf-8') as f:
                self.analysis_log = json.load(f)
        else:
            self.analysis_log = {}
    
    def _log_analysis(self, photo_id: str, analysis: Dict):
        """记录分析日志"""
        self.analysis_log[photo_id] = {
            "analyzed_at": datetime.now().isoformat(),
            "analysis": analysis
        }
        
        # 保存日志
        with open(self.analysis_log_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_log, f, ensure_ascii=False, indent=2)
    
    def get_analysis_stats(self) -> Dict:
        """获取分析统计"""
        
        total = len(self.photo_manager.photos)
        annotated = sum(
            1 for p in self.photo_manager.photos.values()
            if p.description and len(p.tags) > 0
        )
        
        return {
            "total_photos": total,
            "annotated_photos": annotated,
            "unannotated_photos": total - annotated,
            "annotation_rate": round(annotated / total * 100, 2) if total > 0 else 0,
            "last_analysis": max(
                (v["analyzed_at"] for v in self.analysis_log.values()),
                default=None
            )
        }
