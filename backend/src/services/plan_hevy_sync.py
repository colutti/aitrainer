"""Helpers to keep bound plan routines synchronized with Hevy."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from src.api.models.plan import (
    ExternalRoutineBinding,
    TrainingExercise,
    TrainingRoutine,
    UserPlan,
)
from src.api.models.routine import (
    HevyRepRange,
    HevyRoutine,
    HevyRoutineExercise,
    HevySet,
)
from src.services.hevy_service import HevyService


class HevySyncError(ValueError):
    """Raised when a plan update cannot be synchronized with Hevy."""


def _normalize_name(value: str | None) -> str:
    return (value or "").strip().lower()


def _has_hevy_binding(routine: TrainingRoutine) -> bool:
    return any(binding.provider == "hevy" for binding in routine.external_bindings)


def _get_hevy_bindings(routine: TrainingRoutine) -> list[ExternalRoutineBinding]:
    return [
        binding for binding in routine.external_bindings if binding.provider == "hevy"
    ]


def _exercise_note(exercise: TrainingExercise) -> str | None:
    parts = []
    if exercise.notes:
        parts.append(exercise.notes)
    parts.append(f"Intensidade: {exercise.intensity.target}")
    return " | ".join(parts)


def _resolve_exercise_template_id(
    exercise: TrainingExercise,
    current_exercises: list,
    index: int,
) -> str:
    if exercise.external_exercise_template_id:
        return exercise.external_exercise_template_id

    if index >= len(current_exercises):
        raise HevySyncError(
            "Rotina vinculada ao Hevy exige external_exercise_template_id "
            f"para o exercicio '{exercise.name}'."
        )

    current_exercise = current_exercises[index]
    current_title = _normalize_name(getattr(current_exercise, "title", None))
    exercise_name = _normalize_name(exercise.name)
    if current_title != exercise_name:
        raise HevySyncError(
            "Nao foi possivel mapear os exercicios da rotina vinculada ao Hevy. "
            "Inclua external_exercise_template_id ou mantenha o mesmo exercicio na mesma ordem."
        )

    return current_exercise.exercise_template_id


def _build_hevy_exercise(
    exercise: TrainingExercise,
    current_exercises: list,
    index: int,
) -> tuple[HevyRoutineExercise, str]:
    template_id = _resolve_exercise_template_id(exercise, current_exercises, index)
    hevy_sets = [
        HevySet(
            type="normal",
            rep_range=HevyRepRange(
                start=exercise.rep_range.min_reps,
                end=exercise.rep_range.max_reps,
            ),
        )
        for _ in range(exercise.sets)
    ]
    return (
        HevyRoutineExercise(
            exercise_template_id=template_id,
            rest_seconds=exercise.rest_seconds,
            notes=_exercise_note(exercise),
            sets=hevy_sets,
        ),
        template_id,
    )


def _build_hevy_routine_payload(
    routine: TrainingRoutine,
    current_hevy_routine: HevyRoutine,
) -> tuple[HevyRoutine, list[TrainingExercise]]:
    current_exercises = list(current_hevy_routine.exercises)
    synced_exercises: list[HevyRoutineExercise] = []
    enriched_plan_exercises: list[TrainingExercise] = []

    for index, exercise in enumerate(routine.exercises):
        synced_exercise, template_id = _build_hevy_exercise(
            exercise, current_exercises, index
        )
        synced_exercises.append(synced_exercise)
        enriched_plan_exercises.append(
            exercise.model_copy(update={"external_exercise_template_id": template_id})
        )

    return (
        HevyRoutine(
            id=current_hevy_routine.id,
            title=routine.name,
            folder_id=current_hevy_routine.folder_id,
            notes=routine.objective,
            exercises=synced_exercises,
        ),
        enriched_plan_exercises,
    )


async def _sync_one_bound_routine(
    hevy_service: HevyService,
    api_key: str,
    routine: TrainingRoutine,
    binding: ExternalRoutineBinding,
) -> TrainingRoutine:
    current_hevy_routine = await hevy_service.get_routine_by_id(
        api_key,
        binding.external_routine_id,
    )
    if current_hevy_routine is None:
        raise HevySyncError(
            "Nao foi possivel carregar a rotina vinculada "
            f"'{binding.external_routine_id}' no Hevy."
        )

    hevy_payload, enriched_exercises = _build_hevy_routine_payload(
        routine,
        current_hevy_routine,
    )
    synced_hevy_routine = await hevy_service.update_routine(
        api_key,
        binding.external_routine_id,
        hevy_payload,
    )
    if synced_hevy_routine is None:
        raise HevySyncError(
            f"A sincronizacao com Hevy falhou para a rotina '{routine.name}'."
        )

    synced_bindings = []
    for candidate in routine.external_bindings:
        if (
            candidate.provider == "hevy"
            and candidate.external_routine_id == binding.external_routine_id
        ):
            synced_bindings.append(
                candidate.model_copy(
                    update={
                        "external_routine_name": synced_hevy_routine.title,
                        "last_synced_at": datetime.now(timezone.utc),
                        "last_sync_error": None,
                    }
                )
            )
        else:
            synced_bindings.append(candidate)

    return routine.model_copy(
        update={
            "name": synced_hevy_routine.title,
            "exercises": enriched_exercises,
            "external_bindings": synced_bindings,
        }
    )


async def _sync_training_with_hevy_async(
    database,
    user_email: str,
    current_plan: UserPlan,
    updated_plan: UserPlan,
) -> UserPlan:
    profile = database.get_user_profile(user_email)
    if not profile or not profile.hevy_enabled or not profile.hevy_api_key:
        return updated_plan

    current_routines = {routine.id: routine for routine in current_plan.training.routines}
    updated_routines = {routine.id: routine for routine in updated_plan.training.routines}

    removed_bound_routines = [
        routine_id
        for routine_id, routine in current_routines.items()
        if _has_hevy_binding(routine) and routine_id not in updated_routines
    ]
    if removed_bound_routines:
        raise HevySyncError(
            "Nao e possivel remover uma rotina vinculada ao Hevy "
            "sem suporte de exclusao equivalente."
        )

    if not any(_has_hevy_binding(routine) for routine in updated_plan.training.routines):
        return updated_plan

    hevy_service = HevyService(workout_repository=database.workouts_repo)
    synced_routines: list[TrainingRoutine] = []

    for routine in updated_plan.training.routines:
        bindings = _get_hevy_bindings(routine)
        if not bindings:
            synced_routines.append(routine)
            continue

        synced_routine = routine
        for binding in bindings:
            synced_routine = await _sync_one_bound_routine(
                hevy_service=hevy_service,
                api_key=profile.hevy_api_key,
                routine=synced_routine,
                binding=binding,
            )

        synced_routines.append(synced_routine)

    updated_training = updated_plan.training.model_copy(
        update={"routines": synced_routines}
    )
    return updated_plan.model_copy(update={"training": updated_training})


def sync_training_with_hevy_if_needed(
    database,
    user_email: str,
    current_plan: UserPlan,
    updated_plan: UserPlan,
) -> UserPlan:
    """Synchronize bound training routines with Hevy before saving the active plan."""

    async def runner() -> UserPlan:
        return await _sync_training_with_hevy_async(
            database=database,
            user_email=user_email,
            current_plan=current_plan,
            updated_plan=updated_plan,
        )

    try:
        return asyncio.run(runner())
    except RuntimeError:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio  # type: ignore # pylint: disable=import-error,import-outside-toplevel

            nest_asyncio.apply()
            return loop.run_until_complete(runner())
        return loop.run_until_complete(runner())
