# Spend Sense

Spend Sense is a privacy first personal finance intelligence app for tracking budgets, expenses, savings goals, month-end projections, and unlocking gamified achievements. It combines a local-first React frontend with a robust, production-ready FastAPI backend.

Spend Sense helps you understand where your money is going, spot risky spending patterns early, earn XP and achievements for disciplined financial habits, and turn everyday transactions into practical financial decisions.

---

## Architecture & Project Structure

The codebase is organized as a monorepo featuring a React Vite frontend and a FastAPI Python backend:

```text
Spend-Sense/
├── backend/                   # FastAPI backend application
│   ├── alembic/               # Database migration scripts
│   ├── app/
│   │   ├── api/v1/routes/     # API endpoint routers
│   │   ├── core/              # Config, security, logging, AI templates
│   │   ├── db/                # Engine session and Base metadata
│   │   ├── models/            # SQLAlchemy models (Auth, Gamification, etc.)
│   │   ├── repositories/      # Database abstraction layer
│   │   ├── schemas/           # Pydantic validation schemas
│   │   └── services/          # Business logic, AI orchestrator, XP engines
│   └── tests/                 # Backend test suite (pytest)
├── docs/                      # Core engineering documentation
│   ├── api-contracts.md       # API requests, responses, and schemas
│   ├── backend-roadmap.md     # phased backend deliverables and progress
│   ├── deployment.md          # Production deployment runbook
│   └── postgresql-schema.md   # SQL schema and relationship diagrams
├── src/                       # React 19 / TypeScript / Vite 6 frontend
│   ├── components/            # Reusable UI components & layouts
│   ├── constants/             # Default configurations
│   ├── engine/                # Client-side analysis and local insights
│   ├── hooks/                 # Custom React hooks (including feedback store)
│   ├── pages/                 # Route target pages (Dashboard, Analytics, etc.)
│   ├── store/                 # Zustand app store with localStorage persistence
│   └── utils/                 # Formatting, calculations, and helpers
└── package.json               # Frontend package manager configuration
```

---

## What Makes Spend Sense Different

| Feature | Spend Sense | Typical Budget Tracker |
| --- | --- | --- |
| **Predictive Projections** | Forecasts month-end spending from current pace | Shows only static historical lists |
| **Hybrid Persistence** | Works locally first (localStorage) with backend sync | Fails completely without server connectivity |
| **Gamification Engine** | XP, levels, daily challenges, & 20+ achievement badges | Uninspiring lists that fail to drive user habit |
| **Local Insights** | Generates dynamic financial advice and warning flags | Leaves interpretation entirely to the user |
| **Privacy First** | Local control of financial data, exports to CSV & PDF | Keeps data captive or shares with advertisers |

---

## Features

### 📊 Financial Dashboard
Summarizes the active month with income, total spent, remaining budget, savings rate, projected month-end spend, and projected savings. A spend velocity ring shows how quickly the budget is being used, while a seven-day spending chart highlights recent behavior.

### 💰 Monthly Budget Planning
Create monthly budgets with income, planned category allocations, and custom categories. Each category supports direct numeric editing, slider-based adjustment, icon selection, color-coded progress, and allocation previews.

### 💸 Expense Tracker
Log expenses with category, amount, date, and notes. Includes autocomplete category selection, category filters, text search, inline edits, and immediate budget utilization indicators.

### 📈 Predictive Analytics & Insights
Computes category distributions, actual vs. planned expenses, cumulative spending trends, and month-end projections. An **AI-Powered Insights Engine** uses Gemini/Claude/OpenAI to generate plain-language observations, falling back on a rule-based engine when API limits are reached.

### 🏆 Gamification & Achievements
Earn XP, level up, and build streaks by maintaining budgets and logging expenses. Join daily challenges and unlock 20 badges (spanning disciplines, savings, streaks, and community milestones) managed by an idempotent backend events engine.

### 🔒 Feedback & Diagnostic System
Engage with interactive onboarding checklists, What's New changelog alerts, coach mark overlays, non-blocking CSAT star ratings, and an NPS survey helper, coupled with local error diagnostics.

<<<<<<< HEAD
### Expense Tracker

Log expenses with category, amount, date, and notes. The tracker includes:

- Fast category selection with visual icons
- Search by note or category
- Category filters
- Inline edit and delete controls
- Per-category budget usage while logging
- Local toast feedback for successful actions

### Predictive Analytics

Spend Sense computes projections locally from your current spending velocity. The analytics workspace includes:

- Category distribution charts
- Planned vs actual comparison
- Daily cumulative spending trends
- Month-end projection charts
- Budget and income reference lines
- Projected savings and daily average calculations

### Local Insights Engine

The insights engine generates plain-language observations from your budget and expenses. It can flag:

