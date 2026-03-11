import os
import sys

# Ensure backend root is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import firebase_admin.auth
from src.core.deps import get_mongo_database
from src.core.firebase import init_firebase

def migrate():
    """
    Migrates all users from MongoDB to Firebase Auth.
    Users will be created without a password, requiring them to use "Forgot Password"
    or Social Login (Google) to access their account for the first time in the new system.
    """
    init_firebase()
    db = get_mongo_database()
    
    users = db.users.collection.find({})
    count_created = 0
    count_skipped = 0
    
    print("Starting user migration to Firebase...")
    
    for user in users:
        email = user.get("email")
        if not email:
            continue
            
        try:
            # Check if user already exists in Firebase
            firebase_admin.auth.get_user_by_email(email)
            print(f"[-] User {email} already exists in Firebase. Skipping.")
            count_skipped += 1
        except firebase_admin.auth.UserNotFoundError:
            # Create user in Firebase
            try:
                display_name = user.get("display_name") or email.split('@')[0]
                firebase_admin.auth.create_user(
                    email=email,
                    display_name=display_name
                )
                print(f"[+] Created Firebase user: {email}")
                count_created += 1
            except Exception as e:
                print(f"[!] Error creating user {email}: {str(e)}")
        except Exception as e:
            print(f"[!] Fatal error checking user {email}: {str(e)}")

    print("\nMigration finished.")
    print(f"Total created: {count_created}")
    print(f"Total skipped: {count_skipped}")

if __name__ == "__main__":
    migrate()
