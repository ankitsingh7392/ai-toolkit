import uuid

from sqlalchemy import Float, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import Base, TimestampMixin, new_uuid


class FlakyTest(Base, TimestampMixin):
    __tablename__ = "flaky_tests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)

    test_name: Mapped[str] = mapped_column(String(512), nullable=False)
    classname: Mapped[str] = mapped_column(String(512), nullable=False)
    job_name: Mapped[str] = mapped_column(String(256), nullable=False)

    fail_count: Mapped[int] = mapped_column(Integer, default=0)
    pass_count: Mapped[int] = mapped_column(Integer, default=0)
    total_runs: Mapped[int] = mapped_column(Integer, default=0)
    flakiness_score: Mapped[float] = mapped_column(Float, default=0.0)

    indicators: Mapped[dict] = mapped_column(JSONB, default=dict)
