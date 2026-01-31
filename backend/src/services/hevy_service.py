from datetime import datetime, timezone, timedelta
import logging
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

logger = logging.getLogger(__name__)


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
                logger.error(f"Hevy API validation failed: {e}")
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
                logger.error(f"Failed to get workout count: {e}")
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
                logger.warning(f"Hevy API returned {response.status_code}")
                return []
            except Exception as e:
                logger.error(f"Failed to fetch workouts page {page}: {e}")
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
                response = await client.get(
                    f"{self.BASE_URL}/workouts/{workout_id}",
                    headers={"api-key": api_key},
                    timeout=10.0,
                )
                if response.status_code == 200:
                    # Hevy API returns {"workout": {...}}
                    return response.json().get("workout")
                logger.warning(
                    f"Hevy API workout fetch returned {response.status_code} for {workout_id}"
                )
                return None
            except Exception as e:
                logger.error(f"Failed to fetch workout {workout_id}: {e}")
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

                for s in sets_data:
                    reps = s.get("reps")
                    weight = s.get("weight_kg")

                    # Hevy might return None for some fields
                    reps_per_set.append(int(reps) if reps is not None else 0)
                    weights_per_set.append(float(weight) if weight is not None else 0.0)

                exercise_log = ExerciseLog(
                    name=exercise_data["title"],
                    sets=len(sets_data),
                    reps_per_set=reps_per_set,
                    weights_per_set=weights_per_set,
                )
                exercises.append(exercise_log)

            if not exercises:
                logger.warning(
                    f"Hevy workout {hevy_workout.get('id')} has no valid exercises"
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
            logger.error(f"Error transforming workout {hevy_workout.get('id')}: {e}")
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
            f"Starting Hevy import for {user_email}, mode={mode}, from={from_date}"
        )

        while has_more:
            workouts_batch = await self.fetch_workouts(api_key, page, page_size)
            if not workouts_batch:
                break

            for hevy_workout in workouts_batch:
                try:
                    # Check date filter (Hevy returns newest first usually, but we should check)
                    start_time_str = hevy_workout["start_time"].replace("Z", "+00:00")
                    workout_date = datetime.fromisoformat(start_time_str)

                    if from_date and workout_date < from_date:
                        # If workouts are ordered by date desc, we could stop here?
                        # API doc says "Get a paginated list of workouts".
                        # It doesn't explicitly guarantee order, but usually it's desc.
                        # Let's just skip for now to be safe.
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
                        # 2. Daily deduplication (One Workout Per Day Policy)
                        # We use UTC date to catch both midnight entries and regular ones on the same day.
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
                                    f"Workout on day {day_start.date()} already exists, skipping"
                                )
                                skipped_count += 1
                                continue
                            elif mode == "overwrite":
                                for doc in existing_on_day:
                                    self.workout_repository.collection.delete_one(
                                        {"_id": doc["_id"]}
                                    )
                                logger.info(
                                    f"Overwriting {len(existing_on_day)} existing workouts on {day_start.date()}"
                                )

                    elif exists:
                        if mode == "skip_duplicates":
                            logger.debug(
                                f"Workout with external_id {hevy_workout.get('id')} already exists, skipping"
                            )
                            skipped_count += 1
                            continue
                        elif mode == "overwrite":
                            self.workout_repository.collection.delete_one(
                                {"_id": exists["_id"]}
                            )
                            logger.info(
                                f"Overwriting workout with external_id {hevy_workout.get('id')}"
                            )

                    # Save
                    self.workout_repository.save_log(workout_log)
                    imported_count += 1

                except Exception as e:
                    logger.error(f"Error importing specific workout: {e}")
                    failed_count += 1

            # Pagination check
            # We don't have total count in fetch response (wrapper), but we can check if batch < page_size
            if len(workouts_batch) < page_size:
                has_more = False
            else:
                page += 1

            # Safegaurd loop
            if page > 100:  # Limit to 1000 workouts for this batch to prevent timeouts
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
        Max pageSize is 10.
        """
        page_size = min(page_size, 10)
        logger.info(f"Fetching routines from Hevy (page={page}, page_size={page_size})")
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
                    logger.info(f"Hevy API returned {len(data.get('routines', []))} routines")
                    return RoutineListResponse(**data)
                
                logger.error(f"Hevy API routines error: {response.status_code} - Body: {response.text}")
                return None
            except Exception as e:
                logger.error(f"Failed to fetch routines: {e}")
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
                
                logger.error(f"Hevy API get routine error: {response.status_code} - Body: {response.text}")
                return None
            except Exception as e:
                logger.error(f"Failed to fetch routine {routine_id}: {e}")
                return None

    async def create_routine(
        self, api_key: str, routine: HevyRoutine
    ) -> tuple[Optional[HevyRoutine], Optional[str]]:
        """
        Creates a new routine in Hevy.
        Returns: (routine, error_message) - routine is None on failure, error_message contains details
        """
        async with httpx.AsyncClient() as client:
            try:
                # Prepare payload: Hevy API is strict about fields
                # Use exclude_none=True (Hevy rejects many null fields)
                routine_data = routine.model_dump(
                    exclude={"id", "created_at", "updated_at"},
                    exclude_none=True,
                )
                
                # Exclude exercise-metadata (forbidden in POST/PUT)
                if "exercises" in routine_data:
                    for ex in routine_data["exercises"]:
                        # Always remove title even if not None
                        if "title" in ex:
                            del ex["title"]

                # CRITICAL: Hevy API requires folder_id field (null = default folder)
                # Always include it, even if None
                routine_data["folder_id"] = routine.folder_id

                import json
                payload = {"routine": routine_data}

                logger.info(
                    f"[create_routine] Sending payload:\n{json.dumps(payload, indent=2, default=str)}"
                )

                response = await client.post(
                    f"{self.BASE_URL}/routines",
                    headers={"api-key": api_key},
                    json=payload,
                    timeout=20.0,
                )

                logger.info(f"[create_routine] Response status: {response.status_code}")

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

                # Parse error response
                error_body = response.text
                logger.error(f"[create_routine] Error: {response.status_code} - Body: {error_body}")
                
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
                logger.error(f"Failed to create routine: {e}", exc_info=True)
                return None, str(e)

    async def update_routine(
        self, api_key: str, routine_id: str, routine: HevyRoutine
    ) -> Optional[HevyRoutine]:
        """
        Updates an existing routine in Hevy.
        """
        async with httpx.AsyncClient() as client:
            try:
                # Prepare payload: Hevy API is strict about fields
                # Use exclude_none=True (Hevy rejects many null fields)
                routine_data = routine.model_dump(
                    exclude={"id", "created_at", "updated_at"},
                    exclude_none=True,
                )
                
                # Exclude exercise-metadata (forbidden in PUT)
                if "exercises" in routine_data:
                    for ex in routine_data["exercises"]:
                        if "title" in ex:
                            del ex["title"]
                
                # IMPORTANT: 'folder_id' is NOT allowed in PUT payload
                if "folder_id" in routine_data:
                    del routine_data["folder_id"]
                
                import json
                payload = {"routine": routine_data}

                logger.info(
                    f"[update_routine] Sending payload for routine {routine_id}:\n{json.dumps(payload, indent=2, default=str)}"
                )

                response = await client.put(
                    f"{self.BASE_URL}/routines/{routine_id}",
                    headers={"api-key": api_key},
                    json=payload,
                    timeout=20.0,
                )
                
                logger.info(f"[update_routine] Status: {response.status_code}")
                
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
                    f"Hevy routine update failed: {response.status_code} - Body: {error_body}"
                )
                return None
            except Exception as e:
                logger.error(f"Failed to update routine {routine_id}: {e}", exc_info=True)
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
                    f"Hevy API exercise templates returned {response.status_code}"
                )
                return None
            except Exception as e:
                logger.error(f"Failed to fetch exercise templates: {e}")
                return None

    async def get_all_exercise_templates(
        self, api_key: str
    ) -> list[HevyExerciseTemplate]:
        """
        Fetches ALL exercise templates by iterating through all pages.
        Includes in-memory caching to avoid hitting the API too hard/timeouts.
        """
        import time

        now = time.time()

        # Check cache
        if api_key in self._exercises_cache:
            ts, templates = self._exercises_cache[api_key]
            if now - ts < self.CACHE_DURATION:
                logger.debug(
                    f"Returning {len(templates)} exercise templates from memory cache"
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
            logger.error(f"Error in get_all_exercise_templates: {e}")
            # Try to return expired cache if we have it
            if api_key in self._exercises_cache:
                _, templates = self._exercises_cache[api_key]
                return templates
            return []
