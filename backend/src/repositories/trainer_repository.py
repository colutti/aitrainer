from pymongo.database import Database
from src.api.models.trainer_profile import TrainerProfile
from src.repositories.base import BaseRepository


class TrainerRepository(BaseRepository):
    def __init__(self, database: Database):
        super().__init__(database, "trainer_profiles")

    def save_profile(self, trainer_profile: TrainerProfile) -> None:
        result = self.collection.update_one(
            {"user_email": trainer_profile.user_email},
            {"$set": trainer_profile.model_dump()},
            upsert=True,
        )
        if result.upserted_id:
            self.logger.info(
                "New trainer profile created for user: %s", trainer_profile.user_email
            )
        elif result.modified_count > 0:
            self.logger.info(
                "Trainer profile updated for user: %s", trainer_profile.user_email
            )
        else:
            self.logger.debug(
                "Trainer profile for user %s already up-to-date or no changes.",
                trainer_profile.user_email,
            )

    def get_profile(self, email: str) -> TrainerProfile | None:
        trainer_profile = self.collection.find_one({"user_email": email})
        if not trainer_profile:
            self.logger.info("Trainer profile not found for email: %s", email)
            return None
        self.logger.debug("Trainer profile retrieved for email: %s", email)
        return TrainerProfile(**trainer_profile)
