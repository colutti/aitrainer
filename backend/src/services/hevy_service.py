from datetime import datetime, timezone
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
                duration_minutes=duration_minutes
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
                    # We query by date matches (within a small window or exact?)
                    # Hevy's date is precise. Our date is stored as ISODate in Mongo. 
                    # Let's check for exact match on date & user_email
                    exists = self.workout_repository.collection.find_one({
                        "user_email": user_email,
                        "date": workout_date
                    })

                    if exists:
                        if mode == "skip_duplicates":
                            logger.debug(f"Workout at {workout_date} already exists for {user_email}, skipping")
                            skipped_count += 1
                            continue
                        elif mode == "overwrite":
                            # Delete existing
                            self.workout_repository.collection.delete_one({"_id": exists["_id"]})
                    
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
