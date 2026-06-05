import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.db.base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from app.models.db.run import TestRun


class TestCase(Base, TimestampMixin):
    __tablename__ = "test_cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # JUnit XML fields
    suite_name: Mapped[str] = mapped_column(String(256), nullable=False)
    classname: Mapped[str] = mapped_column(String(512), nullable=False)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    duration: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # passed|failed|error|skipped
    failure_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    failure_type: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    stack_trace: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    system_out: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    system_err: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # AI analysis results
    failure_category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    root_cause_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)  # P0–P3
    is_flaky: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_analysis: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Clustering
    cluster_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    run: Mapped["TestRun"] = relationship("TestRun", back_populates="test_cases")
