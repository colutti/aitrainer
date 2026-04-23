"""Endpoints for singleton plan lifecycle."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.api.models.plan import UserPlan, PlanUpsertInput
from src.core.demo_access import WritableCurrentUser
from src.core.deps import get_mongo_database
from src.services.auth import verify_token
from src.services.database import MongoDatabase
from src.services.plan_service import (
    build_plan_singleton,
    missing_execution_fields,
    missing_intake_fields,
)

router = APIRouter()

CurrentUser = Annotated[str, Depends(verify_token)]
DatabaseDep = Annotated[MongoDatabase, Depends(get_mongo_database)]


class UpsertPlanResponse(BaseModel):
    """Response payload for singleton plan upsert."""

    id: str


@router.get("", response_model=UserPlan)
def get_plan(user_email: CurrentUser, db: DatabaseDep) -> UserPlan:
    """Get singleton plan for authenticated user."""
    plan = db.get_plan(user_email)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.post("/upsert", response_model=UpsertPlanResponse)
def upsert_plan(
    user_email: WritableCurrentUser,
    db: DatabaseDep,
    payload: PlanUpsertInput,
) -> UpsertPlanResponse:
    """Create or update singleton plan."""
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

    plan = build_plan_singleton(user_email, latest, payload)
    plan_id = db.save_plan(plan)
    return UpsertPlanResponse(id=plan_id)
