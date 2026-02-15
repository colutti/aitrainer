"""
Service to interact with Hevy API.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
import httpx
from src.api.models.workout_log import WorkoutLog, ExerciseLog
from src.api.models.routine import (
    HevyRoutine,
    RoutineListResponse,
    HevyExerciseTemplate,
    ExerciseTemplateListResponse,
)
from src.repositories.workout_repository import WorkoutRepository
from src.core.logs import logger

# pylint: disable=too-many-locals,broad-exception-caught,no-else-continue,too-many-nested-blocks,too-many-branches,too-many-statements,too-many-return-statements,import-outside-toplevel


class HevyService:
    """
    Service to interact with Hevy API.
    """

    BASE_URL = "https://api.hevyapp.com/v1"

    # Simple in-memory cache for exercise templates
    _exercises_cache: dict[
        str, tuple[float, list[HevyExerciseTemplate]]
    ] = {}  # key: api_key, value: (timestamp, templates)
    CACHE_DURATION = 3600 * 24  # 24 hours

    def __init__(self, workout_repository: WorkoutRepository):
        self.workout_repository = workout_repository

    async def validate_api_key(self, api_key: str) -> bool:
        """
        Validates the Hevy API key by making a lightweight request.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/workouts/count",
                    headers={"api-key": api_key},
                    timeout=10.0,
                )
                return response.status_code == 200
            except httpx.RequestError as e:
                logger.error("Hevy API validation failed: %s", e)
                return False

    async def get_workout_count(self, api_key: str) -> int:
        """
        Returns the total number of workouts available.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/workouts/count",
                    headers={"api-key": api_key},
                    timeout=10.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("workout_count", 0)
                return 0
            except Exception as e:
                logger.error("Failed to get workout count: %s", e)
                return 0

    async def fetch_workouts(
        self, api_key: str, page: int = 1, page_size: int = 10
    ) -> list[dict]:
        """
        Fetches a page of workouts from Hevy API.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/workouts",
                    headers={"api-key": api_key},
                    params={"page": page, "pageSize": page_size},
                    timeout=20.0,
                )
                if response.status_code == 200:
                    return response.json().get("workouts", [])
                logger.warning("Hevy API returned %s", response.status_code)
                return []
            except Exception as e:
                logger.error("Failed to fetch workouts page %d: %s", page, e)
                return []

    async def fetch_workout_by_id(
        self, api_key: str, workout_id: str
    ) -> Optional[dict]:
        """
        Fetches a single workout by ID from Hevy API.
        Used by webhook handler.
        """
        async with httpx.AsyncClient() as client:
            try:
                logger.debug(
                    "[Hevy] Fetching workout %s with key ****%s",
                    workout_id,
                    api_key[-4:],
                )
                response = await client.get(
                    f"{self.BASE_URL}/workouts/{workout_id}",
                    headers={"api-key": api_key},
                    timeout=10.0,
                )
                logger.debug("[Hevy] Response status: %s", response.status_code)

                if response.status_code == 200:
                    # Hevy API returns the workout object directly
                    data = response.json()
                    logger.debug("[Hevy] Response JSON keys: %s", list(data.keys()))
                    logger.debug("[Hevy] Returning workout directly from response")
                    return data

                # Log detailed error for debugging
                logger.error(
                    "[Hevy] Workout fetch failed for %s. Status: %s, Body: %s",
                    workout_id,
                    response.status_code,
                    response.text,
                )
                return None
            except Exception as e:
                logger.error("[Hevy] Exception fetching workout %s: %s", workout_id, e)
                import traceback

                logger.error(traceback.format_exc())
                return None

    def transform_to_workout_log(
        self, hevy_workout: dict, user_email: str
    ) -> Optional[WorkoutLog]:
        """
        Transforms a Hevy workout dict to our WorkoutLog model.
        """
        try:
            # Parse dates
            start_time = datetime.fromisoformat(
                hevy_workout["start_time"].replace("Z", "+00:00")
            )

            # Use end_time to calculate duration if available
            duration_minutes = None
            if hevy_workout.get("end_time"):
                end_time = datetime.fromisoformat(
                    hevy_workout["end_time"].replace("Z", "+00:00")
                )
                delta = end_time - start_time
                duration_minutes = int(delta.total_seconds() / 60)

            # Map exercises
            exercises = []
            for exercise_data in hevy_workout.get("exercises", []):
                sets_data = exercise_data.get("sets", [])
                if not sets_data:
                    continue

                reps_per_set = []
                weights_per_set = []
                distance_meters_per_set = []
                duration_seconds_per_set = []
                has_cardio = False

                for s in sets_data:
                    reps = s.get("reps")
                    weight = s.get("weight_kg")
                    distance = s.get("distance_meters")
                    duration = s.get("duration_seconds")

                    # Hevy might return None for some fields
                    reps_per_set.append(int(reps) if reps is not None else 0)
                    weights_per_set.append(float(weight) if weight is not None else 0.0)

                    # Only populate cardio fields if they exist (not None)
                    if distance is not None:
                        distance_meters_per_set.append(float(distance))
                        has_cardio = True
                    if duration is not None:
                        duration_seconds_per_set.append(int(duration))
                        has_cardio = True

                # Only include weights/cardio lists if exercise actually has that data
                # For cardio exercises with no weight, keep weights_per_set empty to avoid 0kg PRs
                exercise_log = ExerciseLog(
                    name=exercise_data["title"],
                    sets=len(sets_data),
                    reps_per_set=reps_per_set,
                    weights_per_set=weights_per_set if not has_cardio or any(w > 0 for w in weights_per_set) else [],
                    distance_meters_per_set=distance_meters_per_set if has_cardio else [],
                    duration_seconds_per_set=duration_seconds_per_set if has_cardio else [],
                )
                exercises.append(exercise_log)

            if not exercises:
                logger.warning(
                    "Hevy workout %s has no valid exercises", hevy_workout.get("id")
                )
                return None

            # Ensure duration is at least 1 if present to satisfy Pydantic
            if duration_minutes is not None and duration_minutes < 1:
                duration_minutes = 1

            return WorkoutLog(
                user_email=user_email,
                date=start_time,
                workout_type=hevy_workout.get("title") or "Hevy Import",
                exercises=exercises,
                duration_minutes=duration_minutes,
                source="hevy",
                external_id=hevy_workout.get("id"),
            )
        except Exception as e:
            logger.error("Error transforming workout %s: %s", hevy_workout.get("id"), e)
            return None

    async def import_workouts(
        self,
        user_email: str,
        api_key: str,
        from_date: Optional[datetime] = None,
        mode: str = "skip_duplicates",  # 'skip_duplicates' or 'overwrite'
    ) -> dict:
        """
        Orchestrates the import process.
        """
        imported_count = 0
        skipped_count = 0
        failed_count = 0

        # Hevy API pagination
        page = 1
        page_size = 10
        has_more = True

        if from_date and from_date.tzinfo is None:
            from_date = from_date.replace(tzinfo=timezone.utc)

        logger.info(
            "Starting Hevy import for %s, mode=%s, from=%s", user_email, mode, from_date
        )

        while has_more:
            workouts_batch = await self.fetch_workouts(api_key, page, page_size)
            if not workouts_batch:
                break

            for hevy_workout in workouts_batch:
                try:
                    # Check date filter
                    start_time_str = hevy_workout["start_time"].replace("Z", "+00:00")
                    workout_date = datetime.fromisoformat(start_time_str)

                    if from_date and workout_date < from_date:
                        continue

                    # Transform
                    workout_log = self.transform_to_workout_log(
                        hevy_workout, user_email
                    )
                    if not workout_log:
                        failed_count += 1
                        continue

                    # Check for existence
                    # 1. Try by external_id
                    exists = self.workout_repository.collection.find_one(
                        {
                            "user_email": user_email,
                            "external_id": hevy_workout.get("id"),
                        }
                    )

                    if not exists:
                        # 2. Daily deduplication
                        day_start = workout_date.replace(
                            hour=0, minute=0, second=0, microsecond=0
                        )
                        day_end = day_start + timedelta(days=1)

                        existing_on_day = list(
                            self.workout_repository.collection.find(
                                {
                                    "user_email": user_email,
                                    "date": {"$gte": day_start, "$lt": day_end},
                                }
                            )
                        )

                        if existing_on_day:
                            if mode == "skip_duplicates":
                                logger.debug(
                                    "Workout on day %s already exists, skipping",
                                    day_start.date(),
                                )
                                skipped_count += 1
                                continue
                            elif mode == "overwrite":
                                for doc in existing_on_day:
                                    self.workout_repository.collection.delete_one(
                                        {"_id": doc["_id"]}
                                    )
                                logger.info(
                                    "Overwriting %d existing workouts on %s",
                                    len(existing_on_day),
                                    day_start.date(),
                                )

                    elif exists:
                        if mode == "skip_duplicates":
                            logger.debug(
                                "Workout with external_id %s already exists, skipping",
                                hevy_workout.get("id"),
                            )
                            skipped_count += 1
                            continue
                        elif mode == "overwrite":
                            self.workout_repository.collection.delete_one(
                                {"_id": exists["_id"]}
                            )
                            logger.info(
                                "Overwriting workout with external_id %s",
                                hevy_workout.get("id"),
                            )

                    # Save
                    self.workout_repository.save_log(workout_log)
                    imported_count += 1

                except Exception as e:
                    logger.error("Error importing specific workout: %s", e)
                    failed_count += 1

            # Pagination check
            if len(workouts_batch) < page_size:
                has_more = False
            else:
                page += 1

            # Safegaurd loop
            if page > 100:
                logger.warning("Hit page limit safeguard")
                break

        return {
            "imported": imported_count,
            "skipped": skipped_count,
            "failed": failed_count,
        }

    async def get_routines(
        self, api_key: str, page: int = 1, page_size: int = 10
    ) -> Optional[RoutineListResponse]:
        """
        Fetches a paginated list of routines from Hevy.
        """
        page_size = min(page_size, 10)
        logger.info(
            "Fetching routines from Hevy (page=%d, page_size=%d)", page, page_size
        )
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/routines",
                    headers={"api-key": api_key},
                    params={"page": page, "pageSize": page_size},
                    timeout=20.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    logger.info(
                        "Hevy API returned %d routines", len(data.get("routines", []))
                    )
                    return RoutineListResponse(**data)

                logger.error(
                    "Hevy API routines error: %d - Body: %s",
                    response.status_code,
                    response.text,
                )
                return None
            except Exception as e:
                logger.error("Failed to fetch routines: %s", e)
                return None

    async def get_routine_by_id(
        self, api_key: str, routine_id: str
    ) -> Optional[HevyRoutine]:
        """
        Fetches a specific routine by ID.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/routines/{routine_id}",
                    headers={"api-key": api_key},
                    timeout=10.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    routine_data = data.get("routine")
                    if isinstance(routine_data, list) and routine_data:
                        routine_data = routine_data[0]

                    if isinstance(routine_data, dict):
                        return HevyRoutine(**routine_data)

                logger.error(
                    "Hevy API get routine error: %d - Body: %s",
                    response.status_code,
                    response.text,
                )
                return None
            except Exception:
                logger.error("Failed to fetch routine %s", routine_id)
                return None

    @staticmethod
    def _prepare_routine_payload(routine_data: dict, for_update: bool = False) -> dict:
        """
        Cleans routine payload before sending to Hevy API.

        Hevy API rejects:
        - folder_id in PUT requests (remove for_update=True)
        - index in exercises and sets (always remove)
        - title in individual exercises (always remove)

        Args:
            routine_data: Routine dict from model_dump()
            for_update: True if this is a PUT request (removes folder_id)

        Returns:
            Cleaned routine_data dict
        """
        logger.debug(
            "[_prepare_routine_payload] Starting cleanup - for_update=%s, routine_title=%s",
            for_update,
            routine_data.get("title", "UNKNOWN"),
        )

        removed_fields = {"folder_id": 0, "exercise_index": 0, "exercise_title": 0, "set_index": 0}

        # Remove folder_id for PUT (not allowed in update)
        if for_update and "folder_id" in routine_data:
            del routine_data["folder_id"]
            removed_fields["folder_id"] += 1
            logger.debug("[_prepare_routine_payload] Removed folder_id (PUT request)")

        # Clean exercises: remove index and title, then clean sets
        if "exercises" in routine_data:
            num_exercises = len(routine_data["exercises"])
            logger.debug("[_prepare_routine_payload] Cleaning %d exercises", num_exercises)

            for ex_idx, ex in enumerate(routine_data["exercises"]):
                ex_id = ex.get("exercise_template_id", "UNKNOWN")

                # Remove index from exercise
                if "index" in ex:
                    del ex["index"]
                    removed_fields["exercise_index"] += 1

                # Remove title from exercise (API doesn't accept it in routine update)
                if "title" in ex:
                    del ex["title"]
                    removed_fields["exercise_title"] += 1
                    logger.debug(
                        "[_prepare_routine_payload] Removed title from exercise %d (ID: %s)",
                        ex_idx,
                        ex_id,
                    )

                # Remove index from all sets
                if "sets" in ex:
                    num_sets = len(ex["sets"])
                    logger.debug(
                        "[_prepare_routine_payload] Cleaning %d sets in exercise %d",
                        num_sets,
                        ex_idx,
                    )

                    for set_idx, s in enumerate(ex["sets"]):
                        if "index" in s:
                            del s["index"]
                            removed_fields["set_index"] += 1

        logger.info(
            "[_prepare_routine_payload] Cleanup complete - Removed: %s",
            removed_fields,
        )
        return routine_data

    async def create_routine(
        self, api_key: str, routine: HevyRoutine
    ) -> tuple[Optional[HevyRoutine], Optional[str]]:
        """
        Creates a new routine in Hevy.
        """
        async with httpx.AsyncClient() as client:
            try:
                logger.info(
                    "[create_routine] Creating routine: %s", routine.title
                )

                routine_data = routine.model_dump(
                    exclude={"id", "created_at", "updated_at"},
                    exclude_none=True,
                )

                logger.debug(
                    "[create_routine] Routine data before cleanup - exercises: %d",
                    len(routine_data.get("exercises", [])),
                )

                # Ensure folder_id is included (can be null)
                routine_data["folder_id"] = routine.folder_id

                # Clean payload: remove index, title, etc.
                logger.debug("[create_routine] Cleaning payload for POST request")
                routine_data = self._prepare_routine_payload(routine_data, for_update=False)

                import json

                payload = {"routine": routine_data}

                logger.debug(
                    "[create_routine] Payload after cleanup - exercises: %d",
                    len(payload["routine"].get("exercises", [])),
                )

                logger.info(
                    "[create_routine] Sending payload:\n%s",
                    json.dumps(payload, indent=2, default=str),
                )

                response = await client.post(
                    f"{self.BASE_URL}/routines",
                    headers={"api-key": api_key},
                    json=payload,
                    timeout=20.0,
                )

                logger.info(
                    "[create_routine] Response status: %s", response.status_code
                )

                if response.status_code in [200, 201]:
                    response_json = response.json()
                    routine_resp = response_json.get("routine")

                    if isinstance(routine_resp, list):
                        if routine_resp:
                            routine_resp = routine_resp[0]
                        else:
                            return None, "API returned empty list"

                    if isinstance(routine_resp, dict):
                        return HevyRoutine(**routine_resp), None

                    return None, f"Unexpected response format: {type(routine_resp)}"

                error_body = response.text
                logger.error(
                    "[create_routine] Error: %s - Body: %s",
                    response.status_code,
                    error_body,
                )

                try:
                    error_json = response.json()
                    if "routine-limit-exceeded" in str(error_json):
                        return None, "LIMIT_EXCEEDED"
                    error_msg = error_json.get("error", error_body)
                    return None, f"API Error ({response.status_code}): {error_msg}"
                except Exception:
                    pass

                return None, f"API Error ({response.status_code}): {error_body}"
            except Exception as e:
                logger.error("Failed to create routine: %s", e, exc_info=True)
                return None, str(e)

    async def update_routine(
        self, api_key: str, routine_id: str, routine: HevyRoutine
    ) -> Optional[HevyRoutine]:
        """
        Updates an existing routine in Hevy.
        """
        async with httpx.AsyncClient() as client:
            try:
                logger.info(
                    "[update_routine] Updating routine ID: %s (title: %s)",
                    routine_id,
                    routine.title,
                )

                routine_data = routine.model_dump(
                    exclude={"id", "created_at", "updated_at"},
                    exclude_none=True,
                )

                logger.debug(
                    "[update_routine] Routine data before cleanup - exercises: %d",
                    len(routine_data.get("exercises", [])),
                )

                # Clean payload: remove index, title, folder_id, etc. for PUT
                logger.debug("[update_routine] Cleaning payload for PUT request (for_update=True)")
                routine_data = self._prepare_routine_payload(routine_data, for_update=True)

                import json

                payload = {"routine": routine_data}

                logger.debug(
                    "[update_routine] Payload after cleanup - exercises: %d",
                    len(payload["routine"].get("exercises", [])),
                )

                logger.info(
                    "[update_routine] Sending payload for routine %s:\n%s",
                    routine_id,
                    json.dumps(payload, indent=2, default=str),
                )

                response = await client.put(
                    f"{self.BASE_URL}/routines/{routine_id}",
                    headers={"api-key": api_key},
                    json=payload,
                    timeout=20.0,
                )

                logger.info("[update_routine] Status: %d", response.status_code)

                if response.status_code == 200:
                    data = response.json()
                    routine_data = data.get("routine")
                    if isinstance(routine_data, list) and routine_data:
                        routine_data = routine_data[0]

                    if isinstance(routine_data, dict):
                        return HevyRoutine(**routine_data)

                # Detailed error logging
                error_body = response.text
                logger.error(
                    "Hevy routine update failed: %d - Body: %s",
                    response.status_code,
                    error_body,
                )
                return None
            except Exception as e:
                logger.error(
                    "Failed to update routine %s: %s", routine_id, e, exc_info=True
                )
                return None

    async def get_exercise_templates(
        self, api_key: str, page: int = 1, page_size: int = 20
    ) -> Optional[ExerciseTemplateListResponse]:
        """
        Fetches a paginated list of exercise templates from Hevy.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/exercise_templates",
                    headers={"api-key": api_key},
                    params={"page": page, "pageSize": page_size},
                    timeout=20.0,
                )
                if response.status_code == 200:
                    return ExerciseTemplateListResponse(**response.json())
                logger.warning(
                    "Hevy API exercise templates returned %d", response.status_code
                )
                return None
            except Exception as e:
                logger.error("Failed to fetch exercise templates: %s", e)
                return None

    async def get_all_exercise_templates(
        self, api_key: str
    ) -> list[HevyExerciseTemplate]:
        """
        Fetches ALL exercise templates by iterating through all pages.
        """
        import time

        now = time.time()

        # Check cache
        if api_key in self._exercises_cache:
            ts, templates = self._exercises_cache[api_key]
            if now - ts < self.CACHE_DURATION:
                logger.debug(
                    "Returning %d exercise templates from memory cache", len(templates)
                )
                return templates

        all_templates = []
        page = 1
        page_size = 100

        logger.info("Fetching exercise templates from Hevy API (cache miss or expired)")
        try:
            while True:
                resp = await self.get_exercise_templates(api_key, page, page_size)
                if not resp or not resp.exercise_templates:
                    break

                all_templates.extend(resp.exercise_templates)
                if page >= resp.page_count:
                    break
                page += 1

            # Save to cache if successful
            if all_templates:
                self._exercises_cache[api_key] = (now, all_templates)

            return all_templates
        except Exception as e:
            logger.error("Error in get_all_exercise_templates: %s", e)
            # Try to return expired cache if we have it
            if api_key in self._exercises_cache:
                _, templates = self._exercises_cache[api_key]
                return templates
            return []
