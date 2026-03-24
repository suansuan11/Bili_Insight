"""Bili-Insight Python分析服务 - FastAPI应用"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import popular, credential, login, analysis
from .config import settings
from .middleware import APIKeyMiddleware
from .utils.logger import logger

# 创建FastAPI应用实例
logger.info("=" * 60)
logger.info("Bili-Insight Python分析服务启动中...")
logger.info("=" * 60)

app = FastAPI(
    title="Bili-Insight Analysis Service",
    description="B站视频分析微服务 - 提供爬虫、NLP情感分析、时间轴生成、扫码登录功能",
    version="1.0.0"
)

logger.info("FastAPI应用实例创建完成")

# 添加API密钥认证中间件（必须在CORS之前）
logger.info("添加API密钥认证中间件")
app.add_middleware(APIKeyMiddleware)

# 配置CORS中间件
logger.info("配置CORS中间件 - 允许所有来源")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
logger.info("注册API路由...")
app.include_router(analysis.router, prefix="/api/analysis", tags=["视频完整分析"])
logger.info("  ✓ 视频完整分析路由: /api/analysis")
app.include_router(popular.router, prefix="/api/popular", tags=["热门视频"])
logger.info("  ✓ 热门视频路由: /api/popular")
app.include_router(credential.router, prefix="/api/credential", tags=["凭证管理"])
logger.info("  ✓ 凭证管理路由: /api/credential")
app.include_router(login.router, prefix="/api/login", tags=["扫码登录"])
logger.info("  ✓ 扫码登录路由: /api/login")


@app.get("/")
async def root():
    """根路径健康检查"""
    logger.debug("收到根路径健康检查请求")
    return {
        "service": "Bili-Insight Analysis Service",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    logger.debug("收到健康检查请求")
    return {
        "status": "healthy",
        "database": "connected"
    }


logger.info("=" * 60)
logger.info(f"服务配置: {settings.service_host}:{settings.service_port}")
logger.info(f"数据库: {settings.db_host}:{settings.db_port}/{settings.db_name}")
logger.info("Bili-Insight Python分析服务启动完成")
logger.info("=" * 60)


if __name__ == "__main__":
    import uvicorn
    logger.info("直接运行模式 - 启动Uvicorn服务器")
    uvicorn.run(
        "app.main:app",
        host=settings.service_host,
        port=settings.service_port,
        reload=True
    )
