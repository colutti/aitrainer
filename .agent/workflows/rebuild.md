---
description: Rebuild and restart all containers
---

# Rebuild and Restart Containers

This workflow completely rebuilds all Docker/Podman containers and restarts the application.

## Steps

// turbo

1. Stop and remove all containers:

```bash
cd /home/colutti/projects/personal && make clean-pod
```

// turbo 2. Rebuild all containers from scratch:

```bash
cd /home/colutti/projects/personal && podman-compose build --no-cache
```

// turbo 3. Start all services:

```bash
cd /home/colutti/projects/personal && make up
```

4. Wait 10-15 seconds for all services to initialize
5. Check that services are running at:
   - Frontend: http://localhost:3000
   - Backend: http://localhost:8000/health
   - Qdrant: http://localhost:6333/dashboard
