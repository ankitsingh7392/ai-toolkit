import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.db.base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from app.models.db.test_case import TestCase


class TestRun(Base, TimestampMixin):
    __tablename__ = "test_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    run_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    # Status lifecycle: pending → processing → completed | failed
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")

    # Jenkins CI metadata
    build_id: Mapped[str] = mapped_column(String(128), nullable=False)
    job_name: Mapped[str] = mapped_column(String(256), nullable=False)
    git_commit: Mapped[str] = mapped_column(String(40), nullable=False)
    branch: Mapped[str] = mapped_column(String(256), nullable=False)
    environment: Mapped[str] = mapped_column(String(64), nullable=False)
    jenkins_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Test counts
    total_tests: Mapped[int] = mapped_column(Integer, default=0)
    passed_tests: Mapped[int] = mapped_column(Integer, default=0)
    failed_tests: Mapped[int] = mapped_column(Integer, default=0)
    error_tests: Mapped[int] = mapped_column(Integer, default=0)
    skipped_tests: Mapped[int] = mapped_column(Integer, default=0)

    # Build-level AI insight
    build_at_risk: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    regression_commit: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    build_insight: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    test_cases: Mapped[list["TestCase"]] = relationship(
        "TestCase", back_populates="run", cascade="all, delete-orphan"
    )
