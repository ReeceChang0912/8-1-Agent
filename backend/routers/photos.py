"""
照片管理路由
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
import shutil
from pathlib import Path

router = APIRouter()

class PhotoQuery(BaseModel):
    query: Optional[str] = None


def get_agent():
    from main import get_agent as _get_agent
    return _get_agent()


@router.get("/photos")
async def get_photos(query: Optional[str] = None):
    """获取照片列表"""
    agent = get_agent()
    
    if query:
        results = agent.photo_memory.search(query, limit=20)
        return {"photos": results, "total": len(results)}
    else:
        photos = agent.photo_memory.get_all()
        return {"photos": photos, "total": len(photos)}


@router.post("/photos/upload")
async def upload_photo(file: UploadFile = File(...)):
    """上传照片"""
    try:
        # 确保目录存在
        photo_dir = Path("photos")
        photo_dir.mkdir(exist_ok=True)
        
        # 保存文件
        file_path = photo_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 添加到照片记忆
        agent = get_agent()
        agent.photo_memory.add_photo(str(file_path))
        
        return {
            "success": True,
            "filename": file.filename,
            "message": "照片上传成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/photos/analyze")
async def analyze_photos(batch_size: int = 20):
    """智能分析照片"""
    agent = get_agent()
    results = agent.smart_analyzer.analyze_batch(batch_size=batch_size)
    return {"success": True, "analyzed": len(results), "results": results}


@router.get("/photos/analysis-stats")
async def get_analysis_stats():
    """获取分析统计"""
    agent = get_agent()
    stats = agent.smart_analyzer.get_statistics()
    return stats


@router.get("/photos/albums")
async def get_albums():
    """获取自动相册"""
    agent = get_agent()
    albums = agent.smart_analyzer.get_auto_albums()
    return {"albums": albums}
