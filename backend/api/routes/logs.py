from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

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
