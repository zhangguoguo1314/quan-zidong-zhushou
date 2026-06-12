from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import text, inspect

from core.database import engine, Base, SessionLocal
from api.routes import auth, sites, accounts, tasks, logs, settings as settings_routes, config_generator
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
app.include_router(config_generator.router)


def _migrate_database():
    """启动时自动检测并补齐所有表缺失的列。"""
    try:
        # 1. 先创建所有尚未存在的表
        Base.metadata.create_all(bind=engine)

        # 2. 对已有表逐列检测，缺失则补齐
        inspector = inspect(engine)
        with engine.begin() as conn:
            # 遍历所有 ORM 模型定义的表
            for table_name, table in Base.metadata.tables.items():
                existing_columns = {col["name"] for col in inspector.get_columns(table_name)}
                for column in table.columns:
                    if column.name not in existing_columns:
                        # 根据列类型生成 ALTER TABLE 语句
                        col_type = column.type.compile(dialect=engine.dialect)
                        nullable = "NULL" if column.nullable else "NOT NULL"
                        # SQLite 不允许非空列无默认值，这里简化：所有补齐列都用 NULL
                        try:
                            conn.execute(text(
                                f'ALTER TABLE {table_name} ADD COLUMN "{column.name}" {col_type} NULL'
                            ))
                            print(f"[migrate] {table_name} 已添加列 {column.name} ({col_type})")
                        except Exception as e:
                            print(f"[migrate] {table_name}.{column.name} 添加失败: {e}")
    except Exception as e:
        print(f"[migrate] 数据库迁移失败: {e}")


@app.on_event("startup")
def on_startup():
    _migrate_database()

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
