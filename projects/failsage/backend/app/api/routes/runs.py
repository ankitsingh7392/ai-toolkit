from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import distinct, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.db.run import TestRun
from app.models.schemas.analysis import RunResponse

router = APIRouter(prefix="/runs", tags=["Runs"])


@router.get("/meta", tags=["Runs"], summary="Available job names and branches for filter dropdowns")
async def get_meta(db: AsyncSession = Depends(get_db)) -> dict:
    jobs = (await db.execute(
        select(distinct(TestRun.job_name)).order_by(TestRun.job_name)
    )).scalars().all()
    branches = (await db.execute(
        select(distinct(TestRun.branch)).order_by(TestRun.branch)
    )).scalars().all()
    envs = (await db.execute(
        select(distinct(TestRun.environment)).order_by(TestRun.environment)
    )).scalars().all()
    return {"jobs": list(jobs), "branches": list(branches), "environments": list(envs)}


@router.get("", response_model=list[RunResponse], summary="List test runs with filters")
async def list_runs(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    job_name: Optional[str] = Query(None),
    branch: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
    run_status: Optional[str] = Query(None, alias="status"),
    build_at_risk: Optional[bool] = Query(None),
    date_from: Optional[datetime] = Query(None, description="ISO 8601 e.g. 2026-06-01T00:00:00"),
    date_to: Optional[datetime] = Query(None, description="ISO 8601 e.g. 2026-06-05T23:59:59"),
    db: AsyncSession = Depends(get_db),
) -> list[RunResponse]:
    q = select(TestRun).order_by(desc(TestRun.created_at)).limit(limit).offset(offset)
    if job_name:
        q = q.where(TestRun.job_name == job_name)
    if branch:
        q = q.where(TestRun.branch == branch)
    if environment:
        q = q.where(TestRun.environment == environment)
    if run_status:
        q = q.where(TestRun.status == run_status)
    if build_at_risk is not None:
        q = q.where(TestRun.build_at_risk == build_at_risk)
    if date_from:
        q = q.where(TestRun.created_at >= date_from)
    if date_to:
        q = q.where(TestRun.created_at <= date_to)
    rows = (await db.execute(q)).scalars().all()
    return [RunResponse.model_validate(r) for r in rows]


@router.get("/{run_id}", response_model=RunResponse, summary="Get run status and build insight")
async def get_run(run_id: str, db: AsyncSession = Depends(get_db)) -> RunResponse:
    row = (
        await db.execute(select(TestRun).where(TestRun.run_id == run_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Run {run_id!r} not found"
        )
    return RunResponse.model_validate(row)
