from sqlalchemy import Column, Integer, Text, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base


class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    result = Column(Text)
    status = Column(String(20), nullable=False)
    raw_response = Column(Text, default="")
    account_username = Column(String(200), default="")
    site_name = Column(String(200), default="")
    task_name = Column(String(200), default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    task = relationship("Task", back_populates="logs")
