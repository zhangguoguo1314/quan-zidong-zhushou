from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    username = Column(String(100), nullable=False)
    nickname = Column(String(100), default="")
    password = Column(String(255))
    token = Column(Text)
    cookie = Column(Text)
    login_cookies = Column(Text, default="")
    cookies_updated_at = Column(String(30), default="")
    status = Column(String(20), default="active")
    total_signins = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="accounts")
    site = relationship("Site", back_populates="accounts")
    tasks = relationship("Task", back_populates="account", cascade="all, delete-orphan")
