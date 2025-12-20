---
description: Run backend and frontend locally (outside containers)
---

# Run Locally for Development

This workflow runs the backend and frontend outside of containers for faster development cycles.

## Prerequisites

1. Make sure MongoDB and Qdrant are running (via containers):

```bash
cd /home/colutti/projects/personal && podman-compose up -d mongo qdrant
```

## Steps

2. In one terminal, start the backend:

```bash
cd /home/colutti/projects/personal && make api
```

3. In another terminal, start the frontend:

```bash
cd /home/colutti/projects/personal && make front
```

4. Access the application:
   - Frontend: http://localhost:4200
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

Note: This mode allows for hot-reloading on code changes without rebuilding containers.
