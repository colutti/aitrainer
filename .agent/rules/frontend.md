# Frontend Development Rules

## Angular Best Practices

### Component Design

- One component = one responsibility
- Use signals for reactive state management
- Prefer standalone components
- No `any` types - always use proper TypeScript typing

### Services

- Services should be singleton (`providedIn: 'root'`)
- **Always unsubscribe** from Observables in `ngOnDestroy`
- Use `HttpClient` for all HTTP calls
- Implement retry logic for critical API calls

### Routing

- Use route guards for authentication
- **Redirect unauthenticated users** to login immediately
- Lazy load large feature modules
- Define proper route typing

### Styling

- Prefer Tailwind utility classes
- Avoid `!important` at all costs
- Use CSS variables for theme colors and spacing
- Keep component styles scoped

### Code Quality

- Run `npx prettier --write` before commits
- Run `npx eslint` and fix warnings
- Use TypeScript strict mode
- All public methods must have JSDoc comments

### Testing (Cypress)

- Execute `/test` workflow before committing
- Tests must be independent
- Use `data-cy` attributes for element selection
- Prefer `cy.should()` over `cy.wait()`
