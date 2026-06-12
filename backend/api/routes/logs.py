from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from io import StringIO

from core.database import get_db
from models.log import Log
from models.task import Task
from models.account import Account
from schemas.log import LogResponse
from api.deps import get_current_user
from models.user import User

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("", response_model=List[LogResponse])
def get_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    task_id: Optional[int] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Log).join(Task).join(Account).filter(
        Account.user_id == current_user.id
    )

    if task_id:
        query = query.filter(Log.task_id == task_id)

    if status_filter:
        query = query.filter(Log.status == status_filter)

    logs = query.order_by(Log.created_at.desc()).offset(skip).limit(limit).all()
    return logs


@router.get("/export")
def export_logs(
    status_filter: Optional[str] = Query(None, alias="status"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    task_id: Optional[int] = None,
    limit: int = Query(1000, ge=1, le=10000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出日志为 CSV 格式"""
    query = db.query(Log).join(Task).join(Account).filter(
        Account.user_id == current_user.id
    )

    if status_filter:
        query = query.filter(Log.status == status_filter)

    if task_id:
        query = query.filter(Log.task_id == task_id)

    if start_date:
        query = query.filter(Log.created_at >= start_date)

    if end_date:
        query = query.filter(Log.created_at <= end_date)

    logs = query.order_by(Log.created_at.desc()).limit(limit).all()

    # 生成 CSV
    csv_buffer = StringIO()
    csv_buffer.write("\ufeff")  # BOM for Excel UTF-8
    csv_buffer.write("ID,任务ID,状态,结果,创建时间\n")

    for log in logs:
        created_at_str = log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else ""
        result_str = (log.result or "").replace('"', '""')
        csv_buffer.write(f'{log.id},{log.task_id},{log.status},"{result_str}","{created_at_str}"\n')

    csv_content = csv_buffer.getvalue()

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8; header=attachment; filename=logs.csv",
        headers={"Content-Disposition": "attachment; filename=logs.csv"}
    )


@router.get("/{log_id}")
def get_log_detail(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单条日志详情（包含完整的 raw_response）"""
    log = db.query(Log).join(Task).join(Account).filter(
        Log.id == log_id,
        Account.user_id == current_user.id
    ).first()

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log not found"
        )

    return {
        "id": log.id,
        "task_id": log.task_id,
        "result": log.result,
        "status": log.status,
        "raw_response": log.raw_response or "",
        "created_at": log.created_at,
    }


@router.delete("/{log_id}")
def delete_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    log = db.query(Log).join(Task).join(Account).filter(
        Log.id == log_id,
        Account.user_id == current_user.id
    ).first()

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log not found"
        )

    db.delete(log)
    db.commit()
    return {"message": "Log deleted successfully"}


@router.delete("")
def delete_all_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 先查询出要删除的日志 ID，再逐个删除（避免 SQLAlchemy 的 join delete 限制）
    logs_to_delete = db.query(Log).join(Task).join(Account).filter(
        Account.user_id == current_user.id
    ).all()

    count = len(logs_to_delete)
    for log in logs_to_delete:
        db.delete(log)
    db.commit()
    return {"message": f"All logs deleted successfully ({count} records)"}
