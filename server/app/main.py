"""
服务端主程序入口
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .api import auth, order, user, admin, web3_auth
from .database import engine, Base
from .config import settings

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 创建FastAPI应用
app = FastAPI(
    title="币安事件合约群控交易系统 - 服务端",
    description="后台管理系统API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(order.router)
app.include_router(user.router)
app.include_router(admin.router)
app.include_router(web3_auth.router)

# 静态文件和模板
templates = Jinja2Templates(directory="app/templates")


@app.get("/")
def root():
    """根路径"""
    return {
        "message": "币安事件合约群控交易系统 - 服务端API",
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    """健康检查"""
    from .redis_client import check_redis_connection
    redis_ok = check_redis_connection()
    
    return {
        "status": "ok",
        "redis": "ok" if redis_ok else "error"
    }


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """后台管理页面"""
    return templates.TemplateResponse("admin.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )

