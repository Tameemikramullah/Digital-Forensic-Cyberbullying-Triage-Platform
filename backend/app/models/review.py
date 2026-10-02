from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..database import Base


class ClassificationResult(Base):
    __tablename__ = "classification_results"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=False)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), default="1.0")
    prediction = Column(String(50), nullable=False)
    confidence_score = Column(Float, nullable=False)
    risk_level = Column(String(20))
    threshold = Column(Float, default=0.7)
    processing_time_ms = Column(Integer)
    preprocessing_steps = Column(Text)
    explanation_method = Column(String(50))
    explanation_summary = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    evidence = relationship("Evidence", back_populates="classification_results")


class ExaminerReview(Base):
    __tablename__ = "examiner_reviews"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=False)
    examiner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    decision = Column(String(50), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    evidence = relationship("Evidence", back_populates="examiner_reviews")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=False)
    actor = Column(String(255), nullable=False)
    event_type = Column(String(100), nullable=False)
    event_details = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    previous_hash = Column(String(64), nullable=True)
    entry_hash = Column(String(64), nullable=True)

    evidence = relationship("Evidence", back_populates="audit_logs")
