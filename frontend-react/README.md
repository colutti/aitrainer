# AI Personal Trainer - React Frontend

Modern React 19 frontend for the AI Personal Trainer application, built with Vite 6 and TailwindCSS v4.

## Tech Stack

- **React 19** - Latest React with improved performance and new features
- **Vite 6** - Lightning-fast build tool and dev server
- **TypeScript 5.9+** - Strict type safety with `noUncheckedIndexedAccess`
- **TailwindCSS v4** - Utility-first CSS with custom dark theme
- **Zustand 5** - Lightweight state management
- **React Router 7** - Client-side routing
- **Recharts 2.15+** - Declarative charting library
- **react-hook-form 7 + Zod** - Type-safe form validation
- **Vitest 3** - Fast unit testing with 90% coverage threshold
- **Playwright 1.50+** - End-to-end testing
- **ESLint + Prettier** - Strict code quality enforcement

## Project Structure

```
src/
  shared/              # Shared utilities and components
    api/               # HTTP client and API functions
    components/ui/     # shadcn/ui components
    hooks/             # Shared hooks (useAuth, useNotification, etc.)
    types/             # TypeScript interfaces
    utils/             # Utility functions (formatDate, formatNumber)
  features/            # Feature-based modules
    auth/              # Authentication
    chat/              # AI chat with streaming
    dashboard/         # Main dashboard with widgets
    body/              # Weight, nutrition, metabolism tracking
    workouts/          # Workout history
    nutrition/         # Nutrition logs
    memories/          # AI memory management
    settings/          # User settings and integrations
    admin/             # Admin panel
    onboarding/        # User onboarding flow
  test/                # Test setup and utilities
```

## Development

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

# Run E2E tests
npm run test:e2e

# Lint code
npm run lint

# Fix lint errors
npm run lint:fix

# Type check
npm run typecheck

# Run all checks (lint + typecheck + test)
npm run check

# Build for production
npm run build

# Preview production build
npm run preview
```

### Environment Variables

Create a `.env` file:

```env
VITE_API_URL=/api  # For dev (proxied by Vite)
# VITE_API_URL=https://your-backend.com  # For production
```

## Code Quality Standards

### Zero Warnings Policy

- ESLint must pass with zero warnings
- TypeScript must compile with zero errors
- All tests must pass
- Coverage must be ≥90% for branches, functions, lines, and statements

### TypeScript Rules

- `strict: true` - All strict checks enabled
- `noUncheckedIndexedAccess: true` - Extra safety for array/object access
- No `any` types allowed
- No `as` type assertions unless absolutely necessary
- No `// @ts-ignore` comments

### Code Style

- **JSDoc** required on all public functions, hooks, and stores
- **Prettier** for consistent formatting
- **ESLint** with strict TypeScript rules
- **Import order** enforced (builtin → external → internal → parent → sibling → index)

## Testing

### Unit Tests (Vitest)

- Test files colocated with source: `useAuth.test.ts` next to `useAuth.ts`
- Use Testing Library for component tests
- Mock API calls with MSW (Mock Service Worker)
- Coverage thresholds: 90% across all metrics

### E2E Tests (Playwright)

- Located in `e2e/` directory
- Focus on critical user flows
- ~10-15 tests covering: login, chat, dashboard, CRUD operations, navigation

## Architecture Principles

### Feature Isolation

- Features NEVER import from other features
- Features only import from `shared/`
- Each feature has its own components, hooks, and API functions
- Adding a new feature = creating a new folder, no changes to existing code

### State Management

- **Zustand** for global state (auth, notifications, confirmation)
- **React Hook Form** for form state
- **URL state** via React Router for navigation
- Local component state for UI-only state

### API Layer

- Centralized `http-client.ts` with auth token injection
- Feature-specific API modules (e.g., `chat-api.ts`, `dashboard-api.ts`)
- Type-safe responses using TypeScript interfaces
- Error handling with user-friendly notifications

## Migration Status

- ✅ **Phase 0: Scaffolding** - Complete
- ⏳ **Phase 1: Core (Auth + Navigation)** - In Progress
- ⏳ **Phase 2: Chat**
- ⏳ **Phase 3: Dashboard + Widgets**
- ⏳ **Phase 4: Body (Weight + Nutrition + Metabolism)**
- ⏳ **Phase 5: Workouts + Nutrition Pages**
- ⏳ **Phase 6: Settings + Integrations + Memories**
- ⏳ **Phase 7: Admin**
- ⏳ **Phase 8: Onboarding**
- ⏳ **Phase 9: E2E + Docker + Deploy**

## Contributing

1. Follow TDD: Write tests first, then implementation
2. Run `npm run check` before committing
3. Ensure all tests pass and coverage meets thresholds
4. Follow the established folder structure and naming conventions
5. Document all public APIs with JSDoc
