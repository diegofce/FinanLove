# Project: FinanLove

Private personal and shared financial management tool.

## Stack

### Backend
- **Framework:** FastAPI
- **Language:** Python 3.12+
- **Validation:** Pydantic v2
- **ORM:** SQLAlchemy 2 (Async)
- **Migrations:** Alembic
- **Database:** PostgreSQL

### Frontend
- **Framework:** React
- **Language:** TypeScript (Strict)
- **Build Tool:** Vite
- **Styling:** Tailwind CSS
- **Data Fetching:** TanStack Query

## Architecture
This project follows a **Pragmatic Clean Architecture** organized as a **Modular Monolith**. For detailed information, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Repository Structure
```
finanlove/
├── .agents/          # Agent skills and instructions
├── .github/          # Workflows and Copilot rules
├── docs/             # Technical and functional documentation
├── src/
│   ├── backend/      # FastAPI application
│   ├── frontend/     # React application
│   └── shared/       # Shared assets or documentation
├── docker/           # Dockerfiles for each service
├── scripts/          # Automation scripts (sh/ps1)
└── compose.yml       # Docker Compose for local development
```

## Getting Started
See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed setup instructions.

## Agent-Ready Repository
This repository is designed for AI-Agent collaboration.
- **AGENTS.md:** Main operational rules for agents.
- **CLAUDE.md:** Guidance for Claude/Gemini.
- **.github/copilot-instructions.md:** Rules for GitHub Copilot.
- **.agents/skills/:** Procedural guardrails.

## License
Private - All Rights Reserved.