- Categories that are over budget
- Categories approaching their limit
- Spending velocity likely to cause overspending
- Safe daily spend for remaining days
- Recurring charges based on repeated amounts
- Time-to-earn estimates based on hourly wage
- Quick-win savings opportunities
- Month-end projection risks

Insights are grouped into warnings, predictions, tips, and wins, with higher-severity items shown first.

### Savings Goals

Spend Sense includes a dedicated savings goals system for tracking financial milestones such as an emergency fund, vacation, home deposit, car, education, or laptop purchase.

Each goal can store:

- Target amount
- Current saved amount
- Monthly contribution
- Optional target date
- Icon and color
- Contribution history

The goals overview shows active goals, total saved, total target progress, monthly contributions, and savings streak.

### Goal Detail Pages

Each savings goal has its own detail page with progress, remaining amount, predicted completion month, contribution consistency, growth charts, monthly contribution charts, history, edit controls, and delete protection.

Goal-level insights help identify whether you are on track or need to increase monthly contributions to meet a target date.

### Reports and Exports

Generate a monthly summary report with income, spending, savings, savings rate, projected month-end spend, category breakdowns, top categories, and month-over-month comparisons.

Exports include:
- PDF monthly report
- CSV expense export

### Privacy-First Local Storage

Spend Sense persists budgets, expenses, goals, contribution history, and preferences in browser `localStorage` through Zustand persistence. Your financial data stays on your device.
=======
---
>>>>>>> 0dcbbe6 (Updation)

## Technology Stack

### Frontend
- **React 19 & TypeScript**
- **Vite 6** for fast development and building
- **Zustand** for local state management and persistence
- **Tailwind CSS** & **Framer Motion** for premium aesthetics and micro-animations
- **Radix UI** & **Lucide React** icons
- **Recharts** for interactive visual analytics
- **jsPDF** & **jspdf-autotable** for PDF reports

### Backend
- **FastAPI** (Python 3.10+)
- **SQLAlchemy 2.0 ORM** & **PostgreSQL** (via `psycopg3`)
- **Alembic** for automated database migration scripting
- **Pydantic v2** for robust type validation and serialization
- **Pytest** for integration and unit test coverage
- **SlowAPI** for endpoint rate-limiting and security
- **Sentry SDK** for runtime error tracking

---

## Quick Start

### Prerequisites
- Node.js 18 or newer and npm.
- Python 3.10 or newer (with virtualenv/venv).
- PostgreSQL database instance.

### 1. Frontend Setup

Install dependencies and run the development server:
```bash
npm install
npm run dev
```
Open `http://localhost:5173` to access the local-first application.

### 2. Backend Setup

1. **Navigate to the backend directory and set up a virtual environment:**
   ```bash
   cd backend
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

2. **Install Python packages:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Create a `.env` file in the `backend/` directory by copying `.env.example`:
   ```bash
   cp .env.example .env
   ```
   Update the connection string `DATABASE_URL` with your local PostgreSQL credentials, along with security parameters (`SECRET_KEY`).

4. **Run Database Migrations:**
   ```bash
   alembic upgrade head
   ```

5. **Start the FastAPI server:**
   ```bash
   uvicorn app.main:app --reload
   ```
   Open `http://localhost:8000/docs` to view the interactive Swagger/OpenAPI documentation.

---

## Verification & Testing

### Running Frontend Checks
```bash
npm test          # Run Vitest test suites
npm run lint      # Run ESLint validation
npm run build     # Verify production bundler output
```

### Running Backend Checks
```bash
cd backend
pytest                    # Run Pytest suites
python -m compileall app  # Compile app to catch syntax errors
```

---

## Deployment

- **Frontend**: Standard SPA deploy config included for **Vercel** (`vercel.json`).
- **Backend**: Container and configuration blueprint provided for **Render** (`render.yaml`).
- Database migrations are run automatically during backend deployments. Refer to [deployment.md](file:///d:/Projects/Spend%20Sense/docs/deployment.md) for full runbooks and rollback procedures.

---

## Core Engineering Specifications

For deeper details on backend phases, schemas, and endpoints:
- Refer to [AGENTS.md](file:///d:/Projects/Spend%20Sense/AGENTS.md) for development rules.
- Refer to [CODEX.md](file:///d:/Projects/Spend%20Sense/CODEX.md) for command lists.
- Refer to [api-contracts.md](file:///d:/Projects/Spend%20Sense/docs/api-contracts.md) for API routes.
- Refer to [postgresql-schema.md](file:///d:/Projects/Spend%20Sense/docs/postgresql-schema.md) for the database model layout.
- Refer to [backend-roadmap.md](file:///d:/Projects/Spend%20Sense/docs/backend-roadmap.md) to review project phases.

---

## License & Author

- **License**: MIT
- **Author**: Sneha Dagwar & Megha Dagwar
