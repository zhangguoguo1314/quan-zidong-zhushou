from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from io import StringIO
import csv

from core.database import get_db
from core.security import get_password_hash
from models.account import Account
from models.site import Site
from schemas.account import AccountCreate, AccountUpdate, AccountResponse, AccountImportRequest
from api.deps import get_current_user
from models.user import User

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("", response_model=List[AccountResponse])
def get_accounts(
    site_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Account).filter(Account.user_id == current_user.id)
    if site_id:
        query = query.filter(Account.site_id == site_id)
    if search:
        like = f"%{search}%"
        query = query.filter(
            (Account.username.like(like)) | (Account.nickname.like(like))
        )
    accounts = query.all()
    return accounts


@router.get("/grouped")
def get_accounts_grouped(
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    accounts = db.query(Account).filter(Account.user_id == current_user.id).all()
    sites = db.query(Site).all()
    site_map = {s.id: s for s in sites}

    groups: dict = {}
    for acc in accounts:
        site = site_map.get(acc.site_id)
        if not site:
            continue
        if search:
            search_lower = search.lower()
            in_name = search_lower in (acc.username or "").lower()
            in_nick = search_lower in (acc.nickname or "").lower()
            if not in_name and not in_nick:
                continue

        site_display = site.display_name or site.name
        key = f"{site.id}|{site_display}"
        if key not in groups:
            groups[key] = {
                "site_id": site.id,
                "site_name": site.name,
                "site_display_name": site_display,
                "site_category": site.category or "其他",
                "accounts": []
            }
        groups[key]["accounts"].append({
            "id": acc.id,
            "username": acc.username,
            "nickname": acc.nickname or "",
            "status": acc.status,
            "created_at": acc.created_at.isoformat() if acc.created_at else None
        })
    return {"groups": list(groups.values())}


@router.post("", response_model=AccountResponse)
def create_account(
    account_data: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    site = db.query(Site).filter(Site.id == account_data.site_id).first()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")

    account = Account(user_id=current_user.id, **account_data.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.post("/import")
def import_accounts_csv(
    site_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a CSV")

    content = file.file.read().decode('utf-8-sig')
    reader = csv.DictReader(StringIO(content))

    accounts = []
    for row in reader:
        account = Account(
            user_id=current_user.id,
            site_id=site_id,
            username=row.get('username', row.get('账号', '')),
            nickname=row.get('nickname', row.get('昵称', row.get('备注', ''))),
            password=row.get('password', row.get('密码', '')),
            token=row.get('token', row.get('Token', '')),
            cookie=row.get('cookie', row.get('Cookie', '')),
            status='active'
        )
        db.add(account)
        accounts.append(account)

    db.commit()
    for account in accounts:
        db.refresh(account)
    return {"accounts": accounts, "count": len(accounts)}


@router.get("/export/csv")
def export_accounts_csv(
    site_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Account).filter(Account.user_id == current_user.id)
    if site_id:
        query = query.filter(Account.site_id == site_id)
    accounts = query.all()
    sites = {s.id: s for s in db.query(Site).all()}

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["站点", "账号", "昵称", "密码", "Token", "Cookie", "状态"])
    for acc in accounts:
        site = sites.get(acc.site_id)
        writer.writerow([
            site.name if site else '',
            acc.username,
            acc.nickname or '',
            acc.password or '',
            acc.token or '',
            acc.cookie or '',
            acc.status
        ])
    output.seek(0)

    return StreamingResponse(
        iter([output.read()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=accounts.csv"}
    )


@router.post("/bulk", response_model=List[AccountResponse])
def create_accounts_bulk(
    data: AccountImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    site = db.query(Site).filter(Site.id == data.site_id).first()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")

    accounts = []
    for account_data in data.accounts:
        account = Account(user_id=current_user.id, site_id=data.site_id, **account_data.model_dump())
        db.add(account)
        accounts.append(account)

    db.commit()
    for account in accounts:
        db.refresh(account)
    return accounts


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    account = db.query(Account).filter(Account.id == account_id, Account.user_id == current_user.id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account


@router.put("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: int,
    account_data: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    account = db.query(Account).filter(Account.id == account_id, Account.user_id == current_user.id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    update_data = account_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(account, key, value)
    db.commit()
    db.refresh(account)
    return account


@router.delete("/{account_id}")
def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    account = db.query(Account).filter(Account.id == account_id, Account.user_id == current_user.id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    db.delete(account)
    db.commit()
    return {"message": "Account deleted successfully"}
