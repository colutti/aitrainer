from datetime import datetime, timezone, timedelta
import logging
from typing import Optional, Any
import httpx
from src.api.models.workout_log import WorkoutLog, ExerciseLog
from src.repositories.workout_repository import WorkoutRepository

logger = logging.getLogger(__name__)

class HevyService:
    BASE_URL = "https://api.hevyapp.com/v1"

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
                    timeout=10.0
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
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("workout_count", 0)
                return 0
            except Exception as e:
                logger.error(f"Failed to get workout count: {e}")
                return 0

    async def fetch_workouts(self, api_key: str, page: int = 1, page_size: int = 10) -> list[dict]:
        """
        Fetches a page of workouts from Hevy API.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/workouts",
                    headers={"api-key": api_key},
                    params={"page": page, "pageSize": page_size},
                    timeout=20.0
                )
                if response.status_code == 200:
                    return response.json().get("workouts", [])
                logger.warning(f"Hevy API returned {response.status_code}")
                return []
            except Exception as e:
                logger.error(f"Failed to fetch workouts page {page}: {e}")
                return []

    def transform_to_workout_log(self, hevy_workout: dict, user_email: str) -> Optional[WorkoutLog]:
        """
        Transforms a Hevy workout dict to our WorkoutLog model.
        """
        try:
            # Parse dates
            start_time = datetime.fromisoformat(hevy_workout["start_time"].replace("Z", "+00:00"))
            
            # Use end_time to calculate duration if available
            duration_minutes = None
            if hevy_workout.get("end_time"):
                end_time = datetime.fromisoformat(hevy_workout["end_time"].replace("Z", "+00:00"))
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
                    weights_per_set=weights_per_set
                )
                exercises.append(exercise_log)

            if not exercises:
                 logger.warning(f"Hevy workout {hevy_workout.get('id')} has no valid exercises")
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
                external_id=hevy_workout.get("id")
            )
        except Exception as e:
            logger.error(f"Error transforming workout {hevy_workout.get('id')}: {e}")
            return None

    async def import_workouts(
        self, 
        user_email: str, 
        api_key: str, 
        from_date: Optional[datetime] = None,
        mode: str = "skip_duplicates" # 'skip_duplicates' or 'overwrite'
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

        logger.info(f"Starting Hevy import for {user_email}, mode={mode}, from={from_date}")

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
                    workout_log = self.transform_to_workout_log(hevy_workout, user_email)
                    if not workout_log:
                        failed_count += 1
                        continue

                    # Check for existence
                    # 1. Try by external_id
                    exists = self.workout_repository.collection.find_one({
                        "user_email": user_email,
                        "external_id": hevy_workout.get("id")
                    })

                    if not exists:
                        # 2. Daily deduplication (One Workout Per Day Policy)
                        # We use UTC date to catch both midnight entries and regular ones on the same day.
                        day_start = workout_date.replace(hour=0, minute=0, second=0, microsecond=0)
                        day_end = day_start + timedelta(days=1)
                        
                        existing_on_day = list(self.workout_repository.collection.find({
                            "user_email": user_email,
                            "date": {"$gte": day_start, "$lt": day_end}
                        }))
                        
                        if existing_on_day:
                            if mode == "skip_duplicates":
                                logger.debug(f"Workout on day {day_start.date()} already exists, skipping")
                                skipped_count += 1
                                continue
                            elif mode == "overwrite":
                                for doc in existing_on_day:
                                    self.workout_repository.collection.delete_one({"_id": doc["_id"]})
                                logger.info(f"Overwriting {len(existing_on_day)} existing workouts on {day_start.date()}")
                        
                    elif exists:
                        if mode == "skip_duplicates":
                            logger.debug(f"Workout with external_id {hevy_workout.get('id')} already exists, skipping")
                            skipped_count += 1
                            continue
                        elif mode == "overwrite":
                            self.workout_repository.collection.delete_one({"_id": exists["_id"]})
                            logger.info(f"Overwriting workout with external_id {hevy_workout.get('id')}")
                    
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
            if page > 100: # Limit to 1000 workouts for this batch to prevent timeouts
                logger.warning("Hit page limit safeguard")
                break

        return {
            "imported": imported_count,
            "skipped": skipped_count,
            "failed": failed_count
        }
