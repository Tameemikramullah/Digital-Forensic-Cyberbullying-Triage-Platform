from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..database import Base


class ChainAction(str, enum.Enum):
    UPLOAD = "UPLOAD"
    CLASSIFICATION = "CLASSIFICATION"
    REVIEW = "REVIEW"
    EXPORT = "EXPORT"
    ARCHIVE = "ARCHIVE"


class ChainOfCustody(Base):
    __tablename__ = "chain_of_custody"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=False)
    action = Column(String(100), nullable=False)
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    previous_hash = Column(String(64), nullable=True)
    entry_hash = Column(String(64), nullable=True)

    evidence = relationship("Evidence", back_populates="chain_of_custody")
