---
description: Format Python and TypeScript code
---

# Format All Code

This workflow formats Python code with Black and TypeScript code with Prettier.

## Steps

// turbo

1. Format Python backend code:

```bash
cd /home/colutti/projects/personal/backend && black src/
```

// turbo 2. Format TypeScript frontend code:

```bash
cd /home/colutti/projects/personal/frontend && npx prettier --write "src/**/*.{ts,html,css}"
```

3. Review the changes made by the formatters
