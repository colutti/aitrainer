---
trigger: always_on
---

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

**Running**

- To run and debug the solution you should run the Docker Compose file and look at the logs to find issues. Make sure both frontend and backend are running.
- I DO NOT use Docker. I use Podman
- My default shell is fish. You should run your commands with BASH.
