#!/usr/bin/env python3
"""
Script for managing user invites.

Usage:
    python manage_invites.py create --email user@example.com [--expires-hours 72]
    python manage_invites.py list [--status active|all]
    python manage_invites.py get <token>
    python manage_invites.py revoke <token>
"""
import argparse
import sys
import os
import uuid
from datetime import datetime, timedelta, timezone
from pprint import pprint
from pymongo import MongoClient

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.core.config import settings
    from src.api.models.invite import Invite
    from src.repositories.invite_repository import InviteRepository
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
        # Force connection check
        client.admin.command('ping')
        return db
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        sys.exit(1)


def create_invite(args, db):
    """Create a new invite."""
    email = args.email
    expires_hours = args.expires_hours or 72
    
    repo = InviteRepository(db)
    
    # Check if user already exists
    users_collection = db["users"]
    if users_collection.find_one({"email": email}):
        print(f"❌ Error: User with email {email} already exists.")
        return
    
    # Check if there's already an active invite
    if repo.has_active_invite(email):
        print(f"⚠️  Warning: Active invite already exists for {email}")
        existing = repo.get_by_email(email)
        print(f"   Token: {existing.token}")
        print(f"   Expires: {existing.expires_at}")
        
        overwrite = input("Create new invite anyway? (y/N): ")
        if overwrite.lower() != 'y':
            print("Operation cancelled.")
            return
    
    # Create invite
    token = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=expires_hours)
    
    invite = Invite(
        token=token,
        email=email,
        created_at=now,
        expires_at=expires_at,
        used=False
    )
    
    repo.create(invite)
    
    # Construct onboarding URL
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    onboarding_url = f"{frontend_url}/onboarding?token={token}"
    
    print("\n✅ Invite created successfully!")
    print(f"\n📧 Email: {email}")
    print(f"🔑 Token: {token}")
    print(f"⏰ Expires: {expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"\n🔗 Onboarding URL:")
    print(f"   {onboarding_url}")
    print()


def list_invites(args, db):
    """List invites."""
    repo = InviteRepository(db)
    status = args.status or "active"
    
    if status == "active":
        invites = repo.list_active()
        print(f"\n📋 Active Invites ({len(invites)}):")
    else:
        # List all invites
        all_invites_data = db["invites"].find().sort("created_at", -1)
        invites = [Invite(**data) for data in all_invites_data]
        print(f"\n📋 All Invites ({len(invites)}):")
    
    if not invites:
        print("   No invites found.")
        return
    
    print()
    print(f"{'Email':<30} | {'Token':<36} | {'Status':<10} | {'Expires'}")
    print("-" * 110)
    
    now = datetime.now(timezone.utc)
    for invite in invites:
        if invite.used:
            status_str = "Used"
        elif invite.expires_at < now:
            status_str = "Expired"
        else:
            status_str = "Active"
        
        expires_str = invite.expires_at.strftime('%Y-%m-%d %H:%M')
        print(f"{invite.email:<30} | {invite.token:<36} | {status_str:<10} | {expires_str}")
    print()


def get_invite(args, db):
    """Get invite details."""
    token = args.token
    repo = InviteRepository(db)
    
    invite = repo.get_by_token(token)
    if not invite:
        print(f"❌ Invite not found: {token}")
        return
    
    now = datetime.now(timezone.utc)
    
    print(f"\n📄 Invite Details:")
    print(f"   Token: {invite.token}")
    print(f"   Email: {invite.email}")
    print(f"   Created: {invite.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"   Expires: {invite.expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    if invite.used:
        print(f"   Status: ❌ Used")
        print(f"   Used At: {invite.used_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    elif invite.expires_at < now:
        print(f"   Status: ⏰ Expired")
    else:
        time_left = invite.expires_at - now
        hours_left = int(time_left.total_seconds() / 3600)
        print(f"   Status: ✅ Active ({hours_left}h remaining)")
        
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        onboarding_url = f"{frontend_url}/onboarding?token={token}"
        print(f"\n   🔗 Onboarding URL:")
        print(f"      {onboarding_url}")
    print()


def revoke_invite(args, db):
    """Revoke an invite."""
    token = args.token
    repo = InviteRepository(db)
    
    # Check if exists
    invite = repo.get_by_token(token)
    if not invite:
        print(f"❌ Invite not found: {token}")
        return
    
    print(f"\n⚠️  About to revoke invite:")
    print(f"   Email: {invite.email}")
    print(f"   Token: {token}")
    
    confirm = input("\nAre you sure? (y/N): ")
    if confirm.lower() != 'y':
        print("Operation cancelled.")
        return
    
    if repo.revoke(token):
        print("✅ Invite revoked successfully.")
    else:
        print("❌ Failed to revoke invite.")


def main():
    parser = argparse.ArgumentParser(description="Manage User Invites")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # CREATE
    create_parser = subparsers.add_parser("create", help="Create a new invite")
    create_parser.add_argument("--email", required=True, help="Email for the invite")
    create_parser.add_argument(
        "--expires-hours",
        type=int,
        default=72,
        help="Hours until invite expires (default: 72)"
    )
    
    # LIST
    list_parser = subparsers.add_parser("list", help="List invites")
    list_parser.add_argument(
        "--status",
        choices=["active", "all"],
        default="active",
        help="Filter by status (default: active)"
    )
    
    # GET
    get_parser = subparsers.add_parser("get", help="Get invite details")
    get_parser.add_argument("token", help="Invite token")
    
    # REVOKE
    revoke_parser = subparsers.add_parser("revoke", help="Revoke an invite")
    revoke_parser.add_argument("token", help="Invite token to revoke")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    confirm_execution(f"Invite Management - {args.command}", {"args": str(sys.argv[1:])})
    db = get_database()
    
    if args.command == "create":
        create_invite(args, db)
    elif args.command == "list":
        list_invites(args, db)
    elif args.command == "get":
        get_invite(args, db)
    elif args.command == "revoke":
        revoke_invite(args, db)


if __name__ == "__main__":
    main()
