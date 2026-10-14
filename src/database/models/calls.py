from sqlalchemy import Column, Integer, DateTime, String
from .base import Base


class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    caller_id = Column(Integer, index=True)
    callee_id = Column(Integer, index=True)
    kind = Column(String, default="audio")
    started_at = Column(DateTime)
    ended_at = Column(DateTime, nullable=True)
    closed_by = Column(Integer, nullable=True)
