from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..database import Base


class EvidenceStatus(str, enum.Enum):
    PENDING = "PENDING"
    TRIAGED = "TRIAGED"
    REVIEWED = "REVIEWED"
    CLOSED = "CLOSED"


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    evidence_hash = Column(String(64), unique=True, index=True, nullable=False)
    source_platform = Column(String(100), nullable=False)
    source_post_id = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    acquisition_date = Column(DateTime(timezone=True), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(SQLEnum(EvidenceStatus), nullable=False, default=EvidenceStatus.PENDING)
    integrity_status = Column(String(20), nullable=False, default="PENDING")
    integrity_verified_at = Column(DateTime(timezone=True))
    original_file_path = Column(String(1024), nullable=True)
    original_filesize = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    evidence_metadata = relationship("EvidenceMetadata", back_populates="evidence", uselist=False, cascade="all, delete-orphan")
    classification_results = relationship("ClassificationResult", back_populates="evidence", cascade="all, delete-orphan")
    examiner_reviews = relationship("ExaminerReview", back_populates="evidence", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="evidence", cascade="all, delete-orphan")
    chain_of_custody = relationship("ChainOfCustody", back_populates="evidence", cascade="all, delete-orphan")
    explanations = relationship("Explanation", back_populates="evidence", cascade="all, delete-orphan")
    repeatability_tests = relationship("RepeatabilityTest", back_populates="evidence", cascade="all, delete-orphan")
    integrity_checks = relationship("IntegrityCheck", back_populates="evidence", cascade="all, delete-orphan")


class EvidenceMetadata(Base):
    __tablename__ = "evidence_metadata"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=False)
    author_name = Column(String(255))
    source_url = Column(String(1024))
    original_timestamp = Column(DateTime(timezone=True))
    filename = Column(String(255))
    filesize = Column(Integer)

    evidence = relationship("Evidence", back_populates="evidence_metadata")
