import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import User, Evidence, EvidenceMetadata, EvidenceStatus, ClassificationResult, ExaminerReview, AuditLog, ChainOfCustody, Explanation, RepeatabilityTest, IntegrityCheck
from app.security.auth import hash_password

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db):
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_user(db_session):
    user = User(
        email="test@example.com",
        password_hash=hash_password("testpass"),
        role="INVESTIGATOR",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_evidence(db_session, test_user):
    evidence = Evidence(
        evidence_hash="a" * 64,
        source_platform="Twitter",
        source_post_id="tweet_123",
        content="Test content",
        acquisition_date=datetime(2026, 1, 1, 0, 0, 0),
        uploaded_by=test_user.id,
        status=EvidenceStatus.PENDING,
    )
    db_session.add(evidence)
    db_session.commit()
    db_session.refresh(evidence)
    return evidence
