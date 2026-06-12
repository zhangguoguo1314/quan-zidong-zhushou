from pathlib import Path
import os
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import text, inspect

from core.database import engine, Base, SessionLocal
from core.config import settings
from api.routes import auth, sites, accounts, tasks, logs, settings as settings_routes, config_generator
from tasks.scheduler import start_scheduler, stop_scheduler, scheduler

logger = logging.getLogger(__name__)

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


def check_permissions():
    """检查关键目录和文件的读写权限"""
    # 检查数据库目录
    db_url = getattr(settings, "DATABASE_URL", "") or "sqlite:///./data.db"
    db_path = db_url.replace("sqlite:///", "").replace("sqlite://", "")
    if db_path:
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"[permission] 创建数据库目录: {db_dir}")
            except Exception as e:
                logger.error(f"[permission] 无法创建数据库目录 {db_dir}: {e}")

    # 检查 static 目录
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.exists(static_dir):
        test_file = os.path.join(static_dir, ".permission_test")
        try:
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            logger.info(f"[permission] static 目录读写正常: {static_dir}")
        except Exception as e:
            logger.error(f"[permission] static 目录权限异常: {e}")

    logger.info("[permission] 文件权限检查完成")


@app.on_event("startup")
def on_startup():
    _migrate_database()
    check_permissions()

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
