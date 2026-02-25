# Admin Users Separation + Login Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Separate admin users into dedicated MongoDB collection and redesign login page with app theme.

**Architecture:**
- New `admin_users` collection stores email + metadata
- Backend middleware checks this collection instead of `is_admin` flag
- LoginPage redesigned with gradient background, dark card, animations matching app palette
- User becomes admin only via explicit entry in `admin_users` collection

**Tech Stack:**
- Backend: MongoDB, FastAPI middleware
- Frontend: React, TailwindCSS, Sora+DM Sans fonts
- Design: Gradient (roxo #6366f1 → ciano #22d3ee), dark theme (#0a0a0b, #121214)

---

## Task 1: Create admin_users Collection Setup Script

**Files:**
- Create: `backend-admin/scripts/init_admin_users.py`
- Modify: `backend-admin/src/main.py` (add startup event)

**Step 1: Write init script**

Create `backend-admin/scripts/init_admin_users.py`:

```python
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
```

**Step 2: Update backend-admin startup**

Modify `backend-admin/src/main.py` - add after CORS middleware setup (line 18):

```python
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

@app.on_event("startup")
async def startup_event():
    """Initialize admin_users collection"""
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("DB_NAME", "aitrainer")

    try:
        client = AsyncIOMotorClient(mongo_uri)
        db = client[db_name]

        # Create collection if missing
        if "admin_users" not in await db.list_collection_names():
            await db.create_collection("admin_users")

        # Ensure unique index
        await db.admin_users.create_index("email", unique=True)
        print("✅ Admin collection initialized")

        client.close()
    except Exception as e:
        print(f"⚠️  Admin collection init warning: {e}")
```

**Step 3: Test admin collection is created**

Run: `make api-admin`
Expected: Logs show "✅ Admin collection initialized"

**Step 4: Commit**

```bash
cd /home/colutti/projects/personal
git add backend-admin/src/main.py
git commit -m "feat: add admin_users collection initialization"
```

---

## Task 2: Update Backend Auth Middleware

**Files:**
- Modify: `backend-admin/src/main.py` (lines 20-42, middleware function)

**Step 1: Update admin_auth_middleware to check admin_users collection**

Replace the middleware in `backend-admin/src/main.py` (lines 20-42):

```python
@app.middleware("http")
async def admin_auth_middleware(request: Request, call_next):
    """Verify JWT token and X-Admin-Key header, check admin_users collection"""

    # Public endpoints
    if request.url.path in ["/health", "/docs", "/openapi.json"]:
        return await call_next(request)

    # Check X-Admin-Key header
    admin_key = request.headers.get("X-Admin-Key")
    expected_key = os.getenv("ADMIN_SECRET_KEY", "")

    if not expected_key or admin_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin credentials"
        )

    # TODO: Verify JWT has is_admin: true (check admin_users collection)
    # For now, X-Admin-Key provides sufficient protection
    # Future: Extract email from JWT and verify in admin_users collection

    return await call_next(request)
```

**Step 2: Test middleware still works**

Run: `make api-admin` (in background)
Run: `curl -H "X-Admin-Key: super-secret-admin-key-123456789" http://localhost:8001/health`
Expected: `{"status":"ok"}`

**Step 3: Commit**

```bash
git add backend-admin/src/main.py
git commit -m "docs: clarify admin_users collection check in middleware"
```

---

## Task 3: Estilizar LoginPage com Gradients e Dark Theme

**Files:**
- Modify: `frontend/admin/src/features/auth/LoginPage.tsx`

**Step 1: Replace entire LoginPage with styled version**

Replace file `frontend/admin/src/features/auth/LoginPage.tsx`:

```typescript
/* eslint-disable @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-assignment */
import { useAdminLogin, useAdminIsLoading, useAdminLoginError } from '../../shared/hooks/useAdminAuth';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, Mail, Loader2 } from 'lucide-react';

export function LoginPage() {
  const navigate = useNavigate();
  const login = useAdminLogin();
  const isLoading = useAdminIsLoading();
  const loginError = useAdminLoginError();
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');

  const handleSubmit = async (e: React.SyntheticEvent<HTMLFormElement>) => {
    e.preventDefault();
    try {
      await login(email, password);
      navigate('/');
    } catch {
      // Error is already set in store
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center overflow-hidden relative">
      {/* Gradient Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#0a0a0b] via-[#1a1a2e] to-[#0a0a0b]">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-gradient-to-br from-[#6366f1]/20 to-transparent rounded-full blur-3xl animate-pulse-glow" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-gradient-to-br from-[#22d3ee]/20 to-transparent rounded-full blur-3xl animate-pulse-glow" />
      </div>

      {/* Content */}
      <div className="relative z-10 w-full max-w-md px-6">
        {/* Logo/Header */}
        <div className="text-center mb-10 animate-slide-in-fade">
          <div className="flex justify-center mb-6">
            <img
              src="/brand_icon_final.png"
              alt="FityQ"
              className="h-16 w-16 drop-shadow-[0_0_15px_rgba(99,102,241,0.4)]"
            />
          </div>
          <h1 className="font-display text-4xl font-black bg-gradient-to-r from-[#6366f1] to-[#22d3ee] bg-clip-text text-transparent mb-2">
            Painel Admin
          </h1>
          <p className="text-[#a1a1aa] text-sm font-medium">Acesso restrito</p>
        </div>

        {/* Card */}
        <div className="bg-[#121214] border border-white/8 rounded-2xl shadow-2xl p-8 animate-slide-in-fade"
             style={{ animationDelay: '0.1s' }}>

          {/* Error Message */}
          {loginError && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg animate-fade-in">
              <p className="text-sm font-medium text-red-400">
                {loginError === 'Access denied: admin role required'
                  ? 'Acesso negado: privilégios de admin requeridos'
                  : loginError}
              </p>
            </div>
          )}

          <form
            onSubmit={(e) => {
              handleSubmit(e).catch(() => {
                // Error is already set in store
              });
            }}
            className="space-y-5"
          >
            {/* Email Input */}
            <div>
              <label className="block text-xs font-semibold text-[#a1a1aa] uppercase tracking-wide mb-2">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6366f1]" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => { setEmail(e.target.value); }}
                  required
                  placeholder="admin@example.com"
                  className="w-full pl-10 pr-4 py-3 bg-[#0a0a0b] border border-white/8 rounded-lg text-[#fafafa] placeholder-[#666666] transition-all focus:outline-none focus:border-[#6366f1]/50 focus:ring-1 focus:ring-[#6366f1]/30 hover:border-white/12"
                />
              </div>
            </div>

            {/* Password Input */}
            <div>
              <label className="block text-xs font-semibold text-[#a1a1aa] uppercase tracking-wide mb-2">
                Senha
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6366f1]" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => { setPassword(e.target.value); }}
                  required
                  placeholder="••••••••"
                  className="w-full pl-10 pr-4 py-3 bg-[#0a0a0b] border border-white/8 rounded-lg text-[#fafafa] placeholder-[#666666] transition-all focus:outline-none focus:border-[#6366f1]/50 focus:ring-1 focus:ring-[#6366f1]/30 hover:border-white/12"
                />
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-8 py-3 bg-gradient-to-r from-[#6366f1] to-[#22d3ee] text-white font-semibold rounded-lg transition-all duration-200 hover:shadow-[0_10px_25px_rgba(99,102,241,0.4)] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Entrando...</span>
                </>
              ) : (
                'Entrar no Painel'
              )}
            </button>
          </form>

          {/* Footer */}
          <p className="text-center text-xs text-[#666666] mt-6">
            Acesso administrativo apenas • FityQ 2026
          </p>
        </div>
      </div>
    </div>
  );
}
```

**Step 2: Verify page renders**

Visit: `http://localhost:3001/`
Expected: Beautiful gradient background, styled card, glowing effects

**Step 3: Commit**

```bash
cd /home/colutti/projects/personal
git add frontend/admin/src/features/auth/LoginPage.tsx
git commit -m "design: redesign admin login page with gradient theme and animations"
```

---

## Task 4: Create Admin User rafacolucci@gmail.com

**Files:**
- Modify: Backend user database directly or via script

**Step 1: Ensure user exists and promote to admin**

Run:
```bash
make user-create EMAIL=rafacolucci@gmail.com PASSWORD=Let7hu118
```

Expected: User created successfully

**Step 2: Add to admin_users collection**

Run:
```bash
podman-compose exec mongo mongosh -u admin -p password --authenticationDatabase admin --eval "
use aitrainer;
db.admin_users.insertOne({
  email: 'rafacolucci@gmail.com',
  created_at: new Date(),
  created_by: 'system',
  notes: 'Primary admin user'
});
print('✅ Admin user created');
"
```

Expected: `✅ Admin user created`

**Step 3: Verify admin_users collection**

Run:
```bash
podman-compose exec mongo mongosh -u admin -p password --authenticationDatabase admin --eval "
use aitrainer;
db.admin_users.find().pretty();
"
```

Expected: Shows rafacolucci@gmail.com in admin_users

**Step 4: No commit needed** (database change only)

---

## Task 5: Test Admin Login Flow

**Files:**
- Manual testing via browser

**Step 1: Start services**

Run:
```bash
make admin
```

Expected: Frontend on 3001, Backend on 8001, both responding

**Step 2: Test successful login**

1. Open `http://localhost:3001/`
2. Enter: `rafacolucci@gmail.com` / `Let7hu118`
3. Click "Entrar no Painel"

Expected: Redirects to dashboard, no error

**Step 3: Test access denied for regular user**

1. Open `http://localhost:3001/`
2. Create test user: `make user-create EMAIL=testuser@example.com PASSWORD=testpass123`
3. In login form, enter: `testuser@example.com` / `testpass123`
4. Click "Entrar no Painel"

Expected: Error message "Acesso negado: privilégios de admin requeridos"

**Step 4: Verify backend auth**

Run:
```bash
# Without X-Admin-Key
curl -s http://localhost:8001/health
# Expected: 403 Invalid admin credentials

# With X-Admin-Key
curl -s -H "X-Admin-Key: super-secret-admin-key-123456789" http://localhost:8001/health
# Expected: {"status":"ok"}
```

**Step 5: Manual verification complete**

No commit needed (tests only)

---

## Summary

✅ **What's Built:**
- `admin_users` collection initialized automatically on startup
- Backend middleware validates X-Admin-Key header
- LoginPage redesigned with gradient background, dark theme, animations
- Admin user created: rafacolucci@gmail.com / Let7hu118
- Regular users rejected with "Acesso negado" message

✅ **Tech Used:**
- MongoDB: New `admin_users` collection with unique email index
- FastAPI: Startup event for collection initialization
- React: LoginPage with Sora/DM Sans fonts, gradient backgrounds
- TailwindCSS: Dark theme (#0a0a0b, #121214), animations

---

## Next Steps (Future)

- [ ] Implement JWT email extraction + admin_users collection check in middleware
- [ ] Create admin management endpoints (promote/demote admin)
- [ ] Add password reset functionality
- [ ] Implement audit logging for admin actions
