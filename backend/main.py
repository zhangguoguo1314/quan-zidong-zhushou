from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import text

from core.database import engine, Base
from api.routes import auth, sites, accounts, tasks, logs, settings as settings_routes
from tasks.scheduler import start_scheduler, stop_scheduler, scheduler

app = FastAPI(title="Account-Auto-Sign API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(sites.router)
app.include_router(accounts.router)
app.include_router(tasks.router)
app.include_router(logs.router)
app.include_router(settings_routes.router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    # 为旧版本数据库添加缺失列
    try:
        with engine.begin() as conn:
            columns = conn.execute(text("PRAGMA table_info(sites)")).fetchall()
            col_names = {col[1] for col in columns}
            if "api_config" not in col_names:
                conn.execute(text("ALTER TABLE sites ADD COLUMN api_config TEXT"))
            if "display_name" not in col_names:
                conn.execute(text("ALTER TABLE sites ADD COLUMN display_name TEXT DEFAULT ''"))
            if "category" not in col_names:
                conn.execute(text("ALTER TABLE sites ADD COLUMN category TEXT DEFAULT '其他'"))
    except Exception as e:
        print(f"[main] 迁移数据库列失败: {e}")

    if not scheduler.running:
        start_scheduler()


@app.on_event("shutdown")
def on_shutdown():
    if scheduler.running:
        stop_scheduler()


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "scheduler": "running" if scheduler.running else "stopped"}


STATIC_DIR = Path(__file__).resolve().parent / "static"


@app.get("/{full_path:path}")
def serve_frontend(full_path: str):
    if not STATIC_DIR.exists():
        raise HTTPException(status_code=404, detail="Frontend static files not found")
    requested_path = (STATIC_DIR / full_path).resolve()
    if requested_path.is_file() and STATIC_DIR in requested_path.parents:
        return FileResponse(requested_path)
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="Frontend entry file not found")
