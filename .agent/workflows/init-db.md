---
description: Initialize database with default user
---

# Initialize Database

This workflow creates the default admin user in MongoDB.

## Steps

1. Make sure MongoDB is running:

```bash
cd /home/colutti/projects/personal && podman ps | grep mongo
```

2. Initialize the database with admin user (email: admin, password: 123):

```bash
cd /home/colutti/projects/personal && make init-db USUARIO=admin SENHA=123
```

3. Verify the user was created by trying to login at http://localhost:3000

Note: You can create additional users by running the command with different USUARIO and SENHA values.
