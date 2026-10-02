from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
import enum
from ..database import Base


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    INVESTIGATOR = "INVESTIGATOR"
    REVIEWER = "REVIEWER"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.INVESTIGATOR)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
