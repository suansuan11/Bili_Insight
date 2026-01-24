"""Bili-Insight Python分析服务 - FastAPI应用"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import analyze, popular, credential, login, analysis
from .config import settings
from .services.credential_manager import get_credential_manager

# 创建FastAPI应用实例
app = FastAPI(
    title="Bili-Insight Analysis Service",
    description="B站视频分析微服务 - 提供爬虫、NLP情感分析、时间轴生成、扫码登录功能",
    version="1.0.0"
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化凭证管理器（启动时加载默认凭证）
get_credential_manager()

# 注册路由
app.include_router(analyze.router, prefix="/api/analyze", tags=["分析服务"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["视频完整分析"])
app.include_router(popular.router, prefix="/api/popular", tags=["热门视频"])
app.include_router(credential.router, prefix="/api/credential", tags=["凭证管理"])
app.include_router(login.router, prefix="/api/login", tags=["扫码登录"])


@app.get("/")
async def root():
    """根路径健康检查"""
    return {
        "service": "Bili-Insight Analysis Service",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "database": "connected"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.service_host,
        port=settings.service_port,
        reload=True
    )
