# General Development Rules

## Git Workflow

**Commits**

- Atomic commits (one logical change)
- Descriptive commit messages
- Never commit `.env` or secrets

**Before Push**

- Run `/format` `/lint` `/test`
- Self-review changes
- Update documentation

## Security

- **NEVER commit secrets**
- Use environment variables for sensitive config
- Validate/sanitize user inputs
- HTTPS in production
- Rate limiting on public endpoints

## Performance

- Profile before optimizing
- MongoDB indexes for frequent queries
- Pagination for large lists
- Cache when appropriate

## Documentation

- Docstrings in English
- Explain "why" not "what"
- Keep comments updated
- Maintain README

## Workflows

Available in `/.agent/workflows/`:

- `/test` - Run all tests
- `/rebuild` - Rebuild containers
- `/format` - Format all code
- `/lint` - Run linters
- `/logs` - View service logs
- `/init-db` - Initialize database
- `/dev-local` - Local dev (hot reload)
- `/clean-env` - Clean environment

## Development Flow

1. Pull latest changes
2. Run `/clean-pod` if needed
3. Start: `make up`
4. Make changes
5. Run `/format` `/lint` `/test`
6. Commit and push

## Monitoring URLs

- Backend: `http://localhost:8000/health`
- Frontend: `http://localhost:3000`
- Qdrant: `http://localhost:6333/dashboard`
- MongoDB: `http://localhost:8081`

## Project-Specific

**AI Trainer Personality**

- Respect user's `trainer_profile`
- Personalize with `user_profile`
- Use relevant memories
- Maintain consistent tone

**Session Management**

- One session = one `user_email`
- Chat history paginated
- Long-term memories persist
- Logout clears tokens

**Mem0 Memory**

- Store facts, not chat messages
- Verify retrieval after changes
- Log save/retrieve operations
- Test across sessions
