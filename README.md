# Spend Sense

Spend Sense is a privacy-first personal finance intelligence app for tracking budgets, expenses, savings goals, and month-end projections. It helps you understand where your money is going, spot risky spending patterns early, and turn everyday transactions into practical financial decisions.


## What makes Spend Sense different

| Spend Sense | Typical budget tracker |
| --- | --- |
| Predicts end-of-month spending from current pace | Shows only past transactions |
| Generates local insights, warnings, and quick wins | Leaves interpretation to the user |
| Tracks category budgets and dedicated savings goals | Often treats saving as a single leftover number |
| Exports PDF and CSV reports | Often locks reporting behind accounts or subscriptions |
| Stores data locally in the browser | Requires a remote account or server |

## Features

### Financial Dashboard

The dashboard summarizes the active month with income, total spent, remaining budget, savings rate, projected month-end spend, and projected savings. A spend velocity ring shows how quickly the budget is being used, while a seven-day spending chart highlights recent behavior.

The dashboard also surfaces the top local insights so you can act without digging through reports.

### Monthly Budget Planning

Create monthly budgets with income, planned category allocations, and custom categories. Each category supports direct numeric editing, slider-based adjustment, icon selection, color-coded progress, and an allocation preview chart.

Month navigation lets you move between past, current, and future budgets. New months are automatically seeded with sensible default categories.

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

## Technology Stack

- React 19 with TypeScript
- Vite 6 for development and production builds
- React Router 7 for client-side routing
- Zustand for local app state and persistence
- Tailwind CSS with a custom design system
- Radix UI primitives and shadcn-style components
- Lucide React icons
- Recharts for charts and projections
- Framer Motion for page and component transitions
- React Hook Form and Zod
- jsPDF and jspdf-autotable for PDF generation
- Vitest and React Testing Library for tests
- ESLint 9 for linting

## Quick Start

### Prerequisites

Install Node.js 18 or newer and npm.

### Install

```bash
git clone https://github.com/SnehaDagwar/Spend-Sense.git
cd Spend-Sense
npm install
```

### Run locally

```bash
npm run dev
```

Vite will print the local development URL, usually `http://localhost:5173`.

### Build

```bash
npm run build
```

Preview the production build:

```bash
npm run preview
```

### Test

```bash
npm test
```

### Lint

```bash
npm run lint
```

## Project Structure

```text
src/
  components/
    budget/          Budget-specific widgets and savings target cards
    goals/           Savings goal cards and add/edit dialogs
    insights/        Insight widgets
    layout/          App shell, sidebar, and page layout
    tracker/         Quick expense entry components
    ui/              Reusable UI primitives
  constants/         Default categories and suggested budget plan
  engine/            Prediction and insight generation logic
  hooks/             Shared React hooks
  lib/               Utility helpers
  pages/             Dashboard, Budget, Tracker, Analytics, Insights, Reports, Goals
  store/             Zustand app store with localStorage persistence
  test/              Test setup and examples
  types/             Shared TypeScript models
  utils/             Formatting and storage helpers
```

## Core Routes

| Route | Page |
| --- | --- |
| `/` | Dashboard |
| `/budget` | Budget setup and category savings targets |
| `/tracker` | Expense tracker |
| `/analytics` | Charts, trends, and projections |
| `/insights` | All generated insights |
| `/reports` | Monthly reports and exports |
| `/goals` | Savings goals overview |
| `/goals/:id` | Savings goal detail page |

## Data Model

Spend Sense stores:

- Monthly budgets keyed by `YYYY-MM`
- Category budgets with planned amounts, colors, icons, and custom-category flags
- Expenses with category, amount, date, note, and month
- Savings goals with target amount, current amount, contribution target, target date, color, icon, and history
- User settings such as active month, hourly wage, and savings streak

The persisted store key is `spend-sense-store-v1`.

## Data Privacy

All financial data is stored exclusively in your browser. Spend Sense does not send budgets, expenses, goals, or reports to a server.

Clearing browser data or localStorage will remove saved Spend Sense data from that browser.

## Browser Support

Spend Sense is designed for modern evergreen browsers including Chrome, Edge, Firefox, and Safari.

## Contributing

Contributions are welcome. Read `CONTRIBUTING.md` for guidance on issues, feature suggestions, and pull requests.

## License

This project is licensed under the MIT License. See `LICENSE` for details.

## Author

Sneha Dagwar
