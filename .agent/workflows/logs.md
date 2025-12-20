---
description: View logs from all services
---

# View Service Logs

This workflow shows logs from all running containers.

## Steps

// turbo

1. View logs from all services (follow mode):

```bash
cd /home/colutti/projects/personal && make logs
```

2. Press Ctrl+C to stop following logs

Alternative: View logs for a specific service:

- Backend only: `podman logs -f personal_backend_1`
- Frontend only: `podman logs -f personal_frontend_1`
- MongoDB only: `podman logs -f personal_mongo_1`
- Qdrant only: `podman logs -f personal_qdrant_1`
