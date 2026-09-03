# DEVELOPMENT.md

## Local Setup

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose
- PowerShell (Windows) or Bash (Linux/macOS)

### Getting Started

1. **Clone the repository:**

   ```bash
   git clone <repo-url>
   cd finanlove
   ```

2. **Backend Setup:**

   ```bash
   cd src/backend
   python -m venv venv
   source venv/bin/activate # or venv\Scripts\activate on Windows
   python -m pip install --upgrade pip
   python -m pip install -e ".[dev]"
   ```

3. **Frontend Setup:**

   ```bash
   cd src/frontend
   npm ci
   ```

4. **Environment Variables:**
   Copy `.env.example` to `.env` and fill in the values.

### Running the App

- **Using Docker (Recommended):**

  ```bash
   docker compose up --build
  ```

- **Manual (Development):**
  - Backend: `scripts/dev.sh` (or `.ps1`)
  - Frontend: `npm run dev` in `src/frontend`

### Quality Checks

- **Run Tests:** `scripts/test.sh`
- **Linting:**
  - Backend: `ruff check .`
  - Frontend: `npm run lint`
- **Type Checking:**
  - Backend: `mypy .`
  - Frontend: `npm run typecheck`
