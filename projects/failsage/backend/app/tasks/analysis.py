import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from celery import shared_task
from sqlalchemy import select

from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.core.database import get_sync_session
from app.models.db.run import TestRun
from app.models.db.test_case import TestCase
from app.services import ai_service, clustering, flaky_detector, notification
from app.services.junit_parser import parse_junit_xml

logger = logging.getLogger(__name__)
settings = get_settings()


@celery_app.task(
    name="app.tasks.analysis.process_jenkins_run",
    bind=True,
    max_retries=3,
    default_retry_delay=15,
    queue="analysis",
)
def process_jenkins_run(
    self, run_id: str, junit_xml: str, ci_meta: dict[str, Any]
) -> dict[str, Any]:
    logger.info("Starting analysis for run_id=%s", run_id)

    with get_sync_session() as session:
        run = (
            session.execute(select(TestRun).where(TestRun.run_id == run_id))
            .scalar_one_or_none()
        )
        if not run:
            logger.error("TestRun %s not found", run_id)
            return {"error": "run not found"}

        run.status = "processing"
        session.flush()

    try:
        # ── 1. Parse JUnit XML ────────────────────────────────────────────────
        parse_result = parse_junit_xml(junit_xml)

        with get_sync_session() as session:
            run = session.execute(select(TestRun).where(TestRun.run_id == run_id)).scalar_one()

            test_cases: list[TestCase] = []
            for suite in parse_result.suites:
                for ptc in suite.test_cases:
                    tc = TestCase(
                        run_id=run.id,
                        suite_name=ptc.suite_name,
                        classname=ptc.classname,
                        name=ptc.name,
                        duration=ptc.time,
                        status=ptc.status,
                        failure_message=ptc.failure_message,
                        failure_type=ptc.failure_type,
                        stack_trace=ptc.stack_trace,
                        system_out=ptc.system_out,
                        system_err=ptc.system_err,
                    )
                    session.add(tc)
                    test_cases.append(tc)

            run.total_tests = parse_result.total_tests
            run.passed_tests = parse_result.total_passed
            run.failed_tests = parse_result.total_failed
            run.error_tests = parse_result.total_errors
            run.skipped_tests = parse_result.total_skipped
            session.flush()

            tc_ids = [str(tc.id) for tc in test_cases]

        # ── 2. Cluster failures ───────────────────────────────────────────────
        failed_records: list[clustering.FailureRecord] = []
        with get_sync_session() as session:
            rows = session.execute(
                select(TestCase).where(
                    TestCase.run_id == (
                        session.execute(select(TestRun.id).where(TestRun.run_id == run_id)).scalar()
                    ),
                    TestCase.status.in_(["failed", "error"]),
                )
            ).scalars().all()

            for tc in rows:
                failed_records.append(
                    clustering.FailureRecord(
                        index=0,
                        test_id=str(tc.id),
                        classname=tc.classname,
                        failure_type=tc.failure_type,
                        failure_message=tc.failure_message,
                        stack_trace=tc.stack_trace,
                    )
                )

        clusters = clustering.cluster_failures(failed_records)

        # Apply cluster IDs
        cluster_map: dict[str, str] = {}
        for cluster in clusters:
            for tid in cluster.test_ids:
                cluster_map[tid] = cluster.cluster_id

        with get_sync_session() as session:
            run_id_uuid = (
                session.execute(select(TestRun.id).where(TestRun.run_id == run_id))
                .scalar()
            )
            all_tc = session.execute(
                select(TestCase).where(TestCase.run_id == run_id_uuid)
            ).scalars().all()
            for tc in all_tc:
                if str(tc.id) in cluster_map:
                    tc.cluster_id = cluster_map[str(tc.id)]

        # ── 3. AI analysis per cluster (one AI call per unique cluster) ────────
        analyzed_clusters: set[str] = set()
        cluster_analysis_cache: dict[str, dict[str, Any]] = {}

        with get_sync_session() as session:
            run_id_uuid = (
                session.execute(select(TestRun.id).where(TestRun.run_id == run_id))
                .scalar()
            )
            failed_tcs = session.execute(
                select(TestCase).where(
                    TestCase.run_id == run_id_uuid,
                    TestCase.status.in_(["failed", "error"]),
                )
            ).scalars().all()

            for tc in failed_tcs:
                cid = tc.cluster_id or str(tc.id)

                if cid not in analyzed_clusters:
                    analysis = ai_service.analyze_failure(
                        suite_name=tc.suite_name,
                        classname=tc.classname,
                        test_name=tc.name,
                        failure_message=tc.failure_message,
                        failure_type=tc.failure_type,
                        stack_trace=tc.stack_trace,
                        system_out=tc.system_out,
                        ci_metadata=ci_meta,
                        history=[],
                    )
                    cluster_analysis_cache[cid] = analysis
                    analyzed_clusters.add(cid)
                else:
                    analysis = cluster_analysis_cache[cid]

                tc.ai_analysis = analysis
                tc.failure_category = analysis.get("failure_category")
                tc.root_cause_summary = analysis.get("root_cause", {}).get("summary")
                tc.severity = analysis.get("severity")
                tc.confidence_score = analysis.get("confidence_score")

                # ── 4. Flaky detection ────────────────────────────────────────
                flaky_record = flaky_detector.upsert_flaky_record(
                    session=session,
                    test_name=tc.name,
                    classname=tc.classname,
                    job_name=ci_meta.get("job_name", ""),
                    current_status=tc.status,
                    failure_message=tc.failure_message,
                )

                flaky, indicators = flaky_detector.is_flaky(
                    session=session,
                    test_name=tc.name,
                    job_name=ci_meta.get("job_name", ""),
                    failure_message=tc.failure_message,
                )
                tc.is_flaky = flaky
                if flaky and tc.ai_analysis:
                    tc.ai_analysis["flakiness_indicators"] = indicators

        # ── 5. Build-level regression insight ─────────────────────────────────
        failure_summaries = [
            {"test": r.test_id, "message": (r.failure_message or "")[:200], "type": r.failure_type}
            for r in failed_records
        ]
        cluster_dicts = [
            {"cluster_id": c.cluster_id, "count": c.count, "sample": c.representative_message}
            for c in clusters
        ]

        build_insight = ai_service.analyze_build(
            ci_metadata=ci_meta,
            failure_summaries=failure_summaries,
            clusters=cluster_dicts,
        )

        with get_sync_session() as session:
            run = session.execute(select(TestRun).where(TestRun.run_id == run_id)).scalar_one()
            run.build_at_risk = build_insight.get("build_at_risk", False)
            run.risk_level = build_insight.get("risk_level")
            run.regression_commit = build_insight.get("likely_regression_commit")
            run.build_insight = build_insight
            run.status = "completed"
            run.completed_at = datetime.now(timezone.utc)

        # ── 6. Notifications ──────────────────────────────────────────────────
        notification.send_slack_notification(
            run_id=run_id,
            job_name=ci_meta.get("job_name", ""),
            build_id=ci_meta.get("build_id", ""),
            failed=parse_result.total_failed + parse_result.total_errors,
            risk_level=build_insight.get("risk_level"),
            build_at_risk=build_insight.get("build_at_risk", False),
        )

        logger.info("Completed analysis for run_id=%s", run_id)
        return {"run_id": run_id, "status": "completed", "failures_analyzed": len(failed_records)}

    except Exception as exc:
        logger.exception("Analysis failed for run_id=%s: %s", run_id, exc)
        with get_sync_session() as session:
            run = (
                session.execute(select(TestRun).where(TestRun.run_id == run_id))
                .scalar_one_or_none()
            )
            if run:
                run.status = "failed"
                run.error_detail = str(exc)
        raise self.retry(exc=exc)
