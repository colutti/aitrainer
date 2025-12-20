---
trigger: always_on
---

# Backend Development Rules

## Python/FastAPI Best Practices

### Imports

- Always use `from src.*` for internal modules
- Import order: stdlib → third-party → local
- Prefer absolute imports over relative imports

### FastAPI Patterns

- **Use dependency injection** for database, memory, and LLM clients
- All endpoints must have docstrings with parameter and response descriptions
- Use Pydantic models for input/output validation
- Use `StreamingResponse` for long-running LLM operations

### Error Handling

- Use `HTTPException` with appropriate status codes for API errors
- Log errors before raising: `logger.error()`
- Catch specific exceptions, avoid bare `except Exception:`
- Always catch `google.api_core.exceptions.ResourceExhausted` for Gemini API calls

### Mem0 Integration (CRITICAL)

- **MUST consult official documentation** before modifying Mem0 code
- `memory.search()` returns `{"results": [...]}` dictionary, NOT a list
- `memory.add()` expects `[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]`
- Log all memory save/retrieve operations for debugging

### MongoDB

- Always use type hints for query return values
- Validate document existence before updates
- Use aggregation pipeline to avoid N+1 queries
- Index frequently queried fields

### Code Quality

- All docstrings and comments in English
- Type hints for all function parameters and returns
- Follow SOLID principles
- Run `black` for formatting before commits
- Run `pylint` and fix critical warnings

### Testing

- Write unit tests for all new functions
- Use fixtures for test data
- Mock external APIs (Gemini, Mem0) in unit tests
- Run `/test` workflow before committing
- Be carefull. Since this app connects to a paid AI model, it can timeout or have no credits left which can lead to erros when calling it. Those errors should always be ignored when that happens.
