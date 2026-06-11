from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import csv
import io

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    accounts = db.query(Account).filter(Account.user_id == current_user.id).all()
    return accounts


@router.post("", response_model=AccountResponse)
def create_account(
    account_data: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    site = db.query(Site).filter(Site.id == account_data.site_id).first()
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )

    account = Account(
        user_id=current_user.id,
        **account_data.model_dump()
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.post("/import", response_model=List[AccountResponse])
def import_accounts_csv(
    site_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )

    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV"
        )

    content = file.file.read().decode('utf-8')
    reader = csv.DictReader(io.StringIO(content))

    accounts = []
    for row in reader:
        account = Account(
            user_id=current_user.id,
            site_id=site_id,
            username=row.get('username', ''),
            password=row.get('password', ''),
            token=row.get('token', ''),
            cookie=row.get('cookie', ''),
            status='active'
        )
        db.add(account)
        accounts.append(account)

    db.commit()
    for account in accounts:
        db.refresh(account)

    return accounts


@router.post("/bulk", response_model=List[AccountResponse])
def create_accounts_bulk(
    data: AccountImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    site = db.query(Site).filter(Site.id == data.site_id).first()
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )

    accounts = []
    for account_data in data.accounts:
        account = Account(
            user_id=current_user.id,
            site_id=data.site_id,
            **account_data.model_dump()
        )
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
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    return account


@router.put("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: int,
    account_data: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

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
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    db.delete(account)
    db.commit()
    return {"message": "Account deleted successfully"}
