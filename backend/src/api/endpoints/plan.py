"""Endpoints for central plan lifecycle and snapshots."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.api.models.plan import ActivePlan, PlanProposalInput, PlanStatus
from src.core.demo_access import WritableCurrentUser
from src.core.deps import get_mongo_database
from src.services.auth import verify_token
from src.services.database import MongoDatabase
from src.services.plan_service import (
    build_next_plan_version,
    missing_intake_fields,
    missing_execution_fields,
)

router = APIRouter()

CurrentUser = Annotated[str, Depends(verify_token)]
DatabaseDep = Annotated[MongoDatabase, Depends(get_mongo_database)]


class ApprovePlanRequest(BaseModel):
    """Request payload to approve a proposed plan version."""

    version: int = Field(..., ge=1)


class CreatePlanProposalResponse(BaseModel):
    """Response payload for created plan proposal."""

    id: str
    version: int
    status: PlanStatus


class ApprovePlanResponse(BaseModel):
    """Response payload for plan approval."""

    approved: bool
    version: int


@router.get("/active", response_model=ActivePlan)
def get_active_plan(user_email: CurrentUser, db: DatabaseDep) -> ActivePlan:
    """Get current active plan for authenticated user."""
    plan = db.get_active_plan(user_email)
    if plan is None:
        raise HTTPException(status_code=404, detail="Active plan not found")
    return plan


@router.get("/versions", response_model=list[ActivePlan])
def list_plan_versions(user_email: CurrentUser, db: DatabaseDep) -> list[ActivePlan]:
    """List plan versions for authenticated user, latest first."""
    return db.list_plan_versions(user_email)


@router.post("/proposal", response_model=CreatePlanProposalResponse)
def create_plan_proposal(
    user_email: WritableCurrentUser,
    db: DatabaseDep,
    payload: PlanProposalInput,
) -> CreatePlanProposalResponse:
    """Create a new plan version and activate it immediately."""
    latest = db.get_latest_plan(user_email)
    merged_strategy = (
        {**latest.strategy.model_dump(), **payload.strategy}
        if latest is not None
        else payload.strategy
    )
    merged_execution = (
        {**latest.execution.model_dump(), **payload.execution}
        if latest is not None
        else payload.execution
    )
    missing_fields = missing_intake_fields(merged_strategy) + missing_execution_fields(
        merged_execution
    )
    if missing_fields:
        missing_list = ", ".join(missing_fields)
        raise HTTPException(
            status_code=422,
            detail=f"Plano incompleto. Campos obrigatorios ausentes: {missing_list}",
        )

    plan = build_next_plan_version(user_email, latest, payload)
    version = plan.version

    plan_id = db.save_plan(plan)
    return CreatePlanProposalResponse(
        id=plan_id,
        version=version,
        status=PlanStatus.ACTIVE,
    )


@router.post("/approve", response_model=ApprovePlanResponse)
def approve_plan(
    user_email: WritableCurrentUser,
    db: DatabaseDep,
    payload: ApprovePlanRequest,
) -> ApprovePlanResponse:
    """Deprecated endpoint kept for backward compatibility."""
    _ = (user_email, db, payload)
    raise HTTPException(
        status_code=410,
        detail="Fluxo de aprovacao foi removido. O plano e criado/editado diretamente.",
    )
