---
description: Run all Project Tests
---

# Run All Tests

This workflow runs all project tests and make sure everything works.

## Steps

// turbo

0. Make sure that you are using ollama for local development

1. Nagigate to the backend directory and run all python testes in the tests folder

2. Review the test results in the terminal output

3. If tests fail, check the error messages and fix the issues

4. Navigate to frontend directory and run Cypress tests:

```bash
cd /home/colutti/projects/personal/frontend && npx cypress run
```

6. Review the test results in the terminal output

7. If tests fail, check the error messages and fix the issues

8. Make sure to run all tests when fixing issues.

9. Do not execute the backend and the frontend. They are already runninn via docker and will be refreshed automatically when code changes.

10. Since both backend and frontend are running as containers, you should use podman logs to check for errors.
