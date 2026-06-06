"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "001"
down_revision = None
branch_labels = None
depends_on = None

_ts = sa.DateTime(timezone=True)
_now = sa.func.now()


def upgrade() -> None:
    op.create_table(
        "test_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("build_id", sa.String(128), nullable=False),
        sa.Column("job_name", sa.String(256), nullable=False),
        sa.Column("git_commit", sa.String(40), nullable=False),
        sa.Column("branch", sa.String(256), nullable=False),
        sa.Column("environment", sa.String(64), nullable=False),
        sa.Column("jenkins_url", sa.String(512), nullable=True),
        sa.Column("total_tests", sa.Integer, server_default="0"),
        sa.Column("passed_tests", sa.Integer, server_default="0"),
        sa.Column("failed_tests", sa.Integer, server_default="0"),
        sa.Column("error_tests", sa.Integer, server_default="0"),
        sa.Column("skipped_tests", sa.Integer, server_default="0"),
        sa.Column("build_at_risk", sa.Boolean, server_default="false"),
        sa.Column("risk_level", sa.String(20), nullable=True),
        sa.Column("regression_commit", sa.String(40), nullable=True),
        sa.Column("build_insight", JSONB, nullable=True),
        sa.Column("error_detail", sa.Text, nullable=True),
        sa.Column("completed_at", _ts, nullable=True),
        sa.Column("created_at", _ts, server_default=_now, nullable=False),
        sa.Column("updated_at", _ts, server_default=_now, nullable=False),
    )

    op.create_table(
        "test_cases",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "run_id",
            UUID(as_uuid=True),
            sa.ForeignKey("test_runs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("suite_name", sa.String(256), nullable=False),
        sa.Column("classname", sa.String(512), nullable=False),
        sa.Column("name", sa.String(512), nullable=False),
        sa.Column("duration", sa.Float, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("failure_message", sa.Text, nullable=True),
        sa.Column("failure_type", sa.String(256), nullable=True),
        sa.Column("stack_trace", sa.Text, nullable=True),
        sa.Column("system_out", sa.Text, nullable=True),
        sa.Column("system_err", sa.Text, nullable=True),
        sa.Column("failure_category", sa.String(64), nullable=True),
        sa.Column("root_cause_summary", sa.Text, nullable=True),
        sa.Column("severity", sa.String(8), nullable=True),
        sa.Column("is_flaky", sa.Boolean, server_default="false"),
        sa.Column("confidence_score", sa.Float, nullable=True),
        sa.Column("ai_analysis", JSONB, nullable=True),
        sa.Column("cluster_id", sa.String(64), nullable=True, index=True),
        sa.Column("created_at", _ts, server_default=_now, nullable=False),
        sa.Column("updated_at", _ts, server_default=_now, nullable=False),
    )

    op.create_table(
        "flaky_tests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("test_name", sa.String(512), nullable=False),
        sa.Column("classname", sa.String(512), nullable=False),
        sa.Column("job_name", sa.String(256), nullable=False),
        sa.Column("fail_count", sa.Integer, server_default="0"),
        sa.Column("pass_count", sa.Integer, server_default="0"),
        sa.Column("total_runs", sa.Integer, server_default="0"),
        sa.Column("flakiness_score", sa.Float, server_default="0"),
        sa.Column("indicators", JSONB, server_default=sa.text("'{}'")),
        sa.Column("created_at", _ts, server_default=_now, nullable=False),
        sa.Column("updated_at", _ts, server_default=_now, nullable=False),
    )
    op.create_index("ix_flaky_tests_job_name", "flaky_tests", ["job_name"])

    op.create_table(
        "feedback",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "test_case_id",
            UUID(as_uuid=True),
            sa.ForeignKey("test_cases.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("engineer_email", sa.String(256), nullable=True),
        sa.Column("correct_category", sa.String(64), nullable=True),
        sa.Column("correct_severity", sa.String(8), nullable=True),
        sa.Column("feedback_notes", sa.Text, nullable=True),
        sa.Column("is_helpful", sa.Boolean, server_default="true"),
        sa.Column("created_at", _ts, server_default=_now, nullable=False),
        sa.Column("updated_at", _ts, server_default=_now, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("feedback")
    op.drop_table("flaky_tests")
    op.drop_table("test_cases")
    op.drop_table("test_runs")
