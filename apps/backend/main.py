"""
FastAPI 后端服务 - 模块化路由版
提供 RESTful API 接口
"""
import sys
from pathlib import Path
import os
_backend_dir = str(Path(__file__).parent)
_apps_dir = str(Path(__file__).parent.parent)
_project_root = str(Path(__file__).parent.parent.parent)
sys.path = [_project_root, _apps_dir, _backend_dir] + sys.path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging

from family_agent.core import FamilyAgentCore
from family_agent.family_auth import FamilyAuthManager
from family_agent.database import DatabaseManager

# 导入路由模块
from backend.routers import auth, chat, members, shopping, schedule, photos, knowledge, skills, smarthome, tasks, stats, notifications, workbench, finance, memory, modules, life_modules

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_ENV = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "development")).lower()
DEBUG_ERRORS = os.getenv("DEBUG_ERRORS", "true" if APP_ENV != "production" else "false").lower() in {"1", "true", "yes", "on"}
_cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", "").split(",")
    if origin.strip()
]
if not _cors_origins and APP_ENV != "production":
    _cors_origins = ["*"]

# 创建 FastAPI 应用
app = FastAPI(
    title="家庭智能管家 API",
    description="Family Smart Agent Backend API",
    version="2.0.0 - 模块化路由版"
)

# 请求日志中间件（用于调试）
from starlette.middleware.base import BaseHTTPMiddleware

class _ErrorLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        import traceback as _tb
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            tb_str = ''.join(_tb.format_exception(type(exc), exc, exc.__traceback__))
            logger.error(f"中间件捕获 [{request.method} {request.url.path}]: {tb_str}")
            from fastapi.responses import JSONResponse
            if not DEBUG_ERRORS:
                return JSONResponse(
                    status_code=500,
                    content={"detail": "Internal Server Error"}
                )
            return JSONResponse(
                status_code=500,
                content={"detail": f"{type(exc).__name__}: {str(exc)}", "traceback": tb_str}
            )

app.add_middleware(_ErrorLogMiddleware)

# 配置 CORS
if APP_ENV == "production" and not _cors_origins:
    logger.warning("⚠️ 生产环境未配置 CORS_ALLOW_ORIGINS，浏览器跨域请求将被拒绝")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化 Agent（单例）
agent = None
auth_manager = None
db_manager = None

# 启动时提前初始化数据库和认证
try:
    _db_init = DatabaseManager()
    db_manager = _db_init
    logger.info("✅ PostgreSQL 数据库连接成功")
    auth_manager = FamilyAuthManager(db_manager=_db_init, data_dir="data")
    logger.info("✅ 认证管理器初始化完成")
except Exception as _e:
    logger.warning(f"⚠️ 启动初始化失败（请求时将重试）: {_e}")


def get_db_manager() -> DatabaseManager:
    """获取数据库管理器实例"""
    global db_manager
    if db_manager is None:
        try:
            db_manager = DatabaseManager()
            logger.info("✅ PostgreSQL 数据库连接成功")
        except Exception as e:
            logger.warning(f"⚠️ PostgreSQL 连接失败: {e}")
            db_manager = None
    return db_manager


def get_agent() -> FamilyAgentCore:
    """获取 Agent 实例"""
    global agent
    if agent is None:
        agent = FamilyAgentCore(data_dir="data")
        logger.info("✅ Agent 初始化完成")
    return agent


def get_auth_manager() -> FamilyAuthManager:
    """获取认证管理器实例"""
    global auth_manager
    if auth_manager is None:
        auth_manager = FamilyAuthManager(
            db_manager=get_db_manager(),
            data_dir="data"
        )
        logger.info("✅ 认证管理器初始化完成")
    return auth_manager


# ===== 注册路由 =====

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(chat.router, prefix="/api", tags=["聊天"])
app.include_router(members.router, prefix="/api", tags=["成员管理"])
app.include_router(shopping.router, prefix="/api", tags=["购物清单"])
app.include_router(schedule.router, prefix="/api", tags=["日程管理"])
app.include_router(photos.router, prefix="/api", tags=["照片管理"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["知识库"])
app.include_router(skills.router, prefix="/api", tags=["技能中心"])
app.include_router(smarthome.router, prefix="/api", tags=["智能家居"])
app.include_router(tasks.router, prefix="/api", tags=["任务管理"])
app.include_router(stats.router, prefix="/api", tags=["统计信息"])
app.include_router(notifications.router, prefix="/api", tags=["推送通知"])
app.include_router(workbench.router, prefix="/api", tags=["工作台"])
app.include_router(finance.router, prefix="/api", tags=["家庭财务"])
app.include_router(memory.router, prefix="/api", tags=["记忆管理"])
app.include_router(modules.router, prefix="/api", tags=["平台模块"])
app.include_router(life_modules.router, prefix="/api", tags=["生活模块"])


# ===== 根路径 =====

@app.get("/api")
def root():
    """API 根路径"""
    return {
        "message": "家庭智能管家 API 运行中",
        "version": "2.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "ok", "service": "family-agent-api"}


# 挂载静态文件服务(照片目录)
photos_path = Path("photos")
photos_path.mkdir(parents=True, exist_ok=True)
app.mount("/api/photos", StaticFiles(directory=str(photos_path)), name="photos")
logger.info("✅ 照片静态文件服务已挂载: /api/photos")

# 挂载前端构建产物（生产环境）
frontend_dist = Path(__file__).parent.parent / "web" / "dist"
if frontend_dist.exists():

    # Vite 构建的静态资源（带 hash，可直接缓存）
    assets_path = frontend_dist / "assets"
    if assets_path.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_path)), name="frontend_assets")

    # SPA 回退路由：所有非 API 路径返回 index.html（放在最后注册）
    from fastapi.responses import FileResponse, JSONResponse

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        # 排除 API 路径
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi"):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        return FileResponse(str(frontend_dist / "index.html"))

    logger.info("✅ 前端静态文件已挂载")
else:
    logger.warning("⚠️ 前端构建产物不存在（apps/web/dist），请运行: cd apps/web && npm run build")


if __name__ == "__main__":
    import uvicorn
    # 用 Config + Server 方式启动，确保环境变量传递正确
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8000,
        http="h11",
        loop="asyncio",
        log_level="info",
    )
    server = uvicorn.Server(config)
    server.run()
