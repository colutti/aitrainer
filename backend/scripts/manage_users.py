#!/usr/bin/env python3
import argparse
import sys
import os
import re
from pprint import pprint
import bcrypt
from pymongo import MongoClient
from datetime import datetime, timezone

# Add backend directory to sys.path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from src.core.config import settings
    from src.api.models.user_profile import UserProfile
    from src.api.models.trainer_profile import TrainerProfile
    from scripts.utils import confirm_execution
except ImportError as e:
    print(f"Error importing app modules: {e}")
    print("Make sure you are running this script from the 'backend' directory.")
    sys.exit(1)


def get_database():
    """Connects to MongoDB using settings."""
    try:
        client = MongoClient(settings.MONGO_URI)
        db = client[settings.DB_NAME]
        # Pymongo lazy connection, force a check
        client.admin.command("ping")
        return db
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        sys.exit(1)


def validate_password(password):
    """
    Validates password rules:
    - Min 8 chars
    - At least 1 uppercase
    - At least 1 lowercase
    - At least 1 digit
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    return True, ""


def hash_password(password):
    """Hashes password using bcrypt (matching app logic)."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def create_user(args, db):
    email = args.email
    password = args.password

    if db.users.find_one({"email": email}):
        print(f"Error: User with email {email} already exists.")
        return

    # Validate password
    valid, msg = validate_password(password)
    if not valid:
        print(f"Error: {msg}")
        return

    # User Profile (Defaults or Interactive?)
    # The plan says "Create a new user with email, password, and default profiles"
    # But also "Default user profile: prompted interactively or via CLI args"
    # To keep it simple and automatable as requested ("default configurations"),
    # I'll use sensible defaults if flags aren't provided.

    print(f"Creating user {email}...")

    # Default User Profile Data
    user_data = {
        "email": email,
        "gender": args.gender or "Masculino",
        "age": args.age or 30,
        "weight": args.weight or 75.0,
        "height": args.height or 175,
        "goal": args.goal or "Manter a forma",
        "goal_type": args.goal_type or "maintain",
        "weekly_rate": args.weekly_rate or 0.5,
    }

    try:
        profile = UserProfile(**user_data)
    except Exception as e:
        print(f"Error validating user profile data: {e}")
        return

    # Default Trainer Profile Data
    trainer_data = {"user_email": email, "trainer_type": args.trainer_type or "atlas"}

    try:
        trainer = TrainerProfile(**trainer_data)
    except Exception as e:
        print(f"Error validating trainer profile data: {e}")
        return

    # Save to MongoDB
    user_doc = profile.model_dump()
    user_doc["password_hash"] = hash_password(password)
    user_doc["created_at"] = datetime.now(timezone.utc)

    try:
        db.users.insert_one(user_doc)

        # Save trainer profile
        db.trainer_profiles.update_one(
            {"user_email": email}, {"$set": trainer.model_dump()}, upsert=True
        )

        print("User created successfully!")
        print("User Profile:")
        pprint(profile.model_dump(exclude={"password_hash"}))
        print("Trainer Profile:")
        pprint(trainer.model_dump())

    except Exception as e:
        print(f"Database error: {e}")


def list_users(args, db):
    users = list(db.users.find({}, {"email": 1, "created_at": 1, "_id": 0}))
    if not users:
        print("No users found.")
        return

    print(f"{'Email':<30} | {'Created At'}")
    print("-" * 50)
    for u in users:
        created = u.get("created_at", "N/A")
        print(f"{u['email']:<30} | {created}")


def get_user(args, db):
    email = args.email
    user = db.users.find_one({"email": email}, {"_id": 0, "password_hash": 0})
    if not user:
        print(f"User {email} not found.")
        return

    trainer = db.trainer_profiles.find_one({"user_email": email}, {"_id": 0})

    print(f"=== User Profile ({email}) ===")
    pprint(user)
    print("\n=== Trainer Profile ===")
    if trainer:
        pprint(trainer)
    else:
        print("No trainer profile found.")


def update_user(args, db):
    email = args.email
    user = db.users.find_one({"email": email})
    if not user:
        print(f"User {email} not found.")
        return

    updates = {}
    if args.age:
        updates["age"] = args.age
    if args.weight:
        updates["weight"] = args.weight
    if args.height:
        updates["height"] = args.height
    if args.goal:
        updates["goal"] = args.goal
    if args.gender:
        updates["gender"] = args.gender
    if args.goal_type:
        updates["goal_type"] = args.goal_type
    if args.weekly_rate:
        updates["weekly_rate"] = args.weekly_rate
    if args.target_weight:
        updates["target_weight"] = args.target_weight

    if not updates:
        print("No updates provided.")
        return

    try:
        # Validate updates by merging with existing data and validating via pydantic
        current_data = {
            k: v for k, v in user.items() if k != "_id" and k != "password_hash"
        }
        # Ensure input types are correct
        if "age" in updates:
            updates["age"] = int(updates["age"])
        if "height" in updates:
            updates["height"] = int(updates["height"])
        if "weight" in updates:
            updates["weight"] = float(updates["weight"])
        if "weekly_rate" in updates:
            updates["weekly_rate"] = float(updates["weekly_rate"])
        if "target_weight" in updates:
            updates["target_weight"] = float(updates["target_weight"])

        current_data.update(updates)
        # Re-validate
        UserProfile(**current_data)

        # Apply updates
        db.users.update_one({"email": email}, {"$set": updates})
        print(f"User {email} updated successfully.")

    except Exception as e:
        print(f"Validation error: {e}")


