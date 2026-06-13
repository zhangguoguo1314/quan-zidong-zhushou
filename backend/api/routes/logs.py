from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
from io import StringIO

from core.database import get_db
from core.security import decode_access_token
from core.utils import to_beijing_iso, to_beijing_str
from models.log import Log
from models.task import Task
from models.account import Account
from schemas.log import LogResponse
from api.deps import get_current_user
from models.user import User

router = APIRouter(prefix="/api/logs", tags=["logs"])

_optional_bearer = HTTPBearer(auto_error=False)


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_optional_bearer),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """可选鉴权：如果没有提供 token 则返回 None，不抛出异常。"""
    if credentials is None:
        return None
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        return None
    user_id = payload.get("user_id")
    if user_id is None:
        return None
    return db.query(User).filter(User.id == user_id).first()


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
    token: Optional[str] = Query(None, description="Bearer token (备选鉴权方式)"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """导出日志为 CSV 格式

    支持两种鉴权方式：
    1. 标准 Authorization: Bearer <token> header
    2. 通过 query parameter ?token=<token>（适用于浏览器直接下载链接）
    """
    # 如果 header 鉴权未通过，尝试用 query token 鉴权
    if current_user is None and token:
        payload = decode_access_token(token)
        if payload:
            user_id = payload.get("user_id")
            if user_id:
                current_user = db.query(User).filter(User.id == user_id).first()

    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required (provide Bearer token via header or ?token= query param)",
            headers={"WWW-Authenticate": "Bearer"},
        )

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
    csv_buffer.write("ID,任务ID,状态,账号用户名,站点名称,任务名称,结果,创建时间\n")

    for log in logs:
        created_at_str = to_beijing_str(log.created_at) if log.created_at else ""
        result_str = (log.result or "").replace('"', '""')
        csv_buffer.write(
            f'{log.id},{log.task_id},{log.status},'
            f'{getattr(log, "account_username", "") or ""},'
            f'{getattr(log, "site_name", "") or ""},'
            f'{getattr(log, "task_name", "") or ""},'
            f'"{result_str}","{created_at_str}"\n'
        )

    csv_content = csv_buffer.getvalue()

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8",
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
        "account_username": getattr(log, "account_username", None),
        "site_name": getattr(log, "site_name", None),
        "task_name": getattr(log, "task_name", None),
        "created_at": to_beijing_iso(log.created_at),
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
