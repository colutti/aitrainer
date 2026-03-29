# Reimport Prod User Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reimport `rafacolucci@gmail.com` into local dev and add post-import validation so the import fails loudly if the expected user data is missing.

**Architecture:** Keep the sync flow in `backend/scripts/sync_user_data.py`. Add one validation pass after the copy completes that reconnects to local MongoDB and checks the imported record counts for the user across the core collections. Reuse the same email and collection mapping already used by the sync script so the validator measures the real output of the script, not a separate path.

**Tech Stack:** Python 3.12, PyMongo, Qdrant client, existing backend script utilities.

---

### Task 1: Add post-import validation to the sync script

**Files:**
- Modify: `backend/scripts/sync_user_data.py`

- [ ] **Step 1: Add a validation helper**

```python
def validate_local_import(dest_db, user_email: str) -> None:
    expected_counts = {
        "users": 1,
        "trainer_profiles": 1,
        "workout_logs": 1,
        "nutrition_logs": 1,
        "weight_logs": 1,
        "prompt_logs": 1,
        "message_store": 1,
    }

    queries = {
        "users": {"email": user_email},
        "trainer_profiles": {"user_email": user_email},
        "workout_logs": {"user_email": user_email},
        "nutrition_logs": {"user_email": user_email},
        "weight_logs": {"user_email": user_email},
        "prompt_logs": {"user_email": user_email},
        "message_store": {"SessionId": user_email},
    }

    for collection_name, minimum_count in expected_counts.items():
        count = dest_db[collection_name].count_documents(queries[collection_name])
        print(f"   Validation {collection_name}: {count} document(s)")
        if count < minimum_count:
            raise RuntimeError(
                f"Validation failed for {collection_name}: expected at least {minimum_count}, got {count}"
            )
```

- [ ] **Step 2: Call validation after Mongo and Qdrant sync**

```python
    print("\n✅ Running post-import validation...")
    validate_local_import(dest_db, args.email)
    print("✅ Post-import validation passed.")
```

- [ ] **Step 3: Keep Qdrant optional**

```python
    if args.prod_qdrant_url:
        ...
    else:
        print("\n⏭️  Skipping Qdrant Sync (No PROD URL provided).")

    print("\n✨ Sync Completed Successfully! ✨\n")
```

### Task 2: Recreate the local dev stack and re-run the import

**Files:**
- No code changes

- [ ] **Step 1: Start local Mongo and Qdrant**

```bash
cd /home/colutti/projects/personal
./scripts/compose.sh -f compose/base.yml up -d mongo qdrant
```

- [ ] **Step 2: Run the sync script against prod and local**

```bash
cd /home/colutti/projects/personal/backend
SRC_URI=$(grep '^MONGO_URI=' .env.prod | cut -d= -f2- | sed 's/^"//; s/"$//')
SRC_QDRANT_URL=$(grep '^QDRANT_HOST=' .env.prod | cut -d= -f2- | sed 's/^"//; s/"$//')
SRC_QDRANT_KEY=$(grep '^QDRANT_API_KEY=' .env.prod | cut -d= -f2- | sed 's/^"//; s/"$//')
.venv/bin/python scripts/sync_user_data.py \
  --email rafacolucci@gmail.com \
  --source-uri "$SRC_URI" \
  --source-db aitrainerdb \
  --prod-qdrant-url "$SRC_QDRANT_URL" \
  --prod-qdrant-key "$SRC_QDRANT_KEY" \
  --yes
```

- [ ] **Step 3: Confirm the validation output**

```text
Validation users: 1 document(s)
Validation trainer_profiles: 1 document(s)
Validation workout_logs: 159 document(s)
Validation nutrition_logs: 98 document(s)
Validation weight_logs: 64 document(s)
Validation prompt_logs: 20 document(s)
Validation message_store: 1691 document(s)
```

### Task 3: Verify the local data after import

**Files:**
- No code changes

- [ ] **Step 1: Query the local Mongo database for counts**

```bash
cd /home/colutti/projects/personal/backend
.venv/bin/python - <<'PY'
from pymongo import MongoClient
from src.core.config import settings
client = MongoClient(settings.MONGO_URI)
db = client[settings.DB_NAME]
email = 'rafacolucci@gmail.com'
for name, query in [
    ('users', {'email': email}),
    ('trainer_profiles', {'user_email': email}),
    ('workout_logs', {'user_email': email}),
    ('nutrition_logs', {'user_email': email}),
    ('weight_logs', {'user_email': email}),
    ('prompt_logs', {'user_email': email}),
    ('message_store', {'SessionId': email}),
]:
    print(name, db[name].count_documents(query))
PY
```

- [ ] **Step 2: Confirm the app can reach the imported data**

```bash
cd /home/colutti/projects/personal/frontend
npm test -- --run src/shared/hooks/useAuth.test.ts src/features/auth/LoginPage.test.tsx
```

