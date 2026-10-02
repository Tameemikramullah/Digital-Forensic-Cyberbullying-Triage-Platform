from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Explanation(Base):
    __tablename__ = "explanations"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=False)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), default="1.0")
    explanation_method = Column(String(50), nullable=False)
    feature_name = Column(String(255), nullable=False)
    contribution = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    evidence = relationship("Evidence", back_populates="explanations")


class RepeatabilityTest(Base):
    __tablename__ = "repeatability_tests"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=False)
    model_name = Column(String(100), nullable=False)
    iterations = Column(Integer, nullable=False)
    prediction_consistency = Column(Float, nullable=False)
    confidence_variance = Column(Float, nullable=False)
    explanation_consistency = Column(Float, nullable=False)
    pass_fail = Column(String(20), nullable=False)
    details_json = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    evidence = relationship("Evidence", back_populates="repeatability_tests")


class IntegrityCheck(Base):
    __tablename__ = "integrity_checks"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=False)
    original_hash = Column(String(64), nullable=False)
    current_hash = Column(String(64), nullable=False)
    match = Column(Integer, nullable=False)
    checked_at = Column(DateTime(timezone=True), server_default=func.now())

    evidence = relationship("Evidence", back_populates="integrity_checks")
