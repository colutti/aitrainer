---
description: Clean environment (remove containers, volumes, cache)
---

# Clean Environment

This workflow completely cleans the development environment, removing containers, volumes, and cache files.

## Steps

// turbo

1. Stop and remove all containers and the pod:

```bash
cd /home/colutti/projects/personal && make clean-pod
```

// turbo 2. Remove all volumes (WARNING: This deletes all database data):

```bash
cd /home/colutti/projects/personal && podman volume rm personal_mongodata personal_qdrant_data -f
```

// turbo 3. Clean Python cache files:

```bash
cd /home/colutti/projects/personal/backend && find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
```

// turbo 4. Clean Node modules and Angular cache:

```bash
cd /home/colutti/projects/personal/frontend && rm -rf node_modules .angular
```

5. Rebuild everything from scratch:

```bash
cd /home/colutti/projects/personal && podman-compose build --no-cache && make up
```

6. Re-initialize the database if needed
