# Firebase Social Login Implementation Plan

> Execution workflow: use `.agent/workflows/executing-plans.md` to implement this plan in batches.

**Goal:** Implement Google Social Login using Firebase Authentication on the frontend and Firebase Admin SDK on the backend, creating users on the free plan automatically if they don't exist.

**Architecture:** Frontend opens Google popup via Firebase JS SDK, gets `idToken`, and sends to FastAPI. FastAPI verifies the token via Firebase Admin, retrieves/creates the user with default physical attributes and Free plan, and returns the standard app JWT.

**Tech Stack:** React, Zustand, Firebase JS SDK, FastAPI, Firebase Admin SDK, Pytest, Vitest.

---

### Task 1: Backend - Add Firebase Dependencies and Config

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/requirements-dev.txt`
- Modify: `backend/src/core/config.py`
- Modify: `backend/.env` (instruction only)

**Step 1: Write the failing test**
No test needed for dependency addition, but we can verify the settings.

**Step 2: Write minimal implementation**
Add `firebase-admin==6.5.0` to `requirements.txt` and `requirements-dev.txt`.
In `src/core/config.py`, add `FIREBASE_CREDENTIALS: str | None = None` to `Settings`.

**Step 3: Commit**
```bash
git add requirements.txt requirements-dev.txt src/core/config.py
git commit -m "chore(backend): add firebase-admin dependency and config"
```

---

### Task 2: Backend - Initialize Firebase Admin

**Files:**
- Create: `backend/src/core/firebase.py`

**Step 1: Write minimal implementation**
Create `src/core/firebase.py` that initializes the Firebase app if `settings.FIREBASE_CREDENTIALS` is present (can be a path to JSON or a JSON string itself).

```python
import json
import firebase_admin
from firebase_admin import credentials
from src.core.config import settings
from src.core.logs import logger

def init_firebase():
    if not settings.FIREBASE_CREDENTIALS:
        logger.warning("FIREBASE_CREDENTIALS not set, Firebase Admin won't be initialized")
        return
        
    try:
        # Check if it's a JSON string or a file path
        if settings.FIREBASE_CREDENTIALS.strip().startswith('{'):
            cred_dict = json.loads(settings.FIREBASE_CREDENTIALS)
            cred = credentials.Certificate(cred_dict)
        else:
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS)
            
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize Firebase Admin: %s", e)
```

And call `init_firebase()` in `backend/src/main.py` at startup.

**Step 2: Commit**
```bash
git add src/core/firebase.py src/main.py
git commit -m "feat(backend): initialize firebase admin sdk on startup"
```

---

### Task 3: Backend - Create Social Login Endpoint 

**Files:**
- Modify: `backend/src/api/endpoints/user.py`
- Modify: `backend/src/api/models/auth.py`
- Create: `backend/tests/api/endpoints/test_user_social.py`

**Step 1: Write the failing test**
Create `backend/tests/api/endpoints/test_user_social.py`. Mock `firebase_admin.auth.verify_id_token` to return `{"email": "test@google.com", "name": "Google User", "picture": "url"}`. Test `POST /user/social-login`.

Run: `cd backend && pytest tests/api/endpoints/test_user_social.py -v`
Expected: FAIL (404 Not Found)

**Step 2: Write minimal implementation**
In `src/api/models/auth.py`, add:
```python
class SocialLoginRequest(BaseModel):
    token: str
```

In `src/api/endpoints/user.py`, add the `/social-login` route:
- Verify token via `firebase_admin.auth.verify_id_token`.
- Extract email, name, picture.
- Check if user exists via `brain.get_user_profile(email)`.
- If yes, update `display_name` and `photo_base64` if empty.
- If no, create `UserProfile` with defaults (age 30, weight 70, height 170, gender Masculino, goal_type maintain, subscription_plan Free). Create `TrainerProfile` and initial `WeightLog`.
- Return `create_token(email)`.

**Step 3: Run test to verify it passes**
Run: `cd backend && pytest tests/api/endpoints/test_user_social.py -v`
Expected: PASS

**Step 4: Commit**
```bash
git add src/api/endpoints/user.py src/api/models/auth.py tests/api/endpoints/test_user_social.py
git commit -m "feat(backend): add social login endpoint with auto user creation"
```

---

### Task 4: Frontend - Add Firebase Dependency and Config

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/src/shared/config/env.ts`
- Create: `frontend/src/features/auth/firebase.ts`

**Step 1: Write minimal implementation**
Run `cd frontend && npm install firebase`

In `frontend/src/shared/config/env.ts`, add:
```typescript
  FIREBASE_API_KEY: import.meta.env.VITE_FIREBASE_API_KEY as string,
  FIREBASE_AUTH_DOMAIN: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN as string,
  FIREBASE_PROJECT_ID: import.meta.env.VITE_FIREBASE_PROJECT_ID as string,
```

Create `frontend/src/features/auth/firebase.ts` with standard `initializeApp` and `getAuth`.

**Step 2: Commit**
```bash
git add frontend/package.json frontend/package-lock.json frontend/src/shared/config/env.ts frontend/src/features/auth/firebase.ts
git commit -m "chore(frontend): add firebase sdk and config"
```

---

### Task 5: Frontend - Add Social Login to Auth Store

**Files:**
- Modify: `frontend/src/shared/hooks/useAuth.ts`
- Modify: `frontend/src/shared/hooks/useAuth.test.ts`

**Step 1: Write the failing test**
In `useAuth.test.ts`, add a test for `socialLogin` action. Mock `signInWithPopup` and API call.

Run: `cd frontend && npm test -- src/shared/hooks/useAuth.test.ts`
Expected: FAIL (socialLogin is not a function)

**Step 2: Write minimal implementation**
In `useAuth.ts`, add `socialLogin: (provider: 'google' | 'apple') => Promise<void>` to `AuthActions` and `AuthStore`.
Implement the method: call `signInWithPopup(auth, new GoogleAuthProvider())`, get `idToken`, send `POST /user/social-login`, save token and call `loadUserInfo()`.

**Step 3: Run test to verify it passes**
Run `cd frontend && npm test -- src/shared/hooks/useAuth.test.ts`
Expected: PASS

**Step 4: Commit**
```bash
git add frontend/src/shared/hooks/useAuth.ts frontend/src/shared/hooks/useAuth.test.ts
git commit -m "feat(frontend): add socialLogin to auth store"
```

---

### Task 6: Frontend - Update UI with Google Button

**Files:**
- Modify: `frontend/src/features/auth/LoginPage.tsx`
- Modify: `frontend/src/features/auth/LoginPage.test.tsx`

**Step 1: Write the failing test**
In `LoginPage.test.tsx`, assert the presence of the "Continuar com Google" button and simulate click.

Run: `cd frontend && npm test -- src/features/auth/LoginPage.test.tsx`
Expected: FAIL

**Step 2: Write minimal implementation**
In `LoginPage.tsx`, import Social Icons (or create a custom button with SVG). Add the button below the typical login form with an `onClick` that triggers `socialLogin('google')`. Include terms and conditions separator (`Ou continue com`).

**Step 3: Run test to verify it passes**
Run `cd frontend && npm test -- src/features/auth/LoginPage.test.tsx`
Expected: PASS

**Step 4: Commit**
```bash
git add frontend/src/features/auth/LoginPage.tsx frontend/src/features/auth/LoginPage.test.tsx
git commit -m "feat(frontend): add google login button to ui"
```
