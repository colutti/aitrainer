"""Initialize admin_users collection with indexes"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import os

async def init_admin_collection():
    """Create admin_users collection with indexes"""
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("DB_NAME", "aitrainer")

    client = AsyncIOMotorClient(mongo_uri)
    db: AsyncIOMotorDatabase = client[db_name]

    # Create collection if doesn't exist
    if "admin_users" not in await db.list_collection_names():
        await db.create_collection("admin_users")
        print("✅ Created admin_users collection")

    # Create unique index on email
    await db.admin_users.create_index("email", unique=True)
    print("✅ Created unique index on email")

    client.close()

if __name__ == "__main__":
    asyncio.run(init_admin_collection())
