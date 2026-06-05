import uuid
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import Base, TimestampMixin, new_uuid


class Feedback(Base, TimestampMixin):
    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    test_case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("test_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    engineer_email: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    correct_category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    correct_severity: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    feedback_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_helpful: Mapped[bool] = mapped_column(Boolean, default=True)
