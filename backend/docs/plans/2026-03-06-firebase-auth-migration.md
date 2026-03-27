# Firebase Auth Migration Implementation Plan

> Execution workflow: use `.agent/workflows/executing-plans.md` to implement this plan in batches.

**Goal:** Completely replace the custom email/password authentication system with Firebase Authentication, migrating existing users seamlessly.

**Architecture:** Firebase will handle all authentication (Email/Password + Social), becoming the source of truth for passwords. Our backend will only verify Firebase ID tokens using the Admin SDK and generate a custom FityQ JWT for internal session management. We will write a script to migrate existing users to Firebase without requiring immediate password resets (users can use forgot password if they don't want to use social login).

**Tech Stack:** Firebase Auth (Client & Admin SDK), FastAPI, React, Zustand

---

### Task 1: Create User Migration Script

**Files:**
- Create: `backend/scripts/migrate_users_to_firebase.py`

**Step 1: Write the failing test**
*(No unit test needed for migration scripts, but test dry-run is required).*

**Step 2: Run test to verify it fails**
N/A

**Step 3: Write minimal implementation**

```python
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import firebase_admin.auth
from src.core.deps import get_mongo_database
from src.core.firebase import init_firebase

def migrate():
    init_firebase()
    db = get_mongo_database()
    users = db.collection.find({})
    for user in users:
        email = user.get("email")
        if not email:
            continue
            
        try:
            firebase_admin.auth.get_user_by_email(email)
            print(f"User {email} already exists in Firebase.")
        except firebase_admin.auth.UserNotFoundError:
            # We create the user with no password so they can use "forgot password" or social login.
            # Bcrypt hash migration is possible but complex. This is the safest fallback.
            firebase_admin.auth.create_user(email=email, display_name=user.get("display_name"))
            print(f"Created Firebase user: {email}")

if __name__ == "__main__":
    migrate()
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python scripts/migrate_users_to_firebase.py`
Expected: Output showing existing users created in Firebase.

**Step 5: Commit**

```bash
git add backend/scripts/migrate_users_to_firebase.py
git commit -m "feat: add script to migrate existing users to firebase"
```

### Task 2: Update Backend Auth Endpoints

**Files:**
- Modify: `backend/src/api/endpoints/user.py`
- Modify: `backend/src/api/models/auth.py`

**Step 1: Write the failing test**

Modify `backend/tests/api/endpoints/test_user.py` to check `/user/login` with Firebase token instead of email/password.

**Step 2: Run test to verify it fails**

Run: `make test-backend`
Expected: FAIL

**Step 3: Write minimal implementation**

In `backend/src/api/models/auth.py`, rename `SocialLoginRequest` to `FirebaseLoginRequest` (with `token: str`).
In `backend/src/api/endpoints/user.py`:
- Remove the old `/login` that takes email/password.
- Keep the `/social-login` logic, but rename its route to `/login`. It will receive `FirebaseLoginRequest` (the token) and issue our internal JWT.

**Step 4: Run test to verify it passes**

Run: `make test-backend`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/api/endpoints/user.py backend/src/api/models/auth.py
git commit -m "refactor: replace custom login endpoint with firebase token verification"
```

### Task 3: Remove Custom Password Validation

**Files:**
- Modify: `backend/src/services/auth.py`
- Modify: `backend/src/repositories/user_repository.py`
- Modify: `backend/src/api/models/user_profile.py`

**Step 1: Write the failing test / preparation**
Run pytest over all backend tests to see what breaks when we remove `user_login` from auth.py.

**Step 2: Write minimal implementation**
- `auth.py`: Remove `user_login` function.
- `user_repository.py`: Remove `validate_credentials` function.
- `user_profile.py`: Make sure `password_hash` field is optional (it already is) and no longer required by any logic.

**Step 3: Run test to verify it passes**
Fix any tests that relied on `validate_credentials` or password rules.
Run: `make test-backend`
Expected: PASS

**Step 4: Commit**
```bash
git add backend/src/services/auth.py backend/src/repositories/user_repository.py backend/src/api/models/user_profile.py
git commit -m "refactor: remove standard password validation logic"
```

### Task 4: Update Frontend Auth Hook

**Files:**
- Modify: `frontend/src/shared/hooks/useAuth.ts`
- Modify: `frontend/src/shared/hooks/useAuth.test.ts`

**Step 1: Write the failing test**
Update `frontend/src/shared/hooks/useAuth.test.ts` to mock `signInWithEmailAndPassword` from Firebase instead of standard API call to `/user/login` with email/pwd.

**Step 2: Run test to verify it fails**
Run: `npm test useAuth` inside `frontend/`
Expected: FAIL

**Step 3: Write minimal implementation**
In `useAuth.ts`:
```typescript
import { signInWithEmailAndPassword } from 'firebase/auth';
import { auth } from '../../features/auth/firebase';

// Update login action:
login: async (email, password) => {
  set({ isLoading: true });
  try {
     const result = await signInWithEmailAndPassword(auth, email, password);
     const token = await result.user.getIdToken();
     
     // Send token to our new unified backend /login
     const response = await httpClient<{ token: string }>('/user/login', {
       method: 'POST',
       body: JSON.stringify({ token }),
     });
     // ... rest is same
  }
}
```

**Step 4: Run test to verify it passes**
Run: `npm test useAuth` inside `frontend/`
Expected: PASS

**Step 5: Commit**
```bash
git add frontend/src/shared/hooks/useAuth.ts frontend/src/shared/hooks/useAuth.test.ts
git commit -m "feat: migrate frontend login to use firebase email/password"
```

### Task 5: Handle Firebase Registration

**Files:**
- Modify: `frontend/src/features/onboarding/api/onboarding-api.ts` (or where register is called)

**Step 1: Locate Registration flow**
Identify where the system calls the API to create the user account originally.

**Step 2: Change to Firebase Auth**
Execute `createUserWithEmailAndPassword(auth, email, password)` on the frontend. Take the resulting `idToken` and pass it to the backend to create the MongoDB profile.

**Step 3: Test Registration E2E**
Ensure the user can sign up and login cleanly.

**Step 4: Commit**
```bash
git commit -am "feat: use firebase for user registration"
```
