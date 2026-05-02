# Spend Sense

Spend Sense is a personal finance intelligence web application that goes beyond simple expense logging. It helps you understand where your money goes, predict your end-of-month spending, and surface actionable insights tailored to your financial behavior — all running entirely in your browser with no backend required.

## Overview

Most budgeting tools are passive. They record what you spend and leave you to draw conclusions. Spend Sense takes a different approach: it actively computes trends, flags anomalies, and generates smart predictions based on your spending velocity. Think of it as a lightweight financial analyst that lives in your browser tab.

The application was built with a focus on being fast, private, and approachable. Your data never leaves your device. There are no accounts to create, no servers to trust, and no subscription fees.

## Features

### Dashboard
The main dashboard gives you an at-a-glance view of your financial health for the active month. It shows your total income, how much you have spent, how much remains, and your current savings rate. A spend velocity ring visualizes your budget usage as a percentage, and a seven-day spending bar chart shows your recent daily habits. The top three AI-generated insights are surfaced directly on the dashboard.

### Budget Setup
Define your monthly income and allocate it across spending categories such as food, rent, transport, shopping, and others. You can create custom categories with your own name and emoji icon. Each category has a slider and a direct numeric input so you can plan your budget with precision. A donut chart gives you an instant visual breakdown of your allocation.

### Expense Tracker
Log every expense in a clean, focused interface. Each entry is tied to a date, a category, a description, and an amount. The tracker displays all entries for the active month in a sortable, filterable list. A quick-add dialog is accessible from the top navigation bar on every page so you can record an expense without interrupting your workflow.

### Analytics
The analytics page visualizes your spending patterns through charts and tables. You can see how your spending is distributed across categories, how your daily and weekly totals compare, and where you are trending relative to your budget.

### Insights Engine
The insights engine runs locally in your browser and analyzes your spending data to generate plain-language observations. It flags categories where spending is accelerating, identifies months where patterns changed significantly, and offers specific suggestions. Insights are tiered by priority so the most important ones are always shown first.

### Reports
Generate a summary report for any month. Reports can be exported as a PDF document suitable for personal record-keeping or sharing with an accountant.

## Technology Stack

- React 19 with TypeScript for the UI layer
- Vite as the build tool and development server
- Tailwind CSS for styling, using a custom design system based on the Smartech pastel palette
- Zustand for client-side state management with localStorage persistence
- Recharts for data visualization
- Framer Motion for transitions and animations
- Radix UI primitives for accessible interactive components
- React Hook Form with Zod for form validation
- jsPDF and jspdf-autotable for PDF report generation
- Vitest and React Testing Library for unit testing

## Getting Started

### Prerequisites

You need Node.js version 18 or later and npm installed on your machine.

### Installation

Clone the repository and install dependencies.

```bash
git clone https://github.com/SnehaDagwar/Spend-Sense.git
cd Spend-Sense
npm install
```

### Running the Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:5173`. If that port is in use, Vite will automatically select the next available port and print the URL in the terminal.

### Building for Production

```bash
npm run build
```

The production-ready files will be output to the `dist` directory. You can preview the production build locally using:

```bash
npm run preview
```

### Running Tests

```bash
npm test
```

## Project Structure

```
src/
  components/       Reusable UI components organized by feature area
    budget/         Budget-specific components
    insights/       AI insight widget components
    layout/         Application shell, sidebar, and header
    tracker/        Expense tracker components
    ui/             Base UI primitives (shadcn-style)
  constants/        Application-wide constants and category definitions
  engine/           Client-side financial computation and insight generation
  hooks/            Custom React hooks
  lib/              Utility libraries (cn, date helpers)
  pages/            Top-level route components
  store/            Zustand state management and persistence logic
  test/             Test setup and example test files
  types/            Shared TypeScript type definitions
  utils/            Pure utility functions (formatters, calculations)
```

## Data Privacy

All financial data entered into Spend Sense is stored exclusively in your browser's localStorage. Nothing is transmitted to any server. If you clear your browser data, your financial records will be removed. There is no cloud sync, no account creation, and no third-party data sharing of any kind.

## Browser Support

Spend Sense supports all modern evergreen browsers: Chrome, Firefox, Edge, and Safari. It is not designed to support Internet Explorer.

## Contributing

Contributions are welcome. Please read the CONTRIBUTING.md file for guidelines on how to report issues, suggest features, and submit pull requests.

## License

This project is licensed under the MIT License. See the LICENSE file for the full license text.

## Author

Sneha Dagwar
