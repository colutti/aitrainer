"""Endpoints for central plan lifecycle and snapshots."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.api.models.plan import ActivePlan, PlanProposalInput, PlanStatus
from src.core.demo_access import WritableCurrentUser
from src.core.deps import get_mongo_database
from src.services.auth import verify_token
from src.services.database import MongoDatabase
from src.services.plan_service import build_next_plan_version

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
    """Get active plan for authenticated user."""
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
    """Create a new proposed plan version awaiting approval."""
    latest = db.get_latest_plan(user_email)
    plan = build_next_plan_version(user_email, latest, payload)
    version = plan.version

    plan_id = db.save_plan(plan)
    return CreatePlanProposalResponse(
        id=plan_id,
        version=version,
        status=PlanStatus.AWAITING_APPROVAL,
    )


@router.post("/approve", response_model=ApprovePlanResponse)
def approve_plan(
    user_email: WritableCurrentUser,
    db: DatabaseDep,
    payload: ApprovePlanRequest,
) -> ApprovePlanResponse:
    """Approve a pending plan version and make it active."""
    approved = db.approve_plan(user_email, payload.version)
    if not approved:
        raise HTTPException(status_code=404, detail="Plan version not found")
    return ApprovePlanResponse(approved=True, version=payload.version)
