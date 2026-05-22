"""Endpoints for the plan V2 lifecycle."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ValidationError

from src.api.models.plan import (
    PlanCreateInput,
    PlanDiscoveryState,
    PlanDiscoveryUpdateInput,
    PlanProgressSnapshot,
    PlanReviewInput,
    PlanSectionUpdateInput,
    PlanViewModel,
    UserPlan,
)
from src.core.demo_access import WritableCurrentUser
from src.core.deps import get_mongo_database
from src.services.auth import verify_token
from src.services.database import MongoDatabase
from src.services.plan_hevy_sync import HevySyncError, sync_training_with_hevy_if_needed
from src.services.plan_service import (
    apply_discovery_update,
    attach_review,
    build_plan_from_create_input,
    build_plan_view_model,
    build_progress_snapshot,
    build_review_record,
    merge_plan_section,
    missing_discovery_fields,
)

router = APIRouter()

CurrentUser = Annotated[str, Depends(verify_token)]
DatabaseDep = Annotated[MongoDatabase, Depends(get_mongo_database)]


class SaveResponse(BaseModel):
    """Simple response payload for writes."""

    id: str


class PlanStatusResponse(BaseModel):
    """Top-level plan lifecycle response."""

    status: str
    missing_fields: list[str]


@router.get("", response_model=UserPlan)
def get_plan(user_email: CurrentUser, db: DatabaseDep) -> UserPlan:
    """Return the active plan for the authenticated user."""
    plan = db.get_plan(user_email)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.get("/status", response_model=PlanStatusResponse)
def get_plan_status(user_email: CurrentUser, db: DatabaseDep) -> PlanStatusResponse:
    """Return the current plan lifecycle status."""
    plan = db.get_plan(user_email)
    if plan is not None:
        return PlanStatusResponse(status="ACTIVE_PLAN", missing_fields=[])

    discovery = db.get_plan_discovery(user_email)
    missing_fields = missing_discovery_fields(discovery)
    status = "DISCOVERY_IN_PROGRESS" if discovery else "NO_PLAN"
    return PlanStatusResponse(status=status, missing_fields=missing_fields)


@router.get("/discovery", response_model=PlanDiscoveryState | None)
def get_plan_discovery(user_email: CurrentUser, db: DatabaseDep) -> PlanDiscoveryState | None:
    """Return the discovery draft, if one exists."""
    return db.get_plan_discovery(user_email)


@router.post("/discovery", response_model=SaveResponse)
def update_plan_discovery(
    user_email: WritableCurrentUser,
    db: DatabaseDep,
    payload: PlanDiscoveryUpdateInput,
) -> SaveResponse:
    """Persist discovery answers while there is no active plan."""
    current = db.get_plan_discovery(user_email)
    discovery = apply_discovery_update(user_email, current, payload)
    discovery_id = db.save_plan_discovery(discovery)
    return SaveResponse(id=discovery_id)


@router.post("/create-from-discovery", response_model=SaveResponse)
def create_plan_from_discovery(
    user_email: WritableCurrentUser,
    db: DatabaseDep,
    payload: PlanCreateInput,
) -> SaveResponse:
    """Create the first active plan once discovery is complete."""
    discovery = db.get_plan_discovery(user_email)
    missing_fields = missing_discovery_fields(discovery)
    if missing_fields:
        raise HTTPException(
            status_code=422,
            detail=(
                "Discovery incompleto. Campos obrigatorios ausentes: "
                + ", ".join(missing_fields)
            ),
        )

    try:
        plan = build_plan_from_create_input(user_email, payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    plan_id = db.save_plan(plan)
    db.clear_plan_discovery(user_email)
    return SaveResponse(id=plan_id)


@router.patch("/section", response_model=SaveResponse)
def update_plan_section(
    user_email: WritableCurrentUser,
    db: DatabaseDep,
    payload: PlanSectionUpdateInput,
) -> SaveResponse:
    """Apply a typed update to one section of the active plan."""
    current = db.get_plan(user_email)
    if current is None:
        raise HTTPException(status_code=404, detail="Plan not found")

    try:
        updated_plan = merge_plan_section(current, payload)
        if payload.section == "training":
            updated_plan = sync_training_with_hevy_if_needed(
                database=db,
                user_email=user_email,
                current_plan=current,
                updated_plan=updated_plan,
            )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except HevySyncError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    plan_id = db.save_plan(updated_plan)
    return SaveResponse(id=plan_id)


@router.post("/review", response_model=SaveResponse)
def record_plan_review(
    user_email: WritableCurrentUser,
    db: DatabaseDep,
    payload: PlanReviewInput,
) -> SaveResponse:
    """Append a structured review to the active plan."""
    current = db.get_plan(user_email)
    if current is None:
        raise HTTPException(status_code=404, detail="Plan not found")

    review = build_review_record(payload)
    updated_plan = attach_review(current, review)
    plan_id = db.save_plan(updated_plan)
    return SaveResponse(id=plan_id)


@router.get("/progress", response_model=PlanProgressSnapshot)
def get_plan_progress(user_email: CurrentUser, db: DatabaseDep) -> PlanProgressSnapshot:
    """Return the computed progress snapshot for the active plan."""
    plan = db.get_plan(user_email)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return build_progress_snapshot(plan, db)


@router.get("/view", response_model=PlanViewModel)
def get_plan_view(user_email: CurrentUser, db: DatabaseDep) -> PlanViewModel:
    """Return the aggregated view model used by the frontend."""
    plan = db.get_plan(user_email)
    discovery = db.get_plan_discovery(user_email)
    progress = build_progress_snapshot(plan, db) if plan else None
    return build_plan_view_model(plan, discovery, progress)
