"""
照片管理路由
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
from typing import Optional
import shutil
from pathlib import Path

router = APIRouter()


def get_agent():
    from backend.main import get_agent as _get_agent
    return _get_agent()


def get_oss():
    from family_agent.oss_manager import get_oss_manager
    return get_oss_manager()


@router.get("/photos")
async def get_photos(query: Optional[str] = None):
    agent = get_agent()
    if query:
        results = agent.photo_memory.search_photos(query=query, limit=20)
        return {"photos": [p.to_dict() for p in results], "total": len(results)}
    else:
        photos = list(agent.photo_memory.photos.values())
        return {"photos": [p.to_dict() for p in photos], "total": len(photos)}


def parse_csv(value: str):
    return [item.strip() for item in (value or "").replace("，", ",").split(",") if item.strip()]


@router.post("/photos/upload")
async def upload_photo(
    file: UploadFile = File(...),
    description: str = Form(default=""),
    tags: str = Form(default=""),
    people: str = Form(default=""),
    location: str = Form(default=""),
    event: str = Form(default=""),
    mood: str = Form(default=""),
):
    try:
        photo_dir = Path("photos")
        photo_dir.mkdir(exist_ok=True)
        file_path = photo_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        agent = get_agent()

        # 上传到阿里云 OSS
        oss = get_oss()
        oss_url = ""
        if oss.enabled:
            remote_path = f"photos/{file.filename}"
            oss_url = oss.upload_file(str(file_path), remote_path) or ""

        # 添加到照片记忆
        photo_id = agent.photo_memory.add_photo(
            str(file_path),
            description=description,
            tags=parse_csv(tags),
            people=parse_csv(people),
            event=event,
            location=location,
            mood=mood,
            oss_url=oss_url,
        )
        return {
            "success": True,
            "filename": file.filename,
            "photo_id": photo_id,
            "oss_url": oss_url,
            "message": "照片上传成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/photos/analyze")
async def analyze_photos(batch_size: int = 10):
    agent = get_agent()
    results = agent.photo_analyzer.analyze_unannotated_photos(batch_size=batch_size)
    return {"success": True, "results": results}


@router.get("/photos/analysis-stats")
async def get_analysis_stats():
    agent = get_agent()
    stats = agent.photo_analyzer.get_analysis_stats()
    return stats


@router.get("/photos/albums")
async def get_albums():
    agent = get_agent()
    albums = agent.photo_analyzer.generate_auto_albums()
    return {"albums": albums}
