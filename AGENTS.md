# AGENTS.md — Moon-AI-Assistant-Platform

## Project Context
Moon-AI-Assistant-Platform is a desktop AI assistant application with a hierarchical 
multi-agent architecture. It features a Python FastAPI backend and a React + Electron 
frontend arranged as a monorepo.

The application has two main panels:
1. **Chat Interface** (left) — Real-time WebSocket chat with the AI head agent
2. **File Workspace** (right) — A file browser/playground where agents and users 
   create, view, and organize work files

## Architecture
- **Backend:** Python 3.11+, FastAPI, SQLite, FAISS (vector memory), LiteLLM
- **Frontend:** React 18+, TypeScript, Vite, Electron, Tailwind CSS
- **Communication:** WebSocket between frontend and backend
- **State Management:** Zustand (frontend), SQLite (backend persistence)

## Directory Structure
```
moon-ai-assistant-platform/
├── backend/           # Python FastAPI server
│   ├── main.py        # Entry point
│   ├── config/        # Settings and configuration
│   ├── api/routes/    # REST API route handlers
│   ├── api/websocket/ # WebSocket handlers
│   ├── core/          # Core business logic
│   │   ├── agent/     # Head agent logic
│   │   ├── memory/    # Memory systems (vector, condensation, token counting)
│   │   ├── communication/ # Communication book (message chaining)
│   │   ├── spark/     # SPARK heartbeat system
│   │   ├── scheduler/ # Cron jobs
│   │   └── llm/       # LLM integration and routing
│   ├── models/        # SQLite database models
│   ├── services/      # Business logic services
│   ├── agents/        # Agent file storage (core .md files per agent)
│   ├── data/          # SQLite database files
│   ├── workspace/     # User/agent file workspace
│   └── tests/         # pytest tests
├── frontend/          # React + Electron app
│   ├── electron/      # Electron main process
│   ├── src/
│   │   ├── components/
│   │   │   ├── chat/      # Chat interface components
│   │   │   ├── workspace/ # File browser/viewer components
│   │   │   ├── agents/    # Agent status panel
│   │   │   └── common/    # Shared UI components
│   │   ├── hooks/     # Custom React hooks
│   │   ├── services/  # API client services
│   │   ├── stores/    # Zustand state stores
│   │   ├── types/     # TypeScript type definitions
│   │   └── styles/    # Global styles and Tailwind config
│   └── tests/         # Vitest + React Testing Library tests
└── docs/              # Additional documentation
```

## Coding Standards

### Python (Backend)
- Use type hints on ALL function parameters and return types
- Follow PEP 8 style guidelines
- Use async/await for all I/O operations (database, file, network)
- Add docstrings to all public functions and classes
- Use Pydantic BaseModel for all request/response validation
- All API routes prefixed with `/api/v1/`
- WebSocket endpoint at `/ws`

### TypeScript (Frontend)
- Strict TypeScript mode — NO `any` types
- Functional components with hooks only (no class components)
- Named exports preferred over default exports
- Use TypeScript interfaces for all data shapes
- Component files: PascalCase (e.g., `ChatPanel.tsx`)
- Utility files: camelCase (e.g., `apiClient.ts`)
- Hooks: camelCase starting with `use` (e.g., `useWebSocket.ts`)

### Styling
- Use Tailwind CSS utility classes exclusively
- Dark theme as default
- No CSS modules, no styled-components, no inline style objects
- Responsive design with Tailwind breakpoints

### State Management
- Zustand for global state (NOT Redux)
- React state (useState) for component-local state
- No prop drilling beyond 2 levels — use Zustand stores instead

## Environment Setup

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev          # Vite dev server
npm run electron:dev # Electron with hot reload
```

### Testing
```bash
# Backend tests
cd backend && pytest -v

# Frontend tests
cd frontend && npm test
```

## Key Dependencies

### Backend (Python)
- fastapi, uvicorn[standard] — Web framework
- websockets — WebSocket support
- python-dotenv — Environment variables
- pydantic — Data validation
- aiosqlite — Async SQLite
- litellm — Multi-provider LLM gateway
- sentence-transformers — Text embeddings
- faiss-cpu — Vector similarity search
- apscheduler — Job scheduling (SPARK + cron)
- tiktoken — Token counting
- httpx — Async HTTP client

### Frontend (TypeScript/React)
- react, react-dom — UI framework
- typescript — Type safety
- vite — Build tool
- electron, electron-builder — Desktop packaging
- tailwindcss, postcss, autoprefixer — Styling
- zustand — State management
- socket.io-client — WebSocket client
- @monaco-editor/react — Code editor
- react-markdown — Markdown rendering
- lucide-react — Icons
- react-resizable-panels — Resizable split panels

## Important Conventions
- SQLite databases are stored in `backend/data/` directory
- Agent core files (.md) are stored in `backend/agents/<agent-id>/` 
- User workspace files are in `backend/workspace/`
- All timestamps use ISO 8601 format (UTC)
- UUIDs (uuid4) are used for com_ids and agent_ids
- Environment variables are loaded from `.env` file in project root
- CORS is configured to allow frontend origin (localhost:5173 in dev)
