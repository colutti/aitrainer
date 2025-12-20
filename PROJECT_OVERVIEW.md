# AI Personal Trainer

Virtual personal trainer that helps users create personalized exercise plans using AI.

## Stack

- **Frontend**: Angular + TypeScript + Tailwind CSS
- **Backend**: Python 3.11 + FastAPI + Pydantic
- **AI**: Google Gemini (gemini-2.0-flash-exp)
- **Memory**: Mem0 + Qdrant (vector database)
- **Database**: MongoDB
- **Auth**: JWT tokens
- **Container**: Podman/Docker Compose
- **Testing**: Cypress (E2E), Pytest (unit)
- **Quality**: Black, Pylint, ESLint, Prettier

## Architecture

**Frontend** (Angular)

- User authentication and profiles
- Interactive chat interface
- Trainer personality customization

**Backend** (FastAPI)

- REST API with streaming responses
- AI conversation processing
- JWT authentication
- Health monitoring

**Database** (MongoDB)

- Users and authentication
- Chat history (session-based)
- User/Trainer profiles

**Long-term Memory** (Mem0 + Qdrant)

- Extract facts from conversations
- Semantic search for context
- Personalize responses across sessions

## Features

**Trainer Styles**

- Motivational: Energetic and encouraging
- Technical: Detailed and scientific
- Friendly: Casual and supportive

**User Profiles**

- Age, weight, height, fitness level, goals
- Physical limitations and exercise preferences
