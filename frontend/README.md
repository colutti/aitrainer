# Fit IQ - Frontend React

Modern React 19 + Vite 7 + TypeScript single-page application for Fit IQ fitness platform.

## 🚀 Tech Stack

- **Framework**: React 19 with Vite 7
- **Language**: TypeScript 5.7+ (strict mode)
- **Styling**: TailwindCSS v4
- **State Management**: Zustand 5
- **Forms**: react-hook-form 7 + Zod validation
- **Charts**: Recharts 2.15+
- **Testing**: Vitest 3 + Testing Library + Playwright 1.50+
- **Routing**: React Router 7

## 📦 Project Structure

```
src/
  features/          # Feature-based modules (isolated)
    auth/
    chat/
    dashboard/
    body/
    workouts/
    nutrition/
    settings/
    admin/
    onboarding/
    memories/
  shared/            # Shared utilities and components
    api/             # HTTP client and API utilities
    components/      # Reusable UI components (Button, Input, etc.)
    hooks/           # Custom React hooks and Zustand stores
    types/           # TypeScript type definitions
    utils/           # Utility functions (formatting, etc.)
```

## 🛠️ Development

### Prerequisites

- Node.js 22+
- npm 10+

### Setup

```bash
# Install dependencies
npm install

# Start dev server (port 3000)
npm run dev

# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run E2E tests (Playwright)
npm run test:e2e

# Lint code
npm run lint

# Fix lint issues
npm run lint:fix

# Type check
npm run typecheck

# Run all checks (lint + typecheck + test)
npm run check
```

### Environment Variables

Create a `.env` file for local development:

```env
VITE_API_URL=/api
```

For production, the API URL is set via Docker build arg.

## 🧪 Testing

### Unit & Integration Tests

- **Framework**: Vitest + Testing Library
- **Coverage Target**: ≥90% (branches, functions, lines, statements)
- **Location**: `.test.ts` files colocated with source

### E2E Tests

- **Framework**: Playwright
- **Location**: `e2e/` directory
- **Run**: `npm run test:e2e`

## 🏗️ Build & Deploy

### Docker Build

```bash
# Build with default prod API URL
docker build -t aitrainer-frontend .

# Build with custom API URL
docker build --build-arg VITE_API_URL=https://api.example.com -t aitrainer-frontend .
```

### Production Build

```bash
# Create optimized production bundle
npm run build

# Preview production build locally
npm run preview
```

## 📐 Architecture Principles

1. **Feature Isolation**: Features are completely isolated. No feature imports from another feature.
2. **TDD**: Write tests before implementation (Red → Green → Refactor).
3. **Type Safety**: Strict TypeScript with no `any`, `as`, or `// @ts-ignore`.
4. **Documentation**: JSDoc on all public functions, hooks, and stores.
5. **Zero Warnings**: ESLint and TypeScript must pass with zero warnings.

## 🎨 Design System

- **Theme**: Dark mode with gradient accents
- **Colors**: 
  - Primary gradient: `#10b981` (green) → `#3b82f6` (blue)
  - Background: `#09090b` (zinc-950)
  - Cards: `#18181b` (zinc-900)
  - Borders: `#27272a` (zinc-800)
- **Typography**: System font stack with fallbacks
- **Components**: Based on shadcn/ui patterns, customized for dark theme

## 🔐 Authentication

- **Storage**: JWT in `localStorage` (key: `auth_token`)
- **Interceptor**: Automatic Bearer token attachment via `http-client.ts`
- **Auto-logout**: On 401 responses or token expiration
- **Route Guards**: `ProtectedRoute` and `AuthGuard` components

## 📝 Code Style

- **ESLint**: Flat config with `@typescript-eslint/strict`
- **Prettier**: Default config
- **Import Order**: Enforced via `eslint-plugin-import`
- **Naming**: 
  - Components: PascalCase (`LoginPage.tsx`)
  - Hooks: camelCase with `use` prefix (`useAuth.ts`)
  - Utils: camelCase (`format-date.ts`)
  - Constants: UPPER_SNAKE_CASE

## 📚 Key Features

- **Chat**: Streaming AI responses with markdown rendering
- **Dashboard**: 15+ widgets with Recharts visualizations
- **Body**: Weight tracking, nutrition logging, metabolism insights (3 tabs)
- **Workouts**: Paginated workout history with detailed drawer view
- **Nutrition**: Standalone nutrition logs with filters and stats
- **Settings**: User profile, trainer selection, integrations (Hevy, MFP, Zepp Life, Telegram)
- **Admin**: User management, logs viewer, prompts history (admin-only)
- **Onboarding**: 4-step wizard for new users

## 🚨 Production Checklist

Before deploying:

- [ ] `npm run lint` — Zero warnings
- [ ] `npm run typecheck` — Zero errors  
- [ ] `npm test` — All passing
- [ ] `npm run test:coverage` — ≥90% coverage
- [ ] `npm run test:e2e` — All E2E passing
- [ ] `npm run build` — No build warnings
- [ ] Docker build successful
- [ ] Environment variables configured
- [ ] Backend API accessible

## 📄 License

Proprietary - All Rights Reserved

## 👥 Contributors

- Rafael Colutti (@colutti)
