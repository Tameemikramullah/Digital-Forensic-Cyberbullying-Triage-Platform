import sys
import pathlib
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database import Base
from app.models import Evidence, EvidenceStatus, User, UserRole
from app.services.hash_service import generate_hash


@pytest.fixture
def db_session(tmp_path):
    """A fresh, file-backed SQLite database for each test."""
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def examiner(db_session):
    user = User(
        email="examiner@example.test",
        password_hash="not-a-real-password",
        role=UserRole.INVESTIGATOR,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def evidence(db_session, examiner):
    content = "You are worthless and nobody wants you here."
    item = Evidence(
        evidence_hash=generate_hash(content),
        source_platform="Twitter",
        source_post_id="post-001",
        content=content,
        acquisition_date=datetime.now(timezone.utc),
        uploaded_by=examiner.id,
        status=EvidenceStatus.PENDING,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item