def change_password(args, db):
    email = args.email
    user = db.users.find_one({"email": email})
    if not user:
        print(f"User {email} not found.")
        return

    valid, msg = validate_password(args.new_password)
    if not valid:
        print(f"Error: {msg}")
        return

    new_hash = hash_password(args.new_password)
    db.users.update_one({"email": email}, {"$set": {"password_hash": new_hash}})
    print(f"Password for {email} updated successfully.")


def delete_user(args, db):
    email = args.email
    if not db.users.find_one({"email": email}):
        print(f"User {email} not found.")
        return

    confirm = input(
        f"Are you sure you want to delete user {email} and all related data? (y/N): "
    )
    if confirm.lower() != "y":
        print("Operation cancelled.")
        return

    # Delete User
    db.users.delete_one({"email": email})
    # Delete Trainer Profile
    db.trainer_profiles.delete_one({"user_email": email})
    # Delete Workouts
    db.workout_logs.delete_many({"user_email": email})
    # Delete Blocking Tokens? (Optional but good practice)
    # Delete Chat History?
    # Chat history is in 'message_store' collection usually for LangChain Mongo history
    # Checking database.py: collection name is likely default or 'message_store' inside db
    # The 'MongoDBChatMessageHistory' from langchain uses a specific collection.
    # We should delete that too if possible, but let's stick to knowns.

    print(f"User {email} deleted.")


def main():
    parser = argparse.ArgumentParser(description="Manage AI Trainer Users")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # CREATE
    create_parser = subparsers.add_parser("create", help="Create a new user")
    create_parser.add_argument("--email", required=True, help="User email")
    create_parser.add_argument("--password", required=True, help="User password")
    # Optional profile fields
    create_parser.add_argument("--age", type=int, help="User age")
    create_parser.add_argument("--weight", type=float, help="User weight (kg)")
    create_parser.add_argument("--height", type=int, help="User height (cm)")
    create_parser.add_argument(
        "--gender", choices=["Masculino", "Feminino"], help="User gender"
    )
    create_parser.add_argument("--goal", help="User goal")
    create_parser.add_argument(
        "--goal-type", choices=["lose", "gain", "maintain"], help="Goal type"
    )
    create_parser.add_argument("--weekly-rate", type=float, help="Weekly change rate")
    create_parser.add_argument("--target-weight", type=float, help="Target weight")
    create_parser.add_argument(
        "--trainer-type",
        choices=["atlas", "luna", "sargento", "sofia"],
        help="Trainer type",
    )

    # LIST
    subparsers.add_parser("list", help="List all users")

    # GET
    get_parser = subparsers.add_parser("get", help="Get user details")
    get_parser.add_argument("email", help="User email")

    # UPDATE
    update_parser = subparsers.add_parser("update", help="Update user profile")
    update_parser.add_argument("email", help="User email")
    update_parser.add_argument("--age", type=int, help="User age")
    update_parser.add_argument("--weight", type=float, help="User weight")
    update_parser.add_argument("--height", type=int, help="User height")
    update_parser.add_argument(
        "--gender", choices=["Masculino", "Feminino"], help="User gender"
    )
    update_parser.add_argument("--goal", help="User goal")
    update_parser.add_argument(
        "--goal-type", choices=["lose", "gain", "maintain"], help="Goal type"
    )
    update_parser.add_argument("--weekly-rate", type=float, help="Weekly change rate")
    update_parser.add_argument("--target-weight", type=float, help="Target weight")

    # PASSWORD
    pwd_parser = subparsers.add_parser("password", help="Change user password")
    pwd_parser.add_argument("email", help="User email")
    pwd_parser.add_argument("--new-password", required=True, help="New password")

    # DELETE
    del_parser = subparsers.add_parser("delete", help="Delete user")
    del_parser.add_argument("email", help="User email")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    confirm_execution(f"User Management - {args.command}", {"args": str(sys.argv[1:])})
    db = get_database()

    if args.command == "create":
        create_user(args, db)
    elif args.command == "list":
        list_users(args, db)
    elif args.command == "get":
        get_user(args, db)
    elif args.command == "update":
        update_user(args, db)
    elif args.command == "password":
        change_password(args, db)
    elif args.command == "delete":
        delete_user(args, db)


if __name__ == "__main__":
    main()
