---
description: Run linters on backend and frontend
---

# Run All Linters

This workflow runs Pylint on the backend and ESLint on the frontend.

## Steps

// turbo

1. Run Pylint on backend:

```bash
cd /home/colutti/projects/personal/backend && pylint src/
```

// turbo 2. Run ESLint on frontend:

```bash
cd /home/colutti/projects/personal/frontend && npx eslint src/
```

3. Review any warnings or errors
4. Fix critical issues before committing
